"""Dockerfile生成技能 - 根据应用描述生成优化的多阶段Dockerfile"""
import time
import os
from ..llm_client import chat_completion

SKILL_META = {
    "id": "dockerfile_gen",
    "name": "Dockerfile生成",
    "icon": "🐳",
    "description": "根据应用描述生成优化的多阶段Dockerfile",
    "keywords": ["dockerfile", "docker", "容器", "docker构建"],
    "input_type": "textarea",
    "output_type": "text",
}

async def execute(input_data: dict) -> dict:
    """根据应用描述生成优化的Dockerfile"""
    prompt = input_data.get("prompt", "") or input_data.get("text", "")
    if not prompt:
        return {"error": "请描述你的应用信息"}

    system_msg = """你是一个专业的DevOps工程师，精通编写Dockerfile。请根据用户描述生成优化的Dockerfile，要求：
1. 使用多阶段构建（multi-stage build）最小化镜像体积
2. 使用非root用户运行应用
3. 合理利用缓存层，最小化层数
4. 包含必要的健康检查指令
5. 添加清晰的注释说明每个步骤
6. 同时生成 .dockerignore 文件内容

输出格式：先输出 Dockerfile，再输出 .dockerignore，都用代码块包裹。"""

    user_msg = f"请为以下应用生成Dockerfile：\n\n{prompt}"

    content = await chat_completion([
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_msg}
    ], max_tokens=4000)

    if content.startswith("[LLM未配置]"):
        return {"error": content}

    return {"content": content, "type": "dockerfile"}
