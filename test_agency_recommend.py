#!/usr/bin/env python3
"""
AgencyRecommender 交互式命令行测试程序

提供交互式命令行界面来测试 AgencyRecommender 的功能。
支持多种预设对话场景和经纪人配置，帮助验证推荐算法的准确性。
"""

from util import config, logger
from util.types import AgencyRecommendRequest, AgentResponse, ChatMessage, ChatRole, AgencyInfo, AgencyTone
from agent.agency_recommender import AgencyRecommender
import asyncio
import logging
import sys
from pathlib import Path
from typing import List, Optional

# 尝试导入 colorama，如果没有则使用空的颜色代码
try:
    import colorama
    from colorama import Fore, Back, Style
    colorama.init()
    HAS_COLORAMA = True
except ImportError:
    # 如果没有 colorama，定义空的颜色代码
    class _DummyColor:
        def __getattr__(self, _name):
            return ""

    Fore = _DummyColor()
    Back = _DummyColor()
    Style = _DummyColor()
    HAS_COLORAMA = False

try:
    import readline  # 启用命令行历史和编辑功能
    readline.set_startup_hook(None)  # 使用 readline 以避免未使用警告
except ImportError:
    pass  # readline 在某些系统上可能不可用

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))


class ColoredFormatter(logging.Formatter):
    """彩色日志格式化器"""

    def format(self, record):
        if not HAS_COLORAMA:
            return super().format(record)

        color_map = {
            'DEBUG': Fore.CYAN,
            'INFO': Fore.GREEN,
            'WARNING': Fore.YELLOW,
            'ERROR': Fore.RED,
            'CRITICAL': Fore.RED + Back.WHITE
        }

        color = color_map.get(record.levelname, '')
        record.levelname = f"{color}{record.levelname}{Style.RESET_ALL}"
        return super().format(record)


class AgencyRecommendTester:
    """经纪人推荐测试器"""

    def __init__(self):
        self.recommender: Optional[AgencyRecommender] = None
        self.current_user_id = 1
        self.current_agency_id = 1
        self.current_agencies: List[AgencyInfo] = []
        self.current_history: List[ChatMessage] = []

    async def setup(self):
        """初始化测试环境"""
        try:
            # 创建经纪人推荐器
            self.recommender = AgencyRecommender()
            print(f"{Fore.GREEN}✅ AgencyRecommender 初始化成功{Style.RESET_ALL}")

            # 初始化默认经纪人列表
            self.current_agencies = [
                {
                    "agency_id": 1,
                    "name": "张经理",
                    "tone": AgencyTone.FRIENDLY,
                    "experience_years": 3
                },
                {
                    "agency_id": 2,
                    "name": "李专家",
                    "tone": AgencyTone.PROFESSIONAL,
                    "experience_years": 8
                },
                {
                    "agency_id": 3,
                    "name": "王顾问",
                    "tone": AgencyTone.CONSULTATIVE,
                    "experience_years": 12
                },
                {
                    "agency_id": 4,
                    "name": "赵助理",
                    "tone": AgencyTone.ENTHUSIASTIC,
                    "experience_years": 2
                },
                {
                    "agency_id": 5,
                    "name": "陈老师",
                    "tone": AgencyTone.TRUSTWORTHY,
                    "experience_years": 15
                }
            ]

            print(
                f"{Fore.GREEN}✅ 默认经纪人列表初始化完成（{len(self.current_agencies)} 个经纪人）{Style.RESET_ALL}")

        except Exception as e:
            print(f"{Fore.RED}❌ 初始化失败: {e}{Style.RESET_ALL}")
            raise

    def print_banner(self):
        """打印程序横幅"""
        banner = f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════════╗
║                    经纪人推荐测试程序                        ║
║                  Agency Recommend Tester                     ║
╚══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}

{Fore.GREEN}🎯 功能: 测试基于对话分析的智能经纪人推荐{Style.RESET_ALL}
{Fore.YELLOW}💡 提示: 输入 'help' 查看可用命令{Style.RESET_ALL}
"""
        print(banner)

    def print_help(self):
        """打印帮助信息"""
        help_text = f"""
{Fore.CYAN}═══════════════════════════════════════════════════════════════{Style.RESET_ALL}
{Fore.YELLOW}                           帮助信息{Style.RESET_ALL}
{Fore.CYAN}═══════════════════════════════════════════════════════════════{Style.RESET_ALL}

