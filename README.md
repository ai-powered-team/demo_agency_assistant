# AI 保险数字分身项目（添加智能对话助理）

基于 FastAPI + LangGraph 构建的智能保险推荐服务，为用户提供个性化的保险产品推荐和智能经纪人沟通服务。

## 项目特性

- 🤖 **智能用户画像分析**: 基于对话历史和用户信息，智能分析用户需求
- 🎯 **个性化产品推荐**: 结合用户画像和产品库，推荐最适合的保险产品
- 💬 **智能经纪人沟通**: 模拟经纪人对话，并为用户提供专业建议
- 🧠 **智能对话助理**: 模拟第三方助理帮助用户和保险经纪进行对话，在测试场景中AI模拟客户和第三方助理，真人扮演经纪人
- 🔄 **流式响应**: 实时返回 AI 思考过程和结果
- 📊 **结构化数据**: 使用 TypedDict 确保数据类型安全
- 🚀 **异步处理**: 全异步架构，支持高并发

## 技术栈

- **Python 3.11.7**: 编程语言
- **FastAPI**: 高性能 Web 框架
- **LangGraph**: AI 工作流编排
- **LangChain**: LLM 应用开发框架
- **uvicorn**: ASGI 服务器
- **uv**: 包管理工具

## 快速开始

### 1. 环境准备

确保已安装 Python 3.11.7 和 uv 包管理工具。

### 2. 克隆项目

```bash
git clone https://github.com/ai-powered-team/august-demo.git
cd august-demo
```

### 3. 安装依赖

