# System Patterns: AI-Driven Dynamic Analytics Dashboard
*Version: 1.0*
*Created: 2025-01-28*
*Last Updated: 2025-01-28*

## Architecture Overview

The AI-Driven Dynamic Analytics Dashboard follows a **Multi-Agent Backend Architecture** with a **Real-time Frontend**, designed for autonomous data analysis and visualization generation.

### High-Level Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                   Frontend (React + TypeScript)             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   Upload UI     │  │   Dashboard     │  │   Chat/Query    │ │
│  │                 │  │   Display       │  │   Interface     │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                           ↕ WebSocket + HTTP
┌─────────────────────────────────────────────────────────────┐
│                   Backend (FastAPI + LangGraph)             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │  API Gateway    │  │  Agent Manager  │  │  Data Processor │ │
│  │  (FastAPI)      │  │  (LangGraph)    │  │  (pandas)       │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │ Dashboard Agent │  │ Analytics Agent │  │ Workflow Agent  │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                           ↕ API Calls
┌─────────────────────────────────────────────────────────────┐
│                   External Services                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │  OpenRouter     │  │  File Storage   │  │  Config Store   │ │
│  │  (DeepSeek)     │  │  (Local/Cloud)  │  │  (.env)         │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Key Components

### Frontend Components
- **Upload Interface**: File drop zone, validation, progress tracking
- **Dashboard Display**: Dynamic chart rendering, KPI cards, data tables
- **Query Interface**: Natural language input, chat-like responses
- **Real-time Updates**: WebSocket connection manager, state synchronization
- **Error Boundary**: Graceful error handling, fallback UI components

### Backend Components
- **API Gateway (FastAPI)**: Route management, request validation, response formatting
- **Agent Manager (LangGraph)**: Agent coordination, workflow orchestration, state management
- **Data Processor**: File parsing, data validation, transformation pipeline
- **WebSocket Handler**: Real-time communication, event broadcasting
- **Security Layer**: Authentication, rate limiting, input sanitization

### Agent Architecture
- **Dashboard Agent**: Generates KPIs, summaries, and basic visualizations
- **Analytics Agent**: Performs trend analysis, correlation detection, anomaly identification
- **Workflow Agent**: Coordinates multi-step analysis, manages agent communication

## Design Patterns in Use

### 1. Multi-Agent Pattern (Primary)
```python
# Agent coordination through LangGraph
class AgentWorkflow:
    def __init__(self):
        self.dashboard_agent = DashboardAgent()
        self.analytics_agent = AnalyticsAgent()
        self.workflow_agent = WorkflowAgent()
    
    async def process_data(self, data):
        # Workflow coordination
        summary = await self.dashboard_agent.generate_summary(data)
        trends = await self.analytics_agent.analyze_trends(data)
        return await self.workflow_agent.combine_results(summary, trends)
```

### 2. Command Pattern (Agent Actions)
```python
# Each agent action as a command
class AnalyzeDataCommand:
    def __init__(self, agent, data, analysis_type):
        self.agent = agent
        self.data = data
        self.analysis_type = analysis_type
    
    async def execute(self):
        return await self.agent.analyze(self.data, self.analysis_type)
```

### 3. Observer Pattern (Real-time Updates)
```python
# WebSocket event broadcasting
class DashboardEventBus:
    def __init__(self):
        self.subscribers = []
    
    def subscribe(self, websocket):
        self.subscribers.append(websocket)
    
    async def notify_update(self, event_data):
        for subscriber in self.subscribers:
            await subscriber.send_json(event_data)
```

### 4. Strategy Pattern (AI Model Selection)
```python
# Model provider strategy
class AIModelStrategy:
    def __init__(self, provider="openrouter"):
        self.provider = provider
    
    async def generate_response(self, prompt):
        if self.provider == "openrouter":
            return await self.openrouter_call(prompt)
        # Future: Add other providers
```

### 5. Factory Pattern (Agent Creation)
```python
# Agent factory for dynamic agent creation
class AgentFactory:
    @staticmethod
    def create_agent(agent_type: str):
        if agent_type == "dashboard":
            return DashboardAgent()
        elif agent_type == "analytics":
            return AnalyticsAgent()
        elif agent_type == "workflow":
            return WorkflowAgent()
```

## Data Flow Architecture

### 1. Upload & Processing Flow
```
User Upload → File Validation → Data Parsing → Agent Trigger → AI Analysis → Dashboard Generation
     ↓              ↓              ↓             ↓            ↓              ↓
   React UI →   FastAPI →    pandas →   LangGraph →  OpenRouter →   WebSocket
```

### 2. Real-time Query Flow
```
User Query → Query Processing → Agent Selection → AI Inference → Response Streaming
     ↓             ↓               ↓              ↓               ↓
   React →    FastAPI →      Agent Manager →  DeepSeek →    WebSocket
```

### 3. Dashboard Update Flow
```
Data Change → Event Trigger → Agent Analysis → Chart Generation → UI Update
     ↓             ↓              ↓               ↓               ↓
  Backend →   Event Bus →    Analytics Agent →  Chart Data →   React
```

## Key Technical Decisions

### 1. Agent-First Architecture
- **Decision**: Use LangGraph for agent orchestration instead of traditional MVC
- **Rationale**: Enables autonomous data analysis, better scalability for AI workflows
- **Trade-off**: Slightly more complex initial setup, but much more flexible for AI features

