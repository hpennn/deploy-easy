"""数据库配置技能 - 生成数据库初始化和配置"""
import time
import os
from ..llm_client import chat_completion

SKILL_META = {
    "id": "db_setup",
    "name": "数据库配置",
    "icon": "🗄️",
    "description": "生成数据库初始化SQL、权限配置和备份脚本",
    "keywords": ["数据库", "database", "mysql", "postgresql", "mongodb"],
    "input_type": "textarea",
    "output_type": "text",
}

async def execute(input_data: dict) -> dict:
    """生成数据库配置"""
    prompt = input_data.get("prompt", "") or input_data.get("text", "")
    if not prompt:
        return {"error": "请描述数据库需求"}

    system_msg = """你是一个专业的DBA工程师。请根据用户描述生成完整的数据库配置方案，要求：
1. 生成数据库安装和初始化命令
2. 创建数据库和用户的SQL脚本
3. 配置用户权限（遵循最小权限原则）
4. 如需要，生成表结构初始化SQL
5. 配置远程访问（如需要）
6. 生成数据库备份脚本（支持全量和增量备份）
7. 配置自动备份的cron任务
8. 包含性能优化建议（如my.cnf配置）
9. 添加清晰的执行步骤说明

输出格式：按步骤组织，SQL和脚本都用代码块包裹。"""

    user_msg = f"请生成数据库配置：\n\n{prompt}"

    content = await chat_completion([
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_msg}
    ], max_tokens=4000)

    if content.startswith("[LLM未配置]"):
        return {"error": content}

    return {"content": content, "type": "db-setup"}
