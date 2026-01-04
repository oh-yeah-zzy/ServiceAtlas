"""
ServiceAtlas - 轻量级服务注册中心
FastAPI 应用入口
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import settings, BASE_DIR
from app.database import init_db, async_session_maker
from app.api import api_router
from app.web.routes import router as web_router
from app.services.health import check_all_services, check_heartbeat_timeout
from app.services.preload import preload_services
from app.services.registry import register_service, heartbeat as service_heartbeat
from app.schemas.service import ServiceCreate


# 健康检查调度器
scheduler = AsyncIOScheduler()


async def self_heartbeat():
    """ServiceAtlas 自心跳任务"""
    if settings.self_register:
        async with async_session_maker() as db:
            await service_heartbeat(db, settings.service_id)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    # 初始化数据库
    await init_db()
    print(f"数据库初始化完成")

    # 从配置文件预加载服务
    async with async_session_maker() as db:
        await preload_services(db)

        # 自注册：将 ServiceAtlas 自己注册到服务列表
        if settings.self_register:
            self_service = ServiceCreate(
                id=settings.service_id,
                name=f"{settings.app_name} 服务注册中心",
                host=settings.host,
                port=settings.port,
                protocol="http",
                health_check_path="/health",
                is_gateway=False,
                base_path=settings.base_path if settings.base_path else None,
                service_meta={
                    "version": settings.app_version,
                    "description": "服务注册与发现中心",
                    # 声明认证需求，网关会自动应用到路由规则
                    "auth_config": {
                        "require_auth": True,
                        "auth_service_id": "aegis",
                        "public_paths": [
                            "/health",
                            "/docs",
                            "/redoc",
                            "/openapi.json",
                        ],
                    },
                },
            )
            await register_service(db, self_service)
            print(f"ServiceAtlas 已自注册（ID: {settings.service_id}, base_path: {settings.base_path or '未设置'}）")

    # 启动健康检查定时任务
    scheduler.add_job(
        check_all_services,
        'interval',
        seconds=settings.health_check_interval,
        id='health_check'
    )
    scheduler.add_job(
        check_heartbeat_timeout,
        'interval',
        seconds=settings.health_check_interval,
        id='heartbeat_timeout'
    )
    # 自心跳任务（保持 ServiceAtlas 自己的 healthy 状态）
    if settings.self_register:
        scheduler.add_job(
            self_heartbeat,
            'interval',
            seconds=30,  # 每 30 秒发送一次自心跳
            id='self_heartbeat'
        )
    scheduler.start()
    print(f"健康检查调度器已启动（间隔: {settings.health_check_interval}秒）")

    print(f"\n{'='*50}")
    print(f"  ServiceAtlas 服务注册中心已启动")
    print(f"  访问地址: http://{settings.host}:{settings.port}")
    print(f"  API 文档: http://{settings.host}:{settings.port}/docs")
    print(f"{'='*50}\n")

    yield

    # 关闭时
    scheduler.shutdown()
    print("健康检查调度器已停止")


# 创建 FastAPI 应用
app = FastAPI(
    title="ServiceAtlas",
    description="轻量级服务注册中心 - 支持服务注册/发现、依赖管理、网关路由、服务监控",
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# 挂载静态文件
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# 注册 API 路由
app.include_router(api_router, prefix=settings.api_prefix)

# 注册 Web 界面路由
app.include_router(web_router)


# 健康检查端点（供自身健康检查）
@app.get("/health", tags=["健康检查"])
async def health():
    """服务健康检查端点"""
    return {"status": "healthy", "service": "ServiceAtlas"}


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """返回空的 favicon，避免 404 错误"""
    return Response(status_code=204)
