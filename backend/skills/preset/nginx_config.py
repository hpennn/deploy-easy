"""Nginx配置技能 - 生成nginx.conf配置"""
import time
import os
from ..llm_client import chat_completion

SKILL_META = {
    "id": "nginx_config",
    "name": "Nginx配置",
    "icon": "🌐",
    "description": "生成Nginx反向代理、SSL、负载均衡配置",
    "keywords": ["nginx", "反向代理", "proxy", "web服务器"],
    "input_type": "textarea",
    "output_type": "text",
}

async def execute(input_data: dict) -> dict:
    """生成Nginx配置"""
    prompt = input_data.get("prompt", "") or input_data.get("text", "")
    if not prompt:
        return {"error": "请描述Nginx配置需求"}

    system_msg = """你是一个专业的Nginx配置工程师。请根据用户描述生成完整的Nginx配置，要求：
1. 包含完整的nginx.conf主配置和server块配置
2. 配置反向代理时包含正确的proxy_set_header
3. 启用Gzip压缩优化
4. 添加安全响应头（X-Frame-Options, X-Content-Type-Options等）
5. 配置合理的缓冲区大小和超时时间
6. 如需要SSL，包含SSL配置和HTTP到HTTPS重定向
7. 添加清晰的注释说明

输出格式：用代码块包裹配置内容，区分不同配置文件。"""

    user_msg = f"请生成Nginx配置：\n\n{prompt}"

    content = await chat_completion([
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_msg}
    ], max_tokens=4000)

    if content.startswith("[LLM未配置]"):
        return {"error": content}

    return {"content": content, "type": "nginx"}
