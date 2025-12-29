"""
HTTP 代理转发模块
用于网关服务将请求转发到目标服务
"""
from typing import Optional
import httpx
from fastapi import Request, Response


async def proxy_request(
    request: Request,
    target_base_url: str,
    target_path: str,
    timeout: float = 30.0
) -> Response:
    """
    代理转发请求到目标服务

    Args:
        request: 原始 FastAPI 请求
        target_base_url: 目标服务的基础 URL（如 http://127.0.0.1:8000）
        target_path: 目标路径
        timeout: 请求超时时间

    Returns:
        转发后的响应
    """
    # 构建目标 URL
    target_url = f"{target_base_url.rstrip('/')}/{target_path.lstrip('/')}"

    # 读取请求体
    body = await request.body()

    # 准备请求头（移除 host 头，避免冲突）
    headers = dict(request.headers)
    headers.pop("host", None)

    # 发送代理请求
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.request(
            method=request.method,
            url=target_url,
            headers=headers,
            content=body,
            params=dict(request.query_params),
        )

    # 构建响应
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers),
        media_type=response.headers.get("content-type"),
    )


def strip_path_prefix(path: str, prefix: str) -> str:
    """
    剥离路径前缀

    Args:
        path: 原始路径（如 /api/docs/file.pdf）
        prefix: 要剥离的前缀（如 /api/docs）

    Returns:
        剥离后的路径（如 /file.pdf）
    """
    if path.startswith(prefix):
        result = path[len(prefix):]
        if not result.startswith("/"):
            result = "/" + result
        return result
    return path
