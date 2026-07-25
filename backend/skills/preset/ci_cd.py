"""CI/CD流水线技能 - 生成CI/CD配置文件"""
import time
import os
from ..llm_client import chat_completion

SKILL_META = {
    "id": "ci_cd",
    "name": "CI/CD流水线",
    "icon": "🔄",
    "description": "生成GitHub Actions或GitLab CI配置",
    "keywords": ["ci", "cd", "流水线", "github actions", "gitlab ci", "自动化部署"],
    "input_type": "textarea",
    "output_type": "text",
}

async def execute(input_data: dict) -> dict:
    """生成CI/CD配置"""
    prompt = input_data.get("prompt", "") or input_data.get("text", "")
    if not prompt:
        return {"error": "请描述项目信息和CI/CD需求"}

    system_msg = """你是一个专业的CI/CD工程师。请根据用户描述生成完整的CI/CD流水线配置，要求：
1. 根据项目类型选择GitHub Actions或GitLab CI（默认GitHub Actions）
2. 包含完整的流水线：代码检查、测试、构建、部署
3. 使用缓存优化构建速度
4. 配置分支保护和环境变量secrets
5. 包含Docker镜像构建和推送到镜像仓库
6. 配置多环境部署（staging/production）
7. 包含部署成功/失败的通知
8. 添加清晰的注释说明每个步骤

输出格式：用代码块包裹配置文件，并补充配置说明和secrets设置指南。"""

    user_msg = f"请生成CI/CD配置：\n\n{prompt}"

    content = await chat_completion([
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_msg}
    ], max_tokens=4000)

    if content.startswith("[LLM未配置]"):
        return {"error": content}

    return {"content": content, "type": "ci-cd"}
