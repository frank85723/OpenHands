#!/usr/bin/env python3
"""
智能编程助手演示程序
Intelligent Programming Assistant Demo
"""

import sys
import time
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.assistant import IntelligentProgrammingAssistant
from src.utils.logger import get_logger

logger = get_logger(__name__)


def print_demo_banner():
    """打印演示横幅"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                🎯 智能编程助手 - 演示模式                     ║
║              Intelligent Programming Assistant Demo          ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def demo_basic_usage():
    """演示基本使用"""
    print("\n🚀 演示1: 基本代码生成")
    print("=" * 50)
    
    assistant = IntelligentProgrammingAssistant()
    
    request = "创建一个Python函数来计算斐波那契数列"
    print(f"📝 请求: {request}")
    
    response = assistant.handle_request(request)
    
    print(f"\n💻 生成的代码:")
    print("```python")
    print(response.code)
    print("```")
    
    print(f"\n📊 性能指标:")
    print(f"  置信度: {response.confidence:.1%}")
    print(f"  执行时间: {response.execution_time:.2f}秒")
    print(f"  使用工具: {', '.join(response.tools_used)}")


def demo_advanced_reasoning():
    """演示高级推理"""
    print("\n🧠 演示2: 高级推理能力")
    print("=" * 50)
    
    assistant = IntelligentProgrammingAssistant()
    
    request = "设计一个高性能的缓存系统，需要支持LRU淘汰策略和并发访问"
    print(f"📝 请求: {request}")
    
    response = assistant.handle_request(request)
    
    print(f"\n🤔 推理步骤:")
    for i, step in enumerate(response.reasoning_steps[:5], 1):
        print(f"  {i}. {step}")
    
    print(f"\n💻 解决方案:")
    print(response.explanation[:500] + "..." if len(response.explanation) > 500 else response.explanation)
    
    print(f"\n📊 推理分析:")
    print(f"  置信度: {response.confidence:.1%}")
    print(f"  推理策略: 自动选择")


def demo_collaboration():
    """演示多角色协作"""
    print("\n👥 演示3: 多角色协作")
    print("=" * 50)
    
    assistant = IntelligentProgrammingAssistant()
    
    request = "创建一个完整的用户管理系统，包括前端、后端和数据库"
    print(f"📝 请求: {request}")
    
    response = assistant.handle_request(
        request, 
        enable_collaboration=True
    )
    
    if response.collaboration_roles:
        print(f"\n👥 参与的角色:")
        for role in response.collaboration_roles:
            print(f"  • {role}")
    
    print(f"\n💻 协作结果:")
    print(response.explanation[:500] + "..." if len(response.explanation) > 500 else response.explanation)
    
    print(f"\n📊 协作效果:")
    print(f"  置信度: {response.confidence:.1%}")
    print(f"  参与角色数: {len(response.collaboration_roles)}")


def demo_security_features():
    """演示安全功能"""
    print("\n🛡️ 演示4: 安全防护功能")
    print("=" * 50)
    
    assistant = IntelligentProgrammingAssistant()
    
    # 测试安全的请求
    safe_request = "创建一个安全的用户认证系统"
    print(f"📝 安全请求: {safe_request}")
    
    response = assistant.handle_request(safe_request)
    
    print(f"\n✅ 安全检查结果:")
    security_report = response.security_report
    print(f"  安全状态: {'通过' if security_report.get('is_safe', True) else '未通过'}")
    print(f"  安全问题数: {security_report.get('total_issues', 0)}")
    
    if security_report.get('total_issues', 0) > 0:
        print(f"  高危问题: {security_report.get('high_severity_issues', 0)}")
        print(f"  中危问题: {security_report.get('medium_severity_issues', 0)}")


def demo_learning_capabilities():
    """演示学习能力"""
    print("\n📚 演示5: 自主学习能力")
    print("=" * 50)
    
    assistant = IntelligentProgrammingAssistant()
    
    # 进行几次交互来展示学习
    requests = [
        "创建一个简单的计算器",
        "优化计算器的性能",
        "为计算器添加历史记录功能"
    ]
    
    for i, request in enumerate(requests, 1):
        print(f"\n📝 请求 {i}: {request}")
        response = assistant.handle_request(request, enable_learning=True)
        
        if response.learning_insights:
            print(f"💡 学习洞察: {response.learning_insights.get('patterns_learned', 0)} 个新模式")
    
    # 显示学习摘要
    learning_summary = assistant.learning_system.get_learning_summary()
    print(f"\n📊 学习摘要:")
    print(f"  学习模式数: {learning_summary.get('total_patterns', 0)}")
    print(f"  平均有效性: {learning_summary.get('average_effectiveness', 0):.2f}")


def demo_performance_evaluation():
    """演示性能评估"""
    print("\n📈 演示6: 性能评估系统")
    print("=" * 50)
    
    assistant = IntelligentProgrammingAssistant()
    
    request = "创建一个RESTful API服务"
    print(f"📝 请求: {request}")
    
    response = assistant.handle_request(request)
    
    print(f"\n📊 详细评估指标:")
    metrics = response.evaluation_metrics
    if metrics:
        print(f"  代码质量: {metrics.get('code_quality_score', 0):.2f}")
        print(f"  性能评分: {metrics.get('performance_score', 0):.2f}")
        print(f"  安全评分: {metrics.get('security_score', 0):.2f}")
        print(f"  总体评分: {metrics.get('overall_score', 0):.2f}")


def demo_domain_expertise():
    """演示领域专家功能"""
    print("\n🎓 演示7: 领域专家咨询")
    print("=" * 50)
    
    assistant = IntelligentProgrammingAssistant()
    
    request = "使用React和Django创建一个全栈Web应用"
    print(f"📝 请求: {request}")
    
    # 获取专家指导
    expert_guidance = assistant.domain_experts.get_expert_guidance(request)
    
    print(f"\n🎓 涉及的专家:")
    for tech in expert_guidance.get('relevant_technologies', []):
        print(f"  • {tech.upper()} 专家")
    
    print(f"\n💡 专家建议摘要:")
    integrated_guidance = expert_guidance.get('integrated_guidance', '')
    print(integrated_guidance[:300] + "..." if len(integrated_guidance) > 300 else integrated_guidance)


def interactive_demo():
    """交互式演示"""
    print("\n🎮 交互式演示模式")
    print("=" * 50)
    print("您可以输入任何编程相关的问题，系统会展示完整的处理过程")
    print("输入 'quit' 退出演示")
    
    assistant = IntelligentProgrammingAssistant()
    
    while True:
        try:
            user_input = input("\n🤖 您的问题: ").strip()
            
            if user_input.lower() in ['quit', 'exit', '退出']:
                break
            
            if not user_input:
                continue
            
            print("\n🤔 正在处理...")
            
            # 处理请求
            response = assistant.handle_request(user_input)
            
            # 显示完整的处理过程
            print(f"\n🧠 推理过程:")
            print(f"  置信度: {response.confidence:.1%}")
            print(f"  使用工具: {', '.join(response.tools_used) if response.tools_used else '无'}")
            
            if response.code:
                print(f"\n💻 生成的代码:")
                print("```")
                print(response.code[:500] + "..." if len(response.code) > 500 else response.code)
                print("```")
            
            print(f"\n📝 解释:")
            print(response.explanation[:400] + "..." if len(response.explanation) > 400 else response.explanation)
            
            print(f"\n📊 性能指标:")
            print(f"  执行时间: {response.execution_time:.2f}秒")
            print(f"  安全检查: {'通过' if response.security_report.get('is_safe', True) else '未通过'}")
            
        except KeyboardInterrupt:
            print("\n演示被中断")
            break
        except Exception as e:
            print(f"\n❌ 处理过程中发生错误: {e}")


def main():
    """主演示函数"""
    print_demo_banner()
    
    print("选择演示模式:")
    print("1. 自动演示 - 展示所有功能")
    print("2. 交互式演示 - 自由提问")
    print("3. 退出")
    
    try:
        choice = input("\n请选择 (1-3): ").strip()
        
        if choice == '1':
            print("\n🎬 开始自动演示...")
            
            demos = [
                demo_basic_usage,
                demo_advanced_reasoning,
                demo_collaboration,
                demo_security_features,
                demo_learning_capabilities,
                demo_performance_evaluation,
                demo_domain_expertise
            ]
            
            for i, demo_func in enumerate(demos, 1):
                print(f"\n{'='*60}")
                print(f"演示进度: {i}/{len(demos)}")
                print(f"{'='*60}")
                
                try:
                    demo_func()
                except Exception as e:
                    print(f"❌ 演示 {i} 失败: {e}")
                
                if i < len(demos):
                    input("\n按回车键继续下一个演示...")
            
            print("\n🎉 所有演示完成！")
            
        elif choice == '2':
            interactive_demo()
            
        elif choice == '3':
            print("👋 感谢观看演示！")
            
        else:
            print("❌ 无效选择")
            return 1
    
    except KeyboardInterrupt:
        print("\n\n👋 演示被用户中断")
    except Exception as e:
        logger.error(f"演示过程中发生错误: {e}")
        print(f"❌ 演示过程中发生错误: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())