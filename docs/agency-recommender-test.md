# 经纪人推荐测试工具使用文档

## 概述

经纪人推荐测试工具 (`test_agency_recommend.py`) 是一个交互式命令行程序，用于测试和验证 `AgencyRecommender` 的功能。该工具提供了友好的用户界面，支持多种预设对话场景，帮助开发者和测试人员验证推荐算法的准确性和有效性。

## 功能特性

### 🎯 核心功能

- **智能推荐分析**: 基于对话历史分析用户偏好，推荐最适合的经纪人
- **多场景测试**: 提供 5 种预设对话场景，覆盖不同用户类型
- **实时交互**: 支持动态添加对话消息，实时测试推荐效果
- **详细反馈**: 显示完整的分析过程和推荐理由

### 🎨 用户体验

- **彩色输出**: 使用颜色区分不同类型的信息（需要 colorama 库）
- **命令行历史**: 支持命令历史和编辑功能（需要 readline 库）
- **友好界面**: 清晰的帮助信息和状态显示
- **错误处理**: 完善的错误提示和异常处理

## 安装要求

### 必需依赖

- Python 3.8+
- 项目的所有依赖包（见 requirements.txt）
- 有效的 OpenAI API 配置

### 可选依赖

```bash
# 安装可选依赖以获得更好的用户体验
pip install colorama  # 彩色输出
# readline 通常已内置在 Python 中
```

### 环境配置

确保设置了必要的环境变量：

```bash
export AI_INSUR_OPENAI_API_KEY="your_api_key_here"
export AI_INSUR_OPENAI_BASE_URL="https://api.openai.com/v1"  # 可选
export AI_INSUR_OPENAI_MODEL="gpt-4"  # 可选
```

## 使用方法

### 启动程序

```bash
cd /path/to/august-demo
python test_agency_recommend.py
```

### 基本操作流程

#### 1. 查看帮助

```text
> help
```

显示所有可用命令和使用说明。

#### 2. 查看当前状态

```text
> status
```

显示当前用户ID、经纪人信息、对话历史等状态信息。

#### 3. 加载预设场景

```text
> scenario professional_need
```

加载"用户需要专业性强的经纪人"场景。

#### 4. 获取推荐

```text
> recommend
```

基于当前对话历史获取经纪人推荐。

#### 5. 切换经纪人

```text
> current 2
```

切换到经纪人ID为2的经纪人。

#### 6. 添加对话

```text
> add user 我需要更专业的建议
> add assistant 我会为您提供详细的数据分析
```

## 预设场景说明

### 1. professional_need - 专业需求场景

**适用情况**: 用户强调专业性和数据分析

- 当前经纪人: 张经理（友善型，3年经验）
- 用户特点: 注重专业性，要求数据支持
- 预期推荐: 专业型或咨询型经纪人

### 2. friendly_preference - 友善偏好场景

**适用情况**: 用户偏好温暖亲和的沟通方式

- 当前经纪人: 李专家（专业型，8年经验）
- 用户特点: 希望简单易懂的解释
- 预期推荐: 友善型经纪人

### 3. efficiency_focused - 效率导向场景

**适用情况**: 用户注重效率和快速决策

- 当前经纪人: 陈老师（可靠型，15年经验）
- 用户特点: 时间紧迫，要求高效服务
- 预期推荐: 热情型或专业型经纪人

### 4. trust_building - 信任建立场景

**适用情况**: 用户对保险销售缺乏信任

- 当前经纪人: 赵助理（热情型，2年经验）
- 用户特点: 需要客观分析，避免销售话术
- 预期推荐: 可靠型或咨询型经纪人

### 5. consultation_heavy - 咨询导向场景

**适用情况**: 用户需要详细咨询和解释

- 当前经纪人: 李专家（专业型，8年经验）
- 用户特点: 保险小白，需要详细解释
- 预期推荐: 咨询型或友善型经纪人

## 命令参考

### 基本命令

| 命令 | 说明 | 示例 |
|------|------|------|
| `help` | 显示帮助信息 | `help` |
| `status` | 显示当前状态 | `status` |
| `quit/exit` | 退出程序 | `quit` |

### 推荐命令

