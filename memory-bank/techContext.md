# Technical Context: AI-Driven Dynamic Analytics Dashboard
*Version: 1.0*
*Created: 2025-01-28*
*Last Updated: 2025-01-28*

## Technology Stack

### Frontend Stack
- **Framework**: React 18+ with TypeScript
- **Build Tool**: Vite (recommended for fast development)
- **Styling**: CSS Modules or Tailwind CSS
- **State Management**: React Context + useReducer (lightweight approach)
- **Data Visualization**: Recharts (React-optimized) or Plotly.js
- **Real-time Updates**: WebSocket client (native WebSocket API)
- **HTTP Client**: Axios or Fetch API
- **File Upload**: React Dropzone for CSV/Excel handling

### Backend Stack
- **Framework**: FastAPI (Python 3.9+)
- **Agent Framework**: LangGraph with optional Google ADK integration
- **AI Model Provider**: OpenRouter API (DeepSeek R1 model)
- **WebSocket**: FastAPI WebSocket support for real-time updates
- **File Processing**: pandas (CSV), openpyxl (Excel), python-multipart (uploads)
- **API Documentation**: FastAPI automatic OpenAPI/Swagger docs
- **Environment Management**: python-dotenv for configuration
- **Async Runtime**: uvicorn for ASGI server

### Agent Architecture
- **Core Framework**: LangGraph for agent workflow orchestration
- **Agent Types**:
  - **Dashboard Agent**: KPI generation and data summarization
  - **Analytics Agent**: Trend analysis and pattern detection
  - **Workflow Agent**: Task coordination and state management
- **Prompt Management**: Jinja2 templates for dynamic prompt generation
- **State Management**: LangGraph state persistence with SQLite/PostgreSQL
- **Model Integration**: OpenRouter SDK for DeepSeek API calls

### Data Processing & Storage
- **File Processing**: pandas for CSV, openpyxl for Excel
- **Data Validation**: pydantic for schema validation
- **Temporary Storage**: Local file system for uploaded files
- **Session Storage**: Redis (optional) or in-memory for development
- **Configuration**: .env files with environment variable management

### Development & Deployment
- **Package Management**: npm (frontend), pip/pipenv (backend)
- **API Testing**: FastAPI TestClient, pytest for backend testing
- **Frontend Testing**: React Testing Library, Jest
- **Code Quality**: ESLint + Prettier (frontend), Black + Flake8 (backend)
- **Development Server**: Vite dev server + uvicorn with hot reload

## Technology Decision Rationales

### Frontend Technology Choices

**React + TypeScript**
- ✅ **Pros**: Existing codebase, strong typing, excellent ecosystem
- ✅ **Decision**: Leverage existing React investment, TypeScript ensures reliability
- ✅ **Performance**: Virtual DOM optimizations, component reusability

**Recharts for Visualization**
- ✅ **Pros**: React-native, good performance, customizable
- ✅ **Alternative**: Plotly.js (more features but heavier)
- ✅ **Decision**: Start with Recharts, migrate to Plotly.js if complex viz needed

**WebSocket for Real-time Updates**
- ✅ **Pros**: Native browser support, low latency, efficient
- ✅ **Decision**: Essential for <1.5s dashboard update requirement

### Backend Technology Choices

**FastAPI over Flask/Django**
- ✅ **Pros**: Native async support, automatic API docs, pydantic integration
- ✅ **Performance**: ASGI-based, handles concurrent requests efficiently
- ✅ **Decision**: Best fit for real-time AI agent communication

**LangGraph + Google ADK Hybrid**
- ✅ **Pros**: Flexible agent workflows, state management, Google ADK compatibility
- ✅ **Decision**: LangGraph primary, ADK integration for specific components
- ✅ **Fallback**: Pure LangGraph if ADK integration proves complex

**OpenRouter + DeepSeek**
- ✅ **Pros**: Cost-effective, good performance, API compatibility
- ✅ **Cost**: Free tier friendly, predictable pricing
- ✅ **Performance**: <700ms response time requirement achievable

