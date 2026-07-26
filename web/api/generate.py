"""
Generate Project API routes - AI 自动生成项目代码
"""

import os
import re
import io
import json
import asyncio
import zipfile
import tempfile
import shutil
from typing import Optional

import requests
import paramiko
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from web.database import is_paid, get_user_credits, deduct_credits
from web.api.servers import get_server_credentials, load_config

router = APIRouter()

# 豆包 AI 配置
ARK_API_KEY = os.environ.get("ARK_API_KEY", "")
DOUBAO_ENDPOINT = "https://ark.cn-beijing.volces.com/api/v3"
DOUBAO_MODEL_ID = "ep-20260707225043-z7nkm"

# 积分消耗配置
CREDIT_COST_GENERATE = 500
CREDIT_COST_MODIFY = 300

# 技术栈模板
TECH_STACKS = {
    "frontend": {
        "vue3": {"label": "Vue 3 + Vite", "desc": "Vue 3 组合式 API + Vite 构建工具"},
        "react": {"label": "React 18", "desc": "React 18 + Hooks + Vite"},
        "html": {"label": "原生 HTML/CSS/JS", "desc": "纯前端，无框架依赖"},
    },
    "backend": {
        "fastapi": {"label": "FastAPI", "desc": "Python 异步框架，自动生成 API 文档"},
        "flask": {"label": "Flask", "desc": "Python 轻量级 Web 框架"},
        "express": {"label": "Express.js", "desc": "Node.js 最小化 Web 框架"},
    },
    "fullstack": {
        "nextjs": {"label": "Next.js", "desc": "React 全栈框架，支持 SSR/SSG"},
        "nuxtjs": {"label": "Nuxt.js", "desc": "Vue 全栈框架，支持 SSR/SSG"},
    },
}


# ============ Models ============

class GenerateProjectRequest(BaseModel):
    description: str
    project_type: str  # "frontend" | "backend" | "fullstack"
    tech_stack: str    # e.g. "vue3", "react", "fastapi", etc.
    user_id: Optional[str] = None


class GenerateFileItem(BaseModel):
    filename: str
    content: str


class DownloadProjectRequest(BaseModel):
    files: list[GenerateFileItem]
    project_name: Optional[str] = None


class ModifyCodeDownloadRequest(BaseModel):
    files: list[dict]


# ============ AI 调用 ============

def call_doubao_api(messages: list, temperature: float = 0.3) -> str:
    """调用豆包 API"""
    try:
        response = requests.post(
            f"{DOUBAO_ENDPOINT}/chat/completions",
            headers={
                "Authorization": f"Bearer {ARK_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": DOUBAO_MODEL_ID,
                "messages": messages,
                "temperature": temperature,
            },
            timeout=180,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="AI 生成超时，请稍后重试")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 调用失败: {str(e)}")


def parse_generated_files(content: str) -> list:
    """从 AI 返回的内容中解析文件列表"""
    files = []

    # Pattern 1: === filename ===
    pattern1 = re.compile(r'={3,}\s*(.+?)\s*={3,}\s*\n(.*?)(?={3,}\s*.+?\s*={3,}|\Z)', re.DOTALL)
    matches = pattern1.findall(content)
    if matches:
        for filename, file_content in matches:
            files.append({"filename": filename.strip(), "content": file_content.strip()})
        return files

    # Pattern 2: ```lang:filename
    pattern2 = re.compile(r'```(\w+):([^\n`]+)\n(.*?)```', re.DOTALL)
    matches = pattern2.findall(content)
    if matches:
        for lang, filename, file_content in matches:
            files.append({"filename": filename.strip(), "content": file_content.strip()})
        return files

    # Pattern 3: ## filename
    pattern3 = re.compile(r'^##\s+(.+?)\s*\n```[\w]*\n(.*?)```', re.DOTALL | re.MULTILINE)
    matches = pattern3.findall(content)
    if matches:
        for filename, file_content in matches:
            files.append({"filename": filename.strip(), "content": file_content.strip()})
        return files

    # Fallback
    if content.strip():
        files.append({"filename": "README.md", "content": content.strip()})

    return files


