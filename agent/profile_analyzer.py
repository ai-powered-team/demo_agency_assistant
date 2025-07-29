"""
用户画像分析器

使用 LangGraph 实现用户画像分析的业务逻辑。
"""

import time
from typing import AsyncGenerator, List, Optional, Dict, Any, Tuple
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, END
from langgraph.graph.state import CompiledStateGraph
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage
from pydantic import SecretStr

from util import (
    config, logger, ProfileAnalysisRequest, AgentResponse,
    ThinkingResponse, AnswerResponse, ProfileResponse, ErrorResponse, UserProfileCompleteResponse,
    ChatMessage, UserProfile, FeatureData
)
from util.database import db_manager
from util.memory_manager import memory_manager


# 用户特征字典类型：feature_name -> FeatureData
UserFeatures = Dict[str, FeatureData]


class ExistingFeatureForLLM(TypedDict):
    """传递给 LLM 的已有特征数据类型"""
    category_name: str
    feature_name: str
    feature_value: Any
    confidence: float


class LLMExtractedFeature(TypedDict):
    """LLM 提取的特征类型"""
    value: Any
    confidence: float
    reasoning: str


class ProfileAnalyzerState(TypedDict):
    """用户画像分析器状态类"""
    user_id: int
    session_id: int
    history_chats: List[ChatMessage]
    custom_profile: Optional[UserProfile]
    existing_features: UserFeatures
    extracted_features: UserFeatures
    completion_status: Dict[str, Any]
    suggested_questions: Optional[str]
    final_answer: Optional[str]
    is_complete: bool
    asked_questions_history: List[str]  # 记录之前问过的问题
    asked_features_history: List[str]   # 记录之前询问过的特征名称


