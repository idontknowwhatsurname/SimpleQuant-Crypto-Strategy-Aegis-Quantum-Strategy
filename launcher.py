"""
AIQuant Engine - macOS 应用启动器
用于在 macOS 上启动 Web GUI
"""
import subprocess
import sys
import webbrowser
import time
import os
from pathlib import Path


def check_python():
    """检查 Python 版本"""
    if sys.version_info < (3, 10):
        print("❌ 需要 Python 3.10 或更高版本")
        print(f"   当前版本: {sys.version}")
        sys.exit(1)


def check_dependencies():
    """检查依赖是否安装"""
    try:
        import flask
        print("✅ Flask 已安装")
    except ImportError:
        print("⚠️ Flask 未安装，正在安装...")
        subprocess.run([sys.executable, "-m", "pip", "install", "flask"], check=True)


def start_gui():
    """启动 Web GUI"""
    app_path = Path(__file__).parent / "gui" / "app.py"
    
    if not app_path.exists():
        print(f"❌ 找不到 GUI 应用: {app_path}")
        sys.exit(1)
    
    print("🚀 启动 AIQuant Engine...")
    print("   访问地址: http://localhost:5000")
    print("   按 Ctrl+C 停止")
    print("")
    
    # 启动 Flask 应用
    process = subprocess.Popen(
        [sys.executable, str(app_path)],
        cwd=str(Path(__file__).parent)
    )
    
    # 等待服务器启动
    time.sleep(2)
    
    # 打开浏览器
    webbrowser.open("http://localhost:5000")
    
    try:
        process.wait()
    except KeyboardInterrupt:
        print("\n🛑 停止 AIQuant Engine...")
        process.terminate()
        process.wait()


def main():
    """主函数"""
    print("=" * 50)
    print("🛡️ AIQuant Engine - macOS 启动器")
    print("=" * 50)
    print("")
    
    check_python()
    check_dependencies()
    start_gui()


if __name__ == "__main__":
    main()
