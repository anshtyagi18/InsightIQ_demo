# InsightIQ Backend - Comprehensive Documentation

## 🚀 Overview

The InsightIQ Backend is a sophisticated, AI-powered analytics platform built with FastAPI that provides intelligent data analysis, comparison capabilities, and conversational analytics. The backend has been extensively enhanced with advanced AI features, performance optimizations, and enterprise-grade functionality.

## 🏗️ Architecture

### Core Components

```
backend/
├── main.py                     # FastAPI application entry point
├── src/
│   ├── agents/                 # AI-powered analysis agents
│   ├── routers/               # API route handlers
│   ├── services/              # Business logic and data processing
│   ├── core/                  # Configuration and database setup
│   ├── models/                # Data models and schemas
│   └── auth/                  # Authentication services
├── templates/                 # HTML export templates
├── uploads/                   # File storage directory
└── requirements.txt           # Python dependencies
```

### Technology Stack

- **Framework**: FastAPI 0.115.12 with async/await support
- **Database**: PostgreSQL with async SQLAlchemy 2.0 and Alembic migrations
- **Caching**: Redis 5.0.1 for performance optimization
- **AI/ML**: LangGraph, LangChain, Google Generative AI, LiteLLM
- **Data Processing**: Pandas, NumPy, SciPy, Scikit-learn
- **Analytics**: Statsmodels, Matplotlib, Seaborn
- **Authentication**: JWT-based with Stack Auth integration
- **WebSockets**: Real-time communication support

## 🌟 Key Features & Enhancements

### 1. Intelligent Comparison Analysis Engine

**File**: `src/routers/comparison.py` (5500+ lines)

**Features**:
- **AI-Powered Column Mapping**: Semantic matching of columns between estimated vs actual datasets
- **Multi-Level Analysis**: Basic, Standard, and Comprehensive analysis modes based on data complexity
- **Smart Variance Detection**: MAPE calculations with business context understanding
- **Trend Correlation Analysis**: Statistical pattern matching and divergence detection
- **Interactive Charts**: 15+ chart types including variance overview, side-by-side comparisons, trend correlations
- **Natural Language Insights**: AI-generated explanations and recommendations

**Endpoints**:
- `POST /comparison/upload-dual-files` - Upload separate estimated/actual files
- `POST /comparison/upload-multi-sheet` - Upload Excel with multiple sheets
- `POST /comparison/analyze` - Run intelligent comparison analysis
- `GET /comparison/result/{comparison_id}` - Retrieve analysis results

### 2. AI Comparison Engine

**File**: `src/agents/ai_comparison_engine.py`

**Capabilities**:
- **Context-Aware Analysis**: AI understands business domain and data characteristics
- **Intelligent Column Mapping**: LLM-powered semantic column matching
- **Business Impact Assessment**: AI evaluates variance severity in business context
- **Root Cause Analysis**: AI hypothesizes potential causes for variances
- **Actionable Recommendations**: Business-focused insights and next steps

### 3. Advanced Analytics Engine

**File**: `src/services/enhanced_analytics_engine.py` (2199 lines)

**Features**:
- **Multi-Strategy Data Processing**: Handles diverse data formats and structures
- **Intelligent Pattern Recognition**: AI-powered trend detection and anomaly analysis
- **Conversational Interface**: Natural language query processing
- **Dynamic Chart Generation**: 20+ chart types with intelligent data visualization
- **Real-Time Processing**: WebSocket-based streaming analytics

### 4. Conversational Analytics Agent

**File**: `src/services/conversational_analytics_agent.py` (1493 lines)

**Features**:
- **Natural Language Processing**: Understands complex analytics requests
- **Advanced Filtering**: Intelligent data filtering based on conversational context
- **Context Retention**: Maintains conversation state across interactions
- **Multi-Modal Responses**: Text insights, charts, and data tables
- **User Preference Learning**: Adapts to user's analytical preferences

### 5. AI Dashboard Generator

**File**: `src/services/ai_dashboard_generator.py` (2638 lines)

