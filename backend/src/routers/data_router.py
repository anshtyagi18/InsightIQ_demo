"""
Data & Analytics Router for Insightia.
Provides RESTful APIs for file ingestion, automated EDA, data cleaning pipelines,
multilingual AI copilot, and multi-format exports.
Supports both /api/* and /api/data/* paths for maximum client compatibility.
"""

import io
import uuid
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from fastapi import APIRouter, File, HTTPException, Query, Response, UploadFile
from fastapi.responses import JSONResponse, Response, StreamingResponse
from pydantic import BaseModel

from ..services.copilot_engine import ConversationalCopilotEngine
from ..services.data_engine import DataEngine, DataSessionStore, sanitize_value
from ..services.export_engine import ExportEngine

# 1. Primary router with prefix /api/data
router = APIRouter(prefix="/api/data", tags=["Data Intelligence & Analytics"])

# 2. Direct router with prefix /api for direct /api/upload, /api/clean, etc.
api_router = APIRouter(prefix="/api", tags=["Insightia Direct Core Endpoints"])


class CleanRequest(BaseModel):
    session_id: str
    action: str  # 'impute', 'drop_na', 'remove_duplicates', 'remove_outliers', 'coerce_types', 'auto_clean'
    params: Optional[Dict[str, Any]] = None


class ChatRequest(BaseModel):
    session_id: str
    query: str


