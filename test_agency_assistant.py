#!/usr/bin/env python3
"""
AgencyAssistant 交互式命令行测试程序

提供交互式命令行界面来测试智能对话助理功能。
AI 扮演保险用户，真人扮演保险经纪人，系统提供实时意图识别和建议。

使用方法:
    python test_agency_assistant.py

功能特性:
    🤖 AI 扮演保险用户，真人扮演保险经纪人
    🧠 实时进行6个维度的意图识别分析（分步骤显示）
    💡 为AI用户提供对话建议（即时显示）
    📊 显示完整的对话历史和分析结果

常用命令:
    help                    - 显示帮助信息
    broker <message>        - 作为经纪人发言，触发智能分析
    history                 - 查看对话历史
    analysis                - 查看最新意图分析
    suggestions             - 查看最新建议
    user                    - 查看最新AI用户回应
    reset                   - 重置对话会话
    status                  - 显示当前状态
    test_rag                - 测试RAG坑点检索功能
    quit                    - 退出程序

工作流程:
    1. 经纪人发言 -> 2. 意图分析（立即显示）-> 3. 对话建议（立即显示）-> 4. AI用户回应（立即显示）

示例对话:
    > broker 您好，我是您的保险顾问，请问您考虑什么类型的保险？
    # 系统立即显示: 意图分析 → 对话建议 → AI用户回应
    > broker 重疾险是很重要的保障，您了解过吗？
    # 系统再次进行完整分析流程
"""

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any

# 尝试导入 colorama，如果没有则使用空的颜色代码
try:
    import colorama
    from colorama import Fore, Back, Style
    colorama.init()
    HAS_COLORAMA = True
except ImportError:
    # 如果没有 colorama，定义空的颜色代码
    class _DummyColor:
        def __getattr__(self, name):
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

from util import (
    config, logger, AssistantRequest, AgentResponse, ChatMessage, ChatRole, IntentAnalysis,
    IntentAnalysisResponse, UserResponseResponse, SuggestionsResponse
)
from agent.agency_assistant import AgencyAssistant


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


class AgencyAssistantTester:
    """智能对话助理测试器"""

    def __init__(self):
        self.assistant: Optional[AgencyAssistant] = None
        self.current_user_id = 1
        self.current_session_id = 1
        self.conversation_history: List[ChatMessage] = []
        self.latest_intent_analysis: Optional[IntentAnalysis] = None
        self.latest_suggestions: Optional[List[str]] = None
        self.latest_user_response: Optional[str] = None

    async def setup(self):
        """初始化测试环境"""
        try:
            # 验证智能对话助理配置
            config.validate_assistant()
            print(f"{Fore.GREEN}✅ 智能对话助理配置验证成功{Style.RESET_ALL}")

            # 创建智能对话助理实例
            self.assistant = AgencyAssistant()
            print(f"{Fore.GREEN}✅ AgencyAssistant 初始化成功{Style.RESET_ALL}")

        except Exception as e:
            print(f"{Fore.RED}❌ 初始化失败: {e}{Style.RESET_ALL}")
            if "DEEPSEEK_API_KEY" in str(e):
                print(f"{Fore.YELLOW}💡 请设置 AI_INSUR_DEEPSEEK_API_KEY 环境变量{Style.RESET_ALL}")
            if "QWEN_API_KEY" in str(e):
                print(f"{Fore.YELLOW}💡 请设置 AI_INSUR_QWEN_API_KEY 环境变量{Style.RESET_ALL}")
            raise

    async def cleanup(self):
        """清理测试环境"""
        try:
            # 重置对话历史
            self.conversation_history.clear()
            self.latest_intent_analysis = None
            self.latest_suggestions = None
            self.latest_user_response = None
            print(f"{Fore.YELLOW}🧹 已清理会话数据和对话历史{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}❌ 清理失败: {e}{Style.RESET_ALL}")

    def print_banner(self):
        """打印程序横幅"""
        banner = f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════════╗
║                   智能对话助理测试程序                       ║
║                 Agency Assistant Tester                     ║
╚══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}

{Fore.GREEN}🎯 功能: AI扮演保险用户，真人扮演经纪人，分步骤实时显示分析结果{Style.RESET_ALL}
{Fore.YELLOW}💡 提示: 输入 'help' 查看可用命令{Style.RESET_ALL}