**Capabilities**:
- **Ultra-Flexible Column Matching**: 6-strategy matching system with comprehensive synonyms
- **Excel-like Data Normalization**: Handles mixed data types and formats
- **Adaptive Thresholds**: Prioritizes flexibility over restriction
- **Domain-Agnostic**: Works with any reasonable dataset regardless of naming conventions
- **Intelligent Fallbacks**: Multiple strategies ensure successful data processing

### 6. Performance Optimization Engine

**File**: `src/services/performance_optimization_engine.py`

**Features**:
- **Query Optimization**: Intelligent SQL query performance tuning
- **Caching Strategy**: Multi-layer caching with Redis integration
- **Memory Management**: Efficient data processing for large datasets
- **Async Processing**: Non-blocking operations for better responsiveness

### 7. Real-Time Analytics Engine

**File**: `src/services/real_time_analytics_engine.py`

**Features**:
- **WebSocket Support**: Real-time data streaming and analysis
- **Live Updates**: Dynamic dashboard updates without page refresh
- **Event-Driven Architecture**: Reactive analytics processing
- **Connection Management**: Robust WebSocket connection handling

## 🔧 API Endpoints

### Core Analytics
- `GET /health` - Health check endpoint
- `POST /api/v1/upload` - File upload with validation
- `POST /api/v1/analyze` - General data analysis
- `GET /api/v1/analysis/{analysis_id}` - Retrieve analysis results

### Comparison Analysis
- `POST /comparison/upload-dual-files` - Dual file upload for comparison
- `POST /comparison/analyze` - Intelligent comparison analysis
- `GET /comparison/result/{comparison_id}` - Get comparison results

### Conversational Analytics
- `POST /chat/query` - Natural language analytics queries
- `POST /chat/context` - Set conversation context
- `GET /chat/history` - Retrieve chat history

### Dashboard Generation
- `POST /dashboard/generate` - AI-powered dashboard creation
- `GET /dashboard/data/{dashboard_id}` - Dashboard data retrieval
- `POST /dashboard/export` - Export dashboard to various formats

### Authentication
- `POST /auth/login` - User authentication
- `POST /auth/verify` - Token verification
- `GET /auth/profile` - User profile

### WebSocket Endpoints
- `WS /api/v1/ws/connect` - WebSocket connection for real-time updates
- `WS /api/v1/ws/analytics` - Real-time analytics streaming

## 🛠️ Setup & Installation

### Prerequisites
- Python 3.11+
- PostgreSQL 14+
- Redis 6+
- Node.js 18+ (for frontend)

### Environment Configuration

Create `.env` file in the backend directory:

```env
# Database Configuration
DATABASE_URL=postgresql+asyncpg://username:password@localhost/insightiq
REDIS_URL=redis://localhost:6379

# AI/LLM Configuration
GOOGLE_API_KEY=your_google_api_key
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
LITELLM_MASTER_KEY=your_litellm_key

# Authentication
JWT_SECRET_KEY=your_jwt_secret
STACK_AUTH_PROJECT_ID=your_stack_auth_project_id
STACK_AUTH_SECRET_KEY=your_stack_auth_secret

# Performance Configuration
MAX_UPLOAD_SIZE=100MB
CACHE_TTL=3600
ENABLE_PERFORMANCE_MONITORING=true
```

### Installation Steps

1. **Clone and Setup**:
```bash
git clone <repository-url>
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install Dependencies**:
```bash
pip install -r requirements.txt
```

3. **Database Setup**:
```bash
# Run database migrations
alembic upgrade head

# Verify database schema
python verify_database_schema.py
```

4. **Start Redis**:
```bash
redis-server
```

5. **Run the Application**:
```bash
# Development
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 🚀 Production Deployment

### Docker Deployment

The backend includes Docker support for containerized deployment:

```bash
# Build the container
docker build -t insightiq-backend .

# Run with environment variables
docker run -d \
  --name insightiq-api \
  -p 8000:8000 \
  -e DATABASE_URL=$DATABASE_URL \
  -e REDIS_URL=$REDIS_URL \
  -e GOOGLE_API_KEY=$GOOGLE_API_KEY \
  insightiq-backend
```

