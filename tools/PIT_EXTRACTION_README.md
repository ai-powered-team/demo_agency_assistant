# 保险坑点提取工具

这个工具使用DeepSeek AI来分析保险相关文章，自动提取其中提到的保险坑点、陷阱和误导性销售行为，并按照预定义的分类进行整理。

## 🎯 功能特点

- ✅ **AI智能分析**: 使用DeepSeek大语言模型理解文章内容
- ✅ **结构化分类**: 按照6大分类自动整理保险坑点
- ✅ **批量处理**: 支持处理大量文本文件
- ✅ **成本估算**: 自动计算API调用成本
- ✅ **交互界面**: 用户友好的命令行界面
- ✅ **结果验证**: 自动验证提取结果的格式和完整性

## 📋 坑点分类体系

根据`pit_types_new.json`的格式，工具将提取的坑点分为以下6个类别：

1. **产品比较与费率相关坑点** - 涉及产品对比、价格、费率方面的误导
2. **保障责任与理赔条款相关坑点** - 涉及保障范围、理赔条件、免责条款等问题
3. **销售行为与专业伦理相关坑点** - 涉及销售人员不当行为、误导性宣传等
4. **续保、停售与产品稳定性相关坑点** - 涉及产品续保、停售、稳定性等问题
5. **核保与健康告知相关坑点** - 涉及健康告知、核保审查等问题
6. **其他坑点** - 不属于以上分类的其他保险相关坑点

## 📁 文件结构

```
tools/
├── get_pits.py                      # 核心提取逻辑
├── run_pit_extraction.py            # 简化运行脚本
└── PIT_EXTRACTION_README.md         # 使用说明（本文件）

data/
├── text/                            # 输入：文章文本文件
│   ├── 1784464437948104704_血泪教训！惠民保再便宜也别轻易买，90%的人都踩坑了.txt
│   └── ...
├── pit_types_new.json               # 参考：坑点分类格式
└── insurance_pits_extracted.json    # 输出：提取的坑点数据
```

## 🚀 使用方法

### 准备工作

#### 1. 获取DeepSeek API密钥

