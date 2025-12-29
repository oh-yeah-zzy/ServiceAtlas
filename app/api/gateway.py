"""
网关路由 API
处理路由规则的增删改查
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.route import (
    RouteCreate,
    RouteUpdate,
    RouteResponse,
    GatewayRouteResponse,
    TargetServiceInfo,
)
from app.services import gateway as gateway_service
from app.models.service import Service


router = APIRouter()


@router.post(
    "/routes",
    response_model=RouteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建路由规则",
    description="为网关服务创建路由规则"
)
async def create_route(
    route_data: RouteCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建路由规则"""
    route = await gateway_service.create_route(db, route_data)
    if not route:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="网关服务不存在、目标服务不存在，或网关服务未启用网关模式"
        )
    return route


@router.get(
    "/routes",
    response_model=list[RouteResponse],
    summary="获取路由规则列表",
    description="获取所有路由规则，可按网关过滤"
)
async def list_routes(
    gateway_id: Optional[str] = Query(None, description="按网关服务 ID 过滤"),
    enabled_only: bool = Query(False, description="是否只获取启用的规则"),
    db: AsyncSession = Depends(get_db)
):
    """获取路由规则列表"""
    return await gateway_service.get_all_routes(
        db, gateway_id=gateway_id, enabled_only=enabled_only
    )


@router.get(
    "/routes/{route_id}",
    response_model=RouteResponse,
    summary="获取路由规则详情",
    description="获取指定路由规则的详细信息"
)
async def get_route(
    route_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取路由规则详情"""
    route = await gateway_service.get_route(db, route_id)
    if not route:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"路由规则 ID={route_id} 不存在"
        )
    return route


@router.put(
    "/routes/{route_id}",
    response_model=RouteResponse,
    summary="更新路由规则",
    description="更新路由规则的配置"
)
async def update_route(
    route_id: int,
    update_data: RouteUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新路由规则"""
    route = await gateway_service.update_route(db, route_id, update_data)
    if not route:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"路由规则 ID={route_id} 不存在或目标服务不存在"
        )
    return route


@router.delete(
    "/routes/{route_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除路由规则",
    description="删除指定的路由规则"
)
async def delete_route(
    route_id: int,
    db: AsyncSession = Depends(get_db)
):
    """删除路由规则"""
    success = await gateway_service.delete_route(db, route_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"路由规则 ID={route_id} 不存在"
        )
    return None


@router.get(
    "/gateway/routes",
    response_model=list[GatewayRouteResponse],
    summary="网关获取路由规则",
    description="供网关服务获取自己的路由规则（包含目标服务详情）。需要通过 X-Gateway-ID 头传递网关服务 ID。"
)
async def get_gateway_routes(
    x_gateway_id: str = Header(..., description="网关服务 ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    网关专用端点：获取路由规则（包含目标服务完整信息）

    只有 is_gateway=True 的服务才能调用此接口
    """
    # 验证网关服务身份
    gateway = await db.get(Service, x_gateway_id)
    if not gateway:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"网关服务 '{x_gateway_id}' 不存在"
        )

    if not gateway.is_gateway:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"服务 '{x_gateway_id}' 不是网关服务，无权获取路由规则"
        )

    # 获取该网关的所有启用的路由规则
    routes = await gateway_service.get_all_routes(
        db, gateway_id=x_gateway_id, enabled_only=True
    )

    # 构建响应，包含目标服务的完整信息
    result = []
    for route in routes:
        # 获取目标服务信息
        target_service = await db.get(Service, route.target_service_id)
        if not target_service:
            # 目标服务不存在，跳过此路由
            continue

        result.append(GatewayRouteResponse(
            id=route.id,
            path_pattern=route.path_pattern,
            target_service_id=route.target_service_id,
            target_service=TargetServiceInfo(
                id=target_service.id,
                name=target_service.name,
                host=target_service.host,
                port=target_service.port,
                protocol=target_service.protocol,
                status=target_service.status,
                base_url=target_service.base_url,
            ),
            strip_prefix=route.strip_prefix,
            strip_path=route.strip_path,
            priority=route.priority,
            enabled=route.enabled,
        ))

    return result
