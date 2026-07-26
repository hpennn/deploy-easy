"""
Deploy API routes
"""

import os
import io
import uuid
import asyncio
from typing import Optional

import zipfile
import tempfile
import shutil

from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import paramiko

# Import core logic from src
from src.cli import detect_project_type, generate_deploy_script, generate_dockerfile, generate_nginx_config
from web.api.servers import get_server_credentials, load_config

router = APIRouter()

# ============ SSH Session Store (in-memory) ============
ssh_sessions: dict = {}  # session_id -> { "client": paramiko.SSHClient, "info": {...} }


def _get_ssh_client(session_id: str) -> paramiko.SSHClient:
    """Get SSH client by session ID, raise 400 if not found or disconnected."""
    session = ssh_sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=400, detail="SSH 会话不存在或已过期，请重新连接")
    client = session["client"]
    transport = client.get_transport()
    if transport is None or not transport.is_active():
        ssh_sessions.pop(session_id, None)
        raise HTTPException(status_code=400, detail="SSH 连接已断开，请重新连接")
    return client


def _exec_ssh_command(client: paramiko.SSHClient, command: str, timeout: int = 30) -> tuple:
    """Execute a command on remote server via SSH, return (stdout_str, stderr_str, exit_code)."""
    stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    exit_code = stdout.channel.recv_exit_status()
    return out, err, exit_code


# ============ Request / Response Models ============

class ConnectRequest(BaseModel):
    host: str
    port: int = 22
    username: str = "root"
    password: Optional[str] = None
    key_content: Optional[str] = None


class ListPathsRequest(BaseModel):
    session_id: str


class DetectRequest(BaseModel):
    path: str
    session_id: Optional[str] = None  # If provided, detect on remote server


class RemoteDetectRequest(BaseModel):
    path: str
    session_id: str


class GenerateRequest(BaseModel):
    path: str
    deploy_type: str  # "server" | "cloudflare" | "docker" | "local"
    server: Optional[dict] = None
    domain: Optional[str] = None
    session_id: Optional[str] = None


class GenerateResponse(BaseModel):
    script: str
    filename: str
    extra_files: Optional[list] = None


# ============ Routes ============

@router.post("/connect")
async def connect_server(req: ConnectRequest):
    """Connect to a remote server via SSH and return a session ID."""
    if not req.host.strip():
        raise HTTPException(status_code=400, detail="请输入服务器 IP/域名")
    if not req.password and not req.key_content:
        raise HTTPException(status_code=400, detail="请提供密码或密钥")

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    loop = asyncio.get_event_loop()

    def _connect():
        connect_kwargs = {
            "hostname": req.host.strip(),
            "port": req.port,
            "username": req.username,
            "timeout": 15,
        }
        if req.key_content:
            key_file_obj = io.StringIO(req.key_content)
            try:
                pkey = paramiko.RSAKey.from_private_key(key_file_obj)
            except Exception:
                key_file_obj = io.StringIO(req.key_content)
                try:
                    pkey = paramiko.Ed25519Key.from_private_key(key_file_obj)
                except Exception:
                    key_file_obj = io.StringIO(req.key_content)
                    pkey = paramiko.ECDSAKey.from_private_key(key_file_obj)
            connect_kwargs["pkey"] = pkey
        elif req.password:
            connect_kwargs["password"] = req.password
        else:
            raise RuntimeError("需要提供密码或密钥")

        client.connect(**connect_kwargs)

    try:
        await loop.run_in_executor(None, _connect)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"SSH 连接失败: {str(e)}")

    # Verify connection by running a simple command
    try:
        _, _, exit_code = await loop.run_in_executor(
            None, lambda: _exec_ssh_command(client, "echo ok", timeout=10)
        )
    except Exception as e:
        client.close()
        raise HTTPException(status_code=400, detail=f"连接验证失败: {str(e)}")

    session_id = str(uuid.uuid4())[:8]
    ssh_sessions[session_id] = {
        "client": client,
        "info": {
            "host": req.host.strip(),
            "port": req.port,
            "username": req.username,
        },
        "password": req.password,
        "key_content": req.key_content,
    }

    # Get remote hostname for display
    try:
        hostname_out, _, _ = await loop.run_in_executor(
            None, lambda: _exec_ssh_command(client, "hostname", timeout=10)
        )
        hostname = hostname_out.strip()
    except Exception:
        hostname = req.host.strip()

    return {
        "session_id": session_id,
        "host": req.host.strip(),
        "hostname": hostname,
        "message": f"成功连接到 {hostname} ({req.host.strip()})",
    }


