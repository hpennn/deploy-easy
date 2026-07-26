"""
CLI 入口 - 交互式命令行界面
"""

import os
import sys
import json
import subprocess
from pathlib import Path

# ============ 项目类型检测 ============

def detect_project_type(project_dir: str) -> dict:
    """自动检测项目类型"""
    files = set(os.listdir(project_dir))
    
    result = {
        "type": "unknown",
        "framework": None,
        "has_docker": "Dockerfile" in files or "docker-compose.yml" in files,
        "package_manager": None,
        "entry_point": None,
    }
    
    # Python 项目
    if "requirements.txt" in files or "pyproject.toml" in files:
        result["type"] = "python"
        result["package_manager"] = "pip"
        
        # 检测框架
        req_file = os.path.join(project_dir, "requirements.txt")
        if os.path.exists(req_file):
            with open(req_file) as f:
                content = f.read().lower()
                if "fastapi" in content:
                    result["framework"] = "fastapi"
                    result["entry_point"] = "main:app"
                elif "flask" in content:
                    result["framework"] = "flask"
                    result["entry_point"] = "app:app"
                elif "django" in content:
                    result["framework"] = "django"
        
        # 检查 pyproject.toml
        if "pyproject.toml" in files:
            with open(os.path.join(project_dir, "pyproject.toml")) as f:
                content = f.read().lower()
                if "fastapi" in content:
                    result["framework"] = "fastapi"
    
    # Node.js 项目
    elif "package.json" in files:
        result["type"] = "nodejs"
        with open(os.path.join(project_dir, "package.json")) as f:
            pkg = json.load(f)
        
        deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
        
        if "next" in deps:
            result["framework"] = "nextjs"
        elif "nuxt" in deps:
            result["framework"] = "nuxtjs"
        elif "astro" in deps:
            result["framework"] = "astro"
        elif "react" in deps:
            result["framework"] = "react"
        elif "vue" in deps:
            result["framework"] = "vue"
        elif "@angular/core" in deps:
            result["framework"] = "angular"
        elif "vite" in deps:
            result["framework"] = "vite-static"
        else:
            result["framework"] = "nodejs-static"
        
        # 判断包管理器
        if "pnpm-lock.yaml" in files:
            result["package_manager"] = "pnpm"
        elif "yarn.lock" in files:
            result["package_manager"] = "yarn"
        elif "bun.lockb" in files:
            result["package_manager"] = "bun"
        else:
            result["package_manager"] = "npm"
    
    # 纯静态站点
    elif "index.html" in files:
        result["type"] = "static"
        result["framework"] = "html"
    
    return result


# ============ 配置管理 ============

CONFIG_FILE = os.path.expanduser("~/.ai-deploy.json")

