# ServiceAtlas

<p align="center">
  <strong>轻量级服务注册中心</strong><br>
  服务注册/发现 · 依赖管理 · 网关路由 · 可视化监控
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-0.104+-green.svg" alt="FastAPI">
  <img src="https://img.shields.io/badge/SQLite-Async-orange.svg" alt="SQLite">
  <img src="https://img.shields.io/badge/License-MIT-purple.svg" alt="License">
</p>

---

## 概述

ServiceAtlas 是一个轻量级的服务注册中心，专为中小型微服务架构设计。它提供服务注册与发现、依赖关系管理、可自定义网关路由、健康检查监控等核心功能，并附带直观的 Web 管理界面。

### 核心特性

| 特性 | 说明 |
|------|------|
| **服务注册/发现** | 自动注册、心跳检测、健康检查、服务发现 |
| **依赖管理** | 定义服务间调用关系，生成可视化拓扑图 |
| **网关路由** | 可自定义任意服务为入口网关，配置路由转发规则 |
| **服务监控** | 实时状态监控、健康统计、告警提示 |
| **Web 界面** | 仪表盘、服务管理、依赖拓扑可视化 |
| **SDK 支持** | Python SDK 实现自动注册与心跳维护 |

### 技术栈

- **后端**: Python 3.9+ / FastAPI / SQLAlchemy 2.0 (async)
- **数据库**: SQLite (aiosqlite)
- **HTTP 客户端**: httpx
- **定时任务**: APScheduler
- **前端**: Vue 3 + Vite（支持中英文切换）/ Jinja2（传统模板）

---

## 快速开始

### 1. 安装依赖

```bash
cd ServiceAtlas
pip install -r requirements.txt
```

### 2. 启动服务

```bash
# 生产模式
python run.py

# 开发模式（热重载）
python run.py --reload --debug

# 自定义地址和端口
python run.py --host 0.0.0.0 --port 8888
```

### 3. 访问

| 地址 | 说明 |
|------|------|
| http://127.0.0.1:8888 | Web 管理界面（Jinja2 传统版） |
| http://127.0.0.1:8888/app | Web 管理界面（Vue 新版，需先构建） |
| http://127.0.0.1:8888/docs | Swagger API 文档 |
| http://127.0.0.1:8888/redoc | ReDoc API 文档 |

---

## 前端开发

ServiceAtlas 提供两套前端界面：
- **Vue 3 版本**（推荐）：位于 `frontend/` 目录，支持中英文切换，**所有新功能将只在此版本开发**
- **Jinja2 版本**（⚠️ Deprecated）：位于 `templates/` 目录，仅作为向后兼容保留，未来版本将移除

### Vue 前端开发

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 开发模式（热重载，访问 http://localhost:3000）
npm run dev

# 构建生产版本（输出到 ../static/app/）
npm run build
```

构建完成后，访问 `http://127.0.0.1:8888/app` 即可使用 Vue 新版界面。

### 国际化

Vue 前端支持中英文切换：
- 翻译文件位于 `frontend/src/locales/`
- 导航栏右上角提供语言切换按钮
- 语言偏好自动保存到浏览器 localStorage

---

## 服务注册方式

ServiceAtlas 支持三种服务注册方式，可根据场景灵活选择：

### 方式一：配置文件预注册

编辑项目根目录的 `services.yaml`，ServiceAtlas 启动时自动加载：

```yaml
services:
  # DeckView 文档服务
  - id: deckview
    name: DeckView 文档预览服务
    host: 127.0.0.1
    port: 8000
    protocol: http
    health_check_path: /docs
    is_gateway: false
    base_path: /s/deckview  # 通过 Aegis 网关代理时的路径前缀
    metadata:
      version: "1.0.0"
      description: 在线预览 PPT、PDF、Word、Markdown 文件

  # 权限网关（设为入口）
  - id: auth-gateway
    name: 权限认证网关
    host: 127.0.0.1
    port: 8080
    is_gateway: true

# 预定义依赖关系
dependencies:
  - source: auth-gateway
    target: deckview
    description: 网关转发文档请求

# 预定义路由规则
routes:
  - gateway: auth-gateway
    path_pattern: /docs/*
    target: deckview
    strip_prefix: true
    strip_path: /docs
```

