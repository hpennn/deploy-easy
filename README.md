# 智能部署助手 (Deploy Easy)

一站式智能部署平台，集成 AI 项目自动部署与 8 大配置生成技能。

## ✨ 功能特性

### 🚀 自动化部署 (from ai-auto-deploy)
- **上传项目识别** - 上传 ZIP 自动识别项目类型，推荐部署方案
- **服务器管理** - 添加/管理多台服务器，支持 SSH 密钥和密码认证
- **一键部署执行** - 生成部署脚本并远程执行，支持 SSE 实时日志
- **代码检测修复** - 检测代码语法错误、括号匹配等问题，AI 自动修复
- **AI 生成项目** - 根据描述自动生成前后端项目代码
- **AI 代码修改** - 上传项目 ZIP，AI 根据需求修改代码

### ⚙️ 配置生成技能 (8个)
1. 🐳 **Dockerfile 生成** - 生成优化的多阶段 Dockerfile
2. 🐳 **Docker Compose** - 生成完整的 docker-compose.yml 编排配置
3. 🌐 **Nginx 配置** - 生成反向代理、SSL、负载均衡配置
4. 🚀 **部署脚本** - 生成自动化部署 Shell 脚本
5. 🔑 **环境变量** - 生成环境变量模板和安全配置
6. 🔒 **SSL 证书** - 生成 SSL 证书配置和 HTTPS 设置
7. 🔄 **CI/CD 流水线** - 生成 GitHub Actions 或 GitLab CI 配置
8. 🗄️ **数据库配置** - 生成数据库初始化 SQL、权限配置和备份脚本

### 📦 项目中心
- 内置 24 个项目数据，支持按类型筛选

## 🛠 技术栈

- **后端**: FastAPI + SQLite
- **前端**: Vue 3 + Element Plus + Vite
- **AI**: DashScope (qwen-plus) + 豆包大模型
- **SSH**: Paramiko

## 🚀 快速开始

### Docker 部署 (推荐)
```bash
docker-compose up -d
```
访问 `http://localhost:8003`

### 本地开发
```bash
# 安装后端依赖
pip install -r backend/requirements.txt

# 安装前端依赖并构建
cd frontend && npm install && npm run build && cd ..

# 启动服务
python backend/main.py
```

## 📁 项目结构

```
deploy-easy/
├── backend/           # FastAPI 后端
│   ├── main.py        # 应用入口
│   ├── routers/       # 原有路由模块
│   └── skills/        # 8个配置生成技能
├── web/               # 自动部署 API 模块
│   ├── api/
│   │   ├── deploy.py  # 部署核心
│   │   ├── servers.py # 服务器管理
│   │   ├── fix.py     # 代码修复
│   │   ├── generate.py# 项目生成
│   │   ├── auth.py    # 认证
│   │   ├── payment.py # 支付
│   │   └── admin.py   # 管理后台
│   └── database.py    # 部署数据库
├── src/               # CLI 核心逻辑
│   └── cli.py         # 项目检测、脚本生成
├── frontend/          # Vue.js 前端
│   ├── src/
│   │   ├── App.vue    # 主组件
│   │   └── main.js    # 入口
│   └── dist/          # 构建产物
├── Dockerfile
└── docker-compose.yml
```

## 🔑 环境变量

- `LLM_API_KEY` - DashScope API Key (配置生成技能使用)

## 📄 License

MIT
