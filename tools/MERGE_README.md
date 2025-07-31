# 保险坑点合并工具

这个工具用于将AI提取的保险坑点数据与现有的保险坑点数据合并，去除重复项并重新分配编号。

## 🎯 功能特点

- ✅ **智能合并**: 自动合并两个JSON文件的坑点数据
- ✅ **去重处理**: 基于标题自动识别并去除重复项  
- ✅ **重新编号**: 按分类重新分配连续编号
- ✅ **数据验证**: 验证文件格式和数据完整性
- ✅ **自动备份**: 输出文件存在时自动创建备份
- ✅ **格式兼容**: 保持与原始JSON格式的兼容性

## 📁 文件结构

```
tools/
├── merge_pits.py                     # 核心合并逻辑
├── run_merge_pits.py                 # 简化运行脚本
└── MERGE_README.md                   # 使用说明（本文件）

data/
├── pit_types_new.json                # 输入：现有坑点数据
├── insurance_pits_extracted.json     # 输入：AI提取的坑点数据
└── insurance_pits_merged.json        # 输出：合并后的坑点数据
```

## 📊 输入文件格式

### 现有坑点数据 (`pit_types_new.json`)

```json
[
  {
    "category": "产品比较与费率相关坑点",
    "items": [
      {
        "编号": 1,
        "标题": "费率与保障责任的不对等比较",
        "示例描述": "用自家保障差但便宜的产品去对比别家保障好但贵的产品。",
        "坑点原因": "进行"田忌赛马"式的误导，让客户以为占了便宜，实际保障打了折扣。"
      }
    ]
  }
]
```

### AI提取的坑点数据 (`insurance_pits_extracted.json`)

```json
{
  "extraction_time": "2025-07-30T15:30:00",
  "total_categories": 3,
  "total_pits": 15,
  "processed_files": 5,
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

## 🚀 使用方法

### 方法1：简化运行（推荐）

```bash
cd tools
python run_merge_pits.py
```

脚本会自动：
1. 检查输入文件是否存在
2. 显示文件信息和坑点数量
3. 展示合并计划
4. 请求用户确认
5. 执行合并并显示结果

### 方法2：命令行运行

```bash
cd tools

# 使用默认文件路径
python merge_pits.py

# 指定文件路径
python merge_pits.py \
  --extracted ../data/insurance_pits_extracted.json \
  --existing ../data/pit_types_new.json \
  --output ../data/insurance_pits_merged.json

# 不创建备份文件
python merge_pits.py --no-backup
```

### 方法3：程序化使用

```python
from merge_pits import PitsMerger

# 创建合并器
merger = PitsMerger()

# 执行合并
success = merger.merge_files(
    extracted_file="../data/insurance_pits_extracted.json",
    existing_file="../data/pit_types_new.json", 
    output_file="../data/insurance_pits_merged.json"
)

if success:
    print("合并成功！")
```

## 📈 合并过程

### 1. 数据加载与验证

```
📖 加载数据文件...
✅ 提取数据: 3 个分类
✅ 现有数据: 6 个分类
```

### 2. 按分类合并

```
📥 合并现有数据...
  • 产品比较与费率相关坑点: 添加 15 个现有坑点
  • 保障责任与理赔条款相关坑点: 添加 12 个现有坑点

📥 合并提取数据...
  • 产品比较与费率相关坑点: 添加 8 个提取坑点
  • 销售行为与专业伦理相关坑点: 添加 5 个提取坑点
```

### 3. 去重处理

```
🔍 检查重复项...
  • 产品比较与费率相关坑点: 去除 2 个重复项
  • 销售行为与专业伦理相关坑点: 去除 1 个重复项
```

### 4. 重新编号

```
🔢 重新分配编号...
  • 产品比较与费率相关坑点: 21 个坑点 (编号 1-21)
  • 保障责任与理赔条款相关坑点: 12 个坑点 (编号 1-12)
  • 销售行为与专业伦理相关坑点: 16 个坑点 (编号 1-16)
```

## 📊 输出格式

合并后生成的文件格式：

```json
{
  "merge_time": "2025-07-30T16:45:00.123456",
  "total_categories": 5,
  "total_pits": 67,
  "source_info": {
    "extraction_time": "2025-07-30T15:30:00",
    "processed_files": 15,
    "failed_files": []
  },
  "categories": [
    {
      "category": "产品比较与费率相关坑点",
      "items": [
        {
          "编号": 1,
          "标题": "费率与保障责任的不对等比较",
          "示例描述": "...",
          "坑点原因": "..."
        },
        {
          "编号": 2,
          "标题": "首年低保费误导",
          "示例描述": "...",
          "坑点原因": "..."
        }
      ]
    }
  ]
}
```

### 字段说明

- **merge_time**: 合并执行时间
- **total_categories**: 包含坑点的分类总数
- **total_pits**: 合并后的坑点总数
- **source_info**: 原始提取数据的元信息
- **categories**: 按分类整理的坑点数据
  - **编号**: 该分类内的连续编号（从1开始）

## ⚙️ 配置选项

### 命令行参数

| 参数 | 简写 | 描述 | 默认值 |
|------|------|------|--------|
| `--extracted` | `-e` | AI提取的坑点文件 | `../data/insurance_pits_extracted.json` |
| `--existing` | `-x` | 现有坑点文件 | `../data/pit_types_new.json` |
| `--output` | `-o` | 输出文件路径 | `../data/insurance_pits_merged.json` |
| `--no-backup` | `-n` | 不创建备份文件 | 默认创建备份 |

### 去重规则

当前的去重逻辑基于**标题完全匹配**：

```python
# 简单去重：相同标题视为重复
seen_titles = set()
for item in items:
    title = item.get('标题', '').strip()
    if title not in seen_titles:
        seen_titles.add(title)
        unique_items.append(item)
