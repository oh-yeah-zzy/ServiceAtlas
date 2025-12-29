"""
监控统计 API
提供服务状态统计和监控信息
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services import discovery as discovery_service
from app.services import health as health_service


router = APIRouter()


@router.get(
    "/monitor/overview",
    summary="监控概览",
    description="获取服务注册中心的整体监控统计信息"
)
async def get_overview(db: AsyncSession = Depends(get_db)):
    """获取监控概览"""
    stats = await discovery_service.get_service_stats(db)
    return {
        "status": "running",
        "services": stats,
    }


@router.post(
    "/monitor/health-check",
    summary="触发健康检查",
    description="手动触发一次全量健康检查"
)
async def trigger_health_check():
    """手动触发健康检查"""
    result = await health_service.check_all_services()
    return {
        "message": "健康检查完成",
        "result": result
    }
