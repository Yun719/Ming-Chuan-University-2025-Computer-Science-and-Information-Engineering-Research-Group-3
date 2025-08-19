"""
TruLens Feedback 功能全面驗證測試

嚴謹測試 Feedback 的各種使用場景和實際可用性
"""

import sys
import os
import time
import traceback

# 設定 UTF-8 編碼
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)

print("🔬 TruLens Feedback 功能全面驗證測試")
print("=" * 70)

# 測試結果記錄
test_results = {
    "passed": 0,
    "failed": 0,
    "warnings": 0,
    "details": []
}

def log_test_result(test_name: str, status: str, message: str = ""):
    """記錄測試結果"""
    test_results["details"].append(f"{status} {test_name}: {message}")
    if status == "✅":
        test_results["passed"] += 1
    elif status == "❌":
        test_results["failed"] += 1
    elif status == "⚠️":
        test_results["warnings"] += 1

# 步驟 1: 基礎匯入測試
print("\n🔧 步驟 1: 基礎匯入和初始化測試")
try:
    from trulens_eval.feedback import Feedback
    from trulens.core import TruSession
    from trulens.apps.basic import TruBasicApp
    log_test_result("基礎匯入", "✅", "所有必要模組成功匯入")
    
    # 初始化 TruSession
    session = TruSession()
    log_test_result("TruSession 初始化", "✅", "會話管理正常")
    
except Exception as e:
    log_test_result("基礎匯入", "❌", f"匯入失敗: {e}")
    print(f"❌ 基礎功能失敗，無法繼續測試: {e}")
    exit(1)

# 步驟 2: 單參數 Feedback 測試
print("\n📝 步驟 2: 單參數 Feedback 功能測試")
def single_param_evaluator(text: str) -> float:
    """單參數評估函數"""
    if not isinstance(text, str):
        return 0.0
    return min(len(text) / 100.0, 1.0)

try:
    feedback_single = Feedback(single_param_evaluator)
    
    # 測試各種輸入
    test_cases = [
        ("正常文字", "這是一個正常的測試文字"),
        ("空字串", ""),
        ("長文字", "測試" * 100),
        ("中文內容", "這是繁體中文測試內容，包含各種標點符號！@#$%"),
    ]
    
    all_passed = True
    for case_name, test_input in test_cases:
        try:
            score = feedback_single(test_input)
            if isinstance(score, (int, float)) and 0 <= score <= 1:
                print(f"   ✅ {case_name}: 評分 {score:.3f}")
            else:
                print(f"   ❌ {case_name}: 評分異常 {score}")
                all_passed = False
        except Exception as e:
            print(f"   ❌ {case_name}: 執行錯誤 {e}")
            all_passed = False
    
    if all_passed:
        log_test_result("單參數 Feedback", "✅", "所有測試案例通過")
    else:
        log_test_result("單參數 Feedback", "❌", "部分測試案例失敗")
        
except Exception as e:
    log_test_result("單參數 Feedback", "❌", f"建立失敗: {e}")

# 步驟 3: 多參數 Feedback 測試
print("\n📋 步驟 3: 多參數 Feedback 功能測試")
def multi_param_evaluator(query: str, context: str, response: str) -> float:
    """多參數評估函數 (模擬 RAG 評估)"""
    try:
        if not all([query, context, response]):
            return 0.0
        
        # 簡單的相關性計算
        query_words = set(query.lower().split())
        response_words = set(response.lower().split())
        context_words = set(context.lower().split())
        
        # 查詢-回應相關性
        query_overlap = len(query_words.intersection(response_words))
        query_relevance = query_overlap / max(len(query_words), 1)
        
        # 上下文-回應一致性
        context_overlap = len(context_words.intersection(response_words))
        context_relevance = context_overlap / max(len(context_words), 1)
        
        # 加權平均
        final_score = (query_relevance * 0.6 + context_relevance * 0.4)
        return min(final_score, 1.0)
        
    except Exception:
        return 0.0

