"""
依赖管理 API
处理服务间依赖关系的增删查和拓扑图数据
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.dependency import (
    DependencyCreate,
    DependencyResponse,
    TopologyResponse
)
from app.services import dependency as dependency_service


router = APIRouter()


@router.post(
    "/dependencies",
    response_model=DependencyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建依赖关系",
    description="创建服务间的依赖关系"
)
async def create_dependency(
    dependency_data: DependencyCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建依赖关系"""
    dependency = await dependency_service.create_dependency(db, dependency_data)
    if not dependency:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="源服务或目标服务不存在"
        )
    return dependency


@router.get(
    "/dependencies",
    response_model=list[DependencyResponse],
    summary="获取所有依赖关系",
    description="获取系统中定义的所有服务依赖关系"
)
async def list_dependencies(db: AsyncSession = Depends(get_db)):
    """获取所有依赖关系"""
    return await dependency_service.get_all_dependencies(db)


@router.delete(
    "/dependencies/{dependency_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除依赖关系",
    description="删除指定的依赖关系"
)
async def delete_dependency(
    dependency_id: int,
    db: AsyncSession = Depends(get_db)
):
    """删除依赖关系"""
    success = await dependency_service.delete_dependency(db, dependency_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"依赖关系 ID={dependency_id} 不存在"
        )
    return None


@router.get(
    "/services/{service_id}/dependencies",
    response_model=list[DependencyResponse],
    summary="获取服务的依赖",
    description="获取指定服务依赖的其他服务（作为调用方）"
)
async def get_service_dependencies(
    service_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取服务的依赖（作为调用方）"""
    return await dependency_service.get_service_dependencies(
        db, service_id, as_source=True
    )


@router.get(
    "/services/{service_id}/dependents",
    response_model=list[DependencyResponse],
    summary="获取服务的被依赖方",
    description="获取依赖指定服务的其他服务（作为被调用方）"
)
async def get_service_dependents(
    service_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取依赖该服务的其他服务"""
    return await dependency_service.get_service_dependencies(
        db, service_id, as_source=False
    )


@router.get(
    "/topology",
    response_model=TopologyResponse,
    summary="获取拓扑图数据",
    description="获取服务依赖拓扑图的节点和边数据，用于前端可视化"
)
async def get_topology(db: AsyncSession = Depends(get_db)):
    """获取拓扑图数据"""
    return await dependency_service.get_topology(db)