需要提前安装 [uv](https://docs.astral.sh/uv/)。

```bash
uv sync
```

### 4. 配置环境变量

复制并编辑环境变量文件：

```bash
cp .env .env.local
```

编辑 `.env.local` 文件，设置必要的配置：

```bash
# 必须设置的配置
AI_INSUR_OPENAI_API_KEY=your_openai_api_key_here
AI_INSUR_DEEPSEEK_API_KEY=your_deepseek_api_key_here
AI_INSUR_QWEN_API_KEY=your_qwen_api_key_here

# 可选配置
AI_INSUR_HOST=0.0.0.0
AI_INSUR_PORT=8000
AI_INSUR_OPENAI_MODEL=gpt-4
```

### 5. 启动服务

```bash
# 开发模式
uv run python main.py

# 或使用 uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 6. 验证服务

访问健康检查端点：

```bash
curl http://localhost:8000/health
```

### 7. 测试用户画像分析功能

使用交互式测试程序快速验证用户画像分析功能：

```bash
python test_profile_analyzer.py
```

然后在交互界面中输入：

```bash
> scenario young_female  # 加载预设测试场景
> profile               # 查看提取的用户画像
```

详细使用方法请参考 [ProfileAnalyzer 交互式测试工具文档](./docs/profile-analyzer-test.md)。

### 8. 测试产品推荐功能

使用交互式测试程序快速验证产品推荐功能：

```bash
python test_product_recommend.py
```

然后在交互界面中输入：

```bash
> scenario young_tech    # 加载预设用户画像场景
> recommend             # 获取产品推荐
```

详细使用方法请参考 [ProductRecommender 交互式测试工具文档](./docs/product-recommender-test.md)。

### 9. 测试经纪人沟通功能

使用交互式测试程序快速验证经纪人沟通功能：

```bash
python test_agency_communication.py
```

然后在交互界面中输入：

```bash
> agencies              # 查看所有可用经纪人
> switch 2              # 切换到亲和友善型经纪人
> chat 我想了解重疾险   # 开始对话
```

详细使用方法请参考 [AgencyCommunicator 交互式测试工具文档](./docs/agency-communication-test.md)。

### 10. 测试经纪人推荐功能

使用交互式测试程序快速验证经纪人推荐功能：

```bash
python test_agency_recommend.py
```

然后在交互界面中输入：

```bash
> scenario professional_need  # 加载预设对话场景
> recommend                   # 获取经纪人推荐
> current 2                   # 切换到其他经纪人
> recommend                   # 重新获取推荐
```

详细使用方法请参考 [经纪人推荐测试工具文档](./docs/agency-recommender-test.md)。

### 11. 智能对话助理功能

使用命令行对话系统验证智能助理功能：

```bash
python api/insurance_chat_system.py
```

**功能特性：**
- 🧠 **智能意图识别**: 实时分析对话意图，包括：
  - 讨论主题识别
  - 涉及术语提取
  - 涉及产品分析
  - 经纪人阶段性意图识别
  - 经纪人本句话意图识别
  - 用户当下需求分析
- 💡 **实时建议显示**: 为模拟保险用户的 AI 提供实时对话建议
- 🤖 **角色扮演测试**: 在当前测试模式中由 AI 扮演保险客户，真人扮演保险经纪人
- 🔄 **双模型协作**: DeepSeek API 处理对话，Qwen3 API 处理意图识别

**技术架构：**
- **对话引擎**: 基于 LangChain + DeepSeek API
- **意图识别**: 基于 Qwen3 API 的多维度意图分析
- **交互方式**: 命令行实时对话界面
- **角色分工**: AI 客户 + 真人经纪人 + AI 助理建议

## API 接口

本项目提供了完整的 RESTful API 接口，支持用户画像分析、产品推荐、经纪人沟通等核心功能。

### 核心接口列表

| 接口路径 | 方法 | 功能描述 |
|---------|------|----------|
| `/api/v1/profile/analyze` | POST | 用户画像分析 - 基于对话历史智能提取用户特征 |
| `/api/v1/product/recommend` | POST | 保险产品推荐 - 基于用户画像推荐最适合的保险产品 |
| `/api/v1/agency/communicate` | POST | 经纪人沟通 - 模拟不同风格的保险经纪人对话 |
| `/api/v1/agency/recommend` | POST | 经纪人推荐 - 智能推荐最适合用户的经纪人 |
| `/api/v1/agency/assistant` | POST | 智能对话助理 - 带意图识别的保险对话系统 |
| `/health` | GET | 健康检查 - 服务状态检查 |

### 接口特性

- **流式响应**: 所有接口均采用 SSE (Server-Sent Events) 流式输出
- **异步处理**: 全异步架构，支持高并发访问
- **智能分析**: 集成 LangGraph 和 LLM 提供智能分析能力
- **类型安全**: 使用 TypedDict 确保数据类型安全
- **错误处理**: 完善的错误处理和降级机制

### 详细文档

完整的 API 接口文档请参考：[API.md](./API.md)

在线 API 文档请访问：`http://localhost:8000/docs`

## 项目结构

```text
august-demo/
├── main.py                          # 主入口文件
├── API.md                           # API 接口文档
├── test_profile_analyzer.py          # ProfileAnalyzer 交互式测试程序
├── test_product_recommend.py        # ProductRecommender 交互式测试程序
├── test_agency_communication.py     # AgencyCommunicator 交互式测试程序
├── test_agency_recommend.py         # AgencyRecommender 交互式测试程序
├── api/                             # 接口层
│   ├── __init__.py                  # API 路由注册
│   ├── profile_analysis.py           # 用户画像分析接口
│   ├── product_recommendation.py    # 产品推荐接口
│   ├── agency_communication.py      # 经纪人沟通接口
│   ├── agency_recommendation.py     # 经纪人推荐接口
│   └── insurance_chat_system.py     # 智能对话助理系统
├── agent/                           # 逻辑层
│   ├── profile_analyzer.py           # 用户画像分析器
│   ├── product_recommender.py       # 产品推荐器
│   ├── agency_communicator.py       # 经纪人沟通器
│   └── agency_recommender.py        # 经纪人推荐器
├── util/                            # 工具层
│   ├── config.py                     # 配置管理
│   ├── logger.py                    # 日志配置
│   └── types.py                     # 类型定义
├── docs/                            # 文档目录
│   ├── profile-analyzer-test.md      # ProfileAnalyzer 测试工具文档
│   ├── product-recommender-test.md  # ProductRecommender 测试工具文档
│   └── agency-communication-test.md # AgencyCommunicator 测试工具文档
└── .agent/                          # 项目文档目录
    └── OVERALL.md                   # 项目整体文档
```

## 测试工具

项目提供了三个专门的交互式测试工具，帮助开发者快速验证各个功能模块：

### ProfileAnalyzer 交互式测试工具

用于测试用户画像分析功能，提供预设场景和实时监控。

详细使用方法请参考 [ProfileAnalyzer 交互式测试工具文档](./docs/profile-analyzer-test.md)。

### ProductRecommender 交互式测试工具

用于测试产品推荐功能，支持多种用户画像场景和字段微调。

详细使用方法请参考 [ProductRecommender 交互式测试工具文档](./docs/product-recommender-test.md)。

### AgencyCommunicator 交互式测试工具

用于测试经纪人沟通功能，支持5种不同风格的经纪人和智能支付判断。

详细使用方法请参考 [AgencyCommunicator 交互式测试工具文档](./docs/agency-communication-test.md)。

### AgencyRecommender 交互式测试工具

用于测试经纪人推荐功能，支持多种预设对话场景和动态对话测试。

详细使用方法请参考 [AgencyRecommender 交互式测试工具文档](./docs/agency-recommender-test.md)。

### 代码规范

项目遵循以下代码规范：

- 使用 PEP8 代码格式
- 为所有函数和类添加类型注解
- 使用 TypedDict 定义数据结构
- 所有 API 接口使用异步实现
- 中文注释和文档

### 环境变量

所有配置参数都使用 `AI_INSUR_` 前缀：

- `AI_INSUR_HOST`: 服务器地址
- `AI_INSUR_PORT`: 服务器端口
- `AI_INSUR_OPENAI_API_KEY`: OpenAI API 密钥
- `AI_INSUR_OPENAI_MODEL`: 使用的 OpenAI 模型
- `AI_INSUR_DEEPSEEK_API_KEY`: DeepSeek API 密钥（对话助理功能）
- `AI_INSUR_QWEN_API_KEY`: Qwen3 API 密钥（意图识别功能）
- `AI_INSUR_LOG_LEVEL`: 日志级别

## 部署

### 生产环境部署

```bash
uvicorn main:app --host 0.0.0.0 --port $AI_INSUR_PORT
```

### Docker 部署

```dockerfile
FROM python:3.11.7-slim

WORKDIR /app
COPY . .

RUN pip install uv
RUN uv sync

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 贡献

欢迎提交 Issue 和 Pull Request 来改进项目。
