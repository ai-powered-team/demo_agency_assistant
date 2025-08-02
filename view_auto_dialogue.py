#!/usr/bin/env python3
"""
自动化对话日志查看器

用于查看 test_agency_assistant_auto.py 生成的对话日志文件。

使用方法:
    python view_auto_dialogue.py [日志文件名]

功能特性:
    📊 显示对话统计信息
    💬 格式化显示对话内容
    🧠 显示意图分析结果
    💡 显示对话建议
    🔍 搜索特定内容
"""

import json
import sys
import argparse
from pathlib import Path
from typing import Dict, Any, List

# 尝试导入 colorama
try:
    import colorama
    from colorama import Fore, Back, Style
    colorama.init()
    HAS_COLORAMA = True
except ImportError:
    class _DummyColor:
        def __getattr__(self, name):
            return ""
    Fore = _DummyColor()
    Back = _DummyColor()
    Style = _DummyColor()
    HAS_COLORAMA = False


def find_latest_log() -> Path:
    """查找最新的日志文件"""
    log_dir = Path("logs")
    if not log_dir.exists():
        print(f"{Fore.RED}❌ logs目录不存在{Style.RESET_ALL}")
        return None
    
    log_files = list(log_dir.glob("auto_dialogue_*.json"))
    if not log_files:
        print(f"{Fore.RED}❌ 未找到自动化对话日志文件{Style.RESET_ALL}")
        return None
    
    # 按修改时间排序，返回最新的
    latest_log = max(log_files, key=lambda f: f.stat().st_mtime)
    return latest_log


def load_log_file(log_path: Path) -> Dict[str, Any]:
    """加载日志文件"""
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"{Fore.RED}❌ 加载日志文件失败: {e}{Style.RESET_ALL}")
        return None


def print_session_info(session_info: Dict[str, Any]):
    """打印会话信息"""
    print(f"\n{Fore.CYAN}📊 会话信息:{Style.RESET_ALL}")
    print("─" * 50)
    print(f"  用户ID: {session_info.get('user_id', 'N/A')}")
    print(f"  会话ID: {session_info.get('session_id', 'N/A')}")
    print(f"  开始时间: {session_info.get('start_time', 'N/A')}")
    print(f"  结束时间: {session_info.get('end_time', 'N/A')}")
    print(f"  最大轮次: {session_info.get('max_rounds', 'N/A')}")
    print(f"  实际轮次: {session_info.get('total_rounds', 'N/A')}")


def print_conversation_summary(conversation: List[Dict[str, Any]]):
    """打印对话摘要"""
    print(f"\n{Fore.CYAN}📈 对话摘要:{Style.RESET_ALL}")
    print("─" * 50)
    print(f"  总轮次: {len(conversation)}")
    
    if conversation:
        first_round = conversation[0]
        last_round = conversation[-1]
        print(f"  第一轮时间: {first_round.get('timestamp', 'N/A')}")
        print(f"  最后一轮时间: {last_round.get('timestamp', 'N/A')}")


def print_round_details(round_data: Dict[str, Any], round_num: int):
    """打印单轮对话详情"""
    print(f"\n{Fore.YELLOW}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}🔄 第 {round_num} 轮对话{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}{'='*60}{Style.RESET_ALL}")
    
    # 经纪人消息
    broker_message = round_data.get('broker_message', '')
    print(f"\n{Fore.GREEN}🤵 经纪人AI:{Style.RESET_ALL}")
    print(f"  {broker_message}")
    
    # 意图分析
    intent_analysis = round_data.get('intent_analysis', {})
    if intent_analysis:
        print(f"\n{Fore.CYAN}🧠 意图分析:{Style.RESET_ALL}")
        for key, value in intent_analysis.items():
            if isinstance(value, list):
                value_str = ", ".join(value) if value else "无"
            else:
                value_str = str(value) if value else "未识别"
            print(f"  {key}: {Fore.YELLOW}{value_str}{Style.RESET_ALL}")
    
    # 对话建议
    suggestions = round_data.get('suggestions', {})
    if suggestions:
        print(f"\n{Fore.MAGENTA}💡 对话建议:{Style.RESET_ALL}")
        
        # 提醒模块
        reminders = suggestions.get('reminders', {})
        if reminders:
            print(f"  {Fore.CYAN}🔍 提醒模块:{Style.RESET_ALL}")
            
            key_points = reminders.get('key_points', [])
            if key_points:
                print(f"    📋 信息要点:")
                for i, point in enumerate(key_points, 1):
                    print(f"      {i}. {point}")
            
            potential_risks = reminders.get('potential_risks', [])
            if potential_risks:
                print(f"    ⚠️  潜在坑点:")
                for i, risk in enumerate(potential_risks, 1):
                    print(f"      {i}. {risk}")
        
        # 提问模块
        questions = suggestions.get('questions', [])
        if questions:
            print(f"  {Fore.GREEN}❓ 提问建议:{Style.RESET_ALL}")
            for i, q in enumerate(questions, 1):
                print(f"    {i}. {q}")
    
    # 用户回应
    user_response = round_data.get('user_response', '')
    if user_response:
        print(f"\n{Fore.BLUE}🤖 用户AI:{Style.RESET_ALL}")
        print(f"  {user_response}")


