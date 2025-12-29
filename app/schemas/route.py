"""
路由规则相关的 Pydantic 模式
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class RouteCreate(BaseModel):
    """创建路由规则的请求模式"""

    gateway_service_id: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="网关服务 ID",
        examples=["auth-gateway"]
    )
    path_pattern: str = Field(
        ...,
        min_length=1,
        max_length=256,
        description="路径匹配模式（支持通配符 *）",
        examples=["/api/docs/*", "/users/*"]
    )
    target_service_id: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="目标服务 ID",
        examples=["deckview"]
    )
    strip_prefix: bool = Field(
        default=False,
        description="是否剥离前缀路径"
    )
    strip_path: Optional[str] = Field(
        None,
        max_length=256,
        description="需要剥离的前缀路径（如 /api/docs）",
        examples=["/api/docs"]
    )
    priority: int = Field(
        default=0,
        ge=0,
        description="优先级（数字越大优先级越高）"
    )
    enabled: bool = Field(
        default=True,
        description="是否启用此路由"
    )


class RouteUpdate(BaseModel):
    """更新路由规则的请求模式（部分更新）"""

    path_pattern: Optional[str] = Field(None, min_length=1, max_length=256)
    target_service_id: Optional[str] = Field(None, min_length=1, max_length=64)
    strip_prefix: Optional[bool] = None
    strip_path: Optional[str] = Field(None, max_length=256)
    priority: Optional[int] = Field(None, ge=0)
    enabled: Optional[bool] = None


class RouteResponse(BaseModel):
    """路由规则响应模式"""

    id: int
    gateway_service_id: str
    path_pattern: str
    target_service_id: str
    strip_prefix: bool
    strip_path: Optional[str] = None
    priority: int
    enabled: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TargetServiceInfo(BaseModel):
    """目标服务信息（供网关转发使用）"""

    id: str = Field(..., description="服务 ID")
    name: str = Field(..., description="服务名称")
    host: str = Field(..., description="服务地址")
    port: int = Field(..., description="服务端口")
    protocol: str = Field(default="http", description="协议类型")
    status: str = Field(..., description="服务状态")
    base_url: str = Field(..., description="服务基础 URL")


class GatewayRouteResponse(BaseModel):
    """网关专用路由规则响应（包含目标服务完整信息）"""

    id: int
    path_pattern: str
    target_service_id: str
    target_service: TargetServiceInfo = Field(..., description="目标服务详情")
    strip_prefix: bool
    strip_path: Optional[str] = None
    priority: int
    enabled: bool

    class Config:
        from_attributes = True