def build_prompt(description: str, project_type: str, tech_stack: str) -> str:
    """构建 AI 生成 prompt"""
    stack_info = TECH_STACKS.get(project_type, {}).get(tech_stack, {})
    stack_label = stack_info.get("label", tech_stack)
    stack_desc = stack_info.get("desc", "")

    type_labels = {"frontend": "前端", "backend": "后端", "fullstack": "全栈"}
    type_label = type_labels.get(project_type, project_type)

    prompt = (
        "你是一个专业的项目代码生成器。请根据以下需求生成完整的项目代码。\n\n"
        "## 需求\n"
        f"- 项目描述: {description}\n"
        f"- 项目类型: {type_label}\n"
        f"- 技术栈: {stack_label} ({stack_desc})\n\n"
        "## 输出格式要求\n"
        "你必须严格按照以下格式输出每个文件：\n\n"
        "=== 文件路径/文件名 ===\n"
        "文件完整内容\n\n"
        "每个文件之间用 === 文件名 === 分隔。\n\n"
        "## 生成要求\n"
        "1. 生成完整、可运行的项目代码\n"
        "2. 包含必要的配置文件（package.json / requirements.txt 等）\n"
        "3. 包含 README.md 说明文件\n"
        "4. 代码要有适当的注释\n"
        "5. 确保项目结构合理\n"
        f"6. {type_label}项目至少包含 3-5 个文件\n"
        "7. 所有代码必须是完整的，不能有占位符或 TODO\n"
    )
    return prompt


# ============ Routes ============

@router.post("/project")
async def generate_project(req: GenerateProjectRequest):
    """AI 生成项目"""
    # Check credits
    if req.user_id:
        credits = get_user_credits(req.user_id)
        if credits < CREDIT_COST_GENERATE:
            raise HTTPException(
                status_code=402,
                detail=f"积分不足，生成项目需要 {CREDIT_COST_GENERATE} 积分，当前余额 {credits} 积分，请充值",
            )

    if not req.description.strip():
        raise HTTPException(status_code=400, detail="请输入项目描述")

    if req.project_type not in TECH_STACKS:
        raise HTTPException(status_code=400, detail="无效的项目类型")

    valid_stacks = list(TECH_STACKS[req.project_type].keys())
    if req.tech_stack not in valid_stacks:
        raise HTTPException(
            status_code=400,
            detail=f"无效的技术栈，可选: {', '.join(valid_stacks)}",
        )

    # Build prompt and call AI
    prompt = build_prompt(req.description, req.project_type, req.tech_stack)
    messages = [
        {
            "role": "system",
            "content": (
                "你是一个专业的项目代码生成器。你只输出代码文件，每个文件用 "
                "=== 文件路径/文件名 === 分隔。不要输出任何多余的解释文字。"
                "只输出格式化的文件内容，确保每个文件都是完整可运行的。"
            ),
        },
        {"role": "user", "content": prompt},
    ]

    content = call_doubao_api(messages, temperature=0.3)
    files = parse_generated_files(content)

    if not files:
        raise HTTPException(status_code=500, detail="AI 生成结果为空，请重试")

    # Deduct credits after success
    if req.user_id:
        deduct_credits(req.user_id, CREDIT_COST_GENERATE, "生成项目")

    return {
        "files": files,
        "total": len(files),
        "description": req.description,
        "project_type": req.project_type,
        "tech_stack": req.tech_stack,
        "credits_cost": CREDIT_COST_GENERATE,
        "credits_remaining": get_user_credits(req.user_id) if req.user_id else None,
    }


@router.get("/stacks")
async def get_stacks():
    """获取可用技术栈"""
    return {"stacks": TECH_STACKS}



