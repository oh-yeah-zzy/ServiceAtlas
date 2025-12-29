"""
服务发现业务逻辑
处理服务查询和发现相关操作
"""
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.service import Service


async def discover_service(db: AsyncSession, service_id: str) -> Optional[Service]:
    """
    发现指定服务
    只返回状态为 healthy 的服务
    """
    service = await db.get(Service, service_id)
    if service and service.status == "healthy":
        return service
    return None


async def discover_all_healthy(db: AsyncSession) -> list[Service]:
    """
    发现所有健康的服务
    """
    query = select(Service).where(Service.status == "healthy")
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_gateways(db: AsyncSession) -> list[Service]:
    """
    获取所有网关服务
    """
    query = select(Service).where(Service.is_gateway == True)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_service_stats(db: AsyncSession) -> dict:
    """
    获取服务统计信息
    """
    # 总服务数
    total_query = select(func.count()).select_from(Service)
    total_result = await db.execute(total_query)
    total = total_result.scalar() or 0

    # 健康服务数
    healthy_query = select(func.count()).select_from(Service).where(
        Service.status == "healthy"
    )
    healthy_result = await db.execute(healthy_query)
    healthy = healthy_result.scalar() or 0

    # 不健康服务数
    unhealthy_query = select(func.count()).select_from(Service).where(
        Service.status == "unhealthy"
    )
    unhealthy_result = await db.execute(unhealthy_query)
    unhealthy = unhealthy_result.scalar() or 0

    # 未知状态服务数
    unknown = total - healthy - unhealthy

    # 网关数
    gateway_query = select(func.count()).select_from(Service).where(
        Service.is_gateway == True
    )
    gateway_result = await db.execute(gateway_query)
    gateways = gateway_result.scalar() or 0

    return {
        "total": total,
        "healthy": healthy,
        "unhealthy": unhealthy,
        "unknown": unknown,
        "gateways": gateways,
    }