def generate_sample_dataset(sample_id: str) -> pd.DataFrame:
    """Generate realistic business datasets for zero-friction exploration."""
    np.random.seed(42)

    if sample_id == "ecommerce_sales":
        categories = ["Electronics", "Fashion", "Home & Living", "Health & Beauty", "Automotive", "Books & Media"]
        regions = ["North America", "Europe", "Asia-Pacific", "Latin America", "Middle East"]
        products = {
            "Electronics": ["Pro Laptop 15", "Wireless Earbuds", "4K Ultra Monitor", "Smart Fitness Band", "Mechanical Keyboard"],
            "Fashion": ["Merino Wool Sweater", "Denim Jacket", "Performance Running Shoes", "Leather Messenger Bag", "Silk Scarf"],
            "Home & Living": ["Ergonomic Desk Chair", "Espresso Coffee Machine", "Smart LED Lamp", "Aroma Diffuser", "Ceramic Cookware Set"],
            "Health & Beauty": ["Hydrating Serum", "Organic Vitamin C", "Deep Clean Face Wash", "SPF 50 Sunscreen", "Bamboo Toothbrush"],
            "Automotive": ["Dashcam HD", "Tire Pressure Gauge", "Car Vacuum Cleaner", "Bluetooth FM Transmitter", "Emergency Tool Kit"],
            "Books & Media": ["Data Science Handbook", "AI Architecture Bible", "Clean Code Principles", "Economics in One Lesson", "Design Patterns"]
        }

        n = 1000
        cats = np.random.choice(categories, n, p=[0.25, 0.22, 0.18, 0.15, 0.10, 0.10])
        prods = [np.random.choice(products[c]) for c in cats]
        regs = np.random.choice(regions, n, p=[0.35, 0.25, 0.25, 0.10, 0.05])
        
        base_prices = {
            "Electronics": (80.0, 1200.0),
            "Fashion": (25.0, 220.0),
            "Home & Living": (30.0, 450.0),
            "Health & Beauty": (12.0, 95.0),
            "Automotive": (15.0, 180.0),
            "Books & Media": (10.0, 60.0),
        }
        prices = [round(float(np.random.uniform(*base_prices[c])), 2) for c in cats]
        quantities = np.random.geometric(p=0.4, size=n)
        discounts = np.random.choice([0.0, 0.05, 0.10, 0.15, 0.20], n, p=[0.45, 0.20, 0.15, 0.12, 0.08])
        revenues = [round(p * q * (1 - d), 2) for p, q, d in zip(prices, quantities, discounts)]
        ratings = np.clip(np.random.normal(4.2, 0.7, n), 1.0, 5.0).round(1)

        dates = pd.date_range(start="2026-01-01", periods=n, freq="4h").strftime("%Y-%m-%d").tolist()

        df = pd.DataFrame({
            "Transaction_ID": [f"TXN-{10000 + i}" for i in range(n)],
            "Date": dates,
            "Category": cats,
            "Product": prods,
            "Region": regs,
            "Price": prices,
            "Quantity": quantities,
            "Discount": discounts,
            "Revenue": revenues,
            "Customer_Rating": ratings,
        })

        # Inject realistic imperfections for demonstration:
        # 1. Null values in Price & Customer_Rating
        null_indices = np.random.choice(n, 38, replace=False)
        df.loc[null_indices[:20], "Price"] = np.nan
        df.loc[null_indices[20:], "Customer_Rating"] = np.nan
        # 2. Duplicate rows
        dup_rows = df.iloc[np.random.choice(n, 12, replace=False)].copy()
        df = pd.concat([df, dup_rows], ignore_index=True)
        # 3. Extreme outliers in Revenue
        outlier_indices = np.random.choice(len(df), 5, replace=False)
        df.loc[outlier_indices, "Revenue"] = df.loc[outlier_indices, "Revenue"] * 12.5

        return df

    elif sample_id == "customer_churn":
        n = 850
        contract_types = ["Month-to-Month", "One Year", "Two Year"]
        payment_methods = ["Credit Card", "Bank Transfer", "Electronic Check", "Mailed Check"]
        
        tenures = np.random.randint(1, 72, size=n)
        monthly_charges = np.random.uniform(20.0, 125.0, size=n).round(2)
        total_charges = (tenures * monthly_charges * np.random.uniform(0.95, 1.05, size=n)).round(2)
        churn_prob = np.where(tenures < 12, 0.45, 0.15)
        churn = np.random.binomial(1, churn_prob)
        support_calls = np.random.poisson(lam=1.8, size=n)

        df = pd.DataFrame({
            "Customer_ID": [f"CUST-{2000 + i}" for i in range(n)],
            "Contract": np.random.choice(contract_types, n, p=[0.55, 0.25, 0.20]),
            "Payment_Method": np.random.choice(payment_methods, n),
            "Tenure_Months": tenures,
            "Monthly_Charges": monthly_charges,
            "Total_Charges": total_charges,
            "Support_Calls": support_calls,
            "Churn": ["Yes" if c == 1 else "No" for c in churn],
        })

        # Inject some nulls in Total_Charges
        df.loc[np.random.choice(n, 25, replace=False), "Total_Charges"] = np.nan
        return df

    else:
        # Default financial ledger
        n = 500
        depts = ["Engineering", "Marketing", "Sales", "Operations", "Product", "Human Resources"]
        quarters = ["Q1-2026", "Q2-2026", "Q3-2026", "Q4-2026"]
        budgets = np.random.uniform(50000, 750000, n).round(2)
        actuals = (budgets * np.random.normal(0.98, 0.12, n)).round(2)
        variance = (actuals - budgets).round(2)

        df = pd.DataFrame({
            "Ledger_ID": [f"LED-{5000 + i}" for i in range(n)],
            "Department": np.random.choice(depts, n),
            "Fiscal_Quarter": np.random.choice(quarters, n),
            "Budget_Allocated": budgets,
            "Actual_Spend": actuals,
            "Spend_Variance": variance,
            "Headcount": np.random.randint(5, 120, n),
            "ROI_Multiple": np.random.uniform(1.1, 4.5, n).round(2)
        })
        return df


# -------------------------------------------------------------
# Core Handler Functions (shared across /api/data/* and /api/*)
# -------------------------------------------------------------

async def handle_upload(file: UploadFile, preview_rows: int = 50):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file filename provided.")

    try:
        content = await file.read()
        if len(content) == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

        df = DataEngine.parse_file(content, file.filename)
        session_id = str(uuid.uuid4())

        # Register in session store
        DataSessionStore.set(session_id, {
            "session_id": session_id,
            "filename": file.filename,
            "file_size": len(content),
            "df": df,
            "audit_log": [{
                "timestamp": pd.Timestamp.now().isoformat(),
                "message": f"Initial file ingestion: {file.filename} ({len(df)} rows, {len(df.columns)} columns)",
                "rows": len(df),
                "cols": len(df.columns)
            }]
        })

        profile = DataEngine.profile_dataframe(df, dataset_name=file.filename)
        profile["session_id"] = session_id
        profile["file_size_bytes"] = len(content)

        return JSONResponse(status_code=200, content=profile)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process dataset: {str(e)}")