**优点**: 无需修改服务代码，集中管理
**适用**: 已知服务列表、静态部署环境

---

### 方式二：SDK 自动注册（推荐）

#### 安装 SDK

```bash
pip install -e ./sdk
# 或复制 sdk/serviceatlas_client 目录到你的项目
```

#### FastAPI 集成（lifespan 方式）

```python
from fastapi import FastAPI
from serviceatlas_client.decorators import fastapi_lifespan

# 创建注册 lifespan
lifespan = fastapi_lifespan(
    registry_url="http://127.0.0.1:8888",
    service_id="deckview",
    service_name="DeckView 文档预览服务",
    host="127.0.0.1",
    port=8000,
    health_check_path="/docs",
    metadata={"version": "1.0.0"}
)

# 应用到 FastAPI
app = FastAPI(lifespan=lifespan)

@app.get("/docs")
def docs():
    return {"status": "ok"}
```

#### 通用 Python 应用

```python
from serviceatlas_client import ServiceAtlasClient

client = ServiceAtlasClient(
    registry_url="http://127.0.0.1:8888",
    service_id="my-service",
    service_name="我的服务",
    host="127.0.0.1",
    port=5000,
)

# 启动注册 + 心跳
client.start()

# 你的应用逻辑...
# 程序退出时自动注销
```

**优点**: 自动心跳、优雅注销、动态注册
**适用**: 需要动态管理的服务、容器化部署

---

### 方式三：HTTP API 手动注册

```bash
# 注册服务
curl -X POST http://localhost:8888/api/v1/services \
  -H "Content-Type: application/json" \
  -d '{
    "id": "deckview",
    "name": "DeckView 文档预览服务",
    "host": "127.0.0.1",
    "port": 8000,
    "health_check_path": "/docs",
    "base_path": "/s/deckview"
  }'

# 心跳上报
curl -X POST http://localhost:8888/api/v1/services/deckview/heartbeat

# 注销服务
curl -X DELETE http://localhost:8888/api/v1/services/deckview
```

**优点**: 跨语言支持
**适用**: 非 Python 服务、测试调试

> **关于 base_path**：如果服务需要通过 Aegis 等认证网关代理访问，需要在注册时指定 `base_path`（如 `/s/deckview`），并在服务启动时设置相应的环境变量（如 `DECKVIEW_BASE_PATH=/s/deckview`）。如果不需要代理访问，可以省略该字段。

---

## API 参考

### 服务注册 API

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/v1/services` | 注册服务 |
| `GET` | `/api/v1/services` | 获取服务列表 |
| `GET` | `/api/v1/services/{id}` | 获取服务详情 |
| `PUT` | `/api/v1/services/{id}` | 更新服务 |
| `DELETE` | `/api/v1/services/{id}` | 注销服务 |
| `POST` | `/api/v1/services/{id}/heartbeat` | 心跳上报 |

### 服务发现 API

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/v1/discover/{id}` | 发现服务（仅健康） |
| `GET` | `/api/v1/gateways` | 获取所有网关 |

### 依赖管理 API

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/v1/dependencies` | 创建依赖关系 |
| `GET` | `/api/v1/dependencies` | 获取所有依赖 |
| `DELETE` | `/api/v1/dependencies/{id}` | 删除依赖 |
| `GET` | `/api/v1/topology` | 获取拓扑图数据 |

### 路由管理 API

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/v1/routes` | 创建路由规则 |
| `GET` | `/api/v1/routes` | 获取路由列表 |
| `PUT` | `/api/v1/routes/{id}` | 更新路由 |
| `DELETE` | `/api/v1/routes/{id}` | 删除路由 |

### 监控 API

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/v1/monitor/overview` | 监控概览 |
| `POST` | `/api/v1/monitor/health-check` | 触发健康检查 |

---

## 配置说明

### 环境变量配置

创建 `.env` 文件或设置环境变量：

```bash
# 服务器配置
HOST=127.0.0.1
PORT=8888
DEBUG=false

# 数据库
DATABASE_URL=sqlite+aiosqlite:///./serviceatlas.db

# 健康检查
HEALTH_CHECK_INTERVAL=30    # 检查间隔（秒）
HEALTH_CHECK_TIMEOUT=5      # 单次超时（秒）
UNHEALTHY_THRESHOLD=3       # 失败次数阈值
HEARTBEAT_TIMEOUT=60        # 心跳超时（秒）

