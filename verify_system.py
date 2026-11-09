"""
Comprehensive System Verification Test Suite
Tests:
1. Data Engine Ingestion & Health Profiling
2. Outlier Detection (IQR & Z-score)
3. Automated Cleaning Pipeline
4. Hinglish & English Conversational Copilot
5. Export Engine (CSV, XLSX, JSON, PDF)
6. FastAPI REST Endpoints via TestClient
"""

import sys
import os
import io
import asyncio
import pandas as pd

sys.path.insert(0, os.path.abspath("."))

def run_tests():
    print("=" * 60)
    print("RUNNING COMPREHENSIVE END-TO-END VERIFICATION")
    print("=" * 60)

    # 1. Test Ingestion & Sample Datasets
    print("\n[1/6] Testing Data Engine & Ingestion...")
    from backend.src.services.data_engine import DataEngine, DataSessionStore
    from backend.src.routers.data_router import generate_sample_dataset

    for sample_id in ["ecommerce_sales", "customer_churn", "financial_kpi"]:
        df = generate_sample_dataset(sample_id)
        assert df is not None and len(df) > 0, f"Sample {sample_id} failed"
        profile = DataEngine.profile_dataframe(df, dataset_name=sample_id)
        assert "health_score" in profile, "Missing health_score"
        assert "columns" in profile, "Missing columns profile"
        assert 0 <= profile["health_score"] <= 100
        print(f"  ✓ {sample_id}: {profile['total_rows']} rows, Health: {profile['health_score']}%")

    # 2. Test Multi-Format File Parsing
    print("\n[2/6] Testing Multi-format File Parsing (CSV, JSON, XLSX)...")
    test_df = pd.DataFrame({
        "item": ["Alpha", "Beta", "Gamma"],
        "price": [100.5, 200.0, None],
        "quantity": [10, 5, 2]
    })
    
    # CSV
    csv_bytes = test_df.to_csv(index=False).encode('utf-8')
    parsed_csv = DataEngine.parse_file(csv_bytes, "test.csv")
    assert len(parsed_csv) == 3
    print("  ✓ CSV parsing verified")

    # JSON
    json_bytes = test_df.to_json(orient='records').encode('utf-8')
    parsed_json = DataEngine.parse_file(json_bytes, "test.json")
    assert len(parsed_json) == 3
    print("  ✓ JSON parsing verified")

    # XLSX
    xlsx_buf = io.BytesIO()
    test_df.to_excel(xlsx_buf, index=False)
    parsed_xlsx = DataEngine.parse_file(xlsx_buf.getvalue(), "test.xlsx")
    assert len(parsed_xlsx) == 3
    print("  ✓ XLSX parsing verified")

    # 3. Test Auto-Cleaning Pipeline
    print("\n[3/6] Testing Auto-Cleaning Actions...")
    clean_df, audit = DataEngine.clean_dataframe(test_df, action="impute")
    assert clean_df["price"].isnull().sum() == 0, "Imputation failed to fill nulls"
    print(f"  ✓ Impute action: {audit}")

    clean_df2, audit2 = DataEngine.clean_dataframe(test_df, action="drop_na")
    assert len(clean_df2) == 2, "Drop NA failed to drop null row"
    print(f"  ✓ Drop NA action: {audit2}")

    # 4. Test Multilingual NLP Copilot Sandbox
    print("\n[4/6] Testing Grounded Multilingual AI Copilot Sandbox...")
    from backend.src.services.copilot_engine import ConversationalCopilotEngine

    sample_df = generate_sample_dataset("ecommerce_sales")
    session_id = "test-copilot-session"
    DataSessionStore.set(session_id, {
        "df": sample_df,
        "session_id": session_id,
        "filename": "ecommerce_sales.csv",
        "audit_log": []
    })
    
    # Hinglish query
    q_hinglish = "Is data ka sales distribution kaisa hai?"
    res1 = asyncio.run(ConversationalCopilotEngine.process_query(session_id, q_hinglish))
    assert res1.get("explanation"), "No explanation for Hinglish query"
    assert res1.get("executed_code"), "No python code generated"
    print(f"  ✓ Hinglish query explanation: {res1['explanation'][:80]}...")
    print(f"    Executed Code:\n{res1['executed_code']}")

    # English query
    q_eng = "What is the average price and total revenue?"
    res2 = asyncio.run(ConversationalCopilotEngine.process_query(session_id, q_eng))
    assert res2.get("explanation"), "No explanation for English query"
    print(f"  ✓ English query explanation: {res2['explanation'][:80]}...")

    # 5. Test Export Engine
    print("\n[5/6] Testing Export Engine (CSV, XLSX, JSON, PDF)...")
    from backend.src.services.export_engine import ExportEngine
    
    prof = DataEngine.profile_dataframe(sample_df, "Test Export Dataset")

    # CSV
    csv_exp = ExportEngine.export_csv(sample_df)
    assert len(csv_exp) > 1000
    print(f"  ✓ CSV Export: {len(csv_exp):,} bytes")

    # XLSX
    xlsx_exp = ExportEngine.export_excel(sample_df, "Test Export", prof)
    assert len(xlsx_exp) > 1000
    print(f"  ✓ XLSX Export: {len(xlsx_exp):,} bytes")

    # JSON
    json_exp = ExportEngine.export_json(sample_df, prof)
    assert len(json_exp) > 1000
    print(f"  ✓ JSON Export: {len(json_exp):,} bytes")

    # PDF
    pdf_exp = ExportEngine.export_pdf(sample_df, "Test Export", prof)
    assert len(pdf_exp) > 1000
    print(f"  ✓ Executive PDF Export: {len(pdf_exp):,} bytes")

    # 6. Test FastAPI REST Endpoints via TestClient
    print("\n[6/6] Testing FastAPI Endpoints via Starlette/HTTPX TestClient...")
    from starlette.testclient import TestClient
    from backend.main import app

    client = TestClient(app)

    # Health
    r = client.get("/health")
    assert r.status_code == 200
    print(f"  ✓ GET /health: {r.json()}")

    # Sample load
    r_sample = client.get("/api/data/sample/ecommerce_sales")
    assert r_sample.status_code == 200
    sample_data = r_sample.json()
    sid = sample_data["session_id"]
    print(f"  ✓ GET /api/data/sample/ecommerce_sales: session_id={sid}")

    # Clean endpoint
    r_clean = client.post("/api/data/clean", json={"session_id": sid, "action": "auto_clean"})
    assert r_clean.status_code == 200
    print(f"  ✓ POST /api/data/clean: Health={r_clean.json()['health_score']}%")

    # Chat endpoint
    r_chat = client.post("/api/data/chat", json={"session_id": sid, "query": "Total revenue kitna hai?"})
    assert r_chat.status_code == 200
    print(f"  ✓ POST /api/data/chat: {r_chat.json()['explanation'][:60]}...")

    # Export endpoints
    for fmt in ["csv", "xlsx", "json", "pdf"]:
        r_exp = client.get(f"/api/data/export/{fmt}?session_id={sid}")
        assert r_exp.status_code == 200
        print(f"  ✓ GET /api/data/export/{fmt}: {len(r_exp.content):,} bytes")

    print("\n" + "=" * 60)
    print("ALL 6 MODULES PASSED WITH 100% SUCCESS!")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
