#!/bin/bash

# =============================================================================
# RAG 學習助理專案 - 自動安裝腳本
# =============================================================================
# 
# 🎯 腳本用途：
# 1. 自動初始化 git submodules（modules/pdf_Cutting_TextReplaceImage）
# 2. 檢查系統環境（Python 版本）
# 3. 建立 Python 虛擬環境（可選）
# 4. 自動安裝所有必要套件
# 5. 建立 .env 設定檔模板
# 6. 提供完整的安裝後指引
#
# 💡 使用方式：
# 1. git clone <repository-url>
# 2. cd <project-directory>
# 3. chmod +x setup.sh
# 4. ./setup.sh
#
# 🚫 解決的問題：
# - 免除手動執行 git clone --recurse-submodules
# - 避免遺忘安裝某些套件
# - 統一開發環境設置
# - 新手友善的一鍵安裝
# =============================================================================

echo "🚀 正在設置 RAG 學習助理專案..."

# 檢查是否在 git repository 中
if [ ! -d ".git" ]; then
    echo "❌ 錯誤：請先 clone 此專案"
    echo "   git clone https://github.com/your-username/Ming-Chuan-University-2025-Computer-Science-and-Information-Engineering-Research-Group-3.git"
    exit 1
fi

# 初始化並更新 submodules
echo "📦 正在初始化 git submodules..."
git submodule init
git submodule update

# 檢查是否有 Python
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "❌ 錯誤：請先安裝 Python 3.7+"
    exit 1
fi

# 設置 Python 命令
if command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
    PIP_CMD=pip3
else
    PYTHON_CMD=python
    PIP_CMD=pip
fi

echo "🐍 檢測到 Python: $($PYTHON_CMD --version)"

# 建議建立虛擬環境
echo "💡 建議建立虛擬環境："
echo "   $PYTHON_CMD -m venv venv"
echo "   source venv/bin/activate  # Linux/macOS"

read -p "是否要自動建立並啟用虛擬環境? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🔨 建立虛擬環境..."
    $PYTHON_CMD -m venv venv
    source venv/bin/activate
    echo "✅ 虛擬環境已啟用"
fi

# 安裝套件
echo "📚 正在安裝必要套件..."
$PIP_CMD install langchain
$PIP_CMD install -qU "langchain[openai]"
$PIP_CMD install -qU langchain-openai
$PIP_CMD install -qU langchain-community
$PIP_CMD install faiss-cpu
$PIP_CMD install -qU pypdf
$PIP_CMD install unstructured
$PIP_CMD install python-dotenv
$PIP_CMD install fastapi uvicorn python-multipart
$PIP_CMD install PyJWT python-multipart email-validator pydantic[email]

# 建立 .env 模板檔案
if [ ! -f ".env" ]; then
    echo "📝 建立 .env 模板檔案..."
    cat > .env << EOF
# OpenAI API 設定
OPENAI_API_KEY="your_api_key_here"
OPENAI_BASE_URL=https://api.chatanywhere.org/v1

# JWT 密鑰（請改成你自己的隨機字串）
SECRET_KEY=your_secret_key_change_this_random_string

# 資料庫設定（SQLite 會自動建立檔案）
DATABASE_URL=sqlite:///./rag_users.db
EOF
    echo "✅ .env 模板檔案已建立，請編輯並填入你的 API 金鑰"
fi

echo "🎉 設置完成！"
echo ""
echo "📋 下一步："
echo "1. 編輯 .env 檔案，填入你的 OpenAI API 金鑰"
echo "2. 將學習資料放入 pdfFiles/ 目錄"
echo "3. 運行程式："
echo "   - 終端機版本：python Main.py"
echo "   - 網頁版本：python main_web.py"
echo "   - 網頁地址：http://localhost:8080"