### Architecture Decisions

**Agent-Based Backend**
- ✅ **Scalability**: Each agent handles specific responsibilities
- ✅ **Maintainability**: Clear separation of concerns
- ✅ **Extensibility**: Easy to add new agents for future features

**Microservice-Ready Design**
- ✅ **Structure**: Modular agent system allows future service separation
- ✅ **Decision**: Monolith for MVP, microservice transition path preserved

## Dependencies & Versions

### Frontend Dependencies
```json
{
  "react": "^18.2.0",
  "react-dom": "^18.2.0",
  "typescript": "^4.9.5",
  "recharts": "^2.8.0",
  "axios": "^1.6.0",
  "react-dropzone": "^14.2.3"
}
```

### Backend Dependencies
```python
# requirements.txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
langgraph==0.0.62
langchain==0.1.0
openai==1.3.0  # For OpenRouter compatibility
pandas==2.1.3
openpyxl==3.1.2
python-multipart==0.0.6
python-dotenv==1.0.0
pydantic==2.5.0
websockets==12.0
aiofiles==23.2.1
```

## Technical Constraints & Solutions

### Performance Requirements
- **Backend Response**: <1 second
  - **Solution**: FastAPI async endpoints, efficient pandas operations
- **Real-time Updates**: <1.5 seconds
  - **Solution**: WebSocket connection, optimized agent workflows
- **AI Inference**: <700ms average
  - **Solution**: OpenRouter DeepSeek optimization, request batching

### Resource Constraints
- **Local Development**: Limited compute resources
  - **Solution**: Lightweight agent architecture, efficient caching
- **Free Tier AI**: DeepSeek cost optimization
  - **Solution**: Prompt optimization, response caching, rate limiting

### Security Implementation
- **API Key Management**: Environment variable isolation
- **File Upload Security**: Size limits, type validation, sandboxing
- **Rate Limiting**: Request throttling, user session management
- **Authentication**: Bearer token system (optional for MVP)

## Development Environment Setup

### Prerequisites
- Python 3.9+ with pip
- Node.js 18+ with npm
- Git for version control
- VS Code with Python + TypeScript extensions

### Backend Setup Commands
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Environment configuration
cp .env.example .env
# Edit .env with OpenRouter API key

# Run development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup Commands
```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

## Build and Deployment

### Development Build Process
- **Frontend**: Vite build system with TypeScript compilation
- **Backend**: Python with FastAPI auto-reload during development
- **Integration**: Proxy configuration for API requests during development

### Production Deployment Strategy
- **Frontend**: Static build served via CDN or nginx
- **Backend**: Docker container with uvicorn + gunicorn
- **Database**: SQLite for development, PostgreSQL for production
- **Monitoring**: FastAPI built-in metrics, application logging

## Testing Approach

### Backend Testing
- **Unit Tests**: pytest for agent logic, data processing
- **Integration Tests**: FastAPI TestClient for API endpoints
- **AI Testing**: Mock OpenRouter responses, prompt validation
- **Performance Tests**: Load testing for concurrent agent requests

### Frontend Testing
- **Unit Tests**: Jest + React Testing Library
- **Integration Tests**: Component interaction testing
- **E2E Tests**: Playwright for upload-to-dashboard workflow
- **Visual Testing**: Screenshot comparison for chart rendering

### Testing Data
- **Sample Datasets**: Curated CSV/Excel files for various scenarios
- **Performance Benchmarks**: Response time validation
- **AI Model Testing**: Known good prompt/response pairs

## Risk Mitigation

### Technical Risks
- **AI Model Latency**: Implement request timeout, fallback responses
- **File Processing**: Size limits, format validation, error handling
- **WebSocket Reliability**: Connection recovery, state synchronization
- **Agent Coordination**: Error boundaries, graceful degradation

### Development Risks
- **LangGraph Complexity**: Start simple, iterate to complex workflows
- **React Integration**: Incremental migration from existing codebase
- **API Integration**: Mock services for development isolation

---

*This document describes the technologies used in the project and how they're configured.* 