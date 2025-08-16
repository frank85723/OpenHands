"""推理引擎 - 实现Chain-of-Thought, Tree of Thoughts, 反思和验证机制"""

import json
import random
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from ..utils.llm_client import LLMClient
from ..utils.config_loader import config
from ..utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ReasoningResult:
    """推理结果"""
    strategy: str
    reasoning_steps: List[str]
    final_answer: str
    confidence: float
    reflection: Optional[Dict[str, Any]] = None
    verification: Optional[Dict[str, Any]] = None


class ProgrammingReasoningEngine:
    """编程推理引擎"""
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient()
        self.reasoning_config = config.get_reasoning_config()
        self.reasoning_history: List[ReasoningResult] = []
        
        # 配置参数
        self.default_strategy = self.reasoning_config.get('default_strategy', 'auto')
        self.max_reasoning_steps = self.reasoning_config.get('max_reasoning_steps', 10)
        self.confidence_threshold = self.reasoning_config.get('confidence_threshold', 0.7)
        self.enable_reflection = self.reasoning_config.get('enable_reflection', True)
        self.enable_verification = self.reasoning_config.get('enable_verification', True)
        
        logger.info("编程推理引擎初始化完成")
    
    def analyze_programming_request(self, request: str, context: Optional[Dict[str, Any]] = None) -> ReasoningResult:
        """分析编程请求并制定执行计划"""
        logger.info(f"开始分析编程请求: {request[:100]}...")
        
        # 1. 选择推理策略
        strategy = self._select_reasoning_strategy(request, context)
        logger.info(f"选择推理策略: {strategy}")
        
        # 2. 执行推理
        if strategy == 'chain_of_thought':
            result = self._chain_of_thought_reasoning(request, context)
        elif strategy == 'tree_of_thoughts':
            result = self._tree_of_thoughts_reasoning(request, context)
        else:
            result = self._basic_reasoning(request, context)
        
        # 3. 应用反思机制
        if self.enable_reflection and result.confidence < self.confidence_threshold:
            result = self._apply_reflection(result, request, context)
        
        # 4. 验证结果
        if self.enable_verification:
            result.verification = self._verify_reasoning(result, request, context)
        
        # 5. 记录推理历史
        self.reasoning_history.append(result)
        
        logger.info(f"推理完成 - 策略: {result.strategy}, 置信度: {result.confidence}")
        return result
    
    def _select_reasoning_strategy(self, request: str, context: Optional[Dict[str, Any]] = None) -> str:
        """选择最适合的推理策略"""
        if self.default_strategy != 'auto':
            return self.default_strategy
        
        # 分析请求复杂度
        complexity_prompt = f"""
        分析这个编程请求的复杂度，并推荐最佳的推理策略：
        
        请求: {request}
        上下文: {context or '无'}
        
        请从以下策略中选择一个：
        1. basic - 适用于简单的编程问题
        2. chain_of_thought - 适用于需要步骤分解的问题
        3. tree_of_thoughts - 适用于需要探索多种解决方案的复杂问题
        
        只回答策略名称（basic/chain_of_thought/tree_of_thoughts）。
        """
        
        try:
            response = self.llm.completion(complexity_prompt)
            strategy_text = self.llm.get_response_text(response).lower().strip()
            
            if 'tree_of_thoughts' in strategy_text:
                return 'tree_of_thoughts'
            elif 'chain_of_thought' in strategy_text:
                return 'chain_of_thought'
            else:
                return 'basic'
        except Exception as e:
            logger.warning(f"策略选择失败，使用默认策略: {e}")
            return 'basic'
    
    def _chain_of_thought_reasoning(self, request: str, context: Optional[Dict[str, Any]] = None) -> ReasoningResult:
        """Chain-of-Thought推理"""
        logger.info("执行Chain-of-Thought推理")
        
        cot_prompt = f"""
        请使用链式思维（Chain-of-Thought）方法逐步解决这个编程问题：
        
        问题: {request}
        上下文: {context or '无'}
        
        请按以下格式回答：
        1. 问题分析：[分析问题的核心需求]
        2. 解决方案设计：[设计解决方案的步骤]
        3. 技术选择：[选择合适的技术栈和工具]
        4. 实现计划：[具体的实现步骤]
        5. 潜在问题：[可能遇到的问题和解决方案]
        6. 最终答案：[完整的解决方案]
        7. 置信度：[0-1之间的数值]
        
        请确保每个步骤都有清晰的推理过程。
        """
        
        try:
            response = self.llm.completion(cot_prompt)
            response_text = self.llm.get_response_text(response)
            
            # 解析推理步骤
            steps = self._parse_reasoning_steps(response_text)
            confidence = self._extract_confidence(response_text)
            
            return ReasoningResult(
                strategy='chain_of_thought',
                reasoning_steps=steps,
                final_answer=response_text,
                confidence=confidence
            )
        
        except Exception as e:
            logger.error(f"Chain-of-Thought推理失败: {e}")
            return self._fallback_reasoning(request, context)
    
    def _tree_of_thoughts_reasoning(self, request: str, context: Optional[Dict[str, Any]] = None) -> ReasoningResult:
        """Tree of Thoughts推理"""
        logger.info("执行Tree of Thoughts推理")
        
        # 第一步：生成多个解决方案
        generation_prompt = f"""
        请为以下编程问题生成3个不同的解决方案：
        
        问题: {request}
        上下文: {context or '无'}
        
        请为每个方案提供：
        1. 方案名称
        2. 核心思路
        3. 技术栈
        4. 优势
        5. 劣势
        6. 适用场景
        
        格式：
        方案1: [名称]
        思路: [核心思路]
        技术: [技术栈]
        优势: [优势]
        劣势: [劣势]
        场景: [适用场景]
        
        方案2: ...
        方案3: ...
        """
        
        try:
            # 生成多个方案
            generation_response = self.llm.completion(generation_prompt)
            solutions_text = self.llm.get_response_text(generation_response)
            
            # 第二步：评估和选择最佳方案
            evaluation_prompt = f"""
            基于以下生成的解决方案，请选择最佳方案并提供详细的实现计划：
            
            原问题: {request}
            生成的方案: {solutions_text}
            
            请：
            1. 分析每个方案的可行性
            2. 选择最佳方案并说明理由
            3. 提供详细的实现步骤
            4. 给出置信度评估（0-1）
            
            最终回答格式：
            选择方案: [方案名称]
            选择理由: [详细理由]
            实现步骤: [具体步骤]
            置信度: [0-1数值]
            """
            
            evaluation_response = self.llm.completion(evaluation_prompt)
            evaluation_text = self.llm.get_response_text(evaluation_response)
            
            # 解析结果
            steps = self._parse_reasoning_steps(evaluation_text)
            confidence = self._extract_confidence(evaluation_text)
            
            # 合并完整答案
            full_answer = f"方案探索:\n{solutions_text}\n\n方案评估:\n{evaluation_text}"
            
            return ReasoningResult(
                strategy='tree_of_thoughts',
                reasoning_steps=steps,
                final_answer=full_answer,
                confidence=confidence
            )
        
        except Exception as e:
            logger.error(f"Tree of Thoughts推理失败: {e}")
            return self._fallback_reasoning(request, context)
    
    def _basic_reasoning(self, request: str, context: Optional[Dict[str, Any]] = None) -> ReasoningResult:
        """基础推理"""
        logger.info("执行基础推理")
        
        basic_prompt = f"""
        请直接回答这个编程问题：
        
        问题: {request}
        上下文: {context or '无'}
        
        请提供：
        1. 解决方案
        2. 代码示例（如果适用）
        3. 使用说明
        4. 注意事项
        """
        
        try:
            response = self.llm.completion(basic_prompt)
            response_text = self.llm.get_response_text(response)
            
            return ReasoningResult(
                strategy='basic',
                reasoning_steps=[response_text],
                final_answer=response_text,
                confidence=0.7  # 基础推理的默认置信度
            )
        
        except Exception as e:
            logger.error(f"基础推理失败: {e}")
            return ReasoningResult(
                strategy='basic',
                reasoning_steps=["推理失败，请检查输入"],
                final_answer="抱歉，无法处理您的请求。请检查输入并重试。",
                confidence=0.1
            )
    
    def _apply_reflection(self, result: ReasoningResult, request: str, context: Optional[Dict[str, Any]] = None) -> ReasoningResult:
        """应用反思机制改进结果"""
        logger.info("应用反思机制")
        
        reflection_prompt = f"""
        请对以下解决方案进行反思和改进：
        
        原问题: {request}
        当前解决方案: {result.final_answer}
        当前置信度: {result.confidence}
        
        请：
        1. 识别解决方案中的潜在问题
        2. 提出改进建议
        3. 提供改进后的解决方案
        4. 重新评估置信度
        
        格式：
        问题识别: [发现的问题]
        改进建议: [具体建议]
        改进方案: [改进后的解决方案]
        新置信度: [0-1数值]
        """
        
        try:
            response = self.llm.completion(reflection_prompt)
            reflection_text = self.llm.get_response_text(response)
            
            # 提取改进后的置信度
            new_confidence = self._extract_confidence(reflection_text)
            if new_confidence > result.confidence:
                result.confidence = new_confidence
                result.final_answer = reflection_text
            
            result.reflection = {
                'applied': True,
                'reflection_text': reflection_text,
                'improvement_found': new_confidence > result.confidence
            }
            
            logger.info(f"反思完成 - 置信度变化: {result.confidence} -> {new_confidence}")
            
        except Exception as e:
            logger.warning(f"反思机制失败: {e}")
            result.reflection = {
                'applied': False,
                'error': str(e)
            }
        
        return result
    
    def _verify_reasoning(self, result: ReasoningResult, request: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """验证推理结果"""
        logger.info("验证推理结果")
        
        verification_prompt = f"""
        请验证以下解决方案的正确性和可行性：
        
        原问题: {request}
        解决方案: {result.final_answer}
        
        请检查：
        1. 解决方案是否正确回答了问题
        2. 技术方案是否可行
        3. 代码示例是否正确（如果有）
        4. 是否遗漏了重要考虑因素
        
        请回答：
        验证结果: PASS/FAIL
        验证说明: [详细说明]
        改进建议: [如果有问题，提供改进建议]
        """
        
        try:
            response = self.llm.completion(verification_prompt)
            verification_text = self.llm.get_response_text(response)
            
            is_verified = 'PASS' in verification_text.upper()
            
            return {
                'is_verified': is_verified,
                'verification_text': verification_text,
                'verification_applied': True
            }
        
        except Exception as e:
            logger.warning(f"验证失败: {e}")
            return {
                'is_verified': False,
                'verification_text': f"验证失败: {e}",
                'verification_applied': False
            }
    
    def _parse_reasoning_steps(self, text: str) -> List[str]:
        """解析推理步骤"""
        steps = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if line and (
                line[0].isdigit() or 
                line.startswith('-') or 
                line.startswith('•') or
                line.startswith('步骤') or
                line.startswith('Step')
            ):
                steps.append(line)
        
        return steps if steps else [text]
    
    def _extract_confidence(self, text: str) -> float:
        """从文本中提取置信度"""
        import re
        
        # 查找置信度模式
        patterns = [
            r'置信度[：:]\s*([0-9.]+)',
            r'confidence[：:]\s*([0-9.]+)',
            r'新置信度[：:]\s*([0-9.]+)',
            r'([0-9.]+)\s*置信度'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    confidence = float(match.group(1))
                    return min(max(confidence, 0.0), 1.0)  # 确保在0-1范围内
                except ValueError:
                    continue
        
        # 如果没有找到置信度，根据文本质量估算
        if '错误' in text or 'error' in text.lower() or '失败' in text:
            return 0.3
        elif '优秀' in text or 'excellent' in text.lower() or '完美' in text:
            return 0.9
        else:
            return 0.7  # 默认置信度
    
    def _fallback_reasoning(self, request: str, context: Optional[Dict[str, Any]] = None) -> ReasoningResult:
        """后备推理方法"""
        return ReasoningResult(
            strategy='fallback',
            reasoning_steps=["使用后备推理方法"],
            final_answer=f"抱歉，无法完全处理您的请求：{request}。请尝试重新表述问题或提供更多上下文。",
            confidence=0.2
        )
    
    def get_reasoning_summary(self) -> Dict[str, Any]:
        """获取推理性能摘要"""
        if not self.reasoning_history:
            return {
                'total_requests': 0,
                'average_confidence': 0.0,
                'strategy_distribution': {},
                'reflection_usage': 0.0,
                'verification_success_rate': 0.0
            }
        
        total_requests = len(self.reasoning_history)
        total_confidence = sum(r.confidence for r in self.reasoning_history)
        average_confidence = total_confidence / total_requests
        
        # 策略分布
        strategy_counts = {}
        for result in self.reasoning_history:
            strategy_counts[result.strategy] = strategy_counts.get(result.strategy, 0) + 1
        
        # 反思使用率
        reflection_used = sum(1 for r in self.reasoning_history if r.reflection and r.reflection.get('applied'))
        reflection_usage = reflection_used / total_requests
        
        # 验证成功率
        verified_results = sum(1 for r in self.reasoning_history if r.verification and r.verification.get('is_verified'))
        verification_success_rate = verified_results / total_requests
        
        return {
            'total_requests': total_requests,
            'average_confidence': average_confidence,
            'strategy_distribution': strategy_counts,
            'reflection_usage': reflection_usage,
            'verification_success_rate': verification_success_rate
        }