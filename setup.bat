@echo off
chcp 65001 >nul

REM =============================================================================
REM RAG 學習助理專案 - Windows 自動安裝腳本
REM =============================================================================
REM 
REM 🎯 腳本用途：
REM 1. 自動初始化 git submodules（modules/pdf_Cutting_TextReplaceImage）
REM 2. 檢查系統環境（Python 版本）
REM 3. 建立 Python 虛擬環境（可選）
REM 4. 自動安裝所有必要套件
REM 5. 建立 .env 設定檔模板
REM 6. 提供完整的安裝後指引
REM
REM 💡 使用方式：
REM 1. git clone <repository-url>
REM 2. cd <project-directory>
REM 3. setup.bat
REM
REM 🚫 解決的問題：
REM - 免除手動執行 git clone --recurse-submodules
REM - 避免遺忘安裝某些套件
REM - 統一開發環境設置
REM - 新手友善的一鍵安裝
REM =============================================================================

echo 🚀 正在設置 RAG 學習助理專案...

REM 檢查是否在 git repository 中
if not exist ".git" (
    echo ❌ 錯誤：請先 clone 此專案
    echo    git clone https://github.com/your-username/Ming-Chuan-University-2025-Computer-Science-and-Information-Engineering-Research-Group-3.git
    pause
    exit /b 1
)

REM 初始化並更新 submodules
echo 📦 正在初始化 git submodules...
git submodule init
git submodule update

REM 檢查是否有 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 錯誤：請先安裝 Python 3.7+
    pause
    exit /b 1
)

echo 🐍 檢測到 Python:
python --version

REM 建議建立虛擬環境
echo.
echo 💡 建議建立虛擬環境：
echo    python -m venv venv
echo    venv\Scripts\activate  # Windows

set /p choice="是否要自動建立並啟用虛擬環境? (y/n): "
if /i "%choice%"=="y" (
    echo 🔨 建立虛擬環境...
    python -m venv venv
    call venv\Scripts\activate
    echo ✅ 虛擬環境已啟用
)

REM 安裝套件
echo 📚 正在安裝必要套件...
pip install langchain
pip install -qU "langchain[openai]"
pip install -qU langchain-openai
pip install -qU langchain-community
pip install faiss-cpu
pip install -qU pypdf
pip install unstructured
pip install python-dotenv
pip install fastapi uvicorn python-multipart
pip install PyJWT python-multipart email-validator pydantic[email]

REM 建立 .env 模板檔案
if not exist ".env" (
    echo 📝 建立 .env 模板檔案...
    (
        echo # OpenAI API 設定
        echo OPENAI_API_KEY="your_api_key_here"
        echo OPENAI_BASE_URL=https://api.chatanywhere.org/v1
        echo.
        echo # JWT 密鑰（請改成你自己的隨機字串）
        echo SECRET_KEY=your_secret_key_change_this_random_string
        echo.
        echo # 資料庫設定（SQLite 會自動建立檔案）
        echo DATABASE_URL=sqlite:///./rag_users.db
    ) > .env
    echo ✅ .env 模板檔案已建立，請編輯並填入你的 API 金鑰
)

echo.
echo 🎉 設置完成！
echo.
echo 📋 下一步：
echo 1. 編輯 .env 檔案，填入你的 OpenAI API 金鑰
echo 2. 將學習資料放入 pdfFiles\ 目錄
echo 3. 運行程式：
echo    - 終端機版本：python Main.py
echo    - 網頁版本：python main_web.py
echo    - 網頁地址：http://localhost:8080

pause