@router.post("/disconnect")
async def disconnect_server(session_id: str):
    """Disconnect and remove SSH session."""
    session = ssh_sessions.pop(session_id, None)
    if not session:
        return {"message": "会话不存在或已断开"}
    try:
        session["client"].close()
    except Exception:
        pass
    return {"message": "已断开连接"}


@router.get("/list-paths")
async def list_project_paths(session_id: str = None):
    """Scan common directories on REMOTE server via SSH."""
    if not session_id:
        raise HTTPException(status_code=400, detail="请先连接远程服务器")

    client = _get_ssh_client(session_id)

    loop = asyncio.get_event_loop()

    scan_dirs = ["/www/wwwroot/", "/root/", "/home/"]

    # Build the find command - scan one level of subdirectories
    # Using find with maxdepth 2 to get subdirs within scan_dirs
    dir_checks = " ".join([f'[ -d "{d}" ] && ls -1 "{d}"' for d in scan_dirs])
    command = f"""
SKIP_NAMES="node_modules venv .venv env __pycache__ .git .svn .hg cache tmp temp .cache .local .npm .nvm .pyenv .rbenv .rustup .cargo .config .ssh .aws .docker"
for base in {{" ".join(scan_dirs)}}; do
    if [ -d "$base" ]; then
        for entry in $(ls -1 "$base" 2>/dev/null | sort); do
            # Skip hidden and common non-project dirs
            case "$entry" in
                .*|node_modules|venv|.venv|env|__pycache__|.git|.svn|.hg|cache|tmp|temp|.cache|.local|.npm|.nvm|.pyenv|.rbenv|.rustup|.cargo|.config|.ssh|.aws|.docker)
                    continue
                    ;;
            esac
            if [ -d "$base$entry" ]; then
                echo "$base$entry|$entry"
            fi
        done
    fi
done
""".strip()

    def _scan():
        out, err, code = _exec_ssh_command(client, command, timeout=30)
        results = []
        for line in out.strip().split("\n"):
            line = line.strip()
            if not line or "|" not in line:
                continue
            path, name = line.split("|", 1)
            results.append({"path": path, "name": name})
        return results

    results = await loop.run_in_executor(None, _scan)
    return results


@router.post("/detect")
async def detect_project(req: DetectRequest):
    """Detect project type. If session_id is provided, detect on remote server."""
    project_path = req.path.strip()

    if not project_path:
        raise HTTPException(status_code=400, detail="请输入项目路径")

    if req.session_id:
        # Remote detection via SSH
        client = _get_ssh_client(req.session_id)
        loop = asyncio.get_event_loop()

        # Check if directory exists on remote
        def _check_remote():
            out, _, code = _exec_ssh_command(client, f'[ -d "{project_path}" ] && echo "exists" || echo "not_found"')
            return out.strip()

        result = await loop.run_in_executor(None, _check_remote)
        if result != "exists":
            raise HTTPException(status_code=400, detail=f"远程目录不存在: {project_path}")

        # Collect remote file listing for detection
        def _collect_remote_info():
            # Get file listing
            out, _, _ = _exec_ssh_command(client, f'find "{project_path}" -maxdepth 2 -type f | head -200')
            files = out.strip().split("\n")

            # Get key files content for detection
            info = {"files": files, "path": project_path}

            # Check package.json
            out, _, code = _exec_ssh_command(client, f'[ -f "{project_path}/package.json" ] && cat "{project_path}/package.json"', timeout=10)
            if code == 0:
                info["package.json"] = out

            # Check requirements.txt
            out, _, code = _exec_ssh_command(client, f'[ -f "{project_path}/requirements.txt" ] && cat "{project_path}/requirements.txt"', timeout=10)
            if code == 0:
                info["requirements.txt"] = out

            # Check other indicators
            for fname in ["Dockerfile", "docker-compose.yml", "go.mod", "pom.xml", "build.gradle",
                          "manage.py", "app.py", "main.py", "index.js", "index.ts", "index.php",
                          "composer.json", "Cargo.toml", "Gemfile", "next.config.js", "nuxt.config.js",
                          "vite.config.js", "vite.config.ts", "webpack.config.js", ".env", "README.md"]:
                out, _, code = _exec_ssh_command(
                    client,
                    f'[ -f "{project_path}/{fname}" ] && echo "exists"',
                    timeout=5
                )
                if code == 0 and out.strip() == "exists":
                    info[fname] = "exists"

            return info

        remote_info = await loop.run_in_executor(None, _collect_remote_info)

        # Build a simulated local detection based on remote file info
        project_info = _detect_from_remote_info(remote_info, project_path)
        project_info["project_name"] = os.path.basename(project_path.rstrip("/"))
        project_info["path"] = project_path
        project_info["remote"] = True
        return project_info
    else:
        # Local detection (fallback, same as before)
        if not os.path.isdir(project_path):
            raise HTTPException(status_code=400, detail=f"目录不存在: {project_path}")

        try:
            info = detect_project_type(project_path)
            info["project_name"] = os.path.basename(os.path.abspath(project_path))
            info["path"] = project_path
            return info
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"检测失败: {str(e)}")