| 命令 | 说明 | 示例 |
|------|------|------|
| `recommend` | 获取经纪人推荐 | `recommend` |
| `scenario <name>` | 加载预设场景 | `scenario professional_need` |
| `current <id>` | 设置当前经纪人 | `current 2` |
| `agencies` | 显示经纪人列表 | `agencies` |

### 对话管理

| 命令 | 说明 | 示例 |
|------|------|------|
| `history` | 显示对话历史 | `history` |
| `add <role> <content>` | 添加对话消息 | `add user 我需要帮助` |
| `clear` | 清空对话历史 | `clear` |

## 输出说明

### 推荐结果解读

#### 🎯 推荐结果

- **当前经纪人**: 显示当前经纪人姓名和ID
- **推荐经纪人**: 显示推荐的经纪人姓名和ID
- **是否建议切换**: 是/否，基于匹配度差异判断
- **推荐置信度**: 0-100%，表示推荐的可信度

#### 📝 推荐理由

详细说明推荐的原因，包括：

- 匹配度分数对比
- 经纪人优势分析
- 用户需求匹配情况

#### 👤 用户偏好分析

分析用户的沟通偏好，包括：

- 沟通风格（专业型/情感型/效率型/咨询型/信任型）
- 沟通节奏（快节奏/慢节奏/互动型/倾听型）
- 决策风格（理性/感性/谨慎/果断）

#### 📊 沟通效果评估

评估当前沟通效果，包括：

- 沟通质量各维度评分
- 存在的问题识别
- 改进建议

### 思考过程

程序会显示分析的各个步骤：

- 🤔 分析对话历史
- 🤔 提取用户偏好
- 🤔 评估沟通效果
- 🤔 计算匹配度
- 🤔 生成推荐结果

## 测试建议

### 1. 基础功能测试

```bash
# 测试所有预设场景
scenario professional_need
recommend
scenario friendly_preference
recommend
# ... 其他场景
```

### 2. 动态对话测试

```bash
# 加载场景后添加新对话
scenario professional_need
add user 我对你的专业能力有疑问
recommend
```

### 3. 经纪人切换测试

```bash
# 测试不同经纪人的推荐效果
scenario professional_need
current 1
recommend
current 2
recommend
```

### 4. 边界情况测试

```bash
# 测试空对话历史
clear
recommend  # 应该提示需要对话历史

# 测试无效经纪人ID
current 999  # 应该提示经纪人不存在
```

## 故障排除

### 常见问题

#### 1. 程序启动失败

**问题**: 导入错误或配置问题
**解决**:

- 检查 Python 路径和依赖安装
- 确认环境变量配置
- 查看错误日志

#### 2. LLM 调用失败

**问题**: API 密钥无效或网络问题
**解决**:

- 验证 OpenAI API 密钥
- 检查网络连接
- 确认 API 配额

#### 3. 推荐结果异常

**问题**: JSON 解析错误或逻辑错误
**解决**:

- 查看详细日志
- 检查 LLM 响应格式
- 验证输入数据

#### 4. 颜色显示异常

**问题**: 终端不支持颜色或缺少 colorama
**解决**:

- 安装 colorama: `pip install colorama`
- 使用支持颜色的终端

### 日志分析

程序会输出详细的日志信息，包括：

- LLM 调用时间和响应长度
- 各步骤的执行状态
- 错误详情和堆栈跟踪

## 扩展开发

### 添加新场景

在 `load_preset_scenario` 方法中添加新的场景定义：

```python
"new_scenario": {
    "name": "场景描述",
    "current_agency_id": 1,
    "history": [
        {"role": ChatRole.USER, "content": "用户消息"},
        {"role": ChatRole.ASSISTANT, "content": "经纪人回复"}
    ]
}
```

### 自定义经纪人

修改 `setup` 方法中的 `current_agencies` 列表：

```python
{
    "agency_id": 6,
    "name": "新经纪人",
    "tone": AgencyTone.PROFESSIONAL,
    "experience_years": 10
}
```

### 添加新命令

在 `interactive_loop` 方法中添加新的命令处理逻辑。

## 相关文档

- [AgencyRecommender 设计文档](../DESIGN_AGENCY_RECOMMEND.md)
- [API 接口文档](../api/agency_recommendation.py)
- [项目整体文档](../README.md)
