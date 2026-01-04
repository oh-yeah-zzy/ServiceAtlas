"""
网关路由业务逻辑
处理路由规则的管理
"""
from typing import Optional

from sqlalchemy import select, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.service import Service
from app.models.route import Route
from app.schemas.route import RouteCreate, RouteUpdate


async def create_route(
    db: AsyncSession,
    route_data: RouteCreate
) -> Optional[Route]:
    """
    创建路由规则
    验证网关服务和目标服务都存在，且网关服务的 is_gateway=True
    """
    # 验证网关服务
    gateway = await db.get(Service, route_data.gateway_service_id)
    if not gateway:
        return None
    if not gateway.is_gateway:
        return None  # 只有网关服务才能配置路由

    # 验证目标服务
    target = await db.get(Service, route_data.target_service_id)
    if not target:
        return None

    # 创建路由规则
    route = Route(**route_data.model_dump())
    db.add(route)
    await db.commit()
    await db.refresh(route)
    return route


async def update_route(
    db: AsyncSession,
    route_id: int,
    update_data: RouteUpdate
) -> Optional[Route]:
    """
    更新路由规则
    """
    route = await db.get(Route, route_id)
    if not route:
        return None

    # 如果更新了目标服务，验证其存在
    if update_data.target_service_id:
        target = await db.get(Service, update_data.target_service_id)
        if not target:
            return None

    # 更新字段
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(route, field, value)

    await db.commit()
    await db.refresh(route)
    return route


async def delete_route(db: AsyncSession, route_id: int) -> bool:
    """
    删除路由规则
    """
    result = await db.execute(
        delete(Route).where(Route.id == route_id)
    )
    await db.commit()
    return result.rowcount > 0


async def get_route(db: AsyncSession, route_id: int) -> Optional[Route]:
    """
    获取单个路由规则
    """
    return await db.get(Route, route_id)


async def get_all_routes(
    db: AsyncSession,
    gateway_id: Optional[str] = None,
    enabled_only: bool = False
) -> list[Route]:
    """
    获取路由规则列表
    可按网关过滤，可只获取启用的规则
    """
    query = select(Route)

    if gateway_id:
        query = query.where(Route.gateway_service_id == gateway_id)

    if enabled_only:
        query = query.where(Route.enabled == True)

    # 按优先级降序排序
    query = query.order_by(Route.priority.desc(), Route.created_at.desc())

    result = await db.execute(query)
    return list(result.scalars().all())


async def get_matching_route(
    db: AsyncSession,
    gateway_id: str,
    request_path: str
) -> Optional[Route]:
    """
    根据请求路径匹配路由规则
    返回优先级最高的匹配规则
    """
    # 获取该网关的所有启用的路由规则，按优先级排序
    routes = await get_all_routes(db, gateway_id=gateway_id, enabled_only=True)

    for route in routes:
        if match_path(route.path_pattern, request_path):
            return route

    return None


def match_path(pattern: str, path: str) -> bool:
    """
    路径匹配
    支持通配符 * 匹配任意字符
    例如: /api/docs/* 匹配 /api/docs/file.pdf
    """
    import fnmatch
    return fnmatch.fnmatch(path, pattern)


async def find_route_for_service(
    db: AsyncSession,
    gateway_id: str,
    target_service_id: str
) -> Optional[Route]:
    """
    查找网关到指定目标服务的路由规则

    用于动态组装认证服务的登录重定向路径。
    例如：查找 hermes -> aegis 的路由，返回 /aegis/** 规则，
    这样可以组装出 /aegis/admin/login 作为登录重定向路径。

    Args:
        db: 数据库会话
        gateway_id: 网关服务 ID
        target_service_id: 目标服务 ID

    Returns:
        匹配的路由规则，如果没有找到则返回 None
    """
    query = select(Route).where(
        and_(
            Route.gateway_service_id == gateway_id,
            Route.target_service_id == target_service_id,
            Route.enabled == True
        )
    ).order_by(Route.priority.desc())

    result = await db.execute(query)
    return result.scalars().first()

