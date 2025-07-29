"""
推荐经纪人接口

负责处理推荐经纪人相关的 HTTP 请求。
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator

from util import logger, AgencyRecommendRequest, AgentResponse, format_sse_response
from agent.agency_recommender import AgencyRecommender

router = APIRouter()


async def stream_agency_recommendation(request: AgencyRecommendRequest) -> AsyncGenerator[str, None]:
    """流式处理推荐经纪人"""
    try:
        # 创建经纪人推荐器实例
        recommender = AgencyRecommender()

        # 执行推荐并流式返回结果
        async for response in recommender.recommend_agency(request):
            yield await format_sse_response(response)

    except Exception as e:
        logger.error(f"推荐经纪人过程中发生错误: {e}")
        error_response: AgentResponse = {
            "type": "error",
            "error": "推荐过程中发生错误",
            "details": str(e)
        }
        yield await format_sse_response(error_response)


@router.post("/recommend")
async def recommend_agency(request: AgencyRecommendRequest):
    """
    推荐经纪人接口

    输入：
    - user_id: 用户ID（数字）
    - history_chats: 历史对话数组
    - agency_id: 当前经纪人ID（数字）
    - agencies: 所有保险经纪人信息数组

    输出：
    - SSE 流式输出，包含推荐分析过程和推荐结果
    """
    logger.info(
        f"开始推荐经纪人，用户ID: {request['user_id']}, 当前经纪人ID: {request['agency_id']}")

    try:
        return StreamingResponse(
            stream_agency_recommendation(request),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*",
            }
        )
    except Exception as e:
        logger.error(f"推荐经纪人接口错误: {e}")
        raise HTTPException(status_code=500, detail="服务器内部错误")
