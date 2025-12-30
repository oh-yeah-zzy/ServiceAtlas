"""
服务注册业务逻辑
处理服务的注册、注销、更新等操作
"""
import re
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.service import Service
from app.models.route import Route
from app.schemas.service import ServiceCreate, ServiceUpdate


def generate_service_id(name: str) -> str:
    """
    根据服务名称生成唯一ID

    格式：{normalized_name}-{short_uuid}
    例如：deckview-a1b2c3d4
    """
    # 将名称转换为 URL 友好的格式
    # 移除非字母数字字符，转小写，用连字符替换空格
    normalized = re.sub(r'[^a-zA-Z0-9\s-]', '', name.lower())
    normalized = re.sub(r'[\s_]+', '-', normalized)
    normalized = re.sub(r'-+', '-', normalized).strip('-')

    # 如果名称为空，使用 'service'
    if not normalized:
        normalized = 'service'

    # 截取前20个字符，确保总长度不超过64
    normalized = normalized[:20]

    # 添加短UUID（8位）
    short_uuid = uuid.uuid4().hex[:8]

    return f"{normalized}-{short_uuid}"


async def register_service(db: AsyncSession, service_data: ServiceCreate) -> Service:
    """
    注册新服务
    - 如果未提供 ID，自动生成唯一ID
    - 如果提供了 ID 且已存在，更新该服务信息
    - 自动为非网关服务创建默认路由规则
    """
    # 如果未提供 ID，自动生成
    service_id = service_data.id
    if not service_id:
        service_id = generate_service_id(service_data.name)

    # 检查服务是否已存在
    existing = await db.get(Service, service_id)

    if existing:
        # 服务已存在，更新信息
        data_dict = service_data.model_dump(exclude_unset=True)
        data_dict.pop('id', None)  # 不更新 ID
        for field, value in data_dict.items():
            setattr(existing, field, value)
        existing.last_heartbeat = datetime.utcnow()
        existing.status = "unknown"  # 重新注册后重置状态
        existing.consecutive_failures = 0
        await db.commit()
        await db.refresh(existing)
        return existing
    else:
        # 创建新服务
        # base_path 只有在明确指定时才设置，不自动生成
        service = Service(
            id=service_id,
            name=service_data.name,
            host=service_data.host,
            port=service_data.port,
            protocol=service_data.protocol,
            health_check_path=service_data.health_check_path,
            is_gateway=service_data.is_gateway,
            base_path=service_data.base_path,  # 可能为 None
            service_meta=service_data.service_meta,
            registered_at=datetime.utcnow(),
            last_heartbeat=datetime.utcnow(),
            status="unknown",
            consecutive_failures=0,
        )
        db.add(service)
        await db.flush()  # 获取服务ID

        # 为非网关服务自动创建默认路由规则
        if not service_data.is_gateway:
            await _create_default_route(db, service)

        await db.commit()
        await db.refresh(service)
        return service


async def _create_default_route(db: AsyncSession, service: Service):
    """
    为服务创建默认路由规则

    路由模式：/{service_id}/** → 该服务
    """
    # 查找网关服务（如果有多个，选第一个）
    result = await db.execute(
        select(Service).where(Service.is_gateway == True).limit(1)
    )
    gateway = result.scalar_one_or_none()

    if not gateway:
        # 没有网关服务，不创建路由
        return

    # 检查是否已存在该服务的路由
    existing_route = await db.execute(
        select(Route).where(Route.target_service_id == service.id)
    )
    if existing_route.scalar_one_or_none():
        # 已存在路由，不重复创建
        return

    # 创建默认路由
    route = Route(
        gateway_service_id=gateway.id,
        path_pattern=f"/{service.id}/**",
        target_service_id=service.id,
        strip_prefix=True,
        strip_path=f"/{service.id}",
        priority=10,
        enabled=True,
    )
    db.add(route)


async def unregister_service(db: AsyncSession, service_id: str) -> bool:
    """
    注销服务
    返回是否成功删除（如果服务不存在返回 False）
    """
    result = await db.execute(
        delete(Service).where(Service.id == service_id)
    )
    await db.commit()
    return result.rowcount > 0


async def update_service(
    db: AsyncSession,
    service_id: str,
    update_data: ServiceUpdate
) -> Optional[Service]:
    """
    更新服务信息
    返回更新后的服务，如果服务不存在返回 None
    """
    service = await db.get(Service, service_id)
    if not service:
        return None

    # 只更新提供的字段
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(service, field, value)

    await db.commit()
    await db.refresh(service)
    return service


async def get_service(db: AsyncSession, service_id: str) -> Optional[Service]:
    """
    获取单个服务信息
    """
    return await db.get(Service, service_id)


async def get_all_services(
    db: AsyncSession,
    status: Optional[str] = None,
    is_gateway: Optional[bool] = None
) -> list[Service]:
    """
    获取服务列表，支持按状态和是否网关过滤
    """
    query = select(Service)

    if status:
        query = query.where(Service.status == status)

    if is_gateway is not None:
        query = query.where(Service.is_gateway == is_gateway)

    query = query.order_by(Service.registered_at.desc())

    result = await db.execute(query)
    return list(result.scalars().all())


async def heartbeat(db: AsyncSession, service_id: str) -> Optional[Service]:
    """
    更新服务心跳时间
    同时将状态标记为 healthy（如果之前不是）
    """
    service = await db.get(Service, service_id)
    if not service:
        return None

    service.last_heartbeat = datetime.utcnow()
    service.status = "healthy"
    service.consecutive_failures = 0

    await db.commit()
    await db.refresh(service)
    return service