def _detect_from_remote_info(remote_info: dict, project_path: str) -> dict:
    """Detect project type based on remote file listing (since we can't use local detect_project_type)."""
    import json

    files = remote_info.get("files", [])
    info = {
        "type": "unknown",
        "framework": None,
        "package_manager": None,
        "has_docker": False,
        "entry_point": None,
        "dependencies": [],
        "remote": True,
    }

    # Check for Docker
    if "Dockerfile" in remote_info or "docker-compose.yml" in remote_info:
        info["has_docker"] = True

    # Check Node.js
    if "package.json" in remote_info:
        try:
            pkg = json.loads(remote_info["package.json"])
            deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
            info["dependencies"] = list(deps.keys())

            # Determine framework
            if "next" in deps:
                info["framework"] = "nextjs"
            elif "nuxt" in deps or "nuxt3" in deps:
                info["framework"] = "nuxtjs"
            elif "react" in deps:
                info["framework"] = "react"
            elif "vue" in deps:
                info["framework"] = "vue"
            elif "@angular/core" in deps:
                info["framework"] = "angular"
            elif "svelte" in deps:
                info["framework"] = "svelte"

            # Determine package manager
            if "vite.config.js" in remote_info or "vite.config.ts" in remote_info:
                info["framework"] = info["framework"] or "vite-project"

            # Package manager detection
            info["package_manager"] = "npm"
            for f in files:
                if "pnpm-lock.yaml" in f:
                    info["package_manager"] = "pnpm"
                    break
                elif "yarn.lock" in f:
                    info["package_manager"] = "yarn"
                    break
                elif "bun.lockb" in f or "bun.lock" in f:
                    info["package_manager"] = "bun"
                    break

            info["type"] = "nodejs"

            # Entry point
            if "next.config.js" in remote_info:
                info["entry_point"] = "next"
            elif "nuxt.config.js" in remote_info:
                info["entry_point"] = "nuxt"
            elif "index.js" in remote_info:
                info["entry_point"] = "index.js"
            elif "index.ts" in remote_info:
                info["entry_point"] = "index.ts"

        except (json.JSONDecodeError, Exception):
            pass

    # Check Python
    if info["type"] == "unknown":
        has_python = False
        for f in files:
            if f.endswith(".py"):
                has_python = True
                break
        if has_python or "requirements.txt" in remote_info:
            info["type"] = "python"

            # Check framework from requirements.txt
            req_content = remote_info.get("requirements.txt", "")
            if "django" in req_content.lower():
                info["framework"] = "django"
            elif "flask" in req_content.lower():
                info["framework"] = "flask"
            elif "fastapi" in req_content.lower():
                info["framework"] = "fastapi"

            # Entry point
            if "manage.py" in remote_info:
                info["entry_point"] = "manage.py"
            elif "app.py" in remote_info:
                info["entry_point"] = "app.py"
            elif "main.py" in remote_info:
                info["entry_point"] = "main.py"

            # Package manager
            info["package_manager"] = "pip"

    # Check Go
    if info["type"] == "unknown" and "go.mod" in remote_info:
        info["type"] = "go"
        info["framework"] = "go"
        info["package_manager"] = "go mod"

    # Check Java
    if info["type"] == "unknown":
        if "pom.xml" in remote_info:
            info["type"] = "java"
            info["framework"] = "maven"
            info["package_manager"] = "maven"
        elif "build.gradle" in remote_info:
            info["type"] = "java"
            info["framework"] = "gradle"
            info["package_manager"] = "gradle"

    # Check PHP
    if info["type"] == "unknown":
        if "composer.json" in remote_info:
            info["type"] = "php"
            info["framework"] = "composer"
            info["package_manager"] = "composer"
        elif "index.php" in remote_info:
            info["type"] = "php"
            info["framework"] = None
            info["entry_point"] = "index.php"

    # Check Rust
    if info["type"] == "unknown" and "Cargo.toml" in remote_info:
        info["type"] = "rust"
        info["package_manager"] = "cargo"

    # Check static site
    if info["type"] == "unknown":
        has_html = False
        for f in files:
            if f.endswith(".html") or f.endswith(".htm"):
                has_html = True
                break
        if has_html:
            info["type"] = "static"

    return info




