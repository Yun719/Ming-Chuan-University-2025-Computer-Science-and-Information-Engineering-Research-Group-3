import os
import asyncio
import hashlib
import jwt
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional
from RAG_Helper import RAGHelper
from dotenv import load_dotenv
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import sqlite3
import uuid
from contextlib import asynccontextmanager


# 載入 .env 檔案
load_dotenv()   # 載入環境變數，像是 API 金鑰

# 安全設定
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this") # JWT 加密用
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30    #token 30 分鐘內有效


# 資料庫初始化
def init_database():
    """初始化 SQLite 資料庫"""
    conn = sqlite3.connect('rag_users.db')  # 連接到 SQLite 資料庫檔案（若不存在會自動建立
    cursor = conn.cursor()                  # 建立 cursor，後續用來操作 SQL

    # 使用者表（移除 email 欄位的唯一約束）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,    -- 資料表的自動遞增 ID
        user_id TEXT UNIQUE NOT NULL,            -- 使用者唯一 ID（UUID）
        username TEXT UNIQUE NOT NULL,           -- 使用者名稱（唯一）
        email TEXT,                              -- 電子信箱（可選，移除 UNIQUE 和 NOT NULL）
        password_hash TEXT NOT NULL,             -- 密碼的 SHA256 雜湊值（不儲存原文）
        created_at TIMESTAMP DEFAULT (datetime('now', 'localtime')), -- 註冊時間 使用本地時間
        is_active BOOLEAN DEFAULT TRUE,           -- 是否啟用（預設為啟用）
        is_admin BOOLEAN DEFAULT FALSE          -- 是否為管理員
    )
    ''')

    # 問答紀錄表（用於統計分析）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS questions_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,    -- 問答紀錄編號
        user_id TEXT NOT NULL,                   -- 哪位使用者問的（對應到 users.user_id）
        question TEXT NOT NULL,                  -- 問題內容
        answer TEXT NOT NULL,                    -- 回答內容
        sources_count INTEGER DEFAULT 0,         -- 有幾個來源段落
        created_at TIMESTAMP DEFAULT (datetime('now', 'localtime')), -- 問答發生時間
        response_time REAL,                      -- 回答耗時（秒）
        FOREIGN KEY(user_id) REFERENCES users(user_id) -- 關聯到 users 表
    )
    ''')

    conn.commit()   # 儲存這兩張表的建立動作
    conn.close()    # 關閉連線


# 應用程式生命週期管理，設定 FastAPI 應用程式的「生命週期事件（lifespan）」，在網站伺服器「啟動時」或「關閉時」要做的事。
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 啟動時執行
    init_database()
    yield
    # 關閉時執行（如果需要清理）


#這就是後端網站的主體，包含描述、靜態檔案（HTML, JS, CSS）和跨來源設定（CORS）。
app = FastAPI(
    title="RAG 問答系統",
    description="基於文件的智能問答系統（含帳號管理）",
    lifespan=lifespan
)

# 掛載 /static 用來提供 CSS、JS 檔案
app.mount("/static", StaticFiles(directory="static"), name="static")

# 設定 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        #允許任何來源都可以來存取這個 API（開放式）
    allow_credentials=True,     #允許攜帶登入憑證（像 token）
    allow_methods=["*"],        #允許所有 HTTP 方法：GET、POST、PUT、DELETE...
    allow_headers=["*"],        #允許任何 header（像 Authorization、Content-Type）
)

# 全域 RAG 實例
rag_instance: Optional[RAGHelper] = None    #Optional[RAGHelper] 表示它可以是 RAGHelper，也可以是 None（尚未初始化）

# 安全相關
security = HTTPBearer() #這是 FastAPI 用來處理 JWT token 驗證 的一個「安全機制」。


# 資料模型（移除電子郵件）
class UserRegister(BaseModel):
    username: str
    password: str
    # 移除 email: EmailStr

# 用來接收 登入表單資料
class UserLogin(BaseModel):
    username: str
    password: str

#用來回傳 登入成功後的資料
class Token(BaseModel):
    access_token: str   #	JWT token，前端會存起來
    token_type: str
    user_info: dict #	使用者資訊（字典形式）例如 {"user_id": ..., "username": ..., "email": ...}

# 用來接收使用者 提問時送來的資料
class QuestionRequest(BaseModel):
    question: str   #使用者輸入的問題內容（字串）

