#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
深蓝保文章内容提取器
从已爬取的文章URL中提取正文内容，保存为纯文本文件
"""

import json
import os
import time
import re
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
from datetime import datetime


class ArticleContentExtractor:
    """文章内容提取器"""
    
    def __init__(self, output_dir: str = "../data/text"):
        self.output_dir = Path(output_dir)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': 'https://www.shenlanbao.com/',
            'DNT': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin'
        })
        
        # 创建输出目录
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 统计信息
        self.total_articles = 0
        self.success_count = 0
        self.failed_count = 0
        self.failed_urls = []
        
    def get_page_content(self, url: str, retries: int = 3) -> Optional[BeautifulSoup]:
        """获取页面内容"""
        for attempt in range(retries):
            try:
                print(f"    🔗 访问: {url} (尝试 {attempt + 1}/{retries})")
                response = self.session.get(url, timeout=15)
                response.raise_for_status()
                response.encoding = 'utf-8'
                
                soup = BeautifulSoup(response.text, 'html.parser')
                return soup
                
            except requests.exceptions.RequestException as e:
                print(f"    ❌ 请求失败 (尝试 {attempt + 1}/{retries}): {e}")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)  # 指数退避
                else:
                    self.failed_urls.append({
                        'url': url,
                        'error': str(e),
                        'timestamp': datetime.now().isoformat()
                    })
        
        return None
    
    def extract_article_content(self, soup: BeautifulSoup, url: str) -> Optional[Dict[str, str]]:
        """从页面中提取文章内容"""
        try:
            # 提取标题
            title = ""
            title_selectors = [
                'h1.title',
                'title',
                '.article-title',
                '.zhinan-title'
            ]
            
            for selector in title_selectors:
                title_element = soup.select_one(selector)
                if title_element:
                    title = title_element.get_text(strip=True)
                    break
            
            # 如果从h1没找到，尝试从title标签中提取
            if not title:
                title_tag = soup.find('title')
                if title_tag:
                    title = title_tag.get_text(strip=True)
            
            # 提取正文内容 - 根据用户提供的HTML结构
            content = ""
            content_selectors = [
                '#zhinanLinkContains .rich-text-parse',  # 主要的正文容器
                '.rich-text-parse.underline-a',
                '.contains .rich-text-parse',
                '.article-content',
                '.zhinan-content',
                '#zhinanLinkContains',  # 备用选择器
                '.contains'
            ]
            
            for selector in content_selectors:
                content_element = soup.select_one(selector)
                if content_element:
                    # 移除不需要的元素
                    for unwanted in content_element.select('script, style, .advertisement, .ad, .banner'):
                        unwanted.decompose()
                    
                    # 获取纯文本内容
                    content = content_element.get_text(separator='\n', strip=True)
                    break
            
            # 如果还是没找到内容，尝试更宽泛的选择器
            if not content:
                fallback_selectors = [
                    '.centerLeft',
                    '.zhinanContains',
                    'main',
                    'article',
                    '.main-content'
                ]
                
                for selector in fallback_selectors:
                    content_element = soup.select_one(selector)
                    if content_element:
                        # 移除导航、广告等不需要的内容
                        for unwanted in content_element.select(
                            'nav, header, footer, .navigation, .breadcrumb, '
                            'script, style, .advertisement, .ad, .banner, '
                            '.sidebar, .related-articles, .comments'
                        ):
                            unwanted.decompose()
                        
                        content = content_element.get_text(separator='\n', strip=True)
                        if len(content) > 500:  # 确保内容足够长
                            break
            
            # 清理内容
            if content:
                # 移除多余的空行
                content = re.sub(r'\n\s*\n', '\n\n', content)
                # 移除行首尾空白
                content = '\n'.join(line.strip() for line in content.split('\n'))
                # 移除过短的行（可能是导航或无关内容）
                lines = content.split('\n')
                filtered_lines = []
                for line in lines:
                    if len(line) > 10 or not line or line.isspace():
                        filtered_lines.append(line)
                content = '\n'.join(filtered_lines)
            
            return {
                'title': title,
                'content': content,
                'url': url
            }
            
        except Exception as e:
            print(f"    ❌ 内容提取失败: {e}")
            return None
    
    def save_article_text(self, article_data: Dict[str, str], filename: str) -> bool:
        """保存文章文本到文件"""
        try:
            file_path = self.output_dir / filename
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"标题: {article_data['title']}\n")
                f.write(f"URL: {article_data['url']}\n")
                f.write(f"提取时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 80 + "\n\n")
                f.write(article_data['content'])
            
            print(f"    ✅ 保存成功: {file_path}")
            return True
            
        except Exception as e:
            print(f"    ❌ 保存失败: {e}")
            return False
    
    def generate_filename(self, title: str, article_id: str) -> str:
        """生成安全的文件名"""
        # 清理标题，移除不安全的字符
        safe_title = re.sub(r'[<>:"/\\|?*]', '', title)
        safe_title = safe_title.replace('！', '!').replace('？', '?')
        
        # 限制长度
        if len(safe_title) > 50:
            safe_title = safe_title[:50]
        
        # 生成文件名
        filename = f"{article_id}_{safe_title}.txt"
        return filename
    
    def extract_article_id_from_url(self, url: str) -> str:
        """从URL中提取文章ID"""
        try:
            # URL格式: https://www.shenlanbao.com/zhinan/1784464437948104704
            parts = url.strip('/').split('/')
            article_id = parts[-1]
            return article_id
        except:
            # 如果提取失败，使用URL的hash作为ID
            return str(hash(url))[-10:]
    
    def process_articles_from_json(self, json_file: str, max_articles: Optional[int] = None) -> Dict:
        """从JSON文件处理文章"""
        print(f"🚀 开始处理文章内容提取...")
        print(f"📁 输出目录: {self.output_dir}")
        print(f"📄 数据源: {json_file}")
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            articles = data.get('articles', [])
            self.total_articles = len(articles)
            
            if max_articles:
                articles = articles[:max_articles]
                print(f"🔢 限制处理数量: {max_articles}")
            
            print(f"📊 总文章数: {len(articles)}")
            print("=" * 60)
            
            for i, article in enumerate(articles, 1):
                url = article.get('url')
                title = article.get('title', '未知标题')
                
                if not url:
                    continue
                
                print(f"\n📰 处理第 {i}/{len(articles)} 篇文章:")
                print(f"    标题: {title}")
                
                # 获取页面内容
                soup = self.get_page_content(url)
                if not soup:
                    print(f"    ❌ 跳过: 无法获取页面内容")
                    self.failed_count += 1
                    continue
                
                # 提取文章内容
                article_data = self.extract_article_content(soup, url)
                if not article_data or not article_data['content']:
                    print(f"    ❌ 跳过: 无法提取文章内容")
                    self.failed_count += 1
                    continue
                
                # 生成文件名
                article_id = self.extract_article_id_from_url(url)
                filename = self.generate_filename(article_data['title'], article_id)
                
                # 保存文件
                if self.save_article_text(article_data, filename):
                    self.success_count += 1
                else:
                    self.failed_count += 1
                
                # 请求间隔
                time.sleep(1)
            
            # 保存处理报告
            self.save_processing_report()
            
        except Exception as e:
            print(f"❌ 处理JSON文件失败: {e}")
            return {'success': False, 'error': str(e)}
        
        return {
            'success': True,
            'total': self.total_articles,
            'success_count': self.success_count,
            'failed_count': self.failed_count
        }
    
    def save_processing_report(self):
        """保存处理报告"""
        report = {
            'processing_time': datetime.now().isoformat(),
            'total_articles': self.total_articles,
            'success_count': self.success_count,
            'failed_count': self.failed_count,
            'success_rate': f"{(self.success_count/self.total_articles*100):.1f}%" if self.total_articles > 0 else "0%",
            'failed_urls': self.failed_urls
        }
        
        report_file = self.output_dir / f"extraction_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n📊 处理报告已保存: {report_file}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='提取深蓝保文章正文内容')
    parser.add_argument('--json-file', '-f', 
                       default='../data/shenlanbao_避坑指南_20250730_114302.json',
                       help='包含文章URL的JSON文件路径')
    parser.add_argument('--output-dir', '-o',
                       default='../data/text',
                       help='输出文本文件的目录')
    parser.add_argument('--max-articles', '-m',
                       type=int,
                       help='限制处理的文章数量（用于测试）')
    parser.add_argument('--test', '-t',
                       action='store_true',
                       help='测试模式，只处理前5篇文章')
    
    args = parser.parse_args()
    
    if args.test:
        args.max_articles = 5
        print("🧪 测试模式：只处理前5篇文章")
    
    # 检查JSON文件是否存在
    if not os.path.exists(args.json_file):
        print(f"❌ JSON文件不存在: {args.json_file}")
        print("请先运行爬虫获取文章列表")
        return
    
    # 创建提取器并开始处理
    extractor = ArticleContentExtractor(output_dir=args.output_dir)
    result = extractor.process_articles_from_json(args.json_file, args.max_articles)
    
    # 输出最终统计
    if result['success']:
        print(f"\n{'='*60}")
        print(f"🎉 处理完成！")
        print(f"📊 统计信息:")
        print(f"   总文章数: {result['total']}")
        print(f"   成功提取: {result['success_count']}")
        print(f"   失败数量: {result['failed_count']}")
        print(f"   成功率: {(result['success_count']/result['total']*100):.1f}%")
        print(f"📁 输出目录: {extractor.output_dir}")
        print(f"{'='*60}")
    else:
        print(f"❌ 处理失败: {result.get('error', '未知错误')}")


if __name__ == "__main__":
    main() 