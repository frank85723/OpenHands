# 🎯 智能编程助手 - 独立运行版本
## Intelligent Programming Assistant - Standalone Version

这是一个完全独立的AI Agent实战项目，可以脱离OpenHands框架单独运行。

## 🚀 项目特性

- **高级推理能力**: Chain-of-Thought, Tree of Thoughts, 反思机制
- **智能工具集成**: 自动选择和组合编程工具
- **上下文记忆**: 智能的代码上下文管理
- **多角色协作**: 模拟软件开发团队协作
- **自主学习**: 从编程经验中持续学习
- **安全防护**: 全面的代码安全检查
- **领域专家**: 特定技术栈的专业知识
- **性能评估**: 智能的性能监控和评估

## 📦 安装和运行

### 环境要求
- Python 3.8+
- 支持的LLM API (OpenAI, Anthropic, 或本地模型)

### 安装依赖
```bash
cd intelligent_programming_assistant
pip install -r requirements.txt
```

### 配置
1. 复制配置文件：
```bash
cp config/config.example.yaml config/config.yaml
```

2. 编辑配置文件，设置您的LLM API密钥：
```yaml
llm:
  provider: "openai"  # 或 "anthropic", "local"
  api_key: "your-api-key-here"
  model: "gpt-4"
```

### 运行
```bash
# 启动交互式编程助手
python main.py

# 运行演示
python demo.py

# 运行测试
python -m pytest tests/
```

## 🏗️ 项目结构

```
intelligent_programming_assistant/
├── README.md                          # 项目说明
├── requirements.txt                   # 依赖包
├── main.py                           # 主程序入口
├── demo.py                           # 演示程序
├── config/
│   ├── config.example.yaml           # 配置模板
│   └── config.yaml                   # 实际配置（需要创建）
├── src/
│   ├── __init__.py
│   ├── core/                         # 核心系统
│   │   ├── __init__.py
│   │   ├── reasoning_engine.py       # 推理引擎
│   │   ├── tool_manager.py           # 工具管理器
│   │   ├── memory_system.py          # 记忆系统
│   │   ├── collaboration_system.py   # 协作系统
│   │   ├── learning_system.py        # 学习系统
│   │   ├── security_system.py        # 安全系统
│   │   ├── domain_experts.py         # 领域专家
│   │   └── evaluation_system.py      # 评估系统
│   ├── tools/                        # 编程工具
│   │   ├── __init__.py
│   │   ├── code_generator.py         # 代码生成工具
│   │   ├── code_analyzer.py          # 代码分析工具
│   │   ├── debugger.py               # 调试工具
│   │   ├── tester.py                 # 测试工具
│   │   └── refactor.py               # 重构工具
│   ├── agents/                       # 智能体角色
│   │   ├── __init__.py
│   │   ├── architect.py              # 架构师智能体
│   │   ├── developer.py              # 开发者智能体
│   │   ├── tester.py                 # 测试员智能体
│   │   └── reviewer.py               # 代码审查员智能体
│   ├── utils/                        # 工具函数
│   │   ├── __init__.py
│   │   ├── llm_client.py             # LLM客户端
│   │   ├── config_loader.py          # 配置加载器
│   │   └── logger.py                 # 日志工具
│   └── assistant.py                  # 主助手类
├── tests/                            # 测试文件
│   ├── __init__.py
│   ├── test_reasoning_engine.py
│   ├── test_tool_manager.py
│   ├── test_memory_system.py
│   └── test_assistant.py
├── examples/                         # 示例代码
│   ├── basic_usage.py
│   ├── advanced_features.py
│   └── custom_tools.py
└── docs/                            # 文档
    ├── architecture.md
    ├── api_reference.md
    └── development_guide.md
```

## 🎯 快速开始

### 基本使用
```python
from src.assistant import IntelligentProgrammingAssistant

# 初始化助手
assistant = IntelligentProgrammingAssistant()

# 发送编程请求
request = "帮我创建一个Python Web API，用于用户认证"
result = assistant.handle_request(request)

print(f"生成的代码: {result['code']}")
print(f"解释: {result['explanation']}")
```

### 高级功能
```python
# 启用多角色协作
result = assistant.handle_request(
    "创建一个完整的电商系统",
    enable_collaboration=True
)

# 查看推理过程
print(f"推理步骤: {result['reasoning_steps']}")
print(f"使用的工具: {result['tools_used']}")
print(f"协作角色: {result['collaboration_roles']}")
```

## 📚 学习资源

- [架构设计文档](docs/architecture.md)
- [API参考手册](docs/api_reference.md)
- [开发指南](docs/development_guide.md)
- [示例代码](examples/)

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License