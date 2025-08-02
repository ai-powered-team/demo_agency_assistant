"""
类型定义模块

定义项目中使用的各种数据类型和响应类型。
"""

from typing import List, Dict, Any, Optional, Union
from typing_extensions import TypedDict
from enum import Enum


class BaseResponse(TypedDict):
    """基础响应类型，所有 LangGraph workflow 的返回值都应该派生自此类"""
    type: str


class ThinkingResponse(BaseResponse):
    """Agent 思考过程响应"""
    type: str  # "thinking"
    content: str
    step: str


class AnswerResponse(BaseResponse):
    """Agent 最终答案响应"""
    type: str  # "answer"
    content: str
    data: Optional[Dict[str, Any]]


class ErrorResponse(BaseResponse):
    """错误响应"""
    type: str  # "error"
    error: str
    details: Optional[str]


class ProfileResponse(BaseResponse):
    """用户特征提取响应"""
    type: str  # "profile"
    features: List[Dict[str, Any]]  # 新提取的特征数据列表，每个元素是 FeatureData 格式
    message: Optional[str]  # 可选的说明信息


class UserProfileCompleteResponse(BaseResponse):
    """用户画像分析完成响应"""
    type: str  # "profile_complete"
    message: str
    profile_summary: Dict[str, Any]
    completion_rate: float


class ProductInfo(TypedDict):
    """产品推荐信息类型"""
    product_name: str  # 产品名称
    product_description: str  # 产品简介
    product_type: str  # 产品类型（重疾险、寿险、医疗险等）
    recommendation: str  # 推荐理由，结合用户特征和产品推荐打分的结果


class ProductRecommendResponse(BaseResponse):
    """产品推荐响应类型"""
    type: str  # "product_recommendation"
    products: List[ProductInfo]  # 推荐的产品列表
    message: Optional[str]  # 可选的推荐说明信息
    analysis_summary: Optional[str]  # 可选的分析摘要


class AgencyTone(str, Enum):
    """保险经纪人沟通风格枚举"""
    PROFESSIONAL = "professional"     # 专业严谨型
    FRIENDLY = "friendly"             # 亲和友善型
    ENTHUSIASTIC = "enthusiastic"     # 热情积极型
    CONSULTATIVE = "consultative"     # 咨询顾问型
    TRUSTWORTHY = "trustworthy"       # 可靠信赖型


class AgencyInfo(TypedDict):
    """保险经纪人信息类型"""
    agency_id: int                    # 经纪人ID
    name: str                         # 经纪人姓名
    tone: AgencyTone                  # 沟通风格
    experience_years: int             # 从业年限


class PaymentResponse(BaseResponse):
    """支付流程响应"""
    type: str  # "payment"
    message: str                      # 引导支付的消息
    agency_id: int                    # 当前经纪人ID
    agency_name: str                  # 经纪人姓名
    recommended_action: str           # 建议的后续行动


