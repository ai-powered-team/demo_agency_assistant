#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
保险坑点提取运行脚本
提供简化的交互式界面
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from get_pits import InsurancePitExtractor


def check_api_key():
    """检查API密钥"""
    api_key = os.getenv('DEEPSEEK_API_KEY')
    if not api_key:
        print("❌ 未设置DeepSeek API密钥")
        print("\n请选择一种方式设置API密钥：")
        print("1. 设置环境变量：export DEEPSEEK_API_KEY='your_api_key'")
        print("2. 手动输入（本次运行有效）")
        print("3. 退出")
        
        while True:
            choice = input("\n请选择 (1-3): ").strip()
            
            if choice == '1':
                print("\n请在终端中运行：")
                print("export DEEPSEEK_API_KEY='your_api_key'")
                print("然后重新运行此脚本")
                return None
            elif choice == '2':
                api_key = input("请输入DeepSeek API密钥: ").strip()
                if api_key:
                    return api_key
                else:
                    print("❌ API密钥不能为空")
                    continue
            elif choice == '3':
                return None
            else:
                print("❌ 无效选择，请输入 1-3")
    
    return api_key


def check_text_files():
    """检查文本文件"""
    text_dir = Path("../data/text")
    if not text_dir.exists():
        print("❌ 文本目录不存在")
        print("请先运行文章内容提取工具：")
        print("   cd tools")
        print("   python run_content_extraction.py")
        return False, 0
    
    txt_files = list(text_dir.glob("*.txt"))
    txt_files = [f for f in txt_files if not f.name.startswith('extraction_report')]
    
    if not txt_files:
        print("❌ 未找到任何文本文件")
        print("请先运行文章内容提取工具")
        return False, 0
    
    return True, len(txt_files)


def estimate_cost(file_count: int, avg_chars_per_file: int = 3000):
    """估算API调用成本"""
    # DeepSeek收费大约是 $0.14/1M input tokens
    # 1个中文字符大约等于1.5个token
    total_chars = file_count * avg_chars_per_file
    total_tokens = total_chars * 1.5  # 输入token
    output_tokens = file_count * 500  # 估计每个文件输出500个token
    
    total_cost = (total_tokens + output_tokens) / 1000000 * 0.14
    
    return total_cost


def main():
    """主函数"""
    print("🚀 保险坑点提取工具")
    print("=" * 50)
    
    # 检查API密钥
    print("🔑 检查API密钥...")
    api_key = check_api_key()
    if not api_key:
        print("👋 再见！")
        return 0
    
    print("✅ API密钥已设置")
    
    # 检查文本文件
    print("\n📁 检查文本文件...")
    has_files, file_count = check_text_files()
    if not has_files:
        return 1
    
    print(f"✅ 找到 {file_count} 个文本文件")
    
    # 估算成本
    estimated_cost = estimate_cost(file_count)
    print(f"💰 预估API成本: ${estimated_cost:.3f} USD")
    
    # 选择处理模式
    print("\n请选择处理模式:")
    print("1. 测试模式 (处理前3个文件)")
    print("2. 部分处理 (自定义数量)")
    print("3. 全部处理 (处理所有文件)")
    print("4. 退出")
    
    while True:
        choice = input("\n请输入选择 (1-4): ").strip()
        
        if choice == '1':
            max_files = 3
            print("🧪 选择测试模式，将处理前3个文件")
            break
        elif choice == '2':
            try:
                max_files = int(input(f"请输入要处理的文件数量 (1-{file_count}): "))
                if max_files <= 0 or max_files > file_count:
                    print(f"❌ 请输入1到{file_count}之间的数字")
                    continue
                print(f"📊 将处理前 {max_files} 个文件")
                break
            except ValueError:
                print("❌ 请输入有效的数字")
                continue
        elif choice == '3':
            max_files = None
            print("📚 将处理所有文件")
            break
        elif choice == '4':
            print("👋 再见！")
            return 0
        else:
            print("❌ 无效选择，请输入 1-4")
    
    # 显示处理信息
    files_to_process = max_files if max_files else file_count
    estimated_time = files_to_process * 10  # 每个文件大约10秒
    actual_cost = estimate_cost(files_to_process)
    
    print(f"\n📋 处理信息:")
    print(f"   • 文件数量: {files_to_process}")
    print(f"   • 预估时间: {estimated_time//60}分{estimated_time%60}秒")
    print(f"   • 预估成本: ${actual_cost:.3f} USD")
    print(f"   • 输出文件: data/insurance_pits_extracted.json")
    
    # 确认开始处理
    confirm = input("\n确认开始处理？(y/N): ").strip().lower()
    if confirm not in ['y', 'yes']:
        print("👋 已取消处理")
        return 0
    
    # 开始处理
    start_time = datetime.now()
    
    try:
        print("\n" + "="*60)
        extractor = InsurancePitExtractor(api_key=api_key, text_dir="../data/text")
        results = extractor.process_all_files(max_files=max_files)
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        # 保存结果
        if results:
            output_file = "../data/insurance_pits_extracted.json"
            extractor.save_results(results, output_file)
        
        # 显示最终统计
        extractor.print_summary(results)
        
        print(f"\n⏱️  实际耗时: {duration}")
        
        if results:
            print(f"🎉 处理成功完成！")
            print(f"📊 提取结果:")
            print(f"   • 总坑点数: {sum(len(cat['items']) for cat in results)}")
            print(f"   • 分类数: {len(results)}")
            print(f"   • 输出文件: {output_file}")
            
            # 显示分类统计
            print(f"\n📋 各分类坑点统计:")
            for category_data in results:
                count = len(category_data['items'])
                print(f"   • {category_data['category']}: {count} 个")
                
            return 0
        else:
            print("ℹ️  未提取到任何坑点数据")
            return 1
            
    except KeyboardInterrupt:
        print(f"\n\n⚠️  用户中断处理")
        print(f"⏱️  已运行: {datetime.now() - start_time}")
        return 1
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 