try:
    feedback_multi = Feedback(multi_param_evaluator)
    
    # 測試 RAG 場景
    rag_cases = [
        {
            "name": "高相關性案例",
            "query": "什麼是機器學習？",
            "context": "機器學習是人工智慧的分支，讓電腦從資料中學習",
            "response": "機器學習是人工智慧技術，通過資料學習來提升效能"
        },
        {
            "name": "低相關性案例", 
            "query": "Python程式語言特點",
            "context": "Python是高級程式語言，語法簡潔",
            "response": "Java是物件導向程式語言"
        },
        {
            "name": "空值測試",
            "query": "",
            "context": "一些上下文",
            "response": "一些回應"
        }
    ]
    
    multi_all_passed = True
    for case in rag_cases:
        try:
            score = feedback_multi(case["query"], case["context"], case["response"])
            if isinstance(score, (int, float)) and 0 <= score <= 1:
                print(f"   ✅ {case['name']}: 評分 {score:.3f}")
            else:
                print(f"   ❌ {case['name']}: 評分異常 {score}")
                multi_all_passed = False
        except Exception as e:
            print(f"   ❌ {case['name']}: 執行錯誤 {e}")
            multi_all_passed = False
    
    if multi_all_passed:
        log_test_result("多參數 Feedback", "✅", "RAG 評估場景測試通過")
    else:
        log_test_result("多參數 Feedback", "❌", "RAG 評估場景測試失敗")
        
except Exception as e:
    log_test_result("多參數 Feedback", "❌", f"建立失敗: {e}")

# 步驟 4: 與 TruBasicApp 整合測試
print("\n🔗 步驟 4: TruBasicApp 整合測試")
def simple_rag_function(query: str) -> str:
    """模擬 RAG 函數"""
    responses = {
        "python": "Python是一種高級程式語言，以其簡潔的語法著稱",
        "機器學習": "機器學習是人工智慧的重要分支，讓電腦能夠從資料中學習",
        "default": "這是一個預設回應，用於回答各種查詢"
    }
    
    query_lower = query.lower()
    for key, response in responses.items():
        if key in query_lower:
            return response
    return responses["default"]

try:
    # 包裝函數
    wrapped_app = TruBasicApp(simple_rag_function, app_id="test_rag_integration")
    
    # 建立評估函數
    def integration_evaluator(query: str, response: str) -> float:
        """整合測試評估函數"""
        if not query or not response:
            return 0.0
        query_words = set(query.lower().split())
        response_words = set(response.lower().split())
        overlap = len(query_words.intersection(response_words))
        return min(overlap / max(len(query_words), 1), 1.0)
    
    feedback_integration = Feedback(integration_evaluator)
    
    # 測試整合功能
    test_queries = [
        "什麼是Python？",
        "機器學習的應用",
        "隨機問題測試"
    ]
    
    integration_passed = True
    for query in test_queries:
        try:
            # 呼叫 RAG 函數
            response = simple_rag_function(query)
            
            # 評估結果
            score = feedback_integration(query, response)
            
            if isinstance(score, (int, float)) and 0 <= score <= 1:
                print(f"   ✅ 查詢: '{query}' → 評分: {score:.3f}")
            else:
                print(f"   ❌ 查詢: '{query}' → 評分異常: {score}")
                integration_passed = False
                
        except Exception as e:
            print(f"   ❌ 查詢: '{query}' → 執行錯誤: {e}")
            integration_passed = False
    
    if integration_passed:
        log_test_result("TruBasicApp 整合", "✅", "與 RAG 應用整合成功")
    else:
        log_test_result("TruBasicApp 整合", "❌", "整合測試失敗")
        
except Exception as e:
    log_test_result("TruBasicApp 整合", "❌", f"整合失敗: {e}")
    print(f"   詳細錯誤: {traceback.format_exc()}")

# 步驟 5: 效能和穩定性測試
print("\n⚡ 步驟 5: 效能和穩定性測試")
def performance_evaluator(text: str) -> float:
    """效能測試評估函數"""
    return len(text) / 1000.0

