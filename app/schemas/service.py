"""
服务相关的 Pydantic 模式
用于请求验证和响应序列化
"""
from datetime import datetime
from typing import Optional, Any

from pydantic import BaseModel, Field


class ServiceCreate(BaseModel):
    """创建服务的请求模式"""

    id: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=64,
        description="服务唯一标识（可选，不填则自动生成）",
        examples=["deckview"]
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="服务显示名称",
        examples=["DeckView 文档预览服务"]
    )
    host: str = Field(
        ...,
        min_length=1,
        max_length=256,
        description="服务地址（IP 或域名）",
        examples=["127.0.0.1"]
    )
    port: int = Field(
        ...,
        ge=1,
        le=65535,
        description="服务端口",
        examples=[8000]
    )
    protocol: str = Field(
        default="http",
        description="协议类型",
        examples=["http", "https"]
    )
    health_check_path: str = Field(
        default="/health",
        max_length=256,
        description="健康检查路径",
        examples=["/health", "/api/health"]
    )
    is_gateway: bool = Field(
        default=False,
        description="是否作为入口网关"
    )
    service_meta: Optional[dict[str, Any]] = Field(
        default=None,
        description="扩展元数据（版本号、标签等）",
        examples=[{"version": "1.0.0", "tags": ["docs"]}]
    )


class ServiceUpdate(BaseModel):
    """更新服务的请求模式（部分更新）"""

    name: Optional[str] = Field(None, min_length=1, max_length=128)
    host: Optional[str] = Field(None, min_length=1, max_length=256)
    port: Optional[int] = Field(None, ge=1, le=65535)
    protocol: Optional[str] = None
    health_check_path: Optional[str] = Field(None, max_length=256)
    is_gateway: Optional[bool] = None
    service_meta: Optional[dict[str, Any]] = None


class ServiceResponse(BaseModel):
    """服务响应模式"""

    id: str
    name: str
    host: str
    port: int
    protocol: str
    health_check_path: str
    status: str
    is_gateway: bool
    service_meta: Optional[dict[str, Any]] = None
    registered_at: datetime
    last_heartbeat: Optional[datetime] = None
    base_url: str  # 计算属性

    class Config:
        from_attributes = True


class ServiceListResponse(BaseModel):
    """服务列表响应模式"""

    total: int
    services: list[ServiceResponse]
