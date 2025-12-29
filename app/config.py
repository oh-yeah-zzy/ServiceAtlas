"""
配置管理模块
使用 pydantic-settings 管理应用配置，支持环境变量覆盖
"""
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""

    # 应用基本信息
    app_name: str = "ServiceAtlas"
    app_version: str = "1.0.0"
    debug: bool = False

    # 服务器配置
    host: str = "127.0.0.1"
    port: int = 9000

    # 数据库配置（SQLite）
    database_url: str = "sqlite+aiosqlite:///./serviceatlas.db"

    # 健康检查配置
    health_check_interval: int = 30  # 健康检查间隔（秒）
    health_check_timeout: int = 5    # 单次检查超时（秒）
    unhealthy_threshold: int = 3     # 连续失败次数阈值，超过则标记为 unhealthy

    # 心跳配置
    heartbeat_timeout: int = 60      # 心跳超时时间（秒），超过未收到心跳标记为 unhealthy

    # API 前缀
    api_prefix: str = "/api/v1"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# 全局配置实例
settings = Settings()

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent
