"""
配置管理模块

负责读取环境变量和配置文件，提供统一的配置访问接口。
所有配置参数都使用 AI_INSUR_ 前缀。
"""

import os
from typing import Optional
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()


class Config:
    """配置类，提供统一的配置访问接口"""

    # 服务器配置
    HOST: str = os.getenv("AI_INSUR_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("AI_INSUR_PORT", "8000"))
    DEBUG: bool = os.getenv("AI_INSUR_DEBUG", "false").lower() == "true"
    CORS_ORIGINS: str = os.getenv("AI_INSUR_CORS_ORIGINS", "*")

    # OpenAI API 配置
    OPENAI_API_KEY: str = os.getenv("AI_INSUR_OPENAI_API_KEY", "")
    OPENAI_BASE_URL: str = os.getenv(
        "AI_INSUR_OPENAI_BASE_URL", "https://api.gptsapi.net/v1")
    OPENAI_MODEL: str = os.getenv(
        "AI_INSUR_OPENAI_MODEL", "gpt-4.1-mini-2025-04-14")
    OPENAI_LLM_PROVIDER: str = os.getenv(
        "AI_INSUR_OPENAI_LLM_PROVIDER", "openai")
    OPENAI_EMBEDDING_MODEL: str = os.getenv(
        "AI_INSUR_OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    OPENAI_EMBEDDING_PROVIDER: str = os.getenv(
        "AI_INSUR_OPENAI_EMBEDDING_PROVIDER", "openai")

    # 智能对话助理 API 配置
    DEEPSEEK_API_KEY: str = os.getenv("AI_INSUR_DEEPSEEK_API_KEY", "")
    QWEN_API_KEY: str = os.getenv("AI_INSUR_QWEN_API_KEY", "")

    # ElasticSearch 配置
    ES_HOST: str = os.getenv("AI_INSUR_ES_HOST", "localhost")
    ES_PORT: int = int(os.getenv("AI_INSUR_ES_PORT", "9200"))
    ES_USERNAME: Optional[str] = os.getenv("AI_INSUR_ES_USERNAME") or None
    ES_PASSWORD: Optional[str] = os.getenv("AI_INSUR_ES_PASSWORD") or None
    ES_INDEX_PRODUCTS: str = os.getenv(
        "AI_INSUR_ES_INDEX_PRODUCTS", "insurance_products")
    ES_INDEX_ALL_PRODUCTS: str = os.getenv(
        "AI_INSUR_ES_INDEX_ALL_PRODUCTS", "insurance_total_fields")

    # 数据库配置
    DB_HOST: str = os.getenv("AI_INSUR_DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("AI_INSUR_DB_PORT", "3306"))
    DB_NAME: str = os.getenv("AI_INSUR_DB_NAME", "ai_insurance")
    DB_USERNAME: Optional[str] = os.getenv("AI_INSUR_DB_USERNAME") or None
    DB_PASSWORD: Optional[str] = os.getenv("AI_INSUR_DB_PASSWORD") or None

    # 日志配置
    LOG_LEVEL: str = os.getenv("AI_INSUR_LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("AI_INSUR_LOG_FILE", "logs/app.log")

    @classmethod
    def validate(cls) -> None:
        """验证必要的配置项是否已设置"""
        if not cls.OPENAI_API_KEY:
            raise ValueError("AI_INSUR_OPENAI_API_KEY 环境变量未设置")

    @classmethod
    def validate_assistant(cls) -> None:
        """验证智能对话助理的必要配置项是否已设置"""
        if not cls.DEEPSEEK_API_KEY:
            raise ValueError("AI_INSUR_DEEPSEEK_API_KEY 环境变量未设置")
        if not cls.QWEN_API_KEY:
            raise ValueError("AI_INSUR_QWEN_API_KEY 环境变量未设置")

    @classmethod
    def get_es_url(cls) -> str:
        """获取 ElasticSearch 连接 URL"""
        if cls.ES_USERNAME and cls.ES_PASSWORD:
            return f"http://{cls.ES_USERNAME}:{cls.ES_PASSWORD}@{cls.ES_HOST}:{cls.ES_PORT}"
        return f"http://{cls.ES_HOST}:{cls.ES_PORT}"

    @classmethod
    def get_db_url(cls) -> Optional[str]:
        """获取数据库连接 URL"""
        if cls.DB_USERNAME and cls.DB_PASSWORD:
            return f"mysql+aiomysql://{cls.DB_USERNAME}:{cls.DB_PASSWORD}@{cls.DB_HOST}:{cls.DB_PORT}/{cls.DB_NAME}?charset=utf8mb4"
        return None

    @classmethod
    def get_sqlite_url(cls) -> str:
        """获取 SQLite 数据库连接 URL"""
        return "sqlite+aiosqlite:///./ai_insurance.db"


# 全局配置实例
config = Config()
