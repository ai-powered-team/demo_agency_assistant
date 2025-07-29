"""
记忆管理器

基于 mem0ai 框架实现用户记忆管理和特征提取功能。
"""

from typing import List, Dict, Any, Optional
from mem0 import AsyncMemory

from util import config, logger, ChatMessage


class MemoryManager:
    """mem0 记忆管理器"""

    def __init__(self):
        """初始化记忆管理器"""
        self.memory: Optional[AsyncMemory] = None

    async def _initialize_memory(self):
        """初始化 mem0 实例"""
        if self.memory is not None:
            return

        try:
            # 配置 mem0
            mem0_config = {
                "llm": {
                    "provider": config.OPENAI_LLM_PROVIDER,
                    "config": {
                        "model": config.OPENAI_MODEL,
                        "api_key": config.OPENAI_API_KEY,
                        f"{config.OPENAI_LLM_PROVIDER}_base_url": config.OPENAI_BASE_URL,
                    },
                },
                "embedder": {
                    "provider": config.OPENAI_EMBEDDING_PROVIDER,
                    "config": {
                        "model": config.OPENAI_EMBEDDING_MODEL,
                        "api_key": config.OPENAI_API_KEY,
                        f"{config.OPENAI_EMBEDDING_PROVIDER}_base_url": config.OPENAI_BASE_URL,
                    },
                }
            }

            self.memory = await AsyncMemory.from_config(mem0_config)
            logger.info("mem0 记忆管理器初始化成功")

        except Exception as e:
            logger.error(f"mem0 记忆管理器初始化失败: {e}")
            raise

    async def add_conversation_memory(
        self,
        user_id: int,
        conversation: List[ChatMessage],
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """添加对话记忆"""
        try:
            # 确保 memory 已初始化
            await self._initialize_memory()

            if self.memory is None:
                raise RuntimeError("Memory 初始化失败")

            # 将对话转换为文本
            conversation_text = self._format_conversation(conversation)

            # 添加到 mem0
            await self.memory.add(
                messages=conversation_text,
                user_id=str(user_id),
                metadata=metadata or {}
            )

            logger.info(f"用户 {user_id} 对话记忆添加成功")
            return True

        except Exception as e:
            logger.error(f"添加对话记忆失败: {e}")
            return False

    async def get_user_context(
        self,
        user_id: int,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """获取用户相关上下文"""
        try:
            # 确保 memory 已初始化
            await self._initialize_memory()

            if self.memory is None:
                raise RuntimeError("Memory 初始化失败")

            memories = await self.memory.search(
                query=query,
                user_id=str(user_id),
                limit=limit
            )

            # mem0 的 search 返回的是字典，需要处理
            if isinstance(memories, dict):
                memories_list = memories.get('results', [])
            else:
                memories_list = memories if isinstance(memories, list) else []

            return [
                {
                    'content': memory.get('memory', ''),
                    'score': memory.get('score', 0.0),
                    'metadata': memory.get('metadata', {})
                }
                for memory in memories_list
            ]

        except Exception as e:
            logger.error(f"获取用户上下文失败: {e}")
            return []

    def _format_conversation(self, conversation: List[ChatMessage]) -> str:
        """格式化对话为文本"""
        formatted_lines = []
        for message in conversation:
            role = message['role']
            content = message['content']
            formatted_lines.append(f"{role}: {content}")

        return "\n".join(formatted_lines)

    async def update_user_memory(
        self,
        user_id: int,
        new_information: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """更新用户记忆"""
        try:
            # 确保 memory 已初始化
            await self._initialize_memory()

            if self.memory is None:
                raise RuntimeError("Memory 初始化失败")

            await self.memory.add(
                messages=new_information,
                user_id=str(user_id),
                metadata=metadata or {}
            )

            logger.info(f"用户 {user_id} 记忆更新成功")
            return True

        except Exception as e:
            logger.error(f"更新用户记忆失败: {e}")
            return False

    async def get_memory_stats(self, user_id: int) -> Dict[str, Any]:
        """获取用户记忆统计信息"""
        try:
            # 确保 memory 已初始化
            await self._initialize_memory()

            if self.memory is None:
                raise RuntimeError("Memory 初始化失败")

            memories = await self.memory.get_all(user_id=str(user_id))

            # mem0 的 get_all 返回的是字典，需要处理
            if isinstance(memories, dict):
                memories_list = memories.get('results', [])
            else:
                memories_list = memories if isinstance(memories, list) else []

            return {
                'total_memories': len(memories_list),
                'user_id': user_id,
                'last_updated': memories_list[-1].get('created_at') if memories_list else None
            }

        except Exception as e:
            logger.error(f"获取记忆统计失败: {e}")
            return {
                'total_memories': 0,
                'user_id': user_id,
                'last_updated': None
            }


# 全局记忆管理器实例
memory_manager = MemoryManager()
