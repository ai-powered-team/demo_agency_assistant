# 深蓝保网站爬虫工具

这是一个专门用于爬取深蓝保网站（https://www.shenlanbao.com）文章内容的工具。

## 功能特点

- ✅ 支持分页遍历，自动获取所有页面的文章
- ✅ 提取文章基本信息（标题、链接、描述、发布时间、阅读量等）
- ✅ 可选择获取文章详细内容
- ✅ 智能分页识别和处理
- ✅ 请求频率控制，避免对服务器造成压力
- ✅ 结果保存为JSON格式
- ✅ 完善的错误处理和重试机制

## 安装依赖

确保已安装所需的Python库：

```bash
# 安装项目依赖
uv sync

# 或手动安装爬虫相关依赖
pip install requests beautifulsoup4
```

## 使用方法

### 1. 基本使用

```bash
cd tools
python shenlanbao_crawler.py
```

### 2. 在代码中使用

```python
from shenlanbao_crawler import ShenlanbaoCrawler

# 创建爬虫实例
crawler = ShenlanbaoCrawler()

# 爬取指定URL的所有页面
articles = crawler.crawl_all_pages(
    start_url="https://www.shenlanbao.com/zhinan/list-23",
    max_pages=5,  # 限制最大页数
    include_content=False  # 是否获取文章详细内容
)

# 保存结果
crawler.save_to_json(articles, "articles.json")
```

### 3. 自定义配置

可以修改 `crawler_config.py` 文件中的配置：

```python
# 修改请求间隔
CRAWLER_CONFIG['request_delay'] = 2  # 秒

# 修改最大页数
CRAWLER_CONFIG['max_pages'] = 10

# 启用详细内容获取
CRAWLER_CONFIG['include_content'] = True
```

## 支持的页面类型

当前支持以下深蓝保页面的爬取：

- 避坑指南：https://www.shenlanbao.com/zhinan/list-23

## 输出格式

爬取的数据将保存为JSON文件，包含以下信息：

```json
{
  "crawl_time": "2024-01-01T10:00:00",
  "total_articles": 100,
  "articles": [
    {
      "title": "文章标题",
      "url": "https://www.shenlanbao.com/zhinan/1234567890",
      "description": "文章描述内容...",
      "publish_time": "2024-01-01",
      "views": "1234",
      "image_url": "https://example.com/image.jpg",
      "content": "文章详细内容..."  // 仅在include_content=True时包含
    }
  ]
}
```

## 主要类和方法

### ShenlanbaoCrawler

主要的爬虫类，包含以下方法：

- `crawl_all_pages(start_url, max_pages, include_content)`: 爬取所有分页
- `parse_page(url)`: 解析单个页面的文章列表
- `get_article_content(url)`: 获取文章详细内容
- `save_to_json(articles, filename)`: 保存结果到JSON文件

## 配置参数

### 请求配置
- `request_delay`: 请求间隔时间（秒）
- `timeout`: 请求超时时间（秒）
- `max_retries`: 最大重试次数

### 爬取配置
- `max_pages`: 最大爬取页数
- `include_content`: 是否获取文章详细内容

## 注意事项

1. **请遵守网站的robots.txt协议**：爬取前请检查目标网站的爬虫策略
2. **控制爬取频率**：默认设置了1秒的请求间隔，避免对服务器造成压力
3. **数据使用合规**：爬取的数据仅供学习和研究使用，请勿用于商业用途
4. **错误处理**：程序包含完善的错误处理机制，遇到网络错误会自动重试
5. **内容获取**：启用`include_content=True`会显著增加爬取时间，建议按需使用

## 故障排除

### 常见问题

1. **网络连接错误**
   - 检查网络连接
   - 确认目标网站可访问
   - 适当增加超时时间

2. **解析错误**
   - 网站结构可能已更新
   - 检查CSS选择器是否正确
   - 更新配置文件中的选择器

3. **分页识别失败**
   - 手动检查网站分页结构
   - 更新分页识别逻辑

### 调试技巧

1. 减少`max_pages`参数进行小规模测试
2. 查看控制台输出的详细日志
3. 检查保存的JSON文件内容

## 扩展开发

如需扩展支持其他网站，可以：

1. 继承`ShenlanbaoCrawler`类
2. 重写相关的解析方法
3. 更新配置文件中的选择器配置

## 许可证

本工具仅供学习和研究使用，请遵守目标网站的使用条款和相关法律法规。 