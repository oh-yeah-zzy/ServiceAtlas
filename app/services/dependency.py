"""
依赖关系业务逻辑
处理服务间依赖关系的管理和拓扑图生成
"""
from typing import Optional

from sqlalchemy import select, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.service import Service
from app.models.dependency import Dependency
from app.schemas.dependency import DependencyCreate, TopologyNode, TopologyEdge, TopologyResponse


async def create_dependency(
    db: AsyncSession,
    dependency_data: DependencyCreate
) -> Optional[Dependency]:
    """
    创建依赖关系
    如果源服务或目标服务不存在，返回 None
    """
    # 验证两个服务都存在
    source = await db.get(Service, dependency_data.source_service_id)
    target = await db.get(Service, dependency_data.target_service_id)

    if not source or not target:
        return None

    # 检查是否已存在相同的依赖关系
    existing_query = select(Dependency).where(
        and_(
            Dependency.source_service_id == dependency_data.source_service_id,
            Dependency.target_service_id == dependency_data.target_service_id
        )
    )
    existing_result = await db.execute(existing_query)
    if existing_result.scalar_one_or_none():
        # 已存在，返回现有的
        return existing_result.scalar_one_or_none()

    # 创建新的依赖关系
    dependency = Dependency(**dependency_data.model_dump())
    db.add(dependency)
    await db.commit()
    await db.refresh(dependency)
    return dependency


async def delete_dependency(db: AsyncSession, dependency_id: int) -> bool:
    """
    删除依赖关系
    """
    result = await db.execute(
        delete(Dependency).where(Dependency.id == dependency_id)
    )
    await db.commit()
    return result.rowcount > 0


async def get_all_dependencies(db: AsyncSession) -> list[Dependency]:
    """
    获取所有依赖关系
    """
    query = select(Dependency).order_by(Dependency.created_at.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_service_dependencies(
    db: AsyncSession,
    service_id: str,
    as_source: bool = True
) -> list[Dependency]:
    """
    获取指定服务的依赖关系
    as_source=True: 获取该服务作为调用方的依赖（该服务依赖的其他服务）
    as_source=False: 获取该服务作为被调用方的依赖（依赖该服务的其他服务）
    """
    if as_source:
        query = select(Dependency).where(
            Dependency.source_service_id == service_id
        )
    else:
        query = select(Dependency).where(
            Dependency.target_service_id == service_id
        )

    result = await db.execute(query)
    return list(result.scalars().all())


async def get_topology(db: AsyncSession) -> TopologyResponse:
    """
    获取服务依赖拓扑图数据
    返回节点和边的数据，用于前端可视化
    """
    # 获取所有服务作为节点
    services_query = select(Service)
    services_result = await db.execute(services_query)
    services = services_result.scalars().all()

    nodes = [
        TopologyNode(
            id=s.id,
            name=s.name,
            status=s.status,
            is_gateway=s.is_gateway
        )
        for s in services
    ]

    # 获取所有依赖关系作为边
    deps_query = select(Dependency)
    deps_result = await db.execute(deps_query)
    dependencies = deps_result.scalars().all()

    edges = [
        TopologyEdge(
            source=d.source_service_id,
            target=d.target_service_id,
            description=d.description
        )
        for d in dependencies
    ]

    return TopologyResponse(nodes=nodes, edges=edges)
