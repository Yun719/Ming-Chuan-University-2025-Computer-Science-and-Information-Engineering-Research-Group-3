# 銘傳大學 2025 資訊工程學系 專研第 3 組
一個基於 RAG 系統的計算機概論學習助理專案

## 🚀 快速安裝（推薦）

### 方法一：一鍵安裝腳本
```bash
# 1. Clone 專案（不需要 --recurse-submodules）
git clone https://github.com/your-username/Ming-Chuan-University-2025-Computer-Science-and-Information-Engineering-Research-Group-3.git
cd Ming-Chuan-University-2025-Computer-Science-and-Information-Engineering-Research-Group-3

# 2. 運行自動安裝腳本
# Linux/macOS
chmod +x setup.sh
./setup.sh

# Windows
setup.bat
```

腳本會自動處理：
- ✅ Git submodules 初始化
- ✅ Python 環境檢查
- ✅ 虛擬環境建立（可選）
- ✅ 所有套件安裝
- ✅ .env 設定檔模板建立

### 方法二：傳統安裝
如果你不想使用自動腳本，可以依照以下步驟：

```bash
# Clone 專案並初始化 submodules
git clone --recurse-submodules https://github.com/your-username/Ming-Chuan-University-2025-Computer-Science-and-Information-Engineering-Research-Group-3.git
```

## 📦 手動安裝必要套件
為避免套件因版本互相干擾，建議使用虛擬環境安裝
```bash
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
```
# .env 檔案
由於 API 金鑰需保密請參考這一影片 : https://youtu.be/-yf2nkZeiDU?si=KKhdLM3zw1pAVXJr 申請一個 API 金鑰  

並在根目錄中新增 ".env" 檔案，在裡面填上： 
```python
OPENAI_API_KEY="API_KEY"
OPENAI_BASE_URL=https://api.chatanywhere.org/v1

# JWT 密鑰（請改成你自己的隨機字串）
SECRET_KEY=隨機字串

# 資料庫設定（SQLite 會自動建立檔案）
DATABASE_URL=sqlite:///./rag_users.db
```
其中 API_KEY 請改成申請到的金鑰  

SECRET_KEY 請加上隨機的字串，比如 `This-kid-aspires-to-be-homeless`
# 檔案說明：
RAG_Helper.py：RAG 系統的核心，負責讀取檔案、切割、轉換向量、處理問題等等  

Main.py：在終端機輸入問題，列出檢索到語意最接近的段落和語言模型的回答  

main_web.py：網頁版本的後端程式，若目錄中沒有資料庫檔案，會生成 `rag_users.db`，需下載 [DB Browser for SQLite](https://sqlitebrowser.org/) 打開該檔案  

static/：網頁版本的前端程式，包含 `index.html` 和 `style.css`  

pdfFiles：RAG 系統德資料來源，目前使用 [這篇文章](https://hackmd.io/@110FJU-MIIA/Sy2xnSE8K) 的資料做測試，未來會使用課本教材作為資料
