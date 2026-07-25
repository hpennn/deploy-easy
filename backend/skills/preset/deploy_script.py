"""部署脚本技能 - 生成bash部署脚本"""
import time
import os
from ..llm_client import chat_completion

SKILL_META = {
    "id": "deploy_script",
    "name": "部署脚本",
    "icon": "🚀",
    "description": "生成自动化部署Shell脚本",
    "keywords": ["部署", "deploy", "脚本", "shell", "bash"],
    "input_type": "textarea",
    "output_type": "text",
}

async def execute(input_data: dict) -> dict:
    """生成部署脚本"""
    prompt = input_data.get("prompt", "") or input_data.get("text", "")
    if not prompt:
        return {"error": "请描述部署环境和需求"}

    system_msg = """你是一个专业的DevOps工程师，擅长编写自动化部署脚本。请根据用户描述生成完整的bash部署脚本，要求：
1. 包含环境检查（系统版本、依赖检查）
2. 包含错误处理和日志输出（带时间戳）
3. 自动安装必要的依赖
4. 包含应用部署步骤（拉取代码、安装依赖、构建、启动）
5. 配置systemd服务文件或进程管理
6. 包含回滚机制
7. 添加清晰的注释和说明
8. 脚本开头包含set -e等安全设置

输出格式：用代码块包裹脚本内容，并补充使用说明。"""

    user_msg = f"请生成部署脚本：\n\n{prompt}"

    content = await chat_completion([
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_msg}
    ], max_tokens=4000)

    if content.startswith("[LLM未配置]"):
        return {"error": content}

    return {"content": content, "type": "deploy-script"}
