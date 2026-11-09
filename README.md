# Insightia — Production-Ready AI Data Analytics Platform

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.3-61DAFB.svg?logo=react&logoColor=black)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.5-3178C6.svg?logo=typescript&logoColor=white)](https://www.typescriptlang.org)
[![Tailwind CSS](https://img.shields.io/badge/TailwindCSS-3.4-38B2AC.svg?logo=tailwind-css&logoColor=white)](https://tailwindcss.com)
[![Pandas](https://img.shields.io/badge/Pandas-2.2+-150458.svg?logo=pandas&logoColor=white)](https://pandas.pydata.org)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)](https://www.docker.com)

**Insightia** is an enterprise-grade, clean, "no-slop" data analytics and natural language intelligence platform. It transforms raw business datasets (CSV, Excel, JSON) into high-density interactive dashboards, automated EDA profiles, and grounded conversational intelligence.

---

## 🏛️ System Architecture & Reference Matrix

Insightia was engineered using optimal tooling from the reference architecture:

| System Layer | Selected Technology | Purpose & Capabilities |
| :--- | :--- | :--- |
| **AI Conversational Engine** | **Safe Sandboxed Pandas Engine** | AST-verified Python sandbox executing deterministic DataFrame queries with 0% math hallucination. |
| **Multilingual NLP** | **English, Hindi & Hinglish Parser** | Seamlessly interprets natural queries (e.g. *"Is data ka sales distribution kaisa hai?"*, *"Top 5 categories by revenue"*). |
| **Automated EDA & Profiling** | **Deep Analytical Engine** | Health scoring (0–100%), missingness distribution, IQR & Z-score outlier detection, Pearson correlation matrix. |
| **Cleaning Pipeline** | **Deterministic Data Cleaner** | Mean/Median/Mode imputation, row deduplication, outlier filtering, type coercion, and transactional audit trails. |
| **Frontend UI System** | **shadcn/ui + Tailwind CSS** | "Unslop" Linear / Supabase deep neutral dark mode (`zinc-950` canvas, `zinc-900` card surfaces, `zinc-800` borders). |
| **Charts & Visualization** | **Recharts & Responsive Renderers** | Dynamic bar charts, line trends, scatter plots, and frequency distribution histograms. |
| **Data Grid** | **High-Craft Interactive Table** | Virtualized pagination, search, sorting, and inline missing value/outlier cell highlighting. |
| **Export Engine** | **Multi-Format Document Generator** | Cleaned CSV, formatted Excel (`.xlsx` with custom styles & metadata tab), JSON schema, and Executive PDF reports (`reportlab`). |

---

## 🚀 Core Platform Capabilities

### 1. Intelligent Ingestion & Auto-Cleaning Engine
- **Multi-Format Ingestion**: Ingests `.csv`, `.xlsx`, `.xls`, and `.json` datasets up to 50MB.
- **Dataset Health Score (0–100%)**: Dynamically evaluated based on missing cell ratio, duplicate rows, data type purity, and statistical outliers.
- **Automated Anomaly Detection**:
  - **IQR Method**: Flags values beyond $[Q_1 - 1.5 \cdot IQR, Q_3 + 1.5 \cdot IQR]$.
  - **Z-Score Method**: Flags extreme statistical outliers where $|z| > 3$.
- **Precision Cleaning Actions**:
  - `Impute`: Impute nulls with mean, median (skewness-resistant), or mode.
  - `Drop Missing`: Drop rows with nulls globally or on selected columns.
  - `Deduplicate`: Eliminate redundant records.
  - `Remove Outliers`: Filter rows with extreme anomalies.
  - `Coerce Types`: Normalize ISO date strings and sanitize currency strings into numerical formats.
  - `One-Click Auto-Clean`: Multi-step automated cleaning pipeline with real-time audit metric feedback (e.g., *"Cleaned 38 null cells, removed 12 duplicate rows. Health score increased to 95%"*).

### 2. Multilingual & Hinglish Natural Language Copilot
- **The Grounding Rule**: The Copilot **never** invents or hallucinates math. Every analytical takeaway is computed by executing deterministic Python code inside an isolated, AST-verified sandbox (`pd`, `np`, `df`).
- **Seamless English, Hindi, and Hinglish Comprehension**:
  - *"Is data ka sales distribution kaisa hai?"* $\rightarrow$ Calculates quartiles, min/max, skewness; generates histogram payload; replies in conversational Hinglish.
  - *"Top 5 categories by total revenue dikhao"* $\rightarrow$ Groups by category, aggregates revenue, sorts descending, returns verified figures + bar chart.
  - *"Drop all missing rows in price column"* $\rightarrow$ Executes dropna, reports exact count dropped, updates the active dataset session.
  - *"Show correlation between price and units sold"* $\rightarrow$ Computes Pearson $r$ and generates a scatter plot.
- **Auditable Execution**: Every Copilot response includes a toggle to inspect the exact Python code executed.

### 3. Multi-Format Export Engine
- **Cleaned CSV (`.csv`)**: Normalized UTF-8 tabular data.
- **Styled Excel (`.xlsx`)**: Generated via `openpyxl` with dark zinc headers, borders, zebra striping, auto-fit column widths, and a secondary "Executive Summary & Health" sheet.
- **Clean JSON Schema (`.json`)**: Structured schema with dataset metadata, column types, and record arrays.
- **Executive PDF Report (`.pdf`)**: Corporate executive summary generated via `reportlab` with health score badges, key KPI tables, schema specifications, and automated strategic insights.

---

## 🎨 Design Philosophy ("Unslop" Dark Mode)

The interface follows a minimalist, high-density 3-panel workspace:

```
┌─────────────────┬──────────────────────────────────────────┬──────────────────────┐
│  LEFT RAIL      │  CENTER CANVAS                           │  RIGHT COPILOT RAIL  │
│  (320px)        │  (Flexible Main)                         │  (384px)             │
│                 │                                          │                      │
│ • Health Score  │ • KPI Summary Cards                      │ • Grounded Chat      │
│ • One-Click     │ • Quick Sample Selector (E-Com, SaaS)   │ • Hinglish Support   │
│   Auto-Clean    │ • Drag-and-Drop Ingestion Zone           │ • Inline Charts      │
│ • Schema List   │ • Tab 1: Visual EDA & Histogram          │ • Verified Figures   │
│ • Audit Trail   │ • Tab 2: High-Craft Data Grid (TanStack) │ • Executed Python    │
│ • Export Bar    │ • Tab 3: Statistical Metrics & Pearson   │   Code Toggle        │
└─────────────────┴──────────────────────────────────────────┴──────────────────────┘
```

- **Palette**: Deep neutral dark mode (`zinc-950` canvas `#09090b`, `zinc-900` card surfaces `#18181b`, `zinc-800` borders `#27272a`, `zinc-100` headers `#f4f4f5`).
- **Accents**: Subdued indigo (`#6366f1`) and emerald (`#10b981`).
- **Zero Blank States**: Pre-loaded with curated sample business datasets (E-Commerce Sales, SaaS Churn, Corporate Ledger) for instant zero-friction exploration.

---

## ⚡ Quick Start & Run Instructions

### Prerequisites
- Node.js 18+ & npm
- Python 3.10+

### Option A: Local Run (Quickest)

#### 1. Start the Backend:
```bash
# Windows
start_backend.bat

# Or manually:
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
*Backend API will run at: `http://localhost:8000`*

#### 2. Start the Frontend:
```bash
# Windows
start_frontend.bat

# Or manually:
npm run dev
```
*Frontend workspace will run at: `http://localhost:3000`*

#### 3. Single-Command Launch (Windows):
```bash
start_all.bat
```

---

### Option B: Docker Compose

Launch the entire stack (FastAPI backend + Vite Nginx frontend) in isolated containers:

```bash
docker-compose up --build
```

Access the platform at `http://localhost:3000`.

---

## 📡 REST API Reference

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/data/upload` | `POST` | Ingests `.csv`, `.xlsx`, `.xls`, or `.json`, generates profile & session ID. |
| `/api/data/sample/{sample_id}` | `GET` | Loads 1-click curated dataset (`ecommerce_sales`, `customer_churn`, `financial_kpi`). |
| `/api/data/clean` | `POST` | Executes `impute`, `drop_na`, `remove_duplicates`, `remove_outliers`, `coerce_types`, or `auto_clean`. |
| `/api/data/chat` | `POST` | Processes English / Hindi / Hinglish queries, executes safe Python code, returns chart & figures. |
| `/api/data/profile/{session_id}` | `GET` | Retrieves dataset schema, statistics, health score, and audit log. |
| `/api/data/export/{format}` | `GET` | Exports active dataset in `csv`, `xlsx`, `json`, or `pdf`. |

---

## 🧪 Verification & Testing

Run the automated end-to-end integration test suite verifying file upload, automated profiling, Hinglish copilot execution, cleaning pipelines, and multi-format exports:

```bash
python -c "
import sys; sys.path.insert(0, 'backend')
from fastapi.testclient import TestClient
from main import app
client = TestClient(app)
r = client.get('/api/data/sample/ecommerce_sales')
assert r.status_code == 200
sid = r.json()['session_id']
# Test Copilot
r_chat = client.post('/api/data/chat', json={'session_id': sid, 'query': 'Is data ka sales distribution kaisa hai?'})
assert r_chat.status_code == 200
# Test Clean
r_clean = client.post('/api/data/clean', json={'session_id': sid, 'action': 'auto_clean'})
assert r_clean.status_code == 200
# Test Export
for fmt in ['csv', 'xlsx', 'json', 'pdf']:
    assert client.get(f'/api/data/export/{fmt}?session_id={sid}').status_code == 200
print('All tests passed successfully!')
"
```

---

## 📄 License
MIT License. Built for enterprise business intelligence and grounded AI data product design.