@router.post("/modify-code")
async def modify_code(
    file: UploadFile = File(...),
    description: str = Form(...),
    user_id: str = Form(default=""),
):
    """AI 修改整个项目源码包"""
    # Check credits
    if user_id:
        credits = get_user_credits(user_id)
        if credits < CREDIT_COST_MODIFY:
            raise HTTPException(
                status_code=402,
                detail=f"积分不足，修改代码需要 {CREDIT_COST_MODIFY} 积分，当前余额 {credits} 积分，请充值",
            )

    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="文件不能超过 5MB")

    if not description.strip():
        raise HTTPException(status_code=400, detail="请输入修改需求")

    tmp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(tmp_dir, "upload.zip")
    code_files = []

    try:
        with open(zip_path, "wb") as f:
            f.write(contents)

        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(tmp_dir)

        code_exts = {".py", ".js", ".ts", ".vue", ".html", ".css", ".json", ".java",
                     ".go", ".php", ".rb", ".jsx", ".tsx", ".yaml", ".yml", ".toml",
                     ".cfg", ".ini", ".sh", ".sql", ".xml", ".md", ".c", ".cpp", ".h"}
        skip_dirs = {"node_modules", "__pycache__", ".git", "dist", "build", ".venv",
                     "venv", ".next", ".nuxt", "target", ".idea", ".vscode"}

        for root, dirs, files in os.walk(tmp_dir):
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            for fname in files:
                ext = os.path.splitext(fname)[1].lower()
                if ext in code_exts:
                    fpath = os.path.join(root, fname)
                    rel_path = os.path.relpath(fpath, tmp_dir)
                    try:
                        with open(fpath, "r", encoding="utf-8") as cf:
                            file_content = cf.read()
                        if file_content.strip():
                            code_files.append({"path": rel_path, "content": file_content})
                    except Exception:
                        pass

        if not code_files:
            raise HTTPException(status_code=400, detail="ZIP 中未找到代码文件")

        total_chars = 0
        selected_files = []
        for f in sorted(code_files, key=lambda x: len(x["content"]), reverse=True)[:20]:
            if total_chars + len(f["content"]) > 25000:
                break
            selected_files.append(f)
            total_chars += len(f["content"])

        files_text = ""
        for f in selected_files:
            files_text += f"\n=== {f['path']} ===\n{f['content']}\n"

        messages = [
            {
                "role": "system",
                "content": (
                    "你是一个专业的全栈代码修改助手。用户会上传项目源码并描述需要修改的内容。\n"
                    "你需要分析整个项目结构，理解代码逻辑，然后根据用户描述进行修改。\n\n"
                    "要求：\n"
                    "1. 只返回被修改的文件的完整内容\n"
                    "2. 以 JSON 数组格式返回：[{\"filename\": \"文件路径\", \"content\": \"修改后的完整代码\"}]\n"
                    "3. 保持原有代码风格和缩进\n"
                    "4. 只返回 JSON 数组，不要返回任何解释文字"
                ),
            },
            {
                "role": "user",
                "content": f"修改需求：{description}\n\n以下是项目文件内容：\n{files_text}",
            },
        ]

        result = call_doubao_api(messages, temperature=0.3)

        try:
            json_match = re.search(r"\[[\s\S]*\]", result)
            if json_match:
                modified_files = json.loads(json_match.group())
            else:
                modified_files = []
        except json.JSONDecodeError:
            modified_files = []

        if not modified_files:
            raise HTTPException(status_code=500, detail="AI 未能生成有效的修改结果，请尝试更具体的描述")

        response_files = []
        for mf in modified_files:
            if not isinstance(mf, dict) or "filename" not in mf:
                continue
            original = ""
            for sf in selected_files:
                if sf["path"] == mf["filename"]:
                    original = sf["content"]
                    break
            response_files.append({
                "filename": mf["filename"],
                "original": original,
                "modified": mf.get("content", ""),
            })

        # Deduct credits after success
        if user_id:
            deduct_credits(user_id, CREDIT_COST_MODIFY, "修改代码")

        return {
            "files": response_files,
            "credits_cost": CREDIT_COST_MODIFY,
            "credits_remaining": get_user_credits(user_id) if user_id else None,
        }

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


