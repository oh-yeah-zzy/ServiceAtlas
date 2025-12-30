"""
ServiceAtlas Client
服务注册客户端，支持自动注册、心跳维护、优雅注销
"""
import asyncio
import atexit
import signal
import threading
from typing import Optional, Dict, Any
import httpx


class ServiceAtlasClient:
    """
    ServiceAtlas 注册客户端

    使用示例:
    ```python
    from serviceatlas_client import ServiceAtlasClient

    # 创建客户端
    client = ServiceAtlasClient(
        registry_url="http://127.0.0.1:9000",
        service_id="deckview",
        service_name="DeckView 文档预览服务",
        host="127.0.0.1",
        port=8000,
    )

    # 启动（注册 + 心跳）
    client.start()

    # 你的应用逻辑...

    # 程序退出时会自动注销（也可手动调用 client.stop()）
    ```
    """

    def __init__(
        self,
        registry_url: str,
        service_id: str,
        service_name: str,
        host: str,
        port: int,
        protocol: str = "http",
        health_check_path: str = "/health",
        is_gateway: bool = False,
        base_path: str = "",
        metadata: Optional[Dict[str, Any]] = None,
        heartbeat_interval: int = 30,
        trust_env: bool = True,
    ):
        """
        初始化客户端

        Args:
            registry_url: ServiceAtlas 注册中心地址（如 http://127.0.0.1:9000）
            service_id: 服务唯一标识
            service_name: 服务显示名称
            host: 服务地址
            port: 服务端口
            protocol: 协议（http/https）
            health_check_path: 健康检查路径
            is_gateway: 是否作为网关服务
            base_path: 代理路径前缀（通过网关代理时设置，如 /s/deckview）
            metadata: 扩展元数据
            heartbeat_interval: 心跳间隔（秒）
            trust_env: 是否信任环境变量中的代理配置（默认 True，设为 False 可禁用代理）
        """
        self.registry_url = registry_url.rstrip("/")
        self.service_id = service_id
        self.service_name = service_name
        self.host = host
        self.port = port
        self.protocol = protocol
        self.health_check_path = health_check_path
        self.is_gateway = is_gateway
        self.base_path = base_path
        self.metadata = metadata or {}
        self.heartbeat_interval = heartbeat_interval
        self.trust_env = trust_env

        self._running = False
        self._heartbeat_thread: Optional[threading.Thread] = None

        # 注册退出处理
        atexit.register(self.stop)
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """信号处理器，用于优雅退出"""
        self.stop()

    def start(self) -> bool:
        """
        启动客户端：注册服务并开始心跳

        Returns:
            注册是否成功
        """
        if self._running:
            return True

        # 注册服务
        if not self._register():
            return False

        # 启动心跳线程
        self._running = True
        self._heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop,
            daemon=True
        )
        self._heartbeat_thread.start()

        print(f"[ServiceAtlas] 服务 '{self.service_id}' 已注册并开始心跳")
        return True

    def stop(self):
        """停止客户端：停止心跳并注销服务"""
        if not self._running:
            return

        self._running = False

        # 等待心跳线程结束
        if self._heartbeat_thread and self._heartbeat_thread.is_alive():
            self._heartbeat_thread.join(timeout=2)

        # 注销服务
        self._unregister()
        print(f"[ServiceAtlas] 服务 '{self.service_id}' 已注销")

    def _register(self) -> bool:
        """注册服务到 ServiceAtlas"""
        try:
            # 构建注册数据
            register_data = {
                "id": self.service_id,
                "name": self.service_name,
                "host": self.host,
                "port": self.port,
                "protocol": self.protocol,
                "health_check_path": self.health_check_path,
                "is_gateway": self.is_gateway,
                "service_meta": self.metadata,
            }
            # 只有设置了 base_path 才发送该字段
            if self.base_path:
                register_data["base_path"] = self.base_path

            with httpx.Client(timeout=10, trust_env=self.trust_env) as client:
                response = client.post(
                    f"{self.registry_url}/api/v1/services",
                    json=register_data
                )
                if response.status_code in (200, 201):
                    return True
                else:
                    print(f"[ServiceAtlas] 注册失败: {response.text}")
                    return False
        except Exception as e:
            print(f"[ServiceAtlas] 注册异常: {e}")
            return False

    def _unregister(self):
        """从 ServiceAtlas 注销服务"""
        try:
            with httpx.Client(timeout=5, trust_env=self.trust_env) as client:
                client.delete(
                    f"{self.registry_url}/api/v1/services/{self.service_id}"
                )
        except Exception as e:
            print(f"[ServiceAtlas] 注销异常: {e}")

    def _heartbeat(self) -> bool:
        """发送一次心跳"""
        try:
            with httpx.Client(timeout=5, trust_env=self.trust_env) as client:
                response = client.post(
                    f"{self.registry_url}/api/v1/services/{self.service_id}/heartbeat"
                )
                return response.status_code == 200
        except Exception:
            return False

    def _heartbeat_loop(self):
        """心跳循环"""
        while self._running:
            self._heartbeat()
            # 分段等待，以便快速响应停止信号
            for _ in range(self.heartbeat_interval):
                if not self._running:
                    break
                threading.Event().wait(1)


