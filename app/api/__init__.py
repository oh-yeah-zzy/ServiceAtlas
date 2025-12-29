# API 路由模块
from fastapi import APIRouter

from app.api.registry import router as registry_router
from app.api.discovery import router as discovery_router
from app.api.dependency import router as dependency_router
from app.api.gateway import router as gateway_router
from app.api.monitor import router as monitor_router


# 主 API 路由器
api_router = APIRouter()

# 注册子路由
api_router.include_router(registry_router, tags=["服务注册"])
api_router.include_router(discovery_router, tags=["服务发现"])
api_router.include_router(dependency_router, tags=["依赖管理"])
api_router.include_router(gateway_router, tags=["网关路由"])
api_router.include_router(monitor_router, tags=["监控统计"])
