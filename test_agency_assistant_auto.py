#!/usr/bin/env python3
"""
AgencyAssistant 自动化AI对话测试程序

两个AI进行对抗性对话：
- 经纪人AI：扮演保险经纪人，使用误导性话术推销产品
- 用户AI：扮演保险用户，基于智能建议进行回应

使用方法:
    python test_agency_assistant_auto.py

功能特性:
    🤖 经纪人AI：自动生成误导性推销话术
    🤖 用户AI：基于智能建议进行回应
    💡 实时显示对话建议和意图分析
    📊 自动记录对话到日志文件
    ⏱️  自动停止（20回合）

常用命令:
    help                    - 显示帮助信息
    broker                  - 开始自动化AI对话
    status                  - 显示当前状态
    history                 - 查看对话历史
    quit                    - 退出程序
"""

import asyncio
import json
import logging
import sys
import time
from datetime import datetime
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
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import SecretStr


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


class BrokerAI:
    """经纪人AI - 使用DeepSeek生成误导性推销话术"""
    
    def __init__(self):
        # 验证配置
        if not config.DEEPSEEK_API_KEY:
            raise ValueError("需要设置 AI_INSUR_DEEPSEEK_API_KEY 环境变量")
        
        # 初始化DeepSeek模型
        self.deepseek = ChatOpenAI(
            api_key=SecretStr(config.DEEPSEEK_API_KEY),
            base_url="https://api.deepseek.com",
            model="deepseek-chat",
            temperature=0.8  # 稍微提高创造性
        )
        
        self.products = [
            {
                "name": "超级重疾险",
                "features": ["首年保费极低", "理赔条件宽松", "100%报销"],
                "pitfalls": ["后续保费大幅上涨", "理赔条件苛刻", "报销比例有限"]
            },
            {
                "name": "万能医疗险",
                "features": ["无免赔额", "不限医院", "终身保障"],
                "pitfalls": ["保费逐年递增", "特定医院除外", "保障期限有限"]
            },
            {
                "name": "投资型寿险",
                "features": ["高收益", "灵活取现", "免税优惠"],
                "pitfalls": ["收益不确定", "手续费高昂", "提前退保损失"]
            }
        ]
        self.current_product = None
        self.conversation_history = []
    
    def select_product(self):
        """选择要推销的产品"""
        import random
        self.current_product = random.choice(self.products)
        return self.current_product
    
    async def generate_broker_message(self, conversation_history: List[ChatMessage] = None, round_num: int = 0) -> str:
        """使用DeepSeek基于聊天记录生成经纪人AI的误导性话术"""
        if not self.current_product:
            self.select_product()
        
        product = self.current_product
        
        # 构建对话历史上下文
        context_messages = []
        if conversation_history:
            for msg in conversation_history[-6:]:  # 最近3轮对话
                role = "经纪人" if msg["role"] == "assistant" else "用户"
                context_messages.append(f"{role}: {msg['content']}")
        
        context = "\n".join(context_messages) if context_messages else "这是对话的开始"
        
        # 构建系统提示词
        system_prompt = f"""你是一个经验丰富的保险经纪人，专门推销{product['name']}产品。

你的任务：
1. 基于对话历史，生成自然的、有说服力的推销话术
2. 使用误导性技巧，但要让话术听起来合理可信
3. 根据对话进展调整策略：开场、需求挖掘、产品介绍、异议处理、促成签单
4. 利用紧迫感、稀缺性、社会认同等心理技巧
5. 回应要自然，不要过于生硬或重复

产品信息：
- 产品名称：{product['name']}
- 主要卖点：{', '.join(product['features'])}
- 隐藏风险：{', '.join(product['pitfalls'])}（这些不要直接提及，但要巧妙规避）

销售技巧：
- 使用"限时优惠"、"独家特权"等词汇
- 强调"性价比"、"保障全面"等概念
- 利用"很多客户都选择"等社会认同
- 创造紧迫感："错过就没有了"、"保费即将上调"
- 模糊处理不利条款，突出有利方面

当前对话轮次：{round_num + 1}"""

        # 构建用户提示词
        user_prompt = f"""基于以下对话历史，生成一句经纪人的回应：

对话历史：
{context}

请生成一句自然、有说服力的经纪人话术，要：
1. 符合对话上下文
2. 使用误导性销售技巧
3. 推动对话向成交方向发展
4. 回应要简洁，不超过50字

只返回话术内容，不要其他解释。"""

        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            response = await self.deepseek.ainvoke(messages)
            broker_message = str(response.content).strip()
            
            # 清理可能的markdown格式
            if "```" in broker_message:
                lines = broker_message.split("\n")
                broker_message = "\n".join([line for line in lines if not line.strip().startswith("```")])
            
            # 确保话术不为空
            if not broker_message or len(broker_message) < 5:
                broker_message = f"您好！我是{product['name']}的专属顾问，现在有特别优惠，您感兴趣吗？"
            
            return broker_message
            
        except Exception as e:
            logger.error(f"生成经纪人话术失败: {e}")
            # 返回默认话术
            return f"您好！我是{product['name']}的专属顾问，现在有特别优惠，您感兴趣吗？"