def load_config() -> dict:
    """加载全局配置"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            return json.load(f)
    return {"servers": [], "defaults": {}}

def save_config(config: dict):
    """保存全局配置"""
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

def interactive_config() -> dict:
    """交互式配置"""
    config = load_config()
    
    print("\n🔧 AI Auto Deploy - 初始配置")
    print("=" * 40)
    
    if not config["servers"]:
        print("\n📡 添加服务器（可添加多个）")
        while True:
            server = {}
            server["name"] = input("  服务器名称（如：阿里云）: ").strip()
            server["host"] = input("  服务器IP: ").strip()
            server["port"] = input("  SSH端口 [22]: ").strip() or "22"
            server["user"] = input("  SSH用户名 [root]: ").strip() or "root"
            
            key_path = input("  SSH密钥路径（留空用密码）: ").strip()
            if key_path:
                server["key_file"] = key_path
            else:
                server["password"] = input("  SSH密码: ").strip()
            
            # 检测宝塔面板
            has_baota = input("  是否使用宝塔面板？[y/N]: ").strip().lower()
            if has_baota == 'y':
                server["baota"] = True
                server["baota_port"] = input("  宝塔面板端口 [8888]: ").strip() or "8888"
                server["baota_path"] = input("  宝塔面板路径 [如: /abc123]: ").strip()
            
            config["servers"].append(server)
            
            more = input("\n  添加更多服务器？[y/N]: ").strip().lower()
            if more != 'y':
                break
    
    # 默认部署目标
    if config["servers"]:
        print("\n🎯 默认部署目标：")
        for i, s in enumerate(config["servers"]):
            print(f"  [{i}] {s['name']} ({s['host']})")
        default = input(f"  选择默认服务器 [0]: ").strip() or "0"
        config["defaults"]["server"] = int(default)
    
    save_config(config)
    print("\n✅ 配置已保存到", CONFIG_FILE)
    return config


# ============ 部署脚本生成 ============

def generate_deploy_script(project_info: dict, server: dict, project_name: str) -> str:
    """生成一键部署脚本"""
    
    fw = project_info["framework"]
    ptype = project_info["type"]
    has_baota = server.get("baota", False)
    
    # 基础环境准备
    script = f'''#!/bin/bash
# ============================================================
# AI Auto Deploy - 自动生成部署脚本
# 项目: {project_name}
# 类型: {ptype} / {fw}
# 目标: {server['host']}
# 生成时间: $(date)
# ============================================================

set -e

RED='\\033[0;31m'
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
NC='\\033[0m'

log() {{ echo -e "${{GREEN}}[✓]${{NC}} $1"; }}
warn() {{ echo -e "${{YELLOW}}[!]${{NC}} $1"; }}
err() {{ echo -e "${{RED}}[✗]${{NC}} $1"; exit 1; }}

APP_DIR="/www/wwwroot/{project_name}"
REPO_URL=""  # 从 GitHub 克隆时填写

echo "=========================================="
echo "  🚀 AI Auto Deploy - {project_name}"
echo "=========================================="

# ---- 1. 环境检查 ----
echo ""
echo ">>> 步骤 1/5: 环境检查"
'''
    
    # Python 项目
    if ptype == "python":
        script += f'''
# Python 环境
if ! command -v python3 &>/dev/null; then
    warn "安装 Python 3..."
    apt-get update && apt-get install -y python3 python3-pip python3-venv 2>/dev/null || \\
    yum install -y python3 python3-pip
fi
PY_VER=$(python3 -c 'import sys; print(f"{{sys.version_info.major}}.{{sys.version_info.minor}}")')
log "Python $PY_VER"
'''
    
    # Node.js 项目
    if ptype == "nodejs" or fw in ("astro", "nextjs", "nuxtjs", "vite-static", "react", "vue"):
        script += '''
# Node.js 环境
if ! command -v node &>/dev/null; then
    warn "安装 Node.js 18..."
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash - 2>/dev/null
    apt-get install -y nodejs 2>/dev/null || yum install -y nodejs 2>/dev/null
fi
log "Node.js $(node -v)"
'''

    script += f'''
# PM2 进程管理
if ! command -v pm2 &>/dev/null; then
    npm install -g pm2 2>/dev/null || pip3 install pm2 2>/dev/null
    log "PM2 已安装"
fi

# ---- 2. 获取代码 ----
echo ""
echo ">>> 步骤 2/5: 获取代码"
if [ -d "$APP_DIR" ]; then
    cd "$APP_DIR"
    git pull 2>/dev/null && log "代码更新完成" || warn "git pull 失败"
else
    if [ -n "$REPO_URL" ]; then
        git clone "$REPO_URL" "$APP_DIR"
        log "代码已克隆到 $APP_DIR"
    else
        err "请先将代码上传到 $APP_DIR 或设置 REPO_URL"
    fi
fi

cd "$APP_DIR"
'''

    # Python 后端部署
    if ptype == "python":
        script += f'''
# ---- 3. 安装依赖 ----
echo ""
echo ">>> 步骤 3/5: 安装依赖"
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
log "依赖安装完成"

# ---- 4. 启动后端 ----
echo ""
echo ">>> 步骤 4/5: 启动服务"
'''
        if fw == "fastapi":
            script += '''
# 创建 ecosystem 配置
cat > ecosystem.config.js << PM2EOF
module.exports = {
  apps: [{
    name: 'APP_NAME',
    script: 'venv/bin/uvicorn',
    args: 'main:app --host 127.0.0.1 --port 8000 --workers 2',
    cwd: 'APP_DIR',
    interpreter: 'none',
    max_memory_restart: '500M'
  }]
};
PM2EOF

# 替换占位符
sed -i "s|APP_NAME|PROJECT_NAME|g" ecosystem.config.js
sed -i "s|APP_DIR|$APP_DIR|g" ecosystem.config.js

pm2 delete PROJECT_NAME 2>/dev/null || true
pm2 start ecosystem.config.js
pm2 save
log "FastAPI 服务已启动"
'''
        elif fw == "flask":
            script += '''
cat > ecosystem.config.js << PM2EOF
module.exports = {
  apps: [{
    name: 'PROJECT_NAME',
    script: 'venv/bin/gunicorn',
    args: '-w 2 -b 127.0.0.1:8000 app:app',
    cwd: 'APP_DIR',
    interpreter: 'none',
    max_memory_restart: '500M'
  }]
};
PM2EOF

sed -i "s|APP_DIR|$APP_DIR|g" ecosystem.config.js
pm2 delete PROJECT_NAME 2>/dev/null || true
pm2 start ecosystem.config.js
pm2 save
log "Flask 服务已启动"
'''

    # Node.js/前端项目
    elif ptype == "nodejs":
        script += f'''
# ---- 3. 安装依赖 ----
echo ""
echo ">>> 步骤 3/5: 安装依赖"
'''
        pm = project_info["package_manager"]
        script += f'''
{pm} install --registry=https://registry.npmmirror.com
log "依赖安装完成"
'''
        
        # 检查是否需要构建
        if fw in ("astro", "nextjs", "nuxtjs", "vite-static", "react", "vue"):
            script += f'''
# ---- 4. 构建前端 ----
echo ""
echo ">>> 步骤 4/5: 构建前端"
{pm} run build
log "构建完成 → dist/"

# 如果是 SSR 框架（Next.js/Nuxt），用 PM2 管理
'''
            if fw in ("nextjs", "nuxtjs"):
                script += f'''
cat > ecosystem.config.js << PM2EOF
module.exports = {{
  apps: [{{
    name: 'PROJECT_NAME',
    script: 'node_modules/.bin/{pm == "pnpm" and "pnpm" or "npx"}',
    args: '{fw == "nextjs" and "next start -p 3000" or "nuxt start"}',
    cwd: 'APP_DIR',
    max_memory_restart: '500M'
  }}]
}};
PM2EOF

sed -i "s|APP_DIR|$APP_DIR|g" ecosystem.config.js
pm2 delete PROJECT_NAME 2>/dev/null || true
pm2 start ecosystem.config.js
pm2 save
log "{fw} 服务已启动"
'''
            else:
                script += '''
log "静态站点，只需 Nginx 配置即可"
'''
        else:
            # 纯 Node.js 后端
            script += '''
# 检查启动脚本
cat > ecosystem.config.js << PM2EOF
module.exports = {
  apps: [{
    name: 'PROJECT_NAME',
    script: 'index.js',
    cwd: 'APP_DIR',
    max_memory_restart: '500M'
  }]
};
PM2EOF

sed -i "s|APP_DIR|$APP_DIR|g" ecosystem.config.js
pm2 delete PROJECT_NAME 2>/dev/null || true
pm2 start ecosystem.config.js
pm2 save
log "Node.js 服务已启动"
'''

    # Nginx 配置
    script += f'''
# ---- 5. 配置 Nginx ----
echo ""
echo ">>> 步骤 5/5: 配置 Nginx"

SERVER_HOST="{server['host']}"
'''

    if has_baota:
        script += '''
NGINX_CONF="/www/server/panel/vhost/nginx/${PROJECT_NAME}.conf"
if [ -d "/www/server/panel/vhost/nginx" ]; then
    echo "  宝塔面板 Nginx 配置目录已找到"
else
    warn "未找到宝塔 Nginx 目录，请在宝塔面板手动添加站点"
fi
'''
    
    script += '''
# 生成 Nginx 配置
# 根据项目类型自动选择配置模板
# （实际使用时根据项目类型填写具体的 location 块）

echo ""
echo "=========================================="
echo -e "  ${GREEN}🎉 部署完成！${NC}"
echo "=========================================="
echo ""
echo "  访问地址: http://$SERVER_HOST"
echo ""
echo "  管理命令:"
echo "    pm2 status              # 查看状态"
echo "    pm2 logs PROJECT_NAME   # 查看日志"
echo "    pm2 restart PROJECT_NAME # 重启"
echo ""
'''
    
    return script


# ============ Nginx 配置生成 ============

def generate_nginx_config(project_info: dict, domain: str, port: int = 8000) -> str:
    """生成 Nginx 配置"""
    fw = project_info["framework"]
    ptype = project_info["type"]
    
    if ptype == "python":
        return f'''server {{
    listen 80;
    server_name {domain};

    # 后端 API 代理
    location / {{
        proxy_pass http://127.0.0.1:{port};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
    }}
}}'''
    
    elif fw in ("astro", "vite-static", "react", "vue", "html"):
        return f'''server {{
    listen 80;
    server_name {domain};
    root /www/wwwroot/PROJECT_NAME/dist;
    index index.html;

    location / {{
        try_files $uri $uri/ /index.html;
    }}

    # 静态资源缓存
    location ~* \\.(js|css|png|jpg|jpeg|gif|ico|svg|woff2?)$ {{
        expires 30d;
        add_header Cache-Control "public, immutable";
    }}
}}'''
    
    elif fw == "nextjs":
        return f'''server {{
    listen 80;
    server_name {domain};

    location / {{
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }}
}}'''
    
    return f'''server {{
    listen 80;
    server_name {domain};
    
    location / {{
        proxy_pass http://127.0.0.1:{port};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }}
}}'''


# ============ Dockerfile 生成 ============

def generate_dockerfile(project_info: dict) -> str:
    """生成 Dockerfile"""
    ptype = project_info["type"]
    fw = project_info["framework"]
    
    if ptype == "python":
        expose_line = "EXPOSE 8000" if fw == "fastapi" else "EXPOSE 5000"
        if fw == "fastapi":
            cmd_line = 'CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]'
        else:
            cmd_line = 'CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000"]'
        return f'''FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
COPY . .

{expose_line}

{cmd_line}
'''
    
    elif ptype == "nodejs":
        pm = project_info["package_manager"] or "npm"
        if fw in ("nextjs", "nuxtjs"):
            return f'''FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN {pm} install
COPY . .
RUN {pm} run build
EXPOSE 3000
CMD ["{pm}", "start"]
'''
        else:
            return f'''FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN {pm} install
COPY . .
RUN {pm} run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80
'''
    
    return '''FROM nginx:alpine
COPY . /usr/share/nginx/html
EXPOSE 80
'''


# ============ 主流程 ============

def main():
    """主入口"""
    print("""
