"""
依赖关系相关的 Pydantic 模式
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class DependencyCreate(BaseModel):
    """创建依赖关系的请求模式"""

    source_service_id: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="调用方服务 ID",
        examples=["auth-gateway"]
    )
    target_service_id: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="被调用方服务 ID",
        examples=["deckview"]
    )
    description: Optional[str] = Field(
        None,
        max_length=256,
        description="依赖说明",
        examples=["网关调用文档服务获取文件预览"]
    )


class DependencyResponse(BaseModel):
    """依赖关系响应模式"""

    id: int
    source_service_id: str
    target_service_id: str
    description: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TopologyNode(BaseModel):
    """拓扑图节点"""

    id: str
    name: str
    status: str
    is_gateway: bool


class TopologyEdge(BaseModel):
    """拓扑图边（依赖关系）"""

    source: str
    target: str
    description: Optional[str] = None


class TopologyResponse(BaseModel):
    """拓扑图响应模式（用于前端可视化）"""

    nodes: list[TopologyNode]
    edges: list[TopologyEdge]