### 2. WebSocket for Real-time Updates
- **Decision**: Use WebSocket instead of polling for dashboard updates
- **Rationale**: Meets <1.5s latency requirement, more efficient resource usage
- **Implementation**: FastAPI WebSocket with React WebSocket client

### 3. Stateless Agent Design
- **Decision**: Agents maintain minimal internal state, use LangGraph for persistence
- **Rationale**: Better scalability, easier debugging, fault tolerance
- **State Storage**: LangGraph handles state persistence, agents are pure functions

### 4. Modular Frontend Architecture
- **Decision**: Component-based React with clear separation of concerns
- **Rationale**: Maintainable, testable, reusable components
- **Pattern**: Container/Presenter pattern for complex components

### 5. API-First Design
- **Decision**: Design backend APIs before implementing business logic
- **Rationale**: Clear contracts, easier testing, frontend/backend independence
- **Documentation**: FastAPI automatic OpenAPI documentation

## Component Relationships

### Frontend Component Hierarchy
```
App
├── Layout
│   ├── Header (nav, user info)
│   ├── Sidebar (navigation, filters)
│   └── Main (content area)
├── Pages
│   ├── Upload (file handling)
│   ├── Dashboard (chart display)
│   └── Query (chat interface)
├── Shared Components
│   ├── Charts (visualization)
│   ├── Loading (states)
│   └── Error (boundaries)
└── Hooks
    ├── useWebSocket (real-time)
    ├── useFileUpload (handling)
    └── useAgentQuery (AI calls)
```

### Backend Service Architecture
```
FastAPI App
├── Routes
│   ├── /upload (file handling)
│   ├── /dashboard (data display)
│   ├── /query (AI interaction)
│   └── /ws (WebSocket)
├── Services
│   ├── AgentService (coordination)
│   ├── DataService (processing)
│   └── AuthService (security)
├── Agents
│   ├── DashboardAgent
│   ├── AnalyticsAgent
│   └── WorkflowAgent
└── Utils
    ├── FileProcessor
    ├── AIModelClient
    └── WebSocketManager
```

## Scalability Considerations

### Horizontal Scaling Readiness
- **Stateless Design**: Agents can run on multiple instances
- **Event-Driven**: WebSocket events can be distributed via message queue
- **Database Ready**: LangGraph state can use PostgreSQL for multi-instance support

### Performance Optimizations
- **Caching Strategy**: Redis for frequent AI responses, file processing results
- **Async Processing**: All I/O operations use async/await patterns
- **Connection Pooling**: Reuse connections to AI providers, databases

### Resource Management
- **Memory Efficiency**: Stream large file processing, garbage collection
- **CPU Optimization**: Pandas vectorization, concurrent agent execution
- **I/O Optimization**: Async file operations, WebSocket connection management

## Security Architecture

### Authentication & Authorization
```python
# Bearer token authentication (optional for MVP)
class SecurityService:
    def verify_token(self, token: str) -> User:
        # JWT validation logic
        pass
    
    def check_permissions(self, user: User, resource: str) -> bool:
        # Role-based access control
        pass
```

### Input Validation & Sanitization
```python
# Pydantic models for validation
class UploadRequest(BaseModel):
    file_type: str = Field(regex="^(csv|xlsx)$")
    file_size: int = Field(le=10_000_000)  # 10MB limit
    
class QueryRequest(BaseModel):
    query: str = Field(max_length=1000)
    sanitized_query: str = Field(exclude=True)
```

### Rate Limiting & Abuse Prevention
```python
# Rate limiting per user/IP
class RateLimiter:
    def __init__(self, requests_per_minute: int = 60):
        self.limit = requests_per_minute
        self.requests = {}
    
    def allow_request(self, client_id: str) -> bool:
        # Sliding window rate limiting
        pass
```

## Error Handling Strategy

### Frontend Error Boundaries
```typescript
// React error boundary for graceful degradation
class DashboardErrorBoundary extends Component {
    componentDidCatch(error: Error, errorInfo: ErrorInfo) {
        // Log error, show fallback UI
        this.setState({ hasError: true, error });
    }
}
```

### Backend Error Handling
```python
# Structured error responses
class APIError(Exception):
    def __init__(self, message: str, code: int, details: dict = None):
        self.message = message
        self.code = code
        self.details = details or {}

# Global exception handler
@app.exception_handler(APIError)
async def api_error_handler(request, exc: APIError):
    return JSONResponse(
        status_code=exc.code,
        content={"error": exc.message, "details": exc.details}
    )
```

## Integration Patterns

### AI Model Integration
- **Adapter Pattern**: Uniform interface for different AI providers
- **Circuit Breaker**: Fallback when AI service is unavailable
- **Retry Logic**: Exponential backoff for transient failures

### File Processing Integration
- **Pipeline Pattern**: Sequential data transformation steps
- **Validation Chain**: Multiple validation layers for uploaded files
- **Stream Processing**: Handle large files without memory issues

### WebSocket Integration
- **Event Sourcing**: Store events for replay and debugging
- **Message Queuing**: Buffer messages during high load
- **Connection Management**: Handle disconnections gracefully

---

*This document captures the system architecture and design patterns used in the project.* 