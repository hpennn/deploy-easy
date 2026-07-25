"""环境变量配置技能 - 生成.env文件模板"""
import time
import os
from ..llm_client import chat_completion

SKILL_META = {
    "id": "env_config",
    "name": "环境变量",
    "icon": "🔑",
    "description": "生成环境变量模板和安全配置",
    "keywords": ["环境变量", "env", "配置", "密钥"],
    "input_type": "textarea",
    "output_type": "text",
}

async def execute(input_data: dict) -> dict:
    """生成环境变量配置"""
    prompt = input_data.get("prompt", "") or input_data.get("text", "")
    if not prompt:
        return {"error": "请描述应用需要的环境变量"}

    system_msg = """你是一个专业的安全工程师。请根据用户描述生成完整的环境变量配置，要求：
1. 生成 .env.example 文件（包含所有变量和注释，不含真实密钥）
2. 生成 .env 文件模板（包含合理的默认值）
3. 为每个变量添加详细的注释说明用途
4. 对敏感变量标注安全建议（如使用openssl生成随机密钥）
5. 按功能分组（数据库、应用、第三方服务等）
6. 包含docker-compose中的env_file引用示例

输出格式：用代码块分别包裹 .env.example 和 .env 文件内容。"""

    user_msg = f"请生成环境变量配置：\n\n{prompt}"

    content = await chat_completion([
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_msg}
    ], max_tokens=4000)

    if content.startswith("[LLM未配置]"):
        return {"error": content}

    return {"content": content, "type": "env-config"}