async def handle_load_sample(sample_id: str):
    valid_samples = ["ecommerce_sales", "customer_churn", "financial_kpi"]
    if sample_id not in valid_samples:
        sample_id = "ecommerce_sales"

    dataset_names = {
        "ecommerce_sales": "Global E-Commerce Transactions (2026)",
        "customer_churn": "SaaS Customer Churn & Lifetime Value",
        "financial_kpi": "Corporate Financial & Budget Ledger"
    }

    df = generate_sample_dataset(sample_id)
    session_id = str(uuid.uuid4())
    dataset_name = dataset_names.get(sample_id, "Sample Dataset")

    DataSessionStore.set(session_id, {
        "session_id": session_id,
        "filename": dataset_name,
        "df": df,
        "audit_log": [{
            "timestamp": pd.Timestamp.now().isoformat(),
            "message": f"Loaded curated sample: {dataset_name} ({len(df)} rows, {len(df.columns)} columns)",
            "rows": len(df),
            "cols": len(df.columns)
        }]
    })

    profile = DataEngine.profile_dataframe(df, dataset_name=dataset_name)
    profile["session_id"] = session_id
    profile["sample_id"] = sample_id

    return JSONResponse(status_code=200, content=profile)


async def handle_clean(request: CleanRequest):
    df = DataSessionStore.get_df(request.session_id)
    if df is None:
        raise HTTPException(status_code=404, detail="Dataset session not found or expired. Please upload data.")

    old_score = DataEngine.profile_dataframe(df).get("health_score", 100)

    try:
        cleaned_df, audit_entry = DataEngine.clean_dataframe(
            df,
            action=request.action,
            params=request.params or {}
        )

        DataSessionStore.update_df(request.session_id, cleaned_df, audit_entry)

        session = DataSessionStore.get(request.session_id) or {}
        dataset_name = session.get("filename", "Dataset")
        new_profile = DataEngine.profile_dataframe(cleaned_df, dataset_name=dataset_name)
        new_profile["session_id"] = request.session_id
        new_profile["audit_entry"] = audit_entry
        new_profile["health_score_delta"] = new_profile.get("health_score", 100) - old_score
        new_profile["audit_log"] = session.get("audit_log", [])

        return JSONResponse(status_code=200, content=new_profile)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cleaning pipeline error: {str(e)}")


async def handle_chat(request: ChatRequest):
    df = DataSessionStore.get_df(request.session_id)
    if df is None:
        raise HTTPException(status_code=404, detail="Active dataset not found. Please upload a dataset first.")

    res = await ConversationalCopilotEngine.process_query(
        session_id=request.session_id,
        user_query=request.query,
        df=df
    )
    return JSONResponse(status_code=200, content=res)


async def handle_get_profile(session_id: str):
    df = DataSessionStore.get_df(session_id)
    if df is None:
        raise HTTPException(status_code=404, detail="Session not found.")

    session = DataSessionStore.get(session_id) or {}
    dataset_name = session.get("filename", "Dataset")
    profile = DataEngine.profile_dataframe(df, dataset_name=dataset_name)
    profile["session_id"] = session_id
    profile["audit_log"] = session.get("audit_log", [])
    return JSONResponse(status_code=200, content=profile)


async def handle_get_charts(
    session_id: str,
    chart_type: Optional[str] = None,
    column: Optional[str] = None,
    target_column: Optional[str] = None
):
    df = DataSessionStore.get_df(session_id)
    if df is None:
        raise HTTPException(status_code=404, detail="Session dataset not found.")

    charts = DataEngine.generate_charts_payload(
        df=df,
        chart_type=chart_type,
        column=column,
        target_column=target_column
    )
    return JSONResponse(status_code=200, content=charts)


