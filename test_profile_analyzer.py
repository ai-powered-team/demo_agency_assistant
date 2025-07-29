#!/usr/bin/env python3
"""
ProfileAnalyzer 交互式命令行测试程序

提供交互式命令行界面来测试 ProfileAnalyzer 的功能。
每次启动都会创建新的临时 SQLite 数据库，避免测试数据污染。
"""

from util.database import db_manager
from util import config, logger
from util.types import ChatMessage, UserProfile, ProfileAnalysisRequest, AgentResponse
from agent.profile_analyzer import ProfileAnalyzer
import asyncio
import json
import logging
import os
import sys
import tempfile
from pathlib import Path
from typing import List
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
    _ = readline
except ImportError:
    pass  # readline 在某些系统上可能不可用

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))


class ColoredFormatter(logging.Formatter):
    """彩色日志格式化器"""

    def format(self, record):
        # 使用灰色显示所有日志
        formatted = super().format(record)
        return f"{Fore.LIGHTBLACK_EX}{formatted}{Style.RESET_ALL}"


class TestProfileAnalyzer:
    """ProfileAnalyzer 测试类"""

    def __init__(self):
        """初始化测试环境"""

        # 创建临时数据库
        self.temp_db_file = None
        self.setup_temp_database()

        # 设置日志格式
        self.setup_logging()

        # 初始化分析器
        self.analyzer = ProfileAnalyzer()

        # 测试会话信息
        self.user_id = 12345
        self.session_id = 1
        self.conversation_history: List[ChatMessage] = []
        self.asked_questions_history: List[str] = []  # 记录历史问题

        print(f"{Fore.GREEN}🚀 ProfileAnalyzer 测试程序启动成功！{Style.RESET_ALL}")
        print(f"{Fore.CYAN}📁 临时数据库: {self.temp_db_file}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}💡 输入 'help' 查看可用命令{Style.RESET_ALL}")
        print("-" * 60)

    def setup_temp_database(self):
        """设置临时数据库"""
        # 创建临时文件
        temp_fd, temp_db_file = tempfile.mkstemp(
            suffix='.db', prefix='test_profile_')
        os.close(temp_fd)  # 关闭文件描述符，只保留文件路径
        self.temp_db_file = temp_db_file

        # 修改配置以使用临时数据库
        config.get_db_url = lambda: None  # 强制使用 SQLite

        # 修改 SQLite URL 指向临时文件
        from util.database import DatabaseManager

        async def temp_initialize(self):
            """使用临时数据库的初始化方法"""
            # 检查是否已经初始化过
            if self.session_factory is not None:
                logger.info("临时数据库已经初始化，跳过重复初始化")
                return self.session_factory

            try:
                from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
                from sqlalchemy.ext.asyncio import AsyncSession
                from util.database import Base

                # 使用临时数据库文件
                sqlite_url = f"sqlite+aiosqlite:///{temp_db_file}"
                self.engine = create_async_engine(sqlite_url, echo=False)
                self._is_sqlite = True

                # 创建会话工厂
                self.session_factory = async_sessionmaker(
                    self.engine,
                    class_=AsyncSession,
                    expire_on_commit=False
                )

                # 创建表
                async with self.engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)

                logger.info(f"临时数据库初始化完成: {temp_db_file}")
                return self.session_factory

            except Exception as e:
                logger.error(f"临时数据库初始化失败: {e}")
                raise

        # 替换初始化方法
        DatabaseManager.initialize = temp_initialize

    def setup_logging(self):
        """设置日志格式"""
        # 移除现有的处理器
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

        # 添加彩色控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(ColoredFormatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(console_handler)
        logger.setLevel(logging.INFO)

    def cleanup(self):
        """清理临时文件"""
        if self.temp_db_file and os.path.exists(self.temp_db_file):
            try:
                os.unlink(self.temp_db_file)
                print(f"{Fore.GREEN}🗑️  临时数据库已清理{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.RED}❌ 清理临时数据库失败: {e}{Style.RESET_ALL}")

    def print_help(self):
        """打印帮助信息"""
        help_text = f"""
{Fore.CYAN}📖 可用命令:{Style.RESET_ALL}

{Fore.YELLOW}基本命令:{Style.RESET_ALL}
  help                     - 显示此帮助信息
  clear                    - 清空对话历史
  history                  - 显示对话历史
  questions                - 显示历史问题记录
  profile                  - 显示当前用户画像
  export                   - 导出用户画像为JSON格式
  status                   - 显示当前状态信息
  exit/quit               - 退出程序

{Fore.YELLOW}测试命令:{Style.RESET_ALL}
  test <message>          - 发送测试消息进行分析
  custom <json>           - 设置自定义用户画像 (JSON格式)
  analyze                 - 执行完整的画像分析
  scenario <name>         - 加载预设测试场景

{Fore.YELLOW}预设场景:{Style.RESET_ALL}
  young_female            - 25岁女性，互联网公司员工
  middle_aged_male        - 40岁男性工程师，已婚有孩子
  pregnant_woman          - 30岁孕妇，银行员工

{Fore.YELLOW}示例:{Style.RESET_ALL}
  test 我是一个30岁的女性，年收入50万
  custom {{"gender": "女", "annual_total_income": 50.0}}
  scenario young_female
  analyze

{Fore.GREEN}💡 提示: 直接输入消息也会被当作测试消息处理{Style.RESET_ALL}
"""
        print(help_text)

    def print_response(self, response: AgentResponse):
        """美化打印响应结果"""
        response_type = response.get("type", "unknown")

        if response_type == "thinking":
            content = response.get("content", "")
            step = response.get("step", "")
            print(f"{Fore.BLUE}🤔 思考: {content} [{step}]{Style.RESET_ALL}")

        elif response_type == "profile":
            features = response.get("features", [])
            message = response.get("message", "")
            print(f"\n{Fore.GREEN}✨ {message}{Style.RESET_ALL}")

            if features:
                print(f"{Fore.CYAN}📊 提取的特征:{Style.RESET_ALL}")
                for feature in features:
                    category = feature.get("category_name", "")
                    name = feature.get("feature_name", "")
                    value = feature.get("feature_value", "")
                    confidence = feature.get("confidence", 0.0)

                    # 根据置信度选择颜色
                    if confidence >= 0.8:
                        conf_color = Fore.GREEN
                    elif confidence >= 0.5:
                        conf_color = Fore.YELLOW
                    else:
                        conf_color = Fore.RED

                    print(f"  • {Fore.WHITE}{category}.{name}{Style.RESET_ALL}: "
                          f"{Fore.CYAN}{value}{Style.RESET_ALL} "
                          f"({conf_color}置信度: {confidence:.2f}{Style.RESET_ALL}, ")
            print()

        elif response_type == "answer":
            content = response.get("content", "")
            print(f"\n{Fore.YELLOW}❓ {content}{Style.RESET_ALL}\n")

            # 记录问题到历史记录
            if content and content not in self.asked_questions_history:
                self.asked_questions_history.append(content)

        elif response_type == "profile_complete":
            message = response.get("message", "")
            completion_rate = response.get("completion_rate", 0.0)
            print(f"\n{Fore.GREEN}🎉 {message}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}📈 完成度: {completion_rate:.1%}{Style.RESET_ALL}\n")

        elif response_type == "error":
            error = response.get("error", "")
            details = response.get("details", "")
            print(f"\n{Fore.RED}❌ 错误: {error}{Style.RESET_ALL}")
            if details:
                print(f"{Fore.RED}详情: {details}{Style.RESET_ALL}\n")
        else:
            print(
                f"{Fore.MAGENTA}📄 响应: {json.dumps(response, ensure_ascii=False, indent=2)}{Style.RESET_ALL}")

    async def run_analysis(self, custom_profile: UserProfile = {}):
        """运行画像分析"""
        request: ProfileAnalysisRequest = {
            "user_id": self.user_id,
            "session_id": self.session_id,
            "history_chats": self.conversation_history,
            "custom_profile": custom_profile
        }

        print(f"{Fore.CYAN}🔍 开始分析用户画像...{Style.RESET_ALL}")
        print("-" * 40)

        try:
            async for response in self.analyzer.analyze_profile(request):
                self.print_response(response)
        except Exception as e:
            print(f"{Fore.RED}❌ 分析过程中发生错误: {e}{Style.RESET_ALL}")

    def add_message(self, role: str, content: str):
        """添加消息到对话历史"""
        message: ChatMessage = {
            "role": role,  # type: ignore
            "content": content
        }
        self.conversation_history.append(message)

    def show_history(self):
        """显示对话历史"""
        if not self.conversation_history:
            print(f"{Fore.YELLOW}📝 对话历史为空{Style.RESET_ALL}")
            return

        print(f"{Fore.CYAN}📝 对话历史:{Style.RESET_ALL}")
        for i, msg in enumerate(self.conversation_history, 1):
            role_color = Fore.GREEN if msg["role"] == "user" else Fore.BLUE
            print(
                f"  {i}. {role_color}{msg['role']}{Style.RESET_ALL}: {msg['content']}")
        print()

    def show_questions_history(self):
        """显示历史问题记录"""
        if not self.asked_questions_history:
            print(f"{Fore.YELLOW}❓ 历史问题记录为空{Style.RESET_ALL}")
            return

        print(f"{Fore.CYAN}❓ 历史问题记录:{Style.RESET_ALL}")
        for i, question in enumerate(self.asked_questions_history, 1):
            print(f"  {i}. {Fore.MAGENTA}{question}{Style.RESET_ALL}")
        print()

    async def show_profile(self):
        """显示当前用户画像"""
        try:
            # 确保数据库已初始化
            await db_manager.initialize()

            # 获取用户画像摘要
            profile_summary = await db_manager.get_user_profile_summary(self.user_id, self.session_id)
            profile_data = profile_summary.get('profile', {})

            if not profile_data:
                print(f"{Fore.YELLOW}👤 当前用户画像为空{Style.RESET_ALL}")
                return

            print(f"{Fore.CYAN}👤 当前用户画像 (用户ID: {self.user_id}):{Style.RESET_ALL}")

            for category_name, features in profile_data.items():
                if features:
                    print(
                        f"\n  {Fore.YELLOW}📂 {category_name}:{Style.RESET_ALL}")
                    for feature_name, feature_info in features.items():
                        value = feature_info.get('feature_value', '')
                        confidence = feature_info.get('confidence', 0.0)
                        skipped = feature_info.get('skipped', False)

                        # 根据置信度和状态选择颜色
                        if skipped:
                            status_color = Fore.RED
                            status_text = "已跳过"
                        elif confidence >= 0.8:
                            status_color = Fore.GREEN
                            status_text = f"置信度: {confidence:.2f}"
                        elif confidence >= 0.5:
                            status_color = Fore.YELLOW
                            status_text = f"置信度: {confidence:.2f}"
                        else:
                            status_color = Fore.RED
                            status_text = f"置信度: {confidence:.2f}"

                        print(f"    • {Fore.WHITE}{feature_name}{Style.RESET_ALL}: "
                              f"{Fore.CYAN}{value}{Style.RESET_ALL} "
                              f"({status_color}{status_text}{Style.RESET_ALL})")

            completion_rate = profile_summary.get('completion_rate', 0.0)
            print(
                f"\n  {Fore.CYAN}📈 完成度: {completion_rate:.1%}{Style.RESET_ALL}\n")

        except Exception as e:
            print(f"{Fore.RED}❌ 获取用户画像失败: {e}{Style.RESET_ALL}")

    async def export_profile_json(self):
        """导出用户画像为JSON格式，便于ES查询设计"""
        try:
            # 确保数据库已初始化
            await db_manager.initialize()

            # 获取用户画像摘要
            profile_summary = await db_manager.get_user_profile_summary(self.user_id, self.session_id)
            profile_data = profile_summary.get('profile', {})

            if not profile_data:
                print(f"{Fore.YELLOW}👤 当前用户画像为空{Style.RESET_ALL}")
                return {}

            # 转换为扁平化的UserProfile格式
            user_profile = {}

            for _, features in profile_data.items():
                if features:
                    for feature_name, feature_info in features.items():
                        value = feature_info.get('feature_value', '')
                        confidence = feature_info.get('confidence', 0.0)
                        skipped = feature_info.get('skipped', False)

                        # 只包含高置信度且未跳过的特征
                        if not skipped and confidence >= 0.5 and value:
                            user_profile[feature_name] = value

            print(f"{Fore.CYAN}📋 用户特征JSON (用于ES查询设计):{Style.RESET_ALL}")
            print(
                f"{Fore.GREEN}{json.dumps(user_profile, ensure_ascii=False, indent=2)}{Style.RESET_ALL}")

            return user_profile

        except Exception as e:
            print(f"{Fore.RED}❌ 导出用户画像失败: {e}{Style.RESET_ALL}")
            return {}

    def print_status(self):
        """打印当前状态"""
        print(f"{Fore.CYAN}📊 当前状态:{Style.RESET_ALL}")
        print(f"  用户ID: {Fore.YELLOW}{self.user_id}{Style.RESET_ALL}")
        print(f"  会话ID: {Fore.YELLOW}{self.session_id}{Style.RESET_ALL}")
        print(
            f"  对话消息数: {Fore.YELLOW}{len(self.conversation_history)}{Style.RESET_ALL}")
        print(f"  临时数据库: {Fore.YELLOW}{self.temp_db_file}{Style.RESET_ALL}")
        print()

    def load_test_scenario(self, scenario_name: str):
        """加载预设测试场景"""
        scenarios = {
            "young_female": {
                "messages": [
                    "我是一个25岁的女性，刚刚大学毕业",
                    "我在一家互联网公司工作，年收入大概30万",
                    "我还没有结婚，但是有男朋友",
                    "我想了解一些保险产品"
                ],
                "custom_profile": {
                    "gender": "女",
                    "annual_total_income": 30.0
                }
            },
            "middle_aged_male": {
                "messages": [
                    "我今年40岁，是一名工程师",
                    "我已经结婚了，有两个孩子",
                    "我的年收入大概80万，还有房贷要还",
                    "我想给家人买一些保险"
                ],
                "custom_profile": {
                    "gender": "男",
                    "marital_status": "已婚",
                    "number_of_children": 2,
                    "annual_total_income": 80.0
                }
            },
            "pregnant_woman": {
                "messages": [
                    "我是一个30岁的女性，目前怀孕5个月了",
                    "我和老公都在银行工作，收入比较稳定",
                    "我们想为即将出生的宝宝做一些保障规划"
                ],
                "custom_profile": {
                    "gender": "女",
                    "pregnancy_status": "孕中期(4-6月)",
                    "marital_status": "已婚",
                    "occupation_type": "企业员工"
                }
            }
        }

        if scenario_name not in scenarios:
            available = ", ".join(scenarios.keys())
            print(f"{Fore.RED}❌ 未知场景: {scenario_name}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}可用场景: {available}{Style.RESET_ALL}")
            return False

        scenario = scenarios[scenario_name]

        # 清空当前对话历史
        self.conversation_history.clear()

        # 添加场景消息
        for message in scenario["messages"]:
            self.add_message("user", message)

        print(f"{Fore.GREEN}✅ 已加载测试场景: {scenario_name}{Style.RESET_ALL}")
        print(
            f"{Fore.CYAN}📝 场景包含 {len(scenario['messages'])} 条消息{Style.RESET_ALL}")

        return scenario.get("custom_profile")

    async def interactive_loop(self):
        """交互式主循环"""
        try:
            while True:
                try:
                    user_input = input(
                        f"{Fore.WHITE}> {Style.RESET_ALL}").strip()

                    if not user_input:
                        continue

                    # 处理命令
                    if user_input.lower() in ['exit', 'quit']:
                        break
                    elif user_input.lower() == 'help':
                        self.print_help()
                    elif user_input.lower() == 'clear':
                        self.conversation_history.clear()
                        self.asked_questions_history.clear()
                        # 清空 ProfileAnalyzer 中的用户历史记录
                        self.analyzer.clear_user_history(self.user_id)
                        print(f"{Fore.GREEN}🗑️  对话历史和问题记录已清空{Style.RESET_ALL}")
                    elif user_input.lower() == 'history':
                        self.show_history()
                    elif user_input.lower() == 'questions':
                        self.show_questions_history()
                    elif user_input.lower() == 'profile':
                        await self.show_profile()
                    elif user_input.lower() == 'export':
                        await self.export_profile_json()
                    elif user_input.lower() == 'status':
                        self.print_status()
                    elif user_input.lower() == 'analyze':
                        await self.run_analysis()
                    elif user_input.startswith('test '):
                        message = user_input[5:]
                        self.add_message("user", message)
                        print(f"{Fore.GREEN}✅ 已添加测试消息{Style.RESET_ALL}")
                    elif user_input.startswith('scenario '):
                        scenario_name = user_input[9:].strip()
                        custom_profile = self.load_test_scenario(scenario_name)
                        if custom_profile:
                            await self.run_analysis(custom_profile)
                    elif user_input.startswith('custom '):
                        try:
                            custom_json = user_input[7:]
                            custom_profile = json.loads(custom_json)
                            await self.run_analysis(custom_profile)
                        except json.JSONDecodeError as e:
                            print(f"{Fore.RED}❌ JSON 格式错误: {e}{Style.RESET_ALL}")
                    elif user_input:
                        # 直接当作用户消息处理
                        self.add_message("user", user_input)
                        await self.run_analysis()

                except KeyboardInterrupt:
                    print(
                        f"\n{Fore.YELLOW}⚠️  使用 'exit' 或 'quit' 退出程序{Style.RESET_ALL}")
                except Exception as e:
                    print(f"{Fore.RED}❌ 发生错误: {e}{Style.RESET_ALL}")

        finally:
            self.cleanup()