{Fore.MAGENTA}🔥 开始对话吧！用 'broker <您的话>' 开始扮演保险经纪人{Style.RESET_ALL}
{Fore.CYAN}📋 工作流程: 经纪人发言 → 意图分析 → 对话建议 → AI用户回应（分步显示）{Style.RESET_ALL}
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

{Fore.YELLOW}对话命令:{Style.RESET_ALL}
  broker <message>        - 作为保险经纪人发言
  history                 - 显示完整对话历史
  clear                   - 清空对话历史
  reset                   - 重置会话（新的session_id）

{Fore.YELLOW}分析查看:{Style.RESET_ALL}
  analysis                - 查看最新的意图识别结果
  suggestions             - 查看最新的对话建议
  user                    - 查看最新的AI用户回应

{Fore.YELLOW}意图识别维度:{Style.RESET_ALL}
  1. 讨论主题识别        - 当前讨论的主要保险话题
  2. 涉及术语提取        - 提到的保险专业术语
  3. 涉及产品分析        - 提到的具体保险产品类型
  4. 经纪人阶段性意图    - 销售流程中的当前阶段
  5. 经纪人本句话意图    - 这句话的具体目的
  6. 用户当下需求        - 推测的用户需求

{Fore.YELLOW}示例对话:{Style.RESET_ALL}
  broker 您好，我是您的保险顾问，请问您考虑什么类型的保险？
  # 系统自动显示: 🧠意图分析 → 💡对话建议 → 🤖AI用户回应
  
  broker 重疾险是很重要的保障，您了解过吗？
  # 系统再次完整分析并分步显示结果
  
  analysis                # 可随时查看最新意图分析
  user                    # 可随时查看最新AI用户回应
  suggestions             # 可随时查看最新对话建议

