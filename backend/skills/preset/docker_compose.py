"""Docker Compose技能 - 生成完整的docker-compose.yml"""
import time
import os
from ..llm_client import chat_completion

SKILL_META = {
    "id": "docker_compose",
    "name": "Docker Compose",
    "icon": "🐳",
    "description": "生成完整的docker-compose.yml编排配置",
    "keywords": ["docker-compose", "compose", "容器编排", "多容器"],
    "input_type": "textarea",
    "output_type": "text",
}

async def execute(input_data: dict) -> dict:
    """生成docker-compose.yml配置"""
    prompt = input_data.get("prompt", "") or input_data.get("text", "")
    if not prompt:
        return {"error": "请描述你的服务架构"}

    system_msg = """你是一个专业的DevOps工程师，精通Docker Compose编排。请根据用户描述生成完整的docker-compose.yml，要求：
1. 定义所有服务及其镜像/构建配置
2. 配置合理的网络（networks）和卷（volumes）
3. 为每个服务添加健康检查（healthcheck）
4. 设置服务间的依赖关系（depends_on）
5. 配置环境变量和端口映射
6. 使用最新版本的compose规范（无需version字段）
7. 添加清晰的注释

输出格式：用代码块包裹docker-compose.yml内容，并在之后补充关键配置说明。"""

    user_msg = f"请为以下服务架构生成docker-compose.yml：\n\n{prompt}"

    content = await chat_completion([
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_msg}
    ], max_tokens=4000)

    if content.startswith("[LLM未配置]"):
        return {"error": content}

    return {"content": content, "type": "docker-compose"}