class AgencyAssistantAutoTester:
    """智能对话助理自动化测试器"""

    def __init__(self):
        self.assistant: Optional[AgencyAssistant] = None
        self.broker_ai: Optional[BrokerAI] = None
        self.current_user_id = 1
        self.current_session_id = 1
        self.conversation_history: List[ChatMessage] = []
        self.max_rounds = 20
        self.current_round = 0
        self.log_file = None
        self.is_auto_mode = False
        self.timeout_seconds = 60  # API调用超时时间
        self.max_retries = 3      # 最大重试次数

    async def setup(self):
        """初始化测试环境"""
        try:
            # 验证智能对话助理配置
            config.validate_assistant()
            print(f"{Fore.GREEN}✅ 智能对话助理配置验证成功{Style.RESET_ALL}")

            # 创建智能对话助理实例
            self.assistant = AgencyAssistant()
            print(f"{Fore.GREEN}✅ AgencyAssistant 初始化成功{Style.RESET_ALL}")

            # 创建经纪人AI实例
            self.broker_ai = BrokerAI()
            print(f"{Fore.GREEN}✅ 经纪人AI 初始化成功{Style.RESET_ALL}")

            # 创建日志文件
            self._setup_log_file()

        except Exception as e:
            print(f"{Fore.RED}❌ 初始化失败: {e}{Style.RESET_ALL}")
            if "DEEPSEEK_API_KEY" in str(e):
                print(f"{Fore.YELLOW}💡 请设置 AI_INSUR_DEEPSEEK_API_KEY 环境变量{Style.RESET_ALL}")
            if "QWEN_API_KEY" in str(e):
                print(f"{Fore.YELLOW}💡 请设置 AI_INSUR_QWEN_API_KEY 环境变量{Style.RESET_ALL}")
            raise

    def _setup_log_file(self, test_index: int = None):
        """设置日志文件"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if test_index is not None:
            self.log_file = log_dir / f"auto_dialogue_{timestamp}_test{test_index+1}.json"
        else:
            self.log_file = log_dir / f"auto_dialogue_{timestamp}.json"
        
        # 初始化日志文件
        log_data = {
            "session_info": {
                "user_id": self.current_user_id,
                "session_id": self.current_session_id,
                "start_time": datetime.now().isoformat(),
                "test_index": test_index
            },
            "conversation": []
        }
        
        with open(self.log_file, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2, default=self._json_serializer)
        
        print(f"{Fore.GREEN}✅ 日志文件已创建: {self.log_file}{Style.RESET_ALL}")

    def _json_serializer(self, obj):
        """JSON序列化器，处理numpy类型"""
        import numpy as np
        if isinstance(obj, (np.float32, np.float64)):
            return float(obj)
        elif isinstance(obj, (np.int32, np.int64)):
            return int(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    def _print_suggestions(self, suggestions):
        """打印结构化建议"""
        if not suggestions:
            return
        
        print(f"\n{Fore.MAGENTA}💡 智能对话建议:{Style.RESET_ALL}")
        print("─" * 50)
        
        # 打印提醒模块
        reminders = suggestions.get("reminders", {})
        if reminders:
            print(f"\n{Fore.CYAN}🔍 提醒模块:{Style.RESET_ALL}")
            
            # 信息要点
            key_points = reminders.get("key_points", [])
            if key_points:
                print(f"  {Fore.BLUE}📋 信息要点:{Style.RESET_ALL}")
                for i, point in enumerate(key_points, 1):
                    print(f"    {i}. {point}")
            
            # 潜在坑点
            potential_risks = reminders.get("potential_risks", [])
            if potential_risks:
                print(f"  {Fore.RED}⚠️  潜在坑点:{Style.RESET_ALL}")
                for i, risk in enumerate(potential_risks, 1):
                    print(f"    {i}. {risk}")
        
        # 打印提问模块
        questions = suggestions.get("questions", [])
        if questions:
            print(f"\n{Fore.GREEN}❓ 提问建议:{Style.RESET_ALL}")
            for i, q in enumerate(questions, 1):
                print(f"  {i}. {q}")
        
        print("─" * 50)

    def _log_conversation_round(self, round_num: int, broker_message: str, 
                               intent_analysis: Dict, suggestions: Dict, user_response: str, 
                               retrieved_pits: List[Dict] = None):
        """记录对话轮次到日志文件"""
        if not self.log_file:
            return
        
        try:
            # 读取现有日志
            with open(self.log_file, 'r', encoding='utf-8') as f:
                log_data = json.load(f)
            
            # 添加新的对话轮次
            round_data = {
                "round": round_num,
                "timestamp": datetime.now().isoformat(),
                "broker_message": broker_message,
                "intent_analysis": intent_analysis,
                "suggestions": suggestions,
                "user_response": user_response,
                "retrieved_pits": retrieved_pits or []
            }
            
            log_data["conversation"].append(round_data)
            
            # 写回文件
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, ensure_ascii=False, indent=2, default=self._json_serializer)
                
        except Exception as e:
            print(f"{Fore.RED}❌ 记录日志失败: {e}{Style.RESET_ALL}")

    async def cleanup(self):
        """清理测试环境"""
        try:
            # 完成日志文件
            if self.log_file and self.log_file.exists():
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    log_data = json.load(f)
                
                log_data["session_info"]["end_time"] = datetime.now().isoformat()
                log_data["session_info"]["total_rounds"] = self.current_round
                
                with open(self.log_file, 'w', encoding='utf-8') as f:
                    json.dump(log_data, f, ensure_ascii=False, indent=2, default=self._json_serializer)
                
                print(f"{Fore.GREEN}✅ 对话日志已保存: {self.log_file}{Style.RESET_ALL}")
            
            # 重置对话历史
            self.conversation_history.clear()
            self.current_round = 0
            self.is_auto_mode = False
            print(f"{Fore.YELLOW}🧹 已清理会话数据{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}❌ 清理失败: {e}{Style.RESET_ALL}")

    def print_banner(self):
        """打印程序横幅"""
        banner = f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════════╗
║                AI自动化对话测试程序                        ║
║              Auto AI Dialogue Tester                      ║
╚══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}

{Fore.GREEN}🎯 功能: 两个AI进行对抗性对话，自动记录到日志文件{Style.RESET_ALL}
{Fore.YELLOW}💡 提示: 输入 'help' 查看可用命令{Style.RESET_ALL}

{Fore.MAGENTA}🔥 开始自动化对话吧！用 'broker [次数] [回合数]' 启动AI对话{Style.RESET_ALL}
{Fore.CYAN}📋 工作流程: 经纪人AI → 意图分析 → 对话建议 → 用户AI回应（可多次测试）{Style.RESET_ALL}
{Fore.RED}⚠️  注意: 经纪人AI使用DeepSeek生成误导性话术，用户AI基于智能建议回应{Style.RESET_ALL}
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
  timeout [seconds]       - 查看/设置API超时时间（默认60秒）
  quit/exit               - 退出程序

{Fore.YELLOW}对话命令:{Style.RESET_ALL}
  broker [test_num] [turns]  - 开始自动化AI对话
                              test_num: 测试次数（默认1）
                              turns: 每次对话回合数（默认20）
                              示例: broker 3 10  # 进行3次测试，每次10回合
  history                 - 显示完整对话历史
  clear                   - 清空对话历史
  reset                   - 重置会话（新的session_id）

{Fore.YELLOW}AI角色说明:{Style.RESET_ALL}
  🤖 经纪人AI: 使用DeepSeek基于对话历史生成误导性推销话术
  🤖 用户AI: 基于智能建议进行回应，识别潜在风险
  💡 智能建议: 实时分析经纪人话术，提供风险提醒和提问建议

{Fore.YELLOW}对话流程:{Style.RESET_ALL}
  1. 经纪人AI基于对话历史生成误导性话术（DeepSeek）
  2. 系统进行意图识别分析
  3. 生成对话建议（风险提醒+提问建议）
  4. 用户AI基于建议生成回应
  5. 重复指定回合数，可进行多次测试

{Fore.YELLOW}日志记录:{Style.RESET_ALL}
  - 所有对话自动保存到 logs/ 目录
  - 文件名格式: auto_dialogue_YYYYMMDD_HHMMSS.json
  - 包含完整的对话内容、意图分析、建议和回应

{Fore.GREEN}💡 提示: 这是一个对抗性测试，观察AI如何识别和应对误导性话术{Style.RESET_ALL}
{Fore.CYAN}🚀 新特性: 完全自动化的AI对话，无需人工干预！{Style.RESET_ALL}
"""
        print(help_text)

    def print_conversation_history(self):
        """打印对话历史"""
        if not self.conversation_history:
            print(f"{Fore.YELLOW}⚠️  对话历史为空{Style.RESET_ALL}")
            return

        print(f"{Fore.CYAN}📜 对话历史 (共{len(self.conversation_history)}条):{Style.RESET_ALL}")
        print("─" * 60)
        for i, chat in enumerate(self.conversation_history, 1):
            role_color = Fore.BLUE if chat["role"] == ChatRole.USER else Fore.GREEN
            role_name = "AI用户" if chat["role"] == ChatRole.USER else "经纪人AI"
            role_icon = "🤖" if chat["role"] == ChatRole.USER else "🤵"
            print(f"  {i}. {role_icon} {role_color}{role_name}: {chat['content']}{Style.RESET_ALL}")

    def print_status(self):
        """打印当前状态"""
        print(f"{Fore.CYAN}📊 当前状态:{Style.RESET_ALL}")
        print(f"  用户ID: {Fore.YELLOW}{self.current_user_id}{Style.RESET_ALL}")
        print(f"  会话ID: {Fore.YELLOW}{self.current_session_id}{Style.RESET_ALL}")
        print(f"  当前轮次: {Fore.YELLOW}{self.current_round}{Style.RESET_ALL}")
        print(f"  对话轮次: {Fore.YELLOW}{len(self.conversation_history)}{Style.RESET_ALL}")
        
        auto_status = "🟢 运行中" if self.is_auto_mode else "🔴 已停止"
        print(f"  自动模式: {auto_status}")
        
        if self.broker_ai and self.broker_ai.current_product:
            product_name = self.broker_ai.current_product["name"]
            print(f"  推销产品: {Fore.RED}{product_name}{Style.RESET_ALL}")
        
        if self.log_file:
            print(f"  日志文件: {Fore.CYAN}{self.log_file.name}{Style.RESET_ALL}")
        
        print(f"  超时设置: {Fore.YELLOW}{self.timeout_seconds}秒 / {self.max_retries}次重试{Style.RESET_ALL}")

    def reset_session(self):
        """重置会话"""
        self.current_session_id += 1
        self.conversation_history.clear()
        self.current_round = 0
        self.is_auto_mode = False
        self._setup_log_file()
        print(f"{Fore.GREEN}✅ 会话已重置，新会话ID: {self.current_session_id}{Style.RESET_ALL}")

    async def auto_dialogue(self, test_num: int = 1, turns: int = 20):
        """执行自动化AI对话"""
        if not self.assistant or not self.broker_ai:
            print(f"{Fore.RED}❌ 助理或经纪人AI未初始化{Style.RESET_ALL}")
            return

        print(f"{Fore.CYAN}🚀 开始自动化AI对话...{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}📊 测试次数: {test_num}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}📊 每次回合数: {turns}{Style.RESET_ALL}")
        print(f"{Fore.RED}⚠️  经纪人AI将使用误导性话术{Style.RESET_ALL}")
        print(f"{Fore.GREEN}💡 用户AI将基于智能建议进行回应{Style.RESET_ALL}")
        print("─" * 60)

        self.is_auto_mode = True
        total_rounds = 0

        try:
            for test_index in range(test_num):
                # 检查是否需要中断
                if not self.is_auto_mode:
                    print(f"{Fore.YELLOW}⏹️  检测到停止信号，中断测试流程{Style.RESET_ALL}")
                    break
                
                print(f"\n{Fore.MAGENTA}{'='*70}{Style.RESET_ALL}")
                print(f"{Fore.MAGENTA}🧪 第 {test_index + 1}/{test_num} 次测试{Style.RESET_ALL}")
                print(f"{Fore.MAGENTA}{'='*70}{Style.RESET_ALL}")
                
                # 重置对话历史（每次测试独立）
                self.conversation_history.clear()
                self.current_round = 0
                
                # 为每次测试创建新的日志文件
                if test_num > 1:
                    self._setup_log_file(test_index)
                
                try:
                    # 执行单次测试
                    test_rounds = await self._execute_single_test(turns)
                    total_rounds += test_rounds
                    
                    print(f"\n{Fore.GREEN}✅ 第 {test_index + 1} 次测试完成，共 {test_rounds} 轮对话{Style.RESET_ALL}")
                    
                except Exception as e:
                    print(f"\n{Fore.RED}❌ 第 {test_index + 1} 次测试失败: {e}{Style.RESET_ALL}")
                    # 继续下一次测试，不中断整个流程
                    continue
                
                # 如果不是最后一次测试，等待一下
                if test_index < test_num - 1 and self.is_auto_mode:
                    print(f"{Fore.YELLOW}⏳ 等待3秒后开始下一次测试...{Style.RESET_ALL}")
                    await asyncio.sleep(3)

        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}⏹️  用户中断对话{Style.RESET_ALL}")
            self.is_auto_mode = False
        except Exception as e:
            print(f"\n{Fore.RED}❌ 对话过程中发生错误: {e}{Style.RESET_ALL}")
            self.is_auto_mode = False
        finally:
            print(f"\n{Fore.GREEN}🎉 自动化对话结束！{Style.RESET_ALL}")
            print(f"{Fore.CYAN}📊 总测试次数: {test_num}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}📊 总对话轮次: {total_rounds}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}📁 日志文件: {self.log_file}{Style.RESET_ALL}")

    async def _execute_single_test(self, turns: int) -> int:
        """执行单次测试"""
        completed_rounds = 0
        
        try:
            while completed_rounds < turns and self.is_auto_mode:
                completed_rounds += 1
                
                print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
                print(f"{Fore.CYAN}🔄 第 {completed_rounds}/{turns} 轮对话{Style.RESET_ALL}")
                print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")

                # 1. 经纪人AI生成话术
                broker_message = await self.broker_ai.generate_broker_message(
                    conversation_history=self.conversation_history,
                    round_num=completed_rounds-1
                )
                print(f"\n{Fore.GREEN}🤵 经纪人AI: {broker_message}{Style.RESET_ALL}")

                # 2. 添加到对话历史
                broker_chat: ChatMessage = {
                    "role": ChatRole.ASSISTANT,
                    "content": broker_message
                }
                self.conversation_history.append(broker_chat)

                # 3. 执行智能分析
                print(f"\n{Fore.BLUE}🧠 执行智能分析...{Style.RESET_ALL}")
                
                request: AssistantRequest = {
                    "user_id": self.current_user_id,
                    "session_id": self.current_session_id,
                    "broker_input": broker_message,
                    "conversation_history": self.conversation_history[:-1].copy()  # 不包含刚添加的消息
                }

                intent_analysis = None
                suggestions = None
                user_response = None
                retrieved_pits = None

                # 执行助理分析（添加超时处理和重试机制）
                retry_count = 0
                
                while retry_count < self.max_retries:
                    try:
                        # 设置超时时间
                        async with asyncio.timeout(self.timeout_seconds):
                            async for response in self.assistant.assist_conversation(request):
                                response_type = response.get("type", "")
                                
                                if response_type == "intent_analysis":
                                    intent_analysis = response.get("intent_analysis", {})
                                    print(f"{Fore.CYAN}✅ 意图分析完成{Style.RESET_ALL}")
                                
                                elif response_type == "suggestions":
                                    suggestions = response.get("suggestions", {})
                                    retrieved_pits = response.get("retrieved_pits", [])
                                    print(f"{Fore.MAGENTA}✅ 对话建议生成完成{Style.RESET_ALL}")
                                                                        
                                    # 显示检索到的坑点信息
                                    if retrieved_pits:
                                        print(f"{Fore.YELLOW}🔍 检索到 {len(retrieved_pits)} 个相关坑点:{Style.RESET_ALL}")
                                        for i, pit in enumerate(retrieved_pits, 1):
                                            title = pit.get("title", "未知标题")
                                            similarity = pit.get("similarity", 0)
                                            category = pit.get("category", "未分类")
                                            example = pit.get("example", "")
                                            reason = pit.get("reason", "")
                                            
                                            print(f"   {i}. 【{category}】{title} (相似度: {similarity:.3f})")
                                            if example:
                                                print(f"      📝 示例: {example[:100]}{'...' if len(example) > 100 else ''}")
                                            if reason:
                                                print(f"      ⚠️  原因: {reason[:100]}{'...' if len(reason) > 100 else ''}")
                                            print()  # 空行分隔
                                    else:
                                        print(f"{Fore.YELLOW}🔍 未检索到相关坑点{Style.RESET_ALL}")
                                    
                                    # 显示生成的建议
                                    self._print_suggestions(suggestions)
                                
                                elif response_type == "user_response":
                                    user_response = response.get("user_response", "")
                                    print(f"{Fore.GREEN}✅ 用户AI回应生成完成{Style.RESET_ALL}")
                                
                                elif response_type == "error":
                                    error_msg = response.get("error", "未知错误")
                                    print(f"{Fore.RED}❌ 分析过程中发生错误: {error_msg}{Style.RESET_ALL}")
                                    break
                        
                        # 如果成功完成，跳出重试循环
                        break
                    
                    except asyncio.TimeoutError:
                        retry_count += 1
                        if retry_count < self.max_retries:
                            print(f"{Fore.YELLOW}⚠️  分析超时（{self.timeout_seconds}秒），第 {retry_count} 次重试...{Style.RESET_ALL}")
                            await asyncio.sleep(2)  # 等待2秒后重试
                        else:
                            print(f"{Fore.RED}❌ 分析超时（{self.timeout_seconds}秒），已重试 {self.max_retries} 次，跳过本轮对话{Style.RESET_ALL}")
                            # 生成默认回应以避免程序停止
                            user_response = "抱歉，我现在有点忙，稍后再聊。"
                            intent_analysis = {"讨论主题": ["对话中断"], "涉及术语": [], "涉及产品": [], "经纪人阶段性意图识别": ["对话中断"], "经纪人本句话意图识别": ["对话中断"], "用户当下需求": ["对话中断"]}
                            suggestions = {"reminders": {"key_points": ["对话被中断"], "potential_risks": []}, "questions": ["稍后继续对话"]}
                            retrieved_pits = []
                    
                    except Exception as e:
                        retry_count += 1
                        if retry_count < self.max_retries:
                            print(f"{Fore.YELLOW}⚠️  分析过程中发生异常: {e}，第 {retry_count} 次重试...{Style.RESET_ALL}")
                            await asyncio.sleep(2)  # 等待2秒后重试
                        else:
                            print(f"{Fore.RED}❌ 分析过程中发生异常: {e}，已重试 {self.max_retries} 次，跳过本轮对话{Style.RESET_ALL}")
                            # 生成默认回应以避免程序停止
                            user_response = "抱歉，我现在有点忙，稍后再聊。"
                            intent_analysis = {"讨论主题": ["对话中断"], "涉及术语": [], "涉及产品": [], "经纪人阶段性意图识别": ["对话中断"], "经纪人本句话意图识别": ["对话中断"], "用户当下需求": ["对话中断"]}
                            suggestions = {"reminders": {"key_points": ["对话被中断"], "potential_risks": []}, "questions": ["稍后继续对话"]}
                            retrieved_pits = []

                # 4. 显示用户AI回应
                if user_response:
                    print(f"\n{Fore.BLUE}🤖 用户AI: {user_response}{Style.RESET_ALL}")
                    
                    # 添加到对话历史
                    user_chat: ChatMessage = {
                        "role": ChatRole.USER,
                        "content": user_response
                    }
                    self.conversation_history.append(user_chat)

                # 5. 记录到日志
                if user_response:  # 只要有用户回应就记录
                    # 确保有默认值
                    if not intent_analysis:
                        intent_analysis = {"讨论主题": ["未知"], "涉及术语": [], "涉及产品": [], "经纪人阶段性意图识别": ["未知"], "经纪人本句话意图识别": ["未知"], "用户当下需求": ["未知"]}
                    if not suggestions:
                        suggestions = {"reminders": {"key_points": [], "potential_risks": []}, "questions": []}
                    if not retrieved_pits:
                        retrieved_pits = []
                    
                    self._log_conversation_round(
                        completed_rounds, 
                        broker_message, 
                        intent_analysis, 
                        suggestions, 
                        user_response,
                        retrieved_pits
                    )

                # 6. 显示进度
                progress = (completed_rounds / turns) * 100
                print(f"\n{Fore.YELLOW}📈 进度: {progress:.1f}% ({completed_rounds}/{turns}){Style.RESET_ALL}")

                # 7. 短暂延迟，让用户观察
                await asyncio.sleep(1)
                
                # 8. 检查是否需要中断
                if not self.is_auto_mode:
                    print(f"{Fore.YELLOW}⏹️  检测到停止信号，中断当前测试{Style.RESET_ALL}")
                    break
        
        except Exception as e:
            print(f"\n{Fore.RED}❌ 单次测试过程中发生错误: {e}{Style.RESET_ALL}")
        
        return completed_rounds

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

                    elif command == "clear":
                        self.conversation_history.clear()
                        self.current_round = 0
                        print(f"{Fore.GREEN}✅ 对话历史已清空{Style.RESET_ALL}")

                    elif command == "reset":
                        self.reset_session()

                    elif command == "timeout":
                        if len(parts) >= 2:
                            try:
                                new_timeout = int(parts[1])
                                if new_timeout > 0:
                                    self.timeout_seconds = new_timeout
                                    print(f"{Fore.GREEN}✅ 超时时间已设置为 {new_timeout} 秒{Style.RESET_ALL}")
                                else:
                                    print(f"{Fore.RED}❌ 超时时间必须大于0{Style.RESET_ALL}")
                            except ValueError:
                                print(f"{Fore.RED}❌ 超时时间必须是数字{Style.RESET_ALL}")
                        else:
                            print(f"{Fore.CYAN}当前超时设置:{Style.RESET_ALL}")
                            print(f"  超时时间: {self.timeout_seconds} 秒")
                            print(f"  最大重试: {self.max_retries} 次")
                            print(f"{Fore.YELLOW}💡 使用 'timeout <秒数>' 来调整超时时间{Style.RESET_ALL}")

                    elif command == "broker":
                        if self.is_auto_mode:
                            print(f"{Fore.YELLOW}⚠️  自动对话正在进行中，请等待完成{Style.RESET_ALL}")
                            continue
                        
                        # 解析参数
                        test_num = 1  # 默认测试1次
                        turns = 20    # 默认每次20回合
                        
                        if len(parts) >= 2:
                            try:
                                test_num = int(parts[1])
                                if test_num < 1:
                                    print(f"{Fore.RED}❌ 测试次数必须大于0{Style.RESET_ALL}")
                                    continue
                            except ValueError:
                                print(f"{Fore.RED}❌ 测试次数必须是数字{Style.RESET_ALL}")
                                continue
                        
                        if len(parts) >= 3:
                            try:
                                turns = int(parts[2])
                                if turns < 1:
                                    print(f"{Fore.RED}❌ 回合数必须大于0{Style.RESET_ALL}")
                                    continue
                            except ValueError:
                                print(f"{Fore.RED}❌ 回合数必须是数字{Style.RESET_ALL}")
                                continue
                        
                        await self.auto_dialogue(test_num=test_num, turns=turns)

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
    tester = AgencyAssistantAutoTester()

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