╔══════════════════════════════════════╗
║       🚀 AI Auto Deploy v1.0        ║
║    智能识别 · 一键部署 · 多平台支持    ║
╚══════════════════════════════════════╝
    """)
    
    # 检查是否已有配置
    config = load_config()
    if not config["servers"]:
        print("📡 首次使用，请先配置服务器信息")
        config = interactive_config()
    
    # 选择项目目录
    project_dir = input("\n📁 项目目录路径（默认当前目录）: ").strip() or os.getcwd()
    
    if not os.path.isdir(project_dir):
        print(f"❌ 目录不存在: {project_dir}")
        sys.exit(1)
    
    # 检测项目类型
    print(f"\n🔍 检测项目类型...")
    project_info = detect_project_type(project_dir)
    
    project_name = os.path.basename(os.path.abspath(project_dir))
    
    print(f"  📦 项目名: {project_name}")
    print(f"  🏗️  类型: {project_info['type']}")
    print(f"  🔧 框架: {project_info['framework']}")
    print(f"  📋 包管理: {project_info['package_manager']}")
    
    # 选择部署目标
    print("\n🎯 选择部署目标：")
    print("  [0] 云服务器（SSH）")
    print("  [1] Cloudflare Pages")
    print("  [2] 生成本地部署脚本")
    print("  [3] 生成 Docker 部署")
    
    choice = input("  选择 [0]: ").strip() or "0"
    
    if choice == "0":
        # SSH 部署
        if not config["servers"]:
            print("❌ 没有配置服务器，请先运行: python deploy.py config")
            sys.exit(1)
        
        print("\n  可用服务器：")
        for i, s in enumerate(config["servers"]):
            print(f"  [{i}] {s['name']} ({s['host']})")
        
        server_idx = input("  选择服务器 [0]: ").strip() or "0"
        server = config["servers"][int(server_idx)]
        
        domain = input(f"  访问域名/IP [{server['host']}]: ").strip() or server["host"]
        
        # 生成部署脚本
        script = generate_deploy_script(project_info, server, project_name)
        script = script.replace("PROJECT_NAME", project_name)
        
        script_path = os.path.join(project_dir, "deploy.sh")
        with open(script_path, "w") as f:
            f.write(script)
        os.chmod(script_path, 0o755)
        
        print(f"\n✅ 部署脚本已生成: {script_path}")
        print(f"\n🚀 部署方式：")
        print(f"  1. 复制脚本到服务器: scp {script_path} {server['user']}@{server['host']}:/tmp/")
        print(f"  2. SSH登录执行: ssh {server['user']}@{server['host']} 'bash /tmp/deploy.sh'")
        print(f"\n  或者直接在服务器上粘贴运行脚本内容。")
        
        # 生成 Nginx 配置
        nginx_conf = generate_nginx_config(project_info, domain)
        nginx_conf = nginx_conf.replace("PROJECT_NAME", project_name)
        nginx_path = os.path.join(project_dir, "nginx.conf")
        with open(nginx_path, "w") as f:
            f.write(nginx_conf)
        print(f"  Nginx 配置已生成: {nginx_path}")
    
    elif choice == "1":
        # Cloudflare 部署
        print("\n☁️  Cloudflare Pages 部署")
        print("  确保已安装 Wrangler CLI: npm install -g wrangler")
        
        # 检查是否有 wrangler.toml
        wrangler_path = os.path.join(project_dir, "wrangler.toml")
        if not os.path.exists(wrangler_path):
            cf_project = input(f"  Cloudflare 项目名 [{project_name}]: ").strip() or project_name
            build_cmd = "npm run build" if project_info["type"] == "nodejs" else ""
            output_dir = "dist"
            
            if project_info["framework"] == "astro":
                output_dir = "dist"
            elif project_info["framework"] in ("nextjs",):
                output_dir = ".next"
            
            wrangler_content = f'''name = "{cf_project}"
compatibility_date = "2024-01-01"

[site]
bucket = "./{output_dir}"
'''
            with open(wrangler_path, "w") as f:
                f.write(wrangler_content)
            print(f"  ✅ wrangler.toml 已生成")
        
        print(f"\n  部署命令: cd {project_dir} && npx wrangler pages deploy")
    
    elif choice == "2":
        # 本地脚本
        script = generate_deploy_script(
            project_info, 
            {"host": "YOUR_SERVER_IP", "baota": False},
            project_name
        )
        script = script.replace("PROJECT_NAME", project_name)
        
        script_path = os.path.join(project_dir, "deploy.sh")
        with open(script_path, "w") as f:
            f.write(script)
        os.chmod(script_path, 0o755)
        print(f"\n✅ 部署脚本已生成: {script_path}")
        print(f"  修改脚本中的 YOUR_SERVER_IP 为你的服务器地址")
        print(f"  然后执行: bash {script_path}")
    
    elif choice == "3":
        # Docker 部署
        dockerfile = generate_dockerfile(project_info)
        dockerfile_path = os.path.join(project_dir, "Dockerfile")
        with open(dockerfile_path, "w") as f:
            f.write(dockerfile)
        
        # docker-compose
        compose = f'''version: "3.8"
services:
  {project_name}:
    build: .
    ports:
      - "80:80"
    restart: unless-stopped
    environment:
      - NODE_ENV=production
'''
        compose_path = os.path.join(project_dir, "docker-compose.yml")
        with open(compose_path, "w") as f:
            f.write(compose)
        
        print(f"\n✅ Docker 配置已生成:")
        print(f"  Dockerfile: {dockerfile_path}")
        print(f"  docker-compose.yml: {compose_path}")
        print(f"\n  部署命令: docker-compose up -d")
    
    print("\n🎉 Done!")


# CLI 命令处理
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "config":
        interactive_config()
    else:
        main()