#用來回傳 AI 的回答給前端
class AnswerResponse(BaseModel):
    answer: str         #	AI 回答的文字內容
    sources: List[dict] #	引用到的教材段落（清單格式，每一筆是字典）

# 用來統一表示 API 回傳的狀態（成功/失敗）
class StatusResponse(BaseModel):
    status: str     #"success" 或 "error"
    message: str    #說明文字，例如「系統初始化成功」或「找不到檔案」

# 回傳給使用者的統計資訊（在 /stats API）
class UserStats(BaseModel):
    total_questions: int        #	總共問了幾次問題
    questions_today: int        #   今天問了幾次問題
    avg_response_time: float    #   每次回答平均花幾秒
    most_asked_topics: List[str]#   最常問的主題（字串清單）

# 聊天歷史紀錄
class ChatHistoryItem(BaseModel):
    question: str
    answer: str
    timestamp: str
    response_time: float

class ChatHistoryResponse(BaseModel):
    history: List[ChatHistoryItem]
    total_count: int

# 工具函數
#把使用者輸入的密碼「加密（雜湊）」起來，這樣就不會明文儲存在資料庫中
def hash_password(password: str) -> str:
    """密碼雜湊"""
    return hashlib.sha256(password.encode()).hexdigest()

#用來比對使用者輸入的密碼是否正確：
def verify_password(password: str, hashed: str) -> bool:
    """驗證密碼"""
    return hash_password(password) == hashed