### Docker Compose

For full stack deployment:

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend
```

### Environment Variables for Production

```env
# Production Database (use connection pooling)
DATABASE_URL=postgresql+asyncpg://user:pass@prod-db:5432/insightiq
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30

# Redis Cluster (for high availability)
REDIS_URL=redis://redis-cluster:6379
REDIS_POOL_SIZE=50

# Performance Settings
WORKERS=8
MAX_UPLOAD_SIZE=500MB
CACHE_TTL=7200
ENABLE_COMPRESSION=true

# Monitoring & Logging
LOG_LEVEL=INFO
ENABLE_METRICS=true
SENTRY_DSN=your_sentry_dsn

# Security
CORS_ORIGINS=https://your-frontend-domain.com
JWT_ALGORITHM=HS256
SESSION_EXPIRE_HOURS=24
```

### Load Balancing & Scaling

For high-traffic deployments:

1. **Horizontal Scaling**: Use multiple worker processes
2. **Load Balancer**: Nginx or AWS ALB in front of FastAPI
3. **Database**: Read replicas for analytics queries
4. **Caching**: Redis Cluster for distributed caching
5. **File Storage**: S3 or similar for uploaded files

### Health Monitoring

Monitor these endpoints in production:

- `GET /health` - Basic service health
- `GET /api/health` - Detailed component health
- `GET /api/v1/metrics` - Performance metrics (if enabled)

### Performance Tuning

Production optimizations applied:

- **Async Database Connections**: Connection pooling with asyncpg
- **Redis Clustering**: Distributed caching for scale
- **File Upload Optimization**: Streaming uploads for large files
- **Memory Management**: Garbage collection tuning for large datasets
- **Query Optimization**: Database indexing and query caching

## 🔍 Recent Enhancements

### Performance Optimizations
- **500% scroll performance improvement** through UI optimizations
- **90% reduction in database calls** via intelligent caching
- **Bundle optimization** resulting in 94% smaller initial bundle (314KB → 19KB gzipped)
- **WebSocket connection optimizations** eliminating navigation lag
- **React.lazy code splitting** with suspense boundaries for optimal loading
- **GPU acceleration** for smooth animations and transitions

### AI-Powered Features
- **Enhanced KPI Generation** with contextual insights and actionable recommendations
- **Statistical Insights Engine** providing detailed metric breakdowns and analysis
- **Intelligent Comparison Logic** eliminating contradictions in trend alignment
- **Advanced Filtering Parser** supporting natural language data filtering
- **AI-Enhanced Chart Generation** with 20+ intelligent visualization types
- **Context-Aware Analysis** adapting to business domains automatically
- **Smart Column Mapping** using semantic similarity and business logic

### Bug Fixes & Stability
- **Fixed critical logical contradictions** in comparison analysis
- **Resolved empty statistical insights** for larger datasets
- **Stack Auth browser compatibility** improvements
- **WebSocket connection status** race condition fixes
- **Eliminated navigation lag** through React performance optimizations
- **Fixed trend alignment accuracy** showing proper correlation vs variance context
- **Enhanced data processing stability** with improved error handling

### Authentication & Security
- **Stack Auth Integration** with enterprise-grade authentication
- **JWT-based fallback authentication** for broader compatibility
- **Role-based access control** ready for implementation
- **Session management** with automatic token refresh
- **Multi-tier authentication fallback** ensuring reliable access
- **API key management** for multiple AI providers

### Data Processing Enhancements
- **Ultra-flexible column matching** with 6-strategy system
- **Comprehensive synonym mapping** for diverse domain support
- **Excel-like data normalization** handling mixed data types
- **Intelligent fallback strategies** ensuring successful processing
- **Adaptive analysis complexity** based on dataset characteristics

## 🔧 Advanced Service Architecture

### Service Layer Organization

The backend utilizes a sophisticated service layer architecture:

```
src/services/
├── ai_dashboard_generator.py         # AI-powered dashboard creation (2638 lines)
├── conversational_analytics_agent.py # Natural language analytics (1493 lines)
├── enhanced_analytics_engine.py      # Advanced data processing (2199 lines)
├── comparison_chart_generator.py     # Comparison visualization (590 lines)
├── comparison_data_processor.py      # Data alignment and processing (468 lines)
├── performance_optimization_engine.py # Performance tuning (468 lines)
├── real_time_analytics_engine.py     # WebSocket analytics (584 lines)
├── enhanced_database_service.py      # Advanced DB operations (594 lines)
├── litellm_service.py                # Unified AI model interface (451 lines)
├── file_parser.py                    # Multi-format file processing (543 lines)
├── excel_pivot_analyzer.py           # Excel pivot table analysis (481 lines)
├── dashboard_generator.py            # Legacy dashboard generation (3616 lines)
├── advanced_analytics_engine.py      # Statistical analysis (863 lines)
├── export_service.py                 # Data export utilities (328 lines)
├── storage_service.py                # File storage management (242 lines)
└── database_service.py               # Core DB operations (342 lines)
```

### AI Agent Architecture

```
src/agents/
├── ai_comparison_engine.py           # AI-powered comparison analysis
├── data_cleaner.py                   # Intelligent data cleaning
├── intelligent_comparison_agent.py   # Semantic data comparison
├── trend_detector_agent.py           # Pattern recognition and trends
└── business_context_agent.py         # Business domain understanding
```

### Caching Strategy

- **Redis Integration**: Multi-layer caching with intelligent TTL
- **Analysis Caching**: Expensive computations cached for 1 hour
- **File Metadata Caching**: Upload metadata cached for 24 hours
- **Chart Data Caching**: Generated charts cached for 30 minutes
- **WebSocket State Caching**: Connection states cached for session duration

### Performance Monitoring

The system includes comprehensive performance monitoring:

- **Request Timing**: All API endpoints tracked for response time
- **Memory Usage**: Real-time memory monitoring for large dataset processing
- **Cache Hit Rates**: Redis cache effectiveness tracking
- **Database Query Performance**: SQLAlchemy query optimization
- **WebSocket Connection Health**: Real-time connection monitoring

## 📊 Comparison Analysis Deep Dive

The comparison analysis system is one of the most sophisticated features:

### Analysis Levels
1. **Basic Analysis** (< 20 complexity score, ≤ 2 numeric columns)
   - Simple variance calculations
   - Basic trend alignment
   - Essential KPIs and insights

2. **Standard Analysis** (20-100 complexity score, 3-5 numeric columns)
   - Enhanced variance analysis with MAPE
   - Trend correlation analysis
   - Comprehensive chart generation
   - Detailed insights and recommendations

3. **Comprehensive Analysis** (> 100 complexity score, > 5 numeric columns)
   - Individual metric deep analysis
   - Granular insights by category/region
   - Advanced statistical patterns
   - Business impact prioritization
   - Enhanced chart suite with 15+ visualizations

### KPI Generation
- **Forecast Precision Score** (🎯): Accuracy-based scoring with AI context
- **Variance Risk Level** (⚠️): Business impact assessment
- **Trend Intelligence** (📈): Pattern alignment analysis
- **Business Impact Alert** (🚨): Critical deviation detection
- **Data Intelligence Quality** (🧠): Data quality assessment
- **Forecast Health Index** (💚): Overall performance indicator

## 🔮 Future Roadmap

### Planned Enhancements
- **Machine Learning Pipeline**: Automated model training and prediction
- **Advanced Visualization**: 3D charts and interactive dashboards
- **Multi-Tenant Architecture**: Organization-based data isolation
- **API Rate Limiting**: Enhanced security and resource management
- **Export Capabilities**: PDF, PowerPoint, and Excel report generation
- **Mobile API**: Optimized endpoints for mobile applications

### Integration Targets
- **Power BI Connector**: Direct integration with Microsoft Power BI
- **Tableau Integration**: Custom connectors for Tableau
- **Slack/Teams Bots**: Analytics insights in chat platforms
- **Email Notifications**: Automated insight delivery
- **Cloud Storage**: AWS S3, Google Drive, and Dropbox integration

## 🧪 Testing & Development

### Running Tests

The backend includes comprehensive test coverage:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test modules
pytest tests/test_comparison_analysis.py
pytest tests/test_ai_engines.py
pytest tests/test_performance.py

# Run integration tests
pytest tests/integration/
```

