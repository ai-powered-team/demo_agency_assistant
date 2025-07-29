"""
保险经纪人推荐器

使用 LangGraph 实现经纪人推荐的业务逻辑。
"""

import json
import time
from typing import AsyncGenerator, List, Optional, Dict, Any
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, END
from langgraph.graph.state import CompiledStateGraph
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from pydantic import SecretStr

from util import (
    config, logger, AgencyRecommendRequest, AgentResponse,
    ThinkingResponse, AnswerResponse, ErrorResponse, ChatMessage,
    AgencyInfo, AgencyTone, AgencyRecommendResponse,
    QuestionRecommendResponse, ViewpointAnalysisResponse
)


class AgencyRecommenderState(TypedDict):
    """推荐经纪人状态类"""
    user_id: int
    history_chats: List[ChatMessage]
    agency_id: int
    agencies: List[AgencyInfo]
    current_agency: Optional[AgencyInfo]
    conversation_ended: Optional[bool]  # 新增：标记对话是否已结束
    user_preferences: Optional[Dict[str, Any]]
    communication_analysis: Optional[Dict[str, Any]]
    matching_scores: Optional[Dict[int, float]]
    recommendation_result: Optional[Dict[str, Any]]
    question_recommendations: Optional[Dict[str, Any]]
    viewpoint_analysis: Optional[Dict[str, Any]]
    final_answer: Optional[str]


