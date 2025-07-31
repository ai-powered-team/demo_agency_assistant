# 深蓝保文章内容提取工具

这个工具用于从已爬取的深蓝保文章URL中提取正文内容，并保存为纯文本文件。

## 🚀 功能特点

- ✅ **批量提取**: 自动遍历JSON文件中的所有文章URL
- ✅ **智能解析**: 精确识别文章正文内容，过滤导航和广告
- ✅ **错误处理**: 完善的重试机制和错误记录
- ✅ **进度跟踪**: 实时显示处理进度和统计信息
- ✅ **灵活配置**: 支持测试模式和自定义处理数量
- ✅ **详细报告**: 生成处理报告，记录成功和失败的详情

## 📁 文件结构

```
tools/
├── extract_article_content.py      # 核心提取逻辑
├── run_content_extraction.py       # 简化运行脚本
└── CONTENT_EXTRACTION_README.md    # 使用说明（本文件）

data/
├── shenlanbao_避坑指南_*.json      # 输入：爬取的文章列表
└── text/                           # 输出：提取的文本文件
    ├── 1784464437948104704_血泪教训！惠民保再便宜也别轻易买，90%的人都踩坑了.txt
    ├── extraction_report_*.json    # 处理报告
    └── ...
```

## 🎯 使用方法

### 方法1：简化运行（推荐）

```bash
cd tools
python run_content_extraction.py
```

脚本会自动：
1. 查找最新的JSON数据文件
2. 提供交互式选择界面
3. 显示处理进度和统计信息

### 方法2：直接运行

```bash
cd tools

# 测试模式（处理前5篇文章）
python extract_article_content.py --test

# 处理指定数量
python extract_article_content.py --max-articles 20

# 处理所有文章
python extract_article_content.py

# 自定义输出目录
python extract_article_content.py --output-dir /path/to/output
```

### 方法3：程序化使用

```python
from extract_article_content import ArticleContentExtractor

# 创建提取器
extractor = ArticleContentExtractor(output_dir="../data/text")

# 处理文章
result = extractor.process_articles_from_json(
    json_file="../data/shenlanbao_避坑指南_20250730_114302.json",
    max_articles=10  # 可选：限制处理数量
)

print(f"成功提取: {result['success_count']} 篇")
```

## 📊 输出格式

### 文本文件格式

每篇文章保存为独立的文本文件：

```
标题: 血泪教训！惠民保再便宜也别轻易买，90%的人都踩坑了
URL: https://www.shenlanbao.com/zhinan/1784464437948104704
提取时间: 2025-07-30 12:00:00
================================================================================

很多朋友会给自己和家人买份医疗险，生病能帮忙报销医疗费。

但池女士最近跟我们吐槽，她3万的手术费，保险一分钱没赔！想让我们看看到底咋回事？为啥别人的就能100%报销？

我们分析后发现，池女士挑错了产品。为了避免大家再踩坑，今天我们就来分享下，不同医疗险是怎么报销的，来看看怎么选才实用。

一、不同医疗险报销能力PK！哪种更实用？

很多医疗险都宣传能报销几百万的医疗费，但实际能赔多少，要看它的报销条件如何。
...
```

### 文件命名规则

```
{文章ID}_{文章标题}.txt
```

示例：
- `1784464437948104704_血泪教训！惠民保再便宜也别轻易买，90%的人都踩坑了.txt`
- `1922182155329286144_深蓝保—中国最大的保险测评平台，帮你买对保险不踩坑！.txt`

### 处理报告

每次运行都会生成处理报告 (`extraction_report_*.json`)：

```json
{
  "processing_time": "2025-07-30T12:00:00",
  "total_articles": 111,
  "success_count": 108,
  "failed_count": 3,
  "success_rate": "97.3%",
  "failed_urls": [
    {
      "url": "https://example.com/failed-article",
      "error": "Connection timeout",
      "timestamp": "2025-07-30T12:05:00"
    }
  ]
}
```

## ⚙️ 配置选项

### 命令行参数

| 参数 | 描述 | 默认值 | 示例 |
|------|------|--------|------|
| `--json-file`, `-f` | JSON数据文件路径 | 自动查找最新文件 | `-f data/articles.json` |
| `--output-dir`, `-o` | 输出目录 | `../data/text` | `-o /path/to/output` |
| `--max-articles`, `-m` | 限制处理数量 | 无限制 | `-m 50` |
| `--test`, `-t` | 测试模式（前5篇） | 关闭 | `-t` |

### 内容提取配置

脚本会按优先级尝试以下CSS选择器：

