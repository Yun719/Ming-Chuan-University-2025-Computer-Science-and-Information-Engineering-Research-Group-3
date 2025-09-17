#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ABC+main_web完整流程驗證測試 - 簡化版
驗證系統各部件是否正確協作
"""

import os
import json
import sys
from pathlib import Path

def check_stage_a():
    """檢查階段A（圖表識別）結果"""
    print("\n階段A檢查...")

    chart_file = Path("modules/pdf_Cutting_TextReplaceImage/chart_metadata.json")
    if not chart_file.exists():
        print("錯誤: 圖表元數據檔案不存在")
        return False

    try:
        with open(chart_file, 'r', encoding='utf-8') as f:
            chart_data = json.load(f)

        print(f"成功: 找到 {len(chart_data)} 個圖表")

        # 分析圖表類型
        types = {}
        for chart_id, info in chart_data.items():
            chart_type = info.get('chart_type', 'unknown')
            types[chart_type] = types.get(chart_type, 0) + 1

        print(f"圖表類型分布: {types}")
        return True

    except Exception as e:
        print(f"錯誤: {e}")
        return False

def check_stage_b():
    """檢查階段B（LLM描述生成）結果"""
    print("\n階段B檢查...")

    chart_file = Path("modules/pdf_Cutting_TextReplaceImage/chart_metadata.json")
    if not chart_file.exists():
        print("錯誤: 圖表元數據檔案不存在")
        return False

    try:
        with open(chart_file, 'r', encoding='utf-8') as f:
            chart_data = json.load(f)

        with_desc = 0
        total = len(chart_data)

        for chart_id, info in chart_data.items():
            if 'generated_description' in info and info['generated_description']:
                with_desc += 1

        success_rate = with_desc / total if total > 0 else 0
        print(f"成功: {with_desc}/{total} 個圖表有描述 ({success_rate:.1%})")

        if with_desc > 0:
            print("描述示例:")
            for i, (chart_id, info) in enumerate(chart_data.items()):
                if 'generated_description' in info and i < 2:
                    desc = info['generated_description'][:100] + "..." if len(info['generated_description']) > 100 else info['generated_description']
                    print(f"  {chart_id}: {desc}")

        return with_desc > 0

    except Exception as e:
        print(f"錯誤: {e}")
        return False

def check_stage_c():
    """檢查階段C（RAG整合）結果"""
    print("\n階段C檢查...")

    # 檢查增強向量索引
    index_path = Path("modules/pdf_Cutting_TextReplaceImage/enhanced_faiss_index")
    if not index_path.exists():
        print("錯誤: 增強向量索引目錄不存在")
        return False

    faiss_file = index_path / "index.faiss"
    pkl_file = index_path / "index.pkl"

    if faiss_file.exists() and pkl_file.exists():
        print("成功: 增強向量索引檔案存在")
        print(f"  FAISS索引: {faiss_file}")
        print(f"  PKL檔案: {pkl_file}")
        return True
    else:
        print("錯誤: 向量索引檔案不完整")
        return False

def check_main_web_integration():
    """檢查main_web整合狀況"""
    print("\nmain_web整合檢查...")

    # 檢查main_web.py是否包含圖表處理代碼
    main_web_file = Path("main_web.py")
    if not main_web_file.exists():
        print("錯誤: main_web.py 不存在")
        return False

    try:
        with open(main_web_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 檢查關鍵字
        keywords = [
            'chart_metadata.json',
            'chart_images',
            'CHARTS:',
            'is_chart_relevant'
        ]

        found_keywords = []
        for keyword in keywords:
            if keyword in content:
                found_keywords.append(keyword)

        print(f"成功: main_web.py 包含圖表處理功能")
        print(f"  找到關鍵字: {found_keywords}")

        return len(found_keywords) >= 3

    except Exception as e:
        print(f"錯誤: {e}")
        return False

def test_rag_system():
    """測試RAG系統是否可以載入"""
    print("\nRAG系統測試...")

    try:
        from RAG_Helper import RAGHelper
        rag = RAGHelper("pdfFiles")
        print("成功: RAG系統可以正常載入")

        # 簡單測試檢索
        if hasattr(rag, 'vectorstore') and rag.vectorstore:
            test_results = rag.vectorstore.similarity_search("圖1-1", k=3)
            print(f"成功: 向量檢索功能正常，找到 {len(test_results)} 個相關文檔")
            return True
        else:
            print("警告: 向量庫未正確載入")
            return False

    except Exception as e:
        print(f"錯誤: RAG系統載入失敗 - {e}")
        return False

def main():
    """主測試函數"""
    print("=" * 50)
    print("ABC+main_web 流程驗證測試")
    print("=" * 50)

    # 執行各階段檢查
    stage_a_ok = check_stage_a()
    stage_b_ok = check_stage_b()
    stage_c_ok = check_stage_c()
    main_web_ok = check_main_web_integration()
    rag_ok = test_rag_system()

    # 總結報告
    print("\n" + "=" * 50)
    print("測試結果總結")
    print("=" * 50)

    results = {
        "階段A (圖表識別)": stage_a_ok,
        "階段B (LLM描述生成)": stage_b_ok,
        "階段C (RAG整合)": stage_c_ok,
        "main_web整合": main_web_ok,
        "RAG系統": rag_ok
    }

    for name, success in results.items():
        status = "成功" if success else "失敗"
        print(f"{name}: {status}")

    all_ok = all(results.values())

    print(f"\n整體狀態: {'所有測試通過' if all_ok else '部分測試失敗'}")

    if all_ok:
        print("\n建議測試步驟:")
        print("1. 啟動Web伺服器: python main_web.py")
        print("2. 開啟瀏覽器訪問: http://localhost:8000")
        print("3. 測試以下問題:")
        print("   - 圖1-1是什麼？")
        print("   - 請說明表1-1的內容")
        print("   - 圖1-17顯示什麼？")
        print("4. 確認回答中是否包含圖表顯示")
    else:
        print("\n需要修復的問題:")
        for name, success in results.items():
            if not success:
                print(f"  - {name}")

if __name__ == "__main__":
    main()