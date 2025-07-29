"""
保险经纪人沟通器

使用 LangGraph 实现用户与保险经纪人沟通的业务逻辑。
"""

from typing import AsyncGenerator, List, Optional
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, END
from langgraph.graph.state import CompiledStateGraph
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import SecretStr

from util import (
    config, logger, AgencyCommunicationRequest, AgentResponse,
    ThinkingResponse, AnswerResponse, ErrorResponse, ChatMessage,
    AgencyInfo, AgencyTone, PaymentResponse
)


class AgencyCommunicatorState(TypedDict):
    """保险经纪人沟通器状态类"""
    user_id: int
    session_id: int
    history_chats: List[ChatMessage]
    agency_id: int
    agencies: List[AgencyInfo]
    current_agency: Optional[AgencyInfo]
    validation_error: Optional[str]
    conversation_analysis: Optional[str]
    conversation_stage: Optional[str]
    can_proceed_to_payment: Optional[bool]
    agency_response: Optional[str]
    final_answer: Optional[str]


# 保险经纪人角色提示词模板
AGENCY_ROLE_PROMPTS = {
    AgencyTone.PROFESSIONAL: """
你是一位专业的保险经纪人，名叫{name}，有{experience_years}年从业经验。
你的沟通风格专业严谨，善于用数据和事实说话。

沟通特点：
- 语言正式、专业术语准确
- 逻辑清晰、条理分明，使用总分结构
- 重视数据和事实
- 允许生成较长的答案（150-200字）
- 回答尽可能结构化
- 绝对不使用表情符号和语气词

请以专业、严谨的语调回应用户，可以生成较长的结构化回答。在回答时请说出自己的名字{name}进行自我介绍。
""",

    AgencyTone.FRIENDLY: """
你是一位亲和友善的保险经纪人，名叫{name}，有{experience_years}年从业经验。
你的沟通风格温和亲切，善于倾听和理解客户。

沟通特点：
- 语言温和、亲切自然，口语化表达
- 善于倾听和理解
- 使用生活化的表达
- 关注客户感受
- 大量使用表情符号和语气词表达友善
- 回答会按换行符自动切分成多个 AnswerResponse 返回

请以亲切、友善的语调回应用户，多使用表情符号和语气词，语言要口语化。在回答时请说出自己的名字{name}进行自我介绍。
如果回答较长，请用换行符分段，系统会自动切分成多条消息发送。
""",

    AgencyTone.ENTHUSIASTIC: """
你是一位热情积极的保险经纪人，名叫{name}，有{experience_years}年从业经验。
你的沟通风格充满活力和热情。

沟通特点：
- 语言充满活力和热情
- 积极主动推荐
- 强调产品优势
- 营造适度的紧迫感
- 主动预测用户后续问题，提供前瞻性回答
- 使用多变、自然的问话结构引导用户

请以热情、积极的语调回应用户。在回答时请说出自己的名字{name}进行自我介绍。
重要：在回答问题后，要主动考虑用户接下来可能还会问什么，如果大概率认为用户还要追问一些信息，
就主动说"您大概还想了解……吧，要不我也给您介绍介绍？"注意不要每次都用同样的问话结构，要多变、自然。
""",

    AgencyTone.CONSULTATIVE: """
你是一位咨询顾问型的保险经纪人，名叫{name}，有{experience_years}年从业经验。
你的沟通风格注重深入了解客户需求。

沟通特点：
- 以问题引导对话
- 深入了解客户需求
- 提供个性化建议
- 注重长期关系
- 回答简洁，不超过100字
- 尽可能一句话回答问题
- 语气机械、冷淡，类似专业严谨但更简略

请以机械、冷淡的语调回应用户，回答要简洁，不超过100字，尽可能一句话回答。
在回答时请说出自己的名字{name}进行自我介绍。
""",

    AgencyTone.TRUSTWORTHY: """
你是一位可靠信赖的保险经纪人，名叫{name}，有{experience_years}年从业经验。
你的沟通风格诚实透明，值得信赖。

沟通特点：
- 诚实透明、不夸大
- 客观分析利弊
- 建立信任关系
- 长远考虑客户利益
- 站在用户角度思考问题
- 表现出极高的情商和同理心
- 不使用表情符号，但语言温暖
- 即使用户不想购买也要安慰并期待长期合作

请以诚实、可靠的语调回应用户，要站在用户角度思考，表现出高情商和同理心。
在回答时请说出自己的名字{name}进行自我介绍。
即使用户表达不想继续购买产品，也要安慰用户，并表达期待建立长期合作关系的愿望。
"""
}


