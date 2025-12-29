"""
服务表模型
存储注册到注册中心的所有服务信息
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, Boolean, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Service(Base):
    """服务注册信息表"""

    __tablename__ = "services"

    # 服务唯一标识（如 deckview, auth-gateway）
    id: Mapped[str] = mapped_column(String(64), primary_key=True)

    # 服务显示名称
    name: Mapped[str] = mapped_column(String(128), nullable=False)

    # 服务地址（IP 或域名）
    host: Mapped[str] = mapped_column(String(256), nullable=False)

    # 服务端口
    port: Mapped[int] = mapped_column(Integer, nullable=False)

    # 协议类型（http/https）
    protocol: Mapped[str] = mapped_column(String(16), default="http")

    # 健康检查路径（默认 /health）
    health_check_path: Mapped[str] = mapped_column(String(256), default="/health")

    # 服务状态：healthy / unhealthy / unknown
    status: Mapped[str] = mapped_column(String(16), default="unknown")

    # 是否作为入口网关
    is_gateway: Mapped[bool] = mapped_column(Boolean, default=False)

    # 扩展元数据（版本号、标签等）
    service_meta: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # 注册时间
    registered_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )

    # 最后心跳时间
    last_heartbeat: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )

    # 健康检查连续失败次数（用于判断是否标记为 unhealthy）
    consecutive_failures: Mapped[int] = mapped_column(Integer, default=0)

    def __repr__(self) -> str:
        return f"<Service(id={self.id}, name={self.name}, status={self.status})>"

    @property
    def base_url(self) -> str:
        """获取服务的基础 URL"""
        return f"{self.protocol}://{self.host}:{self.port}"

    @property
    def health_url(self) -> str:
        """获取健康检查的完整 URL"""
        path = self.health_check_path
        if not path.startswith("/"):
            path = "/" + path
        return f"{self.base_url}{path}"
