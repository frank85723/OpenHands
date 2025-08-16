"""领域专家系统 - 特定技术栈的专业知识"""

from typing import Dict, List, Any, Optional
import time

from ..utils.llm_client import LLMClient
from ..utils.config_loader import config
from ..utils.logger import get_logger

logger = get_logger(__name__)


class TechStackExperts:
    """技术栈专家系统"""
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient()
        self.domain_config = config.get_domain_experts_config()
        self.consultation_history: List[Dict[str, Any]] = []
        
        # 可用的领域专家
        self.experts = {
            'python': self._python_expert,
            'javascript': self._javascript_expert,
            'java': self._java_expert,
            'react': self._react_expert,
            'django': self._django_expert,
            'fastapi': self._fastapi_expert,
            'docker': self._docker_expert,
            'aws': self._aws_expert,
            'database': self._database_expert,
            'security': self._security_expert
        }
        
        # 启用的领域
        self.enabled_domains = self.domain_config.get('enabled_domains', list(self.experts.keys()))
        
        logger.info("技术栈专家系统初始化完成")
    
    def get_expert_guidance(
        self, 
        request: str, 
        user_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """获取专家指导"""
        logger.info(f"获取专家指导: {request[:100]}...")
        
        try:
            # 1. 识别相关技术栈
            relevant_techs = self._identify_relevant_technologies(request, user_context)
            
            # 2. 获取专家建议
            expert_advice = {}
            for tech in relevant_techs:
                if tech in self.experts and tech in self.enabled_domains:
                    logger.info(f"咨询 {tech} 专家")
                    advice = self.experts[tech](request, user_context)
                    expert_advice[tech] = advice
            
            # 3. 整合专家建议
            integrated_guidance = self._integrate_expert_advice(expert_advice, request)
            
            # 4. 记录咨询历史
            self.consultation_history.append({
                'request': request,
                'relevant_technologies': relevant_techs,
                'expert_advice': expert_advice,
                'integrated_guidance': integrated_guidance,
                'timestamp': time.time()
            })
            
            result = {
                'relevant_technologies': relevant_techs,
                'expert_advice': expert_advice,
                'integrated_guidance': integrated_guidance,
                'consultation_successful': len(expert_advice) > 0
            }
            
            logger.info(f"专家咨询完成 - 涉及技术: {relevant_techs}")
            return result
            
        except Exception as e:
            logger.error(f"专家咨询失败: {e}")
            return {
                'relevant_technologies': [],
                'expert_advice': {},
                'integrated_guidance': f'专家咨询失败: {e}',
                'consultation_successful': False,
                'error': str(e)
            }
    
    def _identify_relevant_technologies(
        self, 
        request: str, 
        user_context: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """识别相关技术栈"""
        identification_prompt = f"""
        分析以下编程请求，识别涉及的技术栈：
        
        请求: {request}
        用户上下文: {user_context or '无'}
        
        可用技术栈:
        - python: Python编程语言
        - javascript: JavaScript编程语言
        - java: Java编程语言
        - react: React前端框架
        - django: Django Web框架
        - fastapi: FastAPI Web框架
        - docker: Docker容器化
        - aws: AWS云服务
        - database: 数据库相关
        - security: 安全相关
        
        请只返回相关的技术栈名称，用逗号分隔。
        """
        
        try:
            response = self.llm.completion(identification_prompt)
            response_text = self.llm.get_response_text(response).lower()
            
            # 解析技术栈
            identified_techs = []
            for tech in self.experts.keys():
                if tech in response_text:
                    identified_techs.append(tech)
            
            # 如果没有识别到技术栈，使用关键词匹配
            if not identified_techs:
                identified_techs = self._keyword_based_identification(request)
            
            return identified_techs
            
        except Exception as e:
            logger.warning(f"技术栈识别失败，使用关键词匹配: {e}")
            return self._keyword_based_identification(request)
    
    def _keyword_based_identification(self, request: str) -> List[str]:
        """基于关键词的技术栈识别"""
        request_lower = request.lower()
        identified_techs = []
        
        tech_keywords = {
            'python': ['python', 'py', 'django', 'flask', 'fastapi', 'pandas', 'numpy'],
            'javascript': ['javascript', 'js', 'node', 'npm', 'react', 'vue', 'angular'],
            'java': ['java', 'spring', 'maven', 'gradle', 'jvm'],
            'react': ['react', 'jsx', 'component', 'hook', 'state'],
            'django': ['django', 'drf', 'orm', 'model', 'view'],
            'fastapi': ['fastapi', 'pydantic', 'uvicorn', 'async'],
            'docker': ['docker', 'container', 'dockerfile', 'image'],
            'aws': ['aws', 'ec2', 's3', 'lambda', 'rds', 'cloudformation'],
            'database': ['database', 'sql', 'mysql', 'postgresql', 'mongodb', 'redis'],
            'security': ['security', 'auth', 'jwt', 'oauth', 'encryption', 'hash']
        }
        
        for tech, keywords in tech_keywords.items():
            if any(keyword in request_lower for keyword in keywords):
                identified_techs.append(tech)
        
        return identified_techs
    
    def _python_expert(self, request: str, user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Python专家"""
        expert_prompt = f"""
        作为Python专家，请为以下需求提供专业建议：
        
        需求: {request}
        用户上下文: {user_context or '无'}
        
        请提供：
        1. Python最佳实践建议
        2. 推荐的库和框架
        3. 代码结构建议
        4. 性能优化建议
        5. 常见陷阱和注意事项
        6. 示例代码片段
        
        请确保建议符合Python的PEP规范和最佳实践。
        """
        
        try:
            response = self.llm.completion(expert_prompt)
            advice_text = self.llm.get_response_text(response)
            
            return {
                'expert': 'python',
                'advice': advice_text,
                'recommendations': self._extract_recommendations(advice_text),
                'best_practices': self._extract_best_practices(advice_text),
                'libraries': self._extract_libraries(advice_text),
                'success': True
            }
        except Exception as e:
            return {
                'expert': 'python',
                'advice': f'Python专家咨询失败: {e}',
                'success': False,
                'error': str(e)
            }
    
    def _javascript_expert(self, request: str, user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """JavaScript专家"""
        expert_prompt = f"""
        作为JavaScript专家，请为以下需求提供专业建议：
        
        需求: {request}
        用户上下文: {user_context or '无'}
        
        请提供：
        1. JavaScript/ES6+最佳实践
        2. 推荐的框架和库
        3. 代码组织建议
        4. 性能优化技巧
        5. 浏览器兼容性考虑
        6. 异步编程建议
        7. 示例代码
        
        请确保建议符合现代JavaScript开发标准。
        """
        
        try:
            response = self.llm.completion(expert_prompt)
            advice_text = self.llm.get_response_text(response)
            
            return {
                'expert': 'javascript',
                'advice': advice_text,
                'frameworks': self._extract_frameworks(advice_text),
                'best_practices': self._extract_best_practices(advice_text),
                'performance_tips': self._extract_performance_tips(advice_text),
                'success': True
            }
        except Exception as e:
            return {
                'expert': 'javascript',
                'advice': f'JavaScript专家咨询失败: {e}',
                'success': False,
                'error': str(e)
            }
    
    def _java_expert(self, request: str, user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Java专家"""
        expert_prompt = f"""
        作为Java专家，请为以下需求提供专业建议：
        
        需求: {request}
        用户上下文: {user_context or '无'}
        
        请提供：
        1. Java最佳实践和设计模式
        2. 推荐的框架（Spring, Hibernate等）
        3. 项目结构建议
        4. 性能优化策略
        5. 内存管理建议
        6. 并发编程建议
        7. 示例代码
        
        请确保建议符合Java企业级开发标准。
        """
        
        try:
            response = self.llm.completion(expert_prompt)
            advice_text = self.llm.get_response_text(response)
            
            return {
                'expert': 'java',
                'advice': advice_text,
                'design_patterns': self._extract_design_patterns(advice_text),
                'frameworks': self._extract_frameworks(advice_text),
                'performance_tips': self._extract_performance_tips(advice_text),
                'success': True
            }
        except Exception as e:
            return {
                'expert': 'java',
                'advice': f'Java专家咨询失败: {e}',
                'success': False,
                'error': str(e)
            }
    
    def _react_expert(self, request: str, user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """React专家"""
        expert_prompt = f"""
        作为React专家，请为以下需求提供专业建议：
        
        需求: {request}
        用户上下文: {user_context or '无'}
        
        请提供：
        1. React最佳实践和模式
        2. 组件设计建议
        3. 状态管理策略
        4. 性能优化技巧
        5. Hook使用建议
        6. 测试策略
        7. 示例代码
        
        请确保建议符合React现代开发标准。
        """
        
        try:
            response = self.llm.completion(expert_prompt)
            advice_text = self.llm.get_response_text(response)
            
            return {
                'expert': 'react',
                'advice': advice_text,
                'component_patterns': self._extract_component_patterns(advice_text),
                'state_management': self._extract_state_management(advice_text),
                'hooks': self._extract_hooks(advice_text),
                'success': True
            }
        except Exception as e:
            return {
                'expert': 'react',
                'advice': f'React专家咨询失败: {e}',
                'success': False,
                'error': str(e)
            }
    
    def _django_expert(self, request: str, user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Django专家"""
        expert_prompt = f"""
        作为Django专家，请为以下需求提供专业建议：
        
        需求: {request}
        用户上下文: {user_context or '无'}
        
        请提供：
        1. Django最佳实践
        2. 模型设计建议
        3. 视图和URL配置
        4. 模板使用建议
        5. 安全配置
        6. 性能优化
        7. 示例代码
        
        请确保建议符合Django开发最佳实践。
        """
        
        try:
            response = self.llm.completion(expert_prompt)
            advice_text = self.llm.get_response_text(response)
            
            return {
                'expert': 'django',
                'advice': advice_text,
                'model_design': self._extract_model_design(advice_text),
                'security_tips': self._extract_security_tips(advice_text),
                'performance_tips': self._extract_performance_tips(advice_text),
                'success': True
            }
        except Exception as e:
            return {
                'expert': 'django',
                'advice': f'Django专家咨询失败: {e}',
                'success': False,
                'error': str(e)
            }
    
    def _fastapi_expert(self, request: str, user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """FastAPI专家"""
        expert_prompt = f"""
        作为FastAPI专家，请为以下需求提供专业建议：
        
        需求: {request}
        用户上下文: {user_context or '无'}
        
        请提供：
        1. FastAPI最佳实践
        2. API设计建议
        3. 数据验证和序列化
        4. 异步编程建议
        5. 认证和授权
        6. 性能优化
        7. 示例代码
        
        请确保建议符合FastAPI现代API开发标准。
        """
        
        try:
            response = self.llm.completion(expert_prompt)
            advice_text = self.llm.get_response_text(response)
            
            return {
                'expert': 'fastapi',
                'advice': advice_text,
                'api_design': self._extract_api_design(advice_text),
                'async_patterns': self._extract_async_patterns(advice_text),
                'validation': self._extract_validation(advice_text),
                'success': True
            }
        except Exception as e:
            return {
                'expert': 'fastapi',
                'advice': f'FastAPI专家咨询失败: {e}',
                'success': False,
                'error': str(e)
            }
    
    def _docker_expert(self, request: str, user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Docker专家"""
        expert_prompt = f"""
        作为Docker专家，请为以下需求提供专业建议：
        
        需求: {request}
        用户上下文: {user_context or '无'}
        
        请提供：
        1. Docker最佳实践
        2. Dockerfile优化建议
        3. 容器编排策略
        4. 安全配置
        5. 性能优化
        6. 监控和日志
        7. 示例配置
        
        请确保建议符合Docker生产环境标准。
        """
        
        try:
            response = self.llm.completion(expert_prompt)
            advice_text = self.llm.get_response_text(response)
            
            return {
                'expert': 'docker',
                'advice': advice_text,
                'dockerfile_tips': self._extract_dockerfile_tips(advice_text),
                'security_tips': self._extract_security_tips(advice_text),
                'orchestration': self._extract_orchestration(advice_text),
                'success': True
            }
        except Exception as e:
            return {
                'expert': 'docker',
                'advice': f'Docker专家咨询失败: {e}',
                'success': False,
                'error': str(e)
            }
    
    def _aws_expert(self, request: str, user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """AWS专家"""
        expert_prompt = f"""
        作为AWS专家，请为以下需求提供专业建议：
        
        需求: {request}
        用户上下文: {user_context or '无'}
        
        请提供：
        1. AWS服务选择建议
        2. 架构设计建议
        3. 成本优化策略
        4. 安全配置
        5. 监控和告警
        6. 自动化部署
        7. 示例配置
        
        请确保建议符合AWS Well-Architected Framework。
        """
        
        try:
            response = self.llm.completion(expert_prompt)
            advice_text = self.llm.get_response_text(response)
            
            return {
                'expert': 'aws',
                'advice': advice_text,
                'services': self._extract_aws_services(advice_text),
                'architecture': self._extract_architecture(advice_text),
                'cost_optimization': self._extract_cost_optimization(advice_text),
                'success': True
            }
        except Exception as e:
            return {
                'expert': 'aws',
                'advice': f'AWS专家咨询失败: {e}',
                'success': False,
                'error': str(e)
            }
    
    def _database_expert(self, request: str, user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """数据库专家"""
        expert_prompt = f"""
        作为数据库专家，请为以下需求提供专业建议：
        
        需求: {request}
        用户上下文: {user_context or '无'}
        
        请提供：
        1. 数据库选择建议
        2. 数据模型设计
        3. 索引优化策略
        4. 查询优化建议
        5. 备份和恢复策略
        6. 安全配置
        7. 示例SQL/查询
        
        请确保建议符合数据库设计最佳实践。
        """
        
        try:
            response = self.llm.completion(expert_prompt)
            advice_text = self.llm.get_response_text(response)
            
            return {
                'expert': 'database',
                'advice': advice_text,
                'database_choice': self._extract_database_choice(advice_text),
                'schema_design': self._extract_schema_design(advice_text),
                'optimization': self._extract_optimization(advice_text),
                'success': True
            }
        except Exception as e:
            return {
                'expert': 'database',
                'advice': f'数据库专家咨询失败: {e}',
                'success': False,
                'error': str(e)
            }
    
    def _security_expert(self, request: str, user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """安全专家"""
        expert_prompt = f"""
        作为安全专家，请为以下需求提供专业建议：
        
        需求: {request}
        用户上下文: {user_context or '无'}
        
        请提供：
        1. 安全威胁分析
        2. 安全架构建议
        3. 认证和授权策略
        4. 数据保护措施
        5. 安全测试建议
        6. 合规性考虑
        7. 安全配置示例
        
        请确保建议符合信息安全最佳实践。
        """
        
        try:
            response = self.llm.completion(expert_prompt)
            advice_text = self.llm.get_response_text(response)
            
            return {
                'expert': 'security',
                'advice': advice_text,
                'threat_analysis': self._extract_threat_analysis(advice_text),
                'security_measures': self._extract_security_measures(advice_text),
                'compliance': self._extract_compliance(advice_text),
                'success': True
            }
        except Exception as e:
            return {
                'expert': 'security',
                'advice': f'安全专家咨询失败: {e}',
                'success': False,
                'error': str(e)
            }
    
    def _integrate_expert_advice(self, expert_advice: Dict[str, Any], request: str) -> str:
        """整合专家建议"""
        if not expert_advice:
            return "没有获得专家建议"
        
        integration_prompt = f"""
        请整合以下多位专家的建议，为用户提供综合性的指导：
        
        原始需求: {request}
        
        专家建议:
        {self._format_expert_advice(expert_advice)}
        
        请提供：
        1. 综合建议摘要
        2. 关键技术选择
        3. 实施优先级
        4. 潜在风险和注意事项
        5. 下一步行动建议
        
        请确保建议一致、可行、完整。
        """
        
        try:
            response = self.llm.completion(integration_prompt)
            return self.llm.get_response_text(response)
        except Exception as e:
            # 后备方案：简单拼接专家建议
            integrated = "专家建议整合:\n\n"
            for expert, advice in expert_advice.items():
                integrated += f"{expert.upper()}专家建议:\n{advice.get('advice', '')}\n\n"
            return integrated
    
    def _format_expert_advice(self, expert_advice: Dict[str, Any]) -> str:
        """格式化专家建议"""
        formatted = []
        for expert, advice in expert_advice.items():
            formatted.append(f"{expert.upper()}专家:")
            formatted.append(advice.get('advice', '无建议'))
            formatted.append("")
        return "\n".join(formatted)
    
    # 提取方法（简化实现）
    def _extract_recommendations(self, text: str) -> List[str]:
        """提取建议"""
        import re
        patterns = [r'建议[：:]\s*([^\n]+)', r'推荐[：:]\s*([^\n]+)', r'recommendation[：:]\s*([^\n]+)']
        recommendations = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            recommendations.extend(matches)
        return recommendations
    
    def _extract_best_practices(self, text: str) -> List[str]:
        """提取最佳实践"""
        import re
        patterns = [r'最佳实践[：:]\s*([^\n]+)', r'best practice[：:]\s*([^\n]+)']
        practices = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            practices.extend(matches)
        return practices
    
    def _extract_libraries(self, text: str) -> List[str]:
        """提取库和框架"""
        import re
        patterns = [r'库[：:]\s*([^\n]+)', r'框架[：:]\s*([^\n]+)', r'library[：:]\s*([^\n]+)', r'framework[：:]\s*([^\n]+)']
        libraries = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            libraries.extend(matches)
        return libraries
    
    def _extract_frameworks(self, text: str) -> List[str]:
        """提取框架"""
        return self._extract_libraries(text)
    
    def _extract_performance_tips(self, text: str) -> List[str]:
        """提取性能优化建议"""
        import re
        patterns = [r'性能[：:]\s*([^\n]+)', r'优化[：:]\s*([^\n]+)', r'performance[：:]\s*([^\n]+)']
        tips = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            tips.extend(matches)
        return tips
    
    def _extract_design_patterns(self, text: str) -> List[str]:
        """提取设计模式"""
        import re
        patterns = [r'设计模式[：:]\s*([^\n]+)', r'pattern[：:]\s*([^\n]+)']
        patterns_found = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            patterns_found.extend(matches)
        return patterns_found
    
    # 其他提取方法的简化实现
    def _extract_component_patterns(self, text: str) -> List[str]:
        return self._extract_recommendations(text)
    
    def _extract_state_management(self, text: str) -> List[str]:
        return self._extract_recommendations(text)
    
    def _extract_hooks(self, text: str) -> List[str]:
        return self._extract_recommendations(text)
    
    def _extract_model_design(self, text: str) -> List[str]:
        return self._extract_recommendations(text)
    
    def _extract_security_tips(self, text: str) -> List[str]:
        return self._extract_recommendations(text)
    
    def _extract_api_design(self, text: str) -> List[str]:
        return self._extract_recommendations(text)
    
    def _extract_async_patterns(self, text: str) -> List[str]:
        return self._extract_recommendations(text)
    
    def _extract_validation(self, text: str) -> List[str]:
        return self._extract_recommendations(text)
    
    def _extract_dockerfile_tips(self, text: str) -> List[str]:
        return self._extract_recommendations(text)
    
    def _extract_orchestration(self, text: str) -> List[str]:
        return self._extract_recommendations(text)
    
    def _extract_aws_services(self, text: str) -> List[str]:
        return self._extract_recommendations(text)
    
    def _extract_architecture(self, text: str) -> List[str]:
        return self._extract_recommendations(text)
    
    def _extract_cost_optimization(self, text: str) -> List[str]:
        return self._extract_recommendations(text)
    
    def _extract_database_choice(self, text: str) -> List[str]:
        return self._extract_recommendations(text)
    
    def _extract_schema_design(self, text: str) -> List[str]:
        return self._extract_recommendations(text)
    
    def _extract_optimization(self, text: str) -> List[str]:
        return self._extract_recommendations(text)
    
    def _extract_threat_analysis(self, text: str) -> List[str]:
        return self._extract_recommendations(text)
    
    def _extract_security_measures(self, text: str) -> List[str]:
        return self._extract_recommendations(text)
    
    def _extract_compliance(self, text: str) -> List[str]:
        return self._extract_recommendations(text)