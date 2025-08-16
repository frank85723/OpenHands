#!/usr/bin/env python3
"""
智能编程助手安装脚本
Intelligent Programming Assistant Setup Script
"""

import os
import sys
import shutil
from pathlib import Path


def create_directories():
    """创建必要的目录"""
    directories = [
        "data",
        "logs",
        "config"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ 创建目录: {directory}")


def setup_config():
    """设置配置文件"""
    config_dir = Path("config")
    example_config = config_dir / "config.example.yaml"
    config_file = config_dir / "config.yaml"
    
    if example_config.exists() and not config_file.exists():
        shutil.copy(example_config, config_file)
        print("✅ 创建配置文件: config/config.yaml")
        print("💡 请编辑 config/config.yaml 设置您的LLM API密钥")
    else:
        print("ℹ️ 配置文件已存在")


def install_dependencies():
    """安装依赖"""
    print("📦 安装基础依赖...")
    
    try:
        import subprocess
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], check=True, capture_output=True, text=True)
        print("✅ 基础依赖安装完成")
    except subprocess.CalledProcessError as e:
        print(f"❌ 依赖安装失败: {e}")
        print("请手动运行: pip install -r requirements.txt")


def setup_llm_provider():
    """设置LLM提供商"""
    print("\n🤖 LLM提供商设置")
    print("选择您要使用的LLM提供商:")
    print("1. OpenAI (推荐)")
    print("2. Anthropic")
    print("3. 跳过 (使用模拟模式)")
    
    choice = input("请选择 (1-3): ").strip()
    
    if choice == "1":
        try:
            import subprocess
            subprocess.run([
                sys.executable, "-m", "pip", "install", "openai>=1.0.0"
            ], check=True)
            print("✅ OpenAI库安装完成")
            print("💡 请在 config/config.yaml 中设置您的 OpenAI API 密钥")
        except subprocess.CalledProcessError:
            print("❌ OpenAI库安装失败，请手动安装: pip install openai")
    
    elif choice == "2":
        try:
            import subprocess
            subprocess.run([
                sys.executable, "-m", "pip", "install", "anthropic>=0.7.0"
            ], check=True)
            print("✅ Anthropic库安装完成")
            print("💡 请在 config/config.yaml 中设置您的 Anthropic API 密钥")
        except subprocess.CalledProcessError:
            print("❌ Anthropic库安装失败，请手动安装: pip install anthropic")
    
    else:
        print("ℹ️ 跳过LLM提供商安装，将使用模拟模式")


def run_tests():
    """运行测试"""
    print("\n🧪 运行测试...")
    
    try:
        import subprocess
        result = subprocess.run([
            sys.executable, "-m", "pytest", "tests/", "-v"
        ], check=True, capture_output=True, text=True)
        print("✅ 所有测试通过")
    except subprocess.CalledProcessError as e:
        print("⚠️ 部分测试失败，但系统仍可正常使用")
    except FileNotFoundError:
        print("ℹ️ pytest未安装，跳过测试")


def main():
    """主安装函数"""
    print("🎯 智能编程助手安装程序")
    print("=" * 50)
    
    # 检查Python版本
    if sys.version_info < (3, 8):
        print("❌ 需要Python 3.8或更高版本")
        return 1
    
    print(f"✅ Python版本: {sys.version}")
    
    try:
        # 1. 创建目录
        create_directories()
        
        # 2. 设置配置
        setup_config()
        
        # 3. 安装依赖
        install_dependencies()
        
        # 4. 设置LLM提供商
        setup_llm_provider()
        
        # 5. 运行测试
        run_tests()
        
        print("\n🎉 安装完成！")
        print("\n📚 使用方法:")
        print("  python main.py          # 启动交互式助手")
        print("  python demo.py          # 运行演示程序")
        print("  python examples/basic_usage.py  # 查看使用示例")
        
        print("\n⚙️ 配置:")
        print("  编辑 config/config.yaml 设置您的偏好")
        print("  设置LLM API密钥以获得最佳体验")
        
        return 0
        
    except Exception as e:
        print(f"❌ 安装过程中发生错误: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())