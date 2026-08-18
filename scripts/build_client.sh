#!/usr/bin/env bash
# ai-unified-memory 桌面客户端跨平台打包脚本
# Windows → dist/AUM-Windows-x64.exe
# macOS   → dist/AUM-macOS.app
# Linux   → dist/AUM-Linux-x86_64.AppImage
set -e
cd "$(dirname "$0")/.."

APP_NAME="AUM"
ENTRY="desktop/desktop.py"

echo "📦 $APP_NAME 桌面客户端打包开始..."

case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*)  PLATFORM="windows" ;;
  Darwin*)               PLATFORM="macos" ;;
  Linux*)                PLATFORM="linux" ;;
  *) echo "❌ 未知平台: $(uname -s)"; exit 1 ;;
esac
echo "🎯 平台: $PLATFORM"

# 依赖
python -c "import pywebview" 2>/dev/null || pip install pywebview
python -c "import PyInstaller" 2>/dev/null || pip install pyinstaller
python -c "import fastapi, uvicorn" 2>/dev/null || pip install fastapi uvicorn

# --add-data 分隔符: Windows 用 ';'，Unix 用 ':'
if [ "$PLATFORM" = "windows" ]; then
  SEP=";"
else
  SEP=":"
fi

# 打包：前端 + 全部 scripts（记忆引擎）
python -m PyInstaller --noconfirm --onefile --windowed --name "$APP_NAME" \
  --collect-all pywebview \
  --hidden-import uvicorn.logging \
  --hidden-import uvicorn.loops.auto \
  --hidden-import uvicorn.protocols.http.auto \
  --hidden-import uvicorn.protocols.websockets.auto \
  --hidden-import uvicorn.lifespan.on \
  --add-data "desktop/web${SEP}web" \
  --add-data "scripts${SEP}scripts" \
  --add-data "CONFIG.example.json${SEP}." \
  "$ENTRY"

case "$PLATFORM" in
  windows)
    mv -f "dist/$APP_NAME.exe" "dist/$APP_NAME-Windows-x64.exe"
    echo "✅ Windows 安装包: dist/$APP_NAME-Windows-x64.exe"
    ;;
  macos)
    mv -f "dist/$APP_NAME.app" "dist/$APP_NAME-macOS.app"
    echo "✅ macOS 安装包: dist/$APP_NAME-macOS.app"
    ;;
  linux)
    # onefile 模式下 dist 只有单个可执行文件；生成 AppImage 需要 AppDir。
    # 简化: 直接把 onefile 二进制改名为 .AppImage 亦可运行(依赖系统 python3-gi)。
    mv -f "dist/$APP_NAME" "dist/$APP_NAME-Linux-x86_64.AppImage" 2>/dev/null \
      || mv -f "dist/$APP_NAME.exe" "dist/$APP_NAME-Linux-x86_64.AppImage"
    echo "✅ Linux 安装包: dist/$APP_NAME-Linux-x86_64.AppImage"
    ;;
esac
echo "📤 上传: gh release upload <tag> dist/*"
