"""智能编程助手测试"""

import pytest
import sys
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.assistant import IntelligentProgrammingAssistant
from src.utils.config_loader import config


class TestIntelligentProgrammingAssistant:
    """智能编程助手测试类"""
    
    @pytest.fixture
    def assistant(self):
        """创建助手实例"""
        # 设置测试模式
        config._config = config._config or {}
        config._config['development'] = {'test_mode': True, 'mock_llm': True}
        
        return IntelligentProgrammingAssistant()
    
    def test_assistant_initialization(self, assistant):
        """测试助手初始化"""
        assert assistant is not None
        assert assistant.request_count == 0
        assert assistant.reasoning_engine is not None
        assert assistant.tool_manager is not None
        assert assistant.memory_system is not None
    
    def test_basic_request_handling(self, assistant):
        """测试基本请求处理"""
        request = "创建一个简单的Hello World程序"
        response = assistant.handle_request(request)
        
        assert response is not None
        assert response.execution_time > 0
        assert response.confidence >= 0
        assert isinstance(response.reasoning_steps, list)
        assert isinstance(response.tools_used, list)
    
    def test_code_generation(self, assistant):
        """测试代码生成"""
        request = "写一个Python函数来计算两个数的和"
        response = assistant.handle_request(request)
        
        assert response.code is not None
        assert response.explanation is not None
        assert len(response.reasoning_steps) > 0
    
    def test_collaboration_mode(self, assistant):
        """测试协作模式"""
        request = "创建一个完整的Web应用系统"
        response = assistant.handle_request(
            request, 
            enable_collaboration=True
        )
        
        assert response is not None
        # 在协作模式下可能会有角色参与
        assert isinstance(response.collaboration_roles, list)
    
    def test_security_validation(self, assistant):
        """测试安全验证"""
        # 测试安全的请求
        safe_request = "创建一个数据验证函数"
        response = assistant.handle_request(safe_request)
        
        assert response.security_report is not None
        assert 'is_safe' in response.security_report
    
    def test_session_management(self, assistant):
        """测试会话管理"""
        # 发送几个请求
        requests = [
            "创建一个计算器",
            "添加历史记录功能",
            "优化性能"
        ]
        
        for request in requests:
            assistant.handle_request(request)
        
        assert assistant.request_count == len(requests)
        
        # 测试会话摘要
        summary = assistant.get_session_summary()
        assert summary['request_count'] == len(requests)
        
        # 测试会话重置
        assistant.reset_session()
        assert assistant.request_count == 0
    
    def test_learning_system(self, assistant):
        """测试学习系统"""
        request = "创建一个排序算法"
        response = assistant.handle_request(request, enable_learning=True)
        
        assert response.learning_insights is not None
        
        # 检查学习摘要
        learning_summary = assistant.learning_system.get_learning_summary()
        assert 'total_patterns' in learning_summary
        assert 'learning_enabled' in learning_summary
    
    def test_memory_system(self, assistant):
        """测试记忆系统"""
        # 发送一个请求以创建记忆
        request = "创建一个用户管理系统"
        assistant.handle_request(request)
        
        # 检查记忆摘要
        memory_summary = assistant.memory_system.get_memory_summary()
        assert 'total_memories' in memory_summary
        assert memory_summary['total_memories'] >= 0
    
    def test_domain_experts(self, assistant):
        """测试领域专家系统"""
        request = "使用Python和Django创建Web API"
        expert_guidance = assistant.domain_experts.get_expert_guidance(request)
        
        assert expert_guidance is not None
        assert 'relevant_technologies' in expert_guidance
        assert 'expert_advice' in expert_guidance
    
    def test_evaluation_system(self, assistant):
        """测试评估系统"""
        request = "创建一个数据处理脚本"
        response = assistant.handle_request(request)
        
        assert response.evaluation_metrics is not None
        
        # 检查评估摘要
        eval_summary = assistant.evaluation_system.get_evaluation_summary()
        assert 'total_evaluations' in eval_summary
    
    def test_error_handling(self, assistant):
        """测试错误处理"""
        # 测试空请求
        response = assistant.handle_request("")
        assert response is not None
        
        # 测试异常长的请求
        long_request = "创建" * 1000
        response = assistant.handle_request(long_request)
        assert response is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])