class AsyncServiceAtlasClient:
    """
    异步版本的 ServiceAtlas 注册客户端
    适用于 FastAPI 等异步框架
    """

    def __init__(
        self,
        registry_url: str,
        service_id: str,
        service_name: str,
        host: str,
        port: int,
        protocol: str = "http",
        health_check_path: str = "/health",
        is_gateway: bool = False,
        base_path: str = "",
        metadata: Optional[Dict[str, Any]] = None,
        heartbeat_interval: int = 30,
        trust_env: bool = True,
    ):
        """
        初始化异步客户端

        Args:
            registry_url: ServiceAtlas 注册中心地址
            service_id: 服务唯一标识
            service_name: 服务显示名称
            host: 服务地址
            port: 服务端口
            protocol: 协议（http/https）
            health_check_path: 健康检查路径
            is_gateway: 是否作为网关服务
            base_path: 代理路径前缀（通过网关代理时设置，如 /s/deckview）
            metadata: 扩展元数据
            heartbeat_interval: 心跳间隔（秒）
            trust_env: 是否信任环境变量中的代理配置（默认 True，设为 False 可禁用代理）
        """
        self.registry_url = registry_url.rstrip("/")
        self.service_id = service_id
        self.service_name = service_name
        self.host = host
        self.port = port
        self.protocol = protocol
        self.health_check_path = health_check_path
        self.is_gateway = is_gateway
        self.base_path = base_path
        self.metadata = metadata or {}
        self.heartbeat_interval = heartbeat_interval
        self.trust_env = trust_env

        self._running = False
        self._heartbeat_task: Optional[asyncio.Task] = None

    async def start(self) -> bool:
        """启动客户端：注册服务并开始心跳"""
        if self._running:
            return True

        if not await self._register():
            return False

        self._running = True
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

        print(f"[ServiceAtlas] 服务 '{self.service_id}' 已注册并开始心跳")
        return True

    async def stop(self):
        """停止客户端：停止心跳并注销服务"""
        if not self._running:
            return

        self._running = False

        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass

        await self._unregister()
        print(f"[ServiceAtlas] 服务 '{self.service_id}' 已注销")

    async def _register(self) -> bool:
        """注册服务"""
        try:
            # 构建注册数据
            register_data = {
                "id": self.service_id,
                "name": self.service_name,
                "host": self.host,
                "port": self.port,
                "protocol": self.protocol,
                "health_check_path": self.health_check_path,
                "is_gateway": self.is_gateway,
                "service_meta": self.metadata,
            }
            # 只有设置了 base_path 才发送该字段
            if self.base_path:
                register_data["base_path"] = self.base_path

            async with httpx.AsyncClient(timeout=10, trust_env=self.trust_env) as client:
                response = await client.post(
                    f"{self.registry_url}/api/v1/services",
                    json=register_data
                )
                return response.status_code in (200, 201)
        except Exception as e:
            print(f"[ServiceAtlas] 注册异常: {e}")
            return False

    async def _unregister(self):
        """注销服务"""
        try:
            async with httpx.AsyncClient(timeout=5, trust_env=self.trust_env) as client:
                await client.delete(
                    f"{self.registry_url}/api/v1/services/{self.service_id}"
                )
        except Exception:
            pass

    async def _heartbeat_loop(self):
        """心跳循环"""
        while self._running:
            try:
                async with httpx.AsyncClient(timeout=5, trust_env=self.trust_env) as client:
                    await client.post(
                        f"{self.registry_url}/api/v1/services/{self.service_id}/heartbeat"
                    )
            except Exception:
                pass
            await asyncio.sleep(self.heartbeat_interval)