{Fore.GREEN}💡 提示: 每次启动都会重置所有数据，确保测试独立性{Style.RESET_ALL}
{Fore.CYAN}🚀 新特性: 分析结果现在分步骤实时显示，无需等待全部完成！{Style.RESET_ALL}
"""
        print(help_text)

    def print_response(self, response: AgentResponse):
        """美化打印响应结果"""
        response_type = response.get("type", "unknown")

        if response_type == "thinking":
            content = response.get("content", "")
            step = response.get("step", "")
            print(f"{Fore.BLUE}🤔 {content}{Style.RESET_ALL}")
            if step:
                print(f"{Fore.CYAN}   步骤: {step}{Style.RESET_ALL}")

        elif response_type == "intent_analysis":
            # 立即显示意图识别结果
            intent_analysis = response.get("intent_analysis", {})
            self.latest_intent_analysis = intent_analysis
            print(f"\n{Fore.CYAN}🧠 意图识别完成！{Style.RESET_ALL}")
            self._print_intent_analysis(intent_analysis)

        elif response_type == "user_response":
            # 立即显示AI用户回应（基于建议生成）
            user_response = response.get("user_response", "")
            self.latest_user_response = user_response
            print(f"\n{Fore.GREEN}🤖 AI用户回应（基于建议生成）: {user_response}{Style.RESET_ALL}")

        elif response_type == "suggestions":
            # 立即显示对话建议
            suggestions = response.get("suggestions", [])
            self.latest_suggestions = suggestions
            print(f"\n{Fore.MAGENTA}💡 对话建议生成完成！{Style.RESET_ALL}")
            self._print_suggestions(suggestions)

        elif response_type == "assistant":
            # 最终完成信号
            print(f"\n{Fore.GREEN}✅ 智能对话助理分析完成！{Style.RESET_ALL}")
            print(f"{Fore.CYAN}可以使用 'analysis'、'user'、'suggestions' 命令查看详细结果{Style.RESET_ALL}")

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

    def _print_intent_analysis(self, intent_analysis: Dict[str, Any]):
        """打印意图识别结果"""
        if not intent_analysis:
            return

        print(f"\n{Fore.CYAN}🧠 意图识别分析:{Style.RESET_ALL}")
        print("─" * 50)
        
        # 定义字段显示名称和图标
        field_info = {
            "讨论主题": ("📋", "讨论主题"),
            "涉及术语": ("📝", "涉及术语"),
            "涉及产品": ("🏢", "涉及产品"),
            "经纪人阶段性意图识别": ("🎯", "销售阶段"),
            "经纪人本句话意图识别": ("💬", "本句意图"),
            "用户当下需求": ("❓", "用户需求")
        }

        for key, value in intent_analysis.items():
            if key in field_info:
                icon, display_name = field_info[key]
                if isinstance(value, list):
                    value_str = ", ".join(value) if value else "无"
                else:
                    value_str = str(value) if value else "未识别"
                print(f"  {icon} {display_name}: {Fore.YELLOW}{value_str}{Style.RESET_ALL}")

    def _print_suggestions(self, suggestions: List[str]):
        """打印对话建议"""
        if not suggestions:
            return

        print(f"\n{Fore.MAGENTA}💡 对话建议:{Style.RESET_ALL}")
        print("─" * 50)
        for i, suggestion in enumerate(suggestions, 1):
            print(f"  {i}. {suggestion}")

    def print_conversation_history(self):
        """打印对话历史"""
        if not self.conversation_history:
            print(f"{Fore.YELLOW}⚠️  对话历史为空{Style.RESET_ALL}")
            return

        print(f"{Fore.CYAN}📜 对话历史 (共{len(self.conversation_history)}条):{Style.RESET_ALL}")
        print("─" * 60)
        for i, chat in enumerate(self.conversation_history, 1):
            role_color = Fore.BLUE if chat["role"] == ChatRole.USER else Fore.GREEN
            role_name = "AI用户" if chat["role"] == ChatRole.USER else "经纪人"
            role_icon = "🤖" if chat["role"] == ChatRole.USER else "🤵"
            print(f"  {i}. {role_icon} {role_color}{role_name}: {chat['content']}{Style.RESET_ALL}")

    def print_latest_analysis(self):
        """打印最新的意图分析"""
        if self.latest_intent_analysis:
            print(f"{Fore.CYAN}🔍 最新意图分析结果:{Style.RESET_ALL}")
            self._print_intent_analysis(self.latest_intent_analysis)
        else:
            print(f"{Fore.YELLOW}⚠️  还没有意图分析结果{Style.RESET_ALL}")

    def print_latest_suggestions(self):
        """打印最新的建议"""
        if self.latest_suggestions:
            print(f"{Fore.MAGENTA}💡 最新对话建议:{Style.RESET_ALL}")
            self._print_suggestions(self.latest_suggestions)
        else:
            print(f"{Fore.YELLOW}⚠️  还没有对话建议{Style.RESET_ALL}")

    def print_latest_user_response(self):
        """打印最新的AI用户回应"""
        if self.latest_user_response:
            print(f"{Fore.GREEN}🤖 最新AI用户回应:{Style.RESET_ALL}")
            print(f"   {self.latest_user_response}")
        else:
            print(f"{Fore.YELLOW}⚠️  还没有AI用户回应{Style.RESET_ALL}")

    def print_status(self):
        """打印当前状态"""
        print(f"{Fore.CYAN}📊 当前状态:{Style.RESET_ALL}")
        print(f"  用户ID: {Fore.YELLOW}{self.current_user_id}{Style.RESET_ALL}")
        print(f"  会话ID: {Fore.YELLOW}{self.current_session_id}{Style.RESET_ALL}")
        print(f"  对话轮次: {Fore.YELLOW}{len(self.conversation_history)}{Style.RESET_ALL}")
        
        analysis_status = "✅ 有" if self.latest_intent_analysis else "❌ 无"
        suggestions_status = "✅ 有" if self.latest_suggestions else "❌ 无"
        response_status = "✅ 有" if self.latest_user_response else "❌ 无"
        
        print(f"  意图分析: {analysis_status}")
        print(f"  用户回应: {response_status}")
        print(f"  对话建议: {suggestions_status}")
        
        if analysis_status == "✅ 有" and suggestions_status == "✅ 有" and response_status == "✅ 有":
            print(f"{Fore.GREEN}  状态: 📋 完整分析数据可用{Style.RESET_ALL}")
        elif analysis_status == "❌ 无" and suggestions_status == "❌ 无" and response_status == "❌ 无":
            print(f"{Fore.YELLOW}  状态: 🚀 准备开始对话{Style.RESET_ALL}")
        else:
            print(f"{Fore.BLUE}  状态: ⚡ 部分数据可用{Style.RESET_ALL}")

    def reset_session(self):
        """重置会话"""
        self.current_session_id += 1
        self.conversation_history.clear()
        self.latest_intent_analysis = None
        self.latest_suggestions = None
        self.latest_user_response = None
        print(f"{Fore.GREEN}✅ 会话已重置，新会话ID: {self.current_session_id}{Style.RESET_ALL}")

    async def test_rag_functionality(self):
        """测试RAG坑点检索功能"""
        print(f"{Fore.CYAN}🔍 开始测试RAG坑点检索功能...{Style.RESET_ALL}")
        
        if not self.assistant or not hasattr(self.assistant, 'pit_retriever') or not self.assistant.pit_retriever:
            print(f"{Fore.RED}❌ RAG坑点检索器未初始化{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}💡 请确保已运行数据预处理脚本: python tools/preprocess_pits_data.py{Style.RESET_ALL}")
            return
        
        # 测试查询列表
        test_queries = [
            "保费上涨",
            "费率比较",
            "首年便宜",
            "保障责任",
            "理赔条件",
            "医疗险便宜",
            "重疾险费用"
        ]
        
        print(f"{Fore.CYAN}📊 将测试以下查询:{Style.RESET_ALL}")
        for i, query in enumerate(test_queries, 1):
            print(f"  {i}. {query}")
        
        print(f"\n{Fore.BLUE}🔍 开始执行检索测试...{Style.RESET_ALL}")
        
        try:
            for i, query in enumerate(test_queries, 1):
                print(f"\n{Fore.YELLOW}{'='*50}{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}测试 {i}/{len(test_queries)}: 查询 '{query}'{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}{'='*50}{Style.RESET_ALL}")
                
                # 执行检索 - 使用更宽松的参数进行测试
                results = self.assistant.pit_retriever.search(
                    query, 
                    top_k=5, 
                    similarity_threshold=0.1  # 非常低的阈值用于测试
                )
                
                if results:
                    print(f"{Fore.GREEN}✅ 检索到 {len(results)} 个相关坑点:{Style.RESET_ALL}")
                    
                    for j, result in enumerate(results, 1):
                        similarity = result.get("similarity", 0)
                        category = result.get("category", "未分类")
                        title = result.get("title", "未知标题")
                        reason = result.get("reason", "")
                        
                        print(f"\n{Fore.CYAN}  {j}. 【{category}】{title}{Style.RESET_ALL}")
                        print(f"     相似度: {similarity:.3f}")
                        if reason:
                            print(f"     风险提示: {reason[:100]}{'...' if len(reason) > 100 else ''}")
                    
                    # 测试格式化功能
                    formatted_warnings = self.assistant.pit_retriever.format_pit_warnings(results)
                    if formatted_warnings:
                        print(f"\n{Fore.MAGENTA}📝 格式化警告信息:{Style.RESET_ALL}")
                        print(formatted_warnings[:300] + "..." if len(formatted_warnings) > 300 else formatted_warnings)
                else:
                    print(f"{Fore.YELLOW}⚠️  未找到相关坑点{Style.RESET_ALL}")
        
        except Exception as e:
            print(f"{Fore.RED}❌ RAG测试失败: {e}{Style.RESET_ALL}")
            return
        
        print(f"\n{Fore.GREEN}{'='*50}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}🎉 RAG功能测试完成！{Style.RESET_ALL}")
        print(f"{Fore.GREEN}{'='*50}{Style.RESET_ALL}")
        
        # 测试集成到建议生成的效果
        print(f"\n{Fore.CYAN}🔗 测试RAG集成到建议生成...{Style.RESET_ALL}")
        test_broker_message = "我们这款重疾险首年保费只要99元，性价比很高！"
        print(f"{Fore.BLUE}模拟经纪人话语: {test_broker_message}{Style.RESET_ALL}")
        
        try:
            # 创建测试请求
            request: AssistantRequest = {
                "user_id": self.current_user_id,
                "session_id": self.current_session_id,
                "broker_input": test_broker_message,
                "conversation_history": []
            }
            
            print(f"{Fore.BLUE}🔄 执行完整助理分析（包含RAG增强）...{Style.RESET_ALL}")
            
            async for response in self.assistant.assist_conversation(request):
                if response.get("type") == "suggestions":
                    suggestions = response.get("data", {}).get("suggestions", [])
                    print(f"\n{Fore.GREEN}💡 RAG增强的建议:{Style.RESET_ALL}")
                    for j, suggestion in enumerate(suggestions, 1):
                        print(f"  {j}. {suggestion}")
                    break
            
        except Exception as e:
            print(f"{Fore.RED}❌ RAG集成测试失败: {e}{Style.RESET_ALL}")

    async def broker_speak(self, broker_message: str):
        """经纪人发言，触发智能助理分析"""
        if not self.assistant:
            print(f"{Fore.RED}❌ 助理未初始化{Style.RESET_ALL}")
            return

        try:
            print(f"{Fore.BLUE}🤵 经纪人: {broker_message}{Style.RESET_ALL}")

            # 创建助理请求
            request: AssistantRequest = {
                "user_id": self.current_user_id,
                "session_id": self.current_session_id,
                "broker_input": broker_message,
                "conversation_history": self.conversation_history.copy()
            }

            print(f"{Fore.BLUE}🔄 开始智能分析流程...{Style.RESET_ALL}")
            print(f"{Fore.CYAN}   预期流程: 意图分析 → 对话建议 → AI用户回应{Style.RESET_ALL}")

            # 执行助理分析
            async for response in self.assistant.assist_conversation(request):
                self.print_response(response)

            # 更新对话历史
            # 添加经纪人消息
            broker_chat: ChatMessage = {
                "role": ChatRole.ASSISTANT,  # 经纪人作为助理角色
                "content": broker_message
            }
            self.conversation_history.append(broker_chat)

            # 添加AI用户回应
            if self.latest_user_response:
                user_chat: ChatMessage = {
                    "role": ChatRole.USER,  # AI用户
                    "content": self.latest_user_response
                }
                self.conversation_history.append(user_chat)

        except Exception as e:
            print(f"{Fore.RED}❌ 分析过程中发生错误: {e}{Style.RESET_ALL}")
            import traceback
            traceback.print_exc()

    async def interactive_loop(self):
        """交互式主循环"""
        try:
            while True:
                try:
                    user_input = input(f"{Fore.WHITE}> {Style.RESET_ALL}").strip()

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

                    elif command == "history":
                        self.print_conversation_history()

                    elif command == "analysis":
                        self.print_latest_analysis()

                    elif command == "suggestions":
                        self.print_latest_suggestions()

                    elif command == "user":
                        self.print_latest_user_response()

                    elif command == "clear":
                        self.conversation_history.clear()
                        self.latest_intent_analysis = None
                        self.latest_suggestions = None
                        self.latest_user_response = None
                        print(f"{Fore.GREEN}✅ 对话历史和分析结果已清空{Style.RESET_ALL}")

                    elif command == "reset":
                        self.reset_session()

                    elif command == "test_rag":
                        await self.test_rag_functionality()

                    elif command == "broker":
                        if len(parts) < 2:
                            print(f"{Fore.RED}❌ 请输入经纪人要说的话{Style.RESET_ALL}")
                            print(f"{Fore.YELLOW}💡 示例: broker 您好，我是您的保险顾问{Style.RESET_ALL}")
                            continue

                        message = " ".join(parts[1:])
                        await self.broker_speak(message)

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

    # 创建测试器
    tester = AgencyAssistantTester()

    try:
        # 初始化
        await tester.setup()

        # 显示横幅
        tester.print_banner()

        # 显示当前状态
        tester.print_status()

        # 进入交互循环
        await tester.interactive_loop()

    except Exception as e:
        print(f"{Fore.RED}❌ 程序运行错误: {e}{Style.RESET_ALL}")
        if "validate_assistant" in str(e):
            print(f"{Fore.YELLOW}💡 请确保已设置以下环境变量:{Style.RESET_ALL}")
            print("  AI_INSUR_DEEPSEEK_API_KEY=your_deepseek_api_key")
            print("  AI_INSUR_QWEN_API_KEY=your_qwen_api_key")
    finally:
        # 清理
        await tester.cleanup()


if __name__ == "__main__":
    asyncio.run(main()) 