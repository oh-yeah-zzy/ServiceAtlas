"""
依赖关系表模型
存储服务之间的调用依赖关系，用于构建依赖拓扑图
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Dependency(Base):
    """服务依赖关系表"""

    __tablename__ = "dependencies"

    # 主键 ID
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # 调用方服务 ID（源服务）
    source_service_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("services.id", ondelete="CASCADE"),
        nullable=False
    )

    # 被调用方服务 ID（目标服务）
    target_service_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("services.id", ondelete="CASCADE"),
        nullable=False
    )

    # 依赖说明（描述调用关系的用途）
    description: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)

    # 创建时间
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )

    def __repr__(self) -> str:
        return f"<Dependency(source={self.source_service_id} -> target={self.target_service_id})>"
