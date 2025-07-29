"""
保险产品推荐接口

负责处理保险产品推荐相关的 HTTP 请求。
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator

from util import logger, ProductRecommendationRequest, AgentResponse, format_sse_response
from agent.product_recommender import ProductRecommender

router = APIRouter()


async def stream_product_recommendation(request: ProductRecommendationRequest) -> AsyncGenerator[str, None]:
    """流式处理保险产品推荐"""
    try:
        # 创建产品推荐器实例
        recommender = ProductRecommender()

        # 执行推荐并流式返回结果
        async for response in recommender.recommend_products(request):
            yield await format_sse_response(response)

    except Exception as e:
        logger.error(f"保险产品推荐过程中发生错误: {e}")
        error_response: AgentResponse = {
            "type": "error",
            "error": "推荐过程中发生错误",
            "details": str(e)
        }
        yield await format_sse_response(error_response)


@router.post("/recommend")
async def recommend_insurance_products(request: ProductRecommendationRequest):
    """
    保险产品推荐接口

    输入：
    - user_id: 用户ID（数字）
    - session_id: 会话ID（数字）
    - custom_profile: 用户自定义画像（可选）

    输出：
    - SSE 流式输出，包含 Agent 的思考过程和最终推荐结果
    """
    logger.info(
        f"开始推荐保险产品，用户ID: {request['user_id']}, 会话ID: {request['session_id']}")

    try:
        return StreamingResponse(
            stream_product_recommendation(request),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*",
            }
        )
    except Exception as e:
        logger.error(f"保险产品推荐接口错误: {e}")
        raise HTTPException(status_code=500, detail="服务器内部错误")
