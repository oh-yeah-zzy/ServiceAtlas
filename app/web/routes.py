"""
Web 管理界面路由
提供仪表盘、服务管理、拓扑图等页面
"""
from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import BASE_DIR, settings
from app.database import get_db
from app.services import discovery as discovery_service
from app.services import dependency as dependency_service


router = APIRouter()

# 模板引擎
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def get_template_context(request: Request, title: str, **kwargs) -> dict:
    """生成模板上下文，自动包含 base_path"""
    return {
        "request": request,
        "title": title,
        "base_path": settings.base_path.rstrip("/"),
        **kwargs,
    }


@router.get("/", include_in_schema=False)
async def dashboard(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """仪表盘首页"""
    stats = await discovery_service.get_service_stats(db)
    return templates.TemplateResponse(
        "dashboard.html",
        get_template_context(request, "ServiceAtlas - 仪表盘", stats=stats)
    )


@router.get("/services", include_in_schema=False)
async def services_page(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """服务列表页面"""
    from app.services import registry as registry_service
    services = await registry_service.get_all_services(db)
    return templates.TemplateResponse(
        "services.html",
        get_template_context(request, "ServiceAtlas - 服务管理", services=services)
    )


@router.get("/topology", include_in_schema=False)
async def topology_page(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """依赖拓扑图页面"""
    topology = await dependency_service.get_topology(db)
    return templates.TemplateResponse(
        "topology.html",
        get_template_context(request, "ServiceAtlas - 依赖拓扑", topology=topology.model_dump())
    )
