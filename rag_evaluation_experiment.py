"""
RAG_Helper.py 系統評估實驗

使用 TruLens 對現有 RAG 系統進行全面評估
"""

import sys
import os
import asyncio
import json
from datetime import datetime
from pathlib import Path

# 設定 UTF-8 編碼
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)

# TruLens 匯入
from trulens_eval.feedback import Feedback
from trulens.core import TruSession
from trulens.apps.basic import TruBasicApp

# 本地 RAG 系統匯入
from RAG_Helper import RAGHelper

print("🔬 RAG_Helper.py 系統評估實驗")
print("=" * 60)

# 初始化 TruLens 會話
session = TruSession()
print("✅ TruLens 會話初始化完成")

class RAGEvaluationExperiment:
    """RAG 評估實驗類別"""
    
    def __init__(self, pdf_folder: str):
        self.pdf_folder = pdf_folder
        self.rag_helper = None
        self.evaluation_results = {
            "experiment_info": {
                "timestamp": datetime.now().isoformat(),
                "pdf_folder": pdf_folder,
                "evaluations": []
            },
            "test_cases": [],
            "metrics": {},
            "summary": {}
        }
        
        # 定義評估指標
        self._setup_feedback_functions()
        
    def _setup_feedback_functions(self):
        """設置評估函數"""
        
        # 1. 回答相關性評估
        def answer_relevance(query: str, answer: str) -> float:
            """評估回答與查詢的相關性 (0-1)"""
            if not query or not answer:
                return 0.0
            
            query_words = set(query.lower().split())
            answer_words = set(answer.lower().split())
            
            if len(query_words) == 0:
                return 0.0
            
            # 關鍵詞重疊比率
            overlap = len(query_words.intersection(answer_words))
            relevance = overlap / len(query_words)
            
            # 回答長度因子 (太短或太長都扣分)
            length_factor = 1.0
            if len(answer) < 10:
                length_factor = 0.5
            elif len(answer) > 1000:
                length_factor = 0.8
                
            return min(relevance * length_factor, 1.0)
        
        # 2. 上下文忠實度評估
        def context_faithfulness(context: str, answer: str) -> float:
            """評估回答是否忠實於檢索到的上下文 (0-1)"""
            if not context or not answer:
                return 0.0
            
            context_words = set(context.lower().split())
            answer_words = set(answer.lower().split())
            
            if len(answer_words) == 0:
                return 0.0
            
            # 回答中來自上下文的詞比例
            supported_words = len(answer_words.intersection(context_words))
            faithfulness = supported_words / len(answer_words)
            
            return min(faithfulness, 1.0)
        
        # 3. 上下文相關性評估
        def context_relevance(query: str, context: str) -> float:
            """評估檢索到的上下文與查詢的相關性 (0-1)"""
            if not query or not context:
                return 0.0
            
            query_words = set(query.lower().split())
            context_words = set(context.lower().split())
            
            if len(query_words) == 0:
                return 0.0
            
            # 查詢詞在上下文中的覆蓋率
            overlap = len(query_words.intersection(context_words))
            relevance = overlap / len(query_words)
            
            return min(relevance, 1.0)
        
        # 4. 回答完整性評估
        def answer_completeness(query: str, answer: str) -> float:
            """評估回答的完整性 (0-1)"""
            if not answer:
                return 0.0
            
            # 基於長度的完整性判斷
            length_score = min(len(answer) / 100.0, 1.0)  # 100字為基準
            
            # 檢查是否包含關鍵要素
            answer_lower = answer.lower()
            completeness_indicators = [
                "因為" in answer or "由於" in answer,  # 有解釋
                "例如" in answer or "比如" in answer,  # 有例子
                "。" in answer,  # 有完整句子
                len(answer.split()) >= 10  # 有足夠詞彙
            ]
            
            indicator_score = sum(completeness_indicators) / len(completeness_indicators)
            
            return (length_score * 0.6 + indicator_score * 0.4)
        
        # 5. 綜合品質評估
        def overall_quality(query: str, context: str, answer: str) -> float:
            """綜合評估 RAG 系統的整體品質 (0-1)"""
            if not all([query, context, answer]):
                return 0.0
            
            relevance = answer_relevance(query, answer)
            faithfulness = context_faithfulness(context, answer)
            context_rel = context_relevance(query, context)
            completeness = answer_completeness(query, answer)
            
            # 加權平均
            weights = {
                "relevance": 0.3,
                "faithfulness": 0.25,
                "context_relevance": 0.25,
                "completeness": 0.2
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
            "answer_relevance": Feedback(answer_relevance),
            "context_faithfulness": Feedback(context_faithfulness),
            "context_relevance": Feedback(context_relevance),
            "answer_completeness": Feedback(answer_completeness),
            "overall_quality": Feedback(overall_quality)
        }
        
        print("✅ 評估函數設置完成")
        
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
        """建立測試案例"""
        
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
            },
            {
                "id": "intermediate_02",
                "category": "資料結構",
                "query": "陣列和串列有什麼差別？",
                "expected_keywords": ["陣列", "串列", "記憶體", "存取"],
                "difficulty": "中"
            },
            {
                "id": "advanced_01",
                "category": "系統概念",
                "query": "作業系統的主要功能是什麼？",
                "expected_keywords": ["管理", "資源", "程序", "檔案"],
                "difficulty": "難"
            },
            {
                "id": "edge_01",
                "category": "邊界測試",
                "query": "請解釋量子計算",
                "expected_keywords": [],  # 可能超出範圍
                "difficulty": "超範圍"
            },
            {
                "id": "edge_02",
                "category": "邊界測試", 
                "query": "天氣如何？",
                "expected_keywords": [],  # 無關問題
                "difficulty": "無關"
            }
        ]
        
        self.test_cases = test_cases
        print(f"✅ 建立了 {len(test_cases)} 個測試案例")
        return test_cases
    
    async def run_evaluation(self):
        """執行評估實驗"""
        print(f"\n🧪 開始執行評估實驗...")
        
        if not self.rag_helper:
            print("❌ RAG 系統未設置")
            return False
        
        results = []
        
        for i, test_case in enumerate(self.test_cases, 1):
            print(f"\n📝 測試案例 {i}/{len(self.test_cases)}: {test_case['id']}")
            print(f"   問題: {test_case['query']}")
            print(f"   分類: {test_case['category']} | 難度: {test_case['difficulty']}")
            
            try:
                # 執行 RAG 查詢
                answer, context_docs = self.rag_helper.ask(test_case['query'])
                
                # 合併上下文
                context = "\\n".join([doc.page_content for doc in context_docs])
                
                print(f"   回答長度: {len(answer)} 字元")
                print(f"   上下文段落: {len(context_docs)} 個")
                
                # 執行各項評估
                scores = {}
                for metric_name, feedback_func in self.feedback_functions.items():
                    try:
                        if metric_name in ["answer_relevance", "answer_completeness"]:
                            score = feedback_func(test_case['query'], answer)
                        elif metric_name == "context_faithfulness":
                            score = feedback_func(context, answer)
                        elif metric_name == "context_relevance":
                            score = feedback_func(test_case['query'], context)
                        elif metric_name == "overall_quality":
                            score = feedback_func(test_case['query'], context, answer)
                        else:
                            score = 0.0
                        
                        scores[metric_name] = float(score)
                        print(f"   {metric_name}: {score:.3f}")
                        
                    except Exception as e:
                        print(f"   ❌ {metric_name} 評估失敗: {e}")
                        scores[metric_name] = 0.0
                
                # 記錄結果
                result = {
                    "test_case": test_case,
                    "rag_output": {
                        "answer": answer,
                        "context_count": len(context_docs),
                        "context_length": len(context)
                    },
                    "scores": scores,
                    "timestamp": datetime.now().isoformat()
                }
                
                results.append(result)
                
            except Exception as e:
                print(f"   ❌ 測試執行失敗: {e}")
                result = {
                    "test_case": test_case,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
                results.append(result)
        
        self.evaluation_results["test_cases"] = results
        return results
    
    def analyze_results(self):
        """分析評估結果"""
        print(f"\n📊 分析評估結果...")
        
        if not self.evaluation_results["test_cases"]:
            print("❌ 沒有評估結果可分析")
            return
        
        # 計算各指標的平均分數
        metrics_summary = {}
        valid_results = [r for r in self.evaluation_results["test_cases"] if "scores" in r]
        
        if not valid_results:
            print("❌ 沒有有效的評估結果")
            return
        
        for metric_name in self.feedback_functions.keys():
            scores = [r["scores"].get(metric_name, 0) for r in valid_results]
            metrics_summary[metric_name] = {
                "average": sum(scores) / len(scores),
                "min": min(scores),
                "max": max(scores),
                "count": len(scores)
            }
        
        # 按類別分析
        category_analysis = {}
        for result in valid_results:
            category = result["test_case"]["category"]
            if category not in category_analysis:
                category_analysis[category] = []
            category_analysis[category].append(result["scores"]["overall_quality"])
        
        category_summary = {}
        for category, scores in category_analysis.items():
            category_summary[category] = {
                "average": sum(scores) / len(scores),
                "count": len(scores)
            }
        
        # 儲存分析結果
        self.evaluation_results["metrics"] = metrics_summary
        self.evaluation_results["summary"] = {
            "total_tests": len(self.evaluation_results["test_cases"]),
            "successful_tests": len(valid_results),
            "failed_tests": len(self.evaluation_results["test_cases"]) - len(valid_results),
            "category_analysis": category_summary
        }
        
        # 顯示結果
        print(f"\n📈 評估結果總結:")
        print(f"   總測試數: {self.evaluation_results['summary']['total_tests']}")
        print(f"   成功測試: {self.evaluation_results['summary']['successful_tests']}")
        print(f"   失敗測試: {self.evaluation_results['summary']['failed_tests']}")
        
        print(f"\n📊 各指標平均分數:")
        for metric, stats in metrics_summary.items():
            print(f"   {metric}: {stats['average']:.3f} (範圍: {stats['min']:.3f}-{stats['max']:.3f})")
        
        print(f"\n🏷️ 各類別表現:")
        for category, stats in category_summary.items():
            print(f"   {category}: {stats['average']:.3f} ({stats['count']} 個測試)")
    
    def save_results(self, filename: str = None):
        """儲存評估結果"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"rag_evaluation_results_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.evaluation_results, f, ensure_ascii=False, indent=2)
            print(f"✅ 評估結果已儲存至: {filename}")
        except Exception as e:
            print(f"❌ 儲存結果失敗: {e}")

async def main():
    """主要執行函數"""
    
    # 檢查 PDF 資料夾
    pdf_folder = "pdfFiles"  # 根據 RAG_Helper.py 的慣例
    
    if not os.path.exists(pdf_folder):
        print(f"❌ PDF 資料夾不存在: {pdf_folder}")
        print("請確認資料夾路徑或在當前目錄建立 pdfFiles 資料夾並放入 PDF 檔案")
        return
    
    # 建立評估實驗
    experiment = RAGEvaluationExperiment(pdf_folder)
    
    # 執行實驗流程
    print("🚀 開始 RAG 評估實驗流程")
    
    # 1. 設置 RAG 系統
    if not await experiment.setup_rag_system():
        print("❌ RAG 系統設置失敗，中止實驗")
        return
    
    # 2. 建立測試案例
    experiment.create_test_cases()
    
    # 3. 執行評估
    await experiment.run_evaluation()
    
    # 4. 分析結果
    experiment.analyze_results()
    
    # 5. 儲存結果
    experiment.save_results()
    
    print(f"\n🎉 RAG 評估實驗完成！")
    print("=" * 60)

if __name__ == "__main__":
    # 檢查 OpenAI API Key
    if not os.getenv('OPENAI_API_KEY'):
        print("⚠️  警告: 未檢測到 OPENAI_API_KEY 環境變數")
        print("請設置 OpenAI API Key 才能執行完整的 RAG 評估")
    else:
        print("✅ 檢測到 OpenAI API Key")
    
    # 執行實驗
    asyncio.run(main())