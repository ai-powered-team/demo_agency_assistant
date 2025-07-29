# AI 保险数字分身 API 接口文档

## 目录

- [概述](#概述)
- [基础信息](#基础信息)
- [通用响应格式](#通用响应格式)
- [通用类型定义](#通用类型定义)
- [API 接口列表](#api-接口列表)
  - [1. 用户画像分析接口](#1-用户画像分析接口)
  - [2. 保险产品推荐接口](#2-保险产品推荐接口)
  - [3. 经纪人沟通接口](#3-经纪人沟通接口)
  - [4. 经纪人推荐接口](#4-经纪人推荐接口)
- [健康检查接口](#健康检查接口)
- [错误处理](#错误处理)
- [使用示例](#使用示例)
- [技术特性](#技术特性)
- [开发工具](#开发工具)

## 概述

AI 保险数字分身项目提供了一套完整的 RESTful API 接口，基于 FastAPI 框架构建，支持用户画像分析、产品推荐、经纪人沟通和经纪人推荐等核心功能。所有接口均采用异步设计，支持高并发访问，并使用 SSE (Server-Sent Events) 流式输出提供实时响应体验。

## 基础信息

- **基础URL**: `http://localhost:8000/api/v1`
- **协议**: HTTP/HTTPS
- **数据格式**: JSON
- **响应格式**: SSE 流式输出
- **字符编码**: UTF-8

## 通用响应格式

所有接口均采用 SSE (Server-Sent Events) 流式输出，每个事件的基本格式为：

```text
data: {"type": "response_type", "content": "响应内容", ...}

```

### 通用响应类型

#### 1. 思考过程响应 (ThinkingResponse)

```json
{
  "type": "thinking",
  "content": "正在分析用户画像...",
  "step": "analyze_conversation"
}
```

#### 2. 错误响应 (ErrorResponse)

```json
{
  "type": "error",
  "error": "错误类型",
  "details": "详细错误信息"
}
```

## 通用类型定义

以下是所有接口共用的 TypeScript 类型定义：

```typescript
// 基础响应类型，所有响应都继承自此类型
interface BaseResponse {
  type: string;
}

// 聊天角色枚举
type ChatRole = "user" | "assistant" | "system";

// 聊天消息类型
interface ChatMessage {
  role: ChatRole;                    // 消息角色
  content: string;                   // 消息内容
}

// 经纪人沟通风格枚举
type AgencyTone = "professional" | "friendly" | "enthusiastic" | "consultative" | "trustworthy";

// 保险经纪人信息类型
interface AgencyInfo {
  agency_id: number;                 // 经纪人ID
  name: string;                      // 经纪人姓名
  tone: AgencyTone;                  // 沟通风格
  experience_years: number;          // 从业年限
}

// 用户画像类型（所有字段都是可选的）
interface UserProfile {
  user_id?: number;                  // 用户ID

  // 基础身份维度
  name?: string;                     // 姓名
  gender?: string;                   // 性别：男/女/其他
  date_of_birth?: string;            // 出生日期：YYYY-MM-DD
  marital_status?: string;           // 婚姻状况：未婚/已婚/离异/丧偶
  residence_city?: string;           // 常住城市
  occupation_type?: string;          // 职业类型：企业员工/公务员/个体经营/企业主/自由职业/学生/退休
  industry?: string;                 // 所属行业

  // 女性特殊状态（仅女性）
  pregnancy_status?: string;         // 孕期状态：未怀孕/备孕期/孕早期(1-3月)/孕中期(4-6月)/孕晚期(7-9月)/产后恢复期
  childbearing_plan?: string;        // 生育计划：1年内/2年内/3年内/暂无计划

  // 家庭结构与责任维度
  family_structure?: string;         // 家庭结构：单身/夫妻/夫妻+子女/三代同堂/其他
  number_of_children?: number;       // 子女数量
  caregiving_responsibility?: string; // 赡养责任：无/赡养父母/赡养双方父母/其他
  monthly_household_expense?: number; // 月度家庭支出（元）
  mortgage_balance?: number;         // 房贷余额（元）
  is_family_financial_support?: string; // 是否家庭经济支柱：是/否/共同承担

  // 财务现状与目标维度
  annual_total_income?: number;      // 年总收入（万元）
  income_stability?: string;         // 收入稳定性：非常稳定/比较稳定/一般/不稳定
  annual_insurance_budget?: number;  // 年度保险预算（万元）

  // 健康与生活习惯维度
  overall_health_status?: string;    // 整体健康状况：非常健康/比较健康/一般/有慢性病/健康状况较差
  has_chronic_disease?: string;      // 慢性疾病情况：无/高血压/糖尿病/心脏病/其他
  smoking_status?: string;           // 吸烟情况：不吸烟/已戒烟/轻度吸烟/重度吸烟
  recent_medical_checkup?: string;   // 近期体检情况：1年内正常/1年内有异常/2年内正常/2年以上未体检
}

// 通用响应类型
interface ThinkingResponse extends BaseResponse {
  type: "thinking";                  // 固定值
  content: string;                   // 思考内容描述
  step: string;                      // 当前执行步骤标识符
}

interface AnswerResponse extends BaseResponse {
  type: "answer";                    // 固定值
  content: string;                   // 回答内容
  data?: Record<string, any>;        // 附加数据
}

interface ErrorResponse extends BaseResponse {
  type: "error";                     // 固定值
  error: string;                     // 错误类型描述
  details?: string;                  // 详细错误信息
}
```

## API 接口列表

### 1. 用户画像分析接口

**接口地址**: `POST /api/v1/profile/analyze`

**功能描述**: 基于用户对话历史和自定义画像信息，使用 mem0 框架进行智能用户画像分析，提取用户特征并持久化存储。

#### 用户画像分析请求参数类型

```typescript
// 用户画像分析请求类型
interface ProfileAnalysisRequest {
  user_id: number;                   // 用户唯一标识符
  session_id: number;                // 会话唯一标识符
  history_chats: ChatMessage[];      // 历史对话数组，按时间顺序排列
  custom_profile?: UserProfile;      // 可选的自定义用户画像信息
}
```

#### 用户画像分析响应参数类型

```typescript
// 特征数据类型
interface FeatureData {
  category_name: string;             // 特征分类名称
  feature_name: string;              // 特征名称
  feature_value: any;                // 特征值
  confidence: number;                // 置信度 (0.0-1.0)
  skipped: boolean;                  // 是否被用户跳过
}

// 用户特征提取响应
interface ProfileResponse extends BaseResponse {
  type: "profile";                   // 固定值
  features: FeatureData[];           // 新提取的特征数据列表
  message?: string;                  // 可选的说明信息
}

// 用户画像分析完成响应
interface UserProfileCompleteResponse extends BaseResponse {
  type: "profile_complete";          // 固定值
  message: string;                   // 完成消息
  profile_summary: Record<string, any>; // 画像摘要
  completion_rate: number;           // 完成率 (0.0-1.0)
}

// 用户画像分析接口的所有可能响应类型
type ProfileAnalysisResponse = ThinkingResponse | ProfileResponse | AnswerResponse | UserProfileCompleteResponse | ErrorResponse;
```

**请求格式示例**:

```json
{
  "user_id": 123,
  "session_id": 456,
  "history_chats": [
    {
      "role": "user",
      "content": "我是26岁的女性，在互联网公司工作"
    },
    {
      "role": "assistant", 
      "content": "了解，请问您的年收入大概是多少呢？"
    }
  ],
  "custom_profile": {
    "annual_total_income": 30.0,
    "annual_insurance_budget": 0.5
  }
}
```

**响应类型**:

- `ThinkingResponse`: 分析过程状态
- `ProfileResponse`: 提取的用户特征数据
- `AnswerResponse`: 询问用户更多信息
- `UserProfileCompleteResponse`: 画像分析完成
- `ErrorResponse`: 错误信息

**ProfileResponse 示例**:

```json
{
  "type": "profile",
  "features": [
    {
      "category_name": "basic_identity",
      "feature_name": "gender",
      "value": "女",
      "confidence": 0.8,
      "skipped": false
    },
    {
      "category_name": "financial_status",
      "feature_name": "annual_total_income",
      "value": 30.0,
      "confidence": 1.0,
      "skipped": false
    }
  ],
  "message": "成功提取了 2 个用户特征"
}
```

**特色功能**:

- 智能特征提取和置信度管理
- 主动询问缺失的重要信息
- 支持女性特殊状态分析
- 实时特征数据返回

### 2. 保险产品推荐接口

**接口地址**: `POST /api/v1/product/recommend`

**功能描述**: 基于用户画像和 ElasticSearch 双索引架构，使用四层匹配算法为用户推荐最适合的保险产品。

#### 产品推荐请求参数类型

```typescript
// 保险产品推荐请求类型
interface ProductRecommendationRequest {
  user_id: number;                   // 用户唯一标识符
  session_id: number;                // 会话唯一标识符
  custom_profile?: UserProfile;      // 可选的自定义用户画像信息
}
```

#### 产品推荐响应参数类型

```typescript
// 产品推荐信息类型
interface ProductInfo {
  product_name: string;              // 产品名称
  product_description: string;       // 产品简介
  product_type: string;              // 产品类型（重疾险、寿险、医疗险等）
  recommendation: string;            // 推荐理由，结合用户特征和产品推荐打分的结果
}

// 产品推荐响应类型
interface ProductRecommendResponse extends BaseResponse {
  type: "product_recommendation";    // 固定值
  products: ProductInfo[];           // 推荐的产品列表
  message?: string;                  // 可选的推荐说明信息
  analysis_summary?: string;         // 可选的分析摘要
}

// 保险产品推荐接口的所有可能响应类型
type ProductRecommendationResponse = ThinkingResponse | ProductRecommendResponse | ErrorResponse;
```

**请求格式示例**:

```json
{
  "user_id": 123,
  "session_id": 456,
  "custom_profile": {
    "gender": "女",
    "date_of_birth": "1998-01-01",
    "annual_total_income": 30.0,
    "annual_insurance_budget": 0.5,
    "occupation_type": "企业员工",
    "industry": "互联网"
  }
}
```

**响应类型**:

- `ThinkingResponse`: 推荐过程状态
- `ProductRecommendResponse`: 推荐的产品列表
- `ErrorResponse`: 错误信息

**ProductRecommendResponse 示例**:

```json
{
  "type": "product_recommend",
  "products": [
    {
      "product_name": "众安尊享e生2024",
      "product_summary": "高性价比百万医疗险，保障全面",
      "product_type": "医疗险",
      "recommendation_reason": "适合年轻女性，保费低廉，保障充足"
    }
  ],
  "user_analysis": "26岁女性互联网从业者，注重性价比",
  "recommendation_summary": "为您推荐了3款高性价比医疗险产品"
}
```

**特色功能**:

- 双索引架构提高查询效率
- 四层匹配算法（硬性筛选、需求匹配、偏好匹配、价值匹配）
- LLM 增强的产品信息生成
- 个性化推荐理由

### 3. 经纪人沟通接口

**接口地址**: `POST /api/v1/agency/communicate`

**功能描述**: 模拟不同风格的保险经纪人与用户进行智能对话，支持多种沟通风格，并能智能判断支付时机。

#### 经纪人沟通请求参数类型

```typescript
// 用户与经纪人沟通请求类型
interface AgencyCommunicationRequest {
  user_id: number;                   // 用户唯一标识符
  session_id: number;                // 会话唯一标识符
  history_chats: ChatMessage[];      // 历史对话数组，按时间顺序排列
  agency_id: number;                 // 当前要扮演的经纪人ID
  agencies: AgencyInfo[];            // 所有可用经纪人信息数组
}
```

#### 经纪人沟通响应参数类型

```typescript
// 支付流程响应
interface PaymentResponse extends BaseResponse {
  type: "payment";                   // 固定值
  message: string;                   // 引导支付的消息
  agency_id: number;                 // 当前经纪人ID
  agency_name: string;               // 经纪人姓名
  recommended_action: string;        // 建议的后续行动
}

// 经纪人沟通接口的所有可能响应类型
type AgencyCommunicationResponse = ThinkingResponse | AnswerResponse | PaymentResponse | ErrorResponse;
```

**请求格式示例**:

```json
{
  "user_id": 123,
  "session_id": 456,
  "history_chats": [
    {
      "role": "user",
      "content": "我想了解重疾险"
    }
  ],
  "agency_id": 1,
  "agencies": [
    {
      "agency_id": 1,
      "name": "张经理",
      "tone": "professional",
      "experience_years": 5
    }
  ]
}
```

**响应类型**:

- `ThinkingResponse`: 处理过程状态
- `AnswerResponse`: 经纪人回答
- `PaymentResponse`: 支付流程引导
- `ErrorResponse`: 错误信息

**AnswerResponse 示例**:

```json
{
  "type": "answer",
  "content": "根据您的情况，我建议您重点关注重疾险的保额配置...",
  "data": {
    "agency_id": 1,
    "agency_name": "张经理",
    "tone": "professional"
  }
}
```

**PaymentResponse 示例**:

```json
{
  "type": "payment",
  "message": "这款产品应该很适合您，我这就将保单信息推送给您",
  "agency_id": 1,
  "agency_name": "张经理",
  "recommended_action": "proceed_to_payment"
}
```

**支持的经纪人风格**:

- `professional`: 专业严谨型
- `friendly`: 亲和友善型
- `enthusiastic`: 热情积极型
- `consultative`: 咨询顾问型
- `trustworthy`: 可靠信赖型

### 4. 经纪人推荐接口

**接口地址**: `POST /api/v1/agency/recommend`

**功能描述**: 分析用户与当前经纪人的沟通效果，智能推荐最适合用户的经纪人。

#### 经纪人推荐请求参数类型

```typescript
// 推荐经纪人请求类型
interface AgencyRecommendRequest {
  user_id: number;                   // 用户唯一标识符
  history_chats: ChatMessage[];      // 历史对话数组，按时间顺序排列
  agency_id: number;                 // 当前经纪人ID
  agencies: AgencyInfo[];            // 所有可用经纪人信息数组
}
```

#### 经纪人推荐响应参数类型 (2025年7月优化版)

```typescript
// 推荐经纪人响应类型 - 优化版
interface AgencyRecommendResponse extends BaseResponse {
  type: "agency_recommend";          // 固定值
  current_agency_id: number;         // 当前经纪人ID
  recommended_agency_id: number;     // 推荐的经纪人ID
  should_switch: boolean;            // 是否建议切换
  recommendation_reason: string;     // 推荐理由（优化后：简化为一句话，≤50字）
  user_preference_analysis: string;  // 用户偏好分析（优化后：返回空字符串）
  communication_effectiveness: string; // 沟通效果评估（优化后：返回空字符串）
  confidence_score: number;          // 推荐置信度 (0.0-1.0)
}

// 推荐问题响应类型 - 优化版
interface QuestionRecommendResponse extends BaseResponse {
  type: "question_recommend";        // 固定值
  questions: string[];               // 推荐的问题列表（优化后：限制3个，每个≤30字）
  analysis_reason: string;           // 推荐理由（优化后：返回空字符串）
  conversation_stage: string;        // 当前对话阶段
  priority_level: string;            // 优先级（高/中/低）
}

// 观点分析响应类型
interface ViewpointAnalysisResponse extends BaseResponse {
  type: "viewpoint_analysis";        // 固定值
  agent_viewpoints: Array<{          // 经纪人观点列表
    viewpoint_content: string;       // 观点内容
    accuracy_assessment: string;     // 准确性评估：准确/部分准确/不准确
    objectivity_assessment: string;  // 客观性评估：客观/部分客观/主观偏向
    risk_level: string;              // 风险级别：低/中/高
    analysis_detail: string;         // 详细分析说明
  }>;
  overall_assessment: string;        // 整体评估
  risk_warnings: string[];           // 风险提醒列表
  suggestions: string[];             // 建议列表
}

// 经纪人推荐接口的所有可能响应类型
type AgencyRecommendationResponse = ThinkingResponse | AgencyRecommendResponse | QuestionRecommendResponse | ViewpointAnalysisResponse | AnswerResponse | ErrorResponse;
```

**请求格式示例**:

```json
{
  "user_id": 123,
  "history_chats": [
    {
      "role": "user",
      "content": "我需要专业的保险建议"
    },
    {
      "role": "assistant",
      "content": "好的，我来为您详细介绍"
    }
  ],
  "agency_id": 1,
  "agencies": [
    {
      "agency_id": 1,
      "name": "张经理",
      "tone": "professional",
      "experience_years": 5
    },
    {
      "agency_id": 2,
      "name": "李经理", 
      "tone": "friendly",
      "experience_years": 3
    }
  ]
}
```

**响应类型**:

- `ThinkingResponse`: 分析过程状态
- `AgencyRecommendResponse`: 经纪人推荐结果
- `QuestionRecommendResponse`: 推荐问题列表
- `ViewpointAnalysisResponse`: 经纪人观点分析
- `AnswerResponse`: 推荐总结和建议
- `ErrorResponse`: 错误信息

**AgencyRecommendResponse 示例 (优化版)**:

```json
{
  "type": "agency_recommend",
  "current_agency_id": 1,
  "recommended_agency_id": 2,
  "should_switch": true,
  "recommendation_reason": "推荐经纪人匹配度更高，沟通效果可能更好",
  "user_preference_analysis": "",
  "communication_effectiveness": "",
  "confidence_score": 0.85
}
```

**优化说明**：

- `recommendation_reason`: 简化为一句话（26字符），去除冗余描述
- `user_preference_analysis` 和 `communication_effectiveness`: 返回空字符串，减少冗余信息
- 保持其他字段不变，确保向后兼容性

**QuestionRecommendResponse 示例 (优化版)**:

```json
{
  "type": "question_recommend",
  "questions": [
    "保障范围有哪些？",
    "保费如何计算？",
    "理赔流程如何？"
  ],
  "analysis_reason": "",
  "conversation_stage": "深入了解",
  "priority_level": "高"
}
```

**优化说明**：

- `questions`: 严格限制为3个问题，每个问题精简到15字以内
- `analysis_reason`: 返回空字符串，减少冗余信息
- 保持问题的实用性和针对性

**ViewpointAnalysisResponse 示例**:

```json
{
  "type": "viewpoint_analysis",
  "agent_viewpoints": [
    {
      "viewpoint_content": "这款产品是市场上最好的重疾险",
      "accuracy_assessment": "部分准确",
      "objectivity_assessment": "主观偏向",
      "risk_level": "中",
      "analysis_detail": "产品确实有优势，但'最好'的表述过于绝对，缺乏客观对比"
    }
  ],
  "overall_assessment": "经纪人整体专业，但存在一定的销售导向",
  "risk_warnings": [
    "注意经纪人可能夸大产品优势",
    "建议多方对比产品信息"
  ],
  "suggestions": [
    "要求提供具体的产品对比数据",
    "咨询第三方专业意见"
  ]
}
```

**分析维度**:

- 用户沟通偏好分析（优化：基于关键词快速分析）
- 沟通效果评估（优化：简化评估模式）
- 经纪人匹配度计算
- 个性化推荐理由（优化：精简为一句话）
- 智能问题推荐（优化：限制3个问题，每个≤30字）
- 经纪人观点客观性分析（优化：条件性执行）

## 性能优化说明 (2025年7月)

### 优化目标

经纪人推荐接口经过深度性能优化，响应时间从原来的平均15秒降低到3秒以内。

### 优化策略

1. **Token优化**: 减少LLM输入和输出token数量
2. **智能跳过**: 短对话和简单场景使用默认设置
3. **精简输出**: 移除冗余信息，保留核心内容
4. **并行处理**: 保持高效的并行分析架构

### 性能指标

- **对话结束场景**: 0.002秒 (99.99%提升)
- **短对话场景**: 1.5秒 (90%提升)
- **长对话场景**: 3-5秒 (67-80%提升)

### 向后兼容性

所有字段结构保持不变，确保现有客户端代码无需修改。优化主要体现在：

- 响应速度大幅提升
- 冗余字段返回空字符串
- 核心功能和数据结构完全保持

## 健康检查接口

**接口地址**: `GET /health`

**功能描述**: 服务健康状态检查

### 健康检查响应类型

```typescript
// 健康检查响应类型
interface HealthCheckResponse {
  status: string;                    // 服务状态：healthy/unhealthy
  service: string;                   // 服务名称
  version: string;                   // 服务版本
}
```

**响应格式示例**:

```json
{
  "status": "healthy",
  "service": "AI 保险数字分身",
  "version": "1.0.0"
}
```

## 错误处理

### 常见错误码

| HTTP状态码 | 错误类型 | 说明 |
|-----------|----------|------|
| 400 | Bad Request | 请求参数错误 |
| 422 | Unprocessable Entity | 参数验证失败 |
| 500 | Internal Server Error | 服务器内部错误 |
| 503 | Service Unavailable | AI服务暂时不可用 |

### 错误响应示例

```json
{
  "type": "error",
  "error": "参数验证失败",
  "details": "user_id 字段不能为空"
}
```

## 使用示例

### 完整的用户画像分析流程

```bash
curl -X POST "http://localhost:8000/api/v1/profile/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 123,
    "session_id": 456,
    "history_chats": [
      {
        "role": "user",
        "content": "我是26岁的女性，在互联网公司工作，年收入30万"
      }
    ],
    "custom_profile": {
      "annual_insurance_budget": 0.5
    }
  }'
```

### 产品推荐请求

```bash
curl -X POST "http://localhost:8000/api/v1/product/recommend" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 123,
    "user_profile": {
      "gender": "女",
      "date_of_birth": "1998-01-01",
      "annual_total_income": 30.0,
      "annual_insurance_budget": 0.5
    }
  }'
```

## 技术特性

- **异步处理**: 所有接口均采用异步设计，支持高并发
- **流式输出**: 使用 SSE 提供实时响应体验
- **类型安全**: 使用 TypedDict 确保数据类型安全
- **智能分析**: 集成 LangGraph 和 LLM 提供智能分析能力
- **持久化存储**: 支持 MySQL/SQLite 双环境数据存储
- **错误处理**: 完善的错误处理和降级机制

## 开发工具

项目提供了完整的交互式测试工具：

- `test_profile_analyzer.py`: 用户画像分析测试工具
- `test_product_recommend.py`: 产品推荐测试工具  
- `test_agency_communication.py`: 经纪人沟通测试工具
- `test_agency_recommend.py`: 经纪人推荐测试工具

详细使用方法请参考项目文档目录中的相关文档。
