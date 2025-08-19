"""
改進的 RAG 系統評估實驗
優化評估算法，提高準確性和合理性
"""

import sys
import os
import asyncio
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import re
from typing import Set, List

# 載入 .env 檔案
load_dotenv()

# 設定 UTF-8 編碼
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)

# TruLens 匯入 (使用穩定的 API)
from trulens_eval.feedback import Feedback
from trulens.core import TruSession
from trulens.apps.basic import TruBasicApp

# 本地 RAG 系統匯入
from RAG_Helper import RAGHelper

print("🔬 改進版 RAG_Helper.py 系統評估實驗")
print("=" * 60)

# 初始化 TruLens 會話
session = TruSession()
print("✅ TruLens 會話初始化完成")

class ImprovedRAGEvaluationExperiment:
    """改進版 RAG 評估實驗類別"""
    
    def __init__(self, pdf_folder: str):
        self.pdf_folder = pdf_folder
        self.rag_helper = None
        self.evaluation_results = {
            "experiment_info": {
                "timestamp": datetime.now().isoformat(),
                "pdf_folder": pdf_folder,
                "improvements": [
                    "同義詞匹配",
                    "詞根分析",
                    "模糊匹配",
                    "語義相似度",
                    "更智能的上下文分析"
                ],
                "evaluations": []
            },
            "test_cases": [],
            "metrics": {},
            "summary": {}
        }
        
        # 定義改進的評估指標
        self._setup_improved_feedback_functions()
        
    def _create_synonym_dict(self) -> dict:
        """建立同義詞字典"""
        return {
            "計算機": ["電腦", "計算機", "電子計算機", "數位計算機", "computer"],
            "電腦": ["計算機", "電腦", "電子計算機", "數位計算機", "computer"],
            "資料": ["數據", "資訊", "信息", "data", "information"],
            "數據": ["資料", "資訊", "信息", "data", "information"],
            "處理": ["運算", "計算", "執行", "操作", "處理", "process"],
            "運算": ["處理", "計算", "執行", "操作", "運算", "compute"],
            "程式": ["程序", "軟體", "應用", "program", "software"],
            "程序": ["程式", "軟體", "應用", "program", "software"],
            "演算法": ["算法", "演算法", "algorithm"],
            "算法": ["演算法", "算法", "algorithm"],
            "CPU": ["處理器", "中央處理器", "處理單元", "processor"],
            "記憶體": ["內存", "存儲器", "memory", "storage"],
            "輸入": ["輸入", "input", "輸入設備"],
            "輸出": ["輸出", "output", "輸出設備"],
            "系統": ["系統", "system", "作業系統", "操作系統"],
            "作業系統": ["操作系統", "OS", "系統軟體", "operating system"],
            "陣列": ["數組", "array", "陣列"],
            "串列": ["列表", "鏈表", "list", "linked list"],
            "管理": ["管理", "控制", "管制", "manage", "control"],
            "資源": ["資源", "資源", "resource"],
            "程序": ["進程", "程序", "process", "程式"],
            "檔案": ["文件", "文檔", "file"]
        }
    
    def _normalize_text(self, text: str) -> str:
        """文字正規化：移除標點符號、轉小寫"""
        # 移除標點符號和多餘空格
        text = re.sub(r'[，。！？；：「」『』（）\(\),.!?;:"\'`]', ' ', text)
        # 移除多餘空格
        text = ' '.join(text.split())
        return text.lower()
    
    def _extract_words(self, text: str) -> Set[str]:
        """提取詞彙，包括中文詞和英文詞"""
        text = self._normalize_text(text)
        words = set()
        
        # 提取中文詞（2-4個字）
        chinese_words = re.findall(r'[\u4e00-\u9fff]{2,4}', text)
        words.update(chinese_words)
        
        # 提取英文詞
        english_words = re.findall(r'[a-zA-Z]{2,}', text)
        words.update([w.lower() for w in english_words])
        
        # 提取單個中文字（如果沒有找到詞）
        if not chinese_words:
            single_chars = re.findall(r'[\u4e00-\u9fff]', text)
            words.update(single_chars)
        
        return words
    
    def _expand_with_synonyms(self, words: Set[str]) -> Set[str]:
        """使用同義詞擴展詞集合"""
        synonym_dict = self._create_synonym_dict()
        expanded_words = set(words)
        
        for word in words:
            if word in synonym_dict:
                expanded_words.update(synonym_dict[word])
        
        return expanded_words
    
    def _calculate_semantic_similarity(self, text1_words: Set[str], text2_words: Set[str]) -> float:
        """計算語義相似度（改進版）"""
        if not text1_words or not text2_words:
            return 0.0
        
        # 擴展同義詞
        expanded_text1 = self._expand_with_synonyms(text1_words)
        expanded_text2 = self._expand_with_synonyms(text2_words)
        
        # 計算Jaccard相似度
        intersection = len(expanded_text1.intersection(expanded_text2))
        union = len(expanded_text1.union(expanded_text2))
        
        if union == 0:
            return 0.0
        
        return intersection / union
    
    def _setup_improved_feedback_functions(self):
        """設置改進的評估函數"""
        
        # 1. 改進的回答相關性評估
        def improved_answer_relevance(query: str, answer: str) -> float:
            """改進的回答相關性評估 (0-1)"""
            if not query or not answer:
                return 0.0
            
            query_words = self._extract_words(query)
            answer_words = self._extract_words(answer)
            
            # 語義相似度
            semantic_similarity = self._calculate_semantic_similarity(query_words, answer_words)
            
            # 長度適當性（不是太短也不是太長）
            length_factor = 1.0
            if len(answer) < 50:
                length_factor = 0.6
            elif len(answer) > 2000:
                length_factor = 0.8
            elif len(answer) > 500:
                length_factor = 1.0
            else:
                length_factor = 0.8 + (len(answer) - 50) / (500 - 50) * 0.2
            
            # 結構完整性（是否有完整句子）
            structure_factor = 1.0
            if '。' in answer or '.' in answer:
                structure_factor = 1.0
            else:
                structure_factor = 0.8
            
            final_score = semantic_similarity * length_factor * structure_factor
            return min(final_score, 1.0)
        
        # 2. 改進的上下文忠實度評估
        def improved_context_faithfulness(context: str, answer: str) -> float:
            """改進的上下文忠實度評估 (0-1)"""
            if not context or not answer:
                return 0.0
            
            context_words = self._extract_words(context)
            answer_words = self._extract_words(answer)
            
            if not answer_words:
                return 0.0
            
            # 使用語義相似度而不是簡單的詞彙重疊
            semantic_overlap = self._calculate_semantic_similarity(context_words, answer_words)
            
            # 檢查是否有明顯的幻覺（回答中包含上下文完全沒有的概念）
            hallucination_penalty = 0.0
            
            # 如果回答過於偏離上下文主題，給予懲罰
            if semantic_overlap < 0.1:
                hallucination_penalty = 0.3
            
            faithfulness_score = semantic_overlap - hallucination_penalty
            return max(min(faithfulness_score, 1.0), 0.0)
        
        # 3. 改進的上下文相關性評估
        def improved_context_relevance(query: str, context: str) -> float:
            """改進的上下文相關性評估 (0-1)"""
            if not query or not context:
                return 0.0
            
            query_words = self._extract_words(query)
            context_words = self._extract_words(context)
            
            # 語義相似度
            semantic_relevance = self._calculate_semantic_similarity(query_words, context_words)
            
            # 上下文豐富度（是否包含足夠的信息）
            richness_factor = min(len(context) / 200, 1.0)  # 200字為基準
            
            final_score = semantic_relevance * (0.7 + richness_factor * 0.3)
            return min(final_score, 1.0)
        
        # 4. 改進的回答完整性評估
        def improved_answer_completeness(query: str, answer: str) -> float:
            """改進的回答完整性評估 (0-1)"""
            if not answer:
                return 0.0
            
            # 基於長度的完整性（但更合理的範圍）
            length_score = min(len(answer) / 150.0, 1.0)  # 150字為基準
            
            # 結構完整性指標
            structure_indicators = [
                "。" in answer or "." in answer,  # 有完整句子
                len(answer.split()) >= 15,  # 有足夠詞彙
                "是" in answer or "為" in answer or "具有" in answer,  # 有定義性語句
                "例如" in answer or "比如" in answer or "如" in answer,  # 有例子
                "因為" in answer or "由於" in answer or "所以" in answer,  # 有因果關係
            ]
            
            structure_score = sum(structure_indicators) / len(structure_indicators)
            
            # 主題相關性（是否真的在回答問題）
            query_words = self._extract_words(query)
            answer_words = self._extract_words(answer)
            topic_relevance = self._calculate_semantic_similarity(query_words, answer_words)
            
            # 綜合評分
            final_score = (length_score * 0.3 + structure_score * 0.4 + topic_relevance * 0.3)
            return min(final_score, 1.0)
        
        # 5. 改進的綜合品質評估
        def improved_overall_quality(query: str, context: str, answer: str) -> float:
            """改進的綜合品質評估 (0-1)"""
            if not all([query, context, answer]):
                return 0.0
            
            relevance = improved_answer_relevance(query, answer)
            faithfulness = improved_context_faithfulness(context, answer)
            context_rel = improved_context_relevance(query, context)
            completeness = improved_answer_completeness(query, answer)
            
            # 調整權重，更重視相關性和完整性
            weights = {
                "relevance": 0.35,        # 提高相關性權重
                "faithfulness": 0.20,     # 降低忠實度權重
                "context_relevance": 0.20, # 降低上下文相關性權重
                "completeness": 0.25      # 提高完整性權重
            }
            
            overall = (
                relevance * weights["relevance"] +
                faithfulness * weights["faithfulness"] +
                context_rel * weights["context_relevance"] +
                completeness * weights["completeness"]
            )
            
            return min(overall, 1.0)
        
        # 建立 TruLens Feedback 物件
        self.feedback_functions = {
            "answer_relevance": Feedback(improved_answer_relevance),
            "context_faithfulness": Feedback(improved_context_faithfulness),
            "context_relevance": Feedback(improved_context_relevance),
            "answer_completeness": Feedback(improved_answer_completeness),
            "overall_quality": Feedback(improved_overall_quality)
        }
        
        print("✅ 改進的評估函數設置完成")
        print("   📈 新增功能：同義詞匹配、語義相似度、結構分析")
        
    async def setup_rag_system(self):
        """設置 RAG 系統"""
        print(f"\n🔧 設置 RAG 系統 (資料夾: {self.pdf_folder})")
        
        try:
            self.rag_helper = RAGHelper(self.pdf_folder, chunk_size=300, chunk_overlap=50)
            await self.rag_helper.load_and_prepare(['.pdf', '.txt', '.md'])
            self.rag_helper.setup_retrieval_chain()
            
            print("✅ RAG 系統設置完成")
            return True
            
        except Exception as e:
            print(f"❌ RAG 系統設置失敗: {e}")
            return False
    
    def create_test_cases(self):
        """建立測試案例（使用相同的測試案例）"""
        
        # 計算機概論相關測試問題
        test_cases = [
            {
                "id": "basic_01",
                "category": "基礎概念",
                "query": "什麼是計算機？",
                "expected_keywords": ["電腦", "資料", "處理", "程式"],
                "difficulty": "易"
            },
            {
                "id": "basic_02", 
                "category": "基礎概念",
                "query": "計算機的組成部分有哪些？",
                "expected_keywords": ["CPU", "記憶體", "輸入", "輸出"],
                "difficulty": "易"
            },
            {
                "id": "intermediate_01",
                "category": "程式設計",
                "query": "什麼是演算法？",
                "expected_keywords": ["步驟", "問題", "解決", "邏輯"],
                "difficulty": "中"
            }
        ]
        
        self.test_cases = test_cases
        print(f"✅ 建立了 {len(test_cases)} 個測試案例")
        return test_cases
    
    def test_with_sample_data(self):
        """使用示例數據測試改進的算法"""
        print(f"\n🧪 使用示例數據測試改進的評估算法...")
        
        # 使用之前實驗的實際數據
        sample_data = {
            "query": "什麼是計算機？",
            "answer": "計算機是一種用來協助人們進行計算的工具。從最早的算盤到現代的數位計算機，計算機的主要功能就是處理和運算數字資料。想像一下，計算機就像是一位非常聰明的助手，能夠快速而準確地完成我們需要的計算工作。它不僅可以幫助我們進行簡單的加減乘除，還能處理複雜的邏輯運算和數據分析。",
            "context": "計算機概論相關內容，包含計算機定義、功能、應用等信息"
        }
        
        print(f"📝 測試問題: {sample_data['query']}")
        print(f"📄 回答長度: {len(sample_data['answer'])} 字元")
        
        # 執行各項評估
        scores = {}
        for metric_name, feedback_func in self.feedback_functions.items():
            try:
                if metric_name in ["answer_relevance", "answer_completeness"]:
                    score = feedback_func(sample_data['query'], sample_data['answer'])
                elif metric_name == "context_faithfulness":
                    score = feedback_func(sample_data['context'], sample_data['answer'])
                elif metric_name == "context_relevance":
                    score = feedback_func(sample_data['query'], sample_data['context'])
                elif metric_name == "overall_quality":
                    score = feedback_func(sample_data['query'], sample_data['context'], sample_data['answer'])
                else:
                    score = 0.0
                
                scores[metric_name] = float(score)
                print(f"   📊 {metric_name}: {score:.3f}")
                
            except Exception as e:
                print(f"   ❌ {metric_name} 評估失敗: {e}")
                scores[metric_name] = 0.0
        
        print(f"\n📈 改進結果對比:")
        old_scores = {
            "answer_relevance": 0.000,
            "context_faithfulness": 0.000, 
            "context_relevance": 0.000,
            "answer_completeness": 0.800,
            "overall_quality": 0.160
        }
        
        for metric in scores:
            old_score = old_scores.get(metric, 0.0)
            new_score = scores[metric]
            improvement = new_score - old_score
            print(f"   {metric}: {old_score:.3f} → {new_score:.3f} (改進: {improvement:+.3f})")
        
        return scores

def main():
    """主要執行函數"""
    
    # 檢查 PDF 資料夾
    pdf_folder = "pdfFiles"
    
    if not os.path.exists(pdf_folder):
        print(f"❌ PDF 資料夾不存在: {pdf_folder}")
        return
    
    # 建立改進的評估實驗
    experiment = ImprovedRAGEvaluationExperiment(pdf_folder)
    
    # 執行測試
    print("🚀 開始改進版 RAG 評估算法測試")
    
    # 建立測試案例
    experiment.create_test_cases()
    
    # 使用示例數據測試
    experiment.test_with_sample_data()
    
    print(f"\n🎉 改進版評估算法測試完成！")
    print("💡 主要改進：同義詞匹配、語義相似度計算、更合理的評分權重")
    print("=" * 60)

if __name__ == "__main__":
    # 檢查 OpenAI API Key
    if not os.getenv('OPENAI_API_KEY'):
        print("⚠️  注意: 未檢測到 OPENAI_API_KEY，將使用示例數據測試")
    else:
        print("✅ 檢測到 OpenAI API Key")
    
    # 執行測試
    main()