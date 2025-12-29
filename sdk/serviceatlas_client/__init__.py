"""
ServiceAtlas Client SDK
轻量级 Python SDK，用于将服务自动注册到 ServiceAtlas 注册中心
"""
from serviceatlas_client.client import ServiceAtlasClient
from serviceatlas_client.decorators import register_service

__version__ = "1.0.0"
__all__ = ["ServiceAtlasClient", "register_service"]
