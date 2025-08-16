"""工具管理器 - 智能工具选择和执行"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import time

from ..utils.llm_client import LLMClient
from ..utils.config_loader import config
from ..utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ToolExecutionResult:
    """工具执行结果"""
    code: str
    explanation: str
    tools_used: List[str]
    execution_time: float
    success: bool
    error_message: Optional[str] = None


class ProgrammingToolManager:
    """编程工具管理器"""
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient()
        self.tools_config = config.get_tools_config()
        self.usage_history: List[Dict[str, Any]] = []
        
        # 可用工具列表
        self.available_tools = {
            'code_generator': self._code_generator_tool,
            'code_analyzer': self._code_analyzer_tool,
            'debugger': self._debugger_tool,
            'tester': self._tester_tool,
            'refactor': self._refactor_tool,
            'documentation': self._documentation_tool
        }
        
        logger.info("编程工具管理器初始化完成")
    
    def execute_programming_task(
        self, 
        request: str, 
        reasoning_result: Any, 
        context: Optional[Dict[str, Any]] = None,
        expert_guidance: Optional[Dict[str, Any]] = None
    ) -> ToolExecutionResult:
        """执行编程任务"""
        start_time = time.time()
        
        logger.info(f"开始执行编程任务: {request[:100]}...")
        
        try:
            # 1. 分析任务需求
            task_analysis = self._analyze_task_requirements(request, reasoning_result)
            
            # 2. 选择合适的工具
            selected_tools = self._select_tools(task_analysis, context)
            
            # 3. 执行工具链
            result = self._execute_tool_chain(selected_tools, request, context, expert_guidance)
            
            # 4. 记录使用历史
            self.usage_history.append({
                'request': request,
                'tools_used': selected_tools,
                'execution_time': time.time() - start_time,
                'success': result.success
            })
            
            result.execution_time = time.time() - start_time
            logger.info(f"任务执行完成 - 工具: {selected_tools}, 耗时: {result.execution_time:.2f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"工具执行失败: {e}")
            return ToolExecutionResult(
                code="",
                explanation=f"工具执行失败: {e}",
                tools_used=[],
                execution_time=time.time() - start_time,
                success=False,
                error_message=str(e)
            )
    
    def _analyze_task_requirements(self, request: str, reasoning_result: Any) -> Dict[str, Any]:
        """分析任务需求"""
        analysis_prompt = f"""
        分析以下编程任务的需求，确定需要使用哪些工具：
        
        任务: {request}
        推理结果: {reasoning_result.final_answer if reasoning_result else '无'}
        
        可用工具:
        - code_generator: 生成代码
        - code_analyzer: 分析代码
        - debugger: 调试代码
        - tester: 测试代码
        - refactor: 重构代码
        - documentation: 生成文档
        
        请回答：
        主要任务类型: [生成/分析/调试/测试/重构/文档]
        需要的工具: [工具列表]
        任务复杂度: [简单/中等/复杂]
        预估时间: [分钟]
        """
        
        try:
            response = self.llm.completion(analysis_prompt)
            analysis_text = self.llm.get_response_text(response)
            
            return {
                'analysis_text': analysis_text,
                'task_type': self._extract_task_type(analysis_text),
                'complexity': self._extract_complexity(analysis_text),
                'estimated_time': self._extract_estimated_time(analysis_text)
            }
        except Exception as e:
            logger.warning(f"任务分析失败: {e}")
            return {
                'analysis_text': '',
                'task_type': 'generation',
                'complexity': 'medium',
                'estimated_time': 5
            }
    
    def _select_tools(self, task_analysis: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> List[str]:
        """选择合适的工具"""
        task_type = task_analysis.get('task_type', 'generation')
        complexity = task_analysis.get('complexity', 'medium')
        
        # 基于任务类型选择工具
        tool_mapping = {
            'generation': ['code_generator'],
            'analysis': ['code_analyzer'],
            'debugging': ['debugger', 'code_analyzer'],
            'testing': ['tester', 'code_generator'],
            'refactoring': ['refactor', 'code_analyzer'],
            'documentation': ['documentation', 'code_analyzer']
        }
        
        selected_tools = tool_mapping.get(task_type, ['code_generator'])
        
        # 根据复杂度调整工具
        if complexity == 'complex':
            if 'code_analyzer' not in selected_tools:
                selected_tools.append('code_analyzer')
            if 'tester' not in selected_tools:
                selected_tools.append('tester')
        
        # 确保工具可用
        available_tools = self.tools_config.get('allowed_tools', list(self.available_tools.keys()))
        selected_tools = [tool for tool in selected_tools if tool in available_tools]
        
        return selected_tools or ['code_generator']
    
    def _execute_tool_chain(
        self, 
        tools: List[str], 
        request: str, 
        context: Optional[Dict[str, Any]] = None,
        expert_guidance: Optional[Dict[str, Any]] = None
    ) -> ToolExecutionResult:
        """执行工具链"""
        results = []
        all_code = ""
        all_explanations = []
        
        for tool_name in tools:
            if tool_name in self.available_tools:
                logger.info(f"执行工具: {tool_name}")
                
                tool_result = self.available_tools[tool_name](
                    request, context, expert_guidance, all_code
                )
                
                results.append(tool_result)
                
                if tool_result.get('code'):
                    all_code += tool_result['code'] + "\n\n"
                
                if tool_result.get('explanation'):
                    all_explanations.append(f"{tool_name}: {tool_result['explanation']}")
        
        return ToolExecutionResult(
            code=all_code.strip(),
            explanation="\n".join(all_explanations),
            tools_used=tools,
            execution_time=0.0,  # 将在上层设置
            success=len(results) > 0
        )
    
    def _code_generator_tool(
        self, 
        request: str, 
        context: Optional[Dict[str, Any]] = None,
        expert_guidance: Optional[Dict[str, Any]] = None,
        existing_code: str = ""
    ) -> Dict[str, Any]:
        """代码生成工具"""
        prompt = f"""
        请根据以下需求生成代码：
        
        需求: {request}
        上下文: {context or '无'}
        专家建议: {expert_guidance or '无'}
        现有代码: {existing_code or '无'}
        
        请提供：
        1. 完整的代码实现
        2. 代码说明
        3. 使用示例
        4. 注意事项
        
        请确保代码质量高、可读性强、有适当的注释。
        """
        
        try:
            response = self.llm.completion(prompt)
            response_text = self.llm.get_response_text(response)
            
            # 提取代码块
            code = self._extract_code_blocks(response_text)
            
            return {
                'code': code,
                'explanation': response_text,
                'tool': 'code_generator'
            }
        except Exception as e:
            return {
                'code': f"# 代码生成失败: {e}",
                'explanation': f"代码生成工具执行失败: {e}",
                'tool': 'code_generator'
            }
    
    def _code_analyzer_tool(
        self, 
        request: str, 
        context: Optional[Dict[str, Any]] = None,
        expert_guidance: Optional[Dict[str, Any]] = None,
        existing_code: str = ""
    ) -> Dict[str, Any]:
        """代码分析工具"""
        if not existing_code:
            return {
                'code': '',
                'explanation': '没有代码需要分析',
                'tool': 'code_analyzer'
            }
        
        prompt = f"""
        请分析以下代码：
        
        代码:
        {existing_code}
        
        请提供：
        1. 代码结构分析
        2. 潜在问题识别
        3. 性能评估
        4. 改进建议
        5. 代码质量评分（1-10）
        """
        
        try:
            response = self.llm.completion(prompt)
            response_text = self.llm.get_response_text(response)
            
            return {
                'code': '',
                'explanation': response_text,
                'tool': 'code_analyzer'
            }
        except Exception as e:
            return {
                'code': '',
                'explanation': f"代码分析失败: {e}",
                'tool': 'code_analyzer'
            }
    
    def _debugger_tool(
        self, 
        request: str, 
        context: Optional[Dict[str, Any]] = None,
        expert_guidance: Optional[Dict[str, Any]] = None,
        existing_code: str = ""
    ) -> Dict[str, Any]:
        """调试工具"""
        prompt = f"""
        请帮助调试以下问题：
        
        问题描述: {request}
        相关代码: {existing_code or '无'}
        上下文: {context or '无'}
        
        请提供：
        1. 问题诊断
        2. 可能的原因
        3. 解决方案
        4. 修复后的代码（如果适用）
        5. 预防措施
        """
        
        try:
            response = self.llm.completion(prompt)
            response_text = self.llm.get_response_text(response)
            
            # 提取修复后的代码
            fixed_code = self._extract_code_blocks(response_text)
            
            return {
                'code': fixed_code,
                'explanation': response_text,
                'tool': 'debugger'
            }
        except Exception as e:
            return {
                'code': '',
                'explanation': f"调试失败: {e}",
                'tool': 'debugger'
            }
    
    def _tester_tool(
        self, 
        request: str, 
        context: Optional[Dict[str, Any]] = None,
        expert_guidance: Optional[Dict[str, Any]] = None,
        existing_code: str = ""
    ) -> Dict[str, Any]:
        """测试工具"""
        prompt = f"""
        请为以下代码生成测试：
        
        代码:
        {existing_code or request}
        
        请提供：
        1. 单元测试代码
        2. 测试用例说明
        3. 边界条件测试
        4. 异常情况测试
        5. 测试运行说明
        """
        
        try:
            response = self.llm.completion(prompt)
            response_text = self.llm.get_response_text(response)
            
            # 提取测试代码
            test_code = self._extract_code_blocks(response_text)
            
            return {
                'code': test_code,
                'explanation': response_text,
                'tool': 'tester'
            }
        except Exception as e:
            return {
                'code': '',
                'explanation': f"测试生成失败: {e}",
                'tool': 'tester'
            }
    
    def _refactor_tool(
        self, 
        request: str, 
        context: Optional[Dict[str, Any]] = None,
        expert_guidance: Optional[Dict[str, Any]] = None,
        existing_code: str = ""
    ) -> Dict[str, Any]:
        """重构工具"""
        if not existing_code:
            return {
                'code': '',
                'explanation': '没有代码需要重构',
                'tool': 'refactor'
            }
        
        prompt = f"""
        请重构以下代码：
        
        原代码:
        {existing_code}
        
        重构目标: {request}
        
        请提供：
        1. 重构后的代码
        2. 重构说明
        3. 改进点说明
        4. 性能提升分析
        5. 重构前后对比
        """
        
        try:
            response = self.llm.completion(prompt)
            response_text = self.llm.get_response_text(response)
            
            # 提取重构后的代码
            refactored_code = self._extract_code_blocks(response_text)
            
            return {
                'code': refactored_code,
                'explanation': response_text,
                'tool': 'refactor'
            }
        except Exception as e:
            return {
                'code': existing_code,
                'explanation': f"重构失败: {e}",
                'tool': 'refactor'
            }
    
    def _documentation_tool(
        self, 
        request: str, 
        context: Optional[Dict[str, Any]] = None,
        expert_guidance: Optional[Dict[str, Any]] = None,
        existing_code: str = ""
    ) -> Dict[str, Any]:
        """文档生成工具"""
        prompt = f"""
        请为以下代码生成文档：
        
        代码:
        {existing_code or request}
        
        请提供：
        1. API文档
        2. 使用说明
        3. 参数说明
        4. 返回值说明
        5. 使用示例
        6. 注意事项
        """
        
        try:
            response = self.llm.completion(prompt)
            response_text = self.llm.get_response_text(response)
            
            return {
                'code': '',
                'explanation': response_text,
                'tool': 'documentation'
            }
        except Exception as e:
            return {
                'code': '',
                'explanation': f"文档生成失败: {e}",
                'tool': 'documentation'
            }
    
    def _extract_code_blocks(self, text: str) -> str:
        """从文本中提取代码块"""
        import re
        
        # 查找代码块
        code_blocks = re.findall(r'```(?:\w+)?\n(.*?)\n```', text, re.DOTALL)
        
        if code_blocks:
            return '\n\n'.join(code_blocks)
        
        # 如果没有找到代码块，查找缩进的代码
        lines = text.split('\n')
        code_lines = []
        in_code_section = False
        
        for line in lines:
            if line.strip().startswith('def ') or line.strip().startswith('class ') or line.strip().startswith('import '):
                in_code_section = True
            
            if in_code_section and (line.startswith('    ') or line.strip() == '' or line.strip().startswith('#')):
                code_lines.append(line)
            elif in_code_section and not line.startswith('    ') and line.strip():
                break
        
        return '\n'.join(code_lines) if code_lines else ''
    
    def _extract_task_type(self, text: str) -> str:
        """从分析文本中提取任务类型"""
        text_lower = text.lower()
        
        if '生成' in text or 'generation' in text_lower or '创建' in text:
            return 'generation'
        elif '分析' in text or 'analysis' in text_lower:
            return 'analysis'
        elif '调试' in text or 'debug' in text_lower:
            return 'debugging'
        elif '测试' in text or 'test' in text_lower:
            return 'testing'
        elif '重构' in text or 'refactor' in text_lower:
            return 'refactoring'
        elif '文档' in text or 'document' in text_lower:
            return 'documentation'
        else:
            return 'generation'
    
    def _extract_complexity(self, text: str) -> str:
        """从分析文本中提取复杂度"""
        text_lower = text.lower()
        
        if '复杂' in text or 'complex' in text_lower:
            return 'complex'
        elif '简单' in text or 'simple' in text_lower:
            return 'simple'
        else:
            return 'medium'
    
    def _extract_estimated_time(self, text: str) -> int:
        """从分析文本中提取预估时间"""
        import re
        
        # 查找时间模式
        time_patterns = [
            r'(\d+)\s*分钟',
            r'(\d+)\s*minutes?',
            r'预估时间[：:]\s*(\d+)',
            r'时间[：:]\s*(\d+)'
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    continue
        
        return 5  # 默认5分钟
    
    def get_usage_summary(self) -> Dict[str, Any]:
        """获取工具使用摘要"""
        if not self.usage_history:
            return {
                'total_executions': 0,
                'success_rate': 0.0,
                'average_execution_time': 0.0,
                'tool_usage_distribution': {},
                'most_used_tools': []
            }
        
        total_executions = len(self.usage_history)
        successful_executions = sum(1 for h in self.usage_history if h['success'])
        success_rate = successful_executions / total_executions
        
        total_time = sum(h['execution_time'] for h in self.usage_history)
        average_execution_time = total_time / total_executions
        
        # 工具使用分布
        tool_counts = {}
        for history in self.usage_history:
            for tool in history['tools_used']:
                tool_counts[tool] = tool_counts.get(tool, 0) + 1
        
        # 最常用工具
        most_used_tools = sorted(tool_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'total_executions': total_executions,
            'success_rate': success_rate,
            'average_execution_time': average_execution_time,
            'tool_usage_distribution': tool_counts,
            'most_used_tools': most_used_tools
        }