@router.post("/upload-detect")
async def upload_detect(file: UploadFile = File(...)):
    """上传ZIP项目检测，自动识别项目类型并推荐部署方案"""
    contents = await file.read()
    if len(contents) > 20 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="文件不能超过 20MB")

    if not file.filename or not file.filename.lower().endswith('.zip'):
        raise HTTPException(status_code=400, detail="请上传 .zip 格式文件")

    tmp_dir = tempfile.mkdtemp(prefix="deploy-upload-")
    zip_path = os.path.join(tmp_dir, "upload.zip")
    extract_dir = os.path.join(tmp_dir, "project")

    try:
        with open(zip_path, "wb") as f:
            f.write(contents)

        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(extract_dir)

        # 如果解压后只有一个子目录，使用该子目录作为项目根目录
        entries = os.listdir(extract_dir)
        if len(entries) == 1:
            single_entry = os.path.join(extract_dir, entries[0])
            if os.path.isdir(single_entry):
                extract_dir = single_entry

        # 调用已有的 detect_project_type 检测项目类型
        info = detect_project_type(extract_dir)
        project_name = os.path.basename(os.path.abspath(extract_dir))
        if not project_name or project_name == "project":
            # 使用上传文件名作为项目名
            project_name = os.path.splitext(file.filename)[0]
        info["project_name"] = project_name
        info["path"] = extract_dir
        info["remote"] = False
        info["temp_dir"] = tmp_dir

        # 根据项目类型推荐部署方式
        recommend_deploy = "local"
        try:
            pkg_json = os.path.join(extract_dir, "package.json")
            dockerfile = os.path.join(extract_dir, "Dockerfile")
            req_txt = os.path.join(extract_dir, "requirements.txt")
            app_py = os.path.join(extract_dir, "app.py")
            main_py = os.path.join(extract_dir, "main.py")

            if os.path.isfile(dockerfile):
                recommend_deploy = "docker"
            elif os.path.isfile(pkg_json):
                recommend_deploy = "cloudflare"
            elif os.path.isfile(req_txt) and (os.path.isfile(app_py) or os.path.isfile(main_py)):
                recommend_deploy = "server"
        except Exception:
            pass

        info["recommend_deploy"] = recommend_deploy
        return info
    except zipfile.BadZipFile:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        raise HTTPException(status_code=400, detail="无效的ZIP文件")
    except Exception as e:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=f"上传检测失败: {str(e)}")