访问 [DeepSeek官网](https://platform.deepseek.com/) 注册账号并获取API密钥。

#### 2. 设置API密钥

```bash
# 方法1：设置环境变量（推荐）
export DEEPSEEK_API_KEY='your_api_key_here'

# 方法2：在运行时手动输入
# 脚本会提示输入API密钥
```

#### 3. 准备文本文件

确保`data/text`目录下有文章文本文件：

```bash
# 如果还没有文本文件，先运行内容提取工具
cd tools
python run_content_extraction.py
```

### 基本使用

#### 方法1：简化运行（推荐）

```bash
cd tools
python run_pit_extraction.py
```

脚本会自动：
1. 检查API密钥设置
2. 验证文本文件存在
3. 估算处理成本和时间
4. 提供交互式选择界面

#### 方法2：直接运行

```bash
cd tools

# 测试模式（处理前3个文件）
python get_pits.py --test

# 处理指定数量
python get_pits.py --max-files 10

# 处理所有文件
python get_pits.py

# 指定输出文件
python get_pits.py --output ../data/my_pits.json
```

#### 方法3：程序化使用

```python
from get_pits import InsurancePitExtractor

# 创建提取器
extractor = InsurancePitExtractor(
    api_key="your_api_key",
    text_dir="../data/text"
)

# 处理文件
results = extractor.process_all_files(max_files=5)

# 保存结果
if results:
    extractor.save_results(results, "output.json")
```

## 📊 输出格式

### 主要输出文件

工具会生成 `insurance_pits_extracted.json` 文件，包含以下结构：

```json
{
  "extraction_time": "2025-07-30T15:30:00",
  "total_categories": 5,
  "total_pits": 47,
  "processed_files": 15,
  "failed_files": [],
  "categories": [
    {
      "category": "产品比较与费率相关坑点",
      "items": [
        {
          "编号": 1,
          "标题": "首年低保费误导",
          "示例描述": "保险公司宣传首年保费很便宜，但不提后续保费大幅上涨",
          "坑点原因": "利用低价诱饵让客户忽略长期成本，续保时面临巨大经济压力"
        }
      ]
    }
  ]
}
```

### 各字段说明

- **extraction_time**: 提取时间
- **total_categories**: 有坑点的分类数量
- **total_pits**: 提取到的坑点总数
- **processed_files**: 处理的文件数量
- **failed_files**: 处理失败的文件列表
- **categories**: 按分类整理的坑点数据
  - **category**: 坑点分类名称
  - **items**: 该分类下的坑点列表
    - **编号**: 坑点在该分类中的序号
    - **标题**: 坑点的简洁标题
    - **示例描述**: 具体的坑点表现形式或案例
    - **坑点原因**: 为什么这是个坑，会造成什么问题

## ⚙️ 配置选项

### 命令行参数

| 参数 | 描述 | 默认值 | 示例 |
|------|------|--------|------|
| `--text-dir`, `-d` | 文本文件目录 | `../data/text` | `-d /path/to/text` |
| `--output`, `-o` | 输出文件路径 | `../data/insurance_pits_extracted.json` | `-o output.json` |
| `--max-files`, `-m` | 限制处理文件数 | 无限制 | `-m 10` |
| `--api-key`, `-k` | API密钥 | 从环境变量读取 | `-k your_key` |
| `--test`, `-t` | 测试模式（前3个文件） | 关闭 | `-t` |

### API配置

```python
# 在get_pits.py中可以调整的参数
{
    "model": "deepseek-chat",      # 使用的模型
    "temperature": 0.3,            # 创造性（0-1，越低越准确）
    "max_tokens": 4000,            # 最大输出长度
    "timeout": 60                  # 请求超时时间（秒）
}
```

## 💰 成本估算

### DeepSeek定价（2024年7月）

- **输入Token**: $0.14 / 1M tokens
- **输出Token**: $0.28 / 1M tokens

### 成本计算

```python
# 每个文件的平均成本估算
文件平均字符数 = 3000
输入Token数 = 3000 * 1.5 = 4500  # 中文字符转Token比率
输出Token数 = 500                # 预估输出长度
总Token数 = 4500 + 500 = 5000

单文件成本 = 5000 / 1000000 * 0.14 ≈ $0.0007
```

### 实际成本示例

| 文件数量 | 预估成本 | 处理时间 |
|----------|----------|----------|
| 3个文件 | $0.002 | 30秒 |
| 10个文件 | $0.007 | 2分钟 |
| 100个文件 | $0.070 | 20分钟 |

## 🔧 工作原理

### 1. 文本预处理

```python
def read_article_content(self, file_path):
    # 读取文件内容
    # 跳过元数据头部
    # 限制内容长度（避免Token超限）
    # 返回纯文本内容
```

### 2. 提示词工程

工具使用精心设计的提示词来指导AI提取：

```python
prompt = f"""
请分析以下保险相关文章，提取其中提到的保险坑点、陷阱、误导性销售行为等问题。

请按照以下6个分类进行整理：
1. 产品比较与费率相关坑点
2. 保障责任与理赔条款相关坑点
...

对于每个坑点，请提供：
- 标题：简洁概括这个坑点
- 示例描述：具体的坑点表现形式或案例
- 坑点原因：为什么这是个坑，会造成什么问题

文章内容：
{article_content}
"""
```

### 3. API调用

```python
def call_deepseek_api(self, prompt):
    # 构造请求负载
    # 发送POST请求到DeepSeek API
    # 处理响应和错误
    # 提取JSON格式的结果
```

### 4. 结果验证

```python
def parse_extraction_result(self, result_text):
    # JSON格式验证
    # 分类名称验证
    # 字段完整性检查
    # 数据清洗和标准化
```

### 5. 数据合并

```python
def merge_pits_data(self, all_pits_data):
    # 按分类合并多个文件的结果
    # 为每个坑点分配编号
    # 生成最终的结构化数据
```

## 🧪 测试建议

### 首次使用

```bash
# 1. 先用测试模式验证功能
cd tools
python run_pit_extraction.py
# 选择 "1. 测试模式"

# 2. 检查输出结果
cat ../data/insurance_pits_extracted.json | jq .
```

### 验证提取质量

```bash
# 查看提取统计
jq '.total_pits, .total_categories' ../data/insurance_pits_extracted.json

# 查看各分类的坑点数量
jq '.categories[] | {category: .category, count: (.items | length)}' ../data/insurance_pits_extracted.json

# 查看某个分类的具体坑点
jq '.categories[] | select(.category == "产品比较与费率相关坑点") | .items[0]' ../data/insurance_pits_extracted.json
```

## ⚠️ 注意事项

### 1. API使用

- **成本控制**: 建议先用测试模式验证效果
- **速率限制**: API有调用频率限制，工具已设置2秒间隔
- **网络稳定**: 确保网络连接稳定，避免中途断网

### 2. 数据质量

- **AI局限性**: AI可能误解某些内容，建议人工审核重要结果
- **上下文长度**: 过长的文章会被截断，可能影响理解
- **专业术语**: 复杂的保险术语可能影响提取准确性

### 3. 结果使用

- **参考价值**: 提取结果仅供参考，不构成专业建议
- **版权声明**: 原文内容版权归原作者所有
- **商用限制**: 请勿将结果用于商业用途

## 🐛 故障排除

### 常见问题

#### 1. API密钥问题

```bash
❌ 错误: 请设置DEEPSEEK_API_KEY环境变量

# 解决方案
export DEEPSEEK_API_KEY='your_api_key'
# 或者使用 --api-key 参数
```

#### 2. 文本文件不存在

```bash
❌ 错误: 文本目录不存在

# 解决方案：先提取文章内容
python run_content_extraction.py
```

#### 3. API调用失败

```bash
❌ API请求失败: Connection timeout

# 可能原因和解决方案：
# 1. 网络连接问题 - 检查网络
# 2. API密钥无效 - 验证密钥
# 3. 服务器临时故障 - 稍后重试
```

#### 4. JSON解析失败

```bash
❌ JSON解析失败: Expecting value: line 1 column 1

# 可能原因：
# 1. AI返回格式不正确
# 2. 网络传输中断
# 3. 内容过于复杂

# 解决方案：
# 1. 重新运行处理
# 2. 减少单次处理文件数
# 3. 检查原始文章内容质量
```

### 调试技巧

```bash
# 1. 查看详细错误信息
python get_pits.py --test 2>&1 | tee debug.log

# 2. 测试单个文件
python -c "
from get_pits import InsurancePitExtractor
extractor = InsurancePitExtractor(api_key='your_key')
result = extractor.extract_pits_from_file('path/to/file.txt')
print(result)
"

# 3. 验证API连接
curl -X POST https://api.deepseek.com/v1/chat/completions \
  -H "Authorization: Bearer your_api_key" \
  -H "Content-Type: application/json" \
  -d '{"model":"deepseek-chat","messages":[{"role":"user","content":"测试"}]}'
```

## 📈 性能优化

### 提高准确性

1. **文章质量**: 确保输入文章内容完整、格式正确
2. **内容长度**: 避免过长或过短的文章
3. **专业术语**: 为复杂术语提供上下文说明

### 提高效率

1. **批量大小**: 合理设置处理文件数量
2. **网络优化**: 在网络稳定时处理
3. **并行处理**: 对于大量文件，可考虑分批处理

### 成本控制

1. **测试优先**: 先用小批量测试效果
2. **内容筛选**: 只处理相关性高的文章
3. **结果复用**: 避免重复处理相同内容

## 🔄 扩展开发

### 自定义分类

```python
# 修改 get_pits.py 中的分类定义
self.categories = [
    "你的自定义分类1",
    "你的自定义分类2",
    # ...
]
```

### 自定义提示词

```python
def create_extraction_prompt(self, article_content):
    # 修改提示词内容
    # 调整分析指令
    # 改变输出格式要求
```

### 支持其他AI模型

```python
# 修改API配置
self.api_url = "https://other-ai-service.com/v1/chat"
self.headers = {"Authorization": "Bearer other_api_key"}
```

## 📞 获取帮助

如果遇到问题：

1. **查看错误日志**: 详细的错误信息通常能指出问题所在
2. **测试模式验证**: 使用小批量数据测试功能
3. **检查环境配置**: 确认API密钥、文件路径等配置正确
4. **网络连接**: 确保能正常访问DeepSeek API服务

## 📝 更新日志

- **v1.0** (2025-07-30): 初始版本
  - 支持6大分类的坑点提取
  - DeepSeek API集成
  - 批量处理功能
  - 交互式界面
  - 成本估算功能 