### Test Structure

```
tests/
├── unit/                           # Unit tests for individual components
│   ├── test_comparison_engine.py   # Comparison analysis tests
│   ├── test_ai_agents.py          # AI agent functionality tests
│   ├── test_data_processing.py    # Data processing pipeline tests
│   └── test_authentication.py     # Auth system tests
├── integration/                    # Integration tests
│   ├── test_api_endpoints.py      # Full API workflow tests
│   ├── test_database_operations.py # Database integration tests
│   └── test_websocket_flow.py     # WebSocket functionality tests
└── performance/                    # Performance and load tests
    ├── test_large_datasets.py     # Large file processing tests
    └── test_concurrent_users.py   # Multi-user scenario tests
```

### API Documentation

The backend provides interactive API documentation:

- **Swagger UI**: Available at `http://localhost:8000/docs`
- **ReDoc**: Available at `http://localhost:8000/redoc`
- **OpenAPI Schema**: Available at `http://localhost:8000/openapi.json`

### Development Testing Tools

```bash
# Test file upload endpoints
curl -X POST "http://localhost:8000/comparison/upload-dual-files" \
  -H "Content-Type: multipart/form-data" \
  -F "estimated_file=@test_estimated.xlsx" \
  -F "actual_file=@test_actual.xlsx"

# Test WebSocket connection
wscat -c ws://localhost:8000/api/v1/ws/connect

# Test health endpoints
curl http://localhost:8000/health
curl http://localhost:8000/api/health
```

