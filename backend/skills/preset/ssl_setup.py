"""SSL证书配置技能 - 生成SSL/HTTPS配置"""
import time
import os
from ..llm_client import chat_completion

SKILL_META = {
    "id": "ssl_setup",
    "name": "SSL证书",
    "icon": "🔒",
    "description": "生成SSL证书配置和HTTPS设置",
    "keywords": ["ssl", "https", "证书", "certbot", "letsencrypt"],
    "input_type": "textarea",
    "output_type": "text",
}

async def execute(input_data: dict) -> dict:
    """生成SSL配置"""
    prompt = input_data.get("prompt", "") or input_data.get("text", "")
    if not prompt:
        return {"error": "请提供域名和服务器信息"}

    system_msg = """你是一个专业的SSL/TLS配置工程师。请根据用户信息生成完整的SSL配置方案，要求：
1. 提供Let's Encrypt/certbot获取证书的完整命令
2. 生成包含SSL配置的Nginx server块
3. 配置HTTP到HTTPS的301重定向
4. 使用强加密套件和TLS 1.2/1.3
5. 配置HSTS安全头
6. 包含证书自动续期cron配置
7. 如适用，包含通配符证书配置
8. 添加清晰的安装步骤说明

输出格式：按步骤组织，命令和配置都用代码块包裹。"""

    user_msg = f"请生成SSL配置：\n\n{prompt}"

    content = await chat_completion([
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_msg}
    ], max_tokens=4000)

    if content.startswith("[LLM未配置]"):
        return {"error": content}

    return {"content": content, "type": "ssl-setup"}
