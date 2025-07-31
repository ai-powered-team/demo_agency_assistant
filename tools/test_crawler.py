#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
爬虫测试脚本
用于快速测试爬虫功能是否正常
"""

import sys
import os
from datetime import datetime

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from shenlanbao_crawler import ShenlanbaoCrawler


def test_single_page():
    """测试单页爬取功能"""
    print("🧪 测试单页爬取功能...")
    
    crawler = ShenlanbaoCrawler()
    target_url = "https://www.shenlanbao.com/zhinan/list-23"
    
    # 只爬取第一页
    articles = crawler.crawl_all_pages(
        start_url=target_url,
        max_pages=1,
        include_content=False
    )
    
    if articles:
        print(f"✅ 单页测试成功，获取到 {len(articles)} 篇文章")
        
        # 显示第一篇文章的详细信息
        first_article = articles[0]
        print(f"\n📰 第一篇文章示例:")
        print(f"   标题: {first_article.get('title', 'N/A')}")
        print(f"   链接: {first_article.get('url', 'N/A')}")
        print(f"   时间: {first_article.get('publish_time', 'N/A')}")
        print(f"   阅读: {first_article.get('views', 'N/A')}")
        print(f"   描述: {first_article.get('description', 'N/A')[:150]}...")
        
        return True
    else:
        print("❌ 单页测试失败，未获取到文章")
        return False


def test_pagination():
    """测试分页功能"""
    print("\n🧪 测试分页功能...")
    
    crawler = ShenlanbaoCrawler()
    target_url = "https://www.shenlanbao.com/zhinan/list-23"
    
    # 爬取前2页
    articles = crawler.crawl_all_pages(
        start_url=target_url,
        max_pages=2,
        include_content=False
    )
    
    if len(articles) > 10:  # 假设每页至少有10篇文章
        print(f"✅ 分页测试成功，获取到 {len(articles)} 篇文章")
        return True
    else:
        print(f"⚠️  分页测试可能有问题，只获取到 {len(articles)} 篇文章")
        return False


def test_url_construction():
    """测试URL构造功能"""
    print("\n🧪 测试URL构造功能...")
    
    crawler = ShenlanbaoCrawler()
    
    # 测试不同的URL模式
    test_cases = [
        ("https://www.shenlanbao.com/zhinan/list-23", 2, "path"),
        ("https://www.shenlanbao.com/zhinan/list-23?param=1", 2, "query"),
        ("https://www.shenlanbao.com/zhinan/list-23", 3, "path")
    ]
    
    for base_url, page_num, pattern_type in test_cases:
        next_url = crawler.construct_next_page_url(base_url, page_num, pattern_type)
        print(f"  {base_url} -> {next_url}")
    
    print("✅ URL构造测试完成")
    return True


def main():
    """主测试函数"""
    print("🚀 深蓝保爬虫功能测试")
    print("=" * 50)
    
    success_count = 0
    total_tests = 3
    
    # 运行测试
    tests = [
        ("单页爬取", test_single_page),
        ("URL构造", test_url_construction),
        ("分页功能", test_pagination)
    ]
    
    for test_name, test_func in tests:
        try:
            if test_func():
                success_count += 1
        except Exception as e:
            print(f"❌ {test_name}测试出错: {e}")
    
    # 输出测试结果
    print(f"\n{'='*50}")
    print(f"🎯 测试完成: {success_count}/{total_tests} 通过")
    
    if success_count == total_tests:
        print("🎉 所有测试通过！爬虫功能正常")
    else:
        print("⚠️  部分测试失败，请检查网络连接或网站结构变化")


if __name__ == "__main__":
    main() 