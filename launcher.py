"""AIQuant Engine - macOS 应用启动器."""
import socket
import sys
import threading
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from gui.app import app


def choose_port(preferred: int = 5000) -> int:
    """选择一个可用端口，优先使用 5000。"""
    for port in (preferred, 5001, 5002, 8000):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            if sock.connect_ex(("127.0.0.1", port)) != 0:
                return port
    raise RuntimeError("没有找到可用端口")


def wait_for_server(url: str, timeout: float = 20.0) -> None:
    """等待本地服务器就绪，然后打开浏览器。"""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(f"{url}/api/status", timeout=1.5) as resp:
                if resp.status == 200:
                    webbrowser.open(url)
                    return
        except (urllib.error.URLError, TimeoutError):
            time.sleep(0.3)
    webbrowser.open(url)


def main():
    """主函数。"""
    port = choose_port()
    url = f"http://127.0.0.1:{port}"
    opener = threading.Thread(target=wait_for_server, args=(url,), daemon=True)
    opener.start()

    print("=" * 50)
    print("🛡️ AIQuant Engine - macOS 启动器")
    print("=" * 50)
    print(f"访问地址: {url}")
    print("=" * 50)

    app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
