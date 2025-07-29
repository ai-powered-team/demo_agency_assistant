#!/usr/bin/env python3
"""
ProductRecommender 交互式命令行测试程序

提供交互式命令行界面来测试 ProductRecommender 的功能。
每次启动都会创建新的临时 SQLite 数据库，避免测试数据污染。
"""

from util.database import db_manager
from util import config, logger
from util.types import UserProfile, ProductRecommendationRequest, AgentResponse
from agent.product_recommender import ProductRecommender
import asyncio
import json
import logging
import os
import sys
import tempfile
from pathlib import Path
from typing import Optional

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


class ProductRecommendTester:
    """产品推荐测试器"""

    def __init__(self):
        self.temp_db_file: Optional[str] = None
        self.recommender: Optional[ProductRecommender] = None
        self.current_user_id = 1
        self.current_session_id = 1
        self.current_profile: UserProfile = {}

    async def setup(self):
        """初始化测试环境"""
        # 创建临时数据库文件
        temp_fd, self.temp_db_file = tempfile.mkstemp(
            suffix='.db', prefix='test_product_recommend_')
        os.close(temp_fd)  # 关闭文件描述符，但保留文件

        # 设置临时数据库路径
        # 注意：这里我们直接使用临时数据库，不修改全局配置
        # 因为 DatabaseManager 会根据配置自动选择数据库类型

        try:
            # 初始化数据库
            await db_manager.initialize()
            print(f"{Fore.GREEN}✅ 临时数据库初始化成功: {self.temp_db_file}{Style.RESET_ALL}")

            # 创建产品推荐器
            self.recommender = ProductRecommender()
            print(f"{Fore.GREEN}✅ ProductRecommender 初始化成功{Style.RESET_ALL}")

        except Exception as e:
            print(f"{Fore.RED}❌ 初始化失败: {e}{Style.RESET_ALL}")
            raise

    async def cleanup(self):
        """清理测试环境"""
        try:
            await db_manager.close()
            if self.temp_db_file and os.path.exists(self.temp_db_file):
                os.unlink(self.temp_db_file)
                print(f"{Fore.YELLOW}🧹 已清理临时数据库{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}❌ 清理失败: {e}{Style.RESET_ALL}")

    def print_banner(self):
        """打印程序横幅"""
        banner = f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════════╗
║                    产品推荐测试程序                          ║
║                  Product Recommend Tester                    ║
╚══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}

{Fore.GREEN}🎯 功能: 测试基于用户画像的保险产品推荐{Style.RESET_ALL}
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
  recommend               - 基于当前用户画像获取产品推荐
  profile <json>          - 设置用户画像 (JSON格式)
  scenario <name>         - 加载预设用户画像场景
  modify <field> <value>  - 修改用户画像中的单个字段

{Fore.YELLOW}预设场景:{Style.RESET_ALL}
  young_tech              - 25岁互联网从业者，年收入30万
  family_man              - 35岁已婚男性，有孩子，年收入80万
  pregnant_woman          - 30岁孕妇，银行员工，收入稳定
  high_income             - 40岁高收入人群，年收入150万
  senior_citizen          - 55岁临近退休，有慢性病

{Fore.YELLOW}示例:{Style.RESET_ALL}
  scenario young_tech
  recommend
  modify annual_insurance_budget 5.0
  recommend
  profile {{"gender": "女", "annual_total_income": 50.0}}

