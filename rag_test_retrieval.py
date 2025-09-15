#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG 檢索測試程式
用於測試文件檢索功能和圖片匹配邏輯，不涉及 LLM
"""

import os
import json
import asyncio
from pathlib import Path
from MultiTurnRAGHelper import MultiTurnRAGHelper
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()


class RAGTester:
    def __init__(self, pdf_folder="./pdfFiles", chunk_size=300, chunk_overlap=50):
        self.pdf_folder = pdf_folder
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.rag_helper = None
        self.chart_data = {}
        self.current_user_id = "test_user"  # 用於測試的固定用戶ID

    async def initialize(self):
        """初始化 RAG 系統"""
        print("🔧 正在初始化 RAG 系統...")

        if not os.getenv("OPENAI_API_KEY"):
            print("❌ 請在 .env 文件中設定 OPENAI_API_KEY")
            return False

        if not os.path.exists(self.pdf_folder):
            print(f"❌ 找不到 {self.pdf_folder} 資料夾")
            return False

        try:
            # 初始化 RAG Helper
            self.rag_helper = MultiTurnRAGHelper(
                pdf_folder=self.pdf_folder,
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap
            )

            # 載入並準備文件（使用 await）
            print("📚 載入文件...")
            await self.rag_helper.load_and_prepare(['.pdf', '.txt', '.docx', '.md', '.csv'])

            # 設定檢索鏈
            # print("🔗 設定檢索鏈...")
            self.rag_helper.setup_retrieval_chain()

            # 載入圖表資訊
            self.load_chart_metadata()

            print("✅ RAG 系統初始化完成")
            return True

        except Exception as e:
            print(f"❌ 初始化失敗：{str(e)}")
            return False

    def load_chart_metadata(self):
        """載入圖表元資料"""
        chart_info_file = Path(f"{self.pdf_folder}/chart_metadata.json")

        if chart_info_file.exists():
            try:
                with open(chart_info_file, 'r', encoding='utf-8') as f:
                    self.chart_data = json.load(f)
                print(f"📊 載入了 {len(self.chart_data)} 個圖表的元資料")
            except Exception as e:
                print(f"⚠️ 載入圖表資訊時發生錯誤：{e}")
                self.chart_data = {}
        else:
            print("⚠️ 未找到 chart_metadata.json 文件")
            self.chart_data = {}

    def print_chat_history(self, user_id: str):
        """列印指定用戶的聊天歷史"""
        if not self.rag_helper:
            print("❌ RAG 系統未初始化")
            return

        # 取得聊天歷史
        history = self.rag_helper.get_conversation_history(user_id)

        if not history:
            print(f"📝 用戶 {user_id} 暫無聊天記錄")
            return

        print(f"\n📜 用戶 {user_id} 的聊天歷史：")
        print("=" * 60)

        for i, msg in enumerate(history, 1):
            if msg["type"] == "user":
                print(f"👤 用戶 ({i // 2 + 1})：{msg['content']}")
            elif msg["type"] == "assistant":
                print(f"🤖 助手 ({i // 2 + 1})：{msg['content'][:200]}{'...' if len(msg['content']) > 200 else ''}")
            print("-" * 40)

    def get_formatted_chat_history(self, user_id: str) -> str:
        """取得格式化的聊天歷史字串（模擬 MultiTurnRAGHelper 中的格式）"""
        if not self.rag_helper or user_id not in self.rag_helper.conversation_memory:
            return ""

        memory = self.rag_helper.conversation_memory[user_id]
        chat_history = memory.chat_memory.messages

        history_text = ""
        for message in chat_history[-self.rag_helper.memory_window * 2:]:
            if hasattr(message, '__class__'):
                if message.__class__.__name__ == 'HumanMessage':
                    history_text += f"用戶: {message.content}\n"
                elif message.__class__.__name__ == 'AIMessage':
                    history_text += f"助手: {message.content}\n"

        return history_text

    def retrieve_documents(self, query, k=5, similarity_threshold=0.45):
        """
        檢索相關文件，並根據相似度門檻過濾結果

        Args:
            query (str): 查詢字串
            k (int): 檢索數量
            similarity_threshold (float): 相似度門檻 (0.0-1.0)，低於此值的結果會被過濾

        Returns:
            list: 過濾後的文件列表，格式為 [doc, doc, ...] (只返回文檔對象)
        """
        if not self.rag_helper:
            print("❌ RAG 系統未初始化")
            return []

        try:
            # 方法1: 使用 similarity_search_with_score (推薦)
            docs_with_scores = self.rag_helper.vectorstore.similarity_search_with_score(
                query, k=k
            )

            # 根據相似度門檻過濾
            filtered_docs = []
            print(f"🔍 檢索到 {len(docs_with_scores)} 個結果，應用相似度門檻 {similarity_threshold}")

            for doc, score in docs_with_scores:
                similarity = 1.0 / (1.0 + score)  # 或根據實際情況調整

                print(f"📄 相似度: {similarity:.4f}, 原始分數: {score:.4f}")

                if similarity >= similarity_threshold:
                    filtered_docs.append(doc)  # 只添加文檔對象
                    print(f"   ✅ 通過門檻，保留此文件")
                else:
                    print(f"   ❌ 低於門檻 {similarity_threshold}，過濾此文件")

            if not filtered_docs:
                print(f"⚠️ 沒有文件通過相似度門檻 {similarity_threshold}")
                return []

            # 打印結果
            print(f"📊 過濾後保留 {len(filtered_docs)} 個文件")

            return filtered_docs

        except Exception as e:
            print(f"❌ 檢索失敗：{str(e)}")
            return []

    def _filter_by_manual_similarity(self, query, docs, threshold):
        """
        手動計算相似度並過濾文件（當向量資料庫不支援 with_score 時使用）
        """
        try:
            from sentence_transformers import SentenceTransformer
            import numpy as np
            from sklearn.metrics.pairwise import cosine_similarity

            # 載入嵌入模型（應該使用與索引相同的模型）
            model = SentenceTransformer('all-MiniLM-L6-v2')  # 替換為你使用的模型

            # 計算查詢的嵌入
            query_embedding = model.encode([query])

            filtered_docs = []

            for doc in docs:
                # 計算文件內容的嵌入
                doc_embedding = model.encode([doc.page_content])

                # 計算餘弦相似度
                similarity = cosine_similarity(query_embedding, doc_embedding)[0][0]

                print(f"📄 手動計算相似度: {similarity:.4f}")

                if similarity >= threshold:
                    filtered_docs.append(doc)
                    print(f"   ✅ 通過門檻，保留此文件")
                else:
                    print(f"   ❌ 低於門檻 {threshold}，過濾此文件")

            return filtered_docs

        except ImportError:
            print("⚠️ 缺少必要的套件，無法手動計算相似度")
            return docs  # 返回未過濾的結果

    def find_related_charts(self, docs, max_charts=1):
        """找出與檢索文件相關的圖表 (會印出匹配的關鍵字方便 debug)"""
        related_charts = []

        if not self.chart_data:
            return related_charts

        # 檢查前幾個檢索結果
        for doc in docs[:5]:
            source_content = doc.page_content.lower()

            # 遍歷所有圖表
            for chart_id, chart_info in self.chart_data.items():
                if 'generated_description' in chart_info:
                    description = chart_info['generated_description'].lower()
                    caption = chart_info.get('original_caption', '').lower()

                    # 檢查相關性（三個條件任一符合即可）
                    is_relevant = False
                    relevance_reason = ""

                    # 條件1: 描述關鍵字匹配（取前10個字）
                    desc_words = [word for word in description.split()[:10] if len(word) >= 2]
                    matched_desc_words = [word for word in desc_words if word in source_content]

                    if matched_desc_words:
                        is_relevant = True
                        relevance_reason = f"描述關鍵字匹配: {', '.join(matched_desc_words)}"
                        print(f"[DEBUG] 圖表 {chart_id} - 描述關鍵字命中: {matched_desc_words}")

                    # 條件2: 標題關鍵字匹配
                    elif caption:
                        caption_words = [word for word in caption.split() if len(word) >= 5]
                        matched_caption_words = [word for word in caption_words if word in source_content]

                        if matched_caption_words:
                            is_relevant = True
                            relevance_reason = f"標題關鍵字匹配: {', '.join(matched_caption_words)}"
                            print(f"[DEBUG] 圖表 {chart_id} - 標題關鍵字命中: {matched_caption_words}")

                    """
                    # 條件3: 檔案來源匹配
                    elif chart_info.get('source_file', '').replace('.pdf', '') in doc.metadata.get('source', ''):
                        is_relevant = True
                        relevance_reason = "檔案來源匹配"
                        print(f"[DEBUG] 圖表 {chart_id} - 檔案來源匹配")
                    """

                    if is_relevant:
                        # 避免重複添加同一張圖表
                        if not any(chart['chart_id'] == chart_id for chart in related_charts):
                            chart_path = f"static/charts/{chart_id}.jpg"
                            if os.path.exists(chart_path):
                                related_charts.append({
                                    'chart_id': chart_id,
                                    'image_path': chart_path,
                                    'caption': chart_info.get('original_caption', ''),
                                    'description': chart_info.get('generated_description', ''),
                                    'chart_type': chart_info.get('chart_type', ''),
                                    'chart_number': chart_info.get('chart_number', ''),
                                    'source_file': chart_info.get('source_file', ''),
                                    'relevance_reason': relevance_reason
                                })

                        # 限制圖表數量
                        if len(related_charts) >= max_charts:
                            break

            if len(related_charts) >= max_charts:
                break

        return related_charts

    def test_query_with_memory(self, query, use_memory=True, k=5, similarity_threshold=0.45):
        """
        測試帶記憶的查詢功能，並顯示 prompt 中的 chat-history
        """
        print(f"\n{'=' * 60}")
        print(f"🔍 測試查詢（{'帶記憶' if use_memory else '無記憶'}）：{query}")
        print(f"🎯 相似度門檻：{similarity_threshold}")
        print(f"{'=' * 60}")

        if use_memory:
            # 使用帶記憶的查詢
            try:
                print(f"\n💭 查詢前的聊天歷史：")
                print("-" * 50)

                # 取得格式化的聊天歷史
                chat_history = self.get_formatted_chat_history(self.current_user_id)
                if chat_history.strip():
                    print(chat_history)
                else:
                    print("（暫無聊天記錄）")

                # 進行帶記憶的查詢
                answer, sources = self.rag_helper.ask_with_memory(query, self.current_user_id)

                print(f"\n🤖 AI 回答：")
                print("-" * 50)
                print(answer)

                print(f"\n📚 使用的文件來源（共 {len(sources)} 個）：")
                print("-" * 50)

                for i, doc in enumerate(sources, 1):
                    source_file = os.path.basename(str(doc.metadata.get('source', '未知來源')))
                    page_info = doc.metadata.get('page', None)
                    if page_info is not None:
                        page = page_info + 1
                        page_str = f"第 {page} 頁"
                    else:
                        page_str = "頁碼未知"

                    content_preview = doc.page_content[:200] if len(doc.page_content) > 200 else doc.page_content

                    print(f"\n{i}. 來源：{source_file} ({page_str})")
                    print(f"   內容預覽：{content_preview}")

                # 查找相關圖表
                related_charts = self.find_related_charts(sources)

                if related_charts:
                    print(f"\n🖼️ 找到 {len(related_charts)} 張相關圖表：")
                    print("-" * 50)

                    for i, chart in enumerate(related_charts, 1):
                        print(f"\n{i}. 圖表 ID：{chart['chart_id']}")
                        print(f"   圖表編號：{chart['chart_number']}")
                        print(f"   標題：{chart['caption']}")
                        print(f"   類型：{chart['chart_type']}")
                        print(f"   來源檔案：{chart['source_file']}")
                        print(f"   匹配原因：{chart['relevance_reason']}")
                        print(f"   圖片路徑：{chart['image_path']}")
                        print(f"   描述：{chart['description'][:150]}...")
                else:
                    print("\n🖼️ 未找到相關圖表")

            except Exception as e:
                print(f"❌ 帶記憶查詢失敗：{str(e)}")
        else:
            # 使用原本的無記憶查詢方式
            self.test_query(query, k, similarity_threshold)

    def test_query(self, query, k=5, similarity_threshold=0.45):
        """
        測試單個查詢（更新版本，包含相似度門檻）
        """
        print(f"\n{'=' * 60}")
        print(f"🔍 測試查詢：{query}")
        print(f"🎯 相似度門檻：{similarity_threshold}")
        print(f"{'=' * 60}")

        # 檢索文件（使用相似度門檻）
        docs = self.retrieve_documents(query, k, similarity_threshold)

        if not docs:
            print("❌ 未檢索到符合門檻的相關文件")
            print("💡 建議：降低 similarity_threshold 或檢查查詢內容")
            return

        print(f"\n📚 檢索到 {len(docs)} 個符合門檻的文件段落：")
        print("-" * 50)

        # 顯示檢索結果（其餘代碼保持不變）
        for i, doc in enumerate(docs, 1):
            source_file = os.path.basename(str(doc.metadata.get('source', '未知來源')))
            page_info = doc.metadata.get('page', None)
            if page_info is not None:
                page = page_info + 1
                page_str = f"第 {page} 頁"
            else:
                page_str = "頁碼未知"

            content_preview = doc.page_content[:200] if len(doc.page_content) > 200 else doc.page_content

            print(f"\n{i}. 來源：{source_file} ({page_str})")
            print(f"   內容預覽：{content_preview}")

        # 查找相關圖表
        related_charts = self.find_related_charts(docs)

        if related_charts:
            print(f"\n🖼️ 找到 {len(related_charts)} 張相關圖表：")
            print("-" * 50)

            for i, chart in enumerate(related_charts, 1):
                print(f"\n{i}. 圖表 ID：{chart['chart_id']}")
                print(f"   圖表編號：{chart['chart_number']}")
                print(f"   標題：{chart['caption']}")
                print(f"   類型：{chart['chart_type']}")
                print(f"   來源檔案：{chart['source_file']}")
                print(f"   匹配原因：{chart['relevance_reason']}")
                print(f"   圖片路徑：{chart['image_path']}")
                print(f"   描述：{chart['description'][:150]}...")
        else:
            print("\n🖼️ 未找到相關圖表")

    async def interactive_test(self):
        """互動式測試模式"""
        print("\n" + "=" * 60)
        print("🎯 RAG 檢索測試程式 - 互動模式")
        print("=" * 60)
        print("輸入 'quit' 或 'exit' 結束程式")
        print("輸入 'help' 查看幫助")
        print("輸入 'history' 查看聊天歷史")
        print("輸入 'clear' 清除聊天記錄")
        print("輸入 '!<問題>' 進行無記憶查詢（例如: !什麼是演算法）")

        while True:
            try:
                user_input = input("\n請輸入測試問題：").strip()

                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 再見！")
                    break
                elif user_input.lower() == 'help':
                    self.show_help()
                    continue
                elif user_input.lower() == 'history':
                    self.print_chat_history(self.current_user_id)
                    continue
                elif user_input.lower() == 'clear':
                    success = self.rag_helper.clear_memory(self.current_user_id)
                    if success:
                        print("✅ 聊天記錄已清除")
                    else:
                        print("⚠️ 沒有找到需要清除的記錄")
                    continue
                elif not user_input:
                    print("⚠️ 請輸入有效的問題")
                    continue

                # 檢查是否是無記憶查詢
                if user_input.startswith('!'):
                    query = user_input[1:]  # 去掉 ! 符號
                    if query:
                        self.test_query_with_memory(query, use_memory=False)
                    else:
                        print("⚠️ 請在 ! 後面輸入問題")
                else:
                    # 進行帶記憶的查詢
                    self.test_query_with_memory(user_input, use_memory=True)

            except KeyboardInterrupt:
                print("\n👋 程式已中斷")
                break
            except Exception as e:
                print(f"❌ 發生錯誤：{str(e)}")

    def show_help(self):
        """顯示幫助資訊"""
        print("\n📖 使用說明（省錢模式）：")
        print("- 輸入任何問題來測試帶記憶的文件檢索和圖表匹配")
        print("- 程式會顯示完整的 prompt 構建過程，但不會發送給 LLM")
        print("- 輸入 '!<問題>' 進行無記憶查詢（例如: !什麼是演算法）")
        print("- 輸入 'history' 查看目前的聊天歷史")
        print("- 輸入 'clear' 清除聊天記錄")
        print("- 輸入 'quit' 或 'exit' 結束程式")
        print("- 輸入 'help' 查看此幫助")
        print("💰 省錢模式：不消耗 OpenAI API 配額")


async def main():
    """主程式"""
    print("🚀 啟動 RAG 檢索測試程式")

    # 創建測試器實例
    tester = RAGTester()

    # 初始化系統（使用 await）
    success = await tester.initialize()
    if not success:
        print("❌ 系統初始化失敗，程式結束")
        return

    # 開始互動式測試
    await tester.interactive_test()


if __name__ == "__main__":
    # 使用 asyncio 運行主程式
    asyncio.run(main())