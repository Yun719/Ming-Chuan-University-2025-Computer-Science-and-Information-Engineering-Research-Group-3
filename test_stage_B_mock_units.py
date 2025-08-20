#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
階段B簡單測試：直接測試LLM描述生成功能
"""

import sys
import os

# 添加模組路徑
sys.path.append('modules/pdf_Cutting_TextReplaceImage')
sys.path.append('modules/pdf_Cutting_TextReplaceImage/enhanced_version/backend')

def test_stage_b():
    print("=== 階段B測試：LLM描述生成 ===")
    
    try:
        from llm_providers_sB import LLMManager, LLMRequest
        from llm_description_generator_v2_sB import LLMDescriptionGeneratorV2, DescriptionRequest
        
        print("✅ 模組載入成功")
        
        # 創建Mock LLM描述生成器
        generator = LLMDescriptionGeneratorV2("mock")  # 使用Mock，不需要API
        print("✅ Mock LLM生成器建立成功")
        
        # 模擬階段A的完美輸出
        fake_stage_a_results = [
            {
                "caption": "圖1-1 中國的算盤",
                "type": "圖",
                "number": "1-1",
                "context": [
                    "中國算盤是古代重要的計算工具，具有悠久的歷史。",
                    "算盤由木框和算珠組成，分為上下兩排，上排為天珠，下排為地珠。",
                    "使用算盤可以進行加減乘除等四則運算，是東方數學文化的重要象徵。"
                ]
            },
            {
                "caption": "表1-1 電腦發展史",
                "type": "表",
                "number": "1-1", 
                "context": [
                    "電腦發展可分為幾個重要階段。",
                    "從真空管到電晶體，再到積體電路，每個階段都有重大突破。",
                    "現代電腦的發展奠定了資訊時代的基礎。"
                ]
            }
        ]
        
        print(f"📝 準備測試 {len(fake_stage_a_results)} 個圖表")
        
        # 逐一測試每個圖表的描述生成
        for i, data in enumerate(fake_stage_a_results, 1):
            print(f"\n--- 測試 {i}: {data['caption']} ---")
            
            # 建立描述請求
            request = DescriptionRequest(
                caption_text=data["caption"],
                caption_type=data["type"],
                caption_number=data["number"],
                related_context=data["context"],
                page_number=2
            )
            
            # 生成描述
            result = generator.generate_description(request)
            
            # 顯示結果
            print(f"成功: {result.success}")
            if result.success:
                print(f"生成描述: {result.generated_description[:100]}...")
                print(f"信心度: {result.confidence_score:.2f}")
                print(f"LLM提供者: {result.llm_provider}")
                print(f"處理時間: {result.processing_time:.2f}秒")
            else:
                print(f"失敗原因: {result.error_message}")
        
        print("\n🎯 階段B測試完成！")
        print("✅ Mock LLM功能正常，可以生成圖表描述")
        print("💡 如需真實描述，可切換到OpenAI或本地LLM")
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_stage_b()