def check_dependencies():
    """检查必要的依赖"""
    missing_deps = []
    optional_deps = []

    # 检查必要依赖
    try:
        import mem0
        _ = mem0
    except ImportError:
        missing_deps.append("mem0ai")

    try:
        import sqlalchemy
        _ = sqlalchemy
    except ImportError:
        missing_deps.append("sqlalchemy[asyncio]")

    try:
        import aiosqlite
        _ = aiosqlite
    except ImportError:
        missing_deps.append("aiosqlite")

    # 检查可选依赖
    if not HAS_COLORAMA:
        optional_deps.append("colorama")

    if missing_deps:
        print(f"{Fore.RED}❌ 缺少必要的依赖包:{Style.RESET_ALL}")
        for dep in missing_deps:
            print(f"  - {dep}")
        print(f"\n{Fore.YELLOW}请运行以下命令安装:{Style.RESET_ALL}")
        print(f"  pip install {' '.join(missing_deps)}")
        return False

    if optional_deps:
        print(f"{Fore.YELLOW}💡 建议安装以下可选依赖以获得更好体验:{Style.RESET_ALL}")
        for dep in optional_deps:
            print(f"  - {dep}")
        print(f"  pip install {' '.join(optional_deps)}")
        print()

    return True


async def main():
    """主函数"""
    print(f"{Fore.CYAN}🧪 ProfileAnalyzer 交互式测试程序{Style.RESET_ALL}")
    print(f"{Fore.CYAN}=" * 50 + Style.RESET_ALL)

    # 检查依赖
    if not check_dependencies():
        return

    # 检查必要的环境变量
    if not config.OPENAI_API_KEY:
        print(f"{Fore.RED}❌ 请设置 AI_INSUR_OPENAI_API_KEY 环境变量{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}💡 可以在 .env 文件中设置:{Style.RESET_ALL}")
        print("  AI_INSUR_OPENAI_API_KEY=your_api_key_here")
        return

    try:
        tester = TestProfileAnalyzer()
        await tester.interactive_loop()
    except Exception as e:
        print(f"{Fore.RED}❌ 程序启动失败: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()

    print(f"{Fore.GREEN}👋 再见！{Style.RESET_ALL}")


if __name__ == "__main__":
    asyncio.run(main())