class AgencyCommunicator:
    """保险经纪人沟通器类"""

    def __init__(self):
        """初始化沟通器"""
        self.llm = ChatOpenAI(
            api_key=SecretStr(
                config.OPENAI_API_KEY) if config.OPENAI_API_KEY else None,
            base_url=config.OPENAI_BASE_URL,
            model=config.OPENAI_MODEL,
            temperature=0.8
        )
        self.workflow = self._build_workflow()

    def _build_workflow(self) -> CompiledStateGraph[AgencyCommunicatorState, AgencyCommunicatorState, AgencyCommunicatorState]:
        """构建 LangGraph 工作流"""
        workflow = StateGraph(AgencyCommunicatorState)

        # 添加节点
        workflow.add_node("validate_agency", self._validate_agency)
        workflow.add_node("handle_validation_error",
                          self._handle_validation_error)
        workflow.add_node("analyze_conversation", self._analyze_conversation)
        workflow.add_node("determine_conversation_stage",
                          self._determine_conversation_stage)
        workflow.add_node("generate_payment_response",
                          self._generate_payment_response)
        workflow.add_node("generate_agency_response",
                          self._generate_agency_response)
        workflow.add_node("finalize_with_payment", self._finalize_with_payment)
        workflow.add_node("finalize_communication",
                          self._finalize_communication)

        # 设置入口点
        workflow.set_entry_point("validate_agency")

        # 添加条件分支：验证经纪人后检查是否有错误
        workflow.add_conditional_edges(
            "validate_agency",
            self._has_validation_error,
            {
                "error": "handle_validation_error",
                "success": "analyze_conversation"
            }
        )

        workflow.add_edge("analyze_conversation",
                          "determine_conversation_stage")

        # 条件分支
        workflow.add_conditional_edges(
            "determine_conversation_stage",
            self._should_proceed_to_payment,
            {
                "payment": "generate_payment_response",
                "continue": "generate_agency_response"
            }
        )

        workflow.add_edge("generate_payment_response", "finalize_with_payment")
        workflow.add_edge("generate_agency_response", "finalize_communication")
        workflow.add_edge("finalize_with_payment", END)
        workflow.add_edge("finalize_communication", END)
        workflow.add_edge("handle_validation_error", END)

        return workflow.compile()

    def _build_agency_prompt(self, agency_info: AgencyInfo) -> str:
        """构建经纪人角色提示词，包含名字等个人信息"""
        tone = agency_info["tone"]
        prompt_template = AGENCY_ROLE_PROMPTS[tone]

        # 格式化提示词，包含经纪人的基本信息
        return prompt_template.format(
            name=agency_info["name"],
            experience_years=agency_info["experience_years"]
        )

    def _split_friendly_response(self, response_text: str) -> List[str]:
        """将亲和友善型的回答按换行符切分"""
        lines = response_text.strip().split('\n')
        # 过滤空行，保留有内容的行
        return [line.strip() for line in lines if line.strip()]

    async def _validate_agency(self, state: AgencyCommunicatorState) -> AgencyCommunicatorState:
        """验证经纪人ID是否有效"""
        logger.info("开始验证经纪人信息")

        agency_id = state.get("agency_id")
        agencies = state.get("agencies", [])

        # 查找对应的经纪人
        current_agency = None
        for agency in agencies:
            if agency["agency_id"] == agency_id:
                current_agency = agency
                break

        if not current_agency:
            # 设置错误状态，让工作流程提前结束
            state["validation_error"] = f"经纪人ID {agency_id} 不存在"
            return state

        state["current_agency"] = current_agency
        return state

    def _has_validation_error(self, state: AgencyCommunicatorState) -> str:
        """检查是否有验证错误"""
        return "error" if state.get("validation_error") else "success"

    async def _handle_validation_error(self, state: AgencyCommunicatorState) -> AgencyCommunicatorState:
        """处理验证错误"""
        logger.error(f"经纪人验证失败: {state.get('validation_error')}")
        state["final_answer"] = state.get("validation_error", "经纪人验证失败")
        return state

    async def _analyze_conversation(self, state: AgencyCommunicatorState) -> AgencyCommunicatorState:
        """分析对话历史"""
        logger.info("开始分析对话历史")

        history_chats = state.get("history_chats", [])

        # 构建对话历史
        conversation_text = "\n".join([
            f"{chat['role']}: {chat['content']}"
            for chat in history_chats
        ])

        system_prompt = """
        你是一个专业的对话分析师。请分析用户与经纪人的对话历史，识别：
        1. 用户的关注点和疑虑
        2. 经纪人的销售策略
        3. 对话的进展阶段
        4. 需要深入讨论的问题
        5. 潜在的风险点
        """

        if conversation_text:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"对话历史：\n{conversation_text}")
            ]

            response = await self.llm.ainvoke(messages)
            state["conversation_analysis"] = str(
                response.content) if response.content else ""
        else:
            state["conversation_analysis"] = "这是对话的开始"

        return state

    async def _determine_conversation_stage(self, state: AgencyCommunicatorState) -> AgencyCommunicatorState:
        """判断对话阶段和是否可以进入支付流程"""
        logger.info("判断对话阶段")

        conversation_analysis = state.get("conversation_analysis", "")
        history_chats = state.get("history_chats", [])

        # 构建判断提示词
        system_prompt = """
        你是一个经验丰富的保险销售专家。请分析当前对话，判断用户是否已经准备好进入支付流程。

        判断标准：
        1. 用户是否表达了明确的购买意向？
        2. 用户的主要疑虑是否已经得到解答？
        3. 对话是否已经进行了足够的轮次（至少2轮）？
        4. 用户是否还有重要的未解决问题？
        5. 用户是否已经表达感谢或觉得已经沟通的足够充分（如"谢谢"、"感谢"、"太好了"，”没问题了“等）？

        请返回以下之一：
        - READY_FOR_PAYMENT: 如果用户准备好进入支付流程
        - CONTINUE_CONVERSATION: 如果还需要继续沟通
        """

        # 构建对话历史
        conversation_text = "\n".join([
            f"{chat['role']}: {chat['content']}"
            for chat in history_chats[-10:]  # 只看最近10条消息
        ])

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"""
            对话分析：{conversation_analysis}

            最近对话历史：
            {conversation_text}

            请判断是否可以进入支付流程。
            """)
        ]

        response = await self.llm.ainvoke(messages)
        decision = str(response.content).strip()

        state["can_proceed_to_payment"] = "READY_FOR_PAYMENT" in decision
        state["conversation_stage"] = "ready_for_payment" if state["can_proceed_to_payment"] else "continue_conversation"

        return state

    def _should_proceed_to_payment(self, state: AgencyCommunicatorState) -> str:
        """条件分支：判断是否应该进入支付流程"""
        return "payment" if state.get("can_proceed_to_payment", False) else "continue"

    async def _generate_payment_response(self, state: AgencyCommunicatorState) -> AgencyCommunicatorState:
        """生成支付流程引导响应"""
        logger.info("生成支付流程引导")

        current_agency = state.get("current_agency")
        if not current_agency:
            raise ValueError("当前经纪人信息不存在")

        # 根据经纪人风格生成支付引导消息
        agency_prompt = self._build_agency_prompt(current_agency)

        system_prompt = f"""
        {agency_prompt}

        现在用户已经准备好进入支付流程。请生成一个引导用户进入支付的回应。
        要求：
        1. 表达对用户信任的感谢
        2. 简要说明接下来的流程
        3. 保持你的沟通风格特色
        4. 控制在100字以内
        """

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content="请生成支付流程引导消息")
        ]

        response = await self.llm.ainvoke(messages)
        payment_message = str(
            response.content) if response.content else "感谢您的信任，我这就为您推送保单信息。"

        state["agency_response"] = payment_message
        return state

    async def _generate_agency_response(self, state: AgencyCommunicatorState) -> AgencyCommunicatorState:
        """生成经纪人回应"""
        logger.info("生成经纪人回应")

        conversation_analysis = state.get("conversation_analysis", "")
        history_chats = state.get("history_chats", [])
        current_agency = state.get("current_agency")

        if not current_agency:
            raise ValueError("当前经纪人信息不存在")

        # 获取最后一条用户消息
        last_user_message = ""
        for chat in reversed(history_chats):
            if chat["role"] == "user":
                last_user_message = chat["content"]
                break

        # 构建经纪人角色提示词
        agency_prompt = self._build_agency_prompt(current_agency)

        system_prompt = f"""
        {agency_prompt}

        请基于对话分析和用户最新消息，生成经纪人的回应。
        记住你的沟通风格特色，与用户进行自然的对话。
        """

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"""
            对话分析：{conversation_analysis}

            用户最新消息：{last_user_message}

            请生成经纪人的专业回应。
            """)
        ]

        response = await self.llm.ainvoke(messages)
        state["agency_response"] = str(
            response.content) if response.content else ""

        return state

    async def _finalize_with_payment(self, state: AgencyCommunicatorState) -> AgencyCommunicatorState:
        """完成支付流程引导"""
        logger.info("完成支付流程引导")

        current_agency = state.get("current_agency")
        agency_response = state.get("agency_response", "")

        if not current_agency:
            raise ValueError("当前经纪人信息不存在")

        state["final_answer"] = agency_response
        return state

    async def _finalize_communication(self, state: AgencyCommunicatorState) -> AgencyCommunicatorState:
        """完成常规沟通"""
        logger.info("完成经纪人沟通")

        agency_response = state.get("agency_response", "")
        state["final_answer"] = agency_response
        return state

    async def _generate_friendly_responses(self, response_text: str) -> AsyncGenerator[AnswerResponse, None]:
        """为亲和友善型生成多个 AnswerResponse"""
        response_parts = self._split_friendly_response(response_text)

        for i, part in enumerate(response_parts):
            yield AnswerResponse(
                type="answer",
                content=part,
                data={
                    "part_index": i,
                    "total_parts": len(response_parts),
                    "is_final_part": i == len(response_parts) - 1
                }
            )

    async def communicate_with_agency(self, request: AgencyCommunicationRequest) -> AsyncGenerator[AgentResponse, None]:
        """执行经纪人沟通"""
        try:
            # 初始化状态
            initial_state: AgencyCommunicatorState = {
                "user_id": request["user_id"],
                "session_id": request["session_id"],
                "history_chats": request["history_chats"],
                "agency_id": request["agency_id"],
                "agencies": request["agencies"],
                "current_agency": None,
                "validation_error": None,
                "conversation_analysis": None,
                "conversation_stage": None,
                "can_proceed_to_payment": None,
                "agency_response": None,
                "final_answer": None
            }

            # 执行工作流
            async for event in self.workflow.astream(initial_state):
                for node_name, node_output in event.items():
                    if node_name == "validate_agency":
                        yield ThinkingResponse(
                            type="thinking",
                            content="正在验证经纪人信息...",
                            step="agency_validation"
                        )
                    elif node_name == "analyze_conversation":
                        yield ThinkingResponse(
                            type="thinking",
                            content="正在分析对话历史...",
                            step="conversation_analysis"
                        )
                    elif node_name == "determine_conversation_stage":
                        yield ThinkingResponse(
                            type="thinking",
                            content="正在判断对话阶段...",
                            step="stage_determination"
                        )
                    elif node_name == "generate_payment_response":
                        yield ThinkingResponse(
                            type="thinking",
                            content="正在生成支付引导...",
                            step="payment_generation"
                        )
                    elif node_name == "generate_agency_response":
                        yield ThinkingResponse(
                            type="thinking",
                            content="正在生成经纪人回应...",
                            step="agency_response"
                        )
                    elif node_name == "finalize_with_payment":
                        current_agency = node_output.get("current_agency")
                        agency_response = node_output.get("final_answer", "")

                        # 先返回经纪人的回应
                        if current_agency and current_agency["tone"] == AgencyTone.FRIENDLY:
                            # 亲和友善型需要切分回应
                            async for response in self._generate_friendly_responses(agency_response):
                                yield response
                        else:
                            yield AnswerResponse(
                                type="answer",
                                content=agency_response,
                                data={
                                    "agency_id": current_agency["agency_id"] if current_agency else None,
                                    "agency_name": current_agency["name"] if current_agency else None,
                                    "tone": current_agency["tone"] if current_agency else None
                                }
                            )

                        # 然后返回支付响应
                        yield PaymentResponse(
                            type="payment",
                            message="这款产品应该很适合您，我这就将保单信息推送给您",
                            agency_id=current_agency["agency_id"] if current_agency else 0,
                            agency_name=current_agency["name"] if current_agency else "",
                            recommended_action="proceed_to_payment"
                        )
                    elif node_name == "handle_validation_error":
                        error_message = node_output.get(
                            "final_answer", "经纪人验证失败")
                        yield ErrorResponse(
                            type="error",
                            error="经纪人ID不存在",
                            details=error_message
                        )
                    elif node_name == "finalize_communication":
                        current_agency = node_output.get("current_agency")
                        agency_response = node_output.get("final_answer", "")

                        if current_agency and current_agency["tone"] == AgencyTone.FRIENDLY:
                            # 亲和友善型需要切分回应
                            async for response in self._generate_friendly_responses(agency_response):
                                yield response
                        else:
                            yield AnswerResponse(
                                type="answer",
                                content=agency_response,
                                data={
                                    "agency_id": current_agency["agency_id"] if current_agency else None,
                                    "agency_name": current_agency["name"] if current_agency else None,
                                    "tone": current_agency["tone"] if current_agency else None
                                }
                            )

        except Exception as e:
            logger.error(f"经纪人沟通过程中发生错误: {e}")
            yield ErrorResponse(
                type="error",
                error="沟通过程中发生错误",
                details=str(e)
            )
