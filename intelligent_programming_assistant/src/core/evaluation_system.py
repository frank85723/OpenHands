"""评估系统 - 性能监控和评估"""

import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

from ..utils.llm_client import LLMClient
from ..utils.config_loader import config
from ..utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class EvaluationMetrics:
    """评估指标"""
    code_quality_score: float
    performance_score: float
    security_score: float
    user_satisfaction_score: float
    execution_time: float
    reasoning_confidence: float
    tool_effectiveness: float
    overall_score: float


class CodingEvaluationSystem:
    """编程评估系统"""
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient()
        self.evaluation_config = config.get_evaluation_config()
        self.evaluation_history: List[Dict[str, Any]] = []
        
        # 配置参数
        self.enable_monitoring = self.evaluation_config.get('enable_performance_monitoring', True)
        self.quality_threshold = self.evaluation_config.get('quality_threshold', 0.8)
        self.performance_threshold = self.evaluation_config.get('performance_threshold', 5.0)
        self.enable_user_feedback = self.evaluation_config.get('enable_user_feedback', True)
        
        # 评估权重
        self.weights = {
            'code_quality': 0.25,
            'performance': 0.20,
            'security': 0.20,
            'user_satisfaction': 0.15,
            'execution_time': 0.10,
            'tool_effectiveness': 0.10
        }
        
        logger.info("编程评估系统初始化完成")
    
    def evaluate_session(self, evaluation_data: Dict[str, Any]) -> EvaluationMetrics:
        """评估会话性能"""
        if not self.enable_monitoring:
            return self._create_default_metrics()
        
        logger.info("开始评估会话性能")
        
        try:
            # 1. 代码质量评估
            code_quality_score = self._evaluate_code_quality(evaluation_data)
            
            # 2. 性能评估
            performance_score = self._evaluate_performance(evaluation_data)
            
            # 3. 安全评估
            security_score = self._evaluate_security(evaluation_data)
            
            # 4. 用户满意度评估
            user_satisfaction_score = self._evaluate_user_satisfaction(evaluation_data)
            
            # 5. 执行时间评估
            execution_time_score = self._evaluate_execution_time(evaluation_data)
            
            # 6. 推理置信度评估
            reasoning_confidence = self._evaluate_reasoning_confidence(evaluation_data)
            
            # 7. 工具有效性评估
            tool_effectiveness = self._evaluate_tool_effectiveness(evaluation_data)
            
            # 8. 计算总体评分
            overall_score = self._calculate_overall_score({
                'code_quality': code_quality_score,
                'performance': performance_score,
                'security': security_score,
                'user_satisfaction': user_satisfaction_score,
                'execution_time': execution_time_score,
                'tool_effectiveness': tool_effectiveness
            })
            
            metrics = EvaluationMetrics(
                code_quality_score=code_quality_score,
                performance_score=performance_score,
                security_score=security_score,
                user_satisfaction_score=user_satisfaction_score,
                execution_time=evaluation_data.get('execution_time', 0.0),
                reasoning_confidence=reasoning_confidence,
                tool_effectiveness=tool_effectiveness,
                overall_score=overall_score
            )
            
            # 记录评估历史
            self.evaluation_history.append({
                'metrics': asdict(metrics),
                'evaluation_data': evaluation_data,
                'timestamp': time.time()
            })
            
            logger.info(f"会话评估完成 - 总体评分: {overall_score:.2f}")
            return metrics
            
        except Exception as e:
            logger.error(f"会话评估失败: {e}")
            return self._create_default_metrics()
    
    def _evaluate_code_quality(self, evaluation_data: Dict[str, Any]) -> float:
        """评估代码质量"""
        result = evaluation_data.get('result', {})
        code = result.get('code', '')
        
        if not code:
            return 0.5  # 没有代码时的默认分数
        
        quality_prompt = f"""
        请评估以下代码的质量，给出0-1之间的分数：
        
        代码:
        {code[:2000]}  # 限制代码长度
        
        评估标准：
        1. 代码结构和组织 (20%)
        2. 可读性和注释 (20%)
        3. 错误处理 (15%)
        4. 性能考虑 (15%)
        5. 安全性 (15%)
        6. 可维护性 (15%)
        
        请只返回一个0-1之间的数值。
        """
        
        try:
            response = self.llm.completion(quality_prompt)
            response_text = self.llm.get_response_text(response).strip()
            
            # 尝试提取数值
            import re
            score_match = re.search(r'([0-9.]+)', response_text)
            if score_match:
                score = float(score_match.group(1))
                return min(max(score, 0.0), 1.0)
            
            return 0.7  # 默认分数
            
        except Exception as e:
            logger.warning(f"代码质量评估失败: {e}")
            return self._heuristic_code_quality_evaluation(code)
    
    def _heuristic_code_quality_evaluation(self, code: str) -> float:
        """启发式代码质量评估"""
        score = 0.5  # 基础分数
        
        # 代码长度合理性
        if 50 <= len(code) <= 2000:
            score += 0.1
        
        # 注释存在性
        if '#' in code or '"""' in code or "'''" in code:
            score += 0.1
        
        # 函数定义
        if 'def ' in code:
            score += 0.1
        
        # 错误处理
        if 'try:' in code or 'except' in code:
            score += 0.1
        
        # 导入语句
        if 'import ' in code:
            score += 0.1
        
        return min(score, 1.0)
    
    def _evaluate_performance(self, evaluation_data: Dict[str, Any]) -> float:
        """评估性能"""
        execution_time = evaluation_data.get('execution_time', 0.0)
        
        # 基于执行时间评估性能
        if execution_time <= 1.0:
            return 1.0
        elif execution_time <= 3.0:
            return 0.8
        elif execution_time <= 5.0:
            return 0.6
        elif execution_time <= 10.0:
            return 0.4
        else:
            return 0.2
    
    def _evaluate_security(self, evaluation_data: Dict[str, Any]) -> float:
        """评估安全性"""
        security_report = evaluation_data.get('security_report', {})
        
        if not security_report:
            return 0.5  # 没有安全报告时的默认分数
        
        is_safe = security_report.get('is_safe', True)
        total_issues = security_report.get('total_issues', 0)
        high_severity_issues = security_report.get('high_severity_issues', 0)
        
        if not is_safe or high_severity_issues > 0:
            return 0.2
        elif total_issues > 5:
            return 0.6
        elif total_issues > 2:
            return 0.8
        else:
            return 1.0
    
    def _evaluate_user_satisfaction(self, evaluation_data: Dict[str, Any]) -> float:
        """评估用户满意度"""
        # 这里可以基于用户反馈、请求完成度等因素评估
        reasoning = evaluation_data.get('reasoning', {})
        result = evaluation_data.get('result', {})
        
        satisfaction_score = 0.5  # 基础分数
        
        # 基于推理置信度
        if hasattr(reasoning, 'confidence'):
            satisfaction_score += reasoning.confidence * 0.3
        
        # 基于结果完整性
        if result.get('code') and result.get('explanation'):
            satisfaction_score += 0.2
        
        return min(satisfaction_score, 1.0)
    
    def _evaluate_execution_time(self, evaluation_data: Dict[str, Any]) -> float:
        """评估执行时间"""
        execution_time = evaluation_data.get('execution_time', 0.0)
        
        # 将执行时间转换为0-1分数
        if execution_time <= self.performance_threshold:
            return 1.0 - (execution_time / self.performance_threshold) * 0.5
        else:
            return 0.5 - min((execution_time - self.performance_threshold) / 10, 0.4)
    
    def _evaluate_reasoning_confidence(self, evaluation_data: Dict[str, Any]) -> float:
        """评估推理置信度"""
        reasoning = evaluation_data.get('reasoning', {})
        
        if hasattr(reasoning, 'confidence'):
            return reasoning.confidence
        else:
            return 0.7  # 默认置信度
    
    def _evaluate_tool_effectiveness(self, evaluation_data: Dict[str, Any]) -> float:
        """评估工具有效性"""
        result = evaluation_data.get('result', {})
        tools_used = result.get('tools_used', [])
        
        if not tools_used:
            return 0.5  # 没有使用工具时的默认分数
        
        # 基于工具数量和结果质量评估
        tool_count = len(tools_used)
        has_code = bool(result.get('code'))
        has_explanation = bool(result.get('explanation'))
        
        effectiveness = 0.3  # 基础分数
        
        if tool_count > 0:
            effectiveness += 0.2
        if tool_count > 2:
            effectiveness += 0.1
        if has_code:
            effectiveness += 0.2
        if has_explanation:
            effectiveness += 0.2
        
        return min(effectiveness, 1.0)
    
    def _calculate_overall_score(self, scores: Dict[str, float]) -> float:
        """计算总体评分"""
        weighted_sum = 0.0
        total_weight = 0.0
        
        for metric, score in scores.items():
            weight = self.weights.get(metric, 0.1)
            weighted_sum += score * weight
            total_weight += weight
        
        return weighted_sum / total_weight if total_weight > 0 else 0.5
    
    def _create_default_metrics(self) -> EvaluationMetrics:
        """创建默认评估指标"""
        return EvaluationMetrics(
            code_quality_score=0.7,
            performance_score=0.7,
            security_score=0.7,
            user_satisfaction_score=0.7,
            execution_time=0.0,
            reasoning_confidence=0.7,
            tool_effectiveness=0.7,
            overall_score=0.7
        )
    
    def analyze_performance_trends(self, window_size: int = 10) -> Dict[str, Any]:
        """分析性能趋势"""
        if len(self.evaluation_history) < 2:
            return {'trend_analysis': 'Insufficient data for trend analysis'}
        
        recent_evaluations = self.evaluation_history[-window_size:]
        
        # 提取各项指标的趋势
        trends = {}
        metrics = ['code_quality_score', 'performance_score', 'security_score', 
                  'user_satisfaction_score', 'overall_score']
        
        for metric in metrics:
            values = [eval_data['metrics'][metric] for eval_data in recent_evaluations]
            
            if len(values) >= 2:
                # 简单的趋势分析：比较最近值和平均值
                recent_avg = sum(values[-3:]) / min(3, len(values))
                overall_avg = sum(values) / len(values)
                
                if recent_avg > overall_avg + 0.05:
                    trend = 'improving'
                elif recent_avg < overall_avg - 0.05:
                    trend = 'declining'
                else:
                    trend = 'stable'
                
                trends[metric] = {
                    'trend': trend,
                    'recent_average': recent_avg,
                    'overall_average': overall_avg,
                    'change': recent_avg - overall_avg
                }
        
        return {
            'trends': trends,
            'evaluation_count': len(recent_evaluations),
            'window_size': window_size
        }
    
    def get_performance_recommendations(self) -> List[str]:
        """获取性能改进建议"""
        if not self.evaluation_history:
            return ["暂无足够数据提供建议"]
        
        recommendations = []
        recent_metrics = self.evaluation_history[-1]['metrics']
        
        # 基于各项指标给出建议
        if recent_metrics['code_quality_score'] < self.quality_threshold:
            recommendations.append("代码质量需要改进：增加注释、优化结构、加强错误处理")
        
        if recent_metrics['performance_score'] < 0.7:
            recommendations.append("性能需要优化：减少执行时间、优化算法复杂度")
        
        if recent_metrics['security_score'] < 0.8:
            recommendations.append("安全性需要加强：修复安全漏洞、加强输入验证")
        
        if recent_metrics['tool_effectiveness'] < 0.7:
            recommendations.append("工具使用效率需要提升：选择更合适的工具组合")
        
        if recent_metrics['reasoning_confidence'] < 0.7:
            recommendations.append("推理置信度需要提高：使用更复杂的推理策略")
        
        if not recommendations:
            recommendations.append("当前性能表现良好，继续保持")
        
        return recommendations
    
    def generate_performance_report(self) -> Dict[str, Any]:
        """生成性能报告"""
        if not self.evaluation_history:
            return {'error': 'No evaluation data available'}
        
        # 计算统计信息
        all_metrics = [eval_data['metrics'] for eval_data in self.evaluation_history]
        
        avg_metrics = {}
        for metric in ['code_quality_score', 'performance_score', 'security_score', 
                      'user_satisfaction_score', 'overall_score']:
            values = [metrics[metric] for metrics in all_metrics]
            avg_metrics[metric] = {
                'average': sum(values) / len(values),
                'min': min(values),
                'max': max(values),
                'latest': values[-1]
            }
        
        # 性能趋势
        trends = self.analyze_performance_trends()
        
        # 改进建议
        recommendations = self.get_performance_recommendations()
        
        return {
            'evaluation_period': {
                'start_time': self.evaluation_history[0]['timestamp'],
                'end_time': self.evaluation_history[-1]['timestamp'],
                'total_evaluations': len(self.evaluation_history)
            },
            'average_metrics': avg_metrics,
            'performance_trends': trends,
            'recommendations': recommendations,
            'quality_threshold': self.quality_threshold,
            'performance_threshold': self.performance_threshold
        }
    
    def reset_session(self):
        """重置会话状态"""
        # 保留历史数据，只重置会话相关状态
        logger.info("重置评估系统会话状态")
    
    def get_evaluation_summary(self) -> Dict[str, Any]:
        """获取评估系统摘要"""
        if not self.evaluation_history:
            return {
                'total_evaluations': 0,
                'average_overall_score': 0.0,
                'latest_score': 0.0,
                'evaluation_enabled': self.enable_monitoring
            }
        
        all_scores = [eval_data['metrics']['overall_score'] for eval_data in self.evaluation_history]
        
        return {
            'total_evaluations': len(self.evaluation_history),
            'average_overall_score': sum(all_scores) / len(all_scores),
            'latest_score': all_scores[-1],
            'best_score': max(all_scores),
            'worst_score': min(all_scores),
            'evaluation_enabled': self.enable_monitoring,
            'quality_threshold': self.quality_threshold,
            'performance_threshold': self.performance_threshold
        }