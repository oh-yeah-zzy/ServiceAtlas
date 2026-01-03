"""
路由规则表模型
存储网关服务的路由转发规则
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Route(Base):
    """网关路由规则表"""

    __tablename__ = "routes"

    # 主键 ID
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # 网关服务 ID（必须是 is_gateway=True 的服务）
    gateway_service_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("services.id", ondelete="CASCADE"),
        nullable=False
    )

    # 路径匹配模式（如 /api/docs/*, /users/*)
    path_pattern: Mapped[str] = mapped_column(String(256), nullable=False)

    # HTTP 方法限制（逗号分隔，如 "GET,POST" 或 "*" 表示所有方法）
    methods: Mapped[str] = mapped_column(String(64), default="*")

    # 目标服务 ID（请求将被转发到此服务）
    target_service_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("services.id", ondelete="CASCADE"),
        nullable=False
    )

    # 是否剥离前缀（如 /api/docs/file.pdf -> /file.pdf）
    strip_prefix: Mapped[bool] = mapped_column(Boolean, default=False)

    # 需要剥离的前缀路径（如果 strip_prefix=True）
    strip_path: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)

    # 优先级（数字越大优先级越高）
    priority: Mapped[int] = mapped_column(Integer, default=0)

    # 是否启用
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    # 认证配置（JSON 格式）
    # 结构: {
    #   "require_auth": true,           # 是否需要认证
    #   "auth_service_id": "aegis",     # 认证服务 ID
    #   "public_paths": ["/health"],    # 公开路径（不需要认证）
    #   "login_redirect": "/login"      # 登录重定向路径
    # }
    auth_config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # 创建时间
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )

    # 更新时间
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, onupdate=datetime.utcnow
    )

    def __repr__(self) -> str:
        return f"<Route(gateway={self.gateway_service_id}, pattern={self.path_pattern} -> target={self.target_service_id})>"

