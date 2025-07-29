# ProfileAnalyzer 交互式测试工具

## 概述

`test_profile_analyzer.py` 是一个专门的交互式命令行测试程序，用于测试用户画像分析功能。该工具提供了友好的交互界面和丰富的测试场景，帮助开发者快速验证用户画像分析器的功能。

## 功能特性

- **🎯 交互式界面**: 提供友好的命令行交互体验
- **🗄️ 临时数据库**: 每次启动创建新的临时 SQLite 数据库，避免测试数据污染
- **🎨 彩色输出**: 日志信息以灰色显示，响应结果高亮显示
- **📊 实时监控**: 显示 LLM 调用耗时、token 消耗、prompt 预览等详细信息
- **🧪 预设场景**: 提供多个预设测试场景快速验证功能

## 启动测试程序

```bash
python test_profile_analyzer.py
```

## 基本命令

| 命令 | 说明 | 示例 |
|------|------|------|
| `help` | 显示帮助信息 | `help` |
| `scenario <n>` | 加载预设测试场景 | `scenario young_female` |
| `test <message>` | 发送测试消息 | `test 我是一个30岁的女性` |
| `custom <json>` | 设置自定义画像 | `custom {"gender": "女", "annual_total_income": 50.0}` |
| `analyze` | 执行完整分析 | `analyze` |
| `profile` | 显示当前用户画像 | `profile` |
| `history` | 显示对话历史 | `history` |
| `status` | 显示系统状态 | `status` |
| `clear` | 清空对话历史 | `clear` |
| `exit/quit` | 退出程序 | `exit` |

## 预设测试场景

| 场景名 | 描述 | 特点 |
|--------|------|------|
| `young_female` | 25岁女性，互联网公司员工 | 年轻、单身、收入30万 |
| `middle_aged_male` | 40岁男性工程师 | 已婚、有孩子、收入80万 |
| `pregnant_woman` | 30岁孕妇，银行员工 | 怀孕中期、已婚、稳定收入 |

## 使用示例

### 1. 快速测试场景

```bash
> scenario young_female
✅ 已加载测试场景: young_female
📝 场景包含 4 条消息
🔍 开始分析用户画像...
```

### 2. 自定义测试

```bash
> test 我是一个35岁的男性，在银行工作
> custom {"annual_total_income": 60.0, "marital_status": "已婚"}
```

### 3. 查看分析结果

```bash
> profile
👤 当前用户画像 (用户ID: 12345):

  📂 basic_identity:
    • gender: 女 (置信度: 1.00)
    • marital_status: single (置信度: 0.80)

  📈 完成度: 45.2%
```

## 输出说明

测试程序会显示详细的执行过程：

- **日志信息**（灰色）: LLM 调用统计、数据库操作等
- **思考过程**（🤔）: Agent 的思考步骤
- **特征提取**（✨）: 高亮显示提取的特征数据，包括置信度和来源
- **问题询问**（❓）: Agent 生成的问题
- **完成状态**（🎉）: 分析完成和完成度

## 依赖要求

测试程序需要以下依赖：

```bash
# 必需依赖
pip install mem0ai sqlalchemy[asyncio] aiosqlite

# 可选依赖（推荐，提供彩色输出）
pip install colorama
```

## 环境配置

确保设置了必要的环境变量：

```bash
# 必须设置
export AI_INSUR_OPENAI_API_KEY="your_openai_api_key_here"

# 可选设置
export AI_INSUR_OPENAI_MODEL="gpt-4"
export AI_INSUR_LOG_LEVEL="INFO"
```

## 故障排除

### 常见问题

**Q: 程序启动失败，提示数据库连接错误**
A: 检查是否有足够的磁盘空间创建临时数据库文件

**Q: 没有彩色输出**
A: 安装 colorama：`pip install colorama`

**Q: LLM 调用失败**
A: 检查 OpenAI API 密钥配置和网络连接

### 调试模式

如果遇到问题，可以启用调试模式：

```bash
export AI_INSUR_LOG_LEVEL=DEBUG
python test_profile_analyzer.py
```

## 注意事项

1. **API 费用**: 程序会调用 OpenAI API，请注意使用费用
2. **数据隔离**: 每次启动都会创建新的临时数据库，确保测试独立性
3. **中文支持**: 程序完全支持中文输入输出
4. **网络要求**: 需要稳定的网络连接访问 OpenAI 服务
