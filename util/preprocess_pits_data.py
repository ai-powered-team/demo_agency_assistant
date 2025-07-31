#!/usr/bin/env python3
"""
保险坑点数据预处理脚本

一次性加载JSON数据，创建向量数据库并保存到本地。
运行此脚本后，RAG系统可以直接加载预构建的向量索引。
"""

import sys
import os
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from util.rag_pit_detector import PitDataLoader, PitVectorStore
from util import logger


def main():
    """主函数：执行数据预处理"""
    print("=" * 60)
    print("保险坑点数据预处理工具")
    print("=" * 60)
    
    start_time = time.time()
    
    try:
        # 1. 检查数据文件是否存在
        data_file = "data/insurance_pits_merged.json"
        if not os.path.exists(data_file):
            print(f"❌ 错误: 数据文件不存在 - {data_file}")
            print("请确保数据文件位于正确的位置")
            return 1
        
        print(f"✅ 找到数据文件: {data_file}")
        
        # 2. 加载数据
        print("\n📖 步骤 1: 加载保险坑点数据...")
        data_loader = PitDataLoader(data_file)
        documents = data_loader.load_documents()
        
        print(f"✅ 成功加载 {len(documents)} 条保险坑点数据")
        
        # 显示数据统计
        categories = set(doc.metadata.get("category", "未分类") for doc in documents)
        print(f"📊 数据统计:")
        print(f"   - 总坑点数: {len(documents)}")
        print(f"   - 分类数量: {len(categories)}")
        print(f"   - 分类列表: {', '.join(sorted(categories))}")
        
        # 3. 创建向量数据库
        print("\n🔧 步骤 2: 创建向量数据库...")
        vector_store_manager = PitVectorStore()
        
        # 检查是否已存在向量数据库
        existing_store = vector_store_manager.load_vector_store()
        if existing_store is not None:
            print("⚠️  发现已存在的向量数据库")
            response = input("是否要重新创建? (y/N): ").strip().lower()
            if response != 'y':
                print("取消操作")
                return 0
        
        # 创建新的向量数据库
        vector_store = vector_store_manager.create_vector_store(documents)
        
        # 4. 保存向量数据库
        print("\n💾 步骤 3: 保存向量数据库...")
        vector_store_manager.save_vector_store()
        
        # 5. 验证保存结果
        print("\n✅ 步骤 4: 验证保存结果...")
        loaded_store = vector_store_manager.load_vector_store()
        if loaded_store is not None:
            print("✅ 向量数据库验证成功")
            
            # 执行测试检索
            test_query = "保费上涨"
            test_results = loaded_store.similarity_search(test_query, k=3)
            print(f"🔍 测试检索 '{test_query}' 返回 {len(test_results)} 个结果")
            
            if test_results:
                print("📝 示例检索结果:")
                for i, doc in enumerate(test_results[:2], 1):
                    title = doc.metadata.get("标题", "未知")
                    category = doc.metadata.get("category", "未分类")
                    print(f"   {i}. 【{category}】{title}")
        else:
            print("❌ 向量数据库验证失败")
            return 1
        
        # 6. 完成
        elapsed_time = time.time() - start_time
        print(f"\n🎉 数据预处理完成!")
        print(f"⏱️  总用时: {elapsed_time:.2f} 秒")
        print(f"📁 向量数据库位置: {vector_store_manager.vector_store_path}")
        
        print("\n📋 后续步骤:")
        print("1. 向量数据库已准备就绪")
        print("2. 可以启动智能对话助理系统")
        print("3. RAG功能将自动加载预构建的向量索引")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ 预处理失败: {e}")
        logger.error(f"数据预处理失败: {e}")
        return 1


def show_help():
    """显示帮助信息"""
    help_text = """
保险坑点数据预处理工具

用法:
    python util/preprocess_pits_data.py [选项]

选项:
    -h, --help     显示此帮助信息
    
功能:
    1. 加载 data/insurance_pits_merged.json 中的保险坑点数据
    2. 使用阿里云通义千问 embeddings 创建向量表示
    3. 构建 FAISS 向量数据库
    4. 保存到 data/vector_store/ 目录
    5. 验证保存结果

环境要求:
    - 设置 AI_INSUR_QWEN_API_KEY 环境变量
    - 或者系统将自动回退到本地 sentence-transformers 模型

示例:
    python util/preprocess_pits_data.py
    """
    print(help_text)


if __name__ == "__main__":
    # 检查命令行参数
    if len(sys.argv) > 1 and sys.argv[1] in ["-h", "--help"]:
        show_help()
        sys.exit(0)
    
    # 执行预处理
    exit_code = main()
    sys.exit(exit_code) 