class ChatRole(str, Enum):
    """聊天角色枚举"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(TypedDict):
    """聊天消息类型"""
    role: ChatRole
    content: str


class AgencySessionData(TypedDict):
    """经纪人沟通会话数据"""
    user_id: int
    session_id: int
    agency_id: int
    agency_info: AgencyInfo
    conversation_history: List[ChatMessage]
    # "initial", "inquiry", "negotiation", "ready_for_payment"
    conversation_stage: str
    last_updated: str                # ISO 格式时间戳


class FeatureData(TypedDict):
    """单个特征数据类型"""
    category_name: str
    feature_name: str
    feature_value: Any
    confidence: float
    skipped: bool


class UserProfile(TypedDict, total=False):
    """用户画像类型 - 包含所有特征字段，所有字段都是可选的"""

    # 用户ID
    user_id: Optional[int]

    # 基础身份维度 (basic_identity)
    name: Optional[str]
    gender: Optional[str]  # 男/女/其他
    date_of_birth: Optional[str]  # YYYY-MM-DD
    marital_status: Optional[str]  # 未婚/已婚/离异/丧偶
    residence_city: Optional[str]
    occupation_type: Optional[str]  # 企业员工/公务员/个体经营/企业主/自由职业/学生/退休
    industry: Optional[str]

    # 女性特殊状态 (female_specific) - 仅女性
    # 未怀孕/备孕期/孕早期(1-3月)/孕中期(4-6月)/孕晚期(7-9月)/产后恢复期
    pregnancy_status: Optional[str]
    childbearing_plan: Optional[str]  # 1年内/2年内/3年内/暂无计划

    # 家庭结构与责任维度 (family_structure)
    family_structure: Optional[str]  # 单身/夫妻/夫妻+子女/三代同堂/其他
    number_of_children: Optional[int]
    caregiving_responsibility: Optional[str]  # 无/赡养父母/赡养双方父母/其他
    monthly_household_expense: Optional[float]  # 元
    mortgage_balance: Optional[float]  # 元
    is_family_financial_support: Optional[str]  # 是/否/共同承担

    # 财务现状与目标维度 (financial_status)
    annual_total_income: Optional[float]  # 万元
    income_stability: Optional[str]  # 非常稳定/比较稳定/一般/不稳定
    annual_insurance_budget: Optional[float]  # 万元

    # 健康与生活习惯维度 (health_lifestyle)
    overall_health_status: Optional[str]  # 非常健康/比较健康/一般/有慢性病/健康状况较差
    has_chronic_disease: Optional[str]  # 无/高血压/糖尿病/心脏病/其他
    smoking_status: Optional[str]  # 不吸烟/已戒烟/轻度吸烟/重度吸烟
    recent_medical_checkup: Optional[str]  # 1年内正常/1年内有异常/2年内正常/2年以上未体检


class InsuranceProduct(TypedDict):
    """保险产品类型"""
    product_id: str
    name: str
    type: str
    description: str
    coverage: List[str]
    premium: float
    age_range: List[int]
    features: List[str]
    provider: str
    rating: Optional[float]


class ProfileAnalysisRequest(TypedDict):
    """用户画像分析接口请求类型"""
    user_id: int
    session_id: int
    history_chats: List[ChatMessage]
    custom_profile: Optional[UserProfile]


class ProductRecommendationRequest(TypedDict):
    """保险产品推荐接口请求类型"""
    user_id: int
    session_id: int
    custom_profile: Optional[UserProfile]


class AgencyCommunicationRequest(TypedDict):
    """用户与经纪人沟通接口请求类型"""
    user_id: int
    session_id: int
    history_chats: List[ChatMessage]
    agency_id: int
    agencies: List[AgencyInfo]


class AgencyRecommendRequest(TypedDict):
    """推荐经纪人接口请求类型"""
    user_id: int
    history_chats: List[ChatMessage]
    agency_id: int
    agencies: List[AgencyInfo]


class AgencyRecommendResponse(BaseResponse):
    """推荐经纪人响应类型"""
    type: str  # "agency_recommend"
    current_agency_id: int              # 当前经纪人ID
    recommended_agency_id: int          # 推荐的经纪人ID
    should_switch: bool                 # 是否建议切换
    recommendation_reason: str          # 推荐理由
    user_preference_analysis: str       # 用户偏好分析
    communication_effectiveness: str    # 沟通效果评估
    confidence_score: float            # 推荐置信度 (0.0-1.0)


class QuestionRecommendResponse(BaseResponse):
    """推荐问题响应类型"""
    type: str  # "question_recommend"
    questions: List[str]                    # 推荐的问题列表
    analysis_reason: str                    # 推荐这些问题的分析理由
    conversation_stage: str                 # 当前对话阶段
    priority_level: str                     # 优先级（高/中/低）


class ViewpointAnalysisResponse(BaseResponse):
    """观点分析响应类型"""
    type: str  # "viewpoint_analysis"
    agent_viewpoints: List[Dict[str, Any]]  # 经纪人观点列表，每个包含观点内容和分析
    overall_assessment: str                 # 整体评估
    risk_warnings: List[str]                # 风险提醒列表
    suggestions: List[str]                  # 建议列表


class IntentAnalysis(TypedDict):
    """意图分析结果类型"""
    讨论主题: str                           # 当前讨论的主要保险话题
    涉及术语: List[str]                     # 提到的保险专业术语
    涉及产品: List[str]                     # 提到的具体保险产品类型
    经纪人阶段性意图识别: str                 # 销售流程中的当前阶段
    经纪人本句话意图识别: str                 # 这句话的具体目的
    用户当下需求: str                       # 推测的用户需求


class IntentAnalysisResponse(BaseResponse):
    """意图分析响应类型"""
    type: str  # "intent_analysis"
    intent_analysis: IntentAnalysis         # 意图识别结果


class UserResponseResponse(BaseResponse):
    """AI用户回应响应类型"""
    type: str  # "user_response"
    user_response: str                      # AI用户的回应


class SuggestionsResponse(BaseResponse):
    """对话建议响应类型"""
    type: str  # "suggestions"
    suggestions: List[str]                  # 给用户的建议列表
    retrieved_pits: Optional[List[dict]] = None  # 检索到的坑点信息


class AssistantResponse(BaseResponse):
    """智能对话助理最终响应类型"""
    type: str  # "assistant"
    user_response: str                      # AI用户的回应
    intent_analysis: IntentAnalysis         # 意图识别结果
    suggestions: Optional[List[str]]        # 给用户的建议（可选）


class AssistantRequest(TypedDict):
    """智能对话助理接口请求类型"""
    user_id: int
    session_id: int
    broker_input: str                       # 经纪人输入的话
    conversation_history: List[ChatMessage] # 对话历史


# 响应类型联合
AgentResponse = Union[ThinkingResponse, AnswerResponse, ProfileResponse,
                      ErrorResponse, UserProfileCompleteResponse, ProductRecommendResponse,
                      PaymentResponse, AgencyRecommendResponse, QuestionRecommendResponse,
                      ViewpointAnalysisResponse, IntentAnalysisResponse, UserResponseResponse,
                      SuggestionsResponse, AssistantResponse]
