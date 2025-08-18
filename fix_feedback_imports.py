"""
修正 TruLens Feedback 匯入問題的探索腳本
"""

import sys

# 設定 UTF-8 編碼
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)

print("🔧 修正 TruLens Feedback 匯入問題")
print("=" * 50)

# 探索各種可能的 Feedback 匯入路徑
feedback_paths = [
    "trulens.feedback.Feedback",
    "trulens_eval.feedback.Feedback", 
    "trulens.core.feedback.Feedback",
    "trulens_feedback.Feedback",
    "trulens_core.feedback.Feedback",
    "trulens.feedback.feedback.Feedback",
    "trulens_eval.feedback.feedback.Feedback",
]

print("\n📦 測試 Feedback 匯入路徑:")
working_feedback_path = None

for path in feedback_paths:
    try:
        module_path, class_name = path.rsplit('.', 1)
        exec(f"from {module_path} import {class_name}")
        print(f"✅ {path} - 成功！")
        working_feedback_path = path
        break
    except ImportError as e:
        print(f"❌ {path} - 失敗: {e}")
    except Exception as e:
        print(f"⚠️  {path} - 其他錯誤: {e}")

# 探索 OpenAI Provider 路徑
provider_paths = [
    "trulens.providers.openai.OpenAI",
    "trulens_eval.feedback.provider.openai.OpenAI",
    "trulens_eval.providers.openai.OpenAI",
    "trulens.feedback.provider.openai.OpenAI",
    "trulens_feedback.provider.openai.OpenAI",
]

print("\n🤖 測試 OpenAI Provider 匯入路徑:")
working_provider_path = None

for path in provider_paths:
    try:
        module_path, class_name = path.rsplit('.', 1)
        exec(f"from {module_path} import {class_name}")
        print(f"✅ {path} - 成功！")
        working_provider_path = path
        break
    except ImportError as e:
        print(f"❌ {path} - 失敗: {e}")
    except Exception as e:
        print(f"⚠️  {path} - 其他錯誤: {e}")

# 如果找到正確路徑，進行功能測試
print("\n🧪 功能測試:")

if working_feedback_path:
    print(f"\n📊 測試 Feedback 功能 (使用 {working_feedback_path}):")
    try:
        module_path, class_name = working_feedback_path.rsplit('.', 1)
        exec(f"from {module_path} import {class_name} as Feedback")
        
        # 建立簡單的評估函數
        def simple_evaluation(text: str) -> float:
            """基於文字長度的簡單評估"""
            return min(len(text) / 50.0, 1.0)
        
        feedback = Feedback(simple_evaluation)
        test_result = feedback("這是一個測試文字，用來檢查 Feedback 功能是否正常運作。")
        
        print(f"✅ Feedback 功能測試成功！評分: {test_result}")
        
    except Exception as e:
        print(f"❌ Feedback 功能測試失敗: {e}")

if working_provider_path:
    print(f"\n🤖 測試 OpenAI Provider 功能 (使用 {working_provider_path}):")
    try:
        module_path, class_name = working_provider_path.rsplit('.', 1)
        exec(f"from {module_path} import {class_name} as OpenAI")
        
        # 檢查是否需要 API Key
        import os
        if os.getenv('OPENAI_API_KEY'):
            provider = OpenAI()
            print("✅ OpenAI Provider 建立成功！")
        else:
            print("⚠️  OpenAI Provider 可匯入，但需要 OPENAI_API_KEY 環境變數")
            
    except Exception as e:
        print(f"❌ OpenAI Provider 測試失敗: {e}")

# 生成修正後的匯入程式碼
print("\n" + "=" * 50)
print("🎯 修正結果總結:")

if working_feedback_path or working_provider_path:
    print("\n✅ 找到可用的匯入路徑！")
    print("\n📝 建議的正確匯入方式:")
    
    if working_feedback_path:
        module_path, class_name = working_feedback_path.rsplit('.', 1)
        print(f"# Feedback 功能")
        print(f"from {module_path} import {class_name}")
        
    if working_provider_path:
        module_path, class_name = working_provider_path.rsplit('.', 1)
        print(f"# OpenAI Provider")
        print(f"from {module_path} import {class_name}")
        
    print(f"\n🔄 接下來可以更新 trulens_test.py 使用正確的匯入路徑")
        
else:
    print("\n❌ 未找到可用的匯入路徑")
    print("建議檢查 TruLens 版本和安裝狀態")

print("\n🚀 準備更新測試腳本...")