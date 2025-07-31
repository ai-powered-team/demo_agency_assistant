#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
深蓝保文章内容提取运行脚本
提供简化的命令行界面
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from extract_article_content import ArticleContentExtractor


def find_latest_json_file():
    """查找最新的JSON数据文件"""
    data_dir = Path("../data")
    if not data_dir.exists():
        return None
    
    # 查找所有避坑指南的JSON文件
    json_files = list(data_dir.glob("shenlanbao_避坑指南_*.json"))
    if not json_files:
        # 查找其他shenlanbao相关文件
        json_files = list(data_dir.glob("shenlanbao_*.json"))
    
    if not json_files:
        return None
    
    # 返回最新的文件
    return max(json_files, key=lambda x: x.stat().st_mtime)


def main():
    """主函数"""
    print("🚀 深蓝保文章内容提取工具")
    print("=" * 50)
    
    # 自动查找JSON文件
    json_file = find_latest_json_file()
    if not json_file:
        print("❌ 未找到JSON数据文件")
        print("请先运行爬虫获取文章列表：")
        print("   cd tools")
        print("   python run_crawler.py --category 避坑指南")
        return 1
    
    print(f"📄 找到数据文件: {json_file.name}")
    
    # 询问用户选择
    print("\n请选择处理模式:")
    print("1. 测试模式 (处理前5篇文章)")
    print("2. 部分处理 (自定义数量)")
    print("3. 全部处理 (处理所有文章)")
    print("4. 退出")
    
    while True:
        choice = input("\n请输入选择 (1-4): ").strip()
        
        if choice == '1':
            max_articles = 5
            print("🧪 选择测试模式，将处理前5篇文章")
            break
        elif choice == '2':
            try:
                max_articles = int(input("请输入要处理的文章数量: "))
                if max_articles <= 0:
                    print("❌ 请输入大于0的数字")
                    continue
                print(f"📊 将处理前 {max_articles} 篇文章")
                break
            except ValueError:
                print("❌ 请输入有效的数字")
                continue
        elif choice == '3':
            max_articles = None
            print("📚 将处理所有文章")
            break
        elif choice == '4':
            print("👋 再见！")
            return 0
        else:
            print("❌ 无效选择，请输入 1-4")
    
    # 确认开始处理
    print(f"\n📁 输出目录: data/text")
    print(f"🔄 请求间隔: 1秒")
    
    confirm = input("\n确认开始处理？(y/N): ").strip().lower()
    if confirm not in ['y', 'yes']:
        print("👋 已取消处理")
        return 0
    
    # 开始处理
    start_time = datetime.now()
    
    try:
        extractor = ArticleContentExtractor(output_dir="../data/text")
        result = extractor.process_articles_from_json(str(json_file), max_articles)
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        if result['success']:
            print(f"\n✅ 处理成功完成！")
            print(f"⏱️  耗时: {duration}")
            print(f"📊 统计:")
            print(f"   - 总计: {result['total']} 篇")
            print(f"   - 成功: {result['success_count']} 篇")
            print(f"   - 失败: {result['failed_count']} 篇")
            print(f"   - 成功率: {(result['success_count']/result['total']*100):.1f}%")
            
            if result['failed_count'] > 0:
                print(f"\n⚠️  有 {result['failed_count']} 篇文章处理失败")
                print("详细信息请查看处理报告")
            
            print(f"\n📁 文本文件保存在: data/text/")
            return 0
        else:
            print(f"❌ 处理失败: {result.get('error', '未知错误')}")
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