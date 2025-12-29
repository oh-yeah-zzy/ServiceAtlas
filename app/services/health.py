"""
健康检查业务逻辑
定时检查注册服务的健康状态
"""
import asyncio
from datetime import datetime, timedelta
from typing import Optional

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import async_session_maker
from app.models.service import Service


async def check_service_health(service: Service) -> bool:
    """
    检查单个服务的健康状态
    通过 HTTP GET 请求服务的健康检查路径
    返回 True 表示健康，False 表示不健康
    """
    try:
        async with httpx.AsyncClient(timeout=settings.health_check_timeout) as client:
            response = await client.get(service.health_url)
            # 2xx 状态码认为是健康的
            return 200 <= response.status_code < 300
    except Exception:
        return False


async def update_service_status(
    db: AsyncSession,
    service: Service,
    is_healthy: bool
) -> None:
    """
    更新服务的健康状态
    根据检查结果和连续失败次数更新状态
    """
    if is_healthy:
        # 健康，重置失败计数
        service.status = "healthy"
        service.consecutive_failures = 0
    else:
        # 不健康，增加失败计数
        service.consecutive_failures += 1

        # 超过阈值则标记为不健康
        if service.consecutive_failures >= settings.unhealthy_threshold:
            service.status = "unhealthy"

    await db.commit()


async def check_all_services() -> dict:
    """
    检查所有注册服务的健康状态
    返回检查结果统计
    """
    async with async_session_maker() as db:
        # 获取所有服务
        query = select(Service)
        result = await db.execute(query)
        services = result.scalars().all()

        checked = 0
        healthy = 0
        unhealthy = 0

        for service in services:
            is_healthy = await check_service_health(service)
            await update_service_status(db, service, is_healthy)

            checked += 1
            if is_healthy:
                healthy += 1
            else:
                unhealthy += 1

        return {
            "checked": checked,
            "healthy": healthy,
            "unhealthy": unhealthy,
            "timestamp": datetime.utcnow().isoformat()
        }


async def check_heartbeat_timeout() -> int:
    """
    检查心跳超时的服务
    将超时未收到心跳的服务标记为 unhealthy
    返回标记的服务数量
    """
    async with async_session_maker() as db:
        timeout_threshold = datetime.utcnow() - timedelta(
            seconds=settings.heartbeat_timeout
        )

        # 查找心跳超时的服务
        query = select(Service).where(
            Service.last_heartbeat < timeout_threshold,
            Service.status != "unhealthy"
        )
        result = await db.execute(query)
        services = result.scalars().all()

        count = 0
        for service in services:
            service.status = "unhealthy"
            count += 1

        await db.commit()
        return count
