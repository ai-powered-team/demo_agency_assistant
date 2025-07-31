"""
智能对话助理

使用 LangGraph 实现带有意图识别的保险对话助理业务逻辑。
AI 扮演保险用户，真人扮演保险经纪人，助理提供实时意图识别和建议。
"""

import json
from typing import AsyncGenerator, List, Optional
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, END
from langgraph.graph.state import CompiledStateGraph
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from pydantic import SecretStr

from util import (
    config, logger, AssistantRequest, AssistantResponse,
    IntentAnalysis, IntentAnalysisResponse, UserResponseResponse, SuggestionsResponse,
    ThinkingResponse, AnswerResponse, ErrorResponse,
    ChatMessage, AgentResponse
)
from .rag_pit_detector import get_pit_retriever


class AgencyAssistantState(TypedDict):
    """智能对话助理状态类"""
    user_id: int
    session_id: int
    broker_input: str
    conversation_history: List[ChatMessage]
    intent_analysis: Optional[IntentAnalysis]
    user_response: str
    suggestions: Optional[List[str]]
    error_message: Optional[str]


class AgencyAssistant:
    """智能对话助理类"""

    def __init__(self):
        """初始化助理"""
        # 验证配置
        config.validate_assistant()
        
        # 初始化DeepSeek模型用于对话生成
        self.deepseek = ChatOpenAI(
            api_key=SecretStr(config.DEEPSEEK_API_KEY),
            base_url="https://api.deepseek.com",
            model="deepseek-chat",
            temperature=0.7
        )
        
        # 初始化Qwen模型用于意图识别
        self.qwen = ChatOpenAI(
            api_key=SecretStr(config.QWEN_API_KEY),
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            model="qwen-plus",
            temperature=0.3
        )
        
        # 初始化RAG坑点检索器
        try:
            self.pit_retriever = get_pit_retriever()
            logger.info("RAG坑点检索器初始化成功")
        except Exception as e:
            logger.error(f"RAG坑点检索器初始化失败: {e}")
            self.pit_retriever = None
        
        # 用户角色提示
        self.user_prompt = """你是一个考虑购买保险的普通用户，对保险知识了解有限，关心保费、保障范围、理赔等问题。
你会根据经纪人的回答继续提问，表现出真实用户的疑虑和需求。请自然、口语化地回应，不要过于正式。"""
        
        self.workflow = self._build_workflow()

    def _build_workflow(self) -> CompiledStateGraph[AgencyAssistantState, AgencyAssistantState, AgencyAssistantState]:
        """构建 LangGraph 工作流"""
        workflow = StateGraph(AgencyAssistantState)

        # 添加节点
        workflow.add_node("analyze_intent", self._analyze_intent)
        workflow.add_node("generate_user_response", self._generate_user_response)
        workflow.add_node("generate_suggestions", self._generate_suggestions)
        workflow.add_node("finalize_assistant", self._finalize_assistant)
        workflow.add_node("handle_error", self._handle_error)

        # 设置入口点
        workflow.set_entry_point("analyze_intent")

        # 添加条件分支：检查意图识别是否成功
        workflow.add_conditional_edges(
            "analyze_intent",
            self._has_error,
            {
                "error": "handle_error",
                "success": "generate_suggestions"
            }
        )

        workflow.add_edge("generate_suggestions", "generate_user_response")
        workflow.add_edge("generate_user_response", "finalize_assistant")
        workflow.add_edge("finalize_assistant", END)
        workflow.add_edge("handle_error", END)

        return workflow.compile()

    def _has_error(self, state: AgencyAssistantState) -> str:
        """检查是否有错误"""
        return "error" if state.get("error_message") else "success"

    async def _analyze_intent(self, state: AgencyAssistantState) -> AgencyAssistantState:
        """意图识别节点"""
        logger.info("开始分析经纪人话语意图")

        broker_input = state["broker_input"]
        conversation_history = state.get("conversation_history", [])
        
        # 构建对话上下文（最近5轮对话）
        context_messages = []
        for msg in conversation_history[-10:]:
            role = "经纪人" if msg["role"] == "assistant" else "用户"
            context_messages.append(f"{role}: {msg['content']}")
        
        context = "\n".join(context_messages)

        prompt = f"""分析保险经纪人话语的意图，返回JSON格式：

经纪人当前话语: {broker_input}

对话历史上下文:
{context}

请从以下6个维度分析：
1. 讨论主题：当前讨论的主要保险话题（如"重疾险咨询"、"保费计算"、"理赔流程"等）
2. 涉及术语：提到的保险专业术语列表（如"免赔额"、"等待期"、"保额"等）
3. 涉及产品：提到的具体保险产品类型列表（如"重疾险"、"医疗险"、"寿险"等）
4. 经纪人阶段性意图识别：判断经纪人在销售流程中的当前阶段（如"需求了解"、"产品介绍"、"异议处理"、"促成签单"等）
5. 经纪人本句话意图识别：这句话的具体目的（如"询问需求"、"解释条款"、"推荐产品"、"催促决定"等）
6. 用户当下需求：推测用户此时最关心的问题或需求（如"了解保费"、"确认保障范围"、"担心理赔"等）

严格按照以下JSON格式返回：
{{
    "讨论主题": "具体主题",
    "涉及术语": ["术语1", "术语2"],
    "涉及产品": ["产品1", "产品2"],
    "经纪人阶段性意图识别": "当前阶段",
    "经纪人本句话意图识别": "具体意图",
    "用户当下需求": "推测需求"
}}"""

        try:
            messages = [
                SystemMessage(content="你是一个专业的对话意图分析专家，擅长分析保险销售对话中的意图和需求。"),
                HumanMessage(content=prompt)
            ]
            
            response = await self.qwen.ainvoke(messages)
            response_text = str(response.content).strip()
            
            # 清理可能的markdown格式
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                lines = response_text.split("\n")
                json_lines = []
                in_json = False
                for line in lines:
                    if line.strip().startswith("{") or in_json:
                        in_json = True
                        json_lines.append(line)
                        if line.strip().endswith("}"):
                            break
                response_text = "\n".join(json_lines)
            
            intent_analysis = json.loads(response_text)
            
            # 验证必需字段
            required_fields = ["讨论主题", "涉及术语", "涉及产品", "经纪人阶段性意图识别", "经纪人本句话意图识别", "用户当下需求"]
            for field in required_fields:
                if field not in intent_analysis:
                    intent_analysis[field] = "未识别" if field not in ["涉及术语", "涉及产品"] else []
                    
            state["intent_analysis"] = intent_analysis
            
        except Exception as e:
            logger.error(f"意图识别失败: {e}")
            state["error_message"] = f"意图识别失败: {str(e)}"
            # 设置默认值
            state["intent_analysis"] = {
                "讨论主题": "未识别",
                "涉及术语": [],
                "涉及产品": [],
                "经纪人阶段性意图识别": "未识别",
                "经纪人本句话意图识别": "未识别",
                "用户当下需求": "未识别"
            }

        return state

    def _format_suggestions_for_user_prompt(self, suggestions) -> str:
        """格式化建议用于用户回应生成的prompt"""
        if not suggestions:
            return "- 暂无建议"
        
        # 处理结构化建议格式
        if isinstance(suggestions, dict):
            formatted_suggestions = []
            
            # 提取提醒模块的要点
            reminders = suggestions.get("reminders", {})
            key_points = reminders.get("key_points", [])
            potential_risks = reminders.get("potential_risks", [])
            
            # 提取提问模块的问题（简化为列表）
            questions = suggestions.get("questions", [])
            
            # 组合关键信息点
            if key_points:
                formatted_suggestions.extend([f"关注要点: {point}" for point in key_points[:2]])
            
            # 组合风险提醒
            if potential_risks:
                formatted_suggestions.extend([f"注意风险: {risk}" for risk in potential_risks[:2]])
            
            # 组合提问建议
            if questions:
                formatted_suggestions.extend([f"可以询问: {q}" for q in questions[:2]])
            
            # 如果没有任何建议，返回默认
            if not formatted_suggestions:
                return "- 暂无具体建议"
            
            return chr(10).join([f"- {suggestion}" for suggestion in formatted_suggestions[:5]])
        
        # 处理旧格式（列表）
        elif isinstance(suggestions, list):
            return chr(10).join([f"- {suggestion}" for suggestion in suggestions[:3]])
        
        return "- 建议格式不正确"

    async def _generate_user_response(self, state: AgencyAssistantState) -> AgencyAssistantState:
        """生成AI用户回应节点"""
        logger.info("生成AI用户回应")

        broker_input = state["broker_input"]
        conversation_history = state.get("conversation_history", [])
        intent_analysis = state.get("intent_analysis", {})
        suggestions = state.get("suggestions", [])

        # 构建增强的用户角色提示，包含对话建议
        enhanced_user_prompt = f"""{self.user_prompt}

当前对话分析：
- 讨论主题：{intent_analysis.get('讨论主题', '未知')}
- 经纪人意图：{intent_analysis.get('经纪人本句话意图识别', '未知')}
- 你的当下需求：{intent_analysis.get('用户当下需求', '未知')}

助理建议（供参考，但要自然表达，不要生硬照搬）：
{self._format_suggestions_for_user_prompt(suggestions)}

请根据以上分析和建议，自然地回应经纪人，体现出真实用户的疑虑和需求。"""

        # 构建对话消息列表
        messages = [SystemMessage(content=enhanced_user_prompt)]
        
        # 添加历史对话（最近10轮）
        for msg in conversation_history[-20:]:
            if msg["role"] == "assistant":  # 经纪人消息
                messages.append(HumanMessage(content=f"经纪人: {msg['content']}"))
            else:  # 用户消息
                messages.append(AIMessage(content=msg["content"]))
        
        # 添加当前经纪人输入
        messages.append(HumanMessage(content=f"经纪人: {broker_input}"))

        try:
            response = await self.deepseek.ainvoke(messages)
            user_response = str(response.content).strip()
            
            # 确保回应自然且符合用户角色
            if not user_response:
                user_response = "抱歉，我没听清楚，能再说一遍吗？"
                
            state["user_response"] = user_response
            
        except Exception as e:
            logger.error(f"生成用户回应失败: {e}")
            state["error_message"] = f"生成用户回应失败: {str(e)}"
            state["user_response"] = "抱歉，我需要考虑一下。"

        return state

    async def _generate_suggestions(self, state: AgencyAssistantState) -> AgencyAssistantState:
        """生成助理建议节点 - 集成RAG坑点检索"""
        logger.info("生成助理建议")

        intent_analysis = state.get("intent_analysis", {})
        broker_input = state["broker_input"]
        conversation_history = state.get("conversation_history", [])

        try:
            # 构建对话上下文
            context_messages = []
            for msg in conversation_history[-6:]:  # 最近3轮对话
                role = "经纪人" if msg["role"] == "assistant" else "用户"
                context_messages.append(f"{role}: {msg['content']}")
            context = "\n".join(context_messages)

            # RAG检索相关坑点
            pit_warnings = ""
            if self.pit_retriever:
                try:
                    # 构建检索查询：结合经纪人话语和意图信息
                    search_query = broker_input
                    if intent_analysis:
                        topic = intent_analysis.get("讨论主题", "")
                        keywords = intent_analysis.get("关键词", [])
                        if topic:
                            search_query += f" {topic}"
                        if keywords:
                            search_query += f" {' '.join(keywords)}"
                    
                    # 执行RAG检索 - 使用更宽松的参数
                    pit_results = self.pit_retriever.search(
                        search_query, 
                        top_k=5, 
                        similarity_threshold=0.2  # 更低的阈值
                    )
                    
                    if pit_results:
                        pit_warnings = self.pit_retriever.format_pit_warnings(pit_results)
                        logger.info(f"检索到 {len(pit_results)} 个相关坑点")
                    else:
                        logger.info("未检索到相关坑点")
                        
                except Exception as e:
                    logger.error(f"RAG检索失败: {e}")
                    pit_warnings = ""

            # 构建增强的建议生成prompt
            base_prompt = f"""根据经纪人话语和意图分析，为AI扮演的保险用户提供3-5个实用的对话建议。

经纪人当前话语: {broker_input}

对话历史上下文:
{context}

意图分析结果: {json.dumps(intent_analysis, ensure_ascii=False, indent=2)}"""

            # 如果有坑点警告，添加到prompt中
            if pit_warnings:
                enhanced_prompt = f"""{base_prompt}

⚠️ 相关风险提示 (基于保险行业坑点数据库):
{pit_warnings}

请特别注意上述风险提示，在生成建议时融入相关的风险防范意识。"""
            else:
                enhanced_prompt = base_prompt

            suggestions_prompt = f"""{enhanced_prompt}

请按照以下结构生成针对性的建议，帮助AI用户更好地与经纪人沟通：

## 提醒模块（解读经纪人的话）
1. **信息要点**: 分析经纪人话语中涉及的关键信息点
2. **潜在坑点**: 识别可能存在的风险点或误导性信息

## 提问模块（帮助用户给出下一步提问）
仅基于当前经纪人话语，生成3个不同类型的提问建议：

1. **澄清式提问**: 对模糊表述要求进一步说明
2. **深挖式提问**: 在介绍基础上深入了解细节  
3. **风险揭示提问**: 针对坑点进行直接询问

请返回JSON格式：
{{
  "reminders": {{
    "key_points": ["要点1", "要点2"],
    "potential_risks": ["风险点1", "风险点2"]
  }},
  "questions": ["提问1", "提问2", "提问3"]
}}"""

            messages = [
                SystemMessage(content="""你是保险领域的专业顾问，具备丰富的风险识别经验。你的任务是为AI扮演的保险用户提供结构化的对话建议，帮助用户更好地与保险经纪人沟通。

你需要分析经纪人的话语，识别关键信息点和潜在风险，然后为用户提供不同类型的提问建议。请严格按照JSON格式返回结果。"""),
                HumanMessage(content=suggestions_prompt)
            ]
            
            response = await self.deepseek.ainvoke(messages)
            response_text = str(response.content).strip()
            
            # 解析结构化建议
            try:
                if "```json" in response_text:
                    response_text = response_text.split("```json")[1].split("```")[0].strip()
                suggestions_data = json.loads(response_text)
                
                # 提取提醒模块
                reminders = suggestions_data.get("reminders", {})
                key_points = reminders.get("key_points", [])
                potential_risks = reminders.get("potential_risks", [])
                
                # 提取提问模块（简化为列表）
                questions = suggestions_data.get("questions", [])
                
                # 构建结构化建议
                structured_suggestions = {
                    "reminders": {
                        "key_points": key_points,
                        "potential_risks": potential_risks
                    },
                    "questions": questions
                }
                
                state["suggestions"] = structured_suggestions
                
            except Exception as e:
                logger.error(f"JSON解析失败: {e}")
                # 如果JSON解析失败，生成包含坑点信息的默认结构化建议
                current_topic = intent_analysis.get("讨论主题", "保险咨询")
                
                default_reminders = {
                    "key_points": [
                        f"经纪人提到了{current_topic}相关内容",
                        "需要关注具体的保障条款和费用"
                    ],
                    "potential_risks": []
                }
                
                default_questions = [
                    f"可以详细说明一下{current_topic}的具体内容吗？",
                    "能否介绍一下相关的理赔流程和条件？",
                    "除了这个方案，还有其他类似的选择吗？"
                ]
                
                # 如果有坑点警告，添加到风险提醒中
                if pit_warnings:
                    default_reminders["potential_risks"].append("经纪人话语中可能存在误导性信息")
                    default_questions[2] = "关于刚才提到的内容，有没有什么需要特别注意的风险点？"
                
                state["suggestions"] = {
                    "reminders": default_reminders,
                    "questions": default_questions
                }
            
            # 记录RAG增强信息
            if pit_warnings:
                logger.info("建议生成已融入RAG坑点检索结果")
            
        except Exception as e:
            logger.error(f"生成建议失败: {e}")
            # 设置默认结构化建议
            state["suggestions"] = {
                "reminders": {
                    "key_points": [
                        "经纪人介绍了保险相关内容",
                        "需要仔细了解产品详情"
                    ],
                    "potential_risks": [
                        "可能存在销售误导风险",
                        "需要核实产品信息的真实性"
                    ]
                },
                "questions": [
                    "可以详细说明一下这个产品的核心特点吗？",
                    "能否介绍一下具体的理赔流程和条件？",
                    "这个产品有什么需要特别注意的限制或风险吗？"
                ]
            }

        return state

    async def _finalize_assistant(self, state: AgencyAssistantState) -> AgencyAssistantState:
        """完成助理分析"""
        logger.info("完成智能对话助理分析")
        return state

    async def _handle_error(self, state: AgencyAssistantState) -> AgencyAssistantState:
        """处理错误"""
        logger.error(f"智能对话助理处理错误: {state.get('error_message')}")
        return state

    async def assist_conversation(self, request: AssistantRequest) -> AsyncGenerator[AgentResponse, None]:
        """执行智能对话助理分析"""
        try:
            # 初始化状态
            initial_state: AgencyAssistantState = {
                "user_id": request["user_id"],
                "session_id": request["session_id"],
                "broker_input": request["broker_input"],
                "conversation_history": request["conversation_history"],
                "intent_analysis": None,
                "user_response": "",
                "suggestions": None,
                "error_message": None
            }

            # 执行工作流
            async for event in self.workflow.astream(initial_state):
                for node_name, node_output in event.items():
                    if node_name == "analyze_intent":
                        yield ThinkingResponse(
                            type="thinking",
                            content="正在分析经纪人话语意图...",
                            step="intent_analysis"
                        )
                        
                        # 完成意图分析后立即返回意图分析结果
                        intent_analysis = node_output.get("intent_analysis", {})
                        if intent_analysis:
                            yield IntentAnalysisResponse(
                                type="intent_analysis",
                                intent_analysis=intent_analysis
                            )
                            
                    elif node_name == "generate_suggestions":
                        yield ThinkingResponse(
                            type="thinking",
                            content="正在生成对话建议...",
                            step="suggestions_generation"
                        )
                        
                        # 完成建议生成后立即返回
                        suggestions = node_output.get("suggestions", [])
                        if suggestions:
                            yield SuggestionsResponse(
                                type="suggestions",
                                suggestions=suggestions
                            )
                            
                    elif node_name == "generate_user_response":
                        yield ThinkingResponse(
                            type="thinking",
                            content="正在基于建议生成AI用户回应...",
                            step="user_response_generation"
                        )
                        
                        # 完成用户回应生成后立即返回
                        user_response = node_output.get("user_response", "")
                        if user_response:
                            yield UserResponseResponse(
                                type="user_response",
                                user_response=user_response
                            )
                            
                    elif node_name == "finalize_assistant":
                        # 返回最终完成信号（可选，主要用于标识流程完成）
                        intent_analysis = node_output.get("intent_analysis", {})
                        user_response = node_output.get("user_response", "")
                        suggestions = node_output.get("suggestions", [])
                        
                        yield AssistantResponse(
                            type="assistant",
                            user_response=user_response,
                            intent_analysis=intent_analysis,
                            suggestions=suggestions
                        )
                    elif node_name == "handle_error":
                        error_message = node_output.get("error_message", "处理过程中发生错误")
                        yield ErrorResponse(
                            type="error",
                            error="智能对话助理错误",
                            details=error_message
                        )

        except Exception as e:
            logger.error(f"智能对话助理过程中发生错误: {e}")
            yield ErrorResponse(
                type="error",
                error="助理处理失败",
                details=str(e)
            ) 