async def handle_export(export_format: str, session_id: str):
    df = DataSessionStore.get_df(session_id)
    if df is None:
        raise HTTPException(status_code=404, detail="Session dataset not found.")

    session = DataSessionStore.get(session_id) or {}
    base_name = session.get("filename", "Insightia_Export").rsplit(".", 1)[0]
    profile = DataEngine.profile_dataframe(df, dataset_name=base_name)

    fmt = export_format.lower()
    if fmt == "csv":
        data = ExportEngine.export_csv(df)
        return Response(
            content=data,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={base_name}_cleaned.csv"}
        )
    elif fmt in ["xlsx", "excel"]:
        data = ExportEngine.export_excel(df, dataset_name=base_name, profile=profile)
        return Response(
            content=data,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={base_name}_formatted.xlsx"}
        )
    elif fmt == "json":
        data = ExportEngine.export_json(df, profile=profile)
        return Response(
            content=data,
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={base_name}_schema.json"}
        )
    elif fmt == "pdf":
        data = ExportEngine.export_pdf(df, dataset_name=base_name, profile=profile)
        return Response(
            content=data,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={base_name}_Executive_Report.pdf"}
        )
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {export_format}. Use csv, xlsx, json, or pdf.")


# -------------------------------------------------------------
# 1. Mount on /api/data/*
# -------------------------------------------------------------

@router.post("/upload")
async def router_upload(file: UploadFile = File(...), preview_rows: int = Query(50, ge=5, le=200)):
    return await handle_upload(file, preview_rows)

@router.get("/sample/{sample_id}")
async def router_sample(sample_id: str):
    return await handle_load_sample(sample_id)

@router.post("/clean")
async def router_clean(request: CleanRequest):
    return await handle_clean(request)

@router.post("/chat")
async def router_chat(request: ChatRequest):
    return await handle_chat(request)

@router.get("/profile/{session_id}")
async def router_profile_path(session_id: str):
    return await handle_get_profile(session_id)

@router.get("/profile")
async def router_profile_query(session_id: str = Query(...)):
    return await handle_get_profile(session_id)

@router.get("/charts")
async def router_charts(
    session_id: str = Query(...),
    chart_type: Optional[str] = Query(None),
    column: Optional[str] = Query(None),
    target_column: Optional[str] = Query(None)
):
    return await handle_get_charts(session_id, chart_type, column, target_column)

@router.get("/export/{export_format}")
async def router_export_path(export_format: str, session_id: str = Query(...)):
    return await handle_export(export_format, session_id)

@router.get("/export")
async def router_export_query(export_format: str = Query("csv"), session_id: str = Query(...)):
    return await handle_export(export_format, session_id)


# -------------------------------------------------------------
# 2. Mount on /api/* (Direct Endpoints)
# -------------------------------------------------------------

@api_router.post("/upload")
async def api_upload(file: UploadFile = File(...), preview_rows: int = Query(50, ge=5, le=200)):
    return await handle_upload(file, preview_rows)

@api_router.get("/sample/{sample_id}")
async def api_sample(sample_id: str):
    return await handle_load_sample(sample_id)

@api_router.post("/clean")
async def api_clean(request: CleanRequest):
    return await handle_clean(request)

@api_router.post("/chat")
async def api_chat(request: ChatRequest):
    return await handle_chat(request)

@api_router.get("/profile/{session_id}")
async def api_profile_path(session_id: str):
    return await handle_get_profile(session_id)

@api_router.get("/profile")
async def api_profile_query(session_id: str = Query(...)):
    return await handle_get_profile(session_id)

@api_router.get("/charts")
async def api_charts(
    session_id: str = Query(...),
    chart_type: Optional[str] = Query(None),
    column: Optional[str] = Query(None),
    target_column: Optional[str] = Query(None)
):
    return await handle_get_charts(session_id, chart_type, column, target_column)

@api_router.get("/export/{export_format}")
async def api_export_path(export_format: str, session_id: str = Query(...)):
    return await handle_export(export_format, session_id)

@api_router.get("/export")
async def api_export_query(export_format: str = Query("csv"), session_id: str = Query(...)):
    return await handle_export(export_format, session_id)