# 反向代理配置（通过网关访问时设置）
BASE_PATH=/s/serviceatlas   # URL 前缀，用于 Aegis 等网关代理
```

### 反向代理配置（Base Path）

当 ServiceAtlas 通过认证网关（如 Aegis）代理访问时，需要设置 `BASE_PATH` 环境变量，使静态资源和页面链接正确工作。

**场景说明**：
- 直接访问：`http://localhost:9000/` → 不需要设置 BASE_PATH
- 通过网关代理访问：`http://aegis:8000/s/serviceatlas/` → 需要设置 `BASE_PATH=/s/serviceatlas`

**启动示例**：

```bash
# 直接访问模式（不设置）
python run.py --host 127.0.0.1 --port 8888

# 通过 Aegis 网关代理访问（设置 BASE_PATH）
BASE_PATH=/s/serviceatlas python run.py --host 127.0.0.1 --port 8888
```

**注意**：设置 BASE_PATH 后，直接访问 `http://localhost:8888/` 将无法正常工作，因为静态资源路径会变成 `/s/serviceatlas/static/...`。请根据实际访问方式选择是否设置

### SDK 配置参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `registry_url` | str | - | 注册中心地址 |
| `service_id` | str | - | 服务唯一标识 |
| `service_name` | str | - | 服务显示名称 |
| `host` | str | - | 服务地址 |
| `port` | int | - | 服务端口 |
| `protocol` | str | `http` | 协议类型 |
| `health_check_path` | str | `/health` | 健康检查路径 |
| `is_gateway` | bool | `False` | 是否为网关 |
| `base_path` | str | `""` | 代理路径前缀（通过网关代理时设置） |
| `metadata` | dict | `None` | 扩展元数据 |
| `heartbeat_interval` | int | `30` | 心跳间隔（秒） |

---

## 项目结构

```
ServiceAtlas/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 应用入口
│   ├── config.py            # 配置管理
│   ├── database.py          # 数据库连接
│   ├── models/              # SQLAlchemy 数据模型
│   │   ├── service.py       # 服务表
│   │   ├── dependency.py    # 依赖关系表
│   │   └── route.py         # 路由规则表
│   ├── schemas/             # Pydantic 请求/响应模型
│   ├── api/                 # API 路由
│   │   ├── registry.py      # 服务注册
│   │   ├── discovery.py     # 服务发现
│   │   ├── dependency.py    # 依赖管理
│   │   ├── gateway.py       # 网关路由
│   │   └── monitor.py       # 监控统计
│   ├── services/            # 业务逻辑层
│   │   ├── registry.py      # 注册逻辑
│   │   ├── discovery.py     # 发现逻辑
│   │   ├── dependency.py    # 依赖处理
│   │   ├── gateway.py       # 路由管理
│   │   ├── health.py        # 健康检查
│   │   └── preload.py       # 配置预加载
│   ├── core/
│   │   └── proxy.py         # HTTP 代理转发
│   └── web/
│       └── routes.py        # Web 界面路由
├── frontend/                # Vue 3 前端（新增）
│   ├── src/
│   │   ├── views/           # 页面组件
│   │   ├── components/      # 公共组件
│   │   ├── locales/         # 国际化翻译
│   │   ├── router/          # 路由配置
│   │   └── api/             # API 封装
│   ├── package.json
│   └── vite.config.js
├── sdk/                     # Python 客户端 SDK
│   └── serviceatlas_client/
│       ├── __init__.py
│       ├── client.py        # 同步/异步客户端
│       └── decorators.py    # FastAPI 装饰器
├── static/                  # 静态资源
│   ├── css/style.css
│   ├── js/main.js
│   └── app/                 # Vue 构建输出目录
├── templates/               # Jinja2 模板（传统版）
│   ├── base.html
│   ├── dashboard.html       # 仪表盘
│   ├── services.html        # 服务管理
│   └── topology.html        # 依赖拓扑
├── ChangeLog/               # 修改日志
├── services.yaml            # 预注册配置
├── requirements.txt         # 依赖包
├── run.py                   # 启动脚本
└── README.md
```

---

## 架构设计

