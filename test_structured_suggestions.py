#!/usr/bin/env python3
"""
测试结构化建议功能

这个脚本用于测试新的提醒模块和提问模块功能
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from agent.agency_assistant import AgencyAssistant
from util import ChatMessage, ChatRole

async def test_structured_suggestions():
    """测试结构化建议功能"""
    print("🧪 测试结构化建议功能")
    print("=" * 50)
    
    try:
        # 创建助理实例
        assistant = AgencyAssistant()
        
        # 测试用例
        test_cases = [
            {
                "name": "费率误导测试",
                "broker_input": "我们这款重疾险首年保费只要99元，性价比很高，收益也很可观！",
                "conversation_history": []
            },
            {
                "name": "理赔条件测试", 
                "broker_input": "这款医疗险可以报销100万医疗费，保障很全面。",
                "conversation_history": []
            },
            {
                "name": "产品推荐测试",
                "broker_input": "根据您的情况，我推荐这款产品，它是市面上最好的选择。",
                "conversation_history": []
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n📋 测试用例 {i}: {test_case['name']}")
            print("-" * 40)
            print(f"经纪人话语: {test_case['broker_input']}")
            
            # 构建请求
            request = {
                "user_id": 1,
                "session_id": 1,
                "broker_input": test_case["broker_input"],
                "conversation_history": test_case["conversation_history"]
            }
            
            print("\n🔄 正在生成结构化建议...")
            
            # 执行分析
            suggestions_found = False
            async for response in assistant.assist_conversation(request):
                if response.get("type") == "suggestions":
                    suggestions = response.get("data", {}).get("suggestions", {})
                    suggestions_found = True
                    
                    print("\n💡 生成的结构化建议:")
                    print("=" * 60)
                    
                    # 显示提醒模块
                    reminders = suggestions.get("reminders", {})
                    if reminders:
                        print("\n🔍 提醒模块 (解读经纪人的话):")
                        print("-" * 30)
                        
                        key_points = reminders.get("key_points", [])
                        if key_points:
                            print("\n📋 信息要点:")
                            for j, point in enumerate(key_points, 1):
                                print(f"  {j}. {point}")
                        
                        potential_risks = reminders.get("potential_risks", [])
                        if potential_risks:
                            print("\n⚠️  潜在坑点:")
                            for j, risk in enumerate(potential_risks, 1):
                                print(f"  {j}. {risk}")
                    
                    # 显示提问模块（简化）
                    questions = suggestions.get("questions", [])
                    if questions:
                        print("\n❓ 提问建议:")
                        print("-" * 20)
                        for j, q in enumerate(questions, 1):
                            print(f"  {j}. {q}")
                    
                    print("=" * 60)
                    break
            
            if not suggestions_found:
                print("❌ 未生成建议")
            
            print("\n" + "="*50)
    
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

def main():
    """主函数"""
    print("结构化建议功能测试")
    print("测试新的提醒模块和提问模块功能")
    print()
    
    # 运行测试
    asyncio.run(test_structured_suggestions())

if __name__ == "__main__":
    main() 