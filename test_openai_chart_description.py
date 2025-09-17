#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試OpenAI圖表描述功能
"""

import sys
import os
from pathlib import Path

# 添加模組路徑
sys.path.append('modules/pdf_Cutting_TextReplaceImage')
sys.path.append('modules/pdf_Cutting_TextReplaceImage/enhanced_version/backend')

def test_openai_provider():
    """測試OpenAI提供者是否可用"""
    print("測試OpenAI提供者...")

    try:
        from llm_providers_sB import OpenAIProvider

        provider = OpenAIProvider()
        is_available = provider.is_available()

        print(f"OpenAI API Key 設定: {'是' if provider.api_key else '否'}")
        print(f"Base URL: {provider.base_url}")
        print(f"提供者可用: {'是' if is_available else '否'}")

        return is_available

    except Exception as e:
        print(f"測試OpenAI提供者失敗: {e}")
        return False

def test_llm_description_generator():
    """測試LLM描述生成器"""
    print("\n測試LLM描述生成器...")

    try:
        from llm_description_generator_v2_sB import LLMDescriptionGeneratorV2, DescriptionRequest

        # 初始化生成器（現在預設使用OpenAI）
        generator = LLMDescriptionGeneratorV2()

        current_provider = generator.get_current_provider()
        print(f"當前使用的LLM提供者: {current_provider}")

        # 如果是OpenAI，測試一個簡單的描述生成
        if current_provider == "OpenAI":
            print("測試OpenAI描述生成...")

            # 建立測試請求
            test_request = DescriptionRequest(
                caption_text="中國的算盤",
                caption_type="figure",
                caption_number="1.1",
                related_context=["計算機的發展歷史", "古代計算工具"],
                page_number=2
            )

            # 生成描述
            result = generator.generate_description(test_request)

            if result.success:
                print("OpenAI描述生成成功!")
                print(f"生成描述: {result.generated_description[:200]}...")
                print(f"信心度: {result.confidence_score}")
                print(f"處理時間: {result.processing_time:.2f}秒")
                print(f"Token使用: {result.token_usage}")
                return True
            else:
                print(f"描述生成失敗: {result.error_message}")
                return False
        else:
            print(f"當前使用的是 {current_provider}，不是OpenAI")
            return current_provider != "MockLLM"

    except Exception as e:
        print(f"測試LLM描述生成器失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_env_configuration():
    """檢查環境配置"""
    print("檢查環境配置...")

    from dotenv import load_dotenv
    load_dotenv()

    openai_key = os.getenv('OPENAI_API_KEY')
    openai_base = os.getenv('OPENAI_BASE_URL')

    print(f"OPENAI_API_KEY 設定: {'是' if openai_key else '否'}")
    print(f"OPENAI_BASE_URL: {openai_base or '預設'}")

    if not openai_key:
        print("警告: 未設定OPENAI_API_KEY，請檢查.env檔案")
        return False

    return True

def main():
    """主測試函數"""
    print("=" * 50)
    print("OpenAI圖表描述功能測試")
    print("=" * 50)

    # 1. 檢查環境配置
    env_ok = test_env_configuration()

    # 2. 測試OpenAI提供者
    provider_ok = test_openai_provider()

    # 3. 測試LLM描述生成器
    generator_ok = test_llm_description_generator()

    # 總結
    print("\n" + "=" * 50)
    print("測試結果總結")
    print("=" * 50)

    results = {
        "環境配置": env_ok,
        "OpenAI提供者": provider_ok,
        "描述生成器": generator_ok
    }

    for name, success in results.items():
        status = "通過" if success else "失敗"
        print(f"{name}: {status}")

    all_ok = all(results.values())
    print(f"\n整體狀態: {'所有測試通過' if all_ok else '部分測試失敗'}")

    if all_ok:
        print("\n圖表描述已成功切換到OpenAI模型!")
        print("現在可以重新運行圖表處理流程來獲得更高品質的描述。")
    else:
        print("\n需要檢查以下問題:")
        for name, success in results.items():
            if not success:
                print(f"  - {name}")

if __name__ == "__main__":
    main()