{Fore.GREEN}💡 提示: 所有数据都是临时的，重启程序后会重置{Style.RESET_ALL}
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

        elif response_type == "product_recommendation":
            products = response.get("products", [])
            message = response.get("message", "")
            analysis_summary = response.get("analysis_summary", "")

            print(f"{Fore.GREEN}🎯 {message}{Style.RESET_ALL}")

            if analysis_summary:
                print(f"{Fore.CYAN}📊 分析摘要:{Style.RESET_ALL}")
                print(f"   {analysis_summary}")
                print()

            if products:
                print(f"{Fore.YELLOW}📋 推荐产品列表:{Style.RESET_ALL}")
                for i, product in enumerate(products, 1):
                    print(
                        f"\n{Fore.YELLOW}{i}. {product.get('product_name', '未知产品')}{Style.RESET_ALL}")
                    print(
                        f"   {Fore.CYAN}类型:{Style.RESET_ALL} {product.get('product_type', '未知')}")
                    print(
                        f"   {Fore.CYAN}简介:{Style.RESET_ALL} {product.get('product_description', '无描述')}")
                    print(
                        f"   {Fore.GREEN}推荐理由:{Style.RESET_ALL} {product.get('recommendation', '无推荐理由')}")
            else:
                print(f"{Fore.YELLOW}⚠️  暂无推荐产品{Style.RESET_ALL}")

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

    def print_current_profile(self):
        """打印当前用户画像"""
        if not self.current_profile:
            print(f"{Fore.YELLOW}⚠️  当前用户画像为空{Style.RESET_ALL}")
            return

        print(f"{Fore.CYAN}👤 当前用户画像:{Style.RESET_ALL}")

        # 按类别组织显示
        categories = {
            "基础信息": ["name", "gender", "date_of_birth", "marital_status", "residence_city", "occupation_type", "industry"],
            "家庭情况": ["family_structure", "number_of_children", "caregiving_responsibility", "monthly_household_expense", "mortgage_balance", "is_family_financial_support"],
            "财务状况": ["annual_total_income", "income_stability", "annual_insurance_budget"],
            "健康状况": ["overall_health_status", "has_chronic_disease", "smoking_status", "recent_medical_checkup"],
            "女性特殊": ["pregnancy_status", "childbearing_plan"]
        }

        for category, fields in categories.items():
            category_data = {
                k: v for k, v in self.current_profile.items() if k in fields and v is not None}
            if category_data:
                print(f"\n  {Fore.YELLOW}{category}:{Style.RESET_ALL}")
                for key, value in category_data.items():
                    print(f"    {key}: {Fore.WHITE}{value}{Style.RESET_ALL}")

    def print_status(self):
        """打印当前状态"""
        print(f"{Fore.CYAN}📊 当前状态:{Style.RESET_ALL}")
        print(f"  用户ID: {Fore.YELLOW}{self.current_user_id}{Style.RESET_ALL}")
        print(
            f"  会话ID: {Fore.YELLOW}{self.current_session_id}{Style.RESET_ALL}")
        print(
            f"  画像字段数: {Fore.YELLOW}{len([k for k, v in self.current_profile.items() if v is not None])}{Style.RESET_ALL}")
        print(f"  临时数据库: {Fore.YELLOW}{self.temp_db_file}{Style.RESET_ALL}")
        print()
        self.print_current_profile()

    def load_preset_scenario(self, scenario_name: str) -> bool:
        """加载预设用户画像场景"""
        scenarios = {
            "young_tech": {
                "name": "25岁互联网从业者",
                "profile": {
                    "gender": "男",
                    "date_of_birth": "1999-03-15",
                    "marital_status": "未婚",
                    "residence_city": "北京",
                    "occupation_type": "企业员工",
                    "industry": "互联网",
                    "family_structure": "单身",
                    "annual_total_income": 30.0,
                    "income_stability": "比较稳定",
                    "annual_insurance_budget": 3.0,
                    "overall_health_status": "非常健康",
                    "has_chronic_disease": "无",
                    "smoking_status": "不吸烟"
                }
            },
            "family_man": {
                "name": "35岁已婚男性",
                "profile": {
                    "gender": "男",
                    "date_of_birth": "1989-07-20",
                    "marital_status": "已婚",
                    "residence_city": "上海",
                    "occupation_type": "企业员工",
                    "industry": "制造业",
                    "family_structure": "夫妻+子女",
                    "number_of_children": 2,
                    "caregiving_responsibility": "无",
                    "monthly_household_expense": 15000.0,
                    "mortgage_balance": 200.0,
                    "is_family_financial_support": "是",
                    "annual_total_income": 80.0,
                    "income_stability": "非常稳定",
                    "annual_insurance_budget": 8.0,
                    "overall_health_status": "比较健康",
                    "has_chronic_disease": "无",
                    "smoking_status": "轻度吸烟"
                }
            },
            "pregnant_woman": {
                "name": "30岁孕妇",
                "profile": {
                    "gender": "女",
                    "date_of_birth": "1994-05-10",
                    "marital_status": "已婚",
                    "residence_city": "深圳",
                    "occupation_type": "企业员工",
                    "industry": "金融",
                    "pregnancy_status": "孕中期(4-6月)",
                    "childbearing_plan": "1年内",
                    "family_structure": "夫妻",
                    "caregiving_responsibility": "无",
                    "monthly_household_expense": 12000.0,
                    "is_family_financial_support": "共同承担",
                    "annual_total_income": 60.0,
                    "income_stability": "非常稳定",
                    "annual_insurance_budget": 6.0,
                    "overall_health_status": "比较健康",
                    "has_chronic_disease": "无",
                    "smoking_status": "不吸烟"
                }
            },
            "high_income": {
                "name": "40岁高收入人群",
                "profile": {
                    "gender": "男",
                    "date_of_birth": "1984-12-03",
                    "marital_status": "已婚",
                    "residence_city": "北京",
                    "occupation_type": "企业主",
                    "industry": "金融",
                    "family_structure": "夫妻+子女",
                    "number_of_children": 1,
                    "caregiving_responsibility": "赡养父母",
                    "monthly_household_expense": 30000.0,
                    "mortgage_balance": 500.0,
                    "is_family_financial_support": "是",
                    "annual_total_income": 150.0,
                    "income_stability": "比较稳定",
                    "annual_insurance_budget": 20.0,
                    "overall_health_status": "比较健康",
                    "has_chronic_disease": "无",
                    "smoking_status": "已戒烟",
                    "recent_medical_checkup": "1年内正常"
                }
            },
            "senior_citizen": {
                "name": "55岁临近退休",
                "profile": {
                    "gender": "女",
                    "date_of_birth": "1969-08-25",
                    "marital_status": "已婚",
                    "residence_city": "广州",
                    "occupation_type": "企业员工",
                    "industry": "教育",
                    "family_structure": "夫妻",
                    "number_of_children": 1,
                    "caregiving_responsibility": "赡养双方父母",
                    "monthly_household_expense": 8000.0,
                    "is_family_financial_support": "共同承担",
                    "annual_total_income": 45.0,
                    "income_stability": "非常稳定",
                    "annual_insurance_budget": 5.0,
                    "overall_health_status": "有慢性病",
                    "has_chronic_disease": "高血压",
                    "smoking_status": "不吸烟",
                    "recent_medical_checkup": "1年内有异常"
                }
            }
        }

        if scenario_name not in scenarios:
            available = ", ".join(scenarios.keys())
            print(f"{Fore.RED}❌ 未知场景: {scenario_name}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}可用场景: {available}{Style.RESET_ALL}")
            return False

        scenario = scenarios[scenario_name]
        self.current_profile = scenario["profile"].copy()

        print(f"{Fore.GREEN}✅ 已加载预设场景: {scenario['name']}{Style.RESET_ALL}")
        print(
            f"{Fore.CYAN}📝 场景包含 {len([k for k, v in self.current_profile.items() if v is not None])} 个用户特征{Style.RESET_ALL}")

        return True

    def modify_profile_field(self, field: str, value: str) -> bool:
        """修改用户画像中的单个字段"""
        try:
            # 尝试解析数值类型
            if field in ["number_of_children"]:
                parsed_value = int(value)
            elif field in ["annual_total_income", "annual_insurance_budget", "monthly_household_expense", "mortgage_balance"]:
                parsed_value = float(value)
            else:
                parsed_value = value

            self.current_profile[field] = parsed_value
            print(f"{Fore.GREEN}✅ 已修改字段 {field} = {parsed_value}{Style.RESET_ALL}")
            return True

        except ValueError as e:
            print(f"{Fore.RED}❌ 字段值格式错误: {e}{Style.RESET_ALL}")
            return False

    async def get_product_recommendation(self):
        """获取产品推荐"""
        if not self.current_profile:
            print(f"{Fore.YELLOW}⚠️  请先设置用户画像或加载预设场景{Style.RESET_ALL}")
            return

        if not self.recommender:
            print(f"{Fore.RED}❌ 推荐器未初始化{Style.RESET_ALL}")
            return

        try:
            # 创建推荐请求
            request: ProductRecommendationRequest = {
                "user_id": self.current_user_id,
                "session_id": self.current_session_id,
                "custom_profile": self.current_profile
            }

            print(f"{Fore.BLUE}🔍 正在获取产品推荐...{Style.RESET_ALL}")

            # 执行推荐
            async for response in self.recommender.recommend_products(request):
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
                        await self.get_product_recommendation()

                    elif command == "scenario":
                        if len(parts) < 2:
                            print(f"{Fore.RED}❌ 请指定场景名称{Style.RESET_ALL}")
                            continue
                        self.load_preset_scenario(parts[1])

                    elif command == "profile":
                        if len(parts) < 2:
                            print(f"{Fore.RED}❌ 请提供JSON格式的用户画像{Style.RESET_ALL}")
                            continue

                        try:
                            profile_json = " ".join(parts[1:])
                            profile_data = json.loads(profile_json)
                            self.current_profile.update(profile_data)
                            print(f"{Fore.GREEN}✅ 用户画像已更新{Style.RESET_ALL}")
                        except json.JSONDecodeError as e:
                            print(f"{Fore.RED}❌ JSON格式错误: {e}{Style.RESET_ALL}")

                    elif command == "modify":
                        if len(parts) < 3:
                            print(
                                f"{Fore.RED}❌ 用法: modify <字段名> <值>{Style.RESET_ALL}")
                            continue

                        field = parts[1]
                        value = " ".join(parts[2:])
                        self.modify_profile_field(field, value)

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
    tester = ProductRecommendTester()

    try:
        # 初始化
        await tester.setup()

        # 显示横幅
        tester.print_banner()

        # 进入交互循环
        await tester.interactive_loop()

    finally:
        # 清理
        await tester.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