#產生一個 JWT token，登入後前端就會收到這個：
def create_access_token(data: dict):
    """建立 JWT token ， token 30 分鐘後過期"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """取得目前使用者 拿到 token → 解開 → 取出 user_id → 傳回去"""
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        return user_id
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

#從資料庫撈出一個使用者的資料，可以用 user_id 或 username 查。
def get_user_from_db(user_id: str = None, username: str = None):
    """從資料庫取得使用者資料"""
    conn = sqlite3.connect('rag_users.db')
    cursor = conn.cursor()

    if user_id:
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    elif username:
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    else:
        return None

    user = cursor.fetchone()
    conn.close()
    return user

#把使用者提問與系統回答的紀錄存進 questions_log 資料表中
def log_question(user_id: str, question: str, answer: str, sources_count: int, response_time: float):
    """記錄問答到資料庫"""
    conn = sqlite3.connect('rag_users.db')
    cursor = conn.cursor()
    cursor.execute('''
                   INSERT INTO questions_log (user_id, question, answer, sources_count, response_time)
                   VALUES (?, ?, ?, ?, ?)
                   ''', (user_id, question, answer, sources_count, response_time))
    conn.commit()
    conn.close()

def verify_admin(user_id: str):
    user = get_user_from_db(user_id=user_id)
    if not user or not user[7]:  # db_user[7] 是 is_admin
        raise HTTPException(status_code=403, detail="您沒有管理員權限")

# API 端點

# 顯示首頁，這是網站的首頁 API，會回傳 static/index.html 給瀏覽器載入。
@app.get("/", response_class=FileResponse)
async def serve_index():
    return FileResponse("static/index.html")


# 使用者註冊（移除電子郵件）
@app.post("/register")
async def register_user(user: UserRegister):
    """使用者註冊"""
    conn = sqlite3.connect('rag_users.db')
    cursor = conn.cursor()

    # 檢查使用者是否已存在（只檢查 username）
    cursor.execute("SELECT * FROM users WHERE username = ?", (user.username,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="使用者名稱已存在")

    # 建立新使用者（不包含 email）
    user_id = str(uuid.uuid4()) #產生 user_id（用 uuid）
    password_hash = hash_password(user.password)    #密碼加密

    cursor.execute('''
                   INSERT INTO users (user_id, username, password_hash)
                   VALUES (?, ?, ?)
                   ''', (user_id, user.username, password_hash))

    conn.commit()
    conn.close()

    return {"message": "註冊成功", "user_id": user_id}  #傳註冊成功訊息：


# 使用者登入，驗證使用者帳密，若正確，就回傳 JWT token 和使用者資訊。
@app.post("/login", response_model=Token)
async def login_user(user: UserLogin):
    """使用者登入"""
    db_user = get_user_from_db(username=user.username)

    #   比對密碼是否正確
    if not db_user or not verify_password(user.password, db_user[4]):  # db_user[4] 是 password_hash
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="帳號或密碼錯誤"
        )
    #   若正確 → 建立 JWT token：
    access_token = create_access_token(data={"sub": db_user[1]})  # db_user[1] 是 user_id

    # 回傳登入成功訊息（email 可能為 None）：
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_info": {
            "user_id": db_user[1],
            "username": db_user[2],
            "email": db_user[3] if db_user[3] else "",  # 如果沒有 email 就回傳空字串
            "is_admin": bool(db_user[7])
        }
    }


# 讓前端查詢「我是誰」用的，會回傳目前登入使用者的基本資料。
@app.get("/me")
async def get_current_user_info(current_user: str = Depends(get_current_user)):
    """取得目前登入使用者的資訊"""
    db_user = get_user_from_db(user_id=current_user)    #FastAPI 會自動解析 Authorization: Bearer <token> header，調用 get_current_user() → 解碼 JWT → 拿到 user_id
    if not db_user:
        raise HTTPException(status_code=404, detail="使用者不存在")

    return {
        "user_id": db_user[1],
        "username": db_user[2],
        "email": db_user[3] if db_user[3] else "",  # 如果沒有 email 就回傳空字串
        "created_at": db_user[5],
        "is_active": db_user[6],
        "is_admin": db_user[7]
    }


# 系統初始化（需要登入）
@app.post("/initialize")
async def initialize_system(current_user: str = Depends(get_current_user)):
    """初始化 RAG 系統"""
    global rag_instance

    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(status_code=500, detail="請在 .env 檔案中設定 OPENAI_API_KEY")

    if not os.path.exists("./pdfFiles"):
        raise HTTPException(status_code=500, detail="找不到 pdfFiles 資料夾")

    try:
        rag_instance = RAGHelper(pdf_folder="./pdfFiles", chunk_size=300, chunk_overlap=50)
        await rag_instance.load_and_prepare(['.pdf', '.txt', '.docx', '.md', '.csv'])
        rag_instance.setup_retrieval_chain()

        return StatusResponse(
            status="success",
            message="RAG 系統初始化完成"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"系統初始化失敗：{str(e)}")


# 問答功能（需要登入）
@app.post("/ask", response_model=AnswerResponse)
async def ask_question(request: QuestionRequest, current_user: str = Depends(get_current_user)):
    """回答問題（需登入）"""
    global rag_instance

    if not rag_instance:
        raise HTTPException(status_code=400, detail="系統尚未初始化")

    try:
        start_time = datetime.now()
        answer, sources = rag_instance.ask(request.question)
        response_time = (datetime.now() - start_time).total_seconds()

        # 格式化來源資訊
        formatted_sources = []
        for doc in sources:
            source_info = {
                "source": os.path.basename(str(doc.metadata.get('source', '未知來源'))),
                "page": doc.metadata.get('page', 0) + 1,
                "content_preview": doc.page_content[:150] + "..." if len(doc.page_content) > 150 else doc.page_content
            }
            formatted_sources.append(source_info)

        # 記錄問答
        log_question(current_user, request.question, answer, len(sources), response_time)

        return AnswerResponse(answer=answer, sources=formatted_sources)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"回答問題時發生錯誤：{str(e)}")


# 使用者統計（需要登入），回傳目前登入的使用者在系統中的個人問答統計資料。取得目前登入者的 user_id（透過 get_current_user()）
@app.get("/stats", response_model=UserStats)
async def get_user_stats(current_user: str = Depends(get_current_user)):
    """取得使用者問答統計"""
    conn = sqlite3.connect('rag_users.db')
    cursor = conn.cursor()

    # 總問題數
    cursor.execute("SELECT COUNT(*) FROM questions_log WHERE user_id = ?", (current_user,))
    total_questions = cursor.fetchone()[0]

    # 今日問題數
    cursor.execute('''
                   SELECT COUNT(*)
                   FROM questions_log
                   WHERE user_id = ? AND DATE (created_at) = DATE ('now')
                   ''', (current_user,))
    questions_today = cursor.fetchone()[0]

    # 平均回應時間
    cursor.execute("SELECT AVG(response_time) FROM questions_log WHERE user_id = ?", (current_user,))
    avg_response_time = cursor.fetchone()[0] or 0.0

    # 取得最近 50 筆問題
    cursor.execute('''
                   SELECT question
                   FROM questions_log
                   WHERE user_id = ?
                   ORDER BY created_at DESC LIMIT 50
                   ''', (current_user,))
    recent_questions = cursor.fetchall()

    conn.close()

    # 統計關鍵字出現次數（簡單字詞分析）
    keyword_counts = {}
    keywords_to_check = ["TCP", "函數", "陣列", "銘傳", "學分", "網路", "電腦", "二進位", "資料庫"]

    for (question,) in recent_questions:
        for keyword in keywords_to_check:
            if keyword in question:
                keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1

    # 排序最多的前幾名
    sorted_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)
    most_asked_topics = [kw for kw, count in sorted_keywords[:3]]

    return UserStats(
        total_questions=total_questions,
        questions_today=questions_today,
        avg_response_time=round(avg_response_time, 2),
        most_asked_topics = most_asked_topics
    )


# 管理員統計（可擴展）
@app.get("/admin/stats")
async def get_admin_stats(current_user: str = Depends(get_current_user)):
    """管理員統計（需要擴展權限檢查）"""
    verify_admin(current_user)  #檢查是否為管理員

    conn = sqlite3.connect('rag_users.db')
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")    #SELECT COUNT(*) FROM users
    total_users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM questions_log")    # 問題總數
    total_questions = cursor.fetchone()[0]

    cursor.execute('''                              ---今日所有人總共問了幾題
                   SELECT COUNT(*)
                   FROM questions_log
                   WHERE DATE (created_at) = DATE ('now')
                   ''')
    questions_today = cursor.fetchone()[0]

    conn.close()

    return {
        "total_users": total_users,
        "total_questions": total_questions,
        "questions_today": questions_today
    }


@app.get("/status")
async def get_status():
    """取得系統狀態"""
    global rag_instance
    return StatusResponse(
        status="ready" if rag_instance else "not_initialized",
        message="系統已就緒" if rag_instance else "系統尚未初始化"
    )


# API 端點：獲取聊天歷史
@app.get("/chat/history", response_model=ChatHistoryResponse)
async def get_chat_history(
        limit: int = 50,  # 預設載入最近 50 筆
        offset: int = 0,  # 分頁偏移
        current_user: str = Depends(get_current_user)
):
    """獲取使用者的聊天歷史紀錄"""
    conn = sqlite3.connect('rag_users.db')
    cursor = conn.cursor()

    # 獲取總筆數
    cursor.execute("SELECT COUNT(*) FROM questions_log WHERE user_id = ?", (current_user,))
    total_count = cursor.fetchone()[0]

    # 獲取歷史紀錄（按時間倒序，最新的在前面）
    cursor.execute('''
                   SELECT question, answer, created_at, response_time
                   FROM questions_log
                   WHERE user_id = ?
                   ORDER BY created_at DESC
                    LIMIT ?
                   OFFSET ?
                   ''', (current_user, limit, offset))

    records = cursor.fetchall()
    conn.close()

    # 格式化歷史紀錄
    history = []
    for record in records:
        history.append(ChatHistoryItem(
            question=record[0],
            answer=record[1],
            timestamp=record[2],
            response_time=record[3]
        ))

    return ChatHistoryResponse(
        history=history,
        total_count=total_count
    )

# 新增 API 端點：清除聊天歷史
@app.delete("/chat/history")
async def clear_chat_history(current_user: str = Depends(get_current_user)):
    """清除使用者的聊天歷史紀錄"""
    conn = sqlite3.connect('rag_users.db')
    cursor = conn.cursor()

    cursor.execute("DELETE FROM questions_log WHERE user_id = ?", (current_user,))
    deleted_count = cursor.rowcount

    conn.commit()
    conn.close()

    return {"message": f"已清除 {deleted_count} 筆歷史紀錄"}

if __name__ == "__main__":
    import uvicorn

    print("🚀 啟動 RAG 網站服務（含帳號系統）...")
    print("📱 網站網址：http://localhost:8080")
    print("📚 API 文件：http://localhost:8080/docs")
    print("📁 請確保 pdfFiles 資料夾中有要處理的檔案")
    print("🔑 請在 .env 檔案中設定 SECRET_KEY 和 OPENAI_API_KEY")
    uvicorn.run(app, host="0.0.0.0", port=8080)