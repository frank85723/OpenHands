"""配置加载器"""

import os
import yaml
from typing import Dict, Any
from pathlib import Path


class ConfigLoader:
    """配置文件加载器"""
    
    def __init__(self, config_path: str = None):
        if config_path is None:
            # 默认配置文件路径
            config_path = Path(__file__).parent.parent.parent / "config" / "config.yaml"
        
        self.config_path = Path(config_path)
        self._config = None
    
    def load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        if self._config is not None:
            return self._config
        
        if not self.config_path.exists():
            # 如果配置文件不存在，尝试加载示例配置
            example_config_path = self.config_path.parent / "config.example.yaml"
            if example_config_path.exists():
                print(f"配置文件不存在，使用示例配置: {example_config_path}")
                self.config_path = example_config_path
            else:
                raise FileNotFoundError(f"配置文件不存在: {self.config_path}")
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f)
            
            # 处理环境变量替换
            self._process_env_variables()
            
            return self._config
        
        except Exception as e:
            raise RuntimeError(f"加载配置文件失败: {e}")
    
    def _process_env_variables(self):
        """处理环境变量替换"""
        def replace_env_vars(obj):
            if isinstance(obj, dict):
                return {k: replace_env_vars(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [replace_env_vars(item) for item in obj]
            elif isinstance(obj, str) and obj.startswith("${") and obj.endswith("}"):
                # 环境变量格式: ${ENV_VAR_NAME}
                env_var = obj[2:-1]
                return os.getenv(env_var, obj)
            else:
                return obj
        
        self._config = replace_env_vars(self._config)
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值，支持点号分隔的嵌套键"""
        config = self.load_config()
        
        keys = key.split('.')
        value = config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_llm_config(self) -> Dict[str, Any]:
        """获取LLM配置"""
        return self.get('llm', {})
    
    def get_reasoning_config(self) -> Dict[str, Any]:
        """获取推理配置"""
        return self.get('reasoning', {})
    
    def get_tools_config(self) -> Dict[str, Any]:
        """获取工具配置"""
        return self.get('tools', {})
    
    def get_memory_config(self) -> Dict[str, Any]:
        """获取记忆配置"""
        return self.get('memory', {})
    
    def get_collaboration_config(self) -> Dict[str, Any]:
        """获取协作配置"""
        return self.get('collaboration', {})
    
    def get_learning_config(self) -> Dict[str, Any]:
        """获取学习配置"""
        return self.get('learning', {})
    
    def get_security_config(self) -> Dict[str, Any]:
        """获取安全配置"""
        return self.get('security', {})
    
    def get_domain_experts_config(self) -> Dict[str, Any]:
        """获取领域专家配置"""
        return self.get('domain_experts', {})
    
    def get_evaluation_config(self) -> Dict[str, Any]:
        """获取评估配置"""
        return self.get('evaluation', {})


# 全局配置实例
config = ConfigLoader()