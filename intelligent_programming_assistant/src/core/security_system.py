"""安全系统 - 代码安全检查和防护"""

import re
import hashlib
from typing import Dict, List, Any, Optional

from ..utils.llm_client import LLMClient
from ..utils.config_loader import config
from ..utils.logger import get_logger

logger = get_logger(__name__)


class CodeSecuritySystem:
    """代码安全系统"""
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient()
        self.security_config = config.get_security_config()
        self.security_history: List[Dict[str, Any]] = []
        
        # 安全配置
        self.enable_security_checks = self.security_config.get('enable_security_checks', True)
        self.vulnerability_scanning = self.security_config.get('vulnerability_scanning', True)
        self.injection_detection = self.security_config.get('code_injection_detection', True)
        self.sensitive_data_detection = self.security_config.get('sensitive_data_detection', True)
        self.max_code_size = self.security_config.get('max_code_size', 100000)
        self.allowed_file_types = self.security_config.get('allowed_file_types', ['.py', '.js', '.java'])
        
        # 危险模式和关键词
        self.dangerous_patterns = [
            r'eval\s*\(',
            r'exec\s*\(',
            r'__import__\s*\(',
            r'subprocess\.',
            r'os\.system\s*\(',
            r'os\.popen\s*\(',
            r'shell=True',
            r'input\s*\(',
            r'raw_input\s*\(',
            r'open\s*\([^)]*["\']w["\']',
            r'pickle\.loads?\s*\(',
            r'yaml\.load\s*\(',
            r'sql.*drop\s+table',
            r'sql.*delete\s+from',
            r'sql.*update.*set',
            r'rm\s+-rf',
            r'sudo\s+',
            r'chmod\s+777'
        ]
        
        self.sensitive_patterns = [
            r'password\s*=\s*["\'][^"\']+["\']',
            r'api_key\s*=\s*["\'][^"\']+["\']',
            r'secret\s*=\s*["\'][^"\']+["\']',
            r'token\s*=\s*["\'][^"\']+["\']',
            r'private_key\s*=\s*["\'][^"\']+["\']',
            r'["\'][A-Za-z0-9]{32,}["\']',  # 可能的密钥
            r'["\'][A-Za-z0-9+/]{40,}={0,2}["\']'  # Base64编码的密钥
        ]
        
        logger.info("代码安全系统初始化完成")
    
    def validate_request(self, request: str, user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """验证请求安全性"""
        if not self.enable_security_checks:
            return {'is_safe': True, 'validation_skipped': True}
        
        logger.info("验证请求安全性")
        
        security_issues = []
        
        try:
            # 1. 检查请求长度
            if len(request) > self.max_code_size:
                security_issues.append({
                    'type': 'request_too_long',
                    'severity': 'medium',
                    'message': f'请求长度超过限制 ({len(request)} > {self.max_code_size})'
                })
            
            # 2. 检查注入攻击
            if self.injection_detection:
                injection_issues = self._detect_injection_attempts(request)
                security_issues.extend(injection_issues)
            
            # 3. 检查恶意关键词
            malicious_issues = self._detect_malicious_keywords(request)
            security_issues.extend(malicious_issues)
            
            # 4. 检查敏感信息
            if self.sensitive_data_detection:
                sensitive_issues = self._detect_sensitive_data(request)
                security_issues.extend(sensitive_issues)
            
            # 5. 用户上下文验证
            context_issues = self._validate_user_context(user_context)
            security_issues.extend(context_issues)
            
            # 判断是否安全
            high_severity_issues = [issue for issue in security_issues if issue.get('severity') == 'high']
            is_safe = len(high_severity_issues) == 0
            
            result = {
                'is_safe': is_safe,
                'security_issues': security_issues,
                'total_issues': len(security_issues),
                'high_severity_issues': len(high_severity_issues),
                'validation_timestamp': time.time()
            }
            
            # 记录安全检查历史
            self.security_history.append({
                'type': 'request_validation',
                'request_hash': hashlib.md5(request.encode()).hexdigest(),
                'result': result,
                'timestamp': time.time()
            })
            
            if not is_safe:
                logger.warning(f"请求安全验证失败 - 发现 {len(high_severity_issues)} 个高危问题")
            else:
                logger.info("请求安全验证通过")
            
            return result
            
        except Exception as e:
            logger.error(f"请求安全验证失败: {e}")
            return {
                'is_safe': False,
                'error': str(e),
                'validation_failed': True
            }
    
    def validate_code_output(self, code: str, user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """验证代码输出安全性"""
        if not self.enable_security_checks:
            return {'is_safe': True, 'validation_skipped': True}
        
        logger.info("验证代码输出安全性")
        
        security_issues = []
        
        try:
            # 1. 代码长度检查
            if len(code) > self.max_code_size:
                security_issues.append({
                    'type': 'code_too_long',
                    'severity': 'medium',
                    'message': f'代码长度超过限制 ({len(code)} > {self.max_code_size})'
                })
            
            # 2. 漏洞扫描
            if self.vulnerability_scanning:
                vulnerability_issues = self._scan_vulnerabilities(code)
                security_issues.extend(vulnerability_issues)
            
            # 3. 危险模式检测
            dangerous_issues = self._detect_dangerous_patterns(code)
            security_issues.extend(dangerous_issues)
            
            # 4. 敏感数据检测
            if self.sensitive_data_detection:
                sensitive_issues = self._detect_sensitive_data(code)
                security_issues.extend(sensitive_issues)
            
            # 5. 代码质量安全检查
            quality_issues = self._check_code_quality_security(code)
            security_issues.extend(quality_issues)
            
            # 6. 使用LLM进行深度安全分析
            llm_analysis = self._llm_security_analysis(code)
            if llm_analysis.get('issues'):
                security_issues.extend(llm_analysis['issues'])
            
            # 判断是否安全
            high_severity_issues = [issue for issue in security_issues if issue.get('severity') == 'high']
            is_safe = len(high_severity_issues) == 0
            
            result = {
                'is_safe': is_safe,
                'security_issues': security_issues,
                'total_issues': len(security_issues),
                'high_severity_issues': len(high_severity_issues),
                'medium_severity_issues': len([i for i in security_issues if i.get('severity') == 'medium']),
                'low_severity_issues': len([i for i in security_issues if i.get('severity') == 'low']),
                'llm_analysis': llm_analysis,
                'validation_timestamp': time.time(),
                'code_hash': hashlib.md5(code.encode()).hexdigest()
            }
            
            # 记录安全检查历史
            self.security_history.append({
                'type': 'code_validation',
                'code_hash': result['code_hash'],
                'result': result,
                'timestamp': time.time()
            })
            
            if not is_safe:
                logger.warning(f"代码安全验证失败 - 发现 {len(high_severity_issues)} 个高危问题")
            else:
                logger.info("代码安全验证通过")
            
            return result
            
        except Exception as e:
            logger.error(f"代码安全验证失败: {e}")
            return {
                'is_safe': False,
                'error': str(e),
                'validation_failed': True
            }
    
    def _detect_injection_attempts(self, text: str) -> List[Dict[str, Any]]:
        """检测注入攻击"""
        issues = []
        
        # SQL注入模式
        sql_injection_patterns = [
            r"'.*or.*'.*'",
            r'".*or.*".*"',
            r'union\s+select',
            r'drop\s+table',
            r'delete\s+from',
            r'insert\s+into',
            r'update\s+.*set',
            r'--.*',
            r'/\*.*\*/'
        ]
        
        for pattern in sql_injection_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                issues.append({
                    'type': 'sql_injection',
                    'severity': 'high',
                    'message': f'检测到可能的SQL注入攻击: {pattern}',
                    'pattern': pattern
                })
        
        # 命令注入模式
        command_injection_patterns = [
            r';\s*rm\s+',
            r';\s*cat\s+',
            r';\s*ls\s+',
            r';\s*pwd',
            r'`.*`',
            r'\$\(.*\)',
            r'&&\s*rm',
            r'\|\s*rm'
        ]
        
        for pattern in command_injection_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                issues.append({
                    'type': 'command_injection',
                    'severity': 'high',
                    'message': f'检测到可能的命令注入攻击: {pattern}',
                    'pattern': pattern
                })
        
        return issues
    
    def _detect_malicious_keywords(self, text: str) -> List[Dict[str, Any]]:
        """检测恶意关键词"""
        issues = []
        
        malicious_keywords = [
            'virus', 'malware', 'trojan', 'backdoor', 'rootkit',
            'keylogger', 'spyware', 'ransomware', 'botnet',
            'exploit', 'payload', 'shellcode', 'reverse_shell',
            'privilege_escalation', 'buffer_overflow'
        ]
        
        text_lower = text.lower()
        for keyword in malicious_keywords:
            if keyword in text_lower:
                issues.append({
                    'type': 'malicious_keyword',
                    'severity': 'medium',
                    'message': f'检测到可疑关键词: {keyword}',
                    'keyword': keyword
                })
        
        return issues
    
    def _detect_sensitive_data(self, text: str) -> List[Dict[str, Any]]:
        """检测敏感数据"""
        issues = []
        
        for pattern in self.sensitive_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                issues.append({
                    'type': 'sensitive_data',
                    'severity': 'medium',
                    'message': '检测到可能的敏感信息（密码、密钥等）',
                    'pattern': pattern,
                    'location': match.span()
                })
        
        return issues
    
    def _validate_user_context(self, user_context: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """验证用户上下文"""
        issues = []
        
        if not user_context:
            return issues
        
        # 检查权限级别
        security_requirements = user_context.get('security_requirements', 'medium')
        if security_requirements == 'high':
            # 高安全要求下的额外检查
            issues.append({
                'type': 'high_security_mode',
                'severity': 'info',
                'message': '当前处于高安全模式，将进行额外的安全检查'
            })
        
        return issues
    
    def _scan_vulnerabilities(self, code: str) -> List[Dict[str, Any]]:
        """扫描代码漏洞"""
        issues = []
        
        for pattern in self.dangerous_patterns:
            matches = re.finditer(pattern, code, re.IGNORECASE)
            for match in matches:
                issues.append({
                    'type': 'vulnerability',
                    'severity': 'high',
                    'message': f'检测到潜在的安全漏洞: {pattern}',
                    'pattern': pattern,
                    'location': match.span(),
                    'code_snippet': code[max(0, match.start()-20):match.end()+20]
                })
        
        return issues
    
    def _detect_dangerous_patterns(self, code: str) -> List[Dict[str, Any]]:
        """检测危险模式"""
        issues = []
        
        # 文件操作危险模式
        file_patterns = [
            r'open\s*\([^)]*["\']w["\'][^)]*\)',
            r'open\s*\([^)]*["\']a["\'][^)]*\)',
            r'with\s+open\s*\([^)]*["\']w["\']',
            r'file\s*\([^)]*["\']w["\']'
        ]
        
        for pattern in file_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                issues.append({
                    'type': 'dangerous_file_operation',
                    'severity': 'medium',
                    'message': f'检测到潜在危险的文件操作: {pattern}',
                    'pattern': pattern
                })
        
        # 网络操作危险模式
        network_patterns = [
            r'socket\.',
            r'urllib\.request',
            r'requests\.',
            r'http\.client',
            r'ftplib\.',
            r'smtplib\.'
        ]
        
        for pattern in network_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                issues.append({
                    'type': 'network_operation',
                    'severity': 'low',
                    'message': f'检测到网络操作，请确保安全: {pattern}',
                    'pattern': pattern
                })
        
        return issues
    
    def _check_code_quality_security(self, code: str) -> List[Dict[str, Any]]:
        """检查代码质量相关的安全问题"""
        issues = []
        
        # 检查硬编码密码
        hardcoded_patterns = [
            r'password\s*=\s*["\'][^"\']{1,50}["\']',
            r'pwd\s*=\s*["\'][^"\']{1,50}["\']',
            r'secret\s*=\s*["\'][^"\']{1,50}["\']'
        ]
        
        for pattern in hardcoded_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                issues.append({
                    'type': 'hardcoded_credentials',
                    'severity': 'high',
                    'message': '检测到硬编码的凭据，存在安全风险',
                    'pattern': pattern
                })
        
        # 检查不安全的随机数生成
        if re.search(r'random\.random\(\)', code):
            issues.append({
                'type': 'weak_random',
                'severity': 'medium',
                'message': '使用了不安全的随机数生成器，建议使用secrets模块'
            })
        
        # 检查不安全的哈希算法
        weak_hash_patterns = [
            r'hashlib\.md5\(',
            r'hashlib\.sha1\('
        ]
        
        for pattern in weak_hash_patterns:
            if re.search(pattern, code):
                issues.append({
                    'type': 'weak_hash',
                    'severity': 'medium',
                    'message': f'使用了不安全的哈希算法: {pattern}',
                    'pattern': pattern
                })
        
        return issues
    
    def _llm_security_analysis(self, code: str) -> Dict[str, Any]:
        """使用LLM进行深度安全分析"""
        if len(code) > 5000:  # 限制代码长度以避免过长的提示
            code = code[:5000] + "... (代码已截断)"
        
        analysis_prompt = f"""
        请对以下代码进行安全分析，识别潜在的安全问题：
        
        代码:
        {code}
        
        请检查：
        1. 输入验证问题
        2. 输出编码问题
        3. 认证和授权问题
        4. 会话管理问题
        5. 加密问题
        6. 错误处理问题
        7. 日志记录问题
        8. 配置安全问题
        
        请以JSON格式返回分析结果：
        {{
            "overall_security_score": 0-10,
            "issues": [
                {{
                    "type": "issue_type",
                    "severity": "low/medium/high",
                    "message": "问题描述",
                    "recommendation": "修复建议"
                }}
            ],
            "recommendations": ["总体建议1", "总体建议2"]
        }}
        """
        
        try:
            response = self.llm.completion(analysis_prompt)
            analysis_text = self.llm.get_response_text(response)
            
            # 尝试解析JSON响应
            import json
            try:
                analysis_result = json.loads(analysis_text)
                return analysis_result
            except json.JSONDecodeError:
                # 如果JSON解析失败，返回文本分析
                return {
                    'overall_security_score': 7,
                    'issues': [],
                    'recommendations': [analysis_text],
                    'analysis_text': analysis_text
                }
        
        except Exception as e:
            logger.warning(f"LLM安全分析失败: {e}")
            return {
                'overall_security_score': 5,
                'issues': [],
                'recommendations': [],
                'error': str(e)
            }
    
    def get_security_summary(self) -> Dict[str, Any]:
        """获取安全系统摘要"""
        if not self.security_history:
            return {
                'total_checks': 0,
                'safe_requests': 0,
                'unsafe_requests': 0,
                'common_issues': [],
                'security_enabled': self.enable_security_checks
            }
        
        total_checks = len(self.security_history)
        safe_checks = sum(1 for h in self.security_history if h['result'].get('is_safe', False))
        unsafe_checks = total_checks - safe_checks
        
        # 统计常见问题
        issue_counts = {}
        for history in self.security_history:
            for issue in history['result'].get('security_issues', []):
                issue_type = issue.get('type', 'unknown')
                issue_counts[issue_type] = issue_counts.get(issue_type, 0) + 1
        
        common_issues = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'total_checks': total_checks,
            'safe_requests': safe_checks,
            'unsafe_requests': unsafe_checks,
            'safety_rate': safe_checks / total_checks if total_checks > 0 else 0.0,
            'common_issues': common_issues,
            'security_enabled': self.enable_security_checks,
            'vulnerability_scanning_enabled': self.vulnerability_scanning,
            'injection_detection_enabled': self.injection_detection,
            'sensitive_data_detection_enabled': self.sensitive_data_detection
        }


import time  # 添加缺失的导入