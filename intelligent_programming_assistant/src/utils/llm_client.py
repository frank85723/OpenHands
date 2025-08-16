"""LLM客户端"""

import asyncio
from typing import Dict, List, Any, Optional, Union
from abc import ABC, abstractmethod

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

from .config_loader import config
from .logger import get_logger

logger = get_logger(__name__)


class BaseLLMClient(ABC):
    """LLM客户端基类"""
    
    @abstractmethod
    def completion(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """同步完成接口"""
        pass
    
    @abstractmethod
    async def acompletion(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """异步完成接口"""
        pass


class OpenAIClient(BaseLLMClient):
    """OpenAI客户端"""
    
    def __init__(self, api_key: str, model: str = "gpt-4", base_url: Optional[str] = None):
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI库未安装，请运行: pip install openai")
        
        self.client = openai.OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        self.model = model
        logger.info(f"OpenAI客户端初始化完成 - 模型: {model}")
    
    def completion(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """同步完成"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                **kwargs
            )
            
            return {
                'choices': [{
                    'message': {
                        'content': response.choices[0].message.content,
                        'role': response.choices[0].message.role
                    }
                }],
                'usage': {
                    'prompt_tokens': response.usage.prompt_tokens,
                    'completion_tokens': response.usage.completion_tokens,
                    'total_tokens': response.usage.total_tokens
                }
            }
        except Exception as e:
            logger.error(f"OpenAI API调用失败: {e}")
            raise
    
    async def acompletion(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """异步完成"""
        # OpenAI的同步客户端，使用线程池执行
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.completion, messages, **kwargs)


class AnthropicClient(BaseLLMClient):
    """Anthropic客户端"""
    
    def __init__(self, api_key: str, model: str = "claude-3-sonnet-20240229"):
        if not ANTHROPIC_AVAILABLE:
            raise ImportError("Anthropic库未安装，请运行: pip install anthropic")
        
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        logger.info(f"Anthropic客户端初始化完成 - 模型: {model}")
    
    def completion(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """同步完成"""
        try:
            # 转换消息格式
            system_message = ""
            user_messages = []
            
            for msg in messages:
                if msg['role'] == 'system':
                    system_message = msg['content']
                else:
                    user_messages.append(msg)
            
            response = self.client.messages.create(
                model=self.model,
                system=system_message,
                messages=user_messages,
                max_tokens=kwargs.get('max_tokens', 4000),
                temperature=kwargs.get('temperature', 0.7)
            )
            
            return {
                'choices': [{
                    'message': {
                        'content': response.content[0].text,
                        'role': 'assistant'
                    }
                }],
                'usage': {
                    'prompt_tokens': response.usage.input_tokens,
                    'completion_tokens': response.usage.output_tokens,
                    'total_tokens': response.usage.input_tokens + response.usage.output_tokens
                }
            }
        except Exception as e:
            logger.error(f"Anthropic API调用失败: {e}")
            raise
    
    async def acompletion(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """异步完成"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.completion, messages, **kwargs)


class MockLLMClient(BaseLLMClient):
    """模拟LLM客户端，用于测试"""
    
    def __init__(self):
        self.call_count = 0
        logger.info("模拟LLM客户端初始化完成")
    
    def completion(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """模拟完成"""
        self.call_count += 1
        
        # 根据消息内容生成模拟响应
        last_message = messages[-1]['content'] if messages else ""
        
        if "代码" in last_message or "code" in last_message.lower():
            response_content = """
```python
def hello_world():
    print("Hello, World!")
    return "Hello, World!"

if __name__ == "__main__":
    hello_world()
```

这是一个简单的Python Hello World程序。
"""
        elif "错误" in last_message or "error" in last_message.lower():
            response_content = "我发现了一个潜在的错误。建议检查变量名和函数调用。"
        else:
            response_content = f"这是对您问题的回答: {last_message[:50]}..."
        
        return {
            'choices': [{
                'message': {
                    'content': response_content,
                    'role': 'assistant'
                }
            }],
            'usage': {
                'prompt_tokens': len(last_message) // 4,
                'completion_tokens': len(response_content) // 4,
                'total_tokens': (len(last_message) + len(response_content)) // 4
            }
        }
    
    async def acompletion(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """异步模拟完成"""
        await asyncio.sleep(0.1)  # 模拟网络延迟
        return self.completion(messages, **kwargs)


class LLMClient:
    """LLM客户端工厂类"""
    
    def __init__(self, provider: Optional[str] = None, **kwargs):
        llm_config = config.get_llm_config()
        
        self.provider = provider or llm_config.get('provider', 'openai')
        self.api_key = kwargs.get('api_key') or llm_config.get('api_key')
        self.model = kwargs.get('model') or llm_config.get('model', 'gpt-4')
        self.base_url = kwargs.get('base_url') or llm_config.get('base_url')
        self.temperature = kwargs.get('temperature') or llm_config.get('temperature', 0.7)
        self.max_tokens = kwargs.get('max_tokens') or llm_config.get('max_tokens', 4000)
        self.timeout = kwargs.get('timeout') or llm_config.get('timeout', 30)
        
        # 检查是否为测试模式
        if config.get('development.test_mode') or config.get('development.mock_llm'):
            self.provider = 'mock'
        
        self.client = self._create_client()
    
    def _create_client(self) -> BaseLLMClient:
        """创建LLM客户端"""
        if self.provider == 'openai':
            if not self.api_key:
                raise ValueError("OpenAI API密钥未配置")
            return OpenAIClient(self.api_key, self.model, self.base_url)
        
        elif self.provider == 'anthropic':
            if not self.api_key:
                raise ValueError("Anthropic API密钥未配置")
            return AnthropicClient(self.api_key, self.model)
        
        elif self.provider == 'mock':
            return MockLLMClient()
        
        else:
            raise ValueError(f"不支持的LLM提供商: {self.provider}")
    
    def completion(self, messages: Union[List[Dict[str, str]], str], **kwargs) -> Dict[str, Any]:
        """同步完成"""
        if isinstance(messages, str):
            messages = [{'role': 'user', 'content': messages}]
        
        # 合并默认参数
        params = {
            'temperature': self.temperature,
            'max_tokens': self.max_tokens,
            **kwargs
        }
        
        return self.client.completion(messages, **params)
    
    async def acompletion(self, messages: Union[List[Dict[str, str]], str], **kwargs) -> Dict[str, Any]:
        """异步完成"""
        if isinstance(messages, str):
            messages = [{'role': 'user', 'content': messages}]
        
        # 合并默认参数
        params = {
            'temperature': self.temperature,
            'max_tokens': self.max_tokens,
            **kwargs
        }
        
        return await self.client.acompletion(messages, **params)
    
    def get_response_text(self, response: Dict[str, Any]) -> str:
        """从响应中提取文本内容"""
        try:
            return response['choices'][0]['message']['content']
        except (KeyError, IndexError):
            return ""
    
    def get_usage_info(self, response: Dict[str, Any]) -> Dict[str, int]:
        """从响应中提取使用信息"""
        try:
            return response['usage']
        except KeyError:
            return {'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0}