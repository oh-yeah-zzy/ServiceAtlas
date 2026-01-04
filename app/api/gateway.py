"""
网关路由 API
处理路由规则的增删改查
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.route import (
    RouteCreate,
    RouteUpdate,
    RouteResponse,
    GatewayRouteResponse,
    TargetServiceInfo,
    AuthConfig,
    AuthServiceInfo,
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

    # 查找所有认证服务（service_type = "authentication"）
    auth_services = {}
    auth_result = await db.execute(select(Service))
    for svc in auth_result.scalars():
        service_meta = svc.service_meta or {}
        if service_meta.get("service_type") == "authentication":
            auth_services[svc.id] = svc

    # 构建响应，包含目标服务的完整信息
    result = []
    for route in routes:
        # 获取目标服务信息
        target_service = await db.get(Service, route.target_service_id)
        if not target_service:
            # 目标服务不存在，跳过此路由
            continue

        # 构建认证配置
        auth_config_data = route.auth_config
        auth_config = None
        auth_service_info = None

        if auth_config_data:
            # 复制一份，避免修改原始数据
            auth_config_dict = dict(auth_config_data)

            # 如果指定了认证服务，获取认证服务信息并动态组装 login_redirect
            auth_service_id = auth_config_dict.get("auth_service_id")
            if auth_service_id and auth_service_id in auth_services:
                auth_svc = auth_services[auth_service_id]
                service_meta = auth_svc.service_meta or {}

                auth_service_info = AuthServiceInfo(
                    id=auth_svc.id,
                    name=auth_svc.name,
                    base_url=auth_svc.base_url,
                    auth_endpoint=service_meta.get("auth_endpoint"),
                )

                # 动态组装 login_redirect（如果路由规则中未指定）
                # 使用网关代理路径而非认证服务的直接地址，因为外部只能通过网关访问
                if not auth_config_dict.get("login_redirect"):
                    login_path = service_meta.get("login_path")
                    if login_path:
                        # 确保路径以 / 开头
                        if not login_path.startswith("/"):
                            login_path = "/" + login_path
                        # 查找网关到认证服务的路由，使用网关代理路径
                        # 例如：网关有 /aegis/** -> aegis 的路由，则使用 /aegis/admin/login
                        auth_route = await gateway_service.find_route_for_service(
                            db, gateway_id=x_gateway_id, target_service_id=auth_service_id
                        )
                        if auth_route and auth_route.strip_prefix:
                            # 使用网关代理路径（相对路径，浏览器会自动补全域名）
                            gateway_prefix = auth_route.strip_path or f"/{auth_service_id}"
                            auth_config_dict["login_redirect"] = gateway_prefix + login_path
                        else:
                            # 回退到直接地址（认证服务没有网关路由时）
                            if auth_svc.base_url:
                                auth_config_dict["login_redirect"] = (
                                    auth_svc.base_url.rstrip("/") + login_path
                                )

            auth_config = AuthConfig(**auth_config_dict)

        result.append(GatewayRouteResponse(
            id=route.id,
            path_pattern=route.path_pattern,
            methods=route.methods if hasattr(route, 'methods') else "*",
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
            auth_config=auth_config,
            auth_service=auth_service_info,
        ))

    return result
