# RAG 保险坑点检测系统

## 概述

本系统使用 Retrieval-Augmented Generation (RAG) 技术，将保险坑点知识库集成到智能对话助理中，为AI用户提供实时的风险提示和专业建议。

## 技术架构

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   JSON数据源    │───▶│   数据预处理     │───▶│   向量数据库    │
│insurance_pits_  │    │  JSONLoader +    │    │   FAISS/Chroma  │
│merged.json      │    │  TextSplitter    │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
┌─────────────────┐    ┌──────────────────┐             │
│   用户对话      │───▶│   意图分析       │             │
│   (经纪人话语)  │    │   + 语义检索     │◀────────────┘
└─────────────────┘    └──────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │   建议生成       │
                       │  (LLM + 坑点)    │
                       └──────────────────┘
```

## 核心组件

### 1. 数据加载模块 (`agent/rag_pit_detector.py`)

**功能**:
- 使用 `langchain_community.document_loaders.JSONLoader` 解析保险坑点数据
- 自定义 metadata 提取器，处理分类、编号、标题等结构化信息
- 文档分割和预处理

**关键类**:
- `PitDataLoader`: 负责JSON数据加载和Document创建
- `PitVectorStore`: 向量数据库管理
- `PitRetriever`: 坑点检索接口

### 2. 向量化存储

**技术选型**:
- **嵌入模型**: 阿里云通义千问 DashScope embeddings 或 sentence-transformers (本地)
- **向量数据库**: FAISS (轻量级) 或 ChromaDB (功能丰富)
- **持久化**: 本地文件系统 `data/vector_store/`

**数据结构**:
```python
Document(
    page_content="标题: 费率与保障责任的不对等比较\n示例: 用自家保障差但便宜的产品...",
    metadata={
        "category": "产品比较与费率相关坑点",
        "编号": 1,
        "标题": "费率与保障责任的不对等比较",
        "坑点原因": "进行"田忌赛马"式的误导..."
    }
)
```

### 3. 检索增强生成

**集成点**: `agency_assistant.py` 中的 `_generate_suggestions` 方法

**工作流程**:
1. 分析经纪人话语和对话历史
2. 提取关键词和意图信息
3. 向量检索相关坑点 (Top-K, 相似度阈值)
4. 将坑点信息注入建议生成 prompt
5. 生成包含风险提示的建议列表

## 文件结构

```
├── agent/
│   ├── agency_assistant.py        # [修改] 集成RAG检索
│   └── rag_pit_detector.py        # [新增] RAG核心模块
├── data/
│   ├── insurance_pits_merged.json # [已存在] 原始数据
│   └── vector_store/              # [新增] 向量索引存储
│       ├── faiss_index/
│       └── metadata.json
├── tools/
│   └── preprocess_pits_data.py    # [新增] 数据预处理脚本
├── util/
│   └── config.py                  # [修改] 新增RAG配置
├── test_agency_assistant.py       # [修改] 新增RAG测试
├── pyproject.toml                 # [修改] 新增依赖
└── RAG_README.md                  # [本文件]
```

## 配置参数

### 环境变量
```bash
# 嵌入模型配置
EMBEDDING_MODEL=dashscope  # 或 sentence-transformers
AI_INSUR_QWEN_API_KEY=your_qwen_api_key_here

# 向量数据库配置
VECTOR_STORE_TYPE=faiss  # 或 chroma
VECTOR_STORE_PATH=data/vector_store

# 检索参数
RETRIEVAL_TOP_K=5
SIMILARITY_THRESHOLD=0.7
```

### 代码配置
```python
RAG_CONFIG = {
    "chunk_size": 500,
    "chunk_overlap": 50,
    "embedding_model": "text-embedding-v4",  # 阿里云通义千问embedding
    "vector_store_type": "faiss",
    "retrieval_top_k": 5,
    "similarity_threshold": 0.7
}
```

## 依赖项

### 新增依赖 (pyproject.toml)
```toml
dependencies = [
    # ... 现有依赖 ...
    "langchain-community>=0.3.0",  # JSONLoader
    "faiss-cpu>=1.7.4",            # 向量数据库
    "sentence-transformers>=2.2.0", # 本地嵌入(可选)
    "dashscope>=1.14.0",            # 阿里云通义千问
]
```

## 使用示例

### 数据预处理 (一次性)
```bash
python tools/preprocess_pits_data.py
```

### 在线检索 (集成到现有系统)
```python
# 在 _generate_suggestions 中
relevant_pits = self.pit_retriever.search(
    query=broker_input + " " + str(intent_analysis),
    top_k=5
)

# 增强建议生成prompt
enhanced_prompt = f"""
{original_prompt}

相关风险提示:
{format_pit_warnings(relevant_pits)}
"""
```

## 性能指标

### 预期性能
- **检索延迟**: < 100ms (FAISS本地检索)
- **准确率**: 基于语义相似度的Top-5检索
- **存储空间**: ~50MB (660条坑点 + 向量索引)

### 评估方法
- **离线评估**: 人工标注测试集，计算 Hit@K, MRR
- **在线评估**: A/B测试，对比建议质量和用户满意度

## 部署说明

### 开发环境
1. 安装依赖: `uv sync`
2. 预处理数据: `python tools/preprocess_pits_data.py`
3. 运行测试: `python -m pytest test_agency_assistant.py -k rag`

### 生产环境
- 向量索引文件需要随代码一起部署
- 建议使用 Redis 缓存热门检索结果
- 监控检索延迟和准确率指标

## 扩展计划

### 短期优化
- [ ] 支持多种嵌入模型切换
- [ ] 增加检索结果重排序
- [ ] 实现增量更新机制

### 长期规划
- [ ] 支持多模态检索 (图片、表格)
- [ ] 集成用户反馈学习
- [ ] 部署到云端向量数据库

## 故障排除

### 常见问题
1. **向量索引加载失败**: 检查文件路径和权限
2. **检索结果不相关**: 调整相似度阈值和Top-K参数
3. **内存占用过高**: 考虑使用量化向量或分片存储

### 调试工具
```bash
# 测试数据加载
python -c "from agent.rag_pit_detector import PitDataLoader; loader = PitDataLoader(); print(len(loader.load_documents()))"

# 测试向量检索
python -c "from agent.rag_pit_detector import PitRetriever; retriever = PitRetriever(); print(retriever.search('保费上涨', 3))"
```

---

**维护者**: 项目开发团队  
**最后更新**: 2024年1月  
**版本**: v1.0 