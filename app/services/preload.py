"""
配置文件加载器
支持从 services.yaml 加载预注册的服务、依赖和路由
"""
from pathlib import Path
from typing import Optional
import yaml

from app.config import BASE_DIR


def load_services_config(config_path: Optional[Path] = None) -> dict:
    """
    加载服务配置文件

    Args:
        config_path: 配置文件路径，默认为项目根目录下的 services.yaml

    Returns:
        配置字典，包含 services, dependencies, routes
    """
    if config_path is None:
        config_path = BASE_DIR / "services.yaml"

    if not config_path.exists():
        return {"services": [], "dependencies": [], "routes": []}

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}

        return {
            "services": config.get("services", []) or [],
            "dependencies": config.get("dependencies", []) or [],
            "routes": config.get("routes", []) or [],
        }
    except Exception as e:
        print(f"[ServiceAtlas] 加载配置文件失败: {e}")
        return {"services": [], "dependencies": [], "routes": []}


async def preload_services(db_session):
    """
    预加载配置文件中的服务到数据库

    Args:
        db_session: 数据库会话
    """
    from app.schemas.service import ServiceCreate
    from app.schemas.dependency import DependencyCreate
    from app.schemas.route import RouteCreate
    from app.services import registry as registry_service
    from app.services import dependency as dependency_service
    from app.services import gateway as gateway_service

    config = load_services_config()

    # 预注册服务
    services_count = 0
    for svc in config["services"]:
        try:
            service_data = ServiceCreate(
                id=svc["id"],
                name=svc["name"],
                host=svc["host"],
                port=svc["port"],
                protocol=svc.get("protocol", "http"),
                health_check_path=svc.get("health_check_path", "/health"),
                is_gateway=svc.get("is_gateway", False),
                service_meta=svc.get("metadata"),
            )
            await registry_service.register_service(db_session, service_data)
            services_count += 1
        except Exception as e:
            print(f"[ServiceAtlas] 预注册服务 '{svc.get('id', '?')}' 失败: {e}")

    # 预创建依赖关系
    deps_count = 0
    for dep in config["dependencies"]:
        try:
            dep_data = DependencyCreate(
                source_service_id=dep["source"],
                target_service_id=dep["target"],
                description=dep.get("description"),
            )
            result = await dependency_service.create_dependency(db_session, dep_data)
            if result:
                deps_count += 1
        except Exception as e:
            print(f"[ServiceAtlas] 预创建依赖关系失败: {e}")

    # 预创建路由规则
    routes_count = 0
    for route in config["routes"]:
        try:
            route_data = RouteCreate(
                gateway_service_id=route["gateway"],
                path_pattern=route["path_pattern"],
                target_service_id=route["target"],
                strip_prefix=route.get("strip_prefix", False),
                strip_path=route.get("strip_path"),
                priority=route.get("priority", 0),
                auth_config=route.get("auth_config"),  # 支持认证配置
            )
            result = await gateway_service.create_route(db_session, route_data)
            if result:
                routes_count += 1
        except Exception as e:
            print(f"[ServiceAtlas] 预创建路由规则失败: {e}")

    if services_count > 0 or deps_count > 0 or routes_count > 0:
        print(f"[ServiceAtlas] 预加载完成: {services_count} 个服务, {deps_count} 个依赖, {routes_count} 条路由")
