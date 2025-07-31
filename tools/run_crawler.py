#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
深蓝保爬虫命令行运行脚本
支持多种参数配置，方便使用
"""

import argparse
import sys
import os
from datetime import datetime

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from shenlanbao_crawler import ShenlanbaoCrawler
from crawler_config import CRAWLER_CONFIG, SHENLANBAO_CONFIG


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='深蓝保网站文章爬虫工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 基本使用 - 爬取避坑指南
  python run_crawler.py

  # 指定分类
  python run_crawler.py --category 小白入门

  # 限制页数和包含内容
  python run_crawler.py --max-pages 5 --include-content

  # 指定自定义URL
  python run_crawler.py --url https://www.shenlanbao.com/zhinan/list-20

支持的分类:
  - 避坑指南 (默认)
  - 小白入门
  - 购险必看
  - 理赔科普
        """
    )
    
    parser.add_argument(
        '--category', '-c',
        choices=['避坑指南', '小白入门', '购险必看', '理赔科普'],
        default='避坑指南',
        help='要爬取的文章分类 (默认: 避坑指南)'
    )
    
    parser.add_argument(
        '--url', '-u',
        type=str,
        help='自定义要爬取的URL (如果指定此参数，--category将被忽略)'
    )
    
    parser.add_argument(
        '--max-pages', '-m',
        type=int,
        default=CRAWLER_CONFIG['max_pages'],
        help=f'最大爬取页数 (默认: {CRAWLER_CONFIG["max_pages"]})'
    )
    
    parser.add_argument(
        '--include-content', '-i',
        action='store_true',
        default=CRAWLER_CONFIG['include_content'],
        help='是否获取文章详细内容 (默认: 否)'
    )
    
    parser.add_argument(
        '--delay', '-d',
        type=float,
        default=CRAWLER_CONFIG['request_delay'],
        help=f'请求间隔时间(秒) (默认: {CRAWLER_CONFIG["request_delay"]})'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        help='输出文件路径 (默认: 自动生成)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='显示详细日志'
    )
    
    return parser.parse_args()


def main():
    """主函数"""
    args = parse_arguments()
    
    # 确定目标URL
    if args.url:
        target_url = args.url
        category_name = "自定义"
    else:
        target_url = SHENLANBAO_CONFIG['target_urls'][args.category]
        category_name = args.category
    
    # 确定输出文件路径
    if args.output:
        output_file = args.output
    else:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"shenlanbao_{category_name}_{timestamp}.json"
        output_file = os.path.join(CRAWLER_CONFIG['output_dir'], filename)
    
    # 创建输出目录
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # 显示配置信息
    print("=" * 60)
    print("深蓝保网站爬虫工具")
    print("=" * 60)
    print(f"分类: {category_name}")
    print(f"URL: {target_url}")
    print(f"最大页数: {args.max_pages}")
    print(f"包含内容: {'是' if args.include_content else '否'}")
    print(f"请求间隔: {args.delay}秒")
    print(f"输出文件: {output_file}")
    print("=" * 60)
    
    # 创建爬虫实例
    crawler = ShenlanbaoCrawler()
    
    # 更新配置
    crawler.session.headers.update(CRAWLER_CONFIG['headers'])
    
    try:
        # 开始爬取
        articles = crawler.crawl_all_pages(
            start_url=target_url,
            max_pages=args.max_pages,
            include_content=args.include_content
        )
        
        if not articles:
            print("\n❌ 未获取到任何文章，请检查URL或网络连接")
            return
        
        # 保存结果
        crawler.save_to_json(articles, output_file)
        
        # 显示统计信息
        print(f"\n{'='*60}")
        print("爬取完成统计")
        print(f"{'='*60}")
        print(f"✅ 总文章数: {len(articles)}")
        print(f"✅ 输出文件: {output_file}")
        
        # 显示示例文章（如果启用详细模式）
        if args.verbose and articles:
            print(f"\n示例文章:")
            for i, article in enumerate(articles[:3]):
                print(f"\n{i+1}. {article.get('title', 'N/A')}")
                print(f"   📅 {article.get('publish_time', 'N/A')}")
                print(f"   👁️  {article.get('views', 'N/A')} 次阅读")
                print(f"   🔗 {article.get('url', 'N/A')}")
                desc = article.get('description', 'N/A')
                if len(desc) > 100:
                    desc = desc[:100] + "..."
                print(f"   📝 {desc}")
        
        print(f"\n🎉 爬取成功完成！")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断操作")
    except Exception as e:
        print(f"\n❌ 爬取过程中发生错误: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main() 