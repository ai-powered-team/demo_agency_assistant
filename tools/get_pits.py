#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
保险坑点提取器
使用DeepSeek API从文章中提取保险坑点，并按照预定义的分类进行整理
"""

import json
import os
import time
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import requests


class InsurancePitExtractor:
    """保险坑点提取器"""
    
    def __init__(self, api_key: str = None, text_dir: str = "../data/text"):
        self.text_dir = Path(text_dir)
        self.api_key = api_key or os.getenv('DEEPSEEK_API_KEY')
        
        if not self.api_key:
            raise ValueError("请设置DEEPSEEK_API_KEY环境变量或传入api_key参数")
        
        # DeepSeek API配置
        self.api_url = "https://api.deepseek.com/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # 坑点分类定义
        self.categories = [
            "产品比较与费率相关坑点",
            "保障责任与理赔条款相关坑点", 
            "销售行为与专业伦理相关坑点",
            "续保、停售与产品稳定性相关坑点",
            "核保与健康告知相关坑点",
            "其他坑点"
        ]
        
        # 统计信息
        self.processed_files = 0
        self.total_pits_found = 0
        self.failed_files = []
        
    def create_extraction_prompt(self, article_content: str) -> str:
        """创建坑点提取的提示词"""
        prompt = f"""
请分析以下保险相关文章，提取其中提到的保险坑点、陷阱、误导性销售行为等问题。如果文章没有明显提及坑点，请返回空数组[]。

请按照以下6个分类进行整理：
1. 产品比较与费率相关坑点 - 涉及产品对比、价格、费率方面的误导
2. 保障责任与理赔条款相关坑点 - 涉及保障范围、理赔条件、免责条款等方面的问题
3. 销售行为与专业伦理相关坑点 - 涉及销售人员的不当行为、误导性宣传等
4. 续保、停售与产品稳定性相关坑点 - 涉及产品续保、停售、稳定性等方面的问题
5. 核保与健康告知相关坑点 - 涉及健康告知、核保审查等方面的问题
6. 其他坑点 - 不属于以上分类的其他保险相关坑点

对于每个坑点，请提供：
- 标题：简洁概括这个坑点，要求是一句容易引起误导的表述
- 示例描述：具体的坑点表现形式或案例
- 坑点原因：为什么这是个坑，会造成什么问题

请以JSON格式返回结果，格式如下：
```json
[
  {{
    "category": "分类名称",
    "items": [
      {{
        "标题": "坑点标题",
        "示例描述": "具体描述",
        "坑点原因": "造成问题的原因"
      }}
    ]
  }}
]
```

文章内容：
{article_content}

