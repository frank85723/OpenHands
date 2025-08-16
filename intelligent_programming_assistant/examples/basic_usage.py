#!/usr/bin/env python3
"""
基本使用示例
Basic Usage Example
"""

import sys
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.assistant import IntelligentProgrammingAssistant


def basic_code_generation():
    """基本代码生成示例"""
    print("🚀 基本代码生成示例")
    print("=" * 40)
    
    # 初始化助手
    assistant = IntelligentProgrammingAssistant()
    
    # 发送编程请求
    request = "创建一个Python函数来计算列表中数字的平均值"
    print(f"📝 请求: {request}")
    
    # 处理请求
    response = assistant.handle_request(request)
    
    # 显示结果
    print(f"\n💻 生成的代码:")
    print("```python")
    print(response.code)
    print("```")
    
    print(f"\n📝 解释:")
    print(response.explanation)
    
    print(f"\n📊 性能指标:")
    print(f"  置信度: {response.confidence:.1%}")
    print(f"  执行时间: {response.execution_time:.2f}秒")
    print(f"  使用工具: {', '.join(response.tools_used)}")


def web_api_example():
    """Web API创建示例"""
    print("\n🌐 Web API创建示例")
    print("=" * 40)
    
    assistant = IntelligentProgrammingAssistant()
    
    request = "使用FastAPI创建一个用户管理的RESTful API，包括CRUD操作"
    print(f"📝 请求: {request}")
    
    response = assistant.handle_request(request)
    
    print(f"\n💻 生成的代码:")
    print("```python")
    print(response.code[:800] + "..." if len(response.code) > 800 else response.code)
    print("```")
    
    print(f"\n🎓 专家建议:")
    expert_guidance = assistant.domain_experts.get_expert_guidance(request)
    if expert_guidance.get('relevant_technologies'):
        print(f"  涉及技术: {', '.join(expert_guidance['relevant_technologies'])}")


def database_design_example():
    """数据库设计示例"""
    print("\n🗄️ 数据库设计示例")
    print("=" * 40)
    
    assistant = IntelligentProgrammingAssistant()
    
    request = "设计一个电商系统的数据库架构，包括用户、商品、订单表"
    print(f"📝 请求: {request}")
    
    response = assistant.handle_request(request)
    
    print(f"\n📋 数据库设计:")
    print(response.explanation[:600] + "..." if len(response.explanation) > 600 else response.explanation)
    
    if response.code:
        print(f"\n💻 SQL代码:")
        print("```sql")
        print(response.code[:500] + "..." if len(response.code) > 500 else response.code)
        print("```")


def algorithm_optimization_example():
    """算法优化示例"""
    print("\n⚡ 算法优化示例")
    print("=" * 40)
    
    assistant = IntelligentProgrammingAssistant()
    
    request = "优化这个冒泡排序算法的性能，并提供更好的替代方案"
    print(f"📝 请求: {request}")
    
    response = assistant.handle_request(request)
    
    print(f"\n🧠 推理步骤:")
    for i, step in enumerate(response.reasoning_steps[:3], 1):
        print(f"  {i}. {step}")
    
    print(f"\n💻 优化后的代码:")
    print("```python")
    print(response.code[:600] + "..." if len(response.code) > 600 else response.code)
    print("```")


def security_focused_example():
    """安全重点示例"""
    print("\n🛡️ 安全重点示例")
    print("=" * 40)
    
    assistant = IntelligentProgrammingAssistant()
    
    request = "创建一个安全的用户认证系统，包括密码哈希和JWT令牌"
    print(f"📝 请求: {request}")
    
    response = assistant.handle_request(request)
    
    print(f"\n🔒 安全检查结果:")
    security_report = response.security_report
    print(f"  安全状态: {'✅ 通过' if security_report.get('is_safe', True) else '❌ 未通过'}")
    print(f"  安全问题数: {security_report.get('total_issues', 0)}")
    
    if security_report.get('total_issues', 0) > 0:
        print(f"  高危问题: {security_report.get('high_severity_issues', 0)}")
        print(f"  中危问题: {security_report.get('medium_severity_issues', 0)}")
    
    print(f"\n💻 安全的认证代码:")
    print("```python")
    print(response.code[:700] + "..." if len(response.code) > 700 else response.code)
    print("```")


def main():
    """主函数"""
    print("🎯 智能编程助手 - 基本使用示例")
    print("=" * 50)
    
    examples = [
        basic_code_generation,
        web_api_example,
        database_design_example,
        algorithm_optimization_example,
        security_focused_example
    ]
    
    for i, example_func in enumerate(examples, 1):
        try:
            example_func()
            
            if i < len(examples):
                input(f"\n按回车键继续下一个示例... ({i}/{len(examples)})")
        
        except Exception as e:
            print(f"❌ 示例 {i} 执行失败: {e}")
    
    print("\n🎉 所有示例执行完成！")
    print("\n💡 提示:")
    print("  - 您可以修改请求内容来测试不同的功能")
    print("  - 尝试启用协作模式处理复杂项目")
    print("  - 查看生成的代码和专家建议")


if __name__ == "__main__":
    main()