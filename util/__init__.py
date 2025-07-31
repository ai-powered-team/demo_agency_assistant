"""
工具层模块

包含配置管理、日志、类型定义等工具函数和类。
"""

from .config import config, Config
from .logger import logger, setup_logger
from .sse import format_sse_response
from .types import (
    BaseResponse,
    ThinkingResponse,
    AnswerResponse,
    ProfileResponse,
    ErrorResponse,
    UserProfileCompleteResponse,
    ProductRecommendResponse,
    ProductInfo,
    ChatRole,
    ChatMessage,
    UserProfile,
    FeatureData,
    InsuranceProduct,
    ProfileAnalysisRequest,
    ProductRecommendationRequest,
    AgencyCommunicationRequest,
    AgencyRecommendRequest,
    AgencyRecommendResponse,
    QuestionRecommendResponse,
    ViewpointAnalysisResponse,
    IntentAnalysis,
    IntentAnalysisResponse,
    UserResponseResponse,
    SuggestionsResponse,
    AssistantResponse,
    AssistantRequest,
    AgentResponse,
    AgencyTone,
    AgencyInfo,
    PaymentResponse,
    AgencySessionData
)

# RAG相关模块（可选导入，避免依赖问题）
try:
    from .rag_pit_detector import PitDataLoader, PitVectorStore, PitRetriever, get_pit_retriever
    _RAG_AVAILABLE = True
    RAG_EXPORTS = ["PitDataLoader", "PitVectorStore", "PitRetriever", "get_pit_retriever"]
except ImportError:
    _RAG_AVAILABLE = False
    RAG_EXPORTS = []

__all__ = [
    "config",
    "Config",
    "logger",
    "setup_logger",
    "format_sse_response",
    "BaseResponse",
    "ThinkingResponse",
    "AnswerResponse",
    "ProfileResponse",
    "ErrorResponse",
    "UserProfileCompleteResponse",
    "ProductRecommendResponse",
    "ProductInfo",
    "ChatRole",
    "ChatMessage",
    "UserProfile",
    "FeatureData",
    "InsuranceProduct",
    "ProfileAnalysisRequest",
    "ProductRecommendationRequest",
    "AgencyCommunicationRequest",
    "AgencyRecommendRequest",
    "AgencyRecommendResponse",
    "QuestionRecommendResponse",
    "ViewpointAnalysisResponse",
    "IntentAnalysis",
    "IntentAnalysisResponse",
    "UserResponseResponse",
    "SuggestionsResponse",
    "AssistantResponse",
    "AssistantRequest",
    "AgentResponse",
    "AgencyTone",
    "AgencyInfo",
    "PaymentResponse",
    "AgencySessionData"
] + RAG_EXPORTS
