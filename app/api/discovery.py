"""
服务发现 API
处理服务查询和发现相关操作
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.service import ServiceResponse, ServiceListResponse
from app.services import registry as registry_service
from app.services import discovery as discovery_service


router = APIRouter()


@router.get(
    "/services",
    response_model=ServiceListResponse,
    summary="获取服务列表",
    description="获取所有注册的服务，支持按状态和类型过滤"
)
async def list_services(
    status: Optional[str] = Query(
        None,
        description="按状态过滤：healthy / unhealthy / unknown"
    ),
    is_gateway: Optional[bool] = Query(
        None,
        description="是否只获取网关服务"
    ),
    db: AsyncSession = Depends(get_db)
):
    """获取服务列表"""
    services = await registry_service.get_all_services(
        db, status=status, is_gateway=is_gateway
    )
    return ServiceListResponse(
        total=len(services),
        services=[
            ServiceResponse(
                **{k: v for k, v in s.__dict__.items() if not k.startswith("_")},
                base_url=s.base_url
            )
            for s in services
        ]
    )


@router.get(
    "/services/{service_id}",
    response_model=ServiceResponse,
    summary="获取服务详情",
    description="获取指定服务的详细信息"
)
async def get_service(
    service_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取服务详情"""
    service = await registry_service.get_service(db, service_id)
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"服务 '{service_id}' 不存在"
        )
    return ServiceResponse(
        **{k: v for k, v in service.__dict__.items() if not k.startswith("_")},
        base_url=service.base_url
    )


@router.get(
    "/gateways",
    response_model=ServiceListResponse,
    summary="获取网关列表",
    description="获取所有标记为网关的服务"
)
async def list_gateways(db: AsyncSession = Depends(get_db)):
    """获取网关服务列表"""
    gateways = await discovery_service.get_gateways(db)
    return ServiceListResponse(
        total=len(gateways),
        services=[
            ServiceResponse(
                **{k: v for k, v in s.__dict__.items() if not k.startswith("_")},
                base_url=s.base_url
            )
            for s in gateways
        ]
    )


@router.get(
    "/discover/{service_id}",
    response_model=ServiceResponse,
    summary="发现服务",
    description="发现指定服务（仅返回健康的服务）"
)
async def discover_service(
    service_id: str,
    db: AsyncSession = Depends(get_db)
):
    """发现服务（仅健康的）"""
    service = await discovery_service.discover_service(db, service_id)
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"服务 '{service_id}' 不存在或不健康"
        )
    return ServiceResponse(
        **{k: v for k, v in service.__dict__.items() if not k.startswith("_")},
        base_url=service.base_url
    )