@router.post("/generate")
async def generate_script(req: GenerateRequest):
    """Generate deployment script"""
    project_path = req.path.strip()

    if not project_path:
        raise HTTPException(status_code=400, detail="请输入项目路径")

    try:
        # Detect project (remote or local based on session_id)
        if req.session_id:
            client = _get_ssh_client(req.session_id)
            loop = asyncio.get_event_loop()

            # Check directory exists
            def _check():
                out, _, code = _exec_ssh_command(client, f'[ -d "{project_path}" ] && echo "exists" || echo "not_found"')
                return out.strip()

            result = await loop.run_in_executor(None, _check)
            if result != "exists":
                raise HTTPException(status_code=400, detail=f"远程目录不存在: {project_path}")

            # Collect remote info for generate
            def _collect():
                info = {"files": [], "path": project_path}
                for fname in ["package.json", "requirements.txt", "Dockerfile", "docker-compose.yml",
                              "go.mod", "pom.xml", "build.gradle", "manage.py", "app.py", "main.py",
                              "index.js", "index.ts", "index.php", "composer.json", "Cargo.toml",
                              "vite.config.js", "vite.config.ts", "next.config.js"]:
                    out, _, code = _exec_ssh_command(client, f'[ -f "{project_path}/{fname}" ] && cat "{project_path}/{fname}"', timeout=10)
                    if code == 0:
                        info[fname] = out
                return info

            remote_info = await loop.run_in_executor(None, _collect)
            project_info = _detect_from_remote_info(remote_info, project_path)
        elif os.path.isdir(project_path):
            project_info = detect_project_type(project_path)
        else:
            raise HTTPException(status_code=400, detail=f"目录不存在: {project_path}")

        project_name = os.path.basename(project_path.rstrip("/"))
        extra_files = []

        if req.deploy_type == "docker":
            script = generate_dockerfile(project_info)
            filename = "Dockerfile"
        elif req.deploy_type == "cloudflare":
            pm = project_info.get("package_manager") or "npm"
            fw = project_info.get("framework", "")
            output_dir = "dist"
            if fw == "nextjs":
                output_dir = ".next"

            script = f"""#!/bin/bash
# AI Auto Deploy - Cloudflare Pages 部署脚本
# 项目: {project_name}

set -e

echo "🚀 Cloudflare Pages 部署中..."

# 构建
{pm} install --registry=https://registry.npmmirror.com
{pm} run build

# 部署到 Cloudflare Pages
npx wrangler pages deploy {output_dir} --project-name={project_name}

echo "✅ 部署完成！"
"""
            filename = "deploy-cloudflare.sh"
        elif req.deploy_type == "server" and req.server:
            server = req.server
            domain = req.domain or server.get("host", "YOUR_SERVER_IP")
            script = generate_deploy_script(project_info, server, project_name)
            script = script.replace("PROJECT_NAME", project_name)
            filename = "deploy.sh"

            nginx_conf = generate_nginx_config(project_info, domain)
            nginx_conf = nginx_conf.replace("PROJECT_NAME", project_name)
            extra_files.append({"filename": "nginx.conf", "content": nginx_conf})
        else:
            server = {"host": "YOUR_SERVER_IP", "baota": False}
            script = generate_deploy_script(project_info, server, project_name)
            script = script.replace("PROJECT_NAME", project_name)
            filename = "deploy.sh"

        return {
            "script": script,
            "filename": filename,
            "extra_files": extra_files,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成失败: {str(e)}")


@router.post("/execute")
async def execute_deploy(req: dict):
    """Execute deployment (optional, requires server access)"""
    return {
        "message": "远程执行功能需要服务器连接配置，请使用生成的脚本手动部署",
        "status": "not_implemented"
    }


# ============ Remote Deploy (SSE) ============

class RemoteDeployRequest(BaseModel):
    server_index: Optional[int] = None  # Use saved server by index
    # Or provide server info directly
    host: Optional[str] = None
    port: int = 22
    user: str = "root"
    password: Optional[str] = None
    key_content: Optional[str] = None
    script: str  # The deployment script to execute
    project_path: Optional[str] = None
    session_id: Optional[str] = None  # Use SSH session


@router.post("/remote")
async def remote_deploy(req: RemoteDeployRequest):
    """Remote deploy via SSH - returns SSE stream of logs"""
    # If session_id is provided, use the existing SSH session
    if req.session_id:
        session = ssh_sessions.get(req.session_id)
        if not session:
            raise HTTPException(status_code=400, detail="SSH 会话不存在或已过期，请重新连接")
        creds = {
            "host": session["info"]["host"],
            "port": session["info"]["port"],
            "user": session["info"]["username"],
        }
        # Get password/key from session if available
        if "password" in session:
            creds["password"] = session["password"]
        if "key_content" in session:
            creds["key_content"] = session["key_content"]
        # If no password in session, try to get from the stored connect info
        # We need to re-store password in session
        if not creds.get("password") and not creds.get("key_content"):
            creds["password"] = session.get("password")
    elif req.server_index is not None:
        config = load_config()
        servers = config.get("servers", [])
        if req.server_index < 0 or req.server_index >= len(servers):
            raise HTTPException(status_code=400, detail="服务器不存在")
        creds = get_server_credentials(servers[req.server_index])
    elif req.host:
        creds = {
            "host": req.host,
            "port": req.port,
            "user": req.user,
            "password": req.password,
            "key_content": req.key_content,
        }
    else:
        raise HTTPException(status_code=400, detail="请选择服务器或提供服务器信息")

    if not req.script.strip():
        raise HTTPException(status_code=400, detail="部署脚本不能为空")

    return StreamingResponse(
        _stream_deploy(creds, req.script, req.project_path),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


async def _stream_deploy(creds: dict, script: str, project_path: Optional[str] = None):
    """Generator that streams deployment logs via SSE"""

    def _send_event(event_type: str, data: str):
        return f"event: {event_type}\ndata: {data}\n\n"

    # Phase 1: Connecting
    yield _send_event("log", "🔌 正在连接服务器...")
    yield _send_event("status", "connecting")

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        loop = asyncio.get_event_loop()

        def _connect():
            connect_kwargs = {
                "hostname": creds["host"],
                "port": creds.get("port", 22),
                "username": creds.get("user", "root"),
                "timeout": 15,
            }
            key_content = creds.get("key_content")
            password = creds.get("password")

            if key_content:
                key_file_obj = io.StringIO(key_content)
                try:
                    pkey = paramiko.RSAKey.from_private_key(key_file_obj)
                except Exception:
                    key_file_obj = io.StringIO(key_content)
                    try:
                        pkey = paramiko.Ed25519Key.from_private_key(key_file_obj)
                    except Exception:
                        key_file_obj = io.StringIO(key_content)
                        pkey = paramiko.ECDSAKey.from_private_key(key_file_obj)
                connect_kwargs["pkey"] = pkey
            elif password:
                connect_kwargs["password"] = password
            else:
                raise RuntimeError("需要提供密码或密钥")

            client.connect(**connect_kwargs)

        await loop.run_in_executor(None, _connect)
        yield _send_event("log", f"✅ 已连接到 {creds['host']}")
        yield _send_event("status", "connected")

        # Phase 2: Upload script
        yield _send_event("log", "📤 正在上传部署脚本...")
        yield _send_event("status", "uploading")

        def _upload_and_exec():
            remote_script_path = "/tmp/ai-auto-deploy.sh"

            full_script = script
            if project_path:
                full_script = f"cd {project_path}\n{script}"

            if not full_script.startswith("#!"):
                full_script = "#!/bin/bash\nset -e\n\n" + full_script

            sftp = client.open_sftp()
            try:
                with sftp.file(remote_script_path, "w") as f:
                    f.write(full_script)
            finally:
                sftp.close()

            client.exec_command(f"chmod +x {remote_script_path}")

            stdin, stdout, stderr = client.exec_command(
                f"bash {remote_script_path}",
                timeout=600,
            )

            import select
            output_lines = []

            while True:
                if stdout.channel.recv_ready():
                    line = stdout.readline()
                    if line:
                        output_lines.append(("stdout", line.rstrip()))
                if stdout.channel.recv_stderr_ready():
                    line = stderr.readline()
                    if line:
                        output_lines.append(("stderr", line.rstrip()))

                if stdout.channel.exit_status_ready():
                    while stdout.channel.recv_ready():
                        line = stdout.readline()
                        if line:
                            output_lines.append(("stdout", line.rstrip()))
                    while stdout.channel.recv_stderr_ready():
                        line = stderr.readline()
                        if line:
                            output_lines.append(("stderr", line.rstrip()))
                    break

                if not output_lines:
                    import time
                    time.sleep(0.1)

            exit_code = stdout.channel.recv_exit_status()

            client.exec_command(f"rm -f {remote_script_path}")

            return output_lines, exit_code

        results = await loop.run_in_executor(None, _upload_and_exec)
        output_lines, exit_code = results

        yield _send_event("status", "executing")

        for stream_type, line in output_lines:
            if stream_type == "stderr":
                yield _send_event("log", f"⚠️ {line}")
            else:
                yield _send_event("log", line)

        if exit_code == 0:
            yield _send_event("log", "🎉 部署完成！")
            yield _send_event("status", "success")
        else:
            yield _send_event("log", f"❌ 部署失败 (退出码: {exit_code})")
            yield _send_event("status", "failed")

    except Exception as e:
        yield _send_event("log", f"❌ 错误: {str(e)}")
        yield _send_event("status", "error")
    finally:
        try:
            client.close()
        except Exception:
            pass
        yield _send_event("done", "stream_end")

# ============ Remote File Read/Write ============

@router.get("/read-file")
async def read_remote_file(session_id: str, file_path: str):
    """Read a file from remote server via SSH session."""
    if not file_path or not file_path.strip():
        raise HTTPException(status_code=400, detail="请提供文件路径")

    client = _get_ssh_client(session_id)
    loop = asyncio.get_event_loop()

    # Security: basic path validation
    clean_path = file_path.strip().replace(";", "").replace("|", "").replace("&", "")

    def _read():
        # Check if file exists
        out, err, code = _exec_ssh_command(client, f'[ -f "{clean_path}" ] && echo "exists" || echo "not_found"')
        if out.strip() != "exists":
            raise HTTPException(status_code=404, detail=f"文件不存在: {clean_path}")

        # Check if it's a binary file (skip common binary extensions)
        binary_exts = (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".svg",
                       ".zip", ".tar", ".gz", ".rar", ".7z", ".exe", ".bin",
                       ".so", ".dll", ".pyc", ".class", ".jar", ".war")
        if any(clean_path.lower().endswith(ext) for ext in binary_exts):
            raise HTTPException(status_code=400, detail="不支持读取二进制文件")

        # Read file content (limit to 2MB to avoid memory issues)
        out, err, code = _exec_ssh_command(
            client,
            f'head -c 2097152 "{clean_path}"',
            timeout=30,
        )
        # Check for binary content (null bytes)
        if "\x00" in out:
            raise HTTPException(status_code=400, detail="该文件为二进制文件，不支持在线编辑")

        return out

    content = await loop.run_in_executor(None, _read)

    # Get file info
    def _stat():
        out, _, _ = _exec_ssh_command(client, f'stat -c "%s|%y" "{clean_path}" 2>/dev/null || stat -f "%z|%Sm" "{clean_path}" 2>/dev/null')
        return out.strip()

    stat_info = await loop.run_in_executor(None, _stat)
    file_size = ""
    file_mtime = ""
    if "|" in stat_info:
        parts = stat_info.split("|", 1)
        file_size = parts[0]
        file_mtime = parts[1].strip()

    return {
        "file_path": clean_path,
        "content": content,
        "file_size": file_size,
        "file_mtime": file_mtime,
    }


@router.post("/write-file")
async def write_remote_file(request: Request):
    """Write content to a file on remote server via SSH session."""
    body = await request.json()
    session_id = body.get("session_id", "")
    file_path = body.get("file_path", "")
    content = body.get("content", "")

    if not session_id:
        raise HTTPException(status_code=400, detail="缺少 session_id")
    if not file_path or not file_path.strip():
        raise HTTPException(status_code=400, detail="请提供文件路径")

    client = _get_ssh_client(session_id)
    loop = asyncio.get_event_loop()

    clean_path = file_path.strip().replace(";", "").replace("|", "").replace("&", "")

    def _write():
        # Create backup first
        _exec_ssh_command(client, f'cp "{clean_path}" "{clean_path}.bak" 2>/dev/null')

        # Write content using heredoc to handle special characters
        import base64
        encoded = base64.b64encode(content.encode("utf-8")).decode("ascii")
        cmd = f'echo "{encoded}" | base64 -d > "{clean_path}"'
        out, err, code = _exec_ssh_command(client, cmd, timeout=30)

        if code != 0:
            raise HTTPException(status_code=500, detail=f"写入失败: {err}")

        return True

    result = await loop.run_in_executor(None, _write)

    return {
        "success": True,
        "file_path": clean_path,
        "message": f"文件 {clean_path} 已成功保存（已自动备份为 {clean_path}.bak）",
    }
