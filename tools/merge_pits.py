#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
保险坑点合并脚本
将 insurance_pits_extracted.json 和 pit_types_new.json 合并，并重新分配编号
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any


class PitsMerger:
    """保险坑点合并器"""
    
    def __init__(self):
        self.categories = [
            "产品比较与费率相关坑点",
            "保障责任与理赔条款相关坑点",
            "销售行为与专业伦理相关坑点",
            "续保、停售与产品稳定性相关坑点",
            "核保与健康告知相关坑点",
            "其他坑点"
        ]
    
    def load_json_file(self, file_path: str) -> Any:
        """加载JSON文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"❌ 文件不存在: {file_path}")
            return None
        except json.JSONDecodeError as e:
            print(f"❌ JSON格式错误: {file_path} - {e}")
            return None
        except Exception as e:
            print(f"❌ 读取文件失败: {file_path} - {e}")
            return None
    
    def normalize_extracted_data(self, extracted_data: Dict) -> List[Dict]:
        """标准化提取的数据格式"""
        if not extracted_data or 'categories' not in extracted_data:
            return []
        
        return extracted_data['categories']
    
    def normalize_existing_data(self, existing_data: List) -> List[Dict]:
        """标准化现有数据格式"""
        if not existing_data or not isinstance(existing_data, list):
            return []
        
        return existing_data
    
    def merge_categories(self, extracted_data: List[Dict], existing_data: List[Dict]) -> Dict[str, List]:
        """合并分类数据"""
        merged_data = {}
        
        # 初始化所有分类
        for category in self.categories:
            merged_data[category] = []
        
        # 添加现有数据
        print("📥 合并现有数据...")
        for category_data in existing_data:
            category = category_data.get('category', '')
            if category in merged_data:
                items = category_data.get('items', [])
                merged_data[category].extend(items)
                print(f"  • {category}: 添加 {len(items)} 个现有坑点")
        
        # 添加提取的数据
        print("📥 合并提取数据...")
        for category_data in extracted_data:
            category = category_data.get('category', '')
            if category in merged_data:
                items = category_data.get('items', [])
                merged_data[category].extend(items)
                print(f"  • {category}: 添加 {len(items)} 个提取坑点")
        
        return merged_data
    
    def remove_duplicates(self, merged_data: Dict[str, List]) -> Dict[str, List]:
        """去除重复项（基于标题相似性）"""
        print("🔍 检查重复项...")
        
        for category, items in merged_data.items():
            if not items:
                continue
            
            # 简单的重复检测：基于标题
            seen_titles = set()
            unique_items = []
            duplicates = 0
            
            for item in items:
                title = item.get('标题', '').strip()
                if title and title not in seen_titles:
                    seen_titles.add(title)
                    unique_items.append(item)
                else:
                    duplicates += 1
            
            merged_data[category] = unique_items
            
            if duplicates > 0:
                print(f"  • {category}: 去除 {duplicates} 个重复项")
        
        return merged_data
    
    def reassign_numbers(self, merged_data: Dict[str, List]) -> List[Dict]:
        """重新分配编号"""
        print("🔢 重新分配编号...")
        
        result = []
        
        for category in self.categories:
            items = merged_data.get(category, [])
            if not items:
                continue
            
            # 重新分配编号
            for i, item in enumerate(items, 1):
                item['编号'] = i
            
            result.append({
                'category': category,
                'items': items
            })
            
            print(f"  • {category}: {len(items)} 个坑点 (编号 1-{len(items)})")
        
        return result
    
    def save_merged_data(self, merged_data: List[Dict], output_file: str, 
                        extracted_metadata: Dict = None):
        """保存合并后的数据"""
        # 构建输出数据
        output_data = {
            'merge_time': datetime.now().isoformat(),
            'total_categories': len(merged_data),
            'total_pits': sum(len(cat['items']) for cat in merged_data),
            'categories': merged_data
        }
        
        # 添加原始提取的元数据（如果有）
        if extracted_metadata:
            output_data['source_info'] = {
                'extraction_time': extracted_metadata.get('extraction_time'),
                'processed_files': extracted_metadata.get('processed_files'),
                'failed_files': extracted_metadata.get('failed_files', [])
            }
        
        # 保存文件
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            print(f"💾 合并结果已保存到: {output_file}")
            return True
        except Exception as e:
            print(f"❌ 保存失败: {e}")
            return False
    
    def print_summary(self, merged_data: List[Dict]):
        """打印合并摘要"""
        print(f"\n{'='*60}")
        print(f"📊 合并完成统计")
        print(f"{'='*60}")
        
        total_pits = sum(len(cat['items']) for cat in merged_data)
        print(f"总分类数: {len(merged_data)}")
        print(f"总坑点数: {total_pits}")
        
        print(f"\n📋 各分类统计:")
        for category_data in merged_data:
            category = category_data['category']
            count = len(category_data['items'])
            print(f"  • {category}: {count} 个")
        
        print(f"{'='*60}")
    
    def merge_files(self, extracted_file: str, existing_file: str, output_file: str):
        """合并两个文件"""
        print("🚀 开始合并保险坑点数据")
        print(f"📄 提取文件: {extracted_file}")
        print(f"📄 现有文件: {existing_file}")
        print(f"📄 输出文件: {output_file}")
        print("=" * 60)
        
        # 加载文件
        print("📖 加载数据文件...")
        extracted_raw = self.load_json_file(extracted_file)
        existing_raw = self.load_json_file(existing_file)
        
        if extracted_raw is None and existing_raw is None:
            print("❌ 无法加载任何数据文件")
            return False
        
        # 标准化数据格式
        extracted_data = self.normalize_extracted_data(extracted_raw) if extracted_raw else []
        existing_data = self.normalize_existing_data(existing_raw) if existing_raw else []
        
        print(f"✅ 提取数据: {len(extracted_data)} 个分类")
        print(f"✅ 现有数据: {len(existing_data)} 个分类")
        
        if not extracted_data and not existing_data:
            print("❌ 没有有效的数据可以合并")
            return False
        
        # 合并数据
        merged_dict = self.merge_categories(extracted_data, existing_data)
        
        # 去重
        merged_dict = self.remove_duplicates(merged_dict)
        
        # 重新分配编号
        merged_data = self.reassign_numbers(merged_dict)
        
        # 保存结果
        success = self.save_merged_data(
            merged_data, 
            output_file, 
            extracted_raw if extracted_raw else None
        )
        
        if success:
            # 显示摘要
            self.print_summary(merged_data)
            return True
        
        return False


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='合并保险坑点JSON文件')
    parser.add_argument('--extracted', '-e',
                       default='../data/insurance_pits_extracted.json',
                       help='提取的坑点文件路径')
    parser.add_argument('--existing', '-x',
                       default='../data/pit_types_new.json',
                       help='现有坑点文件路径')
    parser.add_argument('--output', '-o',
                       default='../data/insurance_pits_merged.json',
                       help='输出文件路径')
    parser.add_argument('--no-backup', '-n',
                       action='store_true',
                       help='不创建备份文件')
    
    args = parser.parse_args()
    
    # 检查输入文件
    extracted_file = Path(args.extracted)
    existing_file = Path(args.existing)
    
    if not extracted_file.exists() and not existing_file.exists():
        print("❌ 输入文件都不存在，无法执行合并")
        print(f"提取文件: {extracted_file}")
        print(f"现有文件: {existing_file}")
        return 1
    
    # 创建备份（如果需要）
    output_file = Path(args.output)
    if output_file.exists() and not args.no_backup:
        backup_file = output_file.with_suffix('.backup.json')
        try:
            import shutil
            shutil.copy2(output_file, backup_file)
            print(f"📦 创建备份: {backup_file}")
        except Exception as e:
            print(f"⚠️  备份失败: {e}")
    
    # 执行合并
    merger = PitsMerger()
    success = merger.merge_files(
        str(extracted_file),
        str(existing_file),
        str(output_file)
    )
    
    if success:
        print(f"\n🎉 合并成功完成！")
        print(f"📁 输出文件: {output_file}")
        
        # 显示后续建议
        print(f"\n💡 建议操作:")
        print(f"1. 查看合并结果: cat {output_file} | jq .")
        print(f"2. 检查数据质量: jq '.total_pits, .total_categories' {output_file}")
        print(f"3. 查看分类统计: jq '.categories[] | {{category: .category, count: (.items | length)}}' {output_file}")
        
        return 0
    else:
        print(f"\n❌ 合并失败")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main()) 