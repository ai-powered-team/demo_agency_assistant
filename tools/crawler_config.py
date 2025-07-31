#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
爬虫配置文件
"""

# 爬虫配置
CRAWLER_CONFIG = {
    # 请求配置
    'headers': {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    },
    
    # 请求间隔（秒）
    'request_delay': 1,
    
    # 超时设置（秒）
    'timeout': 10,
    
    # 重试次数
    'max_retries': 3,
    
    # 最大页数限制
    'max_pages': 50,
    
    # 是否获取文章详细内容
    'include_content': False,
    
    # 输出文件配置
    'output_dir': '../data',
    'output_filename_template': 'shenlanbao_articles_{timestamp}.json'
}

# 深蓝保网站配置
SHENLANBAO_CONFIG = {
    'base_url': 'https://www.shenlanbao.com',
    'target_urls': {
        '避坑指南': 'https://www.shenlanbao.com/zhinan/list-23',
        '小白入门': 'https://www.shenlanbao.com/zhinan/list-20',
        '购险必看': 'https://www.shenlanbao.com/zhinan/list-21',  
        '理赔科普': 'https://www.shenlanbao.com/zhinan/list-22'
    },
    
    # CSS选择器配置
    'selectors': {
        'article_items': 'div.article-item',
        'title': 'a.title',
        'description': 'div.desc',
        'publish_time': 'div.publish-time span',
        'views': 'div.view span',
        'image': 'img',
        'pagination': 'ul#m_fenye, ul.app-pagination',
        'content_selectors': [
            '.article-content',
            '.content',
            '.main-content', 
            '.post-content',
            'article',
            '.article-body'
        ]
    }
} 