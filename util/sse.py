"""
SSE (Server-Sent Events) 工具模块

提供 SSE 响应格式化的公共方法。
"""

import json
from .types import AgentResponse


async def format_sse_response(response: AgentResponse) -> str:
    """
    格式化 SSE 响应

    Args:
        response: Agent 响应对象

    Returns:
        格式化后的 SSE 响应字符串，格式为: data: {JSON}\n\n
    """
    return f"data: {json.dumps(response, ensure_ascii=False)}\n\n"
