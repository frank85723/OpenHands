"""智能编程助手主类"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import time

from .utils.llm_client import LLMClient
from .utils.config_loader import config
from .utils.logger import get_logger

from .core.reasoning_engine import ProgrammingReasoningEngine
from .core.tool_manager import ProgrammingToolManager
from .core.memory_system import CodeMemorySystem
from .core.collaboration_system import ProgrammingTeamSystem
from .core.learning_system import CodingLearningSystem
from .core.security_system import CodeSecuritySystem
from .core.domain_experts import TechStackExperts
from .core.evaluation_system import CodingEvaluationSystem

logger = get_logger(__name__)


@dataclass
class AssistantResponse:
    """助手响应结果"""
    code: str
    explanation: str
    reasoning_steps: List[str]
    tools_used: List[str]
    collaboration_roles: List[str]
    security_report: Dict[str, Any]
    confidence: float
    execution_time: float
    learning_insights: Dict[str, Any]
    evaluation_metrics: Dict[str, Any]


class IntelligentProgrammingAssistant:
    """智能编程助手"""
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        """初始化智能编程助手"""
        logger.info("初始化智能编程助手...")
        
        # 初始化LLM客户端
        self.llm = llm_client or LLMClient()
        
        # 初始化8个核心系统
        self.reasoning_engine = ProgrammingReasoningEngine(self.llm)
        self.tool_manager = ProgrammingToolManager(self.llm)
        self.memory_system = CodeMemorySystem(self.llm)
        self.collaboration_system = ProgrammingTeamSystem(self.llm)
        self.learning_system = CodingLearningSystem(self.llm)
        self.security_system = CodeSecuritySystem(self.llm)
        self.domain_experts = TechStackExperts(self.llm)
        self.evaluation_system = CodingEvaluationSystem(self.llm)
        
        # 会话状态
        self.session_context = {}
        self.request_count = 0
        
        logger.info("智能编程助手初始化完成")
    
    def handle_request(
        self, 
        request: str, 
        user_context: Optional[Dict[str, Any]] = None,
        enable_collaboration: bool = False,
        enable_learning: bool = True
    ) -> AssistantResponse:
        """处理编程请求的完整流程"""
        start_time = time.time()
        self.request_count += 1
        
        logger.info(f"处理第{self.request_count}个请求: {request[:100]}...")
        
        try:
            # 1. 安全检查
            security_check = self.security_system.validate_request(request, user_context)
            if not security_check['is_safe']:
                return self._create_security_violation_response(security_check)
            
            # 2. 推理和规划
            reasoning_result = self.reasoning_engine.analyze_programming_request(
                request, user_context
            )
            
            # 3. 记忆检索
            relevant_context = self.memory_system.retrieve_relevant_context(
                request, user_context
            )
            
            # 4. 领域专家咨询
            expert_guidance = self.domain_experts.get_expert_guidance(
                request, user_context
            )
            
            # 5. 执行编程任务
            if enable_collaboration and self._should_use_collaboration(reasoning_result):
                # 多角色协作
                collab_result = self.collaboration_system.collaborative_programming(
                    request, reasoning_result, relevant_context, expert_guidance
                )
                execution_result = {
                    'code': collab_result.code,
                    'explanation': collab_result.explanation,
                    'tools_used': [],
                    'success': True
                }
                collaboration_roles = collab_result.roles_used
            else:
                # 单一工具执行
                tool_result = self.tool_manager.execute_programming_task(
                    request, reasoning_result, relevant_context, expert_guidance
                )
                execution_result = {
                    'code': tool_result.code,
                    'explanation': tool_result.explanation,
                    'tools_used': tool_result.tools_used,
                    'success': tool_result.success
                }
                collaboration_roles = []
            
            # 6. 安全验证
            security_report = self.security_system.validate_code_output(
                execution_result.get('code', ''), user_context
            )
            
            # 7. 学习更新
            learning_insights = {}
            if enable_learning:
                learning_data = {
                    'request': request,
                    'reasoning_result': reasoning_result,
                    'execution_result': execution_result,
                    'user_context': user_context,
                    'security_report': security_report
                }
                learning_insights = self.learning_system.learn_from_session(learning_data)
            
            # 8. 更新记忆
            self.memory_system.update_memory(
                request, execution_result, reasoning_result, user_context
            )
            
            # 9. 性能评估
            evaluation_data = {
                'request': request,
                'result': execution_result,
                'reasoning': reasoning_result,
                'execution_time': time.time() - start_time,
                'security_report': security_report
            }
            evaluation_metrics = self.evaluation_system.evaluate_session(evaluation_data)
            
            # 10. 构建响应
            response = AssistantResponse(
                code=execution_result.get('code', ''),
                explanation=execution_result.get('explanation', ''),
                reasoning_steps=reasoning_result.reasoning_steps,
                tools_used=execution_result.get('tools_used', []),
                collaboration_roles=collaboration_roles,
                security_report=security_report,
                confidence=reasoning_result.confidence,
                execution_time=time.time() - start_time,
                learning_insights=learning_insights,
                evaluation_metrics=evaluation_metrics
            )
            
            logger.info(f"请求处理完成 - 耗时: {response.execution_time:.2f}s, 置信度: {response.confidence}")
            return response
            
        except Exception as e:
            logger.error(f"请求处理失败: {e}")
            return self._create_error_response(str(e), time.time() - start_time)
    
    def _should_use_collaboration(self, reasoning_result) -> bool:
        """判断是否应该使用多角色协作"""
        # 基于推理结果的复杂度和置信度决定
        complex_keywords = ['系统', '架构', '完整', '项目', '应用', '平台']
        request_text = reasoning_result.final_answer.lower()
        
        has_complex_keywords = any(keyword in request_text for keyword in complex_keywords)
        low_confidence = reasoning_result.confidence < 0.7
        
        return has_complex_keywords or low_confidence
    
    def _create_security_violation_response(self, security_check: Dict[str, Any]) -> AssistantResponse:
        """创建安全违规响应"""
        return AssistantResponse(
            code="",
            explanation="请求被安全系统拒绝",
            reasoning_steps=["安全检查失败"],
            tools_used=[],
            collaboration_roles=[],
            security_report=security_check,
            confidence=0.0,
            execution_time=0.0,
            learning_insights={},
            evaluation_metrics={}
        )
    
    def _create_error_response(self, error_message: str, execution_time: float) -> AssistantResponse:
        """创建错误响应"""
        return AssistantResponse(
            code="",
            explanation=f"处理请求时发生错误: {error_message}",
            reasoning_steps=["错误处理"],
            tools_used=[],
            collaboration_roles=[],
            security_report={'is_safe': False, 'error': error_message},
            confidence=0.0,
            execution_time=execution_time,
            learning_insights={},
            evaluation_metrics={}
        )
    
    def get_session_summary(self) -> Dict[str, Any]:
        """获取会话摘要"""
        return {
            'request_count': self.request_count,
            'reasoning_summary': self.reasoning_engine.get_reasoning_summary(),
            'tool_usage_summary': self.tool_manager.get_usage_summary(),
            'memory_summary': self.memory_system.get_memory_summary(),
            'learning_summary': self.learning_system.get_learning_summary(),
            'security_summary': self.security_system.get_security_summary(),
            'evaluation_summary': self.evaluation_system.get_evaluation_summary()
        }
    
    def reset_session(self):
        """重置会话状态"""
        logger.info("重置会话状态")
        self.session_context = {}
        self.request_count = 0
        
        # 重置各个系统的会话状态
        self.memory_system.clear_short_term_memory()
        self.learning_system.reset_session()
        self.evaluation_system.reset_session()
    
    def save_session(self, filepath: str):
        """保存会话数据"""
        import json
        
        session_data = {
            'session_context': self.session_context,
            'request_count': self.request_count,
            'memory_data': self.memory_system.export_memory(),
            'learning_data': self.learning_system.export_learning_data(),
            'reasoning_history': [
                {
                    'strategy': r.strategy,
                    'confidence': r.confidence,
                    'reasoning_steps': r.reasoning_steps
                }
                for r in self.reasoning_engine.reasoning_history
            ]
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"会话数据已保存到: {filepath}")
    
    def load_session(self, filepath: str):
        """加载会话数据"""
        import json
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            self.session_context = session_data.get('session_context', {})
            self.request_count = session_data.get('request_count', 0)
            
            # 恢复各系统状态
            if 'memory_data' in session_data:
                self.memory_system.import_memory(session_data['memory_data'])
            
            if 'learning_data' in session_data:
                self.learning_system.import_learning_data(session_data['learning_data'])
            
            logger.info(f"会话数据已从 {filepath} 加载")
            
        except Exception as e:
            logger.error(f"加载会话数据失败: {e}")
            raise