```python
# 主要选择器（基于用户提供的HTML结构）
'#zhinanLinkContains .rich-text-parse'  # 主要正文容器
'.rich-text-parse.underline-a'
'.contains .rich-text-parse'

# 备用选择器
'.article-content'
'.zhinan-content'
'#zhinanLinkContains'
'.contains'

# 兜底选择器
'.centerLeft'
'.zhinanContains'
'main'
'article'
```

## 🔧 工作原理

### 1. 页面访问
- 使用合适的User-Agent和HTTP头
- 支持重试机制（指数退避）
- 处理网络错误和超时

### 2. 内容提取
- 精确定位正文容器
- 移除广告、导航等无关内容
- 清理HTML标签，提取纯文本
- 格式化文本（去除多余空行等）

### 3. 文件保存
- 生成安全的文件名（移除特殊字符）
- 包含元数据（标题、URL、时间）
- UTF-8编码保存

### 4. 错误处理
- 记录失败的URL和原因
- 生成详细的处理报告
- 支持中断恢复

## 🧪 测试建议

### 首次使用

```bash
# 1. 先运行测试模式
cd tools
python run_content_extraction.py
# 选择 "1. 测试模式"

# 2. 检查输出结果
ls -la ../data/text/
cat ../data/text/[第一个文件名].txt
```

### 验证提取质量

```bash
# 检查文件大小（正常文章应该有几KB到几十KB）
ls -lh ../data/text/*.txt | head -10

# 查看处理报告
cat ../data/text/extraction_report_*.json | jq .
```

## ⚠️ 注意事项

### 1. 网络和服务器
- **请求频率**: 默认1秒间隔，避免对服务器造成压力
- **超时设置**: 15秒超时，适合大多数网络环境
- **重试机制**: 失败后会重试3次

### 2. 内容质量
- **验证提取**: 建议先用测试模式验证提取效果
- **特殊格式**: 图片、表格等会转为文本描述
- **链接处理**: 保留链接文本，但不保留URL

### 3. 存储空间
- **文件大小**: 每篇文章通常1-50KB
- **总空间**: 111篇文章大约需要5-10MB空间
- **备份建议**: 重要内容建议定期备份

### 4. 合规使用
- **使用目的**: 仅供学习和研究使用
- **版权说明**: 提取的内容版权归原网站所有
- **商用限制**: 请勿用于商业用途

## 🐛 故障排除

### 常见问题

1. **找不到JSON文件**
   ```bash
   # 先运行爬虫获取数据
   python run_crawler.py --category 避坑指南
   ```

2. **网络连接失败**
   - 检查网络连接
   - 增加超时时间
   - 查看错误日志

3. **内容提取失败**
   - 网站结构可能已变化
   - 检查CSS选择器是否正确
   - 查看处理报告了解具体原因

4. **文件保存失败**
   - 检查磁盘空间
   - 确认输出目录权限
   - 查看文件名是否包含特殊字符

### 调试技巧

```bash
# 查看详细错误信息
python extract_article_content.py --test 2>&1 | tee debug.log

# 检查特定文章
python -c "
from extract_article_content import ArticleContentExtractor
extractor = ArticleContentExtractor()
soup = extractor.get_page_content('https://www.shenlanbao.com/zhinan/1784464437948104704')
print('页面标题:', soup.find('title').get_text() if soup and soup.find('title') else 'None')
"
```

## 📈 性能优化

### 处理大量文章

```bash
# 分批处理，避免长时间运行
python extract_article_content.py --max-articles 50

# 后台运行（Linux/Mac）
nohup python extract_article_content.py > extraction.log 2>&1 &
```

### 提高成功率
- 在网络稳定时运行
- 适当增加请求间隔
- 监控处理报告，重新处理失败的文章

## 🆕 更新日志

- **v1.0** (2025-07-30): 初始版本，支持基本文章内容提取
  - 智能HTML解析
  - 批量处理功能
  - 错误处理和报告
  - 交互式界面

## 🤝 扩展开发

如需扩展功能，可以：

1. **自定义选择器**: 修改 `extract_article_content.py` 中的 `content_selectors`
2. **添加新的输出格式**: 扩展 `save_article_text` 方法
3. **集成其他网站**: 继承 `ArticleContentExtractor` 类
4. **并行处理**: 使用多线程或异步处理提高速度

## 📞 获取帮助

如果遇到问题或需要新功能，可以：
1. 查看处理报告了解详细错误信息
2. 使用测试模式验证功能
3. 检查网络连接和目标网站状态
4. 参考故障排除部分的解决方案 