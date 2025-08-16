#!/usr/bin/env python3
"""
智能编程助手 - 主程序入口
Intelligent Programming Assistant - Main Entry Point
"""

import sys
import os
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.assistant import IntelligentProgrammingAssistant
from src.utils.logger import get_logger
from src.utils.config_loader import config

logger = get_logger(__name__)


def print_banner():
    """打印欢迎横幅"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                    🎯 智能编程助手                            ║
║              Intelligent Programming Assistant               ║
║                                                              ║
║  集成8个核心AI Agent技术的智能编程助手系统                    ║
║  • 高级推理能力  • 智能工具集成  • 上下文记忆                ║
║  • 多角色协作    • 自主学习      • 安全防护                  ║
║  • 领域专家      • 性能评估                                  ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def print_help():
    """打印帮助信息"""
    help_text = """
可用命令:
  help          - 显示此帮助信息
  config        - 显示当前配置
  status        - 显示系统状态
  summary       - 显示会话摘要
  reset         - 重置会话状态
  save <file>   - 保存会话到文件
  load <file>   - 从文件加载会话
  quit/exit     - 退出程序

使用方法:
  直接输入您的编程需求，系统会自动选择最佳的推理策略和工具来帮助您。

示例:
  > 帮我创建一个Python Web API，用于用户认证
  > 如何优化这段代码的性能？
  > 创建一个React组件来显示用户列表
  > 设计一个数据库架构来存储订单信息
    """
    print(help_text)


def print_config():
    """打印配置信息"""
    llm_config = config.get_llm_config()
    print("\n📋 当前配置:")
    print(f"  LLM提供商: {llm_config.get('provider', 'unknown')}")
    print(f"  模型: {llm_config.get('model', 'unknown')}")
    print(f"  温度: {llm_config.get('temperature', 0.7)}")
    print(f"  最大令牌: {llm_config.get('max_tokens', 4000)}")
    
    reasoning_config = config.get_reasoning_config()
    print(f"  推理策略: {reasoning_config.get('default_strategy', 'auto')}")
    print(f"  启用反思: {reasoning_config.get('enable_reflection', True)}")
    print(f"  启用验证: {reasoning_config.get('enable_verification', True)}")


def print_status(assistant: IntelligentProgrammingAssistant):
    """打印系统状态"""
    print("\n📊 系统状态:")
    print(f"  请求计数: {assistant.request_count}")
    
    # 推理系统状态
    reasoning_summary = assistant.reasoning_engine.get_reasoning_summary()
    print(f"  推理请求: {reasoning_summary.get('total_requests', 0)}")
    print(f"  平均置信度: {reasoning_summary.get('average_confidence', 0):.2f}")
    
    # 工具使用状态
    tool_summary = assistant.tool_manager.get_usage_summary()
    print(f"  工具执行: {tool_summary.get('total_executions', 0)}")
    print(f"  成功率: {tool_summary.get('success_rate', 0):.2%}")
    
    # 记忆系统状态
    memory_summary = assistant.memory_system.get_memory_summary()
    print(f"  记忆项: {memory_summary.get('total_memories', 0)}")
    print(f"  记忆使用率: {memory_summary.get('memory_usage', '0%')}")


def main():
    """主函数"""
    print_banner()
    
    try:
        # 初始化助手
        print("🚀 正在初始化智能编程助手...")
        assistant = IntelligentProgrammingAssistant()
        print("✅ 初始化完成！")
        
        print("\n💡 输入 'help' 查看帮助信息，输入 'quit' 退出程序")
        print("=" * 60)
        
        while True:
            try:
                # 获取用户输入
                user_input = input("\n🤖 您的编程需求: ").strip()
                
                if not user_input:
                    continue
                
                # 处理特殊命令
                if user_input.lower() in ['quit', 'exit']:
                    print("👋 感谢使用智能编程助手！")
                    break
                
                elif user_input.lower() == 'help':
                    print_help()
                    continue
                
                elif user_input.lower() == 'config':
                    print_config()
                    continue
                
                elif user_input.lower() == 'status':
                    print_status(assistant)
                    continue
                
                elif user_input.lower() == 'summary':
                    summary = assistant.get_session_summary()
                    print("\n📈 会话摘要:")
                    print(f"  总请求数: {summary.get('request_count', 0)}")
                    print(f"  推理摘要: {summary.get('reasoning_summary', {})}")
                    continue
                
                elif user_input.lower() == 'reset':
                    assistant.reset_session()
                    print("✅ 会话状态已重置")
                    continue
                
                elif user_input.lower().startswith('save '):
                    filename = user_input[5:].strip()
                    if filename:
                        assistant.save_session(filename)
                        print(f"✅ 会话已保存到 {filename}")
                    else:
                        print("❌ 请指定文件名")
                    continue
                
                elif user_input.lower().startswith('load '):
                    filename = user_input[5:].strip()
                    if filename:
                        try:
                            assistant.load_session(filename)
                            print(f"✅ 会话已从 {filename} 加载")
                        except Exception as e:
                            print(f"❌ 加载失败: {e}")
                    else:
                        print("❌ 请指定文件名")
                    continue
                
                # 处理编程请求
                print("\n🤔 正在思考...")
                
                # 询问是否启用协作模式
                enable_collaboration = False
                if any(keyword in user_input.lower() for keyword in ['系统', '架构', '完整', '项目', '应用']):
                    collab_input = input("🤝 检测到复杂需求，是否启用多角色协作模式？(y/N): ").strip().lower()
                    enable_collaboration = collab_input in ['y', 'yes', '是']
                
                # 处理请求
                response = assistant.handle_request(
                    user_input,
                    enable_collaboration=enable_collaboration
                )
                
                # 显示结果
                print("\n" + "=" * 60)
                print("🎯 智能编程助手的回答:")
                print("=" * 60)
                
                if response.code:
                    print("\n💻 生成的代码:")
                    print("```")
                    print(response.code)
                    print("```")
                
                if response.explanation:
                    print(f"\n📝 详细说明:")
                    print(response.explanation)
                
                # 显示推理信息
                if response.reasoning_steps:
                    print(f"\n🧠 推理步骤:")
                    for i, step in enumerate(response.reasoning_steps[:3], 1):
                        print(f"  {i}. {step}")
                
                # 显示使用的工具
                if response.tools_used:
                    print(f"\n🔧 使用的工具: {', '.join(response.tools_used)}")
                
                # 显示协作角色
                if response.collaboration_roles:
                    print(f"\n👥 协作角色: {', '.join(response.collaboration_roles)}")
                
                # 显示性能信息
                print(f"\n📊 性能信息:")
                print(f"  置信度: {response.confidence:.1%}")
                print(f"  执行时间: {response.execution_time:.2f}秒")
                
                # 显示安全信息
                if not response.security_report.get('is_safe', True):
                    print(f"\n⚠️ 安全警告: 发现 {response.security_report.get('total_issues', 0)} 个安全问题")
                
                print("=" * 60)
                
            except KeyboardInterrupt:
                print("\n\n👋 程序被用户中断")
                break
            except Exception as e:
                logger.error(f"处理请求时发生错误: {e}")
                print(f"\n❌ 处理请求时发生错误: {e}")
                print("请重试或输入 'help' 查看帮助信息")
    
    except Exception as e:
        logger.error(f"程序启动失败: {e}")
        print(f"❌ 程序启动失败: {e}")
        print("请检查配置文件和依赖是否正确安装")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())