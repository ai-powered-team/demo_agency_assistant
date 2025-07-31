#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
深蓝保网站爬虫
用于爬取 https://www.shenlanbao.com/zhinan/list-23 页面的文章内容
支持分页遍历和内容提取
"""

import requests
import json
import time
import re
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse, parse_qs, urlencode, urlunparse
from bs4 import BeautifulSoup
from datetime import datetime


class ShenlanbaoCrawler:
    """深蓝保网站爬虫类"""
    
    def __init__(self):
        self.base_url = "https://www.shenlanbao.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Referer': 'https://www.shenlanbao.com/',
            'DNT': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin'
        })
        self.articles = []
        
    def get_page_content(self, url: str, retries: int = 3) -> Optional[BeautifulSoup]:
        """获取页面内容，支持重试"""
        for attempt in range(retries):
            try:
                print(f"  正在请求: {url} (尝试 {attempt + 1}/{retries})")
                response = self.session.get(url, timeout=15)
                response.raise_for_status()
                response.encoding = 'utf-8'
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 验证页面是否有效（包含文章内容或分页器）
                if soup.find_all('div', class_='article-item') or soup.find('ul', {'id': 'm_fenye'}):
                    return soup
                else:
                    print(f"  页面无效内容，可能已到达最后一页")
                    return None
                    
            except requests.exceptions.RequestException as e:
                print(f"  请求失败 (尝试 {attempt + 1}/{retries}): {e}")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)  # 指数退避
                else:
                    print(f"  获取页面内容失败: {url}")
        
        return None
    
    def extract_article_info(self, article_element) -> Optional[Dict]:
        """从文章元素中提取文章信息"""
        try:
            article_info = {}
            
            # 提取标题和链接
            title_link = article_element.find('a', class_='title') or article_element.find('a', class_='style-oneline')
            if title_link:
                article_info['title'] = title_link.get_text(strip=True)
                article_info['url'] = urljoin(self.base_url, title_link.get('href', ''))
            else:
                return None
            
            # 提取描述
            desc_element = article_element.find('div', class_='desc') or article_element.find('div', class_='style-mutiline')
            if desc_element:
                article_info['description'] = desc_element.get_text(strip=True)
            
            # 提取发布时间
            time_element = article_element.find('div', class_='publish-time')
            if time_element:
                time_span = time_element.find('span')
                if time_span:
                    article_info['publish_time'] = time_span.get_text(strip=True)
            
            # 提取阅读量
            view_element = article_element.find('div', class_='view')
            if view_element:
                view_span = view_element.find('span')
                if view_span:
                    article_info['views'] = view_span.get_text(strip=True)
            
            # 提取图片
            img_element = article_element.find('img')
            if img_element:
                article_info['image_url'] = img_element.get('src', '')
            
            return article_info
            
        except Exception as e:
            print(f"  提取文章信息失败: {e}")
            return None
    
    def get_article_content(self, article_url: str) -> Optional[str]:
        """获取文章详细内容"""
        try:
            soup = self.get_page_content(article_url)
            if not soup:
                return None
            
            # 尝试多种可能的内容选择器
            content_selectors = [
                '.article-content',
                '.content',
                '.main-content',
                '.post-content',
                'article',
                '.article-body',
                '.zhishi-content',
                '.detail-content'
            ]
            
            for selector in content_selectors:
                content_element = soup.select_one(selector)
                if content_element:
                    # 清理内容，移除脚本和样式
                    for script in content_element(["script", "style"]):
                        script.decompose()
                    return content_element.get_text(strip=True)
            
            # 如果没有找到专门的内容区域，尝试提取主要文本
            body = soup.find('body')
            if body:
                for script in body(["script", "style", "nav", "header", "footer"]):
                    script.decompose()
                return body.get_text(strip=True)[:2000]  # 限制长度
                
        except Exception as e:
            print(f"  获取文章内容失败: {article_url}, 错误: {e}")
        
        return None
    
    def parse_page(self, url: str) -> List[Dict]:
        """解析单个页面的文章列表"""
        soup = self.get_page_content(url)
        if not soup:
            return []
        
        articles = []
        
        # 查找文章列表容器
        article_items = soup.find_all('div', class_='article-item')
        
        for item in article_items:
            article_info = self.extract_article_info(item)
            if article_info:
                articles.append(article_info)
                print(f"  ✓ 提取文章: {article_info['title']}")
        
        return articles
    
    def detect_pagination_pattern(self, url: str) -> Tuple[str, int]:
        """检测分页URL模式"""
        parsed = urlparse(url)
        
        # 常见的分页URL模式
        patterns = [
            # 模式1: /list-23/2, /list-23/3 (路径形式)
            (r'/list-(\d+)$', 'path'),
            # 模式2: ?page=1, ?page=2 (查询参数)
            (r'\?.*page=', 'query'),
            # 模式3: #page1, #page2 (锚点)
            (r'#page', 'hash')
        ]
        
        for pattern, ptype in patterns:
            if re.search(pattern, url):
                return ptype, 1
        
        return 'path', 1  # 默认使用路径模式
    
    def construct_next_page_url(self, base_url: str, page_num: int, pattern_type: str = 'path') -> str:
        """构造下一页URL"""
        try:
            if pattern_type == 'path':
                # 路径模式: /zhinan/list-23 -> /zhinan/list-23/2
                if base_url.endswith('/'):
                    return f"{base_url.rstrip('/')}/{page_num}"
                else:
                    return f"{base_url}/{page_num}"
            
            elif pattern_type == 'query':
                # 查询参数模式
                parsed = urlparse(base_url)
                query_params = parse_qs(parsed.query)
                query_params['page'] = [str(page_num)]
                new_query = urlencode(query_params, doseq=True)
                return urlunparse((
                    parsed.scheme, parsed.netloc, parsed.path,
                    parsed.params, new_query, parsed.fragment
                ))
            
            else:  # hash模式
                parsed = urlparse(base_url)
                return urlunparse((
                    parsed.scheme, parsed.netloc, parsed.path,
                    parsed.params, parsed.query, f"page{page_num}"
                ))
                
        except Exception as e:
            print(f"  构造URL失败: {e}")
            return f"{base_url.rstrip('/')}/{page_num}"  # 备用方案
    
    def find_pagination_info(self, soup: BeautifulSoup, current_url: str) -> Dict:
        """智能分析分页信息"""
        pagination_info = {
            'current_page': 1,
            'total_pages': 1,
            'has_next': False,
            'next_url': None,
            'pattern_type': 'path'
        }
        
        try:
            # 1. 尝试从分页器DOM中获取信息
            pagination = soup.find('ul', {'id': 'm_fenye'}) or soup.find('ul', class_='app-pagination')
            
            if pagination:
                # 查找页码链接
                page_links = pagination.find_all('a')
                page_numbers = []
                
                for link in page_links:
                    href = link.get('href', '')
                    text = link.get_text(strip=True)
                    
                    # 提取页码
                    if text.isdigit():
                        page_numbers.append(int(text))
                    elif '下一页' in text or 'next' in text.lower():
                        pagination_info['has_next'] = True
                        pagination_info['next_url'] = urljoin(self.base_url, href)
                    
                    # 从href中提取页码信息
                    if href:
                        page_match = re.search(r'/(\d+)$', href) or re.search(r'page=(\d+)', href)
                        if page_match:
                            page_numbers.append(int(page_match.group(1)))
                
                if page_numbers:
                    pagination_info['total_pages'] = max(page_numbers)
            
            # 2. 从URL中提取当前页码
            current_page_match = re.search(r'/(\d+)$', current_url) or re.search(r'page=(\d+)', current_url)
            if current_page_match:
                pagination_info['current_page'] = int(current_page_match.group(1))
            
            # 3. 检测URL模式
            pattern_type, _ = self.detect_pagination_pattern(current_url)
            pagination_info['pattern_type'] = pattern_type
            
            # 4. 如果没有找到明确的分页信息，使用智能推测
            if pagination_info['total_pages'] == 1:
                # 通过页面结构推测是否有更多页面
                article_count = len(soup.find_all('div', class_='article-item'))
                if article_count >= 10:  # 假设每页至少10篇文章
                    pagination_info['total_pages'] = 50  # 设置一个合理的最大值
                    pagination_info['has_next'] = True
            
        except Exception as e:
            print(f"  分析分页信息失败: {e}")
        
        return pagination_info
    
    def crawl_all_pages(self, start_url: str, max_pages: int = None, include_content: bool = False) -> List[Dict]:
        """爬取所有分页的文章"""
        all_articles = []
        current_url = start_url
        page_count = 1
        consecutive_empty_pages = 0
        
        print(f"🚀 开始爬取: {start_url}")
        print(f"📄 最大页数: {max_pages if max_pages else '无限制'}")
        print(f"📝 包含内容: {'是' if include_content else '否'}")
        print("=" * 60)
        
        # 检测分页模式
        pattern_type, _ = self.detect_pagination_pattern(start_url)
        base_url = start_url
        
        while current_url and (max_pages is None or page_count <= max_pages):
            print(f"\n📖 正在爬取第 {page_count} 页...")
            print(f"🔗 URL: {current_url}")
            
            soup = self.get_page_content(current_url)
            if not soup:
                print(f"  ❌ 页面加载失败，尝试下一页...")
                consecutive_empty_pages += 1
                if consecutive_empty_pages >= 3:
                    print(f"  🛑 连续3页失败，停止爬取")
                    break
            else:
                consecutive_empty_pages = 0
            
            # 解析当前页面的文章
            if soup:
                page_articles = self.parse_page(current_url)
                
                if not page_articles:
                    print(f"  ⚠️  第 {page_count} 页无文章内容")
                    consecutive_empty_pages += 1
                    if consecutive_empty_pages >= 2:
                        print(f"  🛑 连续空页面，可能已到达最后一页")
                        break
                else:
                    consecutive_empty_pages = 0
                    
                    # 如果需要获取文章详细内容
                    if include_content:
                        for i, article in enumerate(page_articles):
                            if article.get('url'):
                                print(f"  📰 获取文章内容 ({i+1}/{len(page_articles)}): {article['title'][:50]}...")
                                article['content'] = self.get_article_content(article['url'])
                                time.sleep(1)  # 避免请求过于频繁
                    
                    all_articles.extend(page_articles)
                    print(f"  ✅ 第 {page_count} 页获取到 {len(page_articles)} 篇文章")
                
                # 获取分页信息
                pagination_info = self.find_pagination_info(soup, current_url)
                print(f"  📊 分页信息: 当前第{pagination_info['current_page']}页，总计{pagination_info['total_pages']}页")
            
            # 构造下一页URL
            next_page_num = page_count + 1
            
            # 检查是否应该继续
            if soup and pagination_info.get('has_next') and pagination_info.get('next_url'):
                current_url = pagination_info['next_url']
            elif next_page_num <= pagination_info.get('total_pages', 1):
                current_url = self.construct_next_page_url(base_url, next_page_num, pattern_type)
            else:
                # 尝试构造可能的下一页URL
                potential_next_url = self.construct_next_page_url(base_url, next_page_num, pattern_type)
                
                # 快速检查下一页是否存在（HEAD请求）
                try:
                    test_response = self.session.head(potential_next_url, timeout=5)
                    if test_response.status_code == 200:
                        current_url = potential_next_url
                    else:
                        print(f"  🏁 下一页不存在 (HTTP {test_response.status_code})，结束爬取")
                        break
                except:
                    print(f"  🏁 无法访问下一页，结束爬取")
                    break
            
            page_count += 1
            time.sleep(1)  # 请求间隔
        
        print(f"\n{'='*60}")
        print(f"🎉 爬取完成！")
        print(f"📊 总共获取到 {len(all_articles)} 篇文章")
        print(f"📄 共爬取 {page_count - 1} 页")
        print(f"{'='*60}")
        
        return all_articles
    
    def save_to_json(self, articles: List[Dict], filename: str):
        """保存数据到JSON文件"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump({
                    'crawl_time': datetime.now().isoformat(),
                    'total_articles': len(articles),
                    'articles': articles
                }, f, ensure_ascii=False, indent=2)
            print(f"💾 数据已保存到: {filename}")
        except Exception as e:
            print(f"❌ 保存文件失败: {e}")


