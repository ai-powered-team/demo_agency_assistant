"""
智能对话助理接口

负责处理智能对话助理相关的 HTTP 请求。
提供带有意图识别的保险对话系统，AI扮演用户，真人扮演经纪人。
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator

from util import logger, AssistantRequest, AgentResponse, format_sse_response
from agent.agency_assistant import AgencyAssistant

router = APIRouter()


async def stream_assistant_conversation(request: AssistantRequest) -> AsyncGenerator[str, None]:
    """流式处理智能对话助理分析"""
    try:
        # 创建智能对话助理实例
        assistant = AgencyAssistant()

        # 执行对话助理分析并流式返回结果
        async for response in assistant.assist_conversation(request):
            yield await format_sse_response(response)

    except Exception as e:
        logger.error(f"智能对话助理处理过程中发生错误: {e}")
        error_response: AgentResponse = {
            "type": "error",
            "error": "助理处理失败",
            "details": str(e)
        }
        yield await format_sse_response(error_response)


@router.post("/assistant")
async def assistant_conversation(request: AssistantRequest):
    """
    智能对话助理接口

    功能描述：
    - AI 扮演保险用户，真人扮演保险经纪人
    - 实时进行意图识别分析，包括6个维度：
      1. 讨论主题识别
      2. 涉及术语提取  
      3. 涉及产品分析
      4. 经纪人阶段性意图识别
      5. 经纪人本句话意图识别
      6. 用户当下需求分析
    - 生成AI用户的自然回应
    - 提供实时对话建议

    输入参数：
    - user_id: 用户ID（数字）
    - session_id: 会话ID（数字）
    - broker_input: 经纪人输入的话（字符串）
    - conversation_history: 对话历史数组

    输出：
    - SSE 流式输出，包含：
      - thinking: 处理过程思考步骤
      - assistant: 最终结果（用户回应 + 意图识别 + 建议）
      - error: 错误信息（如有）

    技术架构：
    - 对话生成：DeepSeek API
    - 意图识别：Qwen3 API  
    - 工作流：LangGraph
    """
    logger.info(
        f"开始智能对话助理分析，用户ID: {request['user_id']}, 会话ID: {request['session_id']}")

    try:
        return StreamingResponse(
            stream_assistant_conversation(request),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*",
            }
        )
    except Exception as e:
        logger.error(f"智能对话助理接口错误: {e}")
        raise HTTPException(status_code=500, detail="服务器内部错误") 