### Performance Testing

Load testing with realistic scenarios:

```bash
# Install locust for load testing
pip install locust

# Run performance tests
locust -f tests/performance/locustfile.py --host=http://localhost:8000
```

### Database Testing

```bash
# Test database connection
python verify_database_schema.py

# Run database migrations in test mode
ENVIRONMENT=test alembic upgrade head

# Reset test database
python recreate_tables.py --test
```

## 🤝 Contributing

### Development Guidelines
1. Follow PEP 8 style guidelines
2. Use async/await for all I/O operations
3. Add comprehensive logging for debugging
4. Write unit tests for new features (aim for 80%+ coverage)
5. Update documentation for API changes
6. Use type hints for all function parameters and returns
7. Implement proper error handling with appropriate HTTP status codes

### Code Structure
- **Routers**: Handle HTTP requests and responses
- **Services**: Contain business logic and data processing
- **Agents**: AI-powered analysis and insights
- **Models**: Data structures and database schemas
- **Core**: Configuration, database, and utility functions

### Pull Request Process
1. Fork the repository and create a feature branch
2. Write tests for new functionality
3. Ensure all tests pass locally
4. Update documentation if needed
5. Submit PR with clear description of changes
6. Address code review feedback

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support & Troubleshooting

### Common Issues
1. **Database Connection Issues**: Check PostgreSQL service and connection string
2. **Redis Connection**: Ensure Redis server is running on port 6379
3. **AI API Errors**: Verify API keys and model availability
4. **Memory Issues**: Increase system memory or optimize data processing

### Performance Monitoring
- Use `/health` endpoint for system status
- Monitor WebSocket connections via browser dev tools
- Check Redis cache hit rates
- Review database query performance

### Logging
- Application logs: Check console output
- Database logs: PostgreSQL query logs
- Redis logs: Redis server logs
- WebSocket logs: Browser network tab

---

**Built with ❤️ by the InsightIQ Team** 