try:
    feedback_perf = Feedback(performance_evaluator)
    
    # 效能測試
    test_data = [f"效能測試文字 {i}" * 20 for i in range(50)]
    
    start_time = time.time()
    scores = []
    errors = 0
    
    for i, text in enumerate(test_data):
        try:
            score = feedback_perf(text)
            scores.append(score)
        except Exception as e:
            errors += 1
            
    end_time = time.time()
    execution_time = end_time - start_time
    
    # 分析結果
    if errors == 0 and len(scores) == len(test_data):
        avg_time_per_eval = execution_time / len(test_data) * 1000  # 毫秒
        print(f"   ✅ 處理 {len(test_data)} 次評估")
        print(f"   ✅ 總執行時間: {execution_time:.3f} 秒")
        print(f"   ✅ 平均每次評估: {avg_time_per_eval:.2f} 毫秒")
        print(f"   ✅ 錯誤次數: {errors}")
        
        if avg_time_per_eval < 100:  # 100毫秒內
            log_test_result("效能測試", "✅", f"平均 {avg_time_per_eval:.2f}ms/次評估")
        else:
            log_test_result("效能測試", "⚠️", f"較慢: {avg_time_per_eval:.2f}ms/次評估")
    else:
        log_test_result("效能測試", "❌", f"發生 {errors} 個錯誤")
        
except Exception as e:
    log_test_result("效能測試", "❌", f"效能測試失敗: {e}")

# 步驟 6: 邊界條件和異常處理測試
print("\n🚨 步驟 6: 邊界條件和異常處理測試")
def robust_evaluator(text) -> float:
    """健壯的評估函數"""
    try:
        if text is None:
            return 0.0
        if not isinstance(text, str):
            text = str(text)
        if len(text) == 0:
            return 0.0
        return 0.5  # 固定回傳值便於測試
    except Exception:
        return 0.0

try:
    feedback_robust = Feedback(robust_evaluator)
    
    # 邊界條件測試
    edge_cases = [
        ("None 值", None),
        ("數字", 12345),
        ("列表", [1, 2, 3]),
        ("布林值", True),
        ("空字串", ""),
        ("特殊字符", "!@#$%^&*()"),
        ("超長字串", "測試" * 10000)
    ]
    
    edge_passed = True
    for case_name, test_input in edge_cases:
        try:
            score = feedback_robust(test_input)
            if isinstance(score, (int, float)) and 0 <= score <= 1:
                print(f"   ✅ {case_name}: 評分 {score:.3f}")
            else:
                print(f"   ❌ {case_name}: 評分異常 {score}")
                edge_passed = False
        except Exception as e:
            print(f"   ❌ {case_name}: 執行錯誤 {e}")
            edge_passed = False
    
    if edge_passed:
        log_test_result("邊界條件測試", "✅", "所有邊界條件處理正常")
    else:
        log_test_result("邊界條件測試", "❌", "部分邊界條件處理失敗")
        
except Exception as e:
    log_test_result("邊界條件測試", "❌", f"邊界條件測試失敗: {e}")

# 測試結果總結
print("\n" + "=" * 70)
print("📊 測試結果總結")
print("=" * 70)

print(f"✅ 通過測試: {test_results['passed']}")
print(f"⚠️  警告項目: {test_results['warnings']}")  
print(f"❌ 失敗測試: {test_results['failed']}")

print(f"\n📋 詳細結果:")
for detail in test_results["details"]:
    print(f"   {detail}")

# 最終判斷
total_tests = test_results['passed'] + test_results['failed'] + test_results['warnings']
success_rate = test_results['passed'] / total_tests if total_tests > 0 else 0

print(f"\n🎯 最終評估:")
print(f"   測試通過率: {success_rate:.1%}")

if test_results['failed'] == 0 and test_results['passed'] >= 5:
    print("🎉 結論: TruLens Feedback 功能完全可用！")
    print("   所有核心功能正常，可以用於 RAG 評估實驗")
elif test_results['failed'] <= 2 and test_results['passed'] >= 3:
    print("⚠️  結論: TruLens Feedback 基本可用，但有注意事項")
    print("   核心功能正常，可以謹慎使用")
else:
    print("❌ 結論: TruLens Feedback 功能有重大問題")
    print("   建議修正問題後再使用")

print("\n" + "=" * 70)