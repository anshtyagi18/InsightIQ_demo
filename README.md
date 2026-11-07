# InsightIQ

InsightIQ is an AI-powered Business Intelligence (BI) and Analytics Platform designed to transform raw and structured datasets (Excel, CSV, JSON) into interactive, intelligent dashboards with automated insights, dynamic visualizations, and conversational data exploration.

---

## 🚀 Key Capabilities

### 📊 Dynamic Visualizations & Dashboards
- **Automated KPI & Metric Extraction**: Automatically detects key business drivers, summary metrics, and dimensional hierarchies.
- **Adaptive Chart Selection**: Intelligent mapping of data structures to optimal chart types (Line, Bar, Area, Scatter, Pie, and Composition charts).
- **Interactive Analytics Workspace**: Filter, sort, pivot, and drill down into dataset dimensions with responsive layouts.
- **Export & Reporting**: Multi-format reporting and data export capabilities.

### 🤖 AI-Powered Analytics & Discovery
- **Conversational Intelligence**: Ask natural-language questions about your data to generate on-the-fly calculations and chart responses.
- **Automated Trend & Anomaly Detection**: Statistical and machine-learning pattern recognition for variance, outliers, and momentum.
- **Estimated vs. Actual Variance Engine**: Semantic column matching, variance tracking, MAPE calculations, and correlation metrics.
- **Multi-Provider AI Resilience**: Integrated with Google Gemini, LiteLLM, and OpenRouter with fallback handling and response caching.

### 📁 Robust Dataset Management
- **Hierarchical & Complex Excel Ingestion**: Advanced layout recognition, multi-level header handling, and table boundary detection.
- **Data Cleaning & Standardization**: Automated type casting, missing value handling, deduplication, and schema validation.
- **Fast Session Caching**: Optimized in-memory and local database caching for seamless data slicing without round-trip penalties.

---

## 🛠️ Architecture & Tech Stack

### Frontend
- **Framework**: React 18 (TypeScript)
- **Tooling & Bundler**: Vite
- **Styling**: Tailwind CSS, PostCSS
- **Visuals & Charts**: Recharts, Lucide Icons
- **State & Animation**: Motion, React Hooks

### Backend
- **API Engine**: FastAPI (Python 3.11+)
- **Data Processing**: Pandas, NumPy, OpenPyXL, Scikit-learn
- **AI Orchestration**: Google Gemini SDK, LiteLLM, LangGraph
- **Database & Storage**: SQLAlchemy, SQLite / PostgreSQL (Neon-compatible), Redis cache support
- **Streaming**: WebSockets for real-time calculation progress and updates

---

## 📂 Repository Structure

```
.
├── src/                          # InsightIQ Frontend Application (React + Vite)
│   ├── components/               # UI components, dashboard widgets, charts
│   ├── services/                 # API client, WebSocket managers, state handlers
│   ├── hooks/                    # Custom React state and data hooks
│   └── types/                    # TypeScript interfaces and data models
├── backend/                      # InsightIQ FastAPI Backend
│   ├── src/
│   │   ├── agents/               # AI analytics agents and orchestrators
│   │   ├── services/             # Excel parsing, layout detection, chart generators
│   │   ├── routers/              # API route controllers (files, dashboard, chat, providers)
│   │   └── core/                 # Database connection, security, and runtime configuration
│   ├── config.env.example        # Backend environment variables template
│   ├── requirements.txt          # Python dependencies
│   └── main.py                   # Backend entry point
├── .github/                      # CI/CD workflows
│   └── workflows/
│       └── full-stack-ci.yml     # Automated frontend & backend testing pipeline
├── metadata.json                 # Project descriptor and platform capabilities
├── package.json                  # Frontend dependencies and scripts
└── vite.config.ts                # Vite configuration
```

---

## ⚡ Quick Start

### 1. Prerequisites
- **Node.js**: 18.x or higher
- **Python**: 3.11 or higher
- **Package Managers**: `npm` (frontend) and `pip` (backend)

### 2. Frontend Setup
Install dependencies and launch the development server:

```bash
npm install
npm run dev
```

The application will be accessible at `http://localhost:3000`.

### 3. Backend Setup
From the project root:

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

The FastAPI service runs at `http://localhost:8000` (interactive API docs available at `http://localhost:8000/docs`).

### 4. Configuration
- **Frontend**: Create a `.env` file based on `.env.example`:
  ```env
  GEMINI_API_KEY=your_gemini_key
  DATABASE_URL=sqlite:///./insightiq.db
  DEBUG=true
  LOG_LEVEL=INFO
  VITE_API_URL=http://localhost:3000
  ```
- **Backend**: Copy `backend/config.env.example` to `backend/config.env` and supply relevant credentials (OpenRouter, Gemini, or database connection strings).

---

## 🧪 Testing & Validation

Run frontend tests and production builds:
```bash
# Frontend linting
npm run lint

# Production build
npm run build
```

Run backend test suite:
```bash
cd backend
python -m pytest tests/ -v
```

---

## 📄 License
Proprietary & Confidential. All rights reserved.
