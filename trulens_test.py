"""
TruLens 2.2.1 正確 API 測試腳本

基於實際探索結果設計的測試腳本
"""

import sys
import os

# 設定 UTF-8 編碼 (Windows)
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)

print("🚀 TruLens 2.2.1 功能測試")
print("=" * 50)

# 測試1: 使用正確的模組結構
print("\n📦 測試1: 正確的模組匯入")
try:
    from trulens.core import TruSession
    print("✅ TruSession 從 trulens.core 匯入成功")
    
    from trulens_eval.feedback import Feedback
    print("✅ Feedback 從 trulens_eval.feedback 匯入成功")
    print("   ⚠️  使用已棄用的 API，但功能正常")
    
    from trulens.apps.basic import TruBasicApp
    print("✅ TruBasicApp 匯入成功")
    
except ImportError as e:
    print(f"❌ 正確模組匯入失敗: {e}")

# 測試2: 建立 TruSession
print("\n🔧 測試2: 建立 TruSession")
try:
    from trulens.core import TruSession
    session = TruSession()
    print("✅ TruSession 建立成功")
    print(f"   Session 類型: {type(session)}")
except Exception as e:
    print(f"❌ TruSession 建立失敗: {e}")

# 測試3: 測試 Feedback 功能
print("\n📊 測試3: Feedback 功能")
try:
    from trulens_eval.feedback import Feedback
    
    # 建立簡單的評估函數
    def simple_relevance_feedback(input_text: str, output_text: str) -> float:
        """簡單的相關性評估"""
        # 基於文字長度的簡單評分
        if len(input_text) == 0:
            return 0.0
        relevance_score = min(len(output_text) / len(input_text), 1.0)
        return relevance_score
    
    feedback = Feedback(simple_relevance_feedback)
    print("✅ Feedback 函數建立成功")
    
    # 測試評估
    test_input = "什麼是計算機概論？"
    test_output = "計算機概論是介紹計算機基本概念和應用的課程"
    score = feedback(test_input, test_output)
    print(f"   測試評分: {score:.3f}")
    
except Exception as e:
    print(f"❌ Feedback 功能測試失敗: {e}")

# 測試4: 測試基本應用包裝
print("\n🎮 測試4: 基本應用包裝")
try:
    from trulens.apps.basic import TruBasicApp
    
    def simple_rag_function(query: str) -> str:
        """模擬簡單的 RAG 函數"""
        return f"根據查詢「{query}」，這是一個模擬回答。"
    
    # 包裝函數
    wrapped_app = TruBasicApp(simple_rag_function, app_id="test_rag")
    print("✅ TruBasicApp 包裝成功")
    print(f"   App ID: {wrapped_app.app_id}")
    
except Exception as e:
    print(f"❌ 基本應用包裝失敗: {e}")

# 測試5: 檢查評估提供者
print("\n🤖 測試5: 檢查評估提供者")
try:
    # 嘗試匯入 OpenAI 提供者
    from trulens.providers.openai import OpenAI
    print("✅ OpenAI 提供者可用")
    
    # 檢查 API Key
    openai_api_key = os.getenv('OPENAI_API_KEY')
    if openai_api_key:
        print("✅ 檢測到 OPENAI_API_KEY")
        provider = OpenAI()
        print("✅ OpenAI 提供者建立成功")
    else:
        print("⚠️  未檢測到 OPENAI_API_KEY 環境變數")
        
except ImportError as e:
    print(f"❌ OpenAI 提供者不可用: {e}")
except Exception as e:
    print(f"⚠️  OpenAI 提供者匯入成功，但建立失敗: {e}")

# 測試6: 檢查 Dashboard 功能
print("\n📊 測試6: Dashboard 功能")
try:
    from trulens.dashboard import run_dashboard
    print("✅ Dashboard 功能可用")
    print("   可以使用 run_dashboard() 啟動儀表板")
except ImportError as e:
    print(f"❌ Dashboard 功能不可用: {e}")

# 測試7: 版本資訊
print("\n🔍 測試7: 套件資訊")
try:
    import pkg_resources
    trulens_version = pkg_resources.get_distribution("trulens").version
    print(f"✅ TruLens 版本: {trulens_version}")
    
    # 檢查相關套件
    trulens_packages = [
        "trulens-core", "trulens-feedback", "trulens-dashboard", 
        "trulens-otel-semconv", "trulens_eval"
    ]
    
    print("   相關套件:")
    for pkg in trulens_packages:
        try:
            version = pkg_resources.get_distribution(pkg).version
            print(f"     - {pkg}: {version}")
        except:
            print(f"     - {pkg}: 未安裝")
            
except Exception as e:
    print(f"❌ 版本資訊檢查失敗: {e}")

print("\n🎉 TruLens 2.2.1 功能測試完成！")
print("=" * 50)
print("\n💡 測試結果總結:")
print("   ✅ 表示功能正常可用")
print("   ⚠️  表示功能可用但需要額外設定")
print("   ❌ 表示功能不可用或需要修正")
print("\n🔜 下一步: 可以開始整合到 RAG_Helper.py 進行評估")