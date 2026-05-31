# AIQuant Engine - macOS DMG 构建指南

## 前置要求

1. **macOS 10.15+**
2. **Python 3.10+**
   ```bash
   brew install python@3.11
   ```

## 构建步骤

### 方式一：使用构建脚本（推荐）

```bash
# 1. 克隆项目
git clone https://github.com/idontknowwhatsurname/SimpleQuant-Crypto-Strategy-Aegis-Quantum-Strategy.git
cd SimpleQuant-Crypto-Strategy-Aegis-Quantum-Strategy

# 2. 安装依赖
pip install -r requirements.txt

# 3. 构建 DMG
chmod +x build_dmg.sh
./build_dmg.sh
```

构建完成后会生成：
- `AIQuant-Engine-2.0.0.dmg` (macOS 磁盘映像)
- 或 `AIQuant-Engine-2.0.0.zip` (备用格式)

### 方式二：手动构建

```bash
# 1. 创建 .app 目录结构
mkdir -p "build/AIQuant Engine.app/Contents/MacOS"
mkdir -p "build/AIQuant Engine.app/Contents/Resources"

# 2. 复制项目文件
cp -r gui "build/AIQuant Engine.app/Contents/Resources/"
cp -r goal "build/AIQuant Engine.app/Contents/Resources/"
cp -r mcp "build/AIQuant Engine.app/Contents/Resources/"
cp -r exchange "build/AIQuant Engine.app/Contents/Resources/"
cp -r notify "build/AIQuant Engine.app/Contents/Resources/"
cp -r review "build/AIQuant Engine.app/Contents/Resources/"
cp -r evolution "build/AIQuant Engine.app/Contents/Resources/"
cp *.py "build/AIQuant Engine.app/Contents/Resources/"
cp requirements.txt "build/AIQuant Engine.app/Contents/Resources/"
cp config.toml.example "build/AIQuant Engine.app/Contents/Resources/"

# 3. 创建 DMG
hdiutil create -volname "AIQuant Engine" \
    -srcfolder "build/AIQuant Engine.app" \
    -ov -format UDZO \
    "AIQuant-Engine-2.0.0.dmg"
```

## 分发方式

### 1. GitHub Releases（推荐）

```bash
# 创建 Release
gh release create v2.0.0 \
    --title "AIQuant Engine v2.0.0" \
    --notes "AI 原生加密货币量化交易框架" \
    AIQuant-Engine-2.0.0.dmg
```

### 2. 网盘分享

上传 DMG 文件到网盘，生成分享链接。

### 3. 直接发送

通过邮件或即时通讯工具发送 DMG 文件。

## 客户安装流程

1. **下载 DMG 文件**
2. **双击打开 DMG**
3. **拖动应用到 Applications 文件夹**
4. **首次运行**
   - 右键点击应用 → 打开
   - 系统可能提示"无法验证开发者"，点击"打开"
5. **配置 API Key**
   - 应用会自动打开配置向导
   - 填入 OKX API Key 等信息
6. **开始使用**
   - 点击"启动引擎"按钮
   - 浏览器会自动打开 Web GUI

## 注意事项

### 代码签名

如果需要分发给其他用户，建议进行代码签名：

```bash
# 签名应用
codesign --force --deep --sign - "build/AIQuant Engine.app"

# 验证签名
codesign --verify --verbose "build/AIQuant Engine.app"
```

### 公证（可选）

如果需要上架 Mac App Store 或避免 Gatekeeper 警告：

```bash
# 提交公证
xcrun notarytool submit AIQuant-Engine-2.0.0.dmg \
    --apple-id "your@email.com" \
    --team-id "YOUR_TEAM_ID" \
    --password "app-specific-password"

# 等待公证完成
xcrun notarytool info <submission-id> \
    --apple-id "your@email.com" \
    --team-id "YOUR_TEAM_ID"
```

### 常见问题

**Q: 提示"无法验证开发者"怎么办？**
A: 右键点击应用 → 打开，或在 系统设置 → 隐私与安全性 中允许运行。

**Q: 首次运行闪退？**
A: 检查 Python 是否正确安装，运行 `python3 --version` 确认版本 >= 3.10。

**Q: 端口被占用？**
A: 修改 `gui/app.py` 中的端口号，或关闭占用 5000 端口的程序。
