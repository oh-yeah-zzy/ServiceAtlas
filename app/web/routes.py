"""
Web 管理界面路由

⚠️ 已迁移到 Vue SPA：所有 Jinja2 页面现在 302 跳转到 Vue 前端
保留这些路由是为了兼容旧链接
"""
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from app.config import settings


router = APIRouter()


def get_base_path(request: Request) -> str:
    """
    获取 base path，优先从代理 header 读取

    当通过 Hermes 网关代理访问时，X-Forwarded-Prefix 会包含路径前缀（如 /serviceatlas）
    直接访问时使用配置中的 base_path
    """
    forwarded_prefix = request.headers.get("X-Forwarded-Prefix", "").rstrip("/")
    if forwarded_prefix:
        return forwarded_prefix
    return settings.base_path.rstrip("/")


def get_vue_app_url(request: Request, hash_path: str = "/") -> str:
    """
    构建 Vue SPA 的 URL

    Args:
        request: FastAPI Request 对象
        hash_path: Vue 的 hash 路由路径，如 /、/services、/topology

    Returns:
        完整的 Vue SPA URL，如 /serviceatlas/app/#/services
    """
    base_path = get_base_path(request)
    return f"{base_path}/app/#{hash_path}"


@router.get("/", include_in_schema=False)
async def root(request: Request):
    """根路径 - 重定向到 Vue 前端"""
    return RedirectResponse(url=get_vue_app_url(request, "/"), status_code=302)


@router.get("/dashboard", include_in_schema=False)
async def dashboard(request: Request):
    """仪表盘首页 - 302 跳转到 Vue"""
    return RedirectResponse(url=get_vue_app_url(request, "/"), status_code=302)


@router.get("/services", include_in_schema=False)
async def services_page(request: Request):
    """服务列表页面 - 302 跳转到 Vue"""
    return RedirectResponse(url=get_vue_app_url(request, "/services"), status_code=302)


@router.get("/topology", include_in_schema=False)
async def topology_page(request: Request):
    """依赖拓扑图页面 - 302 跳转到 Vue"""
    return RedirectResponse(url=get_vue_app_url(request, "/topology"), status_code=302)
