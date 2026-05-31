#!/bin/bash
# AIQuant Engine - macOS DMG 构建脚本
# 使用 PyInstaller 打包为独立 .app
# 
# 前置条件:
#   pip install flask pyinstaller
#
set -e

APP_NAME="AIQuant Engine"
APP_VERSION="2.0.0"
BUILD_DIR="build"
DMG_NAME="AIQuant-Engine-${APP_VERSION}.dmg"
SPEC_FILE="aiquant.spec"

echo "=========================================="
echo "🚀 AIQuant Engine - DMG 构建脚本"
echo "=========================================="
echo ""

# 检查工具链
echo "🔍 检查环境..."

# Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 需要 Python 3.10+"
    echo "   安装: brew install python@3.11"
    exit 1
fi
PY_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "  ✅ Python $PY_VER"

# PyInstaller
if ! python3 -c "import PyInstaller" 2>/dev/null; then
    echo "  ⏳ 安装 PyInstaller..."
    pip3 install pyinstaller
fi
echo "  ✅ PyInstaller"

# Flask
if ! python3 -c "import flask" 2>/dev/null; then
    echo "  ⏳ 安装 Flask..."
    pip3 install flask
fi
echo "  ✅ Flask"

echo ""

# 清理旧构建
echo "🧹 清理..."
rm -rf "$BUILD_DIR" "$DMG_NAME" dist

# 构建 .app
echo "📦 使用 PyInstaller 构建 .app..."
python3 -m PyInstaller \
    --clean \
    -y \
    --windowed \
    --name "AIQuant Engine" \
    --add-data "exchange:exchange" \
    --add-data "notify:notify" \
    --add-data "review:review" \
    --add-data "evolution:evolution" \
    --add-data "goal:goal" \
    --add-data "mcp:mcp" \
    --add-data "gui/templates:gui/templates" \
    --add-data "gui/static:gui/static" \
    --add-data "config.toml.example:." \
    --add-data "README.md:." \
    --add-data "README_CN.md:." \
    --hidden-import "signals" \
    --hidden-import "risk_manager" \
    --hidden-import "market_regime" \
    --hidden-import "ai_router" \
    --hidden-import "order_executor" \
    --hidden-import "config_loader" \
    --hidden-import "results_analyzer" \
    --hidden-import "real_portfolio" \
    --hidden-import "backtester" \
    --hidden-import "data_loader" \
    --hidden-import "exchange.base" \
    --hidden-import "exchange.okx" \
    --hidden-import "exchange.binance" \
    --hidden-import "exchange.gate" \
    --hidden-import "exchange.factory" \
    --hidden-import "notify.channels.telegram" \
    --hidden-import "notify.channels.wechat" \
    --hidden-import "notify.channels.discord" \
    --hidden-import "notify.channels.qq" \
    --hidden-import "notify.channels.email" \
    --hidden-import "review.analyzer" \
    --hidden-import "evolution.manager" \
    --hidden-import "goal.planner" \
    --hidden-import "mcp.prompt_bar" \
    --hidden-import "appdirs" \
    --exclude "tkinter" \
    --exclude "matplotlib" \
    --exclude "scipy" \
    --exclude "cv2" \
    --exclude-module "pkg_resources" \
    --exclude-module "setuptools" \
    launcher.py

# 检查构建结果
if [ ! -d "dist/AIQuant Engine.app" ]; then
    echo "❌ .app 构建失败"
    exit 1
fi
echo "  ✅ .app 构建成功"

# 设置图标（如果有）
echo "  🎨 配置应用..."
plist="dist/AIQuant Engine.app/Contents/Info.plist"
# 更新 plist
python3 -c "
import plistlib
plist_path = '$plist'
with open(plist_path, 'rb') as f:
    pl = plistlib.load(f)
pl['CFBundleShortVersionString'] = '$APP_VERSION'
pl['CFBundleVersion'] = '$APP_VERSION'
pl['CFBundleIdentifier'] = 'com.aiquant.engine'
pl['CFBundleDisplayName'] = '$APP_NAME'
pl['NSHighResolutionCapable'] = True
pl['LSMinimumSystemVersion'] = '10.15'
with open(plist_path, 'wb') as f:
    plistlib.dump(pl, f)
print('  ✅ Info.plist 已更新')
"

# 签名（本地开发不需要正式签名）
echo "  🔏 签名应用..."
codesign --force --deep --sign - "dist/AIQuant Engine.app" 2>/dev/null && echo "  ✅ 签名完成" || echo "  ⚠️ 签名跳过"

# 创建 DMG
echo "💿 创建 DMG..."
mkdir -p "$BUILD_DIR"

# 创建一个临时目录用于 DMG 内容
TEMP_DMG="$BUILD_DIR/dmg"
mkdir -p "$TEMP_DMG"

# 复制 .app 到 DMG 目录
cp -R "dist/AIQuant Engine.app" "$TEMP_DMG/"

# 创建 Applications 别名（拖拽安装提示）
ln -s /Applications "$TEMP_DMG/Applications"

# 创建 DMG
hdiutil create \
    -volname "$APP_NAME" \
    -srcfolder "$TEMP_DMG" \
    -ov -format UDZO \
    -size 500m \
    "$DMG_NAME"

# 清理
rm -rf "$BUILD_DIR/TEMP_DMG" 2>/dev/null

echo ""
echo "=========================================="
echo "✅ 构建完成！"
echo "=========================================="
echo ""
echo "📦 DMG 文件: $DMG_NAME"
echo "📏 大小: $(du -h "$DMG_NAME" | cut -f1)"
echo ""
echo "安装方式:"
echo "  1. 双击 $DMG_NAME"
echo "  2. 拖动 AIQuant Engine.app 到 Applications 文件夹"
echo "  3. 在终端运行: open -a 'AIQuant Engine'"
echo ""
echo "注意: 首次运行会提示\"无法验证开发者\""
echo "      右键 → 打开 即可运行"
echo "=========================================="
