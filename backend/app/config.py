# Application Configuration
# 应用程序配置

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load .env file from project root
# 从项目根目录加载 .env 文件
_env_path = Path(__file__).parent.parent.parent / ".env"
print(f"Loading .env from: {_env_path}")
load_dotenv(_env_path)


class AppConfig:
    """Application configuration.
    应用程序配置。
    """

    # Server settings
    # 服务器设置
    host: str = os.getenv("APP_HOST", "0.0.0.0")
    port: int = int(os.getenv("APP_PORT", "8000"))
    debug: bool = os.getenv("APP_DEBUG", "false").lower() == "true"

    # Model settings
    # 模型设置
    model_base_url: str = os.getenv("MODEL_BASE_URL", "http://127.0.0.1:1234")
    model_name: Optional[str] = os.getenv("MODEL_NAME", None)

    # Memory settings
    # 记忆设置
    memory_path: str = os.getenv("MEMORY_PATH", "data/memories.jsonl")

    # Skills settings
    # 技能设置
    skills_path: str = os.getenv("SKILLS_PATH", "app/skills/skills")

    # Context settings
    # 上下文设置
    context_max_tokens: int = int(os.getenv("CONTEXT_MAX_TOKENS", "4096"))


config = AppConfig()