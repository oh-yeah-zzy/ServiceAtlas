"""
FastAPI 集成装饰器
提供更简洁的 FastAPI 应用注册方式
"""
from typing import Optional, Dict, Any
from functools import wraps

from serviceatlas_client.client import AsyncServiceAtlasClient


def register_service(
    registry_url: str,
    service_id: str,
    service_name: str,
    host: str,
    port: int,
    protocol: str = "http",
    health_check_path: str = "/health",
    is_gateway: bool = False,
    metadata: Optional[Dict[str, Any]] = None,
    heartbeat_interval: int = 30,
):
    """
    FastAPI 应用注册装饰器

    使用示例:
    ```python
    from fastapi import FastAPI
    from serviceatlas_client import register_service

    @register_service(
        registry_url="http://127.0.0.1:9000",
        service_id="deckview",
        service_name="DeckView 文档预览服务",
        host="127.0.0.1",
        port=8000,
    )
    def create_app():
        app = FastAPI()

        @app.get("/health")
        def health():
            return {"status": "healthy"}

        return app

    app = create_app()
    ```
    """
    def decorator(create_app_func):
        @wraps(create_app_func)
        def wrapper(*args, **kwargs):
            app = create_app_func(*args, **kwargs)

            # 创建客户端
            client = AsyncServiceAtlasClient(
                registry_url=registry_url,
                service_id=service_id,
                service_name=service_name,
                host=host,
                port=port,
                protocol=protocol,
                health_check_path=health_check_path,
                is_gateway=is_gateway,
                metadata=metadata,
                heartbeat_interval=heartbeat_interval,
            )

            # 注入生命周期事件
            original_on_event = getattr(app, 'on_event', None)

            @app.on_event("startup")
            async def startup_register():
                await client.start()

            @app.on_event("shutdown")
            async def shutdown_unregister():
                await client.stop()

            return app
        return wrapper
    return decorator


def fastapi_lifespan(
    registry_url: str,
    service_id: str,
    service_name: str,
    host: str,
    port: int,
    protocol: str = "http",
    health_check_path: str = "/health",
    is_gateway: bool = False,
    metadata: Optional[Dict[str, Any]] = None,
    heartbeat_interval: int = 30,
):
    """
    FastAPI lifespan 上下文管理器（推荐用于 FastAPI 0.95+）

    使用示例:
    ```python
    from fastapi import FastAPI
    from serviceatlas_client.decorators import fastapi_lifespan

    lifespan = fastapi_lifespan(
        registry_url="http://127.0.0.1:9000",
        service_id="deckview",
        service_name="DeckView 文档预览服务",
        host="127.0.0.1",
        port=8000,
    )

    app = FastAPI(lifespan=lifespan)
    ```
    """
    from contextlib import asynccontextmanager

    client = AsyncServiceAtlasClient(
        registry_url=registry_url,
        service_id=service_id,
        service_name=service_name,
        host=host,
        port=port,
        protocol=protocol,
        health_check_path=health_check_path,
        is_gateway=is_gateway,
        metadata=metadata,
        heartbeat_interval=heartbeat_interval,
    )

    @asynccontextmanager
    async def lifespan(app):
        # 启动时注册
        await client.start()
        yield
        # 关闭时注销
        await client.stop()

    return lifespan
