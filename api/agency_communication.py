"""
用户与保险经纪人沟通接口

负责处理用户与保险经纪人沟通相关的 HTTP 请求。
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator

from util import logger, AgencyCommunicationRequest, AgentResponse, format_sse_response
from agent.agency_communicator import AgencyCommunicator

router = APIRouter()


async def stream_agency_communication(request: AgencyCommunicationRequest) -> AsyncGenerator[str, None]:
    """流式处理用户与保险经纪人沟通"""
    try:
        # 创建保险经纪人沟通器实例
        communicator = AgencyCommunicator()

        # 执行沟通并流式返回结果
        async for response in communicator.communicate_with_agency(request):
            yield await format_sse_response(response)

    except Exception as e:
        logger.error(f"用户与保险经纪人沟通过程中发生错误: {e}")
        error_response: AgentResponse = {
            "type": "error",
            "error": "沟通过程中发生错误",
            "details": str(e)
        }
        yield await format_sse_response(error_response)


@router.post("/communicate")
async def communicate_with_agency(request: AgencyCommunicationRequest):
    """
    用户与保险经纪人沟通接口

    输入：
    - user_id: 用户ID（数字）
    - session_id: 会话ID（数字）
    - history_chats: 历史对话数组
    - agency_id: 保险经纪人ID（数字）
    - agencies: 所有保险经纪人信息数组

    输出：
    - SSE 流式输出，包含经纪人回应和支付流程引导
    """
    logger.info(
        f"开始用户与保险经纪人沟通，用户ID: {request['user_id']}, 经纪人ID: {request['agency_id']}")

    try:
        return StreamingResponse(
            stream_agency_communication(request),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*",
            }
        )
    except Exception as e:
        logger.error(f"用户与保险经纪人沟通接口错误: {e}")
        raise HTTPException(status_code=500, detail="服务器内部错误")
