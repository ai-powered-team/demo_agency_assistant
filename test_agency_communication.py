#!/usr/bin/env python3
"""
AgencyCommunicator 交互式命令行测试程序

提供交互式命令行界面来测试 AgencyCommunicator 的功能。
每次启动都会重置会话数据，避免测试数据污染。

使用方法:
    python test_agency_communication.py

预设经纪人:
    1. 张专业 (professional)   - 专业严谨型，8年经验
    2. 李亲和 (friendly)       - 亲和友善型，5年经验
    3. 王热情 (enthusiastic)   - 热情积极型，6年经验
    4. 陈顾问 (consultative)   - 咨询顾问型，10年经验
    5. 刘信赖 (trustworthy)    - 可靠信赖型，12年经验

常用命令:
    help                    - 显示帮助信息
    agencies                - 显示所有经纪人
    switch <id>             - 切换经纪人
    chat <message>          - 与经纪人对话
    history                 - 查看对话历史
    reset                   - 重置会话
    quit                    - 退出程序

示例对话:
    > agencies
    > switch 2
    > chat 我想了解重疾险
    > chat 保费大概多少钱？
    > chat 谢谢你的介绍
"""

from util import config, logger
from util.types import AgencyCommunicationRequest, AgentResponse, ChatMessage, AgencyInfo, AgencyTone, ChatRole
from agent.agency_communicator import AgencyCommunicator
import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional, List

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


class AgencyCommunicationTester:
    """保险经纪人沟通测试器"""

    def __init__(self):
        self.communicator: Optional[AgencyCommunicator] = None
        self.current_user_id = 1
        self.current_session_id = 1
        self.conversation_history: List[ChatMessage] = []
        self.current_agency_id = 1
        self.agencies: List[AgencyInfo] = []

    async def setup(self):
        """初始化测试环境"""
        try:
            # 创建保险经纪人沟通器
            self.communicator = AgencyCommunicator()
            print(f"{Fore.GREEN}✅ AgencyCommunicator 初始化成功{Style.RESET_ALL}")

            # 初始化预设经纪人
            self._init_preset_agencies()
            print(
                f"{Fore.GREEN}✅ 预设经纪人初始化完成，共 {len(self.agencies)} 个经纪人{Style.RESET_ALL}")

        except Exception as e:
            print(f"{Fore.RED}❌ 初始化失败: {e}{Style.RESET_ALL}")
            raise

    async def cleanup(self):
        """清理测试环境"""
        try:
            # 重置对话历史
            self.conversation_history.clear()
            print(f"{Fore.YELLOW}🧹 已清理会话数据和对话历史{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}❌ 清理失败: {e}{Style.RESET_ALL}")

    def _init_preset_agencies(self):
        """初始化预设经纪人"""
        self.agencies = [
            {
                "agency_id": 1,
                "name": "张专业",
                "tone": AgencyTone.PROFESSIONAL,
                "experience_years": 8
            },
            {
                "agency_id": 2,
                "name": "李亲和",
                "tone": AgencyTone.FRIENDLY,
                "experience_years": 5
            },
            {
                "agency_id": 3,
                "name": "王热情",
                "tone": AgencyTone.ENTHUSIASTIC,
                "experience_years": 6
            },
            {
                "agency_id": 4,
                "name": "陈顾问",
                "tone": AgencyTone.CONSULTATIVE,
                "experience_years": 10
            },
            {
                "agency_id": 5,
                "name": "刘信赖",
                "tone": AgencyTone.TRUSTWORTHY,
                "experience_years": 12
            }
        ]

    def print_banner(self):
        """打印程序横幅"""
        banner = f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════════╗
║                  保险经纪人沟通测试程序                      ║
║                Agency Communication Tester                  ║
╚══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}

{Fore.GREEN}🎯 功能: 测试与不同风格保险经纪人的智能沟通{Style.RESET_ALL}
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

{Fore.YELLOW}经纪人管理:{Style.RESET_ALL}
  agencies                - 显示所有可用经纪人
  switch <agency_id>      - 切换到指定经纪人
  current                 - 显示当前经纪人信息

{Fore.YELLOW}对话命令:{Style.RESET_ALL}
  chat <message>          - 与当前经纪人对话
  history                 - 显示对话历史
  clear                   - 清空对话历史
  reset                   - 重置会话（新的session_id）

