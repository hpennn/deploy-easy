# Deploy Easy

🚀 AI自动化部署助手 - 一键生成 Dockerfile、Nginx 配置、部署脚本，让部署变得简单。

## 功能特性

- 🐳 **Dockerfile生成**：根据应用描述生成优化的多阶段Dockerfile，包含最佳实践
- 📦 **Docker Compose**：生成完整编排配置，含服务定义、网络、卷、健康检查
- 🌐 **Nginx配置**：反向代理、SSL、Gzip、安全头、负载均衡一键生成
- 🚀 **部署脚本**：自动化Shell部署脚本，含环境检查、依赖安装、回滚机制
- 🔑 **环境变量**：生成 .env 模板 + .env.example，含安全建议和默认值
- 🔒 **SSL证书**：Let's Encrypt/certbot 命令和 Nginx SSL 配置
- 🔄 **CI/CD流水线**：GitHub Actions / GitLab CI 完整配置
- 🗄️ **数据库配置**：初始化SQL、用户权限、备份脚本

## 快速部署

### 方式一：Docker 部署（推荐）

```bash
# 1. 克隆仓库
git clone https://github.com/hpennn/deploy-easy.git
cd deploy-easy

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 填写 LLM_API_KEY

# 3. 启动
docker-compose up -d

# 4. 访问
open http://localhost:8080
```

### 方式二：直接部署到服务器

```bash
# 1. 安装 Python 3.10+
python3 --version

# 2. 安装依赖
cd deploy-easy
pip install -r backend/requirements.txt

# 3. 配置环境变量
export LLM_API_KEY="your_key"
export LLM_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"

# 4. 启动后端
cd backend
uvicorn main:app --host 0.0.0.0 --port 8080

# 5. 访问 http://your-server:8080
```

### 方式三：Nginx 反向代理

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 环境变量

| 变量 | 说明 | 必填 | 默认值 |
|------|------|------|--------|
| LLM_API_KEY | 大模型 API Key | ✅ | - |
| LLM_BASE_URL | API 地址 | ❌ | 阿里通义 |
| LLM_MODEL | 文本模型 | ❌ | qwen-plus |
| LLM_VL_MODEL | 多模态模型 | ❌ | qwen-vl-plus |

## 技能开发

自定义技能只需实现统一接口：

```python
# backend/skills/preset/my_skill.py
SKILL_META = {
    "id": "my_skill",
    "name": "我的技能",
    "icon": "🔧",
    "description": "技能描述",
    "keywords": ["关键词"],
    "input_type": "textarea",
    "output_type": "text",
}

async def execute(input_data: dict) -> dict:
    # 你的技能逻辑
    return {"content": "处理结果"}
```

然后在 `registry.py` 中注册即可。

## 项目结构

```
deploy-easy/
├── frontend/          # PWA前端
│   ├── index.html     # Deploy Easy 主界面
│   ├── manifest.json
│   └── icons/
├── backend/
│   ├── main.py        # FastAPI入口
│   ├── skills/        # 技能引擎
│   │   ├── registry.py    # 技能注册中心
│   │   ├── engine.py      # 执行引擎
│   │   ├── llm_client.py  # LLM客户端
│   │   └── preset/        # 预置部署技能
│   │       ├── dockerfile_gen.py
│   │       ├── docker_compose.py
│   │       ├── nginx_config.py
│   │       ├── deploy_script.py
│   │       ├── env_config.py
│   │       ├── ssl_setup.py
│   │       ├── ci_cd.py
│   │       └── db_setup.py
│   └── routers/       # API路由
├── .env.example
└── docker-compose.yml
```

## API 文档

启动后端后访问 `http://localhost:8080/docs` 查看完整API文档。

主要接口：
- `GET /api/skills` - 技能列表
- `POST /api/skills/{id}/execute` - 执行技能

## License

MIT