@router.post("/download")
async def download_project(req: DownloadProjectRequest):
    """下载生成的项目为 zip"""
    if not req.files:
        raise HTTPException(status_code=400, detail="没有可下载的文件")

    project_name = req.project_name or "generated-project"

    tmp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(tmp_dir, f"{project_name}.zip")

    try:
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in req.files:
                zf.writestr(f.filename, f.content)

        return FileResponse(
            zip_path,
            media_type="application/zip",
            filename=f"{project_name}.zip",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"打包失败: {str(e)}")


@router.post("/modify-code/download")
async def download_modified(req: ModifyCodeDownloadRequest):
    """下载修改后的项目为 ZIP"""
    if not req.files:
        raise HTTPException(status_code=400, detail="没有可下载的文件")

    tmp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(tmp_dir, "modified-project.zip")

    try:
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in req.files:
                content = f.get("modified") or f.get("original", "")
                if content:
                    zf.writestr(f["filename"], content)

        def iter_file():
            with open(zip_path, "rb") as fh:
                yield from fh

        return StreamingResponse(
            iter_file(),
            media_type="application/zip",
            headers={"Content-Disposition": "attachment; filename=modified-project.zip"},
        )
    finally:
        pass

@router.post("/save-to-server")
async def save_to_server(req: dict):
    """将生成的项目保存到远程服务器"""
    files = req.get("files", [])
    server_id = req.get("server_id", "")
    target_path = req.get("target_path", "").strip()
    user_id = req.get("user_id", "")

    if not files:
        raise HTTPException(status_code=400, detail="没有可保存的文件")
    if not target_path:
        raise HTTPException(status_code=400, detail="请输入目标路径")
    if not server_id:
        raise HTTPException(status_code=400, detail="请选择服务器")

    # 获取服务器配置
    config = load_config()
    servers = config.get("servers", [])
    server_index = None

    # server_id 可以是索引或host
    try:
        server_index = int(server_id)
    except ValueError:
        for i, s in enumerate(servers):
            if s.get("host") == server_id:
                server_index = i
                break

    if server_index is None or server_index >= len(servers):
        raise HTTPException(status_code=400, detail="服务器不存在")

    creds = get_server_credentials(servers[server_index])

    # SSH 连接并上传文件
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    loop = asyncio.get_event_loop()

    def _connect_and_upload():
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

        # 创建目标目录
        sftp = client.open_sftp()
        try:
            # 递归创建目录
            dirs_to_create = set()
            for f in files:
                filepath = f.get("filename", "")
                dirpath = os.path.dirname(filepath)
                if dirpath:
                    full_remote_dir = os.path.join(target_path, dirpath)
                    dirs_to_create.add(full_remote_dir)

            # 先创建目标根目录
            _remote_mkdir_p(sftp, target_path)

            # 创建子目录
            for d in sorted(dirs_to_create, key=len):
                _remote_mkdir_p(sftp, d)

            # 写入文件
            saved_count = 0
            for f in files:
                filepath = f.get("filename", "")
                file_content = f.get("content", "")
                if filepath:
                    remote_file_path = os.path.join(target_path, filepath)
                    with sftp.file(remote_file_path, "w") as rf:
                        rf.write(file_content)
                    saved_count += 1

            return saved_count
        finally:
            sftp.close()

    def _remote_mkdir_p(sftp, remote_dir):
        """递归创建远程目录"""
        if remote_dir == "/" or remote_dir == "":
            return
        try:
            sftp.stat(remote_dir)
        except FileNotFoundError:
            parent = os.path.dirname(remote_dir)
            _remote_mkdir_p(sftp, parent)
            try:
                sftp.mkdir(remote_dir)
            except IOError:
                pass  # 目录可能已存在

    try:
        saved_count = await loop.run_in_executor(None, _connect_and_upload)
        return {
            "success": True,
            "message": f"成功保存 {saved_count} 个文件到 {creds['host']}:{target_path}",
            "server": creds["host"],
            "path": target_path,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存失败: {str(e)}")
    finally:
        client.close()