{Fore.YELLOW}预设经纪人:{Style.RESET_ALL}
  1. 张专业 (professional)   - 专业严谨型，8年经验
  2. 李亲和 (friendly)       - 亲和友善型，5年经验
  3. 王热情 (enthusiastic)   - 热情积极型，6年经验
  4. 陈顾问 (consultative)   - 咨询顾问型，10年经验
  5. 刘信赖 (trustworthy)    - 可靠信赖型，12年经验

{Fore.YELLOW}示例:{Style.RESET_ALL}
  agencies
  switch 2
  chat 我想了解重疾险
  chat 保费大概多少钱？
  chat 谢谢你的介绍

{Fore.GREEN}💡 提示: 每次启动都会重置所有数据，确保测试独立性{Style.RESET_ALL}
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

        elif response_type == "answer":
            content = response.get("content", "")
            data = response.get("data", {})
            agency_name = data.get("agency_name", "经纪人") if data else "经纪人"
            tone = data.get("tone", "") if data else ""

            print(f"{Fore.GREEN}💬 {agency_name}: {content}{Style.RESET_ALL}")
            if tone:
                print(f"{Fore.CYAN}   风格: {tone}{Style.RESET_ALL}")

        elif response_type == "payment":
            message = response.get("message", "")
            agency_name = response.get("agency_name", "经纪人")
            recommended_action = response.get("recommended_action", "")

            print(f"{Fore.MAGENTA}💳 支付流程: {message}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}   经纪人: {agency_name}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}   建议行动: {recommended_action}{Style.RESET_ALL}")

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

    def print_agencies(self):
        """打印所有可用经纪人"""
        print(f"{Fore.CYAN}👥 可用经纪人列表:{Style.RESET_ALL}")
        for agency in self.agencies:
            current_marker = f"{Fore.GREEN}[当前]{Style.RESET_ALL}" if agency["agency_id"] == self.current_agency_id else ""
            tone_desc = {
                AgencyTone.PROFESSIONAL: "专业严谨型",
                AgencyTone.FRIENDLY: "亲和友善型",
                AgencyTone.ENTHUSIASTIC: "热情积极型",
                AgencyTone.CONSULTATIVE: "咨询顾问型",
                AgencyTone.TRUSTWORTHY: "可靠信赖型"
            }.get(agency["tone"], agency["tone"])

            print(
                f"  {agency['agency_id']}. {agency['name']} ({tone_desc}, {agency['experience_years']}年经验) {current_marker}")

    def print_current_agency(self):
        """打印当前经纪人信息"""
        current_agency = next(
            (a for a in self.agencies if a["agency_id"] == self.current_agency_id), None)
        if current_agency:
            tone_desc = {
                AgencyTone.PROFESSIONAL: "专业严谨型",
                AgencyTone.FRIENDLY: "亲和友善型",
                AgencyTone.ENTHUSIASTIC: "热情积极型",
                AgencyTone.CONSULTATIVE: "咨询顾问型",
                AgencyTone.TRUSTWORTHY: "可靠信赖型"
            }.get(current_agency["tone"], current_agency["tone"])

            print(f"{Fore.CYAN}👤 当前经纪人:{Style.RESET_ALL}")
            print(
                f"  姓名: {Fore.YELLOW}{current_agency['name']}{Style.RESET_ALL}")
            print(
                f"  ID: {Fore.YELLOW}{current_agency['agency_id']}{Style.RESET_ALL}")
            print(f"  风格: {Fore.YELLOW}{tone_desc}{Style.RESET_ALL}")
            print(
                f"  经验: {Fore.YELLOW}{current_agency['experience_years']}年{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}❌ 当前经纪人信息不存在{Style.RESET_ALL}")

    def print_conversation_history(self):
        """打印对话历史"""
        if not self.conversation_history:
            print(f"{Fore.YELLOW}⚠️  对话历史为空{Style.RESET_ALL}")
            return

        print(
            f"{Fore.CYAN}📜 对话历史 (共{len(self.conversation_history)}条):{Style.RESET_ALL}")
        for i, chat in enumerate(self.conversation_history, 1):
            role_color = Fore.BLUE if chat["role"] == ChatRole.USER else Fore.GREEN
            role_name = "用户" if chat["role"] == ChatRole.USER else "经纪人"
            print(
                f"  {i}. {role_color}{role_name}: {chat['content']}{Style.RESET_ALL}")

    def print_status(self):
        """打印当前状态"""
        print(f"{Fore.CYAN}📊 当前状态:{Style.RESET_ALL}")
        print(f"  用户ID: {Fore.YELLOW}{self.current_user_id}{Style.RESET_ALL}")
        print(
            f"  会话ID: {Fore.YELLOW}{self.current_session_id}{Style.RESET_ALL}")
        print(
            f"  对话轮次: {Fore.YELLOW}{len(self.conversation_history)}{Style.RESET_ALL}")
        print(f"  可用经纪人: {Fore.YELLOW}{len(self.agencies)}个{Style.RESET_ALL}")
        print()
        self.print_current_agency()

    def switch_agency(self, agency_id: int) -> bool:
        """切换到指定经纪人"""
        agency = next(
            (a for a in self.agencies if a["agency_id"] == agency_id), None)
        if agency:
            self.current_agency_id = agency_id
            print(f"{Fore.GREEN}✅ 已切换到经纪人: {agency['name']}{Style.RESET_ALL}")
            return True
        else:
            print(f"{Fore.RED}❌ 经纪人ID {agency_id} 不存在{Style.RESET_ALL}")
            return False

    def reset_session(self):
        """重置会话"""
        self.current_session_id += 1
        self.conversation_history.clear()
        print(f"{Fore.GREEN}✅ 会话已重置，新会话ID: {self.current_session_id}{Style.RESET_ALL}")

    async def chat_with_agency(self, user_message: str):
        """与经纪人对话"""
        if not self.communicator:
            print(f"{Fore.RED}❌ 沟通器未初始化{Style.RESET_ALL}")
            return

        try:
            # 添加用户消息到历史
            user_chat: ChatMessage = {
                "role": ChatRole.USER,
                "content": user_message
            }
            self.conversation_history.append(user_chat)

            # 创建沟通请求
            request: AgencyCommunicationRequest = {
                "user_id": self.current_user_id,
                "session_id": self.current_session_id,
                "history_chats": self.conversation_history.copy(),
                "agency_id": self.current_agency_id,
                "agencies": self.agencies
            }

            print(f"{Fore.BLUE}🔄 正在与经纪人沟通...{Style.RESET_ALL}")

            # 收集经纪人的回应
            agency_responses = []

            # 执行沟通
            async for response in self.communicator.communicate_with_agency(request):
                self.print_response(response)

                # 收集经纪人的回答
                if response.get("type") == "answer":
                    agency_responses.append(response.get("content", ""))

            # 将经纪人的回应添加到历史（合并多个回应）
            if agency_responses:
                combined_response = "\n".join(agency_responses)
                agency_chat: ChatMessage = {
                    "role": ChatRole.ASSISTANT,
                    "content": combined_response
                }
                self.conversation_history.append(agency_chat)

        except Exception as e:
            print(f"{Fore.RED}❌ 对话过程中发生错误: {e}{Style.RESET_ALL}")
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

                    elif command == "agencies":
                        self.print_agencies()

                    elif command == "current":
                        self.print_current_agency()

                    elif command == "history":
                        self.print_conversation_history()

                    elif command == "clear":
                        self.conversation_history.clear()
                        print(f"{Fore.GREEN}✅ 对话历史已清空{Style.RESET_ALL}")

                    elif command == "reset":
                        self.reset_session()

                    elif command == "switch":
                        if len(parts) < 2:
                            print(f"{Fore.RED}❌ 请指定经纪人ID{Style.RESET_ALL}")
                            continue
                        try:
                            agency_id = int(parts[1])
                            self.switch_agency(agency_id)
                        except ValueError:
                            print(f"{Fore.RED}❌ 经纪人ID必须是数字{Style.RESET_ALL}")

                    elif command == "chat":
                        if len(parts) < 2:
                            print(f"{Fore.RED}❌ 请输入要发送的消息{Style.RESET_ALL}")
                            continue

                        message = " ".join(parts[1:])
                        await self.chat_with_agency(message)

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
    tester = AgencyCommunicationTester()

    try:
        # 初始化
        await tester.setup()

        # 显示横幅
        tester.print_banner()

        # 显示当前状态
        tester.print_status()

        # 进入交互循环
        await tester.interactive_loop()

    finally:
        # 清理
        await tester.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
