#import asyncio
import glob  # 用來找多個檔案
import os
from pathlib import Path
#langchain 相關套件
from langchain.text_splitter import RecursiveCharacterTextSplitter  #切割文字
from langchain_community.vectorstores import FAISS                  # FAISS : Facebook 開發的向量資料庫，用來做快速相似度搜尋。
from langchain_openai import OpenAIEmbeddings, ChatOpenAI           # embeddings 用來將文字轉換成向量
from langchain.chains import create_retrieval_chain                 #建立 RAG 架構中的「檢索＋問答」流程。
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

#可以讀取不同的檔案格式
from langchain_community.document_loaders import (
    PyPDFLoader, TextLoader, CSVLoader,
    UnstructuredWordDocumentLoader,
    UnstructuredMarkdownLoader,
)

class RAGHelper:
    def __init__(self, pdf_folder, chunk_size=300, chunk_overlap=50):    #__init__ 是 python 的建構子
        self.pdf_folder = pdf_folder    # 儲存 PDF 檔案的 PATH
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.vectorstore = None
        self.retrieval_chain = None

    def get_loader(self,path: str):
        ext = Path(path).suffix.lower()
        if ext == ".pdf":
            return PyPDFLoader(path)
        elif ext == ".txt":
            return TextLoader(path, encoding="utf-8")
        elif ext == ".docx":
            return UnstructuredWordDocumentLoader(path)
        elif ext == ".md":
            return UnstructuredMarkdownLoader(path)
        elif ext == ".csv":
            return CSVLoader(path)
        else:
            raise ValueError(f"不支援的檔案類型: {ext}")

    async def load_any_file_async(self,path: str):
        loader = self.get_loader(path)
        # 有些 loader 是 async 的，有些不是
        if hasattr(loader, "alazy_load"):
            pages = []
            async for page in loader.alazy_load():
                pages.append(page)
            return pages
        else:
            return loader.load()  # 同步方式載入

    #切割檔案
    def _split_documents(self, documents):
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", "。", ".", " ", ""],
            length_function=len,
        )
        return splitter.split_documents(documents)

    def _build_vectorstore(self, documents):
        print(f"建立向量資料庫... 共 {len(documents)} 個段落")
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small") # 或是 model="text-embedding-3-large"
        self.vectorstore = FAISS.from_documents(documents, embeddings)

    async def load_and_prepare(self, file_extensions=None):
        print("開始載入檔案...")

        if os.path.exists("my_faiss_index"):    #如果本地有向量資料庫，載入本地的向量資料庫
            print("已偵測到現有向量資料庫，直接載入...")
            self.vectorstore = FAISS.load_local(
                "my_faiss_index",
                OpenAIEmbeddings(model="text-embedding-3-small"),
                allow_dangerous_deserialization=True
            )

        else:

            """
            載入並準備文件
            file_extensions: 要載入的檔案副檔名列表，例如 ['.pdf', '.txt', '.docx']
            如果為 None，則只載入 PDF 檔案（保持原有行為）
            """
            print("正在建立和讀取向量資料庫")

            if file_extensions is None:
                file_extensions = ['.pdf']  # 預設只載入 PDF

            all_chunks = []

            # 根據指定的副檔名載入檔案
            for ext in file_extensions:
                pattern = f"*{ext}"
                file_paths = glob.glob(os.path.join(self.pdf_folder, pattern))

                for path in file_paths:
                    try:
                        print(f"讀取中: {os.path.basename(path)}")
                        pages = await self.load_any_file_async(path)  # 讀檔案
                        chunks = self._split_documents(pages)  # 切割檔案
                        all_chunks.extend(chunks)  # 加入 list
                        print(f" {os.path.basename(path)} 分割完成，共 {len(chunks)} 段")
                    except Exception as e:
                        print(f"載入 {os.path.basename(path)} 時發生錯誤: {e}")

            print(f"所有檔案段落總數：{len(all_chunks)}")

            if len(all_chunks) == 0:
                raise ValueError("沒有成功載入任何文件")

            self._build_vectorstore(all_chunks)  # 將文字轉成向量，並建立向量資料庫
            self.vectorstore.save_local("my_faiss_index")   #將向量資料庫存到本地

    def setup_retrieval_chain(self):
        if not self.vectorstore:
            raise ValueError("請先執行 load_and_prepare()")

        llm = ChatOpenAI(model="gpt-4o", temperature=0.3)
        # 創建檢索器
        retriever = self.vectorstore.as_retriever(
            search_kwargs={"k": 5}  # 只取前5個最相關的段落
        )
        # 創建提示詞模板
        system_prompt = (
            "你是一個基於 RAG 系統的家教。請參考以下提供的內容來回答問題。"
            "用詞上請多使用正向鼓勵的詞語，並基於現有問題延伸出更多相關的問題。"
            "請針對問題舉出簡單好懂的比喻和例子。"
            "如果不知道如何回答問題，還請說出來。"
            "請用繁體中文回答。\n\n"
            "{context}"
        )
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}"),
        ])
        # 創建文檔合併鏈
        question_answer_chain = create_stuff_documents_chain(llm, prompt)
        # 創建檢索鏈
        self.retrieval_chain = create_retrieval_chain(retriever, question_answer_chain)

    def ask(self, query):
        if not self.retrieval_chain:
            raise ValueError("請先執行 setup_qa_chain()")
        try:
            result = self.retrieval_chain.invoke({"input": query})    #將使用者的問題傳給問答鏈，鏈內部會檢索並將檢索到的段落和問題交給大語言模型
            return result["answer"], result["context"]     # result["answer"] 是 語言模型給的答案，result["context"]  是檢索到的原始段落
        except Exception as e:
            if "max_tokens_per_request" in str(e):
                print("內容過長，嘗試使用較短的上下文...")
                self.setup_retrieval_chain_with_shorter_context()
                result = self.retrieval_chain.invoke({"input": query})
                return result["answer"], result["context"]
            else:
                raise e

    def setup_retrieval_chain_with_shorter_context(self):
        """設置更短上下文的檢索鏈"""
        if not self.vectorstore:
            raise ValueError("請先執行 load_and_prepare()")

        llm = ChatOpenAI(model="gpt-4o", temperature=0.0)
        # 更嚴格的檢索配置
        retriever = self.vectorstore.as_retriever(
            search_kwargs={"k": 3}
        )
        system_prompt = (
            "你是一個問答助手。基於以下提供的內容來回答問題。"
            "如果內容中沒有相關資訊，請說「根據提供的資料無法回答這個問題」。"
            "請用繁體中文簡潔回答。\n\n"
            "{context}"
        )
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}"),
        ])
        question_answer_chain = create_stuff_documents_chain(llm, prompt)
        self.retrieval_chain = create_retrieval_chain(retriever, question_answer_chain)