def main():
    """主函数"""
    crawler = ShenlanbaoCrawler()
    
    # 要爬取的URL
    target_url = "https://www.shenlanbao.com/zhinan/list-23"
    
    # 爬取所有页面的文章（不包含详细内容）
    print("🕷️  深蓝保文章爬虫启动...")
    articles = crawler.crawl_all_pages(
        start_url=target_url,
        max_pages=5,  # 限制最大页数，避免爬取时间过长
        include_content=False  # 设置为True可以获取文章详细内容，但会增加爬取时间
    )
    
    # 保存结果
    output_file = f"../data/shenlanbao_articles_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    crawler.save_to_json(articles, output_file)
    
    # 打印统计信息
    if articles:
        print(f"\n📈 示例文章:")
        for i, article in enumerate(articles[:3]):  # 显示前3篇文章
            print(f"\n{i+1}. 📰 {article.get('title', 'N/A')}")
            print(f"   🔗 {article.get('url', 'N/A')}")
            print(f"   📅 {article.get('publish_time', 'N/A')}")
            print(f"   👁️  {article.get('views', 'N/A')} 次阅读")
            desc = article.get('description', 'N/A')
            if len(desc) > 100:
                desc = desc[:100] + "..."
            print(f"   📝 {desc}")


if __name__ == "__main__":
    main() 