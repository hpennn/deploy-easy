"""
Skill Registry - 技能注册中心
负责注册、发现、加载技能
"""
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field


@dataclass
class SkillMeta:
    """技能元数据"""
    id: str
    name: str
    icon: str
    description: str
    input_type: str  # "textarea", "file", "file+text"
    output_type: str  # "text", "file", "structured"
    handler: Optional[Callable] = None
    tags: List[str] = field(default_factory=list)
    enabled: bool = True


class SkillRegistry:
    """技能注册中心 - 单例模式"""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._skills = {}
            cls._instance._initialized = False
        return cls._instance

    def register(self, skill: SkillMeta) -> None:
        """注册一个技能"""
        self._skills[skill.id] = skill

    def unregister(self, skill_id: str) -> None:
        """注销一个技能"""
        self._skills.pop(skill_id, None)

    def get(self, skill_id: str) -> Optional[SkillMeta]:
        """获取技能元数据"""
        return self._skills.get(skill_id)

    def list_all(self, enabled_only: bool = True) -> List[SkillMeta]:
        """列出所有技能"""
        skills = list(self._skills.values())
        if enabled_only:
            skills = [s for s in skills if s.enabled]
        return skills

    def find_by_keyword(self, keyword: str) -> List[SkillMeta]:
        """根据关键词匹配技能"""
        keyword_lower = keyword.lower()
        matched = []
        for skill in self._skills.values():
            if not skill.enabled:
                continue
            if (keyword_lower in skill.name.lower() or
                keyword_lower in skill.description.lower() or
                any(keyword_lower in tag.lower() for tag in skill.tags)):
                matched.append(skill)
        return matched

    def find_by_keywords(self, text: str) -> Optional[SkillMeta]:
        """从文本中匹配最合适的技能"""
        keyword_map = {
            "dockerfile_gen": ["dockerfile", "dockerfile生成", "docker构建", "docker镜像"],
            "docker_compose": ["docker-compose", "compose", "容器编排", "多容器", "docker compose"],
            "nginx_config": ["nginx", "反向代理", "proxy", "web服务器", "负载均衡"],
            "deploy_script": ["部署", "部署脚本", "deploy", "发布", "上线"],
            "env_config": ["环境变量", "env", "配置", "密钥", "secret"],
            "ssl_setup": ["ssl", "https", "证书", "certbot", "letsencrypt"],
            "ci_cd": ["ci", "cd", "流水线", "持续集成", "持续部署", "github actions", "gitlab ci"],
            "db_setup": ["数据库", "database", "mysql", "postgresql", "mongodb", "建库", "备份"],
        }
        text_lower = text.lower()
        for skill_id, keywords in keyword_map.items():
            if any(kw in text_lower for kw in keywords):
                skill = self.get(skill_id)
                if skill and skill.enabled:
                    return skill
        return None

    def load_preset_skills(self) -> None:
        """加载所有预置技能"""
        from skills.preset import dockerfile_gen, docker_compose, nginx_config, deploy_script
        from skills.preset import env_config, ssl_setup, ci_cd, db_setup

        preset_skills = [
            SkillMeta(
                id="dockerfile_gen",
                name="Dockerfile生成",
                icon="🐳",
                description="根据应用描述生成优化的多阶段Dockerfile",
                input_type="textarea",
                output_type="text",
                handler=dockerfile_gen.execute,
                tags=["dockerfile", "docker", "容器", "镜像"],
            ),
            SkillMeta(
                id="docker_compose",
                name="Docker Compose",
                icon="🐳",
                description="生成完整的docker-compose.yml编排配置",
                input_type="textarea",
                output_type="text",
                handler=docker_compose.execute,
                tags=["docker-compose", "compose", "容器编排", "多容器"],
            ),
            SkillMeta(
                id="nginx_config",
                name="Nginx配置",
                icon="🌐",
                description="生成Nginx反向代理、SSL、负载均衡配置",
                input_type="textarea",
                output_type="text",
                handler=nginx_config.execute,
                tags=["nginx", "反向代理", "proxy", "web服务器"],
            ),
            SkillMeta(
                id="deploy_script",
                name="部署脚本",
                icon="🚀",
                description="生成自动化部署Shell脚本",
                input_type="textarea",
                output_type="text",
                handler=deploy_script.execute,
                tags=["部署", "deploy", "脚本", "shell"],
            ),
            SkillMeta(
                id="env_config",
                name="环境变量",
                icon="🔑",
                description="生成环境变量模板和安全配置",
                input_type="textarea",
                output_type="text",
                handler=env_config.execute,
                tags=["环境变量", "env", "配置", "密钥"],
            ),
            SkillMeta(
                id="ssl_setup",
                name="SSL证书",
                icon="🔒",
                description="生成SSL证书配置和HTTPS设置",
                input_type="textarea",
                output_type="text",
                handler=ssl_setup.execute,
                tags=["ssl", "https", "证书", "letsencrypt"],
            ),
            SkillMeta(
                id="ci_cd",
                name="CI/CD流水线",
                icon="🔄",
                description="生成GitHub Actions或GitLab CI配置",
                input_type="textarea",
                output_type="text",
                handler=ci_cd.execute,
                tags=["ci", "cd", "流水线", "自动化部署"],
            ),
            SkillMeta(
                id="db_setup",
                name="数据库配置",
                icon="🗄️",
                description="生成数据库初始化SQL、权限配置和备份脚本",
                input_type="textarea",
                output_type="text",
                handler=db_setup.execute,
                tags=["数据库", "database", "mysql", "postgresql"],
            ),
        ]

        for skill in preset_skills:
            self.register(skill)


# 全局实例
registry = SkillRegistry()
