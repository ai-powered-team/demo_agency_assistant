# ProductRecommender 交互式测试工具

## 概述

`test_product_recommend.py` 是一个专门的交互式命令行测试程序，用于测试产品推荐功能。该工具提供了多个预设用户画像场景和灵活的配置选项，帮助开发者快速验证产品推荐器的功能。

## 功能特性

- **🎯 预设用户画像场景**: 提供5个典型用户场景，方便快速测试
- **🗄️ 临时数据库**: 每次启动创建新的临时 SQLite 数据库，避免测试数据污染
- **🎨 彩色输出**: 支持彩色终端输出，提升用户体验
- **⚙️ 字段微调**: 支持修改用户画像中的单个字段
- **📊 自定义画像**: 支持JSON格式设置完整用户画像

## 启动测试程序

```bash
python test_product_recommend.py
```

## 基本命令

| 命令 | 说明 | 示例 |
|------|------|------|
| `help` | 显示帮助信息 | `help` |
| `status` | 显示当前状态和用户画像 | `status` |
| `recommend` | 基于当前用户画像获取产品推荐 | `recommend` |
| `scenario <n>` | 加载预设用户画像场景 | `scenario young_tech` |
| `profile <json>` | 设置用户画像（JSON格式） | `profile {"gender": "女", "annual_total_income": 50.0}` |
| `modify <field> <value>` | 修改用户画像中的单个字段 | `modify annual_insurance_budget 10.0` |
| `quit/exit/q` | 退出程序 | `quit` |

## 预设用户画像场景

| 场景名 | 描述 | 特点 |
|--------|------|------|
| `young_tech` | 25岁互联网从业者 | 男性、未婚、北京、年收入30万、预算3万 |
| `family_man` | 35岁已婚男性 | 已婚、有2个孩子、上海、年收入80万、预算8万 |
| `pregnant_woman` | 30岁孕妇 | 女性、已婚、深圳、孕中期、年收入60万、预算6万 |
| `high_income` | 40岁高收入人群 | 男性、已婚、北京、企业主、年收入150万、预算20万 |
| `senior_citizen` | 55岁临近退休 | 女性、已婚、广州、有高血压、年收入45万、预算5万 |

## 使用示例

### 1. 快速测试场景

```bash
> scenario young_tech
✅ 已加载预设场景: 25岁互联网从业者
📝 场景包含 13 个用户特征
> recommend
🔍 正在获取产品推荐...
```

### 2. 微调用户特征

```bash
> scenario family_man
> modify annual_insurance_budget 10.0
✅ 已修改字段 annual_insurance_budget = 10.0
> recommend
```

### 3. 自定义用户画像

```bash
> profile {"gender": "女", "annual_total_income": 50.0, "marital_status": "未婚"}
✅ 用户画像已更新
> recommend
```

## 输出说明

测试程序会显示详细的推荐过程：

- **思考过程**（🤔）: 推荐器的分析步骤
- **产品推荐**（🎯）: 推荐的产品列表，包括产品名称、类型、简介和推荐理由
- **错误信息**（❌）: 如果推荐过程中出现错误，会显示详细的错误信息

## 环境配置

确保设置了必要的环境变量：

```bash
# 必须设置
export AI_INSUR_OPENAI_API_KEY="your_openai_api_key_here"

# 可选设置
export AI_INSUR_OPENAI_MODEL="gpt-4"
export AI_INSUR_LOG_LEVEL="INFO"
```

## 依赖要求

测试程序需要以下依赖：

```bash
# 必需依赖
pip install sqlalchemy[asyncio] aiosqlite

# 可选依赖（推荐，提供彩色输出）
pip install colorama
```

## 故障排除

### 常见问题

**Q: 程序启动失败，提示配置验证失败**
A: 检查环境变量配置，确保设置了 `AI_INSUR_OPENAI_API_KEY`

**Q: 没有彩色输出**
A: 安装 colorama：`pip install colorama`

**Q: 推荐结果为空**
A: 检查用户画像是否完整，确保包含必要的字段如收入、预算等

**Q: JSON格式错误**
A: 确保使用正确的JSON格式，字段名使用双引号

### 调试模式

如果遇到问题，可以启用调试模式：

```bash
export AI_INSUR_LOG_LEVEL=DEBUG
python test_product_recommend.py
```

## 扩展功能

### 添加新场景

可以在程序中添加新的预设场景：

```python
"new_scenario": {
    "name": "新场景描述",
    "profile": {
        "gender": "男",
        "age": 30,
        "annual_total_income": 50.0,
        # 更多字段...
    }
}
```

### 自定义字段

支持修改用户画像中的任何字段，包括：

- 基本信息：`gender`, `age`, `marital_status`
- 收入信息：`annual_total_income`, `annual_insurance_budget`
- 地理信息：`city`, `province`
- 健康信息：`health_conditions`
- 其他特征：`occupation`, `education_level`

## 注意事项

1. **API 费用**: 程序会调用 OpenAI API，请注意使用费用
2. **数据隔离**: 每次启动都会创建新的临时数据库，确保测试独立性
3. **中文支持**: 程序完全支持中文输入输出
4. **网络要求**: 需要稳定的网络连接访问 OpenAI 服务
5. **画像完整性**: 确保用户画像包含足够的信息以获得准确的推荐结果
