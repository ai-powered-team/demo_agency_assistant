"""
用户画像分析接口

负责处理用户画像分析相关的 HTTP 请求。
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator

from util import logger, ProfileAnalysisRequest, AgentResponse, format_sse_response
from agent.profile_analyzer import ProfileAnalyzer

router = APIRouter()


async def _stream_profile_analysis(request: ProfileAnalysisRequest) -> AsyncGenerator[str, None]:
    """流式处理用户画像分析"""
    try:
        # 创建画像分析器实例
        analyzer = ProfileAnalyzer()

        # 执行分析并流式返回结果
        async for response in analyzer.analyze_profile(request):
            yield await format_sse_response(response)

    except Exception as e:
        logger.error(f"用户画像分析过程中发生错误: {e}")
        error_response: AgentResponse = {
            "type": "error",
            "error": "分析过程中发生错误",
            "details": str(e)
        }
        yield await format_sse_response(error_response)


@router.post("/analyze")
async def analyze_user_profile(request: ProfileAnalysisRequest):
    """
    用户画像分析接口

    输入：
    - user_id: 用户ID（数字）
    - session_id: 会话ID（数字）
    - history_chats: 历史对话数组
    - custom_profile: 用户自定义画像（可选）

    输出：
    - SSE 流式输出，包含以下类型的响应：
      * thinking: Agent 思考过程
      * profile: 提取的用户特征数据
      * answer: Agent 询问问题
      * profile_complete: 画像分析完成
      * error: 错误信息
    """
    logger.info(
        f"开始分析用户画像，用户ID: {request['user_id']}, 会话ID: {request['session_id']}")

    try:
        return StreamingResponse(
            _stream_profile_analysis(request),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*",
            }
        )
    except Exception as e:
        logger.error(f"用户画像分析接口错误: {e}")
        raise HTTPException(status_code=500, detail="服务器内部错误")
