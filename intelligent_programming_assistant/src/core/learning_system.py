"""学习系统 - 自主学习和适应"""

import json
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

from ..utils.llm_client import LLMClient
from ..utils.config_loader import config
from ..utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class LearningPattern:
    """学习模式"""
    pattern_id: str
    pattern_type: str
    description: str
    success_rate: float
    usage_count: int
    last_used: float
    effectiveness_score: float


class CodingLearningSystem:
    """编程学习系统"""
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient()
        self.learning_config = config.get_learning_config()
        
        # 学习数据存储
        self.learning_patterns: List[LearningPattern] = []
        self.feedback_history: List[Dict[str, Any]] = []
        self.performance_metrics: Dict[str, float] = {}
        
        # 配置参数
        self.enable_learning = self.learning_config.get('enable_learning', True)
        self.feedback_weight = self.learning_config.get('feedback_weight', 0.3)
        self.pattern_threshold = self.learning_config.get('pattern_recognition_threshold', 0.7)
        self.learning_rate = self.learning_config.get('learning_rate', 0.1)
        self.max_history = self.learning_config.get('max_learning_history', 1000)
        
        logger.info("编程学习系统初始化完成")
    
    def learn_from_session(self, learning_data: Dict[str, Any]) -> Dict[str, Any]:
        """从会话中学习"""
        if not self.enable_learning:
            return {'learning_enabled': False}
        
        logger.info("开始从会话中学习")
        
        try:
            # 1. 分析会话数据
            session_analysis = self._analyze_session_data(learning_data)
            
            # 2. 提取成功模式
            success_patterns = self._extract_success_patterns(learning_data, session_analysis)
            
            # 3. 更新学习模式
            self._update_learning_patterns(success_patterns)
            
            # 4. 分析失败原因
            failure_analysis = self._analyze_failures(learning_data, session_analysis)
            
            # 5. 更新性能指标
            self._update_performance_metrics(learning_data, session_analysis)
            
            # 6. 生成学习洞察
            learning_insights = self._generate_learning_insights(
                session_analysis, success_patterns, failure_analysis
            )
            
            # 7. 记录反馈历史
            self.feedback_history.append({
                'timestamp': time.time(),
                'learning_data': learning_data,
                'session_analysis': session_analysis,
                'success_patterns': success_patterns,
                'failure_analysis': failure_analysis,
                'learning_insights': learning_insights
            })
            
            # 管理历史记录大小
            if len(self.feedback_history) > self.max_history:
                self.feedback_history = self.feedback_history[-self.max_history:]
            
            logger.info(f"学习完成 - 发现 {len(success_patterns)} 个成功模式")
            return learning_insights
            
        except Exception as e:
            logger.error(f"学习过程失败: {e}")
            return {'learning_error': str(e)}
    
    def _analyze_session_data(self, learning_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析会话数据"""
        analysis_prompt = f"""
        分析以下编程会话的数据，提取关键信息：
        
        请求: {learning_data.get('request', '')}
        推理结果: {learning_data.get('reasoning_result', {}).get('final_answer', '') if learning_data.get('reasoning_result') else ''}
        执行结果: {learning_data.get('execution_result', {})}
        安全报告: {learning_data.get('security_report', {})}
        用户上下文: {learning_data.get('user_context', {})}
        
        请分析：
        1. 任务类型和复杂度
        2. 使用的技术栈
        3. 解决方案的质量
        4. 执行效率
        5. 潜在的改进点
        6. 成功因素
        7. 失败因素（如果有）
        
        请提供结构化的分析结果。
        """
        
        try:
            response = self.llm.completion(analysis_prompt)
            analysis_text = self.llm.get_response_text(response)
            
            return {
                'analysis_text': analysis_text,
                'task_type': self._extract_task_type(analysis_text),
                'complexity': self._extract_complexity(analysis_text),
                'tech_stack': self._extract_tech_stack(analysis_text),
                'quality_score': self._extract_quality_score(analysis_text),
                'efficiency_score': self._extract_efficiency_score(analysis_text),
                'success_factors': self._extract_success_factors(analysis_text),
                'failure_factors': self._extract_failure_factors(analysis_text)
            }
        except Exception as e:
            logger.warning(f"会话数据分析失败: {e}")
            return {
                'analysis_text': '',
                'task_type': 'unknown',
                'complexity': 'medium',
                'tech_stack': [],
                'quality_score': 0.5,
                'efficiency_score': 0.5,
                'success_factors': [],
                'failure_factors': []
            }
    
    def _extract_success_patterns(
        self, 
        learning_data: Dict[str, Any], 
        session_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """提取成功模式"""
        # 判断会话是否成功
        reasoning_result = learning_data.get('reasoning_result')
        execution_result = learning_data.get('execution_result', {})
        security_report = learning_data.get('security_report', {})
        
        is_successful = (
            reasoning_result and reasoning_result.confidence > 0.7 and
            execution_result.get('success', False) and
            security_report.get('is_safe', True)
        )
        
        if not is_successful:
            return []
        
        patterns = []
        
        # 推理策略模式
        if reasoning_result:
            patterns.append({
                'pattern_type': 'reasoning_strategy',
                'strategy': reasoning_result.strategy,
                'confidence': reasoning_result.confidence,
                'task_type': session_analysis.get('task_type'),
                'complexity': session_analysis.get('complexity'),
                'success_rate': 1.0
            })
        
        # 工具使用模式
        tools_used = execution_result.get('tools_used', [])
        if tools_used:
            patterns.append({
                'pattern_type': 'tool_usage',
                'tools': tools_used,
                'task_type': session_analysis.get('task_type'),
                'execution_time': execution_result.get('execution_time', 0),
                'success_rate': 1.0
            })
        
        # 技术栈模式
        tech_stack = session_analysis.get('tech_stack', [])
        if tech_stack:
            patterns.append({
                'pattern_type': 'tech_stack',
                'technologies': tech_stack,
                'task_type': session_analysis.get('task_type'),
                'quality_score': session_analysis.get('quality_score', 0.5),
                'success_rate': 1.0
            })
        
        return patterns
    
    def _update_learning_patterns(self, success_patterns: List[Dict[str, Any]]):
        """更新学习模式"""
        for pattern_data in success_patterns:
            pattern_id = self._generate_pattern_id(pattern_data)
            
            # 查找现有模式
            existing_pattern = None
            for pattern in self.learning_patterns:
                if pattern.pattern_id == pattern_id:
                    existing_pattern = pattern
                    break
            
            if existing_pattern:
                # 更新现有模式
                existing_pattern.usage_count += 1
                existing_pattern.last_used = time.time()
                
                # 更新成功率（使用指数移动平均）
                new_success_rate = pattern_data.get('success_rate', 1.0)
                existing_pattern.success_rate = (
                    (1 - self.learning_rate) * existing_pattern.success_rate +
                    self.learning_rate * new_success_rate
                )
                
                # 更新效果评分
                existing_pattern.effectiveness_score = (
                    existing_pattern.success_rate * 0.7 +
                    min(existing_pattern.usage_count / 10, 1.0) * 0.3
                )
            else:
                # 创建新模式
                new_pattern = LearningPattern(
                    pattern_id=pattern_id,
                    pattern_type=pattern_data.get('pattern_type', 'unknown'),
                    description=self._generate_pattern_description(pattern_data),
                    success_rate=pattern_data.get('success_rate', 1.0),
                    usage_count=1,
                    last_used=time.time(),
                    effectiveness_score=pattern_data.get('success_rate', 1.0)
                )
                self.learning_patterns.append(new_pattern)
    
    def _analyze_failures(
        self, 
        learning_data: Dict[str, Any], 
        session_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """分析失败原因"""
        reasoning_result = learning_data.get('reasoning_result')
        execution_result = learning_data.get('execution_result', {})
        security_report = learning_data.get('security_report', {})
        
        failures = []
        
        # 推理失败
        if not reasoning_result or reasoning_result.confidence < 0.5:
            failures.append({
                'type': 'reasoning_failure',
                'reason': 'Low confidence in reasoning',
                'confidence': reasoning_result.confidence if reasoning_result else 0.0
            })
        
        # 执行失败
        if not execution_result.get('success', True):
            failures.append({
                'type': 'execution_failure',
                'reason': execution_result.get('error_message', 'Unknown execution error')
            })
        
        # 安全问题
        if not security_report.get('is_safe', True):
            failures.append({
                'type': 'security_failure',
                'reason': security_report.get('error', 'Security validation failed')
            })
        
        return {
            'has_failures': len(failures) > 0,
            'failure_count': len(failures),
            'failures': failures,
            'failure_analysis': self._generate_failure_analysis(failures) if failures else None
        }
    
    def _generate_failure_analysis(self, failures: List[Dict[str, Any]]) -> str:
        """生成失败分析"""
        analysis_prompt = f"""
        分析以下失败情况，提供改进建议：
        
        失败列表:
        {json.dumps(failures, ensure_ascii=False, indent=2)}
        
        请提供：
        1. 失败原因分析
        2. 改进建议
        3. 预防措施
        4. 优化策略
        """
        
        try:
            response = self.llm.completion(analysis_prompt)
            return self.llm.get_response_text(response)
        except Exception as e:
            return f"失败分析生成失败: {e}"
    
    def _update_performance_metrics(
        self, 
        learning_data: Dict[str, Any], 
        session_analysis: Dict[str, Any]
    ):
        """更新性能指标"""
        # 更新平均置信度
        reasoning_result = learning_data.get('reasoning_result')
        if reasoning_result:
            current_confidence = self.performance_metrics.get('average_confidence', 0.5)
            new_confidence = reasoning_result.confidence
            self.performance_metrics['average_confidence'] = (
                current_confidence * 0.9 + new_confidence * 0.1
            )
        
        # 更新平均质量分数
        quality_score = session_analysis.get('quality_score', 0.5)
        current_quality = self.performance_metrics.get('average_quality', 0.5)
        self.performance_metrics['average_quality'] = (
            current_quality * 0.9 + quality_score * 0.1
        )
        
        # 更新平均效率分数
        efficiency_score = session_analysis.get('efficiency_score', 0.5)
        current_efficiency = self.performance_metrics.get('average_efficiency', 0.5)
        self.performance_metrics['average_efficiency'] = (
            current_efficiency * 0.9 + efficiency_score * 0.1
        )
        
        # 更新成功率
        execution_result = learning_data.get('execution_result', {})
        is_successful = execution_result.get('success', False)
        current_success_rate = self.performance_metrics.get('success_rate', 0.5)
        success_value = 1.0 if is_successful else 0.0
        self.performance_metrics['success_rate'] = (
            current_success_rate * 0.9 + success_value * 0.1
        )
    
    def _generate_learning_insights(
        self,
        session_analysis: Dict[str, Any],
        success_patterns: List[Dict[str, Any]],
        failure_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成学习洞察"""
        insights = {
            'session_summary': {
                'task_type': session_analysis.get('task_type'),
                'complexity': session_analysis.get('complexity'),
                'quality_score': session_analysis.get('quality_score'),
                'efficiency_score': session_analysis.get('efficiency_score')
            },
            'patterns_learned': len(success_patterns),
            'pattern_types': list(set(p.get('pattern_type') for p in success_patterns)),
            'has_failures': failure_analysis.get('has_failures', False),
            'failure_count': failure_analysis.get('failure_count', 0),
            'performance_trends': self._analyze_performance_trends(),
            'recommendations': self._generate_recommendations(session_analysis, success_patterns, failure_analysis)
        }
        
        return insights
    
    def _analyze_performance_trends(self) -> Dict[str, Any]:
        """分析性能趋势"""
        if len(self.feedback_history) < 2:
            return {'trend_analysis': 'Insufficient data for trend analysis'}
        
        # 分析最近的性能变化
        recent_sessions = self.feedback_history[-10:]  # 最近10个会话
        
        confidence_trend = []
        quality_trend = []
        
        for session in recent_sessions:
            session_analysis = session.get('session_analysis', {})
            confidence_trend.append(session_analysis.get('quality_score', 0.5))
            quality_trend.append(session_analysis.get('efficiency_score', 0.5))
        
        return {
            'confidence_trend': 'improving' if confidence_trend[-1] > confidence_trend[0] else 'declining',
            'quality_trend': 'improving' if quality_trend[-1] > quality_trend[0] else 'declining',
            'recent_average_confidence': sum(confidence_trend) / len(confidence_trend),
            'recent_average_quality': sum(quality_trend) / len(quality_trend)
        }
    
    def _generate_recommendations(
        self,
        session_analysis: Dict[str, Any],
        success_patterns: List[Dict[str, Any]],
        failure_analysis: Dict[str, Any]
    ) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        # 基于成功模式的建议
        if success_patterns:
            most_successful_pattern = max(success_patterns, key=lambda x: x.get('success_rate', 0))
            recommendations.append(
                f"继续使用 {most_successful_pattern.get('pattern_type')} 模式，成功率较高"
            )
        
        # 基于失败分析的建议
        if failure_analysis.get('has_failures'):
            recommendations.append("关注失败原因分析，改进相关流程")
        
        # 基于性能指标的建议
        if self.performance_metrics.get('average_confidence', 0.5) < 0.6:
            recommendations.append("提高推理置信度，考虑使用更复杂的推理策略")
        
        if self.performance_metrics.get('average_quality', 0.5) < 0.6:
            recommendations.append("关注代码质量，增加代码审查和测试")
        
        return recommendations
    
    def get_best_patterns_for_task(self, task_type: str, complexity: str = None) -> List[LearningPattern]:
        """获取任务的最佳模式"""
        relevant_patterns = []
        
        for pattern in self.learning_patterns:
            # 这里简化处理，实际应该根据模式的上下文信息匹配
            if pattern.effectiveness_score > self.pattern_threshold:
                relevant_patterns.append(pattern)
        
        # 按效果评分排序
        relevant_patterns.sort(key=lambda x: x.effectiveness_score, reverse=True)
        
        return relevant_patterns[:5]  # 返回前5个最佳模式
    
    def _generate_pattern_id(self, pattern_data: Dict[str, Any]) -> str:
        """生成模式ID"""
        pattern_type = pattern_data.get('pattern_type', 'unknown')
        
        if pattern_type == 'reasoning_strategy':
            return f"reasoning_{pattern_data.get('strategy', 'unknown')}_{pattern_data.get('task_type', 'unknown')}"
        elif pattern_type == 'tool_usage':
            tools = '_'.join(sorted(pattern_data.get('tools', [])))
            return f"tools_{tools}_{pattern_data.get('task_type', 'unknown')}"
        elif pattern_type == 'tech_stack':
            techs = '_'.join(sorted(pattern_data.get('technologies', [])))
            return f"tech_{techs}_{pattern_data.get('task_type', 'unknown')}"
        else:
            return f"{pattern_type}_{hash(str(pattern_data)) % 10000}"
    
    def _generate_pattern_description(self, pattern_data: Dict[str, Any]) -> str:
        """生成模式描述"""
        pattern_type = pattern_data.get('pattern_type', 'unknown')
        
        if pattern_type == 'reasoning_strategy':
            return f"使用 {pattern_data.get('strategy')} 推理策略处理 {pattern_data.get('task_type')} 类型任务"
        elif pattern_type == 'tool_usage':
            tools = ', '.join(pattern_data.get('tools', []))
            return f"使用工具组合 [{tools}] 处理 {pattern_data.get('task_type')} 类型任务"
        elif pattern_type == 'tech_stack':
            techs = ', '.join(pattern_data.get('technologies', []))
            return f"使用技术栈 [{techs}] 实现 {pattern_data.get('task_type')} 类型项目"
        else:
            return f"{pattern_type} 模式"
    
    def _extract_task_type(self, text: str) -> str:
        """提取任务类型"""
        text_lower = text.lower()
        
        if 'web' in text_lower or 'api' in text_lower:
            return 'web_development'
        elif 'data' in text_lower or '数据' in text:
            return 'data_processing'
        elif 'algorithm' in text_lower or '算法' in text:
            return 'algorithm'
        elif 'test' in text_lower or '测试' in text:
            return 'testing'
        else:
            return 'general'
    
    def _extract_complexity(self, text: str) -> str:
        """提取复杂度"""
        text_lower = text.lower()
        
        if '复杂' in text or 'complex' in text_lower:
            return 'complex'
        elif '简单' in text or 'simple' in text_lower:
            return 'simple'
        else:
            return 'medium'
    
    def _extract_tech_stack(self, text: str) -> List[str]:
        """提取技术栈"""
        tech_keywords = ['python', 'javascript', 'react', 'django', 'flask', 'fastapi', 'docker', 'kubernetes']
        found_tech = []
        text_lower = text.lower()
        
        for tech in tech_keywords:
            if tech in text_lower:
                found_tech.append(tech)
        
        return found_tech
    
    def _extract_quality_score(self, text: str) -> float:
        """提取质量分数"""
        import re
        
        score_patterns = [
            r'质量[：:]\s*([0-9.]+)',
            r'quality[：:]\s*([0-9.]+)',
            r'([0-9.]+)\s*分'
        ]
        
        for pattern in score_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    score = float(match.group(1))
                    return min(max(score / 10 if score > 1 else score, 0.0), 1.0)
                except ValueError:
                    continue
        
        return 0.7  # 默认质量分数
    
    def _extract_efficiency_score(self, text: str) -> float:
        """提取效率分数"""
        import re
        
        efficiency_patterns = [
            r'效率[：:]\s*([0-9.]+)',
            r'efficiency[：:]\s*([0-9.]+)',
            r'性能[：:]\s*([0-9.]+)'
        ]
        
        for pattern in efficiency_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    score = float(match.group(1))
                    return min(max(score / 10 if score > 1 else score, 0.0), 1.0)
                except ValueError:
                    continue
        
        return 0.7  # 默认效率分数
    
    def _extract_success_factors(self, text: str) -> List[str]:
        """提取成功因素"""
        import re
        
        success_patterns = [
            r'成功因素[：:]\s*([^\n]+)',
            r'success factor[：:]\s*([^\n]+)',
            r'优势[：:]\s*([^\n]+)'
        ]
        
        factors = []
        for pattern in success_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            factors.extend(matches)
        
        return factors
    
    def _extract_failure_factors(self, text: str) -> List[str]:
        """提取失败因素"""
        import re
        
        failure_patterns = [
            r'失败因素[：:]\s*([^\n]+)',
            r'failure factor[：:]\s*([^\n]+)',
            r'问题[：:]\s*([^\n]+)',
            r'缺点[：:]\s*([^\n]+)'
        ]
        
        factors = []
        for pattern in failure_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            factors.extend(matches)
        
        return factors
    
    def reset_session(self):
        """重置会话状态"""
        # 保留学习模式和长期性能指标，只清除会话相关数据
        logger.info("重置学习系统会话状态")
    
    def export_learning_data(self) -> Dict[str, Any]:
        """导出学习数据"""
        return {
            'learning_patterns': [asdict(pattern) for pattern in self.learning_patterns],
            'performance_metrics': self.performance_metrics,
            'feedback_history': self.feedback_history[-100:],  # 只导出最近100条
            'export_timestamp': time.time()
        }
    
    def import_learning_data(self, learning_data: Dict[str, Any]):
        """导入学习数据"""
        try:
            # 导入学习模式
            self.learning_patterns = [
                LearningPattern(**pattern_data)
                for pattern_data in learning_data.get('learning_patterns', [])
            ]
            
            # 导入性能指标
            self.performance_metrics = learning_data.get('performance_metrics', {})
            
            # 导入反馈历史
            self.feedback_history = learning_data.get('feedback_history', [])
            
            logger.info("学习数据导入完成")
        except Exception as e:
            logger.error(f"学习数据导入失败: {e}")
    
    def get_learning_summary(self) -> Dict[str, Any]:
        """获取学习系统摘要"""
        if not self.learning_patterns:
            return {
                'total_patterns': 0,
                'average_effectiveness': 0.0,
                'most_effective_patterns': [],
                'performance_metrics': self.performance_metrics,
                'learning_enabled': self.enable_learning
            }
        
        total_patterns = len(self.learning_patterns)
        total_effectiveness = sum(p.effectiveness_score for p in self.learning_patterns)
        average_effectiveness = total_effectiveness / total_patterns
        
        # 最有效的模式
        most_effective = sorted(
            self.learning_patterns, 
            key=lambda x: x.effectiveness_score, 
            reverse=True
        )[:5]
        
        return {
            'total_patterns': total_patterns,
            'average_effectiveness': average_effectiveness,
            'most_effective_patterns': [
                {
                    'pattern_type': p.pattern_type,
                    'description': p.description,
                    'effectiveness_score': p.effectiveness_score,
                    'usage_count': p.usage_count
                }
                for p in most_effective
            ],
            'performance_metrics': self.performance_metrics,
            'learning_enabled': self.enable_learning,
            'total_feedback_sessions': len(self.feedback_history)
        }