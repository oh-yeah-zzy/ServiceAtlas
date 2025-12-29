# ServiceAtlas Client SDK

轻量级 Python SDK，用于将服务自动注册到 ServiceAtlas 注册中心。

## 安装

```bash
# 从本地安装
pip install -e ./sdk

# 或直接复制 serviceatlas_client 目录到你的项目
```

## 使用方式

### 方式一：直接使用客户端（通用）

```python
from serviceatlas_client import ServiceAtlasClient

# 创建客户端
client = ServiceAtlasClient(
    registry_url="http://127.0.0.1:9000",
    service_id="deckview",
    service_name="DeckView 文档预览服务",
    host="127.0.0.1",
    port=8000,
    health_check_path="/health",
    metadata={"version": "1.0.0"}
)

# 启动（注册 + 心跳）
client.start()

# 你的应用逻辑...
# 程序退出时会自动注销
```

### 方式二：FastAPI lifespan（推荐）

```python
from fastapi import FastAPI
from serviceatlas_client.decorators import fastapi_lifespan

# 创建 lifespan 上下文
lifespan = fastapi_lifespan(
    registry_url="http://127.0.0.1:9000",
    service_id="deckview",
    service_name="DeckView 文档预览服务",
    host="127.0.0.1",
    port=8000,
)

# 应用 lifespan
app = FastAPI(lifespan=lifespan)

@app.get("/health")
def health():
    return {"status": "healthy"}
```

### 方式三：异步客户端（手动控制）

```python
from serviceatlas_client.client import AsyncServiceAtlasClient

client = AsyncServiceAtlasClient(
    registry_url="http://127.0.0.1:9000",
    service_id="deckview",
    service_name="DeckView",
    host="127.0.0.1",
    port=8000,
)

# 在异步上下文中使用
async def main():
    await client.start()
    # ...
    await client.stop()
```

## 配置参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| registry_url | str | - | ServiceAtlas 注册中心地址 |
| service_id | str | - | 服务唯一标识 |
| service_name | str | - | 服务显示名称 |
| host | str | - | 服务地址 |
| port | int | - | 服务端口 |
| protocol | str | "http" | 协议类型 |
| health_check_path | str | "/health" | 健康检查路径 |
| is_gateway | bool | False | 是否作为网关 |
| metadata | dict | None | 扩展元数据 |
| heartbeat_interval | int | 30 | 心跳间隔（秒） |
