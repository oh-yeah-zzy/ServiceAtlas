#!/usr/bin/env python3
"""
ServiceAtlas 启动脚本
使用 uvicorn 启动 FastAPI 应用
"""
import argparse
import uvicorn

from app.config import settings


def main():
    parser = argparse.ArgumentParser(
        description="ServiceAtlas - 轻量级服务注册中心"
    )
    parser.add_argument(
        "-H", "--host",
        type=str,
        default=settings.host,
        help=f"绑定地址 (默认: {settings.host})"
    )
    parser.add_argument(
        "-p", "--port",
        type=int,
        default=settings.port,
        help=f"监听端口 (默认: {settings.port})"
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="启用热重载（开发模式）"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="启用调试模式"
    )

    args = parser.parse_args()

    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="debug" if args.debug else "info",
    )


if __name__ == "__main__":
    main()
