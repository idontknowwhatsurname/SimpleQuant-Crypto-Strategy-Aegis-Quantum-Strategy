#!/bin/bash
# AIQuant Engine - macOS DMG 构建脚本
# 用法: ./build_dmg.sh

set -e

APP_NAME="AIQuant Engine"
APP_VERSION="2.0.0"
BUILD_DIR="build"
APP_DIR="$BUILD_DIR/$APP_NAME.app"
DMG_NAME="AIQuant-Engine-$APP_VERSION.dmg"

echo "=========================================="
echo "🚀 AIQuant Engine - DMG 构建脚本"
echo "=========================================="

# 清理旧的构建
rm -rf "$BUILD_DIR"
mkdir -p "$APP_DIR/Contents/MacOS"
mkdir -p "$APP_DIR/Contents/Resources"

# 创建 Info.plist
cat > "$APP_DIR/Contents/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>aiquant-engine</string>
    <key>CFBundleIdentifier</key>
    <string>com.aiquant.engine</string>
    <key>CFBundleName</key>
    <string>$APP_NAME</string>
    <key>CFBundleDisplayName</key>
    <string>$APP_NAME</string>
    <key>CFBundleVersion</key>
    <string>$APP_VERSION</string>
    <key>CFBundleShortVersionString</key>
    <string>$APP_VERSION</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleSignature</key>
    <string>????</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.15</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSHumanReadableCopyright</key>
    <string>Copyright © 2026 AIQuant Engine. All rights reserved.</string>
</dict>
</plist>
EOF

# 创建启动脚本
cat > "$APP_DIR/Contents/MacOS/aiquant-engine" << 'EOF'
#!/bin/bash
# AIQuant Engine 启动脚本

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
APP_DIR="$( dirname "$( dirname "$SCRIPT_DIR" )" )"

# 检查 Python
if ! command -v python3 &> /dev/null; then
    osascript -e 'display dialog "请先安装 Python 3.10+\n\nbrew install python@3.11" buttons {"确定"} default button 1 with icon stop with title "AIQuant Engine"'
    exit 1
fi

# 检查依赖
PYTHON_DIR="$APP_DIR/Contents/Resources/python"
if [ ! -d "$PYTHON_DIR" ]; then
    osascript -e 'display dialog "首次运行需要安装依赖\n\n请运行: pip install -r requirements.txt" buttons {"确定"} default button 1 with icon note with title "AIQuant Engine"'
fi

# 启动 Web GUI
cd "$APP_DIR/Contents/Resources"
open -a "Python Launcher" gui/app.py 2>/dev/null || python3 gui/app.py &

# 等待服务器启动
sleep 2

# 打开浏览器
open "http://localhost:5000"
EOF

chmod +x "$APP_DIR/Contents/MacOS/aiquant-engine"

# 复制项目文件
echo "📦 复制项目文件..."
cp -r gui "$APP_DIR/Contents/Resources/"
cp -r goal "$APP_DIR/Contents/Resources/"
cp -r mcp "$APP_DIR/Contents/Resources/"
cp -r exchange "$APP_DIR/Contents/Resources/"
cp -r notify "$APP_DIR/Contents/Resources/"
cp -r review "$APP_DIR/Contents/Resources/"
cp -r evolution "$APP_DIR/Contents/Resources/"
cp *.py "$APP_DIR/Contents/Resources/"
cp requirements.txt "$APP_DIR/Contents/Resources/"
cp config.toml.example "$APP_DIR/Contents/Resources/"
cp README.md "$APP_DIR/Contents/Resources/"
cp README_CN.md "$APP_DIR/Contents/Resources/"

# 创建 DMG
echo "💿 创建 DMG..."
if command -v hdiutil &> /dev/null; then
    # 使用 hdiutil 创建 DMG
    hdiutil create -volname "$APP_NAME" \
        -srcfolder "$APP_DIR" \
        -ov -format UDZO \
        "$DMG_NAME"
    
    echo "✅ DMG 创建成功: $DMG_NAME"
else
    echo "⚠️ hdiutil 不可用，创建 ZIP 替代..."
    cd "$BUILD_DIR"
    zip -r "../$APP_NAME-$APP_VERSION.zip" "$APP_NAME.app"
    cd ..
    echo "✅ ZIP 创建成功: $APP_NAME-$APP_VERSION.zip"
fi

# 清理
rm -rf "$BUILD_DIR"

echo ""
echo "=========================================="
echo "✅ 构建完成！"
echo "=========================================="
echo ""
echo "文件位置:"
if [ -f "$DMG_NAME" ]; then
    echo "  DMG: $DMG_NAME"
else
    echo "  ZIP: $APP_NAME-$APP_VERSION.zip"
fi
echo ""
echo "分发方式:"
echo "  1. 上传到 GitHub Releases"
echo "  2. 上传到网盘分享给客户"
echo "  3. 直接发送文件"
