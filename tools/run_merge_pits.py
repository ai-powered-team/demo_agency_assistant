#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
保险坑点合并运行脚本
简化的交互式界面
"""

import os
import sys
from pathlib import Path

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from merge_pits import PitsMerger


def check_files():
    """检查输入文件"""
    extracted_file = Path("../data/insurance_pits_extracted.json")
    existing_file = Path("../data/pit_types_new.json")
    
    files_info = []
    
    # 检查提取文件
    if extracted_file.exists():
        try:
            import json
            with open(extracted_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            total_pits = data.get('total_pits', 0)
            files_info.append(f"✅ 提取文件: {extracted_file.name} ({total_pits} 个坑点)")
        except:
            files_info.append(f"⚠️  提取文件: {extracted_file.name} (格式错误)")
    else:
        files_info.append(f"❌ 提取文件: {extracted_file.name} (不存在)")
    
    # 检查现有文件
    if existing_file.exists():
        try:
            import json
            with open(existing_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, list):
                total_pits = sum(len(cat.get('items', [])) for cat in data)
                files_info.append(f"✅ 现有文件: {existing_file.name} ({total_pits} 个坑点)")
            else:
                files_info.append(f"⚠️  现有文件: {existing_file.name} (格式不明)")
        except:
            files_info.append(f"⚠️  现有文件: {existing_file.name} (格式错误)")
    else:
        files_info.append(f"❌ 现有文件: {existing_file.name} (不存在)")
    
    return files_info, extracted_file.exists() or existing_file.exists()


def main():
    """主函数"""
    print("🔗 保险坑点合并工具")
    print("=" * 50)
    
    # 检查文件
    print("📁 检查输入文件...")
    files_info, has_files = check_files()
    
    for info in files_info:
        print(f"  {info}")
    
    if not has_files:
        print("\n❌ 没有可用的输入文件")
        print("请确保至少有一个文件存在：")
        print("  • ../data/insurance_pits_extracted.json")
        print("  • ../data/pit_types_new.json")
        return 1
    
    # 输出文件配置
    output_file = Path("../data/insurance_pits_merged.json")
    
    print(f"\n📄 输出配置:")
    print(f"  • 输出文件: {output_file}")
    
    if output_file.exists():
        print(f"  ⚠️  输出文件已存在，将创建备份")
    
    # 显示合并计划
    print(f"\n📋 合并计划:")
    print(f"  1. 加载现有坑点数据")
    print(f"  2. 加载AI提取的坑点数据")
    print(f"  3. 按分类合并数据")
    print(f"  4. 去除重复项（基于标题）")
    print(f"  5. 重新分配编号")
    print(f"  6. 保存到新文件")
    
    # 确认合并
    confirm = input(f"\n确认开始合并？(y/N): ").strip().lower()
    if confirm not in ['y', 'yes']:
        print("👋 已取消合并")
        return 0
    
    # 执行合并
    print(f"\n{'='*60}")
    
    try:
        merger = PitsMerger()
        success = merger.merge_files(
            "../data/insurance_pits_extracted.json",
            "../data/pit_types_new.json",
            str(output_file)
        )
        
        if success:
            print(f"\n🎉 合并成功完成！")
            print(f"📁 输出文件: {output_file}")
            
            # 验证结果
            print(f"\n🔍 快速验证:")
            try:
                import json
                with open(output_file, 'r', encoding='utf-8') as f:
                    result = json.load(f)
                
                print(f"  • 总分类数: {result.get('total_categories', 0)}")
                print(f"  • 总坑点数: {result.get('total_pits', 0)}")
                print(f"  • 合并时间: {result.get('merge_time', 'N/A')}")
                
                if 'categories' in result:
                    print(f"\n📊 分类明细:")
                    for cat in result['categories']:
                        name = cat.get('category', 'Unknown')
                        count = len(cat.get('items', []))
                        print(f"    • {name}: {count} 个")
                
            except Exception as e:
                print(f"  ❌ 验证失败: {e}")
            
            # 后续建议
            print(f"\n💡 后续操作建议:")
            print(f"1. 人工审核合并结果，确保数据质量")
            print(f"2. 检查是否有需要进一步分类的坑点")
            print(f"3. 验证编号是否连续且正确")
            print(f"4. 考虑是否需要优化坑点描述")
            
            return 0
        else:
            print(f"\n❌ 合并失败")
            return 1
            
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main()) 