{Fore.YELLOW}基本命令:{Style.RESET_ALL}
  help                    - 显示此帮助信息
  status                  - 显示当前状态
  quit/exit               - 退出程序

{Fore.YELLOW}推荐命令:{Style.RESET_ALL}
  recommend               - 基于当前对话历史获取经纪人推荐
  scenario <name>         - 加载预设对话场景
  current <id>            - 设置当前经纪人ID
  agencies                - 显示所有经纪人信息

{Fore.YELLOW}对话管理:{Style.RESET_ALL}
  history                 - 显示当前对话历史
  add <role> <content>    - 添加对话消息
  clear                   - 清空对话历史

{Fore.YELLOW}预设场景:{Style.RESET_ALL}
  professional_need       - 用户需要专业性强的经纪人
  friendly_preference     - 用户偏好友善亲和的经纪人
  efficiency_focused      - 用户注重效率和快速决策
  trust_building          - 用户需要建立信任关系
  consultation_heavy      - 用户需要详细咨询和解释
  conversation_ended      - 对话已结束的场景（测试对话结束检测）

{Fore.YELLOW}示例:{Style.RESET_ALL}
  scenario professional_need
  recommend
  current 2
  recommend
  add user 我觉得你的回答不够专业
  recommend

{Fore.GREEN}💡 提示: 推荐算法会分析对话内容和用户偏好{Style.RESET_ALL}
{Fore.GREEN}🔍 新功能: 智能检测对话结束状态，优化推荐流程{Style.RESET_ALL}
{Fore.GREEN}🚀 优化: 简化工作流，实现并行分析，提升处理效率{Style.RESET_ALL}
"""
        print(help_text)

    def print_response(self, response: AgentResponse):
        """美化打印响应结果"""
        response_type = response.get("type", "unknown")

        if response_type == "thinking":
            content = response.get("content", "")
            step = response.get("step", "")

            # 为不同的步骤使用不同的图标
            step_icons = {
                "check_conversation_end": "🔍",
                "handle_conversation_end": "✋",
                "start_parallel_analysis": "🚀",
                "generate_recommendation": "💡",
                "generate_question_recommendations": "❓",
                "analyze_viewpoints": "🔍"
            }

            icon = step_icons.get(step, "🤔")
            print(f"{Fore.BLUE}{icon} {content}{Style.RESET_ALL}")
            if step:
                print(f"{Fore.CYAN}   步骤: {step}{Style.RESET_ALL}")

        elif response_type == "agency_recommend":
            current_id = response.get("current_agency_id", 0)
            recommended_id = response.get("recommended_agency_id", 0)
            should_switch = response.get("should_switch", False)
            confidence = response.get("confidence_score", 0.0)
            reason = response.get("recommendation_reason", "")
            user_analysis = response.get("user_preference_analysis", "")
            comm_analysis = response.get("communication_effectiveness", "")

            # 获取经纪人信息
            current_agency = next(
                (a for a in self.current_agencies if a["agency_id"] == current_id), None)
            recommended_agency = next(
                (a for a in self.current_agencies if a["agency_id"] == recommended_id), None)

            print(f"\n{Fore.GREEN}🎯 推荐结果{Style.RESET_ALL}")
            print(
                f"   当前经纪人: {Fore.YELLOW}{current_agency['name'] if current_agency else '未知'} (ID: {current_id}){Style.RESET_ALL}")
            print(
                f"   推荐经纪人: {Fore.YELLOW}{recommended_agency['name'] if recommended_agency else '未知'} (ID: {recommended_id}){Style.RESET_ALL}")
            print(
                f"   是否建议切换: {Fore.GREEN if should_switch else Fore.RED}{'是' if should_switch else '否'}{Style.RESET_ALL}")
            print(f"   推荐置信度: {Fore.CYAN}{confidence:.1%}{Style.RESET_ALL}")

            if reason:
                print(f"\n{Fore.CYAN}📝 推荐理由:{Style.RESET_ALL}")
                print(f"   {reason}")

            if user_analysis:
                print(f"\n{Fore.CYAN}👤 用户偏好分析:{Style.RESET_ALL}")
                print(f"   {user_analysis}")

            if comm_analysis:
                print(f"\n{Fore.CYAN}📊 沟通效果评估:{Style.RESET_ALL}")
                print(f"   {comm_analysis}")

        elif response_type == "question_recommend":
            questions = response.get("questions", [])
            analysis_reason = response.get("analysis_reason", "")
            conversation_stage = response.get("conversation_stage", "")
            priority_level = response.get("priority_level", "")

            print(f"\n{Fore.GREEN}❓ 推荐问题{Style.RESET_ALL}")
            print(
                f"   对话阶段: {Fore.YELLOW}{conversation_stage}{Style.RESET_ALL}")
            print(f"   优先级: {Fore.YELLOW}{priority_level}{Style.RESET_ALL}")

            if questions:
                print(f"\n{Fore.CYAN}💡 建议询问的问题:{Style.RESET_ALL}")
                for i, question in enumerate(questions, 1):
                    print(f"   {i}. {question}")

            if analysis_reason:
                print(f"\n{Fore.CYAN}📝 推荐理由:{Style.RESET_ALL}")
                print(f"   {analysis_reason}")

        elif response_type == "viewpoint_analysis":
            agent_viewpoints = response.get("agent_viewpoints", [])
            overall_assessment = response.get("overall_assessment", "")
            risk_warnings = response.get("risk_warnings", [])
            suggestions = response.get("suggestions", [])

            print(f"\n{Fore.GREEN}🔍 观点分析{Style.RESET_ALL}")

            if overall_assessment:
                print(f"\n{Fore.CYAN}📊 整体评估:{Style.RESET_ALL}")
                print(f"   {overall_assessment}")

            if agent_viewpoints:
                print(f"\n{Fore.CYAN}💭 经纪人观点分析:{Style.RESET_ALL}")
                for i, viewpoint in enumerate(agent_viewpoints, 1):
                    content = viewpoint.get("viewpoint_content", "")
                    accuracy = viewpoint.get("accuracy_assessment", "")
                    objectivity = viewpoint.get("objectivity_assessment", "")
                    risk_level = viewpoint.get("risk_level", "")
                    analysis = viewpoint.get("analysis_detail", "")

                    print(f"   {i}. 观点: {content}")
                    print(
                        f"      准确性: {Fore.YELLOW}{accuracy}{Style.RESET_ALL}")
                    print(
                        f"      客观性: {Fore.YELLOW}{objectivity}{Style.RESET_ALL}")
                    print(
                        f"      风险级别: {Fore.YELLOW}{risk_level}{Style.RESET_ALL}")
                    if analysis:
                        print(f"      分析: {analysis}")

            if risk_warnings:
                print(f"\n{Fore.RED}⚠️  风险提醒:{Style.RESET_ALL}")
                for warning in risk_warnings:
                    print(f"   • {warning}")

            if suggestions:
                print(f"\n{Fore.GREEN}💡 建议:{Style.RESET_ALL}")
                for suggestion in suggestions:
                    print(f"   • {suggestion}")

        elif response_type == "answer":
            content = response.get("content", "")
            print(f"\n{Fore.GREEN}💬 最终建议:{Style.RESET_ALL}")
            print(f"   {content}")

        elif response_type == "error":
            error = response.get("error", "未知错误")
            details = response.get("details", "")
            print(f"{Fore.RED}❌ 错误: {error}{Style.RESET_ALL}")
            if details:
                print(f"{Fore.RED}   详情: {details}{Style.RESET_ALL}")

        else:
            print(f"{Fore.MAGENTA}📄 响应类型: {response_type}{Style.RESET_ALL}")
            content = response.get("content", response.get("message", ""))
            if content:
                print(f"   {content}")

    def print_current_agencies(self):
        """打印当前经纪人列表"""
        if not self.current_agencies:
            print(f"{Fore.YELLOW}⚠️  当前经纪人列表为空{Style.RESET_ALL}")
            return

        print(f"{Fore.CYAN}👥 经纪人列表:{Style.RESET_ALL}")
        for agency in self.current_agencies:
            is_current = agency["agency_id"] == self.current_agency_id
            marker = f"{Fore.GREEN}[当前]{Style.RESET_ALL}" if is_current else "     "
            print(f"  {marker} ID: {Fore.YELLOW}{agency['agency_id']}{Style.RESET_ALL} | "
                  f"姓名: {Fore.WHITE}{agency['name']}{Style.RESET_ALL} | "
                  f"风格: {Fore.CYAN}{agency['tone'].value}{Style.RESET_ALL} | "
                  f"经验: {Fore.MAGENTA}{agency['experience_years']}年{Style.RESET_ALL}")

    def print_current_history(self):
        """打印当前对话历史"""
        if not self.current_history:
            print(f"{Fore.YELLOW}⚠️  当前对话历史为空{Style.RESET_ALL}")
            return

        print(f"{Fore.CYAN}💬 对话历史 ({len(self.current_history)} 条消息):{Style.RESET_ALL}")
        for i, msg in enumerate(self.current_history, 1):
            role_color = Fore.GREEN if msg["role"] == ChatRole.USER else Fore.BLUE
            role_name = "用户" if msg["role"] == ChatRole.USER else "经纪人"
            print(
                f"  {i:2d}. {role_color}{role_name}:{Style.RESET_ALL} {msg['content']}")

    def print_status(self):
        """打印当前状态"""
        current_agency = next(
            (a for a in self.current_agencies if a["agency_id"] == self.current_agency_id), None)

        print(f"{Fore.CYAN}📊 当前状态:{Style.RESET_ALL}")
        print(f"  用户ID: {Fore.YELLOW}{self.current_user_id}{Style.RESET_ALL}")
        print(
            f"  当前经纪人: {Fore.YELLOW}{current_agency['name'] if current_agency else '未知'} (ID: {self.current_agency_id}){Style.RESET_ALL}")
        print(
            f"  经纪人总数: {Fore.YELLOW}{len(self.current_agencies)}{Style.RESET_ALL}")
        print(
            f"  对话消息数: {Fore.YELLOW}{len(self.current_history)}{Style.RESET_ALL}")
        print()
        self.print_current_agencies()
        print()
        self.print_current_history()

    def load_preset_scenario(self, scenario_name: str) -> bool:
        """加载预设对话场景"""
        scenarios = {
            "professional_need": {
                "name": "用户需要专业性强的经纪人",
                "current_agency_id": 1,  # 友善型经纪人
                "history": [
                    {"role": ChatRole.USER, "content": "你好，我想了解一下保险产品，我比较注重专业性和数据分析。"},
                    {"role": ChatRole.ASSISTANT,
                        "content": "您好！我是张经理，很高兴为您服务。根据您的需求，我建议您考虑以下几种保险产品..."},
                    {"role": ChatRole.USER, "content": "能否提供一些具体的数据和对比分析？我需要详细的信息来做决策。"},
                    {"role": ChatRole.ASSISTANT,
                        "content": "当然可以！让我为您详细介绍一下各个产品的保障范围和费率情况..."},
                    {"role": ChatRole.USER, "content": "我觉得你的回答还不够专业，能否更加深入一些？"}
                ]
            },
            "friendly_preference": {
                "name": "用户偏好友善亲和的经纪人",
                "current_agency_id": 2,  # 专业型经纪人
                "history": [
                    {"role": ChatRole.USER, "content": "我想买保险，但是对这方面不太懂，希望能有人耐心地给我解释。"},
                    {"role": ChatRole.ASSISTANT,
                        "content": "根据您的年龄和收入状况，建议配置重疾险、医疗险和寿险。重疾险保额建议年收入的3-5倍..."},
                    {"role": ChatRole.USER, "content": "你说的太专业了，我听不太懂，能不能用简单一点的话解释？"},
                    {"role": ChatRole.ASSISTANT,
                        "content": "从风险管理角度分析，您的保障缺口主要体现在疾病风险和身故风险两个维度..."},
                    {"role": ChatRole.USER, "content": "我觉得你说话太正式了，能不能像朋友一样聊天？"}
                ]
            },
            "efficiency_focused": {
                "name": "用户注重效率和快速决策",
                "current_agency_id": 5,  # 可靠型经纪人
                "history": [
                    {"role": ChatRole.USER, "content": "我时间比较紧，想快速了解适合我的保险产品。"},
                    {"role": ChatRole.ASSISTANT,
                        "content": "我理解您的时间宝贵。让我先详细了解一下您的家庭情况和财务状况，这样才能为您推荐最合适的产品..."},
                    {"role": ChatRole.USER, "content": "能不能直接推荐几个产品？我可以自己研究细节。"},
                    {"role": ChatRole.ASSISTANT,
                        "content": "为了确保推荐的准确性，我们需要充分了解您的需求。请您耐心回答几个问题..."},
                    {"role": ChatRole.USER, "content": "你们的流程太复杂了，我需要更高效的服务。"}
                ]
            },
            "trust_building": {
                "name": "用户需要建立信任关系",
                "current_agency_id": 4,  # 热情型经纪人
                "history": [
                    {"role": ChatRole.USER, "content": "我之前买保险被坑过，现在对保险销售很不信任。"},
                    {"role": ChatRole.ASSISTANT,
                        "content": "太好了！您来对地方了！我们的产品绝对是市场上最好的，保证让您满意！"},
                    {"role": ChatRole.USER, "content": "你这样说我更不放心了，能不能客观一点介绍？"},
                    {"role": ChatRole.ASSISTANT,
                        "content": "没问题！我们的产品有很多优势，比如保费低、保障全、理赔快..."},
                    {"role": ChatRole.USER, "content": "我需要看到更多证据和客观的分析，而不是销售话术。"}
                ]
            },
            "consultation_heavy": {
                "name": "用户需要详细咨询和解释",
                "current_agency_id": 2,  # 专业型经纪人
                "history": [
                    {"role": ChatRole.USER, "content": "我是保险小白，希望能详细了解保险的基本概念和原理。"},
                    {"role": ChatRole.ASSISTANT,
                        "content": "保险是风险转移工具，通过缴纳保费获得保障。主要分为人身险和财产险两大类..."},
                    {"role": ChatRole.USER, "content": "什么是保险责任？什么是免责条款？这些我都不太明白。"},
                    {"role": ChatRole.ASSISTANT,
                        "content": "保险责任是指保险公司承担的赔偿或给付责任。免责条款是保险公司不承担责任的情况..."},
                    {"role": ChatRole.USER, "content": "能不能更详细地解释一下，最好举一些具体的例子？"}
                ]
            },
            "conversation_ended": {
                "name": "对话已结束的场景（测试对话结束检测）",
                "current_agency_id": 1,  # 友善型经纪人
                "history": [
                    {"role": ChatRole.USER, "content": "我想了解一下重疾险的相关信息。"},
                    {"role": ChatRole.ASSISTANT,
                        "content": "好的，重疾险是保障重大疾病的保险产品。主要保障恶性肿瘤、急性心肌梗塞、脑中风后遗症等重大疾病..."},
                    {"role": ChatRole.USER, "content": "保费大概是多少？"},
                    {"role": ChatRole.ASSISTANT,
                        "content": "保费会根据您的年龄、性别、保额等因素确定。一般来说，30岁男性，50万保额，年保费大约在5000-8000元..."},
                    {"role": ChatRole.USER, "content": "好的，我了解了。谢谢你的详细介绍，我回去考虑一下。"},
                    {"role": ChatRole.ASSISTANT,
                        "content": "不客气！如果您还有任何问题，随时可以联系我。祝您生活愉快！"}
                ]
            }
        }

        if scenario_name not in scenarios:
            available = ", ".join(scenarios.keys())
            print(f"{Fore.RED}❌ 未知场景: {scenario_name}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}可用场景: {available}{Style.RESET_ALL}")
            return False

        scenario = scenarios[scenario_name]
        self.current_agency_id = scenario["current_agency_id"]
        self.current_history = scenario["history"].copy()

        print(f"{Fore.GREEN}✅ 已加载预设场景: {scenario['name']}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}📝 场景包含 {len(self.current_history)} 条对话消息{Style.RESET_ALL}")
        print(f"{Fore.CYAN}👤 当前经纪人ID: {self.current_agency_id}{Style.RESET_ALL}")

        return True

    def add_message(self, role: str, content: str) -> bool:
        """添加对话消息"""
        try:
            if role.lower() == "user":
                chat_role = ChatRole.USER
            elif role.lower() in ["assistant", "agent", "经纪人"]:
                chat_role = ChatRole.ASSISTANT
            else:
                print(
                    f"{Fore.RED}❌ 无效的角色: {role}，请使用 'user' 或 'assistant'{Style.RESET_ALL}")
                return False

            message: ChatMessage = {
                "role": chat_role,
                "content": content
            }

            self.current_history.append(message)
            print(
                f"{Fore.GREEN}✅ 已添加消息: {role} -> {content[:50]}{'...' if len(content) > 50 else ''}{Style.RESET_ALL}")
            return True

        except Exception as e:
            print(f"{Fore.RED}❌ 添加消息失败: {e}{Style.RESET_ALL}")
            return False

    def set_current_agency(self, agency_id: int) -> bool:
        """设置当前经纪人"""
        agency = next(
            (a for a in self.current_agencies if a["agency_id"] == agency_id), None)
        if not agency:
            print(f"{Fore.RED}❌ 经纪人ID {agency_id} 不存在{Style.RESET_ALL}")
            return False

        self.current_agency_id = agency_id
        print(
            f"{Fore.GREEN}✅ 已切换到经纪人: {agency['name']} (ID: {agency_id}){Style.RESET_ALL}")
        return True

    def clear_history(self):
        """清空对话历史"""
        self.current_history.clear()
        print(f"{Fore.GREEN}✅ 对话历史已清空{Style.RESET_ALL}")

    async def get_agency_recommendation(self):
        """获取经纪人推荐"""
        if not self.current_history:
            print(f"{Fore.YELLOW}⚠️  请先加载预设场景或添加对话历史{Style.RESET_ALL}")
            return

        if not self.recommender:
            print(f"{Fore.RED}❌ 推荐器未初始化{Style.RESET_ALL}")
            return

        try:
            # 创建推荐请求
            request: AgencyRecommendRequest = {
                "user_id": self.current_user_id,
                "history_chats": self.current_history,
                "agency_id": self.current_agency_id,
                "agencies": self.current_agencies
            }

            print(f"{Fore.BLUE}🔍 正在分析对话并推荐经纪人...{Style.RESET_ALL}")

            # 执行推荐
            async for response in self.recommender.recommend_agency(request):
                self.print_response(response)

        except Exception as e:
            print(f"{Fore.RED}❌ 推荐过程中发生错误: {e}{Style.RESET_ALL}")
            import traceback
            traceback.print_exc()

    async def interactive_loop(self):
        """交互式主循环"""
        try:
            while True:
                try:
                    user_input = input(
                        f"{Fore.WHITE}> {Style.RESET_ALL}").strip()

                    if not user_input:
                        continue

                    # 解析命令
                    parts = user_input.split()
                    command = parts[0].lower()

                    if command in ["quit", "exit", "q"]:
                        print(f"{Fore.YELLOW}👋 再见！{Style.RESET_ALL}")
                        break

                    elif command == "help":
                        self.print_help()

                    elif command == "status":
                        self.print_status()

                    elif command == "recommend":
                        await self.get_agency_recommendation()

                    elif command == "scenario":
                        if len(parts) < 2:
                            print(f"{Fore.RED}❌ 请指定场景名称{Style.RESET_ALL}")
                            continue
                        self.load_preset_scenario(parts[1])

                    elif command == "current":
                        if len(parts) < 2:
                            print(f"{Fore.RED}❌ 请指定经纪人ID{Style.RESET_ALL}")
                            continue
                        try:
                            agency_id = int(parts[1])
                            self.set_current_agency(agency_id)
                        except ValueError:
                            print(f"{Fore.RED}❌ 经纪人ID必须是数字{Style.RESET_ALL}")

                    elif command == "agencies":
                        self.print_current_agencies()

                    elif command == "history":
                        self.print_current_history()

                    elif command == "add":
                        if len(parts) < 3:
                            print(
                                f"{Fore.RED}❌ 用法: add <role> <content>{Style.RESET_ALL}")
                            continue
                        role = parts[1]
                        content = " ".join(parts[2:])
                        self.add_message(role, content)

                    elif command == "clear":
                        self.clear_history()

                    else:
                        print(f"{Fore.RED}❌ 未知命令: {command}{Style.RESET_ALL}")
                        print(f"{Fore.YELLOW}💡 输入 'help' 查看可用命令{Style.RESET_ALL}")

                except KeyboardInterrupt:
                    print(f"\n{Fore.YELLOW}👋 再见！{Style.RESET_ALL}")
                    break
                except EOFError:
                    print(f"\n{Fore.YELLOW}👋 再见！{Style.RESET_ALL}")
                    break
                except Exception as e:
                    print(f"{Fore.RED}❌ 处理命令时发生错误: {e}{Style.RESET_ALL}")

        except Exception as e:
            print(f"{Fore.RED}❌ 交互循环发生错误: {e}{Style.RESET_ALL}")
            import traceback
            traceback.print_exc()


async def main():
    """主函数"""
    # 设置日志
    if HAS_COLORAMA:
        handler = logging.StreamHandler()
        handler.setFormatter(ColoredFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logger.handlers.clear()
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    # 检查配置
    try:
        config.validate()
    except Exception as e:
        print(f"{Fore.RED}❌ 配置验证失败: {e}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}💡 请检查环境变量配置，特别是:{Style.RESET_ALL}")
        print("  AI_INSUR_OPENAI_API_KEY=your_api_key_here")
        return

    # 创建测试器
    tester = AgencyRecommendTester()

    try:
        # 初始化
        await tester.setup()

        # 显示横幅
        tester.print_banner()

        # 进入交互循环
        await tester.interactive_loop()

    except Exception as e:
        print(f"{Fore.RED}❌ 程序运行出错: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