请仔细分析文章内容，提取所有提到的保险坑点。如果文章中没有明确提到坑点，请返回空数组[]。
"""
        return prompt
    
    def call_deepseek_api(self, prompt: str, max_retries: int = 3) -> Optional[str]:
        """调用DeepSeek API"""
        for attempt in range(max_retries):
            try:
                payload = {
                    "model": "deepseek-chat",
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.3,
                    "max_tokens": 4000
                }
                
                print(f"    🤖 调用DeepSeek API (尝试 {attempt + 1}/{max_retries})")
                response = requests.post(self.api_url, headers=self.headers, json=payload, timeout=60)
                response.raise_for_status()
                
                result = response.json()
                content = result['choices'][0]['message']['content']
                
                # 提取JSON部分
                json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
                if json_match:
                    return json_match.group(1)
                else:
                    # 如果没有代码块标记，尝试直接解析
                    return content.strip()
                
            except requests.exceptions.RequestException as e:
                print(f"    ❌ API请求失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # 指数退避
            except Exception as e:
                print(f"    ❌ 处理响应失败: {e}")
                break
        
        return None
    
    def parse_extraction_result(self, result_text: str) -> List[Dict[str, Any]]:
        """解析API返回的结果"""
        try:
            # 尝试直接解析JSON
            pits_data = json.loads(result_text)
            
            # 验证数据格式
            if isinstance(pits_data, list):
                validated_data = []
                for category_data in pits_data:
                    if isinstance(category_data, dict) and 'category' in category_data and 'items' in category_data:
                        # 验证分类名称
                        if category_data['category'] in self.categories:
                            validated_items = []
                            for item in category_data.get('items', []):
                                if isinstance(item, dict) and all(key in item for key in ['标题', '示例描述', '坑点原因']):
                                    validated_items.append(item)
                            
                            if validated_items:
                                validated_data.append({
                                    'category': category_data['category'],
                                    'items': validated_items
                                })
                
                return validated_data
            
        except json.JSONDecodeError as e:
            print(f"    ❌ JSON解析失败: {e}")
            print(f"    原始内容: {result_text[:200]}...")
        
        return []
    
    def read_article_content(self, file_path: Path) -> Optional[str]:
        """读取文章内容"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 跳过文件头部的元数据，只提取正文内容
            lines = content.split('\n')
            content_start_idx = 0
            
            for i, line in enumerate(lines):
                if line.strip() == '=' * 80:  # 找到分隔线
                    content_start_idx = i + 1
                    break
            
            article_content = '\n'.join(lines[content_start_idx:]).strip()
            
            # 限制内容长度，避免API token超限
            if len(article_content) > 8000:
                article_content = article_content[:8000] + "..."
            
            return article_content
            
        except Exception as e:
            print(f"    ❌ 读取文件失败: {e}")
            return None
    
    def extract_pits_from_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """从单个文件提取坑点"""
        print(f"📄 处理文件: {file_path.name}")
        
        # 读取文章内容
        article_content = self.read_article_content(file_path)
        if not article_content:
            return []
        
        print(f"    📝 文章长度: {len(article_content)} 字符")
        
        # 创建提取提示词
        prompt = self.create_extraction_prompt(article_content)
        
        # 调用API
        result_text = self.call_deepseek_api(prompt)
        if not result_text:
            print(f"    ❌ API调用失败")
            self.failed_files.append(str(file_path))
            return []
        
        # 解析结果
        pits_data = self.parse_extraction_result(result_text)
        
        if pits_data:
            total_pits = sum(len(category['items']) for category in pits_data)
            print(f"    ✅ 提取到 {total_pits} 个坑点")
            self.total_pits_found += total_pits
        else:
            print(f"    ℹ️  未发现明显坑点")
        
        return pits_data
    
    def merge_pits_data(self, all_pits_data: List[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """合并所有文件的坑点数据"""
        merged_data = {}
        pit_counter = {}
        
        # 初始化分类
        for category in self.categories:
            merged_data[category] = []
            pit_counter[category] = 0
        
        # 合并数据
        for file_pits in all_pits_data:
            for category_data in file_pits:
                category = category_data['category']
                if category in merged_data:
                    for item in category_data['items']:
                        pit_counter[category] += 1
                        item['编号'] = pit_counter[category]
                        merged_data[category].append(item)
        
        # 转换为最终格式
        result = []
        for category in self.categories:
            if merged_data[category]:
                result.append({
                    'category': category,
                    'items': merged_data[category]
                })
        
        return result
    
    def save_results(self, pits_data: List[Dict[str, Any]], output_file: str):
        """保存结果到文件"""
        try:
            # 添加元数据
            output_data = {
                'extraction_time': datetime.now().isoformat(),
                'total_categories': len(pits_data),
                'total_pits': sum(len(category['items']) for category in pits_data),
                'processed_files': self.processed_files,
                'failed_files': self.failed_files,
                'categories': pits_data
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            
            print(f"💾 结果已保存到: {output_file}")
            
        except Exception as e:
            print(f"❌ 保存结果失败: {e}")
    
    def process_all_files(self, max_files: Optional[int] = None) -> List[Dict[str, Any]]:
        """处理所有文本文件"""
        print(f"🚀 开始处理保险坑点提取")
        print(f"📁 文本目录: {self.text_dir}")
        print(f"🤖 使用API: DeepSeek")
        print("=" * 60)
        
        # 查找所有txt文件
        txt_files = list(self.text_dir.glob("*.txt"))
        # 过滤掉报告文件
        txt_files = [f for f in txt_files if not f.name.startswith('extraction_report')]
        
        if not txt_files:
            print("❌ 未找到任何文本文件")
            return []
        
        if max_files:
            txt_files = txt_files[:max_files]
            print(f"🔢 限制处理数量: {max_files}")
        
        print(f"📊 找到 {len(txt_files)} 个文本文件")
        print("=" * 60)
        
        all_pits_data = []
        
        for i, file_path in enumerate(txt_files, 1):
            print(f"\n📖 处理第 {i}/{len(txt_files)} 个文件")
            
            pits_data = self.extract_pits_from_file(file_path)
            if pits_data:
                all_pits_data.append(pits_data)
            
            self.processed_files += 1
            
            # API调用间隔
            if i < len(txt_files):
                print(f"    ⏱️  等待 2 秒...")
                time.sleep(2)
        
        # 合并结果
        print(f"\n🔄 合并所有提取结果...")
        merged_results = self.merge_pits_data(all_pits_data)
        
        return merged_results
    
    def print_summary(self, results: List[Dict[str, Any]]):
        """打印提取摘要"""
        print(f"\n{'='*60}")
        print(f"📊 提取完成统计")
        print(f"{'='*60}")
        print(f"处理文件数: {self.processed_files}")
        print(f"总坑点数: {self.total_pits_found}")
        print(f"失败文件数: {len(self.failed_files)}")
        
        if results:
            print(f"\n📋 分类统计:")
            for category_data in results:
                category = category_data['category']
                count = len(category_data['items'])
                print(f"  • {category}: {count} 个")
        
        if self.failed_files:
            print(f"\n⚠️  处理失败的文件:")
            for failed_file in self.failed_files:
                print(f"  • {failed_file}")
        
        print(f"{'='*60}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='从文本文件中提取保险坑点')
    parser.add_argument('--text-dir', '-d',
                       default='../data/text',
                       help='文本文件目录')
    parser.add_argument('--output', '-o',
                       default='../data/insurance_pits_extracted.json',
                       help='输出文件路径')
    parser.add_argument('--max-files', '-m',
                       type=int,
                       help='限制处理的文件数量（用于测试）')
    parser.add_argument('--api-key', '-k',
                       help='DeepSeek API密钥（也可通过环境变量DEEPSEEK_API_KEY设置）')
    parser.add_argument('--test', '-t',
                       action='store_true',
                       help='测试模式，只处理前3个文件')
    
    args = parser.parse_args()
    
    if args.test:
        args.max_files = 3
        print("🧪 测试模式：只处理前3个文件")
    
    # 检查文本目录
    text_dir = Path(args.text_dir)
    if not text_dir.exists():
        print(f"❌ 文本目录不存在: {text_dir}")
        print("请先运行文章内容提取工具")
        return
    
    # 检查API密钥
    api_key = args.api_key or os.getenv('DEEPSEEK_API_KEY')
    if not api_key:
        print("❌ 请设置DeepSeek API密钥")
        print("方法1: export DEEPSEEK_API_KEY='your_api_key'")
        print("方法2: python get_pits.py --api-key your_api_key")
        return
    
    try:
        # 创建提取器
        extractor = InsurancePitExtractor(api_key=api_key, text_dir=args.text_dir)
        
        # 开始处理
        start_time = datetime.now()
        results = extractor.process_all_files(max_files=args.max_files)
        end_time = datetime.now()
        
        # 保存结果
        if results:
            extractor.save_results(results, args.output)
        
        # 显示摘要
        extractor.print_summary(results)
        
        print(f"\n⏱️  总耗时: {end_time - start_time}")
        
        if results:
            print(f"🎉 处理完成！坑点数据已保存到: {args.output}")
        else:
            print("ℹ️  未提取到任何坑点数据")
        
    except KeyboardInterrupt:
        print(f"\n\n⚠️  用户中断处理")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 