class ProfileAnalyzer:
    """用户画像分析器类"""

    def __init__(self):
        """初始化分析器"""
        # 用户历史问题记录 - 按用户ID存储
        self.user_questions_history: Dict[int, List[str]] = {}
        self.user_features_history: Dict[int, List[str]] = {}

        self.llm = ChatOpenAI(
            api_key=SecretStr(
                config.OPENAI_API_KEY) if config.OPENAI_API_KEY else None,
            base_url=config.OPENAI_BASE_URL,
            model=config.OPENAI_MODEL,
            temperature=0.7
        )
        self.workflow = self._build_workflow()

        # 特征分类定义
        self.feature_categories = {
            'basic_identity': [
                'gender', 'date_of_birth', 'marital_status',
                'residence_city', 'occupation_type', 'industry'
            ],
            'female_specific': [
                'pregnancy_status', 'childbearing_plan'
            ],
            'family_structure': [
                'family_structure', 'number_of_children', 'caregiving_responsibility',
                'monthly_household_expense', 'mortgage_balance', 'is_family_financial_support'
            ],
            'financial_status': [
                'annual_total_income', 'income_stability', 'annual_insurance_budget'
            ],
            'health_lifestyle': [
                'overall_health_status', 'has_chronic_disease', 'smoking_status', 'recent_medical_checkup'
            ]
        }

        # 必要特征定义
        self.required_features = {
            'gender', 'date_of_birth', 'marital_status', 'occupation_type', 'industry',
            'family_structure', 'monthly_household_expense', 'is_family_financial_support',
            'annual_total_income', 'income_stability', 'annual_insurance_budget', 'overall_health_status'
        }

        # 字段值标准化规则
        self.field_normalization_rules = {
            'gender': {
                'valid_values': ['男', '女'],
                'mappings': {
                    '男性': '男', 'male': '男', 'M': '男', 'm': '男',
                    '女性': '女', 'female': '女', 'F': '女', 'f': '女'
                }
            },
            'marital_status': {
                'valid_values': ['未婚', '已婚', '离异', '丧偶'],
                'mappings': {
                    '单身': '未婚', '未结婚': '未婚', '单身狗': '未婚',
                    '结婚': '已婚', '结婚了': '已婚', '有配偶': '已婚',
                    '离婚': '离异', '离婚了': '离异', '分居': '离异',
                    '丧偶了': '丧偶', '失偶': '丧偶'
                }
            },
            'occupation_type': {
                'valid_values': ['企业员工', '公务员', '个体经营', '企业主', '自由职业', '学生', '退休'],
                'mappings': {
                    '上班族': '企业员工', '员工': '企业员工', '打工人': '企业员工', '职员': '企业员工',
                    '公务员': '公务员', '事业单位': '公务员', '国企员工': '企业员工',
                    '个体户': '个体经营', '自营': '个体经营', '小老板': '个体经营',
                    '老板': '企业主', '创业者': '企业主', '企业家': '企业主',
                    '自由职业者': '自由职业', '自由工作者': '自由职业', '自雇': '自由职业',
                    '大学生': '学生', '研究生': '学生', '博士生': '学生',
                    '退休人员': '退休', '已退休': '退休'
                }
            },
            'family_structure': {
                'valid_values': ['单身', '夫妻', '夫妻+子女', '三代同堂', '其他'],
                'mappings': {
                    '一个人': '单身', '独居': '单身', '单身贵族': '单身',
                    '两口子': '夫妻', '夫妻二人': '夫妻', '丁克': '夫妻',
                    '三口之家': '夫妻+子女', '四口之家': '夫妻+子女', '有孩子': '夫妻+子女',
                    '大家庭': '三代同堂', '和父母一起住': '三代同堂'
                }
            },
            'income_stability': {
                'valid_values': ['非常稳定', '比较稳定', '一般', '不稳定'],
                'mappings': {
                    '很稳定': '非常稳定', '稳定': '比较稳定', '还行': '一般',
                    '不太稳定': '不稳定', '波动大': '不稳定'
                }
            },
            'overall_health_status': {
                'valid_values': ['非常健康', '比较健康', '一般', '有慢性病', '健康状况较差'],
                'mappings': {
                    '很健康': '非常健康', '健康': '比较健康', '还可以': '一般',
                    '有病': '有慢性病', '不太好': '健康状况较差', '较差': '健康状况较差'
                }
            },
            'has_chronic_disease': {
                'valid_values': ['无', '高血压', '糖尿病', '心脏病', '其他'],
                'mappings': {
                    '没有': '无', '无慢性病': '无', '健康': '无',
                    '高血压病': '高血压', '血压高': '高血压',
                    '糖尿病': '糖尿病', '血糖高': '糖尿病',
                    '心脏病': '心脏病', '心血管疾病': '心脏病'
                }
            },
            'smoking_status': {
                'valid_values': ['不吸烟', '已戒烟', '轻度吸烟', '重度吸烟'],
                'mappings': {
                    '不抽烟': '不吸烟', '从不吸烟': '不吸烟',
                    '戒烟了': '已戒烟', '已经戒了': '已戒烟',
                    '偶尔抽': '轻度吸烟', '少量吸烟': '轻度吸烟',
                    '经常抽': '重度吸烟', '大量吸烟': '重度吸烟'
                }
            },
            'is_family_financial_support': {
                'valid_values': ['是', '否', '共同承担'],
                'mappings': {
                    '是的': '是', '主要收入来源': '是', '经济支柱': '是',
                    '不是': '否', '不算': '否',
                    '一起承担': '共同承担', '共同负担': '共同承担', '都有收入': '共同承担'
                }
            }
        }

    def _build_workflow(self) -> CompiledStateGraph[ProfileAnalyzerState, ProfileAnalyzerState, ProfileAnalyzerState]:
        """构建 LangGraph 工作流"""
        workflow = StateGraph(ProfileAnalyzerState)

        # 添加节点
        workflow.add_node("load_existing_features",
                          self._load_existing_features)
        workflow.add_node("analyze_conversation", self._analyze_conversation)
        workflow.add_node("extract_new_features", self._extract_new_features)
        workflow.add_node("update_database", self._update_database)
        workflow.add_node("evaluate_completeness", self._evaluate_completeness)
        workflow.add_node("generate_questions", self._generate_questions)
        workflow.add_node("finalize_complete", self._finalize_complete)

        # 设置入口点
        workflow.set_entry_point("load_existing_features")

        # 添加边
        workflow.add_edge("load_existing_features", "analyze_conversation")
        workflow.add_edge("analyze_conversation", "extract_new_features")
        workflow.add_edge("extract_new_features", "update_database")
        workflow.add_edge("update_database", "evaluate_completeness")

        # 条件边：根据完成状态决定下一步
        workflow.add_conditional_edges(
            "evaluate_completeness",
            self._decide_next_step,
            {
                "generate_questions": "generate_questions",
                "complete": "finalize_complete"
            }
        )

        workflow.add_edge("generate_questions", END)
        workflow.add_edge("finalize_complete", END)

        return workflow.compile()

    async def _load_existing_features(self, state: ProfileAnalyzerState) -> ProfileAnalyzerState:
        """加载已有的用户特征"""
        logger.info("开始加载已有用户特征")

        user_id = state["user_id"]
        session_id = state["session_id"]

        try:
            # 从数据库加载已有特征
            existing_features = await db_manager.get_user_features(user_id, session_id)

            # 组织特征数据
            organized_features: UserFeatures = {}
            for feature in existing_features:
                feature_name = feature['feature_name']

                organized_features[feature_name] = {
                    'category_name': feature['category_name'],
                    'feature_name': feature_name,
                    'feature_value': feature['feature_value'],
                    'confidence': feature['confidence'],
                    'skipped': feature['skipped']
                }

            state["existing_features"] = organized_features
            logger.info(f"加载了用户 {user_id} 的 {len(existing_features)} 个已有特征")

        except Exception as e:
            logger.error(f"加载用户特征失败: {e}")
            state["existing_features"] = {}

        return state

    async def _analyze_conversation(self, state: ProfileAnalyzerState) -> ProfileAnalyzerState:
        """分析对话内容"""
        logger.info("开始分析对话内容")

        history_chats = state.get("history_chats", [])

        if history_chats:
            try:
                # 添加对话到记忆管理器
                await memory_manager.add_conversation_memory(
                    user_id=state["user_id"],
                    conversation=history_chats
                )
                logger.info("对话已添加到记忆管理器")

            except Exception as e:
                logger.error(f"添加对话记忆失败: {e}")

        return state

    async def _extract_new_features(self, state: ProfileAnalyzerState) -> ProfileAnalyzerState:
        """提取新特征"""
        logger.info("开始提取新特征")

        history_chats = state.get("history_chats", [])
        custom_profile = state.get("custom_profile", {})
        existing_features = state.get("existing_features", {})

        extracted_features: UserFeatures = {}

        try:
            # 1. 处理 custom_profile（置信度 1.0）
            if custom_profile:
                custom_features = self._process_custom_profile(custom_profile)
                extracted_features.update(custom_features)

            # 2. 使用 LLM 进行智能的特征提取
            if history_chats:
                llm_features = await self._extract_features_with_llm(history_chats, existing_features)

                # 合并 LLM 提取的特征
                for feature_name, feature_data in llm_features.items():
                    # 如果特征已存在，选择置信度更高的
                    if feature_name in extracted_features:
                        if feature_data['confidence'] > extracted_features[feature_name]['confidence']:
                            extracted_features[feature_name] = feature_data
                    else:
                        extracted_features[feature_name] = feature_data

            state["extracted_features"] = extracted_features
            total_features = len(extracted_features)
            logger.info(f"提取了 {total_features} 个新特征")

        except Exception as e:
            logger.error(f"特征提取失败: {e}")
            state["extracted_features"] = {}

        return state

    async def _update_database(self, state: ProfileAnalyzerState) -> ProfileAnalyzerState:
        """更新数据库"""
        logger.info("开始更新数据库")

        user_id = state["user_id"]
        session_id = state["session_id"]
        extracted_features = state.get("extracted_features", {})

        try:
            # 更新数据库中的特征
            for feature_name, feature_data in extracted_features.items():
                await db_manager.upsert_user_feature(
                    user_id=user_id,
                    session_id=session_id,
                    category_name=feature_data['category_name'],
                    feature_name=feature_name,
                    feature_value=feature_data['feature_value'],
                    confidence=feature_data['confidence'],
                    skipped=feature_data.get('skipped', False)
                )

            logger.info(f"成功更新用户 {user_id} 的特征到数据库")

        except Exception as e:
            logger.error(f"更新数据库失败: {e}")

        return state

    async def _evaluate_completeness(self, state: ProfileAnalyzerState) -> ProfileAnalyzerState:
        """评估完整性和完成状态"""
        logger.info("开始评估完整性和完成状态")

        user_id = state["user_id"]
        session_id = state["session_id"]

        try:
            # 获取最新的用户特征摘要
            profile_summary = await db_manager.get_user_profile_summary(user_id, session_id)

            # 分析特征覆盖情况
            coverage_analysis = self._analyze_feature_coverage(
                profile_summary['profile'])

            # 检查必要特征完整性
            required_completeness = self._check_required_features(
                profile_summary['profile'])

            completion_status = {
                'coverage_analysis': coverage_analysis,
                'required_completeness': required_completeness,
                'profile_summary': profile_summary,
                'is_complete': coverage_analysis['all_covered'] and required_completeness['all_required_complete']
            }

            state["completion_status"] = completion_status
            state["is_complete"] = completion_status['is_complete']

            logger.info(
                f"完整性评估完成: 覆盖率 {coverage_analysis['coverage_rate']:.2f}, 必要特征完整性 {required_completeness['completion_rate']:.2f}")

        except Exception as e:
            logger.error(f"评估完整性失败: {e}")
            state["completion_status"] = {
                'coverage_analysis': {'all_covered': False, 'coverage_rate': 0.0},
                'required_completeness': {'all_required_complete': False, 'completion_rate': 0.0},
                'is_complete': False
            }
            state["is_complete"] = False

        return state

    async def _generate_questions(self, state: ProfileAnalyzerState) -> ProfileAnalyzerState:
        """生成问题"""
        logger.info("开始生成问题")

        completion_status = state.get("completion_status", {})
        coverage_analysis = completion_status.get('coverage_analysis', {})
        required_completeness = completion_status.get(
            'required_completeness', {})

        try:
            # 确定需要询问的特征
            missing_features = coverage_analysis.get('missing_features', [])
            missing_required = required_completeness.get(
                'missing_required', [])

            # 生成问题
            questions = await self._generate_smart_questions(missing_features, missing_required, state)

            state["suggested_questions"] = questions
            state["final_answer"] = questions

        except Exception as e:
            logger.error(f"生成问题失败: {e}")
            state["suggested_questions"] = "抱歉，生成问题时出现错误。"
            state["final_answer"] = "抱歉，生成问题时出现错误。"

        return state

    async def _finalize_complete(self, state: ProfileAnalyzerState) -> ProfileAnalyzerState:
        """完成分析"""
        logger.info("用户画像分析完成")

        completion_status = state.get("completion_status", {})
        profile_summary = completion_status.get('profile_summary', {})

        # 生成完成响应
        final_answer = f"""
        🎉 恭喜！您的用户画像分析已完成！

        ## 画像完整度
        - 总体完成率: {profile_summary.get('completion_rate', 0) * 100:.1f}%
        - 已完成特征: {profile_summary.get('completed_features', 0)} 个
        - 总特征数: {profile_summary.get('total_features', 0)} 个

        ## 下一步
        基于您完整的用户画像，我们现在可以为您推荐最适合的保险产品。
        您可以继续使用产品推荐功能来获取个性化的保险建议。
        """

        state["final_answer"] = final_answer
        state["is_complete"] = True

        return state

    def _decide_next_step(self, state: ProfileAnalyzerState) -> str:
        """决定下一步操作"""
        is_complete = state.get("is_complete", False)

        if is_complete:
            return "complete"
        else:
            return "generate_questions"

    # 辅助方法
    async def _call_llm_with_logging(
        self,
        messages: List[BaseMessage],
        operation_name: str
    ) -> str:
        """调用 LLM 并记录详细日志"""
        try:
            # 记录 prompt 前100个字符
            prompt_preview = ""
            if messages:
                first_message = messages[0]
                if hasattr(first_message, 'content') and first_message.content:
                    prompt_preview = str(first_message.content)[:100]

            logger.info(f"开始 LLM 调用 - {operation_name}")
            logger.info(f"Prompt 预览: {prompt_preview}...")

            # 记录开始时间
            start_time = time.time()

            # 调用 LLM
            response = await self.llm.ainvoke(messages)

            # 记录结束时间和耗时
            end_time = time.time()
            duration = end_time - start_time

            # 记录响应信息
            response_content = str(
                response.content) if response.content else ""

            # 记录 token 使用情况（如果可用）
            token_info = ""
            if hasattr(response, 'response_metadata') and response.response_metadata:
                usage = response.response_metadata.get('token_usage', {})
                if usage:
                    prompt_tokens = usage.get('prompt_tokens', 0)
                    completion_tokens = usage.get('completion_tokens', 0)
                    total_tokens = usage.get('total_tokens', 0)
                    token_info = f"Tokens - Prompt: {prompt_tokens}, Completion: {completion_tokens}, Total: {total_tokens}"

            logger.info(f"LLM 调用完成 - {operation_name}")
            logger.info(f"耗时: {duration:.2f}秒")
            if token_info:
                logger.info(token_info)
            logger.info(f"响应长度: {len(response_content)} 字符")

            return response_content

        except Exception as e:
            logger.error(f"LLM 调用失败 - {operation_name}: {e}")
            raise

    def _process_custom_profile(self, custom_profile: UserProfile) -> UserFeatures:
        """处理自定义画像（置信度 1.0）"""
        processed_features: UserFeatures = {}

        for feature_name, value in custom_profile.items():
            if value is None:
                continue

            # 确定特征所属分类
            category = self._get_feature_category(feature_name)
            if category:
                # 标准化字段值
                normalized_value = self._normalize_field_value(
                    feature_name, value)

                processed_features[feature_name] = {
                    'category_name': category,
                    'feature_name': feature_name,
                    'feature_value': normalized_value,
                    'confidence': 1.0,
                    'skipped': False
                }

        return processed_features

    def _get_feature_category(self, feature_name: str) -> Optional[str]:
        """获取特征所属分类"""
        for category, features in self.feature_categories.items():
            if feature_name in features:
                return category
        return None

    def _normalize_field_value(self, feature_name: str, value: Any) -> Any:
        """标准化字段值，确保符合预期的枚举值"""
        if not isinstance(value, str):
            return value

        # 清理输入值
        cleaned_value = str(value).strip()

        # 检查是否有标准化规则
        if feature_name not in self.field_normalization_rules:
            return cleaned_value

        rules = self.field_normalization_rules[feature_name]

        # 首先检查是否已经是有效值
        if cleaned_value in rules['valid_values']:
            return cleaned_value

        # 尝试映射转换
        if cleaned_value in rules['mappings']:
            normalized_value = rules['mappings'][cleaned_value]
            logger.info(
                f"字段 {feature_name} 值标准化: '{cleaned_value}' -> '{normalized_value}'")
            return normalized_value

        # 尝试模糊匹配（忽略大小写）
        cleaned_lower = cleaned_value.lower()
        for mapping_key, mapping_value in rules['mappings'].items():
            if mapping_key.lower() == cleaned_lower:
                logger.info(
                    f"字段 {feature_name} 值标准化(忽略大小写): '{cleaned_value}' -> '{mapping_value}'")
                return mapping_value

        # 如果都不匹配，记录警告并返回原值
        logger.warning(
            f"字段 {feature_name} 的值 '{cleaned_value}' 不在预期的枚举值中: {rules['valid_values']}")
        return cleaned_value

    async def _extract_features_with_llm(
        self,
        history_chats: List[ChatMessage],
        existing_features: UserFeatures
    ) -> UserFeatures:
        """使用 LLM 提取特征"""
        try:
            # 构建对话文本
            conversation_text = "\n".join([
                f"{chat['role']}: {chat['content']}"
                for chat in history_chats
            ])

            # 构建提示词，传入已有特征
            system_prompt = self._build_feature_extraction_prompt(
                existing_features)

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"请分析以下对话并提取用户特征：\n\n{conversation_text}")
            ]

            # 使用带日志的 LLM 调用
            response_content = await self._call_llm_with_logging(messages, "特征提取")

            # 解析 LLM 响应
            if response_content:
                return self._parse_llm_feature_response(response_content)
            else:
                return {}

        except Exception as e:
            logger.error(f"LLM 特征提取失败: {e}")
            return {}

    def _build_feature_extraction_prompt(self, existing_features: UserFeatures) -> str:
        """构建特征提取提示词"""

        # 准备已有特征信息
        existing_features_text = self._format_existing_features_for_llm(
            existing_features)

        return f"""
你是一个专业的保险经纪人和用户画像分析师。请从用户的对话中提取以下特征信息：

{self._format_feature_categories()}

已有的用户特征信息：
{existing_features_text}

请以 JSON 格式返回提取的特征，格式如下：
{{
    "category_name": {{
        "feature_name": {{
            "value": "特征值",
            "confidence": 0.8,
            "reasoning": "提取理由"
        }}
    }}
}}

注意事项：
1. 只提取对话中明确提到或可以合理推断的信息
2. 置信度范围 0.0-1.0，直接提到的信息置信度 0.8，推断的信息置信度 0.5
3. 如果某个特征没有相关信息，请不要包含在结果中
4. 女性特殊状态只有在确认用户是女性时才提取
5. 如果已有特征信息与对话内容冲突，请在 reasoning 中说明
6. 不要重复提取已有的特征，除非发现了更准确的信息
"""

    def _format_feature_categories(self) -> str:
        """格式化特征分类信息，包含详细的特征定义"""

        # 详细的特征定义，来自设计文档
        feature_definitions = {
            "basic_identity": {
                "gender": "性别 (男/女) - 产品匹配、费率计算",
                "date_of_birth": "出生年月日 (YYYY-MM-DD) - 精确年龄计算、产品适配、费率计算",
                "marital_status": "婚姻状况 (未婚/已婚/离异/丧偶) - 家庭责任评估",
                "residence_city": "常住城市 - 产品地区限制、医疗资源评估",
                "occupation_type": "职业类型 (企业员工/公务员/个体经营/企业主/自由职业/学生/退休) - 职业风险评估、产品匹配",
                "industry": "所属行业 - 职业风险评估、收入稳定性判断"
            },
            "female_specific": {
                "pregnancy_status": "孕期状态 (未怀孕/备孕期/孕早期(1-3月)/孕中期(4-6月)/孕晚期(7-9月)/产后恢复期) - 母婴保险需求评估、费率计算",
                "childbearing_plan": "生育计划 (1年内/2年内/3年内/暂无计划) - 母婴保障规划、产品推荐"
            },
            "family_structure": {
                "family_structure": "家庭结构 (单身/夫妻/夫妻+子女/三代同堂/其他) - 家庭责任评估基础",
                "number_of_children": "子女数量 (整数) - 教育规划需求、家庭责任计算",
                "caregiving_responsibility": "赡养责任 (无/赡养父母/赡养双方父母/其他) - 家庭责任评估",
                "monthly_household_expense": "月度家庭支出 (元，数字) - 家庭责任计算、寿险保额计算",
                "mortgage_balance": "房贷余额 (元，数字) - 家庭责任计算、寿险保额计算",
                "is_family_financial_support": "是否家庭经济支柱 (是/否/共同承担) - 家庭责任评估、保额计算"
            },
            "financial_status": {
                "annual_total_income": "年总收入 (万元，数字) - 保额计算、预算规划",
                "income_stability": "收入稳定性 (非常稳定/比较稳定/一般/不稳定) - 风险评估、产品选择",
                "annual_insurance_budget": "年度保险预算 (万元，数字) - 产品组合规划、保费预算分配"
            },
            "health_lifestyle": {
                "overall_health_status": "整体健康状况 (非常健康/比较健康/一般/有慢性病/健康状况较差) - 产品匹配、费率计算",
                "has_chronic_disease": "是否有慢性疾病 (无/高血压/糖尿病/心脏病/其他) - 承保评估、产品匹配",
                "smoking_status": "吸烟情况 (不吸烟/已戒烟/轻度吸烟/重度吸烟) - 健康风险评估、费率计算",
                "recent_medical_checkup": "近期体检情况 (1年内正常/1年内有异常/2年内正常/2年以上未体检) - 健康风险评估、承保评估"
            }
        }

        formatted = []
        for category, features in self.feature_categories.items():
            # 添加分类标题
            category_title = {
                "basic_identity": "基础身份维度 (basic_identity)",
                "female_specific": "女性特殊状态 (female_specific) - 仅女性",
                "family_structure": "家庭结构与责任维度 (family_structure)",
                "financial_status": "财务现状与目标维度 (financial_status)",
                "health_lifestyle": "健康与生活习惯维度 (health_lifestyle)"
            }.get(category, category)

            formatted.append(f"\n{category_title}:")

            # 添加特征定义
            for feature in features:
                definition = feature_definitions.get(
                    category, {}).get(feature, feature)
                formatted.append(f"  - {feature}: {definition}")

        return "\n".join(formatted)

    def _format_existing_features_for_llm(self, existing_features: UserFeatures) -> str:
        """格式化已有特征信息供 LLM 使用"""
        if not existing_features:
            return "暂无已有特征信息"

        formatted_features: List[ExistingFeatureForLLM] = []

        for feature_name, feature_data in existing_features.items():
            # 跳过已跳过的特征
            if not feature_data.get('skipped', False):
                formatted_features.append({
                    'category_name': feature_data['category_name'],
                    'feature_name': feature_name,
                    'feature_value': feature_data['feature_value'],
                    'confidence': feature_data['confidence']
                })

        if not formatted_features:
            return "暂无有效的已有特征信息"

        # 格式化为易读的文本
        formatted_lines = []
        for feature in formatted_features:
            formatted_lines.append(
                f"- {feature['category_name']}.{feature['feature_name']}: "
                f"{feature['feature_value']} (置信度: {feature['confidence']:.2f})"
            )

        return "\n".join(formatted_lines)

    def _parse_llm_feature_response(self, response_content: str) -> UserFeatures:
        """解析 LLM 的特征提取响应"""
        try:
            import json
            import re

            # 尝试提取 JSON 内容
            json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
            if not json_match:
                logger.warning("LLM 响应中未找到 JSON 格式的内容")
                return {}

            json_str = json_match.group(0)
            parsed_data = json.loads(json_str)

            # 转换为 UserFeatures 格式
            result: UserFeatures = {}

            for category_name, features in parsed_data.items():
                if category_name in self.feature_categories:
                    for feature_name, feature_info in features.items():
                        if feature_name in self.feature_categories[category_name]:
                            if isinstance(feature_info, dict) and 'value' in feature_info:
                                # 标准化字段值
                                normalized_value = self._normalize_field_value(
                                    feature_name, feature_info['value'])

                                result[feature_name] = {
                                    'category_name': category_name,
                                    'feature_name': feature_name,
                                    'feature_value': normalized_value,
                                    'confidence': feature_info.get('confidence', 0.5),
                                    'skipped': False
                                }

            return result

        except Exception as e:
            logger.error(f"解析 LLM 响应失败: {e}")
            logger.debug(f"LLM 响应内容: {response_content}")
            return {}

    def _analyze_feature_coverage(self, profile: UserFeatures) -> Dict[str, Any]:
        """分析特征覆盖情况"""
        total_features = sum(len(features)
                             for features in self.feature_categories.values())
        covered_features = 0
        missing_features = []

        for category, expected_features in self.feature_categories.items():
            for feature_name in expected_features:
                if feature_name in profile:
                    feature_data = profile[feature_name]
                    # 如果特征有值或被跳过，都算作已覆盖
                    if feature_data.get('skipped') or (feature_data.get('feature_value') is not None and feature_data.get('confidence', 0) > 0):
                        covered_features += 1
                    else:
                        missing_features.append((category, feature_name))
                else:
                    missing_features.append((category, feature_name))

        coverage_rate = covered_features / total_features if total_features > 0 else 0.0

        return {
            'total_features': total_features,
            'covered_features': covered_features,
            'missing_features': missing_features,
            'coverage_rate': coverage_rate,
            'all_covered': coverage_rate >= 0.8  # 80% 覆盖率认为已完成
        }

    def _check_required_features(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """检查必要特征完整性

        Args:
            profile: 扁平格式的特征数据 (UserFeatures): {feature_name: {feature_value, confidence, skipped, ...}}
        """
        completed_required = 0
        missing_required = []

        for feature_name in self.required_features:
            if feature_name in profile:
                feature_data = profile[feature_name]
                # 必要特征必须有值且置信度 > 0.5
                if (feature_data.get('feature_value') is not None and
                    feature_data.get('confidence', 0) > 0.5 and
                        not feature_data.get('skipped', False)):
                    completed_required += 1
                else:
                    missing_required.append(feature_name)
            else:
                missing_required.append(feature_name)

        total_required = len(self.required_features)
        completion_rate = completed_required / \
            total_required if total_required > 0 else 0.0

        return {
            'total_required': total_required,
            'completed_required': completed_required,
            'missing_required': missing_required,
            'completion_rate': completion_rate,
            'all_required_complete': completion_rate >= 1.0
        }

    def _get_user_questions_history(self, user_id: int) -> List[str]:
        """获取用户的历史问题记录"""
        return self.user_questions_history.get(user_id, [])

    def _get_user_features_history(self, user_id: int) -> List[str]:
        """获取用户的历史特征记录"""
        return self.user_features_history.get(user_id, [])

    def _add_user_question(self, user_id: int, question: str):
        """添加用户问题到历史记录"""
        if user_id not in self.user_questions_history:
            self.user_questions_history[user_id] = []
        self.user_questions_history[user_id].append(question)

        # 限制历史记录长度，避免内存过度使用
        if len(self.user_questions_history[user_id]) > 10:
            self.user_questions_history[user_id] = self.user_questions_history[user_id][-10:]

    def _add_user_features(self, user_id: int, features: List[str]):
        """添加用户特征到历史记录"""
        if user_id not in self.user_features_history:
            self.user_features_history[user_id] = []

        for feature in features:
            if feature not in self.user_features_history[user_id]:
                self.user_features_history[user_id].append(feature)

    def clear_user_history(self, user_id: int):
        """清空指定用户的历史记录"""
        if user_id in self.user_questions_history:
            del self.user_questions_history[user_id]
        if user_id in self.user_features_history:
            del self.user_features_history[user_id]
        logger.info(f"已清空用户 {user_id} 的历史记录")

    async def _generate_smart_questions(
        self,
        missing_features: List[Tuple[str, str]],
        missing_required: List[str],
        state: ProfileAnalyzerState
    ) -> str:
        """生成智能问题，避免重复询问"""
        try:
            user_id = state["user_id"]

            # 获取持久化的已询问过的特征
            asked_features = set(self._get_user_features_history(user_id))

            # 过滤掉已询问过的必要特征
            filtered_missing_required = [
                feature for feature in missing_required
                if feature not in asked_features
            ]

            # 过滤掉已询问过的其他特征
            filtered_missing_features = [
                (category, feature) for category, feature in missing_features
                if feature not in asked_features
            ]

            # 优先询问未问过的必要特征
            priority_features = []
            if filtered_missing_required:
                # 最多询问3个必要特征
                for feature_name in filtered_missing_required[:3]:
                    category = self._get_feature_category(feature_name)
                    if category:
                        priority_features.append((category, feature_name))

            # 如果必要特征不足3个，补充其他未问过的缺失特征
            if len(priority_features) < 3:
                for category, feature_name in filtered_missing_features:
                    if (category, feature_name) not in priority_features:
                        priority_features.append((category, feature_name))
                        if len(priority_features) >= 3:
                            break

            # 如果所有特征都问过了，但仍有缺失，则重新询问最重要的特征
            if not priority_features and (missing_required or missing_features):
                logger.info("所有特征都已询问过，重新询问最重要的必要特征")
                if missing_required:
                    feature_name = missing_required[0]
                    category = self._get_feature_category(feature_name)
                    if category:
                        priority_features.append((category, feature_name))

            # 检查是否需要询问女性特殊状态
            should_ask_female_specific = self._should_ask_female_specific(
                state)

            # 生成问题
            questions_prompt = self._build_questions_prompt(
                priority_features, should_ask_female_specific, state)

            messages = [
                SystemMessage(content=questions_prompt),
                HumanMessage(content="请生成自然、直接的问题来收集这些信息。")
            ]

            # 使用带日志的 LLM 调用
            response_content = await self._call_llm_with_logging(messages, "问题生成")

            # 记录本次询问的特征和问题到持久化存储
            if priority_features and response_content:
                features_to_record = [
                    f for _, f in priority_features if f not in asked_features]
                if features_to_record:
                    self._add_user_features(user_id, features_to_record)
                    logger.info(f"记录询问特征: {features_to_record}")

                self._add_user_question(user_id, response_content)
                logger.info(f"记录询问问题: {response_content[:50]}...")

            return response_content if response_content else "请告诉我更多关于您的信息，以便为您提供更好的保险建议。"

        except Exception as e:
            logger.error(f"生成智能问题失败: {e}")
            return "请告诉我更多关于您的信息，以便为您提供更好的保险建议。"

    def _should_ask_female_specific(self, state: ProfileAnalyzerState) -> bool:
        """判断是否应该询问女性特殊状态"""
        existing_features = state.get("existing_features", {})

        # 从扁平结构中直接查找 gender 特征
        gender_data = existing_features.get("gender", {})

        if gender_data:
            gender_value = gender_data.get("feature_value", "")
            if isinstance(gender_value, str):
                gender_value = gender_value.lower()
            confidence = gender_data.get("confidence", 0)
            return gender_value == "女" and confidence > 0.5

        return False

    def _build_questions_prompt(self, priority_features: List[Tuple[str, str]], ask_female_specific: bool, state: ProfileAnalyzerState) -> str:
        """构建问题生成提示词，避免重复询问"""
        feature_descriptions = {
            'gender': '性别',
            'date_of_birth': '出生年月日',
            'marital_status': '婚姻状况',
            'occupation_type': '职业类型',
            'industry': '所属行业',
            'family_structure': '家庭结构',
            'monthly_household_expense': '月度家庭支出',
            'is_family_financial_support': '是否为家庭经济支柱',
            'annual_total_income': '年总收入',
            'income_stability': '收入稳定性',
            'annual_insurance_budget': '年度保险预算',
            'overall_health_status': '整体健康状况'
        }

        features_to_ask = []
        for _, feature_name in priority_features:
            description = feature_descriptions.get(feature_name, feature_name)
            features_to_ask.append(description)

        # 获取持久化的历史问题，用于避免重复的问法
        user_id = state["user_id"]
        asked_questions = self._get_user_questions_history(user_id)
        question_count = len(asked_questions)

        # 构建历史问题上下文
        history_context = ""
        if asked_questions:
            recent_questions = asked_questions[-3:]  # 只显示最近3个问题
            history_context = f"""
之前已询问过的问题：
{chr(10).join(f"- {q}" for q in recent_questions)}

请避免使用相同的开头、问法或语气。要更加直接、自然，不要每次都打招呼。
"""

        # 根据问题次数调整语气
        if question_count == 0:
            tone_instruction = "这是第一次询问，可以稍微正式一些，但要友好。"
        elif question_count <= 2:
            tone_instruction = "继续对话，语气要自然，就像朋友间的交流。"
        else:
            tone_instruction = "已经问过几个问题了，要更加直接简洁，避免过多的客套话。"

        prompt = f"""
你是一位专业的保险经纪人，你需要通过一些自然的对话，从客户那里了解一些隐私信息。

要求：
1. 每次只问1个问题，选择最重要的信息
2. 问题要直接、自然，避免重复的开头和问法
3. 不要每次都说"您好"、"为了更好地..."等客套话
4. 可以假定用户对保险有兴趣，不需要解释为什么需要这些信息
5. 允许用户选择不回答，但不要主动提及
6. 语气要像真实的保险经纪人，专业但不生硬
7. {tone_instruction}

{'注意：如果用户是女性，可以适当询问生育相关的信息。' if ask_female_specific else ''}

{history_context}

现在需要了解的信息：
{', '.join(features_to_ask)}

请生成一个自然、直接的问题：
"""
        return prompt

    async def analyze_profile(self, request: ProfileAnalysisRequest) -> AsyncGenerator[AgentResponse, None]:
        """执行用户画像分析"""
        try:
            # 确保数据库已初始化
            await db_manager.initialize()

            # 初始化状态
            initial_state: ProfileAnalyzerState = {
                "user_id": request["user_id"],
                "session_id": request["session_id"],
                "history_chats": request["history_chats"],
                "custom_profile": request.get("custom_profile"),
                "existing_features": {},
                "extracted_features": {},
                "completion_status": {},
                "suggested_questions": None,
                "final_answer": None,
                "is_complete": False,
                "asked_questions_history": [],
                "asked_features_history": []
            }

            # 执行工作流
            async for event in self.workflow.astream(initial_state):
                for node_name, node_output in event.items():
                    if node_name == "load_existing_features":
                        yield ThinkingResponse(
                            type="thinking",
                            content="正在加载您的已有信息...",
                            step="load_features"
                        )
                    elif node_name == "analyze_conversation":
                        yield ThinkingResponse(
                            type="thinking",
                            content="正在分析您的对话内容...",
                            step="analyze_conversation"
                        )
                    elif node_name == "extract_new_features":
                        yield ThinkingResponse(
                            type="thinking",
                            content="正在提取新的用户特征...",
                            step="extract_features"
                        )

                        # 检查是否有新提取的特征，如果有则及时返回
                        extracted_features = node_output.get(
                            "extracted_features", {})
                        if extracted_features:
                            # 将特征转换为 ProfileResponse 格式
                            features_list = []
                            for feature_name, feature_data in extracted_features.items():
                                features_list.append({
                                    "category_name": feature_data["category_name"],
                                    "feature_name": feature_name,
                                    "feature_value": feature_data["feature_value"],
                                    "confidence": feature_data["confidence"],
                                    "skipped": feature_data.get("skipped", False)})

                            yield ProfileResponse(
                                type="profile",
                                features=features_list,
                                message=f"成功提取了 {len(features_list)} 个用户特征"
                            )
                    elif node_name == "update_database":
                        yield ThinkingResponse(
                            type="thinking",
                            content="正在更新您的用户画像...",
                            step="update_database"
                        )
                    elif node_name == "evaluate_completeness":
                        yield ThinkingResponse(
                            type="thinking",
                            content="正在评估画像完整性...",
                            step="evaluate_completeness"
                        )
                    elif node_name == "generate_questions":
                        yield AnswerResponse(
                            type="answer",
                            content=node_output.get("final_answer", "请提供更多信息"),
                            data={
                                "questions": node_output.get("suggested_questions"),
                                "completion_status": node_output.get("completion_status", {})
                            }
                        )
                    elif node_name == "finalize_complete":
                        completion_status = node_output.get(
                            "completion_status", {})
                        profile_summary = completion_status.get(
                            "profile_summary", {})

                        yield UserProfileCompleteResponse(
                            type="profile_complete",
                            message=node_output.get(
                                "final_answer", "用户画像分析完成"),
                            profile_summary=profile_summary.get("profile", {}),
                            completion_rate=profile_summary.get(
                                "completion_rate", 0.0)
                        )

        except Exception as e:
            logger.error(f"用户画像分析过程中发生错误: {e}")
            yield ErrorResponse(
                type="error",
                error="分析过程中发生错误",
                details=str(e)
            )
