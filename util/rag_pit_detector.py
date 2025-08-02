"""
RAG 保险坑点检测器

使用 LangChain 的 JSONLoader 加载保险坑点数据，
通过向量检索为对话助理提供相关的风险提示。
"""

import json
import os
from typing import List, Dict, Any, Optional
from pathlib import Path

from langchain_community.document_loaders import JSONLoader
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

from . import logger, config


class PitDataLoader:
    """保险坑点数据加载器"""
    
    def __init__(self, json_file_path: str = "data/insurance_pits_merged.json"):
        self.json_file_path = json_file_path
        
    def _extract_metadata(self, record: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """从JSON记录中提取元数据"""
        # 获取分类信息
        category = self._clean_text(metadata.get("category", "未分类"))
        
        # 提取坑点基本信息
        extracted_metadata = {
            "category": category,
            "编号": record.get("编号", 0),
            "标题": self._clean_text(record.get("标题", "")),
            "坑点原因": self._clean_text(record.get("坑点原因", "")),
            "source": "insurance_pits_merged.json"
        }
        
        return extracted_metadata
    
    def _clean_text(self, text: str) -> str:
        """清理文本中的特殊字符，避免编码问题"""
        if not text:
            return ""
        
        # 替换常见的智能引号和特殊字符
        replacements = {
            '\u2018': "'",  # 左单引号
            '\u2019': "'",  # 右单引号
            '\u201c': '"',  # 左双引号
            '\u201d': '"',  # 右双引号
            '\u2013': '-',  # en dash
            '\u2014': '-',  # em dash
            '\u2026': '...',  # 省略号
            '\u00a0': ' ',  # 不间断空格
        }
        
        cleaned_text = text
        for old_char, new_char in replacements.items():
            cleaned_text = cleaned_text.replace(old_char, new_char)
        
        return cleaned_text
    
    def _format_content(self, record: Dict[str, Any], category: str) -> str:
        """格式化文档内容"""
        title = self._clean_text(record.get("标题", ""))
        example = self._clean_text(record.get("示例描述", ""))
        reason = self._clean_text(record.get("坑点原因", ""))
        category = self._clean_text(category)
        
        content_parts = [
            f"分类: {category}",
            f"标题: {title}",
            f"示例: {example}",
            f"原因: {reason}"
        ]
        
        return "\n".join(filter(None, content_parts))
    
    def load_documents(self) -> List[Document]:
        """加载并转换JSON数据为Document对象"""
        logger.info(f"开始加载保险坑点数据: {self.json_file_path}")
        
        if not os.path.exists(self.json_file_path):
            raise FileNotFoundError(f"数据文件不存在: {self.json_file_path}")
        
        documents = []
        
        try:
            with open(self.json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            categories = data.get("categories", [])
            
            for category_data in categories:
                category_name = category_data.get("category", "未分类")
                items = category_data.get("items", [])
                
                for item in items:
                    # 格式化内容
                    content = self._format_content(item, category_name)
                    
                    # 提取元数据
                    metadata = self._extract_metadata(
                        item, 
                        {"category": category_name}
                    )
                    
                    # 创建Document对象
                    doc = Document(
                        page_content=content,
                        metadata=metadata
                    )
                    documents.append(doc)
            
            logger.info(f"成功加载 {len(documents)} 条保险坑点数据")
            return documents
            
        except Exception as e:
            logger.error(f"加载保险坑点数据失败: {e}")
            raise


class PitVectorStore:
    """保险坑点向量数据库管理器"""
    
    def __init__(
        self, 
        vector_store_path: str = "data/vector_store",
        embedding_model: str = "text-embedding-v4"
    ):
        self.vector_store_path = Path(vector_store_path)
        self.embedding_model = embedding_model
        self.embeddings = None
        self.vector_store = None
        
        # 确保向量存储目录存在
        self.vector_store_path.mkdir(parents=True, exist_ok=True)
        
    def _initialize_embeddings(self):
        """初始化嵌入模型"""
        if self.embeddings is None:
            try:
                self.embeddings = DashScopeEmbeddings(
                    model=self.embedding_model,
                    dashscope_api_key=config.QWEN_API_KEY
                )
                logger.info(f"初始化阿里云嵌入模型: {self.embedding_model}")
            except Exception as e:
                logger.error(f"初始化阿里云嵌入模型失败: {e}")
                # 回退到sentence-transformers
                try:
                    from langchain_community.embeddings import SentenceTransformerEmbeddings
                    self.embeddings = SentenceTransformerEmbeddings(
                        model_name="paraphrase-multilingual-MiniLM-L12-v2"
                    )
                    logger.info("回退到本地sentence-transformers模型")
                except Exception as fallback_e:
                    logger.error(f"本地嵌入模型初始化也失败: {fallback_e}")
                    raise
    
    def create_vector_store(self, documents: List[Document]) -> FAISS:
        """创建向量数据库"""
        logger.info("开始创建向量数据库")
        
        self._initialize_embeddings()
        
        # 使用文本分割器处理长文档
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            length_function=len,
            separators=["\n\n", "\n", "。", "，", " ", ""]
        )
        
        # 分割文档
        split_docs = text_splitter.split_documents(documents)
        logger.info(f"文档分割完成，共 {len(split_docs)} 个文档块")
        
        # 创建FAISS向量存储 - 分批处理以避免API限制
        try:
            # 阿里云DashScope API限制每批最多10个文档
            batch_size = 8  # 设置为8以确保安全
            
            if len(split_docs) <= batch_size:
                # 如果文档数量少，直接创建
                self.vector_store = FAISS.from_documents(
                    documents=split_docs,
                    embedding=self.embeddings
                )
            else:
                # 分批处理大量文档
                logger.info(f"分批处理文档，每批 {batch_size} 个")
                
                # 创建第一批
                first_batch = split_docs[:batch_size]
                self.vector_store = FAISS.from_documents(
                    documents=first_batch,
                    embedding=self.embeddings
                )
                logger.info(f"处理第1批: {len(first_batch)} 个文档")
                
                # 处理剩余批次
                for i in range(batch_size, len(split_docs), batch_size):
                    batch = split_docs[i:i + batch_size]
                    batch_num = (i // batch_size) + 1
                    
                    logger.info(f"处理第{batch_num}批: {len(batch)} 个文档")
                    
                    # 创建临时向量存储
                    temp_store = FAISS.from_documents(
                        documents=batch,
                        embedding=self.embeddings
                    )
                    
                    # 合并到主存储
                    self.vector_store.merge_from(temp_store)
            
            logger.info("FAISS向量数据库创建成功")
            return self.vector_store
            
        except Exception as e:
            logger.error(f"创建向量数据库失败: {e}")
            raise

    
    def save_vector_store(self):
        """保存向量数据库到本地"""
        if self.vector_store is None:
            raise ValueError("向量数据库未初始化")
        
        try:
            faiss_path = str(self.vector_store_path / "faiss_index")
            self.vector_store.save_local(faiss_path)
            logger.info(f"向量数据库已保存到: {faiss_path}")
        except Exception as e:
            logger.error(f"保存向量数据库失败: {e}")
            raise
    
    def load_vector_store(self) -> Optional[FAISS]:
        """从本地加载向量数据库"""
        self._initialize_embeddings()
        
        faiss_path = str(self.vector_store_path / "faiss_index")
        
        if not os.path.exists(faiss_path):
            logger.warning(f"向量数据库文件不存在: {faiss_path}")
            return None
        
        try:
            self.vector_store = FAISS.load_local(
                faiss_path, 
                self.embeddings,
                allow_dangerous_deserialization=True
            )
            logger.info(f"成功加载向量数据库: {faiss_path}")
            return self.vector_store
        except Exception as e:
            logger.error(f"加载向量数据库失败: {e}")
            return None


class PitRetriever:
    """保险坑点检索器"""
    
    def __init__(
        self,
        vector_store_path: str = "data/vector_store",
        top_k: int = 8,
        similarity_threshold: float = 0.3
    ):
        self.vector_store_manager = PitVectorStore(vector_store_path)
        self.top_k = top_k
        self.similarity_threshold = similarity_threshold
        self.vector_store = None
        
        # 尝试加载现有的向量数据库
        self._load_or_create_vector_store()
    
    def _load_or_create_vector_store(self):
        """加载或创建向量数据库"""
        # 首先尝试加载现有的向量数据库
        self.vector_store = self.vector_store_manager.load_vector_store()
        
        if self.vector_store is None:
            logger.info("未找到现有向量数据库，将创建新的数据库")
            self._create_new_vector_store()
    
    def _create_new_vector_store(self):
        """创建新的向量数据库"""
        try:
            # 加载数据
            data_loader = PitDataLoader()
            documents = data_loader.load_documents()
            
            # 创建向量数据库
            self.vector_store = self.vector_store_manager.create_vector_store(documents)
            
            # 保存到本地
            self.vector_store_manager.save_vector_store()
            
        except Exception as e:
            logger.error(f"创建向量数据库失败: {e}")
            raise
    
    def search(self, query: str, top_k: Optional[int] = None, similarity_threshold: Optional[float] = None) -> List[Dict[str, Any]]:
        """检索相关的保险坑点"""
        if self.vector_store is None:
            logger.error("向量数据库未初始化")
            return []
        
        k = top_k or self.top_k
        threshold = similarity_threshold or self.similarity_threshold
        
        try:
            # 先尝试更大范围的搜索，确保不遗漏相关内容
            search_k = max(k * 2, 15)  # 搜索更多候选结果
            
            # 执行相似度搜索
            docs_with_scores = self.vector_store.similarity_search_with_score(
                query, k=search_k
            )
            
            results = []
            all_candidates = []  # 记录所有候选结果用于调试
            
            for doc, score in docs_with_scores:
                # 转换分数为相似度 (FAISS返回的是距离，需要转换)
                similarity = 1 / (1 + score)
                
                candidate = {
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "similarity": similarity,
                    "score": score,  # 保留原始分数用于调试
                    "category": doc.metadata.get("category", "未分类"),
                    "title": doc.metadata.get("title", ""),
                    "reason": doc.metadata.get("reason", "")
                }
                all_candidates.append(candidate)
                
                # 应用阈值过滤
                if similarity >= threshold:
                    results.append(candidate)
            
            # 如果过滤后结果太少，放宽条件
            if len(results) < 2 and len(all_candidates) > 0:
                # 降低阈值，取前k个结果
                relaxed_threshold = threshold * 0.7  # 降低30%
                logger.info(f"结果过少，降低阈值到 {relaxed_threshold:.3f}")
                
                results = []
                for candidate in all_candidates[:k]:
                    if candidate["similarity"] >= relaxed_threshold:
                        results.append(candidate)
                
                # 如果还是太少，至少返回前2个最相似的
                if len(results) < 2:
                    results = all_candidates[:min(2, len(all_candidates))]
                    logger.info("进一步放宽条件，返回最相似的前2个结果")
            
            # 按相似度排序并限制数量
            results = sorted(results, key=lambda x: x["similarity"], reverse=True)[:k]
            
            # 记录详细的检索信息
            if results:
                min_sim = min(r["similarity"] for r in results)
                max_sim = max(r["similarity"] for r in results)
                logger.info(f"检索到 {len(results)} 个相关坑点 (查询: {query[:50]}..., 相似度范围: {min_sim:.3f}-{max_sim:.3f})")
                #results_example = "\n".join([r['content'] for r in results])
                #logger.info(f"检索到的坑点: {results_example}")
            else:
                logger.warning(f"未检索到满足条件的坑点 (查询: {query[:50]}..., 阈值: {threshold})")
                if all_candidates:
                    best_sim = max(c["similarity"] for c in all_candidates)
                    logger.info(f"最佳候选相似度: {best_sim:.3f}")
            
            return results
            
        except Exception as e:
            logger.error(f"检索失败: {e}")
            return []
    
    def search_by_category(self, query: str, category: str, top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        """在指定分类中检索坑点"""
        all_results = self.search(query, top_k * 2 if top_k else self.top_k * 2)
        
        # 过滤指定分类
        filtered_results = [
            result for result in all_results 
            if result["category"] == category
        ]
        
        # 返回前top_k个结果
        k = top_k or self.top_k
        return filtered_results[:k]
    
    def format_pit_warnings(self, search_results: List[Dict[str, Any]]) -> str:
        """格式化坑点警告信息"""
        if not search_results:
            return ""
        
        warnings = []
        for i, result in enumerate(search_results, 1):
            title = result.get("title", "未知坑点")
            reason = result.get("reason", "")
            category = result.get("category", "")
            
            warning = f"{i}. 【{category}】{title}"
            if reason:
                warning += f"\n   风险提示: {reason}"
            
            warnings.append(warning)
        
        return "\n\n".join(warnings)


# 全局单例实例
_pit_retriever_instance = None


def get_pit_retriever() -> PitRetriever:
    """获取坑点检索器单例"""
    global _pit_retriever_instance
    
    if _pit_retriever_instance is None:
        _pit_retriever_instance = PitRetriever()
    
    return _pit_retriever_instance 