```
┌─────────────────────────────────────────────────────────────────┐
│                        ServiceAtlas                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌───────────────┐  ┌───────────────┐  ┌───────────────────┐   │
│   │   Registry    │  │   Discovery   │  │   Route Rules     │   │
│   │   服务注册    │  │   服务发现    │  │    路由规则管理   │   │
│   └───────────────┘  └───────────────┘  └───────────────────┘   │
│                                                                 │
│   ┌───────────────┐  ┌───────────────┐  ┌───────────────────┐   │
│   │  Dependency   │  │    Monitor    │  │      Web UI       │   │
│   │   依赖管理    │  │   服务监控    │  │     管理界面      │   │
│   └───────────────┘  └───────────────┘  └───────────────────┘   │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                      SQLite Database                            │
└─────────────────────────────────────────────────────────────────┘

                              ▲
                              │ HTTP API / SDK
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│    Hermes     │     │     Aegis     │     │   DeckView    │
│  (API 网关)   │     │  (IAM 系统)   │     │  (文档服务)   │
└───────────────┘     └───────────────┘     └───────────────┘
        │
        │ 获取路由规则
        ▼
┌─────────────────────────────────────────────────────────────────┐
│                      请求转发流程                                │
│  用户 → Hermes → 路由匹配 → 负载均衡 → Aegis/DeckView/其他服务  │
└─────────────────────────────────────────────────────────────────┘
```

### 与 Hermes 网关集成

ServiceAtlas 为 Hermes API 网关提供路由规则：

1. Hermes 启动时注册到 ServiceAtlas（标记为 `is_gateway=true`）
2. Hermes 定期从 ServiceAtlas 获取路由规则
3. ServiceAtlas 在 Web 界面或 API 中管理路由规则

---

## 使用场景示例

### 场景一：文档服务 + 权限网关

```yaml
# services.yaml
services:
  - id: deckview
    name: DeckView 文档服务
    host: 192.168.1.100
    port: 8000

  - id: auth-gateway
    name: 权限网关
    host: 192.168.1.1
    port: 80
    is_gateway: true

dependencies:
  - source: auth-gateway
    target: deckview

routes:
  - gateway: auth-gateway
    path_pattern: /docs/*
    target: deckview
    strip_prefix: true
    strip_path: /docs
```

**访问流程**:
```
用户 → auth-gateway:80/docs/file.pdf → deckview:8000/file.pdf
```

### 场景二：多服务依赖拓扑

```yaml
services:
  - id: api-gateway
    name: API 网关
    host: 10.0.0.1
    port: 8080
    is_gateway: true

  - id: user-service
    name: 用户服务
    host: 10.0.0.2
    port: 8001

  - id: order-service
    name: 订单服务
    host: 10.0.0.3
    port: 8002

  - id: payment-service
    name: 支付服务
    host: 10.0.0.4
    port: 8003

dependencies:
  - source: api-gateway
    target: user-service
  - source: api-gateway
    target: order-service
  - source: order-service
    target: user-service
  - source: order-service
    target: payment-service
```

Web 界面的拓扑图会自动渲染服务间的调用关系。

---

## 健康检查机制

ServiceAtlas 采用双重健康检查机制：

### 1. 主动探测

注册中心定期向服务的 `health_check_path` 发送 HTTP GET 请求：

- 返回 2xx → 标记为 `healthy`
- 返回其他/超时 → 累计失败次数
- 连续失败 ≥ 3 次 → 标记为 `unhealthy`

### 2. 被动心跳

服务主动上报心跳（SDK 自动处理）：

- 收到心跳 → 标记为 `healthy`，重置失败计数
- 超过 60 秒未收到 → 标记为 `unhealthy`

---

## 开发指南

### 本地开发

```bash
# 克隆项目
git clone <repo-url>
cd ServiceAtlas

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt

# 开发模式启动
python run.py --reload --debug
```

### 运行测试

```bash
# 安装测试依赖
pip install pytest pytest-asyncio httpx

# 运行测试
pytest tests/
```

### 代码风格

项目遵循 PEP 8 规范，建议使用：

```bash
pip install black isort
black app/
isort app/
```

---

## 许可证

本项目采用 MIT 许可证，详见 [LICENSE](LICENSE) 文件。

---

## 更新日志

详见 [ChangeLog](ChangeLog/) 目录。

---

<p align="center">
  <sub>Built with FastAPI & SQLAlchemy</sub>
</p>
