"""记忆系统 - 上下文管理和记忆存储"""

import json
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

from ..utils.llm_client import LLMClient
from ..utils.config_loader import config
from ..utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class MemoryItem:
    """记忆项"""
    id: str
    content: str
    context: Dict[str, Any]
    timestamp: float
    importance: float
    access_count: int = 0
    last_accessed: float = 0.0


class CodeMemorySystem:
    """代码记忆系统"""
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient()
        self.memory_config = config.get_memory_config()
        
        # 记忆存储
        self.short_term_memory: List[MemoryItem] = []
        self.long_term_memory: List[MemoryItem] = []
        
        # 配置参数
        self.max_short_term = self.memory_config.get('max_short_term_items', 100)
        self.max_long_term = self.memory_config.get('max_long_term_items', 1000)
        self.compression_threshold = self.memory_config.get('compression_threshold', 0.8)
        self.memory_file = self.memory_config.get('memory_file', 'data/memory.json')
        
        # 加载持久化记忆
        if self.memory_config.get('memory_persistence', True):
            self._load_persistent_memory()
        
        logger.info("代码记忆系统初始化完成")
    
    def retrieve_relevant_context(
        self, 
        request: str, 
        user_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """检索相关上下文"""
        logger.info(f"检索相关上下文: {request[:50]}...")
        
        try:
            # 1. 从短期记忆中检索
            short_term_matches = self._search_memory(request, self.short_term_memory)
            
            # 2. 从长期记忆中检索
            long_term_matches = self._search_memory(request, self.long_term_memory)
            
            # 3. 合并和排序结果
            all_matches = short_term_matches + long_term_matches
            all_matches.sort(key=lambda x: x['relevance'], reverse=True)
            
            # 4. 选择最相关的记忆
            top_matches = all_matches[:5]  # 取前5个最相关的
            
            # 5. 更新访问统计
            for match in top_matches:
                self._update_access_stats(match['memory_item'])
            
            relevant_context = {
                'relevant_memories': [
                    {
                        'content': match['memory_item'].content,
                        'context': match['memory_item'].context,
                        'relevance': match['relevance'],
                        'timestamp': match['memory_item'].timestamp
                    }
                    for match in top_matches
                ],
                'total_matches': len(all_matches),
                'search_query': request
            }
            
            logger.info(f"找到 {len(top_matches)} 个相关记忆")
            return relevant_context
            
        except Exception as e:
            logger.error(f"上下文检索失败: {e}")
            return {'relevant_memories': [], 'total_matches': 0, 'search_query': request}
    
    def update_memory(
        self, 
        request: str, 
        execution_result: Dict[str, Any], 
        reasoning_result: Any,
        user_context: Optional[Dict[str, Any]] = None
    ):
        """更新记忆"""
        logger.info("更新记忆系统")
        
        try:
            # 创建新的记忆项
            memory_content = self._create_memory_content(request, execution_result, reasoning_result)
            importance = self._calculate_importance(request, execution_result, reasoning_result)
            
            memory_item = MemoryItem(
                id=f"mem_{int(time.time() * 1000)}",
                content=memory_content,
                context={
                    'request': request,
                    'user_context': user_context or {},
                    'execution_result': execution_result,
                    'reasoning_strategy': reasoning_result.strategy if reasoning_result else 'unknown',
                    'confidence': reasoning_result.confidence if reasoning_result else 0.0
                },
                timestamp=time.time(),
                importance=importance
            )
            
            # 添加到短期记忆
            self.short_term_memory.append(memory_item)
            
            # 管理记忆容量
            self._manage_memory_capacity()
            
            # 保存持久化记忆
            if self.memory_config.get('memory_persistence', True):
                self._save_persistent_memory()
            
            logger.info(f"记忆已更新 - 重要性: {importance:.2f}")
            
        except Exception as e:
            logger.error(f"记忆更新失败: {e}")
    
    def _search_memory(self, query: str, memory_list: List[MemoryItem]) -> List[Dict[str, Any]]:
        """在记忆中搜索相关内容"""
        if not memory_list:
            return []
        
        try:
            # 使用LLM进行语义搜索
            search_prompt = f"""
            在以下记忆中找到与查询最相关的内容：
            
            查询: {query}
            
            记忆内容:
            {self._format_memories_for_search(memory_list[:20])}  # 限制搜索范围
            
            请为每个记忆项评分（0-1），表示与查询的相关性。
            格式: 记忆ID: 相关性分数
            """
            
            response = self.llm.completion(search_prompt)
            relevance_scores = self._parse_relevance_scores(
                self.llm.get_response_text(response), memory_list
            )
            
            # 过滤和排序结果
            matches = []
            for memory_item in memory_list:
                relevance = relevance_scores.get(memory_item.id, 0.0)
                if relevance > 0.3:  # 相关性阈值
                    matches.append({
                        'memory_item': memory_item,
                        'relevance': relevance
                    })
            
            return matches
            
        except Exception as e:
            logger.warning(f"语义搜索失败，使用关键词搜索: {e}")
            return self._keyword_search(query, memory_list)
    
    def _keyword_search(self, query: str, memory_list: List[MemoryItem]) -> List[Dict[str, Any]]:
        """关键词搜索（后备方案）"""
        query_words = set(query.lower().split())
        matches = []
        
        for memory_item in memory_list:
            content_words = set(memory_item.content.lower().split())
            common_words = query_words.intersection(content_words)
            
            if common_words:
                relevance = len(common_words) / len(query_words)
                matches.append({
                    'memory_item': memory_item,
                    'relevance': relevance
                })
        
        return matches
    
    def _format_memories_for_search(self, memories: List[MemoryItem]) -> str:
        """格式化记忆用于搜索"""
        formatted = []
        for memory in memories:
            formatted.append(f"ID: {memory.id}\n内容: {memory.content[:200]}...")
        return "\n\n".join(formatted)
    
    def _parse_relevance_scores(self, response_text: str, memory_list: List[MemoryItem]) -> Dict[str, float]:
        """解析相关性分数"""
        import re
        
        scores = {}
        memory_ids = {mem.id for mem in memory_list}
        
        # 查找分数模式
        patterns = [
            r'(\w+):\s*([0-9.]+)',
            r'ID:\s*(\w+).*?([0-9.]+)',
            r'记忆(\w+).*?([0-9.]+)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, response_text)
            for match in matches:
                memory_id, score_str = match
                if memory_id in memory_ids:
                    try:
                        scores[memory_id] = float(score_str)
                    except ValueError:
                        continue
        
        return scores
    
    def _create_memory_content(
        self, 
        request: str, 
        execution_result: Dict[str, Any], 
        reasoning_result: Any
    ) -> str:
        """创建记忆内容"""
        content_parts = [
            f"请求: {request}",
            f"解决方案: {execution_result.get('explanation', '')}",
        ]
        
        if execution_result.get('code'):
            content_parts.append(f"代码: {execution_result['code'][:500]}...")
        
        if reasoning_result:
            content_parts.append(f"推理策略: {reasoning_result.strategy}")
            content_parts.append(f"置信度: {reasoning_result.confidence}")
        
        return "\n".join(content_parts)
    
    def _calculate_importance(
        self, 
        request: str, 
        execution_result: Dict[str, Any], 
        reasoning_result: Any
    ) -> float:
        """计算记忆重要性"""
        importance = 0.5  # 基础重要性
        
        # 基于置信度调整
        if reasoning_result and reasoning_result.confidence:
            importance += reasoning_result.confidence * 0.3
        
        # 基于代码长度调整
        if execution_result.get('code'):
            code_length = len(execution_result['code'])
            if code_length > 1000:
                importance += 0.2
            elif code_length > 500:
                importance += 0.1
        
        # 基于工具使用调整
        tools_used = execution_result.get('tools_used', [])
        if len(tools_used) > 2:
            importance += 0.1
        
        # 基于请求复杂度调整
        complex_keywords = ['系统', '架构', '完整', '项目', '应用', '平台']
        if any(keyword in request for keyword in complex_keywords):
            importance += 0.2
        
        return min(importance, 1.0)
    
    def _update_access_stats(self, memory_item: MemoryItem):
        """更新访问统计"""
        memory_item.access_count += 1
        memory_item.last_accessed = time.time()
    
    def _manage_memory_capacity(self):
        """管理记忆容量"""
        # 管理短期记忆
        if len(self.short_term_memory) > self.max_short_term:
            # 将重要的记忆转移到长期记忆
            self.short_term_memory.sort(key=lambda x: x.importance, reverse=True)
            
            # 转移前20%到长期记忆
            transfer_count = min(20, len(self.short_term_memory) // 5)
            for _ in range(transfer_count):
                memory_item = self.short_term_memory.pop(0)
                self.long_term_memory.append(memory_item)
            
            # 删除最不重要的记忆
            excess_count = len(self.short_term_memory) - self.max_short_term
            if excess_count > 0:
                self.short_term_memory = self.short_term_memory[:-excess_count]
        
        # 管理长期记忆
        if len(self.long_term_memory) > self.max_long_term:
            # 按重要性和访问频率排序
            self.long_term_memory.sort(
                key=lambda x: (x.importance, x.access_count, x.last_accessed), 
                reverse=True
            )
            
            # 保留最重要的记忆
            self.long_term_memory = self.long_term_memory[:self.max_long_term]
    
    def _load_persistent_memory(self):
        """加载持久化记忆"""
        try:
            memory_path = Path(self.memory_file)
            if memory_path.exists():
                with open(memory_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 恢复长期记忆
                for item_data in data.get('long_term_memory', []):
                    memory_item = MemoryItem(**item_data)
                    self.long_term_memory.append(memory_item)
                
                logger.info(f"加载了 {len(self.long_term_memory)} 个持久化记忆")
        
        except Exception as e:
            logger.warning(f"加载持久化记忆失败: {e}")
    
    def _save_persistent_memory(self):
        """保存持久化记忆"""
        try:
            memory_path = Path(self.memory_file)
            memory_path.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                'long_term_memory': [asdict(item) for item in self.long_term_memory],
                'save_timestamp': time.time()
            }
            
            with open(memory_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        
        except Exception as e:
            logger.warning(f"保存持久化记忆失败: {e}")
    
    def clear_short_term_memory(self):
        """清空短期记忆"""
        self.short_term_memory.clear()
        logger.info("短期记忆已清空")
    
    def export_memory(self) -> Dict[str, Any]:
        """导出记忆数据"""
        return {
            'short_term_memory': [asdict(item) for item in self.short_term_memory],
            'long_term_memory': [asdict(item) for item in self.long_term_memory],
            'export_timestamp': time.time()
        }
    
    def import_memory(self, memory_data: Dict[str, Any]):
        """导入记忆数据"""
        try:
            # 导入短期记忆
            self.short_term_memory = [
                MemoryItem(**item_data) 
                for item_data in memory_data.get('short_term_memory', [])
            ]
            
            # 导入长期记忆
            self.long_term_memory = [
                MemoryItem(**item_data) 
                for item_data in memory_data.get('long_term_memory', [])
            ]
            
            logger.info("记忆数据导入完成")
        
        except Exception as e:
            logger.error(f"记忆数据导入失败: {e}")
    
    def get_memory_summary(self) -> Dict[str, Any]:
        """获取记忆系统摘要"""
        total_memories = len(self.short_term_memory) + len(self.long_term_memory)
        
        if total_memories == 0:
            return {
                'total_memories': 0,
                'short_term_count': 0,
                'long_term_count': 0,
                'average_importance': 0.0,
                'most_accessed_memories': [],
                'memory_usage': '0%'
            }
        
        # 计算平均重要性
        all_memories = self.short_term_memory + self.long_term_memory
        total_importance = sum(mem.importance for mem in all_memories)
        average_importance = total_importance / total_memories
        
        # 最常访问的记忆
        most_accessed = sorted(all_memories, key=lambda x: x.access_count, reverse=True)[:5]
        
        # 记忆使用率
        max_capacity = self.max_short_term + self.max_long_term
        usage_percentage = (total_memories / max_capacity) * 100
        
        return {
            'total_memories': total_memories,
            'short_term_count': len(self.short_term_memory),
            'long_term_count': len(self.long_term_memory),
            'average_importance': average_importance,
            'most_accessed_memories': [
                {
                    'id': mem.id,
                    'access_count': mem.access_count,
                    'importance': mem.importance,
                    'content_preview': mem.content[:100] + '...'
                }
                for mem in most_accessed
            ],
            'memory_usage': f'{usage_percentage:.1f}%'
        }