def print_conversation_only(conversation: List[Dict[str, Any]]):
    """只显示对话内容（简化版）"""
    print(f"\n{Fore.CYAN}💬 对话内容:{Style.RESET_ALL}")
    print("─" * 60)
    
    for i, round_data in enumerate(conversation, 1):
        print(f"\n{Fore.YELLOW}第 {i} 轮:{Style.RESET_ALL}")
        
        broker_message = round_data.get('broker_message', '')
        user_response = round_data.get('user_response', '')
        
        print(f"{Fore.GREEN}🤵 经纪人: {broker_message}{Style.RESET_ALL}")
        print(f"{Fore.BLUE}🤖 用户: {user_response}{Style.RESET_ALL}")


def search_in_conversation(conversation: List[Dict[str, Any]], keyword: str):
    """在对话中搜索关键词"""
    print(f"\n{Fore.CYAN}🔍 搜索关键词: '{keyword}'{Style.RESET_ALL}")
    print("─" * 60)
    
    found_rounds = []
    
    for i, round_data in enumerate(conversation, 1):
        broker_message = round_data.get('broker_message', '')
        user_response = round_data.get('user_response', '')
        
        if keyword.lower() in broker_message.lower() or keyword.lower() in user_response.lower():
            found_rounds.append(i)
            print(f"\n{Fore.YELLOW}第 {i} 轮包含关键词:{Style.RESET_ALL}")
            if keyword.lower() in broker_message.lower():
                print(f"{Fore.GREEN}🤵 经纪人: {broker_message}{Style.RESET_ALL}")
            if keyword.lower() in user_response.lower():
                print(f"{Fore.BLUE}🤖 用户: {user_response}{Style.RESET_ALL}")
    
    if not found_rounds:
        print(f"{Fore.YELLOW}未找到包含关键词的对话{Style.RESET_ALL}")
    else:
        print(f"\n{Fore.CYAN}共找到 {len(found_rounds)} 轮对话包含关键词{Style.RESET_ALL}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="查看自动化对话日志")
    parser.add_argument("log_file", nargs="?", help="日志文件路径")
    parser.add_argument("--simple", "-s", action="store_true", help="只显示对话内容")
    parser.add_argument("--search", help="搜索关键词")
    parser.add_argument("--list", "-l", action="store_true", help="列出所有日志文件")
    
    args = parser.parse_args()
    
    # 列出所有日志文件
    if args.list:
        log_dir = Path("logs")
        if log_dir.exists():
            log_files = list(log_dir.glob("auto_dialogue_*.json"))
            if log_files:
                print(f"{Fore.CYAN}📁 可用的日志文件:{Style.RESET_ALL}")
                for log_file in sorted(log_files, key=lambda f: f.stat().st_mtime, reverse=True):
                    mtime = log_file.stat().st_mtime
                    from datetime import datetime
                    mtime_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
                    print(f"  {log_file.name} ({mtime_str})")
            else:
                print(f"{Fore.YELLOW}未找到日志文件{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}logs目录不存在{Style.RESET_ALL}")
        return
    
    # 确定日志文件路径
    if args.log_file:
        log_path = Path(args.log_file)
        if not log_path.exists():
            print(f"{Fore.RED}❌ 指定的日志文件不存在: {args.log_file}{Style.RESET_ALL}")
            return
    else:
        log_path = find_latest_log()
        if not log_path:
            return
    
    print(f"{Fore.CYAN}📖 正在加载日志文件: {log_path.name}{Style.RESET_ALL}")
    
    # 加载日志数据
    log_data = load_log_file(log_path)
    if not log_data:
        return
    
    session_info = log_data.get('session_info', {})
    conversation = log_data.get('conversation', [])
    
    # 显示会话信息
    print_session_info(session_info)
    
    # 显示对话摘要
    print_conversation_summary(conversation)
    
    # 搜索功能
    if args.search:
        search_in_conversation(conversation, args.search)
        return
    
    # 显示对话内容
    if args.simple:
        print_conversation_only(conversation)
    else:
        # 显示详细对话
        for i, round_data in enumerate(conversation, 1):
            print_round_details(round_data, i)
    
    print(f"\n{Fore.GREEN}✅ 日志查看完成{Style.RESET_ALL}")


if __name__ == "__main__":
    main() 