```

### 分类顺序

坑点按照以下固定顺序排列：

1. 产品比较与费率相关坑点
2. 保障责任与理赔条款相关坑点
3. 销售行为与专业伦理相关坑点
4. 续保、停售与产品稳定性相关坑点
5. 核保与健康告知相关坑点
6. 其他坑点

## 🧪 测试示例

### 创建测试数据

```bash
# 创建简单的测试数据
cat > ../data/test_extracted.json << 'EOF'
{
  "extraction_time": "2025-07-30T15:30:00",
  "total_categories": 1,
  "total_pits": 2,
  "categories": [
    {
      "category": "产品比较与费率相关坑点",
      "items": [
        {
          "编号": 1,
          "标题": "测试坑点1",
          "示例描述": "这是一个测试坑点",
          "坑点原因": "仅用于测试"
        }
      ]
    }
  ]
}
EOF

# 运行测试合并
python merge_pits.py \
  --extracted ../data/test_extracted.json \
  --existing ../data/pit_types_new.json \
  --output ../data/test_merged.json
```

### 验证结果

```bash
# 查看合并统计
jq '.total_pits, .total_categories' ../data/test_merged.json

# 查看各分类数量
jq '.categories[] | {category: .category, count: (.items | length)}' ../data/test_merged.json

# 验证编号连续性
jq '.categories[0].items[] | .编号' ../data/test_merged.json
```

## ⚠️ 注意事项

### 1. 文件兼容性

- 支持任一文件不存在的情况（会跳过不存在的文件）
- 自动处理不同的JSON格式结构
- 保持与原始数据格式的兼容性

### 2. 去重限制

- 当前仅基于标题进行去重
- 标题相同但描述不同的坑点会被视为重复
- 建议人工审核去重结果

### 3. 数据完整性

- 合并过程会验证必需字段的存在
- 缺少关键字段的坑点会被跳过
- 建议在合并后进行数据质量检查

### 4. 备份机制

- 输出文件存在时会自动创建 `.backup.json` 文件
- 使用 `--no-backup` 可以跳过备份创建
- 建议保留备份文件直到确认合并结果正确

## 🔧 自定义扩展

### 增强去重逻辑

```python
def enhanced_remove_duplicates(self, merged_data):
    """增强的去重逻辑"""
    for category, items in merged_data.items():
        unique_items = []
        
        for item in items:
            title = item.get('标题', '').strip()
            description = item.get('示例描述', '').strip()
            
            # 检查标题和描述的相似性
            is_duplicate = False
            for existing in unique_items:
                if self.is_similar(title, existing.get('标题', '')):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_items.append(item)
        
        merged_data[category] = unique_items
```

### 添加新分类

```python
# 修改 merge_pits.py 中的分类定义
self.categories = [
    "产品比较与费率相关坑点",
    "保障责任与理赔条款相关坑点",
    "销售行为与专业伦理相关坑点",
    "续保、停售与产品稳定性相关坑点",
    "核保与健康告知相关坑点",
    "你的新分类",  # 添加新分类
    "其他坑点"
]
```

## 🚨 故障排除

### 常见错误

#### 1. 文件格式错误

```bash
❌ JSON格式错误: ../data/insurance_pits_extracted.json - Expecting ',' delimiter

# 解决方案：检查JSON语法
python -m json.tool ../data/insurance_pits_extracted.json
```

#### 2. 文件不存在

```bash
❌ 输入文件都不存在，无法执行合并

# 解决方案：检查文件路径
ls -la ../data/insurance_pits_*.json
ls -la ../data/pit_types_new.json
```

#### 3. 权限错误

```bash
❌ 保存失败: [Errno 13] Permission denied

# 解决方案：检查目录权限
chmod 755 ../data
```

### 调试技巧

```bash
# 1. 验证输入文件格式
python -c "
import json
with open('../data/pit_types_new.json') as f:
    data = json.load(f)
print(f'Categories: {len(data)}')
print(f'Total items: {sum(len(cat[\"items\"]) for cat in data)}')
"

# 2. 检查合并结果
python -c "
from merge_pits import PitsMerger
merger = PitsMerger()
merger.merge_files(
    '../data/insurance_pits_extracted.json',
    '../data/pit_types_new.json', 
    '../data/debug_merged.json'
)
"

# 3. 比较合并前后的数据
diff <(jq -S . ../data/pit_types_new.json) <(jq -S '.categories' ../data/insurance_pits_merged.json)
```

## 📋 使用检查清单

合并前检查：
- [ ] 确认输入文件存在且格式正确
- [ ] 备份重要的现有数据文件
- [ ] 确认输出目录有写入权限

合并后验证：
- [ ] 检查总坑点数是否合理
- [ ] 验证各分类的编号是否连续
- [ ] 人工抽查合并质量
- [ ] 确认没有重要数据丢失

## 📞 获取帮助

如果遇到问题：

1. **查看详细日志**: 运行时的输出包含详细的处理信息
2. **验证文件格式**: 使用 `jq` 或 `python -m json.tool` 检查JSON格式
3. **检查权限**: 确保对输入和输出目录有适当的读写权限
4. **测试小数据集**: 先用少量数据测试合并逻辑

## 📝 更新日志

- **v1.0** (2025-07-30): 初始版本
  - 基本合并功能
  - 标题去重
  - 自动编号分配
  - 备份机制
  - 交互式界面 