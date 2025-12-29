"""
服务注册 API
处理服务的注册、注销、更新、心跳等操作
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.service import ServiceCreate, ServiceUpdate, ServiceResponse
from app.services import registry as registry_service


router = APIRouter()


@router.post(
    "/services",
    response_model=ServiceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="注册服务",
    description="注册新服务到注册中心。如果服务 ID 已存在，则更新该服务的信息。"
)
async def register_service(
    service_data: ServiceCreate,
    db: AsyncSession = Depends(get_db)
):
    """注册或更新服务"""
    service = await registry_service.register_service(db, service_data)
    return ServiceResponse(
        **{k: v for k, v in service.__dict__.items() if not k.startswith("_")},
        base_url=service.base_url
    )


@router.delete(
    "/services/{service_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="注销服务",
    description="从注册中心注销指定服务"
)
async def unregister_service(
    service_id: str,
    db: AsyncSession = Depends(get_db)
):
    """注销服务"""
    success = await registry_service.unregister_service(db, service_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"服务 '{service_id}' 不存在"
        )
    return None


@router.put(
    "/services/{service_id}",
    response_model=ServiceResponse,
    summary="更新服务",
    description="更新服务的配置信息"
)
async def update_service(
    service_id: str,
    update_data: ServiceUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新服务信息"""
    service = await registry_service.update_service(db, service_id, update_data)
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"服务 '{service_id}' 不存在"
        )
    return ServiceResponse(
        **{k: v for k, v in service.__dict__.items() if not k.startswith("_")},
        base_url=service.base_url
    )


@router.post(
    "/services/{service_id}/heartbeat",
    response_model=ServiceResponse,
    summary="心跳上报",
    description="服务主动上报心跳，更新最后心跳时间并将状态设为 healthy"
)
async def heartbeat(
    service_id: str,
    db: AsyncSession = Depends(get_db)
):
    """心跳上报"""
    service = await registry_service.heartbeat(db, service_id)
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"服务 '{service_id}' 不存在"
        )
    return ServiceResponse(
        **{k: v for k, v in service.__dict__.items() if not k.startswith("_")},
        base_url=service.base_url
    )