class AgencyRecommender:
    """保险经纪人推荐器"""

    def __init__(self):
        """初始化推荐器"""
        self.llm = ChatOpenAI(
            model=config.OPENAI_MODEL,
            api_key=SecretStr(config.OPENAI_API_KEY),
            base_url=config.OPENAI_BASE_URL,
            temperature=0.1
        )
        self.workflow = self._create_workflow()

    def _create_workflow(self) -> CompiledStateGraph:
        """创建 LangGraph 工作流"""
        workflow = StateGraph(AgencyRecommenderState)

        # 添加节点
        workflow.add_node("check_conversation_end",
                          self._check_conversation_end)
        workflow.add_node("start_parallel_analysis",
                          self._start_parallel_analysis)
        workflow.add_node("generate_recommendation",
                          self._generate_recommendation)
        workflow.add_node("generate_question_recommendations",
                          self._generate_question_recommendations)
        workflow.add_node("analyze_viewpoints", self._analyze_viewpoints)
        workflow.add_node("handle_conversation_end",
                          self._handle_conversation_end)

        # 设置入口点
        workflow.set_entry_point("check_conversation_end")

        # 添加条件边：检查对话是否结束
        workflow.add_conditional_edges(
            "check_conversation_end",
            self._decide_conversation_flow,
            {
                "continue": "start_parallel_analysis",
                "end": "handle_conversation_end"
            }
        )

        # 恢复并行执行，但优化LLM调用
        workflow.add_edge("start_parallel_analysis", "generate_recommendation")
        workflow.add_edge("start_parallel_analysis",
                          "generate_question_recommendations")
        workflow.add_edge("start_parallel_analysis", "analyze_viewpoints")

        # 所有节点直接结束，不需要汇聚
        workflow.add_edge("generate_recommendation", END)
        workflow.add_edge("generate_question_recommendations", END)
        workflow.add_edge("analyze_viewpoints", END)
        workflow.add_edge("handle_conversation_end", END)

        return workflow.compile()

    async def recommend_agency(self, request: AgencyRecommendRequest) -> AsyncGenerator[AgentResponse, None]:
        """推荐经纪人主方法"""
        try:
            # 初始化状态
            initial_state: AgencyRecommenderState = {
                "user_id": request["user_id"],
                "history_chats": request["history_chats"],
                "agency_id": request["agency_id"],
                "agencies": request["agencies"],
                "current_agency": None,
                "conversation_ended": None,
                "user_preferences": None,
                "communication_analysis": None,
                "matching_scores": None,
                "recommendation_result": None,
                "question_recommendations": None,
                "viewpoint_analysis": None,
                "final_answer": None
            }

            # 查找当前经纪人信息
            for agency in request["agencies"]:
                if agency["agency_id"] == request["agency_id"]:
                    initial_state["current_agency"] = agency
                    break

            if not initial_state["current_agency"]:
                yield ErrorResponse(
                    type="error",
                    error="当前经纪人信息未找到",
                    details=f"经纪人ID {request['agency_id']} 不在提供的经纪人列表中"
                )
                return

            # 执行工作流
            async for output in self.workflow.astream(initial_state):
                for node_name, node_output in output.items():
                    if node_name == "check_conversation_end":
                        yield ThinkingResponse(
                            type="thinking",
                            content="正在检查对话状态...",
                            step="check_conversation_end"
                        )
                    elif node_name == "handle_conversation_end":
                        yield ThinkingResponse(
                            type="thinking",
                            content="正在处理对话结束...",
                            step="handle_conversation_end"
                        )

                        # 返回对话结束的答案
                        if node_output.get("final_answer"):
                            yield AnswerResponse(
                                type="answer",
                                content=node_output["final_answer"],
                                data=None
                            )
                    elif node_name == "start_parallel_analysis":
                        yield ThinkingResponse(
                            type="thinking",
                            content="正在启动并行分析...",
                            step="start_parallel_analysis"
                        )
                    elif node_name == "generate_recommendation":
                        yield ThinkingResponse(
                            type="thinking",
                            content="正在快速生成推荐结果...",
                            step="generate_recommendation"
                        )

                        # 返回推荐结果
                        if node_output.get("recommendation_result"):
                            result = node_output["recommendation_result"]
                            yield AgencyRecommendResponse(
                                type="agency_recommend",
                                current_agency_id=result["current_agency_id"],
                                recommended_agency_id=result["recommended_agency_id"],
                                should_switch=result["should_switch"],
                                recommendation_reason=result["recommendation_reason"],
                                user_preference_analysis=result["user_preference_analysis"],
                                communication_effectiveness=result["communication_effectiveness"],
                                confidence_score=result["confidence_score"]
                            )
                    elif node_name == "generate_question_recommendations":
                        yield ThinkingResponse(
                            type="thinking",
                            content="正在快速推荐问题...",
                            step="generate_question_recommendations"
                        )

                        # 返回问题推荐结果
                        if node_output.get("question_recommendations"):
                            result = node_output["question_recommendations"]
                            yield QuestionRecommendResponse(
                                type="question_recommend",
                                questions=result["questions"],
                                analysis_reason=result["analysis_reason"],
                                conversation_stage=result["conversation_stage"],
                                priority_level=result["priority_level"]
                            )
                    elif node_name == "analyze_viewpoints":
                        yield ThinkingResponse(
                            type="thinking",
                            content="正在分析经纪人观点...",
                            step="analyze_viewpoints"
                        )

                        # 返回观点分析结果
                        if node_output.get("viewpoint_analysis"):
                            result = node_output["viewpoint_analysis"]
                            yield ViewpointAnalysisResponse(
                                type="viewpoint_analysis",
                                agent_viewpoints=result["agent_viewpoints"],
                                overall_assessment=result["overall_assessment"],
                                risk_warnings=result["risk_warnings"],
                                suggestions=result["suggestions"]
                            )

        except Exception as e:
            logger.error(f"推荐经纪人过程中发生错误: {e}")
            yield ErrorResponse(
                type="error",
                error="推荐过程中发生错误",
                details=str(e)
            )

    async def _call_llm_with_logging(self, operation_name: str, messages: List) -> str:
        """带日志记录的 LLM 调用"""
        start_time = time.time()

        # 记录调用开始
        prompt_preview = messages[0].content[:100] if messages else "无内容"
        logger.info(f"开始 LLM 调用 - {operation_name}")
        logger.info(f"Prompt 预览: {prompt_preview}...")

        try:
            response = await self.llm.ainvoke(messages)

            # 记录调用完成
            end_time = time.time()
            duration = end_time - start_time

            # 确保返回字符串类型
            content = response.content
            if isinstance(content, list):
                # 如果是列表，尝试提取第一个字符串元素或转换为JSON字符串
                if content and isinstance(content[0], str):
                    content = content[0]
                else:
                    content = json.dumps(content, ensure_ascii=False)
            elif not isinstance(content, str):
                # 如果不是字符串也不是列表，转换为字符串
                content = str(content)

            logger.info(f"LLM 调用完成 - {operation_name}")
            logger.info(f"耗时: {duration:.2f}秒")
            logger.info(f"响应长度: {len(content)} 字符")

            return content

        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            logger.error(
                f"LLM 调用失败 - {operation_name}, 耗时: {duration:.2f}秒, 错误: {e}")
            raise

    async def _check_conversation_end(self, state: AgencyRecommenderState) -> AgencyRecommenderState:
        """检查对话是否已经结束（精简LLM版）"""
        logger.info("开始检查对话是否已经结束")

        history_chats = state["history_chats"]

        if not history_chats:
            logger.info("对话历史为空，认为对话未结束")
            state["conversation_ended"] = False
            return state

        # 先进行快速关键词检查
        last_user_message = None
        for msg in reversed(history_chats):
            if msg["role"] == "user":
                last_user_message = msg["content"].lower()
                break

        if last_user_message:
            # 明确的结束关键词，直接判断
            end_keywords = ["谢谢", "感谢", "再见", "不用了", "够了", "明白了"]
            for keyword in end_keywords:
                if keyword in last_user_message:
                    state["conversation_ended"] = True
                    logger.info(f"对话已结束，原因：用户使用了结束关键词：{keyword}")
                    return state

        # 如果没有明确关键词，且对话较短，认为未结束
        if len(history_chats) < 6:
            state["conversation_ended"] = False
            logger.info("对话较短，认为未结束")
            return state

        # 对于较长对话，使用精简LLM判断
        last_few_messages = history_chats[-4:]  # 只看最后4条消息
        conversation_text = "\n".join([
            f"{msg['role'].value}: {msg['content']}"
            for msg in last_few_messages
        ])

        prompt = f"""判断对话是否结束：
{conversation_text}

用户是否表达了结束意图？返回JSON：
{{"conversation_ended": true/false}}

只返回JSON，不要其他内容。"""

        try:
            messages = [HumanMessage(content=prompt)]
            response = await self._call_llm_with_logging("对话结束判断", messages)
            result = json.loads(response.strip())
            conversation_ended = result.get("conversation_ended", False)

            state["conversation_ended"] = conversation_ended
            logger.info(f"对话{'已结束' if conversation_ended else '未结束'}")

        except Exception as e:
            logger.error(f"对话结束判断失败: {e}")
            state["conversation_ended"] = False

        return state

    def _decide_conversation_flow(self, state: AgencyRecommenderState) -> str:
        """决定对话流程的下一步"""
        if state.get("conversation_ended", False):
            return "end"
        else:
            return "continue"

    async def _start_parallel_analysis(self, state: AgencyRecommenderState) -> AgencyRecommenderState:
        """启动并行分析的中间节点"""
        logger.info("启动并行分析")
        # 这个节点只是用来触发并行执行，不做任何处理
        return state

    async def _handle_conversation_end(self, state: AgencyRecommenderState) -> AgencyRecommenderState:
        """处理对话结束的情况"""
        logger.info("处理对话结束情况")

        state["final_answer"] = """
感谢您的咨询！看起来您对当前的沟通已经比较满意了。

如果您后续还有任何关于保险经纪人推荐的问题，随时可以继续咨询。

祝您生活愉快！
"""

        # 清空其他不必要的分析结果
        state["recommendation_result"] = None
        state["question_recommendations"] = None
        state["viewpoint_analysis"] = None

        return state

    def _calculate_agency_match_score(self, user_preferences: Dict[str, Any], agency: AgencyInfo) -> float:
        """计算单个经纪人的匹配度分数"""
        score = 0.0

        # 风格匹配度 (权重: 0.5)
        style_score = self._calculate_style_match(
            user_preferences.get("communication_style", ""), agency["tone"])
        score += style_score * 0.5

        # 经验适配度 (权重: 0.3)
        experience_score = self._calculate_experience_match(
            user_preferences, agency["experience_years"])
        score += experience_score * 0.3

        # 节奏匹配度 (权重: 0.2)
        pace_score = self._calculate_pace_match(
            user_preferences.get("communication_pace", ""), agency["tone"])
        score += pace_score * 0.2

        return min(1.0, max(0.0, score))  # 确保分数在 0-1 范围内

    def _calculate_style_match(self, user_style: str, agency_tone: AgencyTone) -> float:
        """计算风格匹配度"""
        # 风格匹配映射表
        style_mapping = {
            "专业型": {
                AgencyTone.PROFESSIONAL: 1.0,
                AgencyTone.CONSULTATIVE: 0.8,
                AgencyTone.TRUSTWORTHY: 0.7,
                AgencyTone.FRIENDLY: 0.4,
                AgencyTone.ENTHUSIASTIC: 0.3
            },
            "情感型": {
                AgencyTone.FRIENDLY: 1.0,
                AgencyTone.TRUSTWORTHY: 0.8,
                AgencyTone.ENTHUSIASTIC: 0.7,
                AgencyTone.CONSULTATIVE: 0.5,
                AgencyTone.PROFESSIONAL: 0.3
            },
            "效率型": {
                AgencyTone.PROFESSIONAL: 0.9,
                AgencyTone.ENTHUSIASTIC: 0.8,
                AgencyTone.CONSULTATIVE: 0.6,
                AgencyTone.TRUSTWORTHY: 0.5,
                AgencyTone.FRIENDLY: 0.4
            },
            "咨询型": {
                AgencyTone.CONSULTATIVE: 1.0,
                AgencyTone.PROFESSIONAL: 0.8,
                AgencyTone.TRUSTWORTHY: 0.7,
                AgencyTone.FRIENDLY: 0.6,
                AgencyTone.ENTHUSIASTIC: 0.4
            },
            "信任型": {
                AgencyTone.TRUSTWORTHY: 1.0,
                AgencyTone.FRIENDLY: 0.8,
                AgencyTone.CONSULTATIVE: 0.7,
                AgencyTone.PROFESSIONAL: 0.6,
                AgencyTone.ENTHUSIASTIC: 0.5
            }
        }

        return style_mapping.get(user_style, {}).get(agency_tone, 0.5)

    def _calculate_experience_match(self, user_preferences: Dict[str, Any], experience_years: int) -> float:
        """计算经验适配度"""
        # 根据用户决策风格和关注点判断对经验的需求
        decision_style = user_preferences.get("decision_style", "谨慎")

        # 基础经验分数
        if experience_years >= 10:
            base_score = 1.0
        elif experience_years >= 5:
            base_score = 0.8
        elif experience_years >= 3:
            base_score = 0.6
        else:
            base_score = 0.4

        # 根据决策风格调整
        if decision_style == "谨慎":
            # 谨慎型用户更看重经验
            return min(1.0, base_score + 0.1)
        elif decision_style == "果断":
            # 果断型用户对经验要求相对较低
            return max(0.5, base_score - 0.1)

        return base_score

    def _calculate_pace_match(self, user_pace: str, agency_tone: AgencyTone) -> float:
        """计算节奏匹配度"""
        # 节奏匹配映射表
        pace_mapping = {
            "快节奏": {
                AgencyTone.ENTHUSIASTIC: 1.0,
                AgencyTone.PROFESSIONAL: 0.8,
                AgencyTone.CONSULTATIVE: 0.5,
                AgencyTone.TRUSTWORTHY: 0.6,
                AgencyTone.FRIENDLY: 0.7
            },
            "慢节奏": {
                AgencyTone.TRUSTWORTHY: 1.0,
                AgencyTone.CONSULTATIVE: 0.9,
                AgencyTone.FRIENDLY: 0.8,
                AgencyTone.PROFESSIONAL: 0.6,
                AgencyTone.ENTHUSIASTIC: 0.3
            },
            "互动型": {
                AgencyTone.FRIENDLY: 1.0,
                AgencyTone.ENTHUSIASTIC: 0.9,
                AgencyTone.CONSULTATIVE: 0.8,
                AgencyTone.TRUSTWORTHY: 0.7,
                AgencyTone.PROFESSIONAL: 0.5
            },
            "倾听型": {
                AgencyTone.CONSULTATIVE: 1.0,
                AgencyTone.TRUSTWORTHY: 0.9,
                AgencyTone.FRIENDLY: 0.8,
                AgencyTone.PROFESSIONAL: 0.7,
                AgencyTone.ENTHUSIASTIC: 0.4
            }
        }

        return pace_mapping.get(user_pace, {}).get(agency_tone, 0.5)

    async def _generate_recommendation(self, state: AgencyRecommenderState) -> Dict[str, Any]:
        """生成推荐结果"""
        logger.info("开始生成推荐结果")
        result = {}

        # 如果对话已结束，跳过推荐生成
        if state.get("conversation_ended", False):
            logger.info("对话已结束，跳过推荐生成")
            result["recommendation_result"] = None
            return result

        current_agency_id = state["agency_id"]
        history_chats = state["history_chats"]
        agencies = state["agencies"]

        # 步骤1: 快速提取用户沟通偏好
        logger.info("步骤1: 快速提取用户沟通偏好")
        user_preferences = await self._extract_user_preferences_internal(history_chats)

        # 步骤2: 计算匹配度分数
        logger.info("步骤2: 计算匹配度分数")
        matching_scores = self._calculate_matching_scores_internal(
            user_preferences, agencies)

        # 步骤3: 生成推荐结果
        logger.info("步骤3: 生成推荐结果")

        # 找到最佳匹配的经纪人
        best_agency_id = max(matching_scores.keys(),
                             key=lambda x: matching_scores[x])
        best_score = matching_scores[best_agency_id]
        current_score = matching_scores.get(current_agency_id, 0.0)

        # 判断是否建议切换
        score_difference = best_score - current_score
        should_switch = score_difference > 0.2 and current_score < 0.7

        # 使用简化的 LLM 生成推荐理由
        recommendation_result = await self._generate_recommendation_with_llm(
            user_preferences, matching_scores, current_agency_id, best_agency_id, should_switch
        )

        result["recommendation_result"] = recommendation_result
        logger.info("推荐结果生成完成")

        return result

    async def _extract_user_preferences_internal(self, history_chats: List[ChatMessage]) -> Dict[str, Any]:
        """内部方法：提取用户沟通偏好（精简LLM版）"""

        # 如果对话历史很短，直接使用默认偏好
        if len(history_chats) < 4:
            logger.info("对话历史较短，使用默认偏好设置")
            return {
                "communication_style": "咨询型",
                "communication_pace": "互动型",
                "decision_style": "谨慎",
                "key_concerns": [],
                "analysis_summary": ""
            }

        # 只提取用户消息，减少输入token
        user_messages = [
            msg["content"] for msg in history_chats[-6:]  # 只取最近6条消息
            if msg["role"] == "user"
        ]

        if not user_messages:
            return {
                "communication_style": "咨询型",
                "communication_pace": "互动型",
                "decision_style": "谨慎",
                "key_concerns": [],
                "analysis_summary": ""
            }

        # 精简的prompt，减少输入token
        user_text = " ".join(user_messages)
        prompt = f"""分析用户沟通偏好，用户说："{user_text}"

返回JSON：
{{
    "communication_style": "专业型/情感型/效率型/咨询型/信任型",
    "communication_pace": "快节奏/慢节奏/互动型/倾听型",
    "decision_style": "理性/感性/谨慎/果断"
}}

只返回JSON，不要其他内容，以花括号开头和结尾。"""

        try:
            messages = [HumanMessage(content=prompt)]
            response = await self._call_llm_with_logging("用户偏好分析", messages)
            result = json.loads(response.strip())

            return {
                "communication_style": result.get("communication_style", "咨询型"),
                "communication_pace": result.get("communication_pace", "互动型"),
                "decision_style": result.get("decision_style", "谨慎"),
                "key_concerns": [],  # 简化：不分析关注点
                "analysis_summary": ""  # 简化：不返回详细分析
            }
        except Exception as e:
            logger.error(f"用户偏好分析失败: {e}")
            return {
                "communication_style": "咨询型",
                "communication_pace": "互动型",
                "decision_style": "谨慎",
                "key_concerns": [],
                "analysis_summary": ""
            }

    async def _evaluate_communication_internal(self, history_chats: List[ChatMessage], current_agency: Optional[AgencyInfo]) -> Dict[str, Any]:
        """内部方法：评估当前沟通效果（简化版）"""

        if not current_agency:
            logger.warning("当前经纪人信息不存在，跳过沟通效果评估")
            return {
                "effectiveness_score": 5.0,
                "analysis_summary": ""
            }

        # 简化评估：只计算基础评分，不进行详细分析
        conversation_length = len(history_chats)

        # 基于对话长度简单评估效果
        if conversation_length >= 10:
            effectiveness_score = 7.5  # 对话较长，认为效果较好
        elif conversation_length >= 5:
            effectiveness_score = 6.5  # 对话中等，效果一般
        else:
            effectiveness_score = 5.5  # 对话较短，效果待观察

        return {
            "communication_quality": {
                "understanding_level": "中",
                "response_matching": "中",
                "information_delivery": "中",
                "emotional_connection": "中"
            },
            "identified_issues": [],  # 简化：不分析具体问题
            "effectiveness_score": effectiveness_score,
            "improvement_suggestions": [],  # 简化：不提供改进建议
            "analysis_summary": ""  # 简化：不返回详细分析
        }

    def _calculate_matching_scores_internal(self, user_preferences: Dict[str, Any], agencies: List[AgencyInfo]) -> Dict[int, float]:
        """内部方法：计算经纪人匹配度分数"""
        matching_scores = {}
        for agency in agencies:
            score = self._calculate_agency_match_score(
                user_preferences, agency)
            matching_scores[agency["agency_id"]] = score
        logger.info(f"计算完成，共评估 {len(agencies)} 个经纪人")
        return matching_scores

    async def _generate_recommendation_with_llm(self, user_preferences: Dict[str, Any],
                                                matching_scores: Dict[int, float], current_agency_id: int, best_agency_id: int,
                                                should_switch: bool) -> Dict[str, Any]:
        """内部方法：使用精简LLM生成推荐结果"""

        # 如果不需要切换，直接返回简单结果
        if not should_switch:
            return {
                "current_agency_id": current_agency_id,
                "recommended_agency_id": current_agency_id,
                "should_switch": False,
                "recommendation_reason": "当前经纪人与您的沟通风格匹配良好，建议继续当前对话。",
                "user_preference_analysis": "",  # 简化：不返回详细分析
                "communication_effectiveness": "",  # 简化：不返回详细分析
                "confidence_score": matching_scores.get(current_agency_id, 0.7)
            }

        # 需要切换时，使用精简prompt生成理由
        current_score = matching_scores.get(current_agency_id, 0.0)
        best_score = matching_scores[best_agency_id]
        user_style = user_preferences.get('communication_style', '咨询型')

        prompt = f"""用户偏好{user_style}风格，当前经纪人匹配度{current_score:.1f}，推荐经纪人匹配度{best_score:.1f}。

用一句话（不超过30字）说明切换好处："""

        try:
            messages = [HumanMessage(content=prompt)]
            response = await self._call_llm_with_logging("推荐理由生成", messages)

            # 确保理由不超过50字
            recommendation_reason = response.strip()[:50]

            return {
                "current_agency_id": current_agency_id,
                "recommended_agency_id": best_agency_id,
                "should_switch": should_switch,
                "recommendation_reason": recommendation_reason,
                "user_preference_analysis": "",  # 简化：不返回详细分析
                "communication_effectiveness": "",  # 简化：不返回详细分析
                "confidence_score": best_score
            }
        except Exception as e:
            logger.error(f"推荐理由生成失败: {e}")
            return {
                "current_agency_id": current_agency_id,
                "recommended_agency_id": best_agency_id,
                "should_switch": should_switch,
                "recommendation_reason": "推荐经纪人匹配度更高，沟通效果可能更好。",
                "user_preference_analysis": "",
                "communication_effectiveness": "",
                "confidence_score": best_score
            }

    async def _generate_question_recommendations(self, state: AgencyRecommenderState) -> Dict[str, Any]:
        """生成问题推荐"""
        logger.info("开始生成问题推荐")
        result = {}

        history_chats = state["history_chats"]

        # 如果对话已结束，不生成问题推荐
        if state.get("conversation_ended", False):
            logger.info("对话已结束，跳过问题推荐")
            result["question_recommendations"] = {
                "questions": [],
                "analysis_reason": "",  # 简化：不返回分析理由
                "conversation_stage": "结束阶段",
                "priority_level": "无"
            }
            return result

        # 使用精简LLM生成问题推荐
        logger.info("使用精简LLM生成问题推荐")

        # 只取最近的对话内容，减少输入token
        recent_chats = history_chats[-6:]  # 只看最近6条消息
        conversation_text = "\n".join([
            f"{msg['role']}: {msg['content']}"
            for msg in recent_chats
        ])

        prompt = f"""基于对话推荐3个问题：
{conversation_text}

推荐3个用户应该问的保险问题，每个不超过15字。

返回JSON：
{{
    "questions": ["问题1", "问题2", "问题3"],
    "stage": "初期/深入/决策"
}}

只返回JSON，不要其他内容。"""

        try:
            messages = [HumanMessage(content=prompt)]
            response = await self._call_llm_with_logging("问题推荐生成", messages)

            recommendations = json.loads(response.strip())
            questions = recommendations.get("questions", [])[:3]

            # 确保每个问题不超过30字
            filtered_questions = [q[:30] for q in questions]

            # 如果LLM返回的问题不够，补充默认问题
            if len(filtered_questions) < 3:
                default_questions = ["保障范围有哪些？", "保费如何计算？", "理赔流程如何？"]
                for q in default_questions:
                    if len(filtered_questions) < 3:
                        filtered_questions.append(q)

            result["question_recommendations"] = {
                "questions": filtered_questions[:3],
                "analysis_reason": "",  # 简化：不返回分析理由
                "conversation_stage": recommendations.get("stage", "深入了解"),
                "priority_level": "高" if len(history_chats) < 6 else "中"
            }

            logger.info("问题推荐生成完成（精简LLM模式）")

        except Exception as e:
            logger.error(f"问题推荐生成失败: {e}")
            # 设置默认推荐
            result["question_recommendations"] = {
                "questions": ["保障范围有哪些？", "保费如何计算？", "理赔流程如何？"],
                "analysis_reason": "",
                "conversation_stage": "深入了解",
                "priority_level": "中"
            }

        return result

    async def _analyze_viewpoints(self, state: AgencyRecommenderState) -> Dict[str, Any]:
        """分析经纪人观点（精简LLM版）"""
        logger.info("开始分析经纪人观点")
        result = {}

        # 如果对话已结束，不进行观点分析
        if state.get("conversation_ended", False):
            logger.info("对话已结束，跳过观点分析")
            result["viewpoint_analysis"] = {
                "agent_viewpoints": [],
                "overall_assessment": "对话已结束，无需进行观点分析",
                "risk_warnings": [],
                "suggestions": []
            }
            return result

        history_chats = state["history_chats"]

        # 提取经纪人的发言
        agent_messages = [
            msg["content"] for msg in history_chats
            if msg["role"] == "assistant"
        ]

        # 如果对话太短或经纪人没有表达观点，跳过分析
        if not agent_messages or not self._has_meaningful_viewpoints(agent_messages):
            logger.info("对话较短或经纪人没有表达明确观点，跳过观点分析")
            result["viewpoint_analysis"] = {
                "agent_viewpoints": [],
                "overall_assessment": "经纪人主要在客观回答问题，没有表达明确的主观观点",
                "risk_warnings": [],
                "suggestions": []
            }
            return result

        # 使用精简LLM进行观点分析
        logger.info("使用精简LLM进行观点分析")

        # 只取最近的经纪人发言，减少输入token
        recent_agent_messages = agent_messages[-3:]  # 只看最近3条经纪人消息
        agent_text = " ".join(recent_agent_messages)

        prompt = f"""分析经纪人观点："{agent_text}"

是否有风险表述？返回JSON：
{{
    "risk_level": "低/中/高",
    "assessment": "简短评估",
    "warnings": ["风险1", "风险2"]
}}

只返回JSON，不要其他内容。"""

        try:
            messages = [HumanMessage(content=prompt)]
            response = await self._call_llm_with_logging("观点分析", messages)

            analysis = json.loads(response.strip())

            result["viewpoint_analysis"] = {
                "agent_viewpoints": [
                    {
                        "viewpoint_content": "经纪人的产品介绍和建议",
                        "accuracy_assessment": "部分准确",
                        "objectivity_assessment": "部分客观",
                        "risk_level": analysis.get("risk_level", "低"),
                        "analysis_detail": analysis.get("assessment", "基于LLM分析的评估结果")
                    }
                ],
                "overall_assessment": analysis.get("assessment", "经纪人表现基本正常"),
                "risk_warnings": analysis.get("warnings", ["建议核实经纪人提供的信息"]),
                "suggestions": ["建议多方比较", "仔细阅读条款"]
            }

            logger.info("观点分析完成（精简LLM模式）")

        except Exception as e:
            logger.error(f"观点分析失败: {e}")
            # 设置默认分析
            result["viewpoint_analysis"] = {
                "agent_viewpoints": [
                    {
                        "viewpoint_content": "经纪人的产品介绍和建议",
                        "accuracy_assessment": "部分准确",
                        "objectivity_assessment": "部分客观",
                        "risk_level": "低",
                        "analysis_detail": "分析失败，使用默认评估"
                    }
                ],
                "overall_assessment": "建议用户谨慎评估经纪人的建议",
                "risk_warnings": ["请仔细核实经纪人提供的信息"],
                "suggestions": ["建议咨询多个经纪人的意见"]
            }

        return result

    def _has_meaningful_viewpoints(self, agent_messages: List[str]) -> bool:
        """判断经纪人是否表达了有意义的观点"""
        if not agent_messages:
            return False

        # 检查是否包含主观性表述的关键词
        viewpoint_keywords = [
            "建议", "推荐", "认为", "觉得", "应该", "最好", "优势", "劣势",
            "适合", "不适合", "值得", "划算", "性价比", "比较好", "更好",
            "我觉得", "我认为", "我建议", "个人建议"
        ]

        combined_text = " ".join(agent_messages).lower()

        # 如果包含主观性关键词，认为有观点
        for keyword in viewpoint_keywords:
            if keyword in combined_text:
                return True

        # 检查消息长度，如果经纪人回复很简短，可能只是客观回答
        avg_length = sum(len(msg)
                         for msg in agent_messages) / len(agent_messages)
        if avg_length < 20:  # 平均每条消息少于20字符，可能只是简单回答
            return False

        return True
