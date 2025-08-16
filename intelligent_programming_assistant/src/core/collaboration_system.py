"""协作系统 - 多智能体协作编程"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import time

from ..utils.llm_client import LLMClient
from ..utils.config_loader import config
from ..utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class CollaborationResult:
    """协作结果"""
    code: str
    explanation: str
    roles_used: List[str]
    collaboration_log: List[Dict[str, Any]]
    consensus_reached: bool
    execution_time: float


class ProgrammingTeamSystem:
    """编程团队协作系统"""
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient()
        self.collaboration_config = config.get_collaboration_config()
        self.collaboration_history: List[Dict[str, Any]] = []
        
        # 可用角色
        self.available_roles = {
            'architect': self._software_architect_agent,
            'developer': self._developer_agent,
            'tester': self._tester_agent,
            'reviewer': self._code_reviewer_agent,
            'devops': self._devops_agent
        }
        
        # 配置参数
        self.max_agents = self.collaboration_config.get('max_agents', 5)
        self.consensus_threshold = self.collaboration_config.get('consensus_threshold', 0.6)
        self.communication_timeout = self.collaboration_config.get('communication_timeout', 30)
        
        logger.info("编程团队协作系统初始化完成")
    
    def collaborative_programming(
        self,
        request: str,
        reasoning_result: Any,
        context: Optional[Dict[str, Any]] = None,
        expert_guidance: Optional[Dict[str, Any]] = None
    ) -> CollaborationResult:
        """多角色协作编程"""
        start_time = time.time()
        
        logger.info(f"开始多角色协作编程: {request[:100]}...")
        
        try:
            # 1. 分析项目需求并分配角色
            role_assignments = self._assign_roles(request, reasoning_result)
            
            # 2. 执行协作阶段
            collaboration_log = []
            results = {}
            
            # 设计阶段
            if 'architect' in role_assignments:
                design_result = self._execute_role_task(
                    'architect', 'design', request, context, expert_guidance
                )
                results['design'] = design_result
                collaboration_log.append({
                    'phase': 'design',
                    'role': 'architect',
                    'result': design_result,
                    'timestamp': time.time()
                })
            
            # 开发阶段
            if 'developer' in role_assignments:
                dev_result = self._execute_role_task(
                    'developer', 'implementation', request, context, expert_guidance, results.get('design')
                )
                results['implementation'] = dev_result
                collaboration_log.append({
                    'phase': 'implementation',
                    'role': 'developer',
                    'result': dev_result,
                    'timestamp': time.time()
                })
            
            # 测试阶段
            if 'tester' in role_assignments:
                test_result = self._execute_role_task(
                    'tester', 'testing', request, context, expert_guidance, results.get('implementation')
                )
                results['testing'] = test_result
                collaboration_log.append({
                    'phase': 'testing',
                    'role': 'tester',
                    'result': test_result,
                    'timestamp': time.time()
                })
            
            # 代码审查阶段
            if 'reviewer' in role_assignments:
                review_result = self._execute_role_task(
                    'reviewer', 'review', request, context, expert_guidance, results.get('implementation')
                )
                results['review'] = review_result
                collaboration_log.append({
                    'phase': 'review',
                    'role': 'reviewer',
                    'result': review_result,
                    'timestamp': time.time()
                })
            
            # 部署阶段
            if 'devops' in role_assignments:
                deploy_result = self._execute_role_task(
                    'devops', 'deployment', request, context, expert_guidance, results.get('implementation')
                )
                results['deployment'] = deploy_result
                collaboration_log.append({
                    'phase': 'deployment',
                    'role': 'devops',
                    'result': deploy_result,
                    'timestamp': time.time()
                })
            
            # 3. 整合结果
            integrated_result = self._integrate_collaboration_results(results, request)
            
            # 4. 检查共识
            consensus_reached = self._check_consensus(results)
            
            # 5. 记录协作历史
            self.collaboration_history.append({
                'request': request,
                'roles_used': role_assignments,
                'results': results,
                'consensus_reached': consensus_reached,
                'execution_time': time.time() - start_time
            })
            
            result = CollaborationResult(
                code=integrated_result.get('code', ''),
                explanation=integrated_result.get('explanation', ''),
                roles_used=role_assignments,
                collaboration_log=collaboration_log,
                consensus_reached=consensus_reached,
                execution_time=time.time() - start_time
            )
            
            logger.info(f"协作完成 - 角色: {role_assignments}, 共识: {consensus_reached}")
            return result
            
        except Exception as e:
            logger.error(f"协作编程失败: {e}")
            return CollaborationResult(
                code="",
                explanation=f"协作编程失败: {e}",
                roles_used=[],
                collaboration_log=[],
                consensus_reached=False,
                execution_time=time.time() - start_time
            )
    
    def _assign_roles(self, request: str, reasoning_result: Any) -> List[str]:
        """分配角色"""
        assignment_prompt = f"""
        分析以下编程项目需求，确定需要哪些角色参与：
        
        项目需求: {request}
        复杂度评估: {reasoning_result.strategy if reasoning_result else '未知'}
        置信度: {reasoning_result.confidence if reasoning_result else 0.0}
        
        可用角色:
        - architect: 软件架构师，负责系统设计
        - developer: 开发者，负责代码实现
        - tester: 测试员，负责测试用例
        - reviewer: 代码审查员，负责代码质量
        - devops: 运维工程师，负责部署配置
        
        请根据项目需求选择合适的角色（最多{self.max_agents}个）。
        只回答角色名称，用逗号分隔。
        """
        
        try:
            response = self.llm.completion(assignment_prompt)
            response_text = self.llm.get_response_text(response).lower()
            
            # 解析角色
            assigned_roles = []
            for role in self.available_roles.keys():
                if role in response_text:
                    assigned_roles.append(role)
            
            # 确保至少有开发者角色
            if not assigned_roles:
                assigned_roles = ['developer']
            elif 'developer' not in assigned_roles:
                assigned_roles.append('developer')
            
            # 限制角色数量
            return assigned_roles[:self.max_agents]
            
        except Exception as e:
            logger.warning(f"角色分配失败，使用默认角色: {e}")
            return ['developer']
    
    def _execute_role_task(
        self,
        role: str,
        phase: str,
        request: str,
        context: Optional[Dict[str, Any]] = None,
        expert_guidance: Optional[Dict[str, Any]] = None,
        previous_result: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """执行角色任务"""
        logger.info(f"执行角色任务: {role} - {phase}")
        
        if role in self.available_roles:
            return self.available_roles[role](
                phase, request, context, expert_guidance, previous_result
            )
        else:
            return {
                'success': False,
                'output': f"未知角色: {role}",
                'role': role,
                'phase': phase
            }
    
    def _software_architect_agent(
        self,
        phase: str,
        request: str,
        context: Optional[Dict[str, Any]] = None,
        expert_guidance: Optional[Dict[str, Any]] = None,
        previous_result: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """软件架构师智能体"""
        prompt = f"""
        作为软件架构师，请为以下项目设计系统架构：
        
        项目需求: {request}
        上下文: {context or '无'}
        专家建议: {expert_guidance or '无'}
        前期结果: {previous_result or '无'}
        
        请提供：
        1. 系统架构设计
        2. 技术栈选择
        3. 模块划分
        4. 接口设计
        5. 数据流设计
        6. 部署架构
        
        请确保架构设计合理、可扩展、易维护。
        """
        
        try:
            response = self.llm.completion(prompt)
            response_text = self.llm.get_response_text(response)
            
            return {
                'success': True,
                'output': response_text,
                'role': 'architect',
                'phase': phase,
                'deliverables': {
                    'architecture_design': response_text,
                    'tech_stack': self._extract_tech_stack(response_text),
                    'modules': self._extract_modules(response_text)
                }
            }
        except Exception as e:
            return {
                'success': False,
                'output': f"架构设计失败: {e}",
                'role': 'architect',
                'phase': phase
            }
    
    def _developer_agent(
        self,
        phase: str,
        request: str,
        context: Optional[Dict[str, Any]] = None,
        expert_guidance: Optional[Dict[str, Any]] = None,
        previous_result: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """开发者智能体"""
        design_info = ""
        if previous_result and previous_result.get('deliverables', {}).get('architecture_design'):
            design_info = f"架构设计: {previous_result['deliverables']['architecture_design']}"
        
        prompt = f"""
        作为开发者，请实现以下项目：
        
        项目需求: {request}
        {design_info}
        上下文: {context or '无'}
        专家建议: {expert_guidance or '无'}
        
        请提供：
        1. 完整的代码实现
        2. 代码结构说明
        3. 关键功能实现
        4. 依赖管理
        5. 配置文件
        6. 使用说明
        
        请确保代码质量高、结构清晰、注释完整。
        """
        
        try:
            response = self.llm.completion(prompt)
            response_text = self.llm.get_response_text(response)
            
            # 提取代码
            code = self._extract_code_blocks(response_text)
            
            return {
                'success': True,
                'output': response_text,
                'role': 'developer',
                'phase': phase,
                'deliverables': {
                    'code': code,
                    'implementation_notes': response_text,
                    'dependencies': self._extract_dependencies(response_text)
                }
            }
        except Exception as e:
            return {
                'success': False,
                'output': f"代码实现失败: {e}",
                'role': 'developer',
                'phase': phase
            }
    
    def _tester_agent(
        self,
        phase: str,
        request: str,
        context: Optional[Dict[str, Any]] = None,
        expert_guidance: Optional[Dict[str, Any]] = None,
        previous_result: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """测试员智能体"""
        code_info = ""
        if previous_result and previous_result.get('deliverables', {}).get('code'):
            code_info = f"待测试代码: {previous_result['deliverables']['code'][:1000]}..."
        
        prompt = f"""
        作为测试员，请为以下项目设计和实现测试：
        
        项目需求: {request}
        {code_info}
        上下文: {context or '无'}
        
        请提供：
        1. 测试策略
        2. 单元测试代码
        3. 集成测试代码
        4. 测试用例设计
        5. 边界条件测试
        6. 性能测试建议
        7. 测试报告模板
        
        请确保测试覆盖全面、用例设计合理。
        """
        
        try:
            response = self.llm.completion(prompt)
            response_text = self.llm.get_response_text(response)
            
            # 提取测试代码
            test_code = self._extract_code_blocks(response_text)
            
            return {
                'success': True,
                'output': response_text,
                'role': 'tester',
                'phase': phase,
                'deliverables': {
                    'test_code': test_code,
                    'test_strategy': response_text,
                    'test_cases': self._extract_test_cases(response_text)
                }
            }
        except Exception as e:
            return {
                'success': False,
                'output': f"测试设计失败: {e}",
                'role': 'tester',
                'phase': phase
            }
    
    def _code_reviewer_agent(
        self,
        phase: str,
        request: str,
        context: Optional[Dict[str, Any]] = None,
        expert_guidance: Optional[Dict[str, Any]] = None,
        previous_result: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """代码审查员智能体"""
        code_info = ""
        if previous_result and previous_result.get('deliverables', {}).get('code'):
            code_info = f"待审查代码: {previous_result['deliverables']['code']}"
        
        prompt = f"""
        作为代码审查员，请审查以下代码：
        
        项目需求: {request}
        {code_info}
        
        请从以下方面进行审查：
        1. 代码质量评估
        2. 设计模式使用
        3. 性能优化建议
        4. 安全性检查
        5. 可维护性评估
        6. 代码规范检查
        7. 改进建议
        8. 总体评分（1-10）
        
        请提供详细的审查报告和改进建议。
        """
        
        try:
            response = self.llm.completion(prompt)
            response_text = self.llm.get_response_text(response)
            
            return {
                'success': True,
                'output': response_text,
                'role': 'reviewer',
                'phase': phase,
                'deliverables': {
                    'review_report': response_text,
                    'quality_score': self._extract_quality_score(response_text),
                    'improvement_suggestions': self._extract_improvements(response_text)
                }
            }
        except Exception as e:
            return {
                'success': False,
                'output': f"代码审查失败: {e}",
                'role': 'reviewer',
                'phase': phase
            }
    
    def _devops_agent(
        self,
        phase: str,
        request: str,
        context: Optional[Dict[str, Any]] = None,
        expert_guidance: Optional[Dict[str, Any]] = None,
        previous_result: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """DevOps工程师智能体"""
        code_info = ""
        if previous_result and previous_result.get('deliverables', {}).get('code'):
            code_info = f"待部署代码: {previous_result['deliverables']['code'][:500]}..."
        
        prompt = f"""
        作为DevOps工程师，请为以下项目设计部署方案：
        
        项目需求: {request}
        {code_info}
        上下文: {context or '无'}
        
        请提供：
        1. 部署架构设计
        2. Docker配置文件
        3. CI/CD流水线配置
        4. 监控和日志方案
        5. 备份和恢复策略
        6. 安全配置
        7. 性能优化配置
        8. 运维手册
        
        请确保部署方案稳定、可扩展、易维护。
        """
        
        try:
            response = self.llm.completion(prompt)
            response_text = self.llm.get_response_text(response)
            
            # 提取配置文件
            config_files = self._extract_config_files(response_text)
            
            return {
                'success': True,
                'output': response_text,
                'role': 'devops',
                'phase': phase,
                'deliverables': {
                    'deployment_plan': response_text,
                    'config_files': config_files,
                    'monitoring_setup': self._extract_monitoring_setup(response_text)
                }
            }
        except Exception as e:
            return {
                'success': False,
                'output': f"部署方案设计失败: {e}",
                'role': 'devops',
                'phase': phase
            }
    
    def _integrate_collaboration_results(self, results: Dict[str, Any], request: str) -> Dict[str, Any]:
        """整合协作结果"""
        integration_prompt = f"""
        请整合以下多角色协作的结果，生成最终的项目交付物：
        
        原始需求: {request}
        
        协作结果:
        {self._format_results_for_integration(results)}
        
        请提供：
        1. 最终的完整代码
        2. 项目说明文档
        3. 部署指南
        4. 使用手册
        5. 项目总结
        
        请确保整合结果完整、一致、可用。
        """
        
        try:
            response = self.llm.completion(integration_prompt)
            response_text = self.llm.get_response_text(response)
            
            # 提取最终代码
            final_code = self._extract_code_blocks(response_text)
            
            # 如果没有提取到代码，使用开发者的代码
            if not final_code and 'implementation' in results:
                final_code = results['implementation'].get('deliverables', {}).get('code', '')
            
            return {
                'code': final_code,
                'explanation': response_text,
                'integration_successful': True
            }
        except Exception as e:
            logger.error(f"结果整合失败: {e}")
            
            # 后备方案：直接使用开发者的结果
            if 'implementation' in results:
                dev_result = results['implementation']
                return {
                    'code': dev_result.get('deliverables', {}).get('code', ''),
                    'explanation': dev_result.get('output', ''),
                    'integration_successful': False
                }
            
            return {
                'code': '',
                'explanation': f'结果整合失败: {e}',
                'integration_successful': False
            }
    
    def _check_consensus(self, results: Dict[str, Any]) -> bool:
        """检查团队共识"""
        successful_results = sum(1 for result in results.values() if result.get('success', False))
        total_results = len(results)
        
        if total_results == 0:
            return False
        
        consensus_rate = successful_results / total_results
        return consensus_rate >= self.consensus_threshold
    
    def _format_results_for_integration(self, results: Dict[str, Any]) -> str:
        """格式化结果用于整合"""
        formatted = []
        for phase, result in results.items():
            formatted.append(f"{phase.upper()}阶段结果:")
            formatted.append(f"成功: {result.get('success', False)}")
            formatted.append(f"输出: {result.get('output', '')[:300]}...")
            formatted.append("")
        
        return "\n".join(formatted)
    
    def _extract_code_blocks(self, text: str) -> str:
        """提取代码块"""
        import re
        
        code_blocks = re.findall(r'```(?:\w+)?\n(.*?)\n```', text, re.DOTALL)
        return '\n\n'.join(code_blocks) if code_blocks else ''
    
    def _extract_tech_stack(self, text: str) -> List[str]:
        """提取技术栈"""
        tech_keywords = ['python', 'javascript', 'react', 'django', 'flask', 'fastapi', 'docker', 'kubernetes']
        found_tech = []
        text_lower = text.lower()
        
        for tech in tech_keywords:
            if tech in text_lower:
                found_tech.append(tech)
        
        return found_tech
    
    def _extract_modules(self, text: str) -> List[str]:
        """提取模块"""
        import re
        
        module_patterns = [
            r'模块[：:]\s*([^\n]+)',
            r'module[：:]\s*([^\n]+)',
            r'组件[：:]\s*([^\n]+)'
        ]
        
        modules = []
        for pattern in module_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            modules.extend(matches)
        
        return modules
    
    def _extract_dependencies(self, text: str) -> List[str]:
        """提取依赖"""
        import re
        
        # 查找requirements.txt或package.json中的依赖
        dep_patterns = [
            r'pip install\s+([^\n]+)',
            r'npm install\s+([^\n]+)',
            r'requirements\.txt.*?\n(.*?)(?=\n\n|\Z)',
            r'"dependencies".*?\{(.*?)\}'
        ]
        
        dependencies = []
        for pattern in dep_patterns:
            matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
            dependencies.extend(matches)
        
        return dependencies
    
    def _extract_test_cases(self, text: str) -> List[str]:
        """提取测试用例"""
        import re
        
        test_patterns = [
            r'test_\w+',
            r'测试用例[：:]\s*([^\n]+)',
            r'test case[：:]\s*([^\n]+)'
        ]
        
        test_cases = []
        for pattern in test_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            test_cases.extend(matches)
        
        return test_cases
    
    def _extract_quality_score(self, text: str) -> float:
        """提取质量评分"""
        import re
        
        score_patterns = [
            r'评分[：:]\s*([0-9.]+)',
            r'score[：:]\s*([0-9.]+)',
            r'质量[：:]\s*([0-9.]+)',
            r'([0-9.]+)\s*分'
        ]
        
        for pattern in score_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    continue
        
        return 7.0  # 默认评分
    
    def _extract_improvements(self, text: str) -> List[str]:
        """提取改进建议"""
        import re
        
        improvement_patterns = [
            r'建议[：:]\s*([^\n]+)',
            r'改进[：:]\s*([^\n]+)',
            r'suggestion[：:]\s*([^\n]+)',
            r'improvement[：:]\s*([^\n]+)'
        ]
        
        improvements = []
        for pattern in improvement_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            improvements.extend(matches)
        
        return improvements
    
    def _extract_config_files(self, text: str) -> Dict[str, str]:
        """提取配置文件"""
        import re
        
        config_files = {}
        
        # 查找Dockerfile
        dockerfile_match = re.search(r'dockerfile.*?\n(.*?)(?=\n\n|\Z)', text, re.DOTALL | re.IGNORECASE)
        if dockerfile_match:
            config_files['Dockerfile'] = dockerfile_match.group(1)
        
        # 查找docker-compose.yml
        compose_match = re.search(r'docker-compose.*?\n(.*?)(?=\n\n|\Z)', text, re.DOTALL | re.IGNORECASE)
        if compose_match:
            config_files['docker-compose.yml'] = compose_match.group(1)
        
        return config_files
    
    def _extract_monitoring_setup(self, text: str) -> Dict[str, str]:
        """提取监控配置"""
        monitoring = {}
        
        if '监控' in text or 'monitoring' in text.lower():
            monitoring['enabled'] = True
            monitoring['tools'] = []
            
            if 'prometheus' in text.lower():
                monitoring['tools'].append('prometheus')
            if 'grafana' in text.lower():
                monitoring['tools'].append('grafana')
            if 'elk' in text.lower() or 'elasticsearch' in text.lower():
                monitoring['tools'].append('elk')
        
        return monitoring