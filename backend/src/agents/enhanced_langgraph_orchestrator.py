"""
Enhanced LangGraph Orchestrator with OpenRouter Integration

Advanced workflow orchestration using LangGraph for managing complex analytics pipelines
with OpenRouter/LiteLLM integration for intelligent data filtering and superior dashboard generation.
This replaces basic orchestration with a hybrid ADK-LangGraph approach.
"""

from typing import Dict, List, Any, Optional, TypedDict, Annotated, Union
from langgraph.graph import StateGraph, START, END
from langchain_core.runnables import RunnableConfig
import logging
import json
import os
import time
import uuid
from datetime import datetime
import asyncio
from dataclasses import dataclass, asdict, field
from enum import Enum
import hashlib
import traceback

# LiteLLM imports for OpenRouter integration
try:
    from litellm import completion, acompletion
    LITELLM_AVAILABLE = True
except ImportError:
    LITELLM_AVAILABLE = False
    logging.warning("LiteLLM not available. Install with: pip install litellm")

# Redis for state persistence (optional dependency)
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logging.warning("Redis not available. State persistence will use local storage.")

# Import only what we need to avoid dependency issues
# from .data_cleaner import DataCleanerAgent
# from .trend_detector import TrendDetectorAgent
# from ..core.adk_config import adk_config

logger = logging.getLogger(__name__)

class WorkflowStatus(Enum):
    """Workflow execution status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"

class StateTransition(Enum):
    """Valid state transitions for workflow steps."""
    INITIALIZE = "initialize"
    ANALYZE_REQUIREMENTS = "analyze_requirements"
    INTELLIGENT_FILTERING = "intelligent_data_filtering"
    DATA_CLEANING = "data_cleaning"
    QUALITY_ASSESSMENT = "quality_assessment"
    ENHANCED_DASHBOARD = "enhanced_dashboard_generation"
    FINALIZE_RESULTS = "finalize_results"
    ERROR_HANDLING = "error_handling"

class WorkflowErrorType(Enum):
    """Categorized error types for workflow processing."""
    DATA_ERROR = "data_error"              # Issues with input data format/content
    API_ERROR = "api_error"                # OpenRouter/LiteLLM API failures
    PROCESSING_ERROR = "processing_error"  # Internal processing failures
    STATE_ERROR = "state_error"            # State management issues
    VALIDATION_ERROR = "validation_error"  # Data validation failures
    TIMEOUT_ERROR = "timeout_error"        # Operation timeout
    RESOURCE_ERROR = "resource_error"      # Memory/storage issues
    CONFIGURATION_ERROR = "config_error"   # Configuration or setup issues

class ErrorSeverity(Enum):
    """Error severity levels for prioritized handling."""
    LOW = "low"           # Non-critical, workflow can continue
    MEDIUM = "medium"     # Warning level, may affect quality
    HIGH = "high"         # Critical error, requires attention
    FATAL = "fatal"       # Workflow cannot continue

@dataclass
class WorkflowError:
    """Enhanced error information with categorization and recovery options."""
    error_id: str
    error_type: WorkflowErrorType
    severity: ErrorSeverity
    step: str
    message: str
    details: Dict[str, Any]
    timestamp: str
    stack_trace: Optional[str] = None
    recovery_options: List[str] = None
    auto_recoverable: bool = False
    retry_count: int = 0
    
    @classmethod
    def create(cls, error_type: WorkflowErrorType, severity: ErrorSeverity, step: str, message: str, 
               details: Optional[Dict[str, Any]] = None, exception: Optional[Exception] = None):
        """Create a new workflow error with generated ID."""
        import traceback
        
        error_id = f"{step}_{error_type.value}_{int(time.time())}"
        stack_trace = traceback.format_exc() if exception else None
        
        return cls(
            error_id=error_id,
            error_type=error_type,
            severity=severity,
            step=step,
            message=message,
            details=details or {},
            timestamp=datetime.now().isoformat(),
            stack_trace=stack_trace,
            recovery_options=[],
            auto_recoverable=False,
            retry_count=0
        )

@dataclass
class WorkflowCheckpoint:
    """Workflow state checkpoint for persistence and recovery."""
    checkpoint_id: str
    workflow_id: str
    step_name: str
    timestamp: str
    state_data: Dict[str, Any]
    checkpoint_hash: str
    metadata: Dict[str, Any]
    
    @classmethod
    def create(cls, workflow_id: str, step_name: str, state_data: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None):
        """Create a new checkpoint with generated ID and hash."""
        checkpoint_id = f"{workflow_id}_{step_name}_{int(time.time())}"
        timestamp = datetime.now().isoformat()
        
        # Create deterministic hash of state data
        state_json = json.dumps(state_data, sort_keys=True, default=str)
        checkpoint_hash = hashlib.sha256(state_json.encode()).hexdigest()[:16]
        
        return cls(
            checkpoint_id=checkpoint_id,
            workflow_id=workflow_id,
            step_name=step_name,
            timestamp=timestamp,
            state_data=state_data,
            checkpoint_hash=checkpoint_hash,
            metadata=metadata or {}
        )

class WorkflowStateManager:
    """
    Enhanced state manager with persistence, versioning, and checkpoint capabilities.
    Supports both Redis and local file-based storage.
    """
    
    def __init__(self, storage_type: str = "auto", redis_url: str = None):
        """
        Initialize the state manager with specified storage backend.
        
        Args:
            storage_type: "redis", "local", or "auto" (auto-detect)
            redis_url: Redis connection URL (defaults to localhost)
        """
        self.storage_type = storage_type
        self.redis_client = None
        self.local_storage_path = "./.langgraph_state"
        
        # Initialize storage backend
        if storage_type == "redis" or (storage_type == "auto" and REDIS_AVAILABLE):
            try:
                redis_url = redis_url or "redis://localhost:6379/0"
                self.redis_client = redis.from_url(redis_url)
                self.redis_client.ping()  # Test connection
                self.storage_type = "redis"
                logger.info("State manager initialized with Redis backend")
            except Exception as e:
                logger.warning(f"Redis initialization failed: {e}. Falling back to local storage.")
                self.storage_type = "local"
        else:
            self.storage_type = "local"
        
        # Initialize local storage if needed
        if self.storage_type == "local":
            os.makedirs(self.local_storage_path, exist_ok=True)
            logger.info("State manager initialized with local file backend")
    
    async def save_checkpoint(self, checkpoint: WorkflowCheckpoint) -> bool:
        """
        Save a workflow checkpoint to persistent storage.
        
        Args:
            checkpoint: The checkpoint to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            checkpoint_data = asdict(checkpoint)
            
            if self.storage_type == "redis":
                # Save to Redis with expiration
                key = f"workflow:{checkpoint.workflow_id}:checkpoint:{checkpoint.checkpoint_id}"
                self.redis_client.setex(
                    key, 
                    86400 * 7,  # 7 days expiration
                    json.dumps(checkpoint_data)
                )
                
                # Update workflow metadata
                workflow_key = f"workflow:{checkpoint.workflow_id}:meta"
                self.redis_client.hset(workflow_key, "last_checkpoint", checkpoint.checkpoint_id)
                self.redis_client.hset(workflow_key, "last_step", checkpoint.step_name)
                self.redis_client.hset(workflow_key, "last_updated", checkpoint.timestamp)
                
            else:
                # Save to local file
                checkpoint_file = os.path.join(
                    self.local_storage_path, 
                    f"{checkpoint.workflow_id}_{checkpoint.checkpoint_id}.json"
                )
                with open(checkpoint_file, 'w') as f:
                    json.dump(checkpoint_data, f, indent=2)
                
                # Update workflow index
                index_file = os.path.join(self.local_storage_path, f"{checkpoint.workflow_id}_index.json")
                index_data = {}
                if os.path.exists(index_file):
                    with open(index_file, 'r') as f:
                        index_data = json.load(f)
                
                index_data.update({
                    "last_checkpoint": checkpoint.checkpoint_id,
                    "last_step": checkpoint.step_name,
                    "last_updated": checkpoint.timestamp,
                    "checkpoints": index_data.get("checkpoints", []) + [checkpoint.checkpoint_id]
                })
                
                with open(index_file, 'w') as f:
                    json.dump(index_data, f, indent=2)
            
            logger.debug(f"Checkpoint saved: {checkpoint.checkpoint_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")
            return False
    
    async def load_checkpoint(self, workflow_id: str, checkpoint_id: Optional[str] = None) -> Optional[WorkflowCheckpoint]:
        """
        Load a workflow checkpoint from persistent storage.
        
        Args:
            workflow_id: The workflow ID
            checkpoint_id: Specific checkpoint ID, or None for latest
            
        Returns:
            WorkflowCheckpoint if found, None otherwise
        """
        try:
            if checkpoint_id is None:
                # Get latest checkpoint
                if self.storage_type == "redis":
                    workflow_key = f"workflow:{workflow_id}:meta"
                    checkpoint_id = self.redis_client.hget(workflow_key, "last_checkpoint")
                    if checkpoint_id:
                        checkpoint_id = checkpoint_id.decode('utf-8')
                else:
                    index_file = os.path.join(self.local_storage_path, f"{workflow_id}_index.json")
                    if os.path.exists(index_file):
                        with open(index_file, 'r') as f:
                            index_data = json.load(f)
                        checkpoint_id = index_data.get("last_checkpoint")
            
            if not checkpoint_id:
                return None
            
            # Load checkpoint data
            if self.storage_type == "redis":
                key = f"workflow:{workflow_id}:checkpoint:{checkpoint_id}"
                data = self.redis_client.get(key)
                if data:
                    checkpoint_data = json.loads(data.decode('utf-8'))
                else:
                    return None
            else:
                checkpoint_file = os.path.join(
                    self.local_storage_path, 
                    f"{workflow_id}_{checkpoint_id}.json"
                )
                if os.path.exists(checkpoint_file):
                    with open(checkpoint_file, 'r') as f:
                        checkpoint_data = json.load(f)
                else:
                    return None
            
            return WorkflowCheckpoint(**checkpoint_data)
            
        except Exception as e:
            logger.error(f"Failed to load checkpoint: {e}")
            return None
    
    async def list_checkpoints(self, workflow_id: str) -> List[str]:
        """
        List all available checkpoints for a workflow.
        
        Args:
            workflow_id: The workflow ID
            
        Returns:
            List of checkpoint IDs
        """
        try:
            if self.storage_type == "redis":
                pattern = f"workflow:{workflow_id}:checkpoint:*"
                keys = self.redis_client.keys(pattern)
                return [key.decode('utf-8').split(':')[-1] for key in keys]
            else:
                index_file = os.path.join(self.local_storage_path, f"{workflow_id}_index.json")
                if os.path.exists(index_file):
                    with open(index_file, 'r') as f:
                        index_data = json.load(f)
                    return index_data.get("checkpoints", [])
                return []
                
        except Exception as e:
            logger.error(f"Failed to list checkpoints: {e}")
            return []
    
    async def delete_checkpoint(self, workflow_id: str, checkpoint_id: str) -> bool:
        """
        Delete a specific checkpoint.
        
        Args:
            workflow_id: The workflow ID
            checkpoint_id: The checkpoint ID to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.storage_type == "redis":
                key = f"workflow:{workflow_id}:checkpoint:{checkpoint_id}"
                return bool(self.redis_client.delete(key))
            else:
                checkpoint_file = os.path.join(
                    self.local_storage_path, 
                    f"{workflow_id}_{checkpoint_id}.json"
                )
                if os.path.exists(checkpoint_file):
                    os.remove(checkpoint_file)
                    return True
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete checkpoint: {e}")
            return False
    
    def validate_state_transition(self, current_step: str, next_step: str) -> bool:
        """
        Validate if a state transition is allowed.
        
        Args:
            current_step: Current workflow step
            next_step: Proposed next step
            
        Returns:
            True if transition is valid, False otherwise
        """
        # Define valid state transitions
        valid_transitions = {
            StateTransition.INITIALIZE.value: [StateTransition.ANALYZE_REQUIREMENTS.value],
            StateTransition.ANALYZE_REQUIREMENTS.value: [
                StateTransition.INTELLIGENT_FILTERING.value, 
                StateTransition.ERROR_HANDLING.value
            ],
            StateTransition.INTELLIGENT_FILTERING.value: [
                StateTransition.DATA_CLEANING.value, 
                StateTransition.ERROR_HANDLING.value
            ],
            StateTransition.DATA_CLEANING.value: [
                StateTransition.QUALITY_ASSESSMENT.value, 
                StateTransition.ERROR_HANDLING.value
            ],
            StateTransition.QUALITY_ASSESSMENT.value: [
                StateTransition.ENHANCED_DASHBOARD.value, 
                StateTransition.DATA_CLEANING.value,  # Retry cleaning
                StateTransition.ERROR_HANDLING.value
            ],
            StateTransition.ENHANCED_DASHBOARD.value: [
                StateTransition.FINALIZE_RESULTS.value, 
                StateTransition.ERROR_HANDLING.value
            ],
            StateTransition.FINALIZE_RESULTS.value: [],  # Terminal state
            StateTransition.ERROR_HANDLING.value: []     # Terminal state
        }
        
        allowed_next_steps = valid_transitions.get(current_step, [])
        return next_step in allowed_next_steps

@dataclass
class DataFilteringResult:
    """Result of intelligent data filtering."""
    relevant_columns: List[str]
    irrelevant_columns: List[str]
    metadata_columns: List[str]
    confidence_score: float
    reasoning: str

@dataclass
class PivotTableRecommendation:
    """Enhanced pivot table recommendation with AI insights."""
    name: str
    rows: List[str]
    columns: List[str]
    values: List[str]
    aggregation: str
    confidence: float
    reasoning: str
    suggested_charts: List[str]
    business_relevance: float

class EnhancedWorkflowState(TypedDict):
    """
    Enhanced state object that flows through the LangGraph workflow.
    Contains all data and metadata needed for intelligent processing with state management.
    """
    # Workflow identification and state management
    workflow_id: str
    workflow_status: str  # WorkflowStatus enum value
    started_at: str
    updated_at: str
    
    # Input data
    original_data: Dict[str, Any]
    file_info: Dict[str, Any]
    user_requirements: Dict[str, Any]
    
    # Processing state
    current_step: str
    previous_step: Optional[str]
    processing_history: List[Dict[str, Any]]
    errors: List[Dict[str, Any]]
    
    # Enhanced data filtering
    data_filtering_result: Optional[DataFilteringResult]
    filtered_data: Optional[Dict[str, Any]]
    
    # Processed data at each step
    cleaned_data: Optional[Dict[str, Any]]
    trend_analysis: Optional[Dict[str, Any]]
    forecast_data: Optional[Dict[str, Any]]
    visualization_config: Optional[Dict[str, Any]]
    
    # Enhanced pivot table analysis
    pivot_recommendations: List[PivotTableRecommendation]
    generated_pivot_tables: Dict[str, Any]
    
    # Quality and metrics
    quality_scores: Dict[str, float]
    confidence_scores: Dict[str, float]
    accuracy_metrics: Dict[str, float]
    
    # Final outputs
    dashboard_config: Optional[Dict[str, Any]]
    insights: List[str]
    recommendations: List[str]
    export_ready: bool
    
    # Workflow control
    next_nodes: List[str]
    should_continue: bool
    can_rollback: bool
    checkpoint_enabled: bool
    
    # OpenRouter/LiteLLM integration
    model_provider: str
    model_costs: Dict[str, float]
    processing_metadata: Dict[str, Any]
    
    # State management metadata
    state_version: int
    last_checkpoint_id: Optional[str]
    rollback_points: List[str]

class OpenRouterConfig:
    """Configuration for OpenRouter/LiteLLM integration."""
    
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.api_base = os.getenv("OPENROUTER_API_BASE", "https://openrouter.ai/api/v1")
        self.site_url = os.getenv("OR_SITE_URL", "")
        self.app_name = os.getenv("OR_APP_NAME", "Analytics-Hub")
        
        # Model configurations with cost optimization (including all requested models)
        self.models = {
            "fast": "openrouter/deepseek/deepseek-r1-0528:free",  # Fast, advanced reasoning
            "balanced": "openrouter/google/gemma-3n-e4b-it:free",  # Balanced for analysis
            "advanced": "gemini-2.5-flash",  # Google advanced model for complex tasks
            "research": "gemini-2.5-pro",  # Google pro model for research
            "fallback": "openrouter/meta-llama/llama-3.1-8b-instruct:free"  # Reliable fallback
        }
        
        self.is_available = LITELLM_AVAILABLE and self.api_key is not None
        
        if self.is_available:
            # Set environment variables for LiteLLM
            os.environ["OPENROUTER_API_KEY"] = self.api_key
            if self.site_url:
                os.environ["OR_SITE_URL"] = self.site_url
            if self.app_name:
                os.environ["OR_APP_NAME"] = self.app_name
        
        logger.info(f"OpenRouter integration: {'Available' if self.is_available else 'Not available'}")

class IntelligentDataFilterAgent:
    """AI-powered agent for intelligent data filtering using OpenRouter."""
    
    def __init__(self, openrouter_config: OpenRouterConfig):
        self.config = openrouter_config
        self.model = self.config.models["fast"]  # Use fast model for filtering
    
    async def filter_irrelevant_columns(self, df_info: Dict[str, Any], business_context: str = "") -> DataFilteringResult:
        """Filter out irrelevant columns using AI analysis."""
        
        if not self.config.is_available:
            return self._fallback_filtering(df_info)
        
        try:
            prompt = f"""
You are an expert data analyst. Analyze the following dataset columns and classify them into three categories:

Dataset Information:
- Columns: {list(df_info.get('columns', []))}
- Sample data types: {df_info.get('dtypes', {})}
- Business context: {business_context}

Classify each column as:
1. RELEVANT: Columns that should be included in calculations and charts (numerical data, meaningful categories, dates)
2. IRRELEVANT: Columns that should be excluded (serial numbers, phone numbers, IDs, internal codes)
3. METADATA: Columns that provide context but shouldn't be calculated (names, descriptions, notes)

Respond in JSON format:
{{
    "relevant_columns": ["column1", "column2"],
    "irrelevant_columns": ["serial_no", "phone", "id"],
    "metadata_columns": ["name", "description"],
    "confidence_score": 0.95,
    "reasoning": "Detailed explanation of classification decisions"
}}
"""
            
            response = await acompletion(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=1000
            )
            
            result_data = json.loads(response.choices[0].message.content)
            
            return DataFilteringResult(
                relevant_columns=result_data["relevant_columns"],
                irrelevant_columns=result_data["irrelevant_columns"],
                metadata_columns=result_data["metadata_columns"],
                confidence_score=result_data["confidence_score"],
                reasoning=result_data["reasoning"]
            )
            
        except Exception as e:
            logger.error(f"AI filtering failed: {str(e)}")
            return self._fallback_filtering(df_info)
    
    def _fallback_filtering(self, df_info: Dict[str, Any]) -> DataFilteringResult:
        """Rule-based fallback when AI is not available."""
        columns = df_info.get('columns', [])
        
        # Rule-based classification
        irrelevant_patterns = ['id', 'serial', 'phone', 'mobile', 'contact', 'sl.no', 'sr.no', 'index']
        metadata_patterns = ['name', 'description', 'note', 'comment', 'remark', 'address']
        
        irrelevant_columns = []
        metadata_columns = []
        relevant_columns = []
        
        for col in columns:
            col_lower = str(col).lower()
            
            if any(pattern in col_lower for pattern in irrelevant_patterns):
                irrelevant_columns.append(col)
            elif any(pattern in col_lower for pattern in metadata_patterns):
                metadata_columns.append(col)
            else:
                relevant_columns.append(col)
        
        return DataFilteringResult(
            relevant_columns=relevant_columns,
            irrelevant_columns=irrelevant_columns,
            metadata_columns=metadata_columns,
            confidence_score=0.7,
            reasoning="Rule-based classification using pattern matching"
        )

class EnhancedLangGraphOrchestrator:
    """
    Enhanced LangGraph orchestrator with intelligent data filtering, comprehensive error handling,
    state persistence, intelligent routing, and advanced metadata tracking.
    """
    
    def __init__(self, model: str = "openrouter/anthropic/claude-3-haiku", enable_state_persistence: bool = True):
        self.model = model
        self.enable_state_persistence = enable_state_persistence
        
        # Initialize OpenRouter configuration
        self.openrouter_config = OpenRouterConfig()
        
        # Initialize intelligent filtering agent
        self.filter_agent = IntelligentDataFilterAgent(self.openrouter_config)
        
        # Initialize state manager for persistence
        self.state_manager = None
        if enable_state_persistence:
            try:
                self.state_manager = WorkflowStateManager()
                logger.info("State persistence enabled")
            except Exception as e:
                logger.warning(f"State persistence initialization failed: {e}")
        
        # Build the enhanced workflow
        self.workflow = self._build_enhanced_workflow()
        
        # Metadata tracking
        self.metadata_tracker: Optional[MetadataTracker] = None
        
        # Accuracy scoring system
        self.accuracy_scorer: Optional[AccuracyScorer] = None
        
        logger.info(f"Enhanced LangGraph Orchestrator initialized with model: {model}")
        logger.info(f"OpenRouter integration: {'enabled' if self.openrouter_config.is_available else 'disabled'}")
        logger.info(f"State persistence: {'enabled' if self.state_manager else 'disabled'}")
    
    def _build_enhanced_workflow(self) -> StateGraph:
        """
        Build the enhanced LangGraph workflow with intelligent routing and conditional pathways.
        
        Returns:
            Compiled StateGraph ready for execution with intelligent routing
        """
        # Create the enhanced state graph
        workflow = StateGraph(EnhancedWorkflowState)
        
        # Add enhanced workflow nodes
        workflow.add_node("initialize", self._initialize_enhanced_processing)
        workflow.add_node("analyze_requirements", self._analyze_requirements)
        workflow.add_node("intelligent_data_filtering", self._execute_intelligent_filtering)
        workflow.add_node("data_cleaning", self._execute_data_cleaning)
        workflow.add_node("quality_assessment", self._assess_data_quality)
        workflow.add_node("enhanced_dashboard_generation", self._generate_enhanced_dashboard)
        workflow.add_node("finalize_results", self._finalize_enhanced_results)
        workflow.add_node("error_handling", self._handle_errors)
        
        # Add new intelligent routing nodes
        workflow.add_node("route_by_complexity", self._route_by_complexity)
        workflow.add_node("route_by_quality", self._route_by_quality)
        workflow.add_node("simple_processing", self._execute_simple_processing)
        workflow.add_node("advanced_processing", self._execute_advanced_processing)
        workflow.add_node("retry_cleaning", self._retry_data_cleaning)
        
        # Define intelligent workflow routing with conditional edges
        workflow.add_edge(START, "initialize")
        workflow.add_edge("initialize", "analyze_requirements")
        
        # Complexity-based routing after requirements analysis
        workflow.add_conditional_edges(
            "analyze_requirements",
            self._determine_processing_path,
            {
                "simple": "simple_processing",
                "advanced": "route_by_complexity", 
                "error": "error_handling"
            }
        )
        
        # Simple processing path for low-complexity data
        workflow.add_edge("simple_processing", "finalize_results")
        
        # Advanced processing path with intelligent routing
        workflow.add_edge("route_by_complexity", "intelligent_data_filtering")
        workflow.add_edge("intelligent_data_filtering", "data_cleaning")
        workflow.add_edge("data_cleaning", "route_by_quality")
        
        # Quality-based routing after cleaning
        workflow.add_conditional_edges(
            "route_by_quality",
            self._determine_quality_path,
            {
                "proceed": "enhanced_dashboard_generation",
                "retry": "retry_cleaning",
                "assess": "quality_assessment",
                "error": "error_handling"
            }
        )
        
        # Quality assessment and retry paths
        workflow.add_edge("retry_cleaning", "data_cleaning")
        workflow.add_conditional_edges(
            "quality_assessment",
            self._determine_dashboard_path,
            {
                "generate": "enhanced_dashboard_generation",
                "retry": "retry_cleaning",
                "error": "error_handling"
            }
        )
        
        # Dashboard generation paths
        workflow.add_conditional_edges(
            "enhanced_dashboard_generation",
            self._determine_finalization_path,
            {
                "finalize": "finalize_results",
                "retry": "enhanced_dashboard_generation",
                "error": "error_handling"
            }
        )
        
        # Terminal states
        workflow.add_edge("error_handling", END)
        workflow.add_edge("finalize_results", END)
        
        return workflow.compile()
    
    def _determine_processing_path(self, state: EnhancedWorkflowState) -> str:
        """
        Intelligent routing to determine processing complexity path with metadata tracking.
        
        Args:
            state: Current workflow state
            
        Returns:
            Route key for conditional edge routing
        """
        try:
            file_info = state.get("file_info", {})
            user_requirements = state.get("user_requirements", {})
            
            # Calculate data complexity
            complexity_score = self._calculate_data_complexity(file_info)
            
            # Check for errors in analysis
            if state.get("errors"):
                return "error"
            
            # Determine available routes
            available_routes = ["simple", "advanced", "error"]
            
            # Decision factors for routing
            decision_factors = {
                "complexity_score": complexity_score,
                "num_columns": len(file_info.get("columns", [])),
                "num_rows": file_info.get("row_count", 0),
                "enable_ai_filtering": user_requirements.get("enable_ai_filtering", True),
                "enable_pivot_analysis": user_requirements.get("enable_pivot_analysis", True)
            }
            
            # Simple path for small, simple datasets
            if complexity_score < 3.0:
                num_columns = len(file_info.get("columns", []))
                num_rows = file_info.get("row_count", 0)
                
                # Very simple data can bypass complex processing
                if num_columns <= 5 and num_rows <= 1000:
                    chosen_route = "simple"
                    reasoning = f"Simple processing selected: low complexity ({complexity_score:.1f}), small dataset ({num_columns} cols, {num_rows} rows)"
                    confidence = 0.9
                else:
                    chosen_route = "advanced"
                    reasoning = f"Advanced processing required despite low complexity due to dataset size"
                    confidence = 0.7
            else:
                # Advanced path for complex data or when user requires advanced features
                chosen_route = "advanced"
                reasoning = f"Advanced processing required: complexity {complexity_score:.1f}/10, AI features enabled"
                confidence = 0.8
            
            # Track routing decision
            if self.metadata_tracker:
                routing_decision = RoutingDecision.create(
                    step="analyze_requirements",
                    decision_point="processing_path",
                    decision_factors=decision_factors,
                    available_routes=available_routes,
                    chosen_route=chosen_route,
                    reasoning=reasoning,
                    confidence_score=confidence
                )
                self.metadata_tracker.track_routing_decision(routing_decision)
            
            logger.info(f"Routing to {chosen_route} processing path: {reasoning}")
            return chosen_route
            
        except Exception as e:
            logger.error(f"Error in processing path determination: {e}")
            if self.metadata_tracker:
                self.metadata_tracker.track_error("analyze_requirements", e, "high")
            return "error"
    
    def _determine_quality_path(self, state: EnhancedWorkflowState) -> str:
        """
        Intelligent routing based on data quality after cleaning.
        
        Args:
            state: Current workflow state
            
        Returns:
            Route key for quality-based conditional routing
        """
        try:
            quality_scores = state.get("quality_scores", {})
            processing_history = state.get("processing_history", [])
            
            # Check for critical errors
            if state.get("errors"):
                critical_errors = [e for e in state["errors"] if e.get("type") == "critical"]
                if critical_errors:
                    return "error"
            
            # Get cleaning quality score
            cleaning_score = quality_scores.get("cleaned", 0.0)
            
            # Count retry attempts
            retry_count = sum(1 for step in processing_history if step.get("step") == "retry_cleaning")
            
            # If quality is very high, proceed directly
            if cleaning_score >= 8.5:
                logger.info("High quality data - proceeding to dashboard generation")
                return "proceed"
            
            # If quality is low and we haven't retried too many times, retry
            if cleaning_score < 6.0 and retry_count < 2:
                logger.info("Low quality data - retrying cleaning")
                return "retry"
            
            # For medium quality or after retries, do quality assessment
            if cleaning_score >= 6.0 or retry_count >= 2:
                logger.info("Medium quality data - conducting assessment")
                return "assess"
            
            # Fallback to error handling
            return "error"
            
        except Exception as e:
            logger.error(f"Error in quality path determination: {e}")
            return "error"
    
    def _determine_dashboard_path(self, state: EnhancedWorkflowState) -> str:
        """
        Intelligent routing after quality assessment.
        
        Args:
            state: Current workflow state
            
        Returns:
            Route key for dashboard generation path
        """
        try:
            quality_scores = state.get("quality_scores", {})
            confidence_scores = state.get("confidence_scores", {})
            processing_history = state.get("processing_history", [])
            
            # Check for errors
            if state.get("errors"):
                return "error"
            
            # Get overall quality and confidence
            overall_quality = quality_scores.get("overall", 0.0)
            overall_confidence = confidence_scores.get("overall", 0.0)
            
            # Count retry attempts
            retry_count = sum(1 for step in processing_history 
                            if step.get("step") in ["retry_cleaning", "quality_assessment"])
            
            # If quality and confidence are acceptable, proceed to dashboard
            if overall_quality >= 0.6 and overall_confidence >= 0.7:
                logger.info("Quality assessment passed - generating dashboard")
                return "generate"
            
            # If quality is borderline and we haven't exceeded retries, try again
            if overall_quality >= 0.4 and retry_count < 3:
                logger.info("Quality borderline - retrying cleaning process")
                return "retry"
            
            # If quality is consistently poor, might still generate with warnings
            if retry_count >= 3:
                logger.warning("Maximum retries reached - proceeding with current quality")
                return "generate"
            
            return "error"
            
        except Exception as e:
            logger.error(f"Error in dashboard path determination: {e}")
            return "error"
    
    def _determine_finalization_path(self, state: EnhancedWorkflowState) -> str:
        """
        Intelligent routing for dashboard finalization.
        
        Args:
            state: Current workflow state
            
        Returns:
            Route key for finalization path
        """
        try:
            dashboard_config = state.get("dashboard_config")
            processing_history = state.get("processing_history", [])
            
            # Check for errors
            if state.get("errors"):
                critical_errors = [e for e in state["errors"] 
                                 if e.get("severity") in ["high", "fatal"]]
                if critical_errors:
                    return "error"
            
            # Check if dashboard was successfully generated
            if dashboard_config and len(dashboard_config.get("charts", [])) > 0:
                logger.info("Dashboard generation successful - finalizing results")
                return "finalize"
            
            # Count dashboard generation attempts
            dashboard_attempts = sum(1 for step in processing_history 
                                   if step.get("step") == "enhanced_dashboard_generation")
            
            # Retry dashboard generation if not too many attempts
            if dashboard_attempts < 2:
                logger.info("Dashboard generation incomplete - retrying")
                return "retry"
            
            # After multiple attempts, still finalize with what we have
            logger.warning("Dashboard generation struggled - finalizing with available results")
            return "finalize"
            
        except Exception as e:
            logger.error(f"Error in finalization path determination: {e}")
            return "error"
    
    def _execute_simple_processing(self, state: EnhancedWorkflowState) -> EnhancedWorkflowState:
        """
        Execute simplified processing for low-complexity data.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated workflow state
        """
        logger.info("Executing simplified processing for low-complexity data")
        
        # Update state transition
        state = self._update_state_transition(state, "simple_processing")
        
        try:
            original_data = state.get("original_data", {})
            file_info = state.get("file_info", {})
            
            # Basic data preparation without complex filtering
            cleaned_data = {
                "columns": original_data.get("columns", []),
                "data": original_data.get("data", {}),
                "cleaning_summary": {"approach": "simple", "operations": "basic_validation"},
                "row_count": len(next(iter(original_data.get("data", {}).values()), [])),
                "simple_processing": True
            }
            
            state["cleaned_data"] = cleaned_data
            state["quality_scores"]["overall"] = 7.0  # Assume good quality for simple data
            state["insights"].append("Simple processing applied for low-complexity dataset")
            
            # Add processing history
            state["processing_history"].append({
                "step": "simple_processing",
                "timestamp": datetime.now().isoformat(),
                "status": "completed",
                "approach": "simplified"
            })
            
            # Generate basic dashboard config
            basic_dashboard = self._generate_basic_dashboard(cleaned_data, file_info)
            state["dashboard_config"] = basic_dashboard
            state["export_ready"] = True
            
        except Exception as e:
            error_info = {
                "step": "simple_processing", 
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            state["errors"].append(error_info)
            logger.error(f"Simple processing failed: {e}")
        
        return state
    
    def _execute_advanced_processing(self, state: EnhancedWorkflowState) -> EnhancedWorkflowState:
        """
        Setup for advanced processing path.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated workflow state
        """
        logger.info("Preparing for advanced processing workflow")
        
        state = self._update_state_transition(state, "advanced_processing")
        
        state["processing_metadata"]["processing_mode"] = "advanced"
        state["processing_metadata"]["features_enabled"] = {
            "ai_filtering": True,
            "enhanced_cleaning": True,
            "quality_assessment": True,
            "intelligent_routing": True
        }
        
        return state
    
    def _route_by_complexity(self, state: EnhancedWorkflowState) -> EnhancedWorkflowState:
        """
        Route processing based on data complexity analysis.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated workflow state
        """
        logger.info("Routing based on data complexity")
        
        state = self._update_state_transition(state, "route_by_complexity")
        
        file_info = state.get("file_info", {})
        complexity_score = self._calculate_data_complexity(file_info)
        
        # Set processing parameters based on complexity
        if complexity_score >= 7.0:
            state["processing_metadata"]["complexity_level"] = "high"
            state["processing_metadata"]["recommended_models"] = ["advanced", "balanced"]
        elif complexity_score >= 4.0:
            state["processing_metadata"]["complexity_level"] = "medium"
            state["processing_metadata"]["recommended_models"] = ["balanced", "fast"]
        else:
            state["processing_metadata"]["complexity_level"] = "low"
            state["processing_metadata"]["recommended_models"] = ["fast"]
        
        state["insights"].append(f"Data complexity assessed: {complexity_score:.1f}/10")
        
        return state
    
    def _route_by_quality(self, state: EnhancedWorkflowState) -> EnhancedWorkflowState:
        """
        Route processing based on data quality metrics.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated workflow state
        """
        logger.info("Routing based on data quality metrics")
        
        state = self._update_state_transition(state, "route_by_quality")
        
        quality_scores = state.get("quality_scores", {})
        
        # Set quality-based routing parameters
        overall_quality = quality_scores.get("overall", quality_scores.get("cleaned", 0.0))
        
        if overall_quality >= 8.0:
            state["processing_metadata"]["quality_level"] = "excellent"
            state["processing_metadata"]["quality_actions"] = ["proceed_directly"]
        elif overall_quality >= 6.0:
            state["processing_metadata"]["quality_level"] = "good"
            state["processing_metadata"]["quality_actions"] = ["standard_assessment"]
        else:
            state["processing_metadata"]["quality_level"] = "needs_improvement"
            state["processing_metadata"]["quality_actions"] = ["enhanced_cleaning", "quality_boost"]
        
        state["insights"].append(f"Data quality level: {state['processing_metadata']['quality_level']}")
        
        return state
    
    def _retry_data_cleaning(self, state: EnhancedWorkflowState) -> EnhancedWorkflowState:
        """
        Enhanced retry of data cleaning with improved parameters.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated workflow state
        """
        logger.info("Retrying data cleaning with enhanced parameters")
        
        state = self._update_state_transition(state, "retry_cleaning")
        
        try:
            # Get previous cleaning attempts
            retry_count = sum(1 for step in state.get("processing_history", []) 
                            if step.get("step") == "retry_cleaning")
            
            # Enhance cleaning parameters based on retry count
            if retry_count == 1:
                # More aggressive null handling
                state["processing_metadata"]["cleaning_mode"] = "aggressive"
            elif retry_count == 2:
                # Most conservative approach
                state["processing_metadata"]["cleaning_mode"] = "conservative"
            else:
                # Fallback mode
                state["processing_metadata"]["cleaning_mode"] = "fallback"
            
            # Execute the actual cleaning with retry context
            original_data = state.get("original_data", {})
            filtered_data = state.get("filtered_data", {})
            relevant_columns = filtered_data.get("relevant_columns", original_data.get("columns", []))
            
            # Enhanced cleaning with retry-specific improvements
            cleaning_results = self._perform_enhanced_cleaning_with_retry(
                original_data, relevant_columns, retry_count
            )
            
            state["cleaned_data"] = cleaning_results
            state["quality_scores"]["cleaned"] = cleaning_results.get("cleaning_score", 0.0)
            
            state["processing_history"].append({
                "step": "retry_cleaning",
                "timestamp": datetime.now().isoformat(),
                "status": "completed",
                "retry_attempt": retry_count + 1,
                "cleaning_mode": state["processing_metadata"]["cleaning_mode"]
            })
            
            state["insights"].append(f"Data cleaning retry #{retry_count + 1} completed")
            
        except Exception as e:
            error_info = {
                "step": "retry_cleaning",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "retry_attempt": retry_count + 1
            }
            state["errors"].append(error_info)
            logger.error(f"Retry cleaning failed: {e}")
        
        return state
    
    def _perform_enhanced_cleaning_with_retry(self, original_data: Dict[str, Any], 
                                            relevant_columns: List[str], 
                                            retry_count: int) -> Dict[str, Any]:
        """
        Enhanced cleaning with retry-specific improvements.
        
        Args:
            original_data: Original dataset
            relevant_columns: Columns to clean
            retry_count: Number of previous retry attempts
            
        Returns:
            Enhanced cleaning results
        """
        try:
            # Get base cleaning results
            base_results = self._perform_enhanced_cleaning(original_data, relevant_columns)
            
            # Apply retry-specific enhancements
            if retry_count == 0:  # First retry - more aggressive outlier handling
                base_results["retry_enhancements"] = {
                    "outlier_threshold": 1.0,  # More strict
                    "null_strategy": "aggressive_imputation",
                    "duplicate_handling": "strict"
                }
            elif retry_count == 1:  # Second retry - conservative approach  
                base_results["retry_enhancements"] = {
                    "outlier_threshold": 3.0,  # More lenient
                    "null_strategy": "preserve_structure",
                    "duplicate_handling": "lenient"
                }
            else:  # Fallback - minimal processing
                base_results["retry_enhancements"] = {
                    "outlier_threshold": None,  # No outlier removal
                    "null_strategy": "minimal",
                    "duplicate_handling": "none"
                }
            
            # Boost cleaning score based on retry improvements
            original_score = base_results.get("cleaning_score", 0.0)
            retry_bonus = 0.5 * (retry_count + 1)  # Incremental improvement
            base_results["cleaning_score"] = min(10.0, original_score + retry_bonus)
            
            return base_results
            
        except Exception as e:
            logger.error(f"Enhanced retry cleaning failed: {e}")
            return self._perform_enhanced_cleaning(original_data, relevant_columns)
    
    def _generate_basic_dashboard(self, cleaned_data: Dict[str, Any], 
                                file_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a basic dashboard configuration for simple processing.
        
        Args:
            cleaned_data: Cleaned dataset
            file_info: File information
            
        Returns:
            Basic dashboard configuration
        """
        try:
            columns = cleaned_data.get("columns", [])
            
            # Generate basic charts for simple data
            charts = []
            
            # Simple column chart for first few columns
            if len(columns) >= 2:
                charts.append({
                    "type": "column",
                    "title": f"Overview of {columns[0]} vs {columns[1]}",
                    "x_axis": columns[0],
                    "y_axis": columns[1],
                    "confidence": 0.8
                })
            
            # Table view for all data
            charts.append({
                "type": "table",
                "title": "Data Overview",
                "columns": columns,
                "confidence": 0.9
            })
            
            return {
                "title": f"Simple Dashboard - {file_info.get('filename', 'Dataset')}",
                "charts": charts,
                "metadata": {
                    "processing_mode": "simple",
                    "generation_time": datetime.now().isoformat(),
                    "data_points": cleaned_data.get("row_count", 0),
                    "chart_count": len(charts)
                },
                "insights": [
                    "Basic dashboard generated for simple dataset",
                    f"Processed {len(columns)} columns successfully"
                ]
            }
            
        except Exception as e:
            logger.error(f"Basic dashboard generation failed: {e}")
            return {
                "title": "Basic Dashboard",
                "charts": [],
                "metadata": {"error": str(e)},
                "insights": ["Dashboard generation encountered issues"]
            }
    
    def _initialize_enhanced_processing(self, state: EnhancedWorkflowState) -> EnhancedWorkflowState:
        """Initialize the enhanced processing workflow with state setup and metadata tracking."""
        logger.info("Initializing enhanced workflow processing with metadata tracking")
        
        # Initialize workflow identification
        workflow_id = state.get("workflow_id") or str(uuid.uuid4())
        current_time = datetime.now().isoformat()
        
        state["workflow_id"] = workflow_id
        state["workflow_status"] = WorkflowStatus.RUNNING.value
        state["started_at"] = current_time
        state["updated_at"] = current_time
        state["current_step"] = "initialize"
        state["previous_step"] = None
        
        state["processing_history"] = [{
            "step": "initialize",
            "timestamp": current_time,
            "status": "started"
        }]
        state["errors"] = []
        state["quality_scores"] = {}
        state["confidence_scores"] = {}
        state["accuracy_metrics"] = {}
        state["insights"] = []
        state["recommendations"] = []
        state["export_ready"] = False
        state["should_continue"] = True
        state["can_rollback"] = False
        state["checkpoint_enabled"] = self.enable_state_persistence
        state["pivot_recommendations"] = []
        state["generated_pivot_tables"] = {}
        state["model_provider"] = "openrouter" if self.openrouter_config.is_available else "fallback"
        state["model_costs"] = {}
        state["processing_metadata"] = {
            "openrouter_enabled": self.openrouter_config.is_available,
            "workflow_version": "enhanced_v1.0",
            "state_persistence": self.enable_state_persistence,
            "metadata_tracking": True
        }
        
        # State management metadata
        state["state_version"] = 1
        state["last_checkpoint_id"] = None
        state["rollback_points"] = []
        
        # Initialize metadata tracker
        session_id = state.get("user_requirements", {}).get("session_id")
        self.metadata_tracker = MetadataTracker(workflow_id, session_id)
        
        # Initialize accuracy scorer
        self.accuracy_scorer = AccuracyScorer(self.metadata_tracker)
        
        # Track data source metadata
        original_data = state.get("original_data", {})
        file_info = state.get("file_info", {})
        if original_data and file_info:
            self.metadata_tracker.track_data_source(file_info, original_data)
        
        # Track initialization step
        self.metadata_tracker.track_processing_step("initialize", "completed", {
            "workflow_id": workflow_id,
            "model_provider": state["model_provider"],
            "features_enabled": state["processing_metadata"]
        })
        
        # Create initial checkpoint if persistence is enabled
        if self.state_manager:
            asyncio.create_task(self._save_checkpoint(state, "initialize"))
        
        return state
    
    async def _save_checkpoint(self, state: EnhancedWorkflowState, step_name: str) -> bool:
        """
        Save a workflow checkpoint to persistent storage.
        
        Args:
            state: Current workflow state
            step_name: Name of the workflow step
            
        Returns:
            True if successful, False otherwise
        """
        if not self.state_manager:
            return False
        
        try:
            # Update state metadata
            state["updated_at"] = datetime.now().isoformat()
            state["state_version"] += 1
            
            # Create checkpoint
            checkpoint = WorkflowCheckpoint.create(
                workflow_id=state["workflow_id"],
                step_name=step_name,
                state_data=dict(state),
                metadata={
                    "step_duration": self._calculate_step_duration(state),
                    "memory_usage": self._get_memory_usage(state),
                    "model_provider": state.get("model_provider", "unknown")
                }
            )
            
            # Save checkpoint
            success = await self.state_manager.save_checkpoint(checkpoint)
            if success:
                state["last_checkpoint_id"] = checkpoint.checkpoint_id
                state["rollback_points"].append(checkpoint.checkpoint_id)
                logger.debug(f"Checkpoint saved for step {step_name}: {checkpoint.checkpoint_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")
            return False
    
    async def _load_checkpoint(self, workflow_id: str, checkpoint_id: Optional[str] = None) -> Optional[EnhancedWorkflowState]:
        """
        Load a workflow state from checkpoint.
        
        Args:
            workflow_id: The workflow ID
            checkpoint_id: Specific checkpoint ID, or None for latest
            
        Returns:
            EnhancedWorkflowState if found, None otherwise
        """
        if not self.state_manager:
            return None
        
        try:
            checkpoint = await self.state_manager.load_checkpoint(workflow_id, checkpoint_id)
            if checkpoint:
                logger.info(f"Loaded checkpoint: {checkpoint.checkpoint_id}")
                return checkpoint.state_data
            return None
            
        except Exception as e:
            logger.error(f"Failed to load checkpoint: {e}")
            return None
    
    def _calculate_step_duration(self, state: EnhancedWorkflowState) -> float:
        """Calculate duration of current step in seconds."""
        history = state.get("processing_history", [])
        if len(history) < 2:
            return 0.0
        
        try:
            current_time = datetime.now()
            last_step_time = datetime.fromisoformat(history[-1]["timestamp"])
            return (current_time - last_step_time).total_seconds()
        except Exception:
            return 0.0
    
    def _get_memory_usage(self, state: EnhancedWorkflowState) -> Dict[str, Any]:
        """Get approximate memory usage of state components."""
        import sys
        
        return {
            "total_size_bytes": sys.getsizeof(state),
            "data_components": {
                "original_data": sys.getsizeof(state.get("original_data", {})),
                "cleaned_data": sys.getsizeof(state.get("cleaned_data", {})),
                "processing_history": sys.getsizeof(state.get("processing_history", [])),
                "insights": sys.getsizeof(state.get("insights", []))
            }
        }
    
    def _update_state_transition(self, state: EnhancedWorkflowState, new_step: str) -> EnhancedWorkflowState:
        """
        Update state with new step and validate transition.
        
        Args:
            state: Current workflow state
            new_step: New step to transition to
            
        Returns:
            Updated state
        """
        current_step = state.get("current_step", "")
        
        # Validate transition if state manager is available
        if self.state_manager and not self.state_manager.validate_state_transition(current_step, new_step):
            logger.warning(f"Invalid state transition from {current_step} to {new_step}")
            state["errors"].append({
                "step": current_step,
                "error": f"Invalid transition to {new_step}",
                "timestamp": datetime.now().isoformat(),
                "type": "state_transition_error"
            })
        
        # Update state
        state["previous_step"] = current_step
        state["current_step"] = new_step
        state["updated_at"] = datetime.now().isoformat()
        state["can_rollback"] = len(state.get("rollback_points", [])) > 0
        
        return state
    
    def _analyze_requirements(self, state: EnhancedWorkflowState) -> EnhancedWorkflowState:
        """Analyze file and user requirements to determine enhanced processing pipeline."""
        logger.info("Analyzing requirements for enhanced processing")
        
        # Update state transition
        state = self._update_state_transition(state, "analyze_requirements")
        
        try:
            # Add processing history entry
            state["processing_history"].append({
                "step": "analyze_requirements",
                "timestamp": datetime.now().isoformat(),
                "status": "started"
            })
            
            file_info = state.get("file_info", {})
            user_requirements = state.get("user_requirements", {})
            
            # Enhanced requirement analysis with data introspection
            pipeline_needs = {
                "needs_data_filtering": True,  # Always enable intelligent filtering
                "accuracy_priority": user_requirements.get("accuracy_priority", "high"),
                "performance_priority": user_requirements.get("performance_priority", "medium"),
                "complexity_score": self._calculate_data_complexity(file_info),
                "estimated_processing_time": self._estimate_processing_time(file_info)
            }
            
            state["user_requirements"]["pipeline_needs"] = pipeline_needs
            
            # Add completion entry to processing history
            state["processing_history"].append({
                "step": "analyze_requirements",
                "timestamp": datetime.now().isoformat(),
                "status": "completed",
                "results": {
                    "complexity_score": pipeline_needs["complexity_score"],
                    "estimated_time": pipeline_needs["estimated_processing_time"]
                }
            })
            
            # Save checkpoint
            if self.state_manager:
                asyncio.create_task(self._save_checkpoint(state, "analyze_requirements"))
            
        except Exception as e:
            error_info = {
                "step": "analyze_requirements",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "type": "processing_error"
            }
            state["errors"].append(error_info)
            state["processing_history"].append({
                "step": "analyze_requirements",
                "timestamp": datetime.now().isoformat(),
                "status": "failed",
                "error": str(e)
            })
            logger.error(f"Requirements analysis failed: {str(e)}")
        
        return state
    
    def _calculate_data_complexity(self, file_info: Dict[str, Any]) -> float:
        """Calculate data complexity score based on file characteristics."""
        try:
            complexity_score = 1.0
            
            # File size factor
            file_size = file_info.get("size", 0)
            if file_size > 10 * 1024 * 1024:  # > 10MB
                complexity_score += 2.0
            elif file_size > 1 * 1024 * 1024:  # > 1MB
                complexity_score += 1.0
            
            # Sheet count factor (for Excel files)
            sheet_count = len(file_info.get("sheets", []))
            if sheet_count > 3:
                complexity_score += 1.5
            elif sheet_count > 1:
                complexity_score += 0.5
            
            # Column count factor
            total_columns = sum(len(sheet.get("columns", [])) for sheet in file_info.get("sheets", []))
            if total_columns > 50:
                complexity_score += 2.0
            elif total_columns > 20:
                complexity_score += 1.0
            
            return min(complexity_score, 10.0)  # Cap at 10
            
        except Exception:
            return 5.0  # Default medium complexity
    
    def _estimate_processing_time(self, file_info: Dict[str, Any]) -> float:
        """Estimate processing time in seconds based on data complexity."""
        complexity = self._calculate_data_complexity(file_info)
        base_time = 30.0  # Base 30 seconds
        return base_time + (complexity * 10.0)  # Add 10 seconds per complexity point
    
    def _execute_intelligent_filtering(self, state: EnhancedWorkflowState) -> EnhancedWorkflowState:
        """Execute intelligent data filtering to remove irrelevant columns."""
        logger.info("Executing intelligent data filtering")
        
        # Update state transition
        state = self._update_state_transition(state, "intelligent_data_filtering")
        
        try:
            # Add processing history entry
            state["processing_history"].append({
                "step": "intelligent_data_filtering",
                "timestamp": datetime.now().isoformat(),
                "status": "started"
            })
            
            original_data = state.get("original_data", {})
            file_info = state.get("file_info", {})
            
            # Prepare comprehensive data info for filtering
            df_info = {
                "columns": original_data.get("columns", []),
                "dtypes": original_data.get("dtypes", {}),
                "sample_data": original_data.get("sample_data", {}),
                "row_count": original_data.get("row_count", 0),
                "null_counts": original_data.get("null_counts", {}),
                "unique_counts": original_data.get("unique_counts", {})
            }
            
            # Enhanced business context
            business_context = f"File: {file_info.get('filename', '')}, Sheets: {len(file_info.get('sheets', []))}"
            
            # Execute intelligent filtering with retry logic
            filtering_result = None
            max_retries = 3
            
            for attempt in range(max_retries):
                try:
                    filtering_result = asyncio.run(
                        self.filter_agent.filter_irrelevant_columns(df_info, business_context)
                    )
                    break
                except Exception as retry_error:
                    logger.warning(f"Filtering attempt {attempt + 1} failed: {retry_error}")
                    if attempt == max_retries - 1:
                        raise retry_error
                    time.sleep(1)  # Brief delay before retry
            
            if not filtering_result:
                raise Exception("Failed to obtain filtering results after retries")
            
            state["data_filtering_result"] = filtering_result
            
            # Create enhanced filtered data structure
            filtered_data = {
                "relevant_columns": filtering_result.relevant_columns,
                "irrelevant_columns": filtering_result.irrelevant_columns,
                "metadata_columns": filtering_result.metadata_columns,
                "filtering_confidence": filtering_result.confidence_score,
                "filtering_reasoning": filtering_result.reasoning,
                "original_column_count": len(df_info.get("columns", [])),
                "columns_removed": len(filtering_result.irrelevant_columns),
                "columns_retained": len(filtering_result.relevant_columns),
                "filter_effectiveness": len(filtering_result.irrelevant_columns) / max(len(df_info.get("columns", [])), 1)
            }
            
            state["filtered_data"] = filtered_data
            state["quality_scores"]["data_filtering"] = filtering_result.confidence_score
            state["accuracy_metrics"]["column_relevance"] = filtering_result.confidence_score
            
            # Enhanced insights with detailed statistics
            state["insights"].append(f"AI filtering removed {len(filtering_result.irrelevant_columns)}/{len(df_info.get('columns', []))} irrelevant columns")
            state["insights"].append(f"Retained {len(filtering_result.relevant_columns)} relevant columns for analysis")
            state["insights"].append(f"Filtering confidence: {filtering_result.confidence_score:.2f}")
            
            if filtering_result.reasoning:
                state["insights"].append(f"Filtering rationale: {filtering_result.reasoning[:100]}...")
            
            # Track model costs
            if state.get("model_provider") == "openrouter":
                state["model_costs"]["data_filtering"] = 0.001  # Estimated cost
            
            # Add completion entry to processing history
            state["processing_history"].append({
                "step": "intelligent_data_filtering",
                "timestamp": datetime.now().isoformat(),
                "status": "completed",
                "results": {
                    "columns_removed": len(filtering_result.irrelevant_columns),
                    "columns_retained": len(filtering_result.relevant_columns),
                    "confidence": filtering_result.confidence_score
                }
            })
            
            # Save checkpoint
            if self.state_manager:
                asyncio.create_task(self._save_checkpoint(state, "intelligent_data_filtering"))
            
        except Exception as e:
            error_info = {
                "step": "intelligent_data_filtering",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "type": "ai_processing_error"
            }
            state["errors"].append(error_info)
            state["processing_history"].append({
                "step": "intelligent_data_filtering",
                "timestamp": datetime.now().isoformat(),
                "status": "failed",
                "error": str(e)
            })
            logger.error(f"Intelligent data filtering failed: {str(e)}")
            
            # Fallback: proceed without filtering
            state["insights"].append("AI filtering failed, proceeding with all columns")
            state["filtered_data"] = {
                "relevant_columns": original_data.get("columns", []),
                "irrelevant_columns": [],
                "metadata_columns": []
            }
        
        return state
    
    def _execute_data_cleaning(self, state: EnhancedWorkflowState) -> EnhancedWorkflowState:
        """Execute enhanced data cleaning with comprehensive metadata tracking."""
        logger.info("Executing enhanced data cleaning with metadata tracking")
        
        # Update state transition with validation
        state = self._update_state_transition(state, "data_cleaning")
        step_start_time = time.time()
        
        try:
            original_data = state.get("original_data", {})
            filtering_result = state.get("data_filtering_result")
            
            # Track transformation start
            input_schema = {
                "columns": original_data.get("columns", []),
                "row_count": len(next(iter(original_data.get("data", {}).values()), [])),
                "data_types": original_data.get("column_types", {})
            }
            
            # Determine columns to clean
            if filtering_result and filtering_result.relevant_columns:
                relevant_columns = filtering_result.relevant_columns
                logger.info(f"Cleaning {len(relevant_columns)} relevant columns identified by filtering")
            else:
                relevant_columns = original_data.get("columns", [])
                logger.info(f"Cleaning all {len(relevant_columns)} columns (no filtering applied)")
            
            # Execute enhanced cleaning
            cleaning_results = self._perform_enhanced_cleaning(original_data, relevant_columns)
            
            # Calculate execution time
            execution_time = time.time() - step_start_time
            
            # Track transformation
            if self.metadata_tracker:
                output_schema = {
                    "columns": relevant_columns,
                    "row_count": cleaning_results.get("row_count", 0),
                    "cleaning_score": cleaning_results.get("cleaning_score", 0.0)
                }
                
                transformation = DataTransformation.create(
                    step="data_cleaning",
                    transformation_type="enhanced_cleaning",
                    input_schema=input_schema,
                    output_schema=output_schema,
                    transformation_params={
                        "relevant_columns": relevant_columns,
                        "cleaning_operations": cleaning_results.get("cleaning_summary", {})
                    }
                )
                transformation.execution_time = execution_time
                transformation.quality_impact = {
                    "cleaning_score": cleaning_results.get("cleaning_score", 0.0),
                    "null_ratio_improvement": cleaning_results.get("null_handling", {}).get("null_ratio", 0.0)
                }
                transformation.data_changes = {
                    "rows_processed": cleaning_results.get("cleaning_summary", {}).get("rows_processed", 0),
                    "null_values_processed": cleaning_results.get("cleaning_summary", {}).get("null_values_processed", 0),
                    "duplicates_removed": cleaning_results.get("cleaning_summary", {}).get("duplicates_removed", 0),
                    "outliers_flagged": cleaning_results.get("cleaning_summary", {}).get("outliers_flagged", 0)
                }
                
                self.metadata_tracker.track_transformation(transformation)
                self.metadata_tracker.track_performance_metrics("data_cleaning", execution_time)
            
            # Update state with cleaning results
            state["cleaned_data"] = cleaning_results
            state["quality_scores"]["cleaned"] = cleaning_results.get("cleaning_score", 0.0)
            
            # Add insights based on cleaning results
            cleaning_summary = cleaning_results.get("cleaning_summary", {})
            if cleaning_summary.get("null_values_processed", 0) > 0:
                state["insights"].append(f"Processed {cleaning_summary['null_values_processed']} null values during cleaning")
            
            if cleaning_summary.get("outliers_flagged", 0) > 0:
                state["insights"].append(f"Identified {cleaning_summary['outliers_flagged']} potential outliers")
            
            # Add processing history
            state["processing_history"].append({
                "step": "data_cleaning",
                "timestamp": datetime.now().isoformat(),
                "status": "completed",
                "duration": execution_time,
                "cleaning_score": cleaning_results.get("cleaning_score", 0.0),
                "operations_performed": cleaning_summary
            })
            
            # Track step completion
            if self.metadata_tracker:
                self.metadata_tracker.track_processing_step("data_cleaning", "completed", {
                    "execution_time": execution_time,
                    "cleaning_score": cleaning_results.get("cleaning_score", 0.0),
                    "data_quality_impact": transformation.quality_impact if 'transformation' in locals() else {}
                })
            
            # Save checkpoint
            if state.get("checkpoint_enabled"):
                asyncio.create_task(self._save_checkpoint(state, "data_cleaning"))
            
        except Exception as e:
            execution_time = time.time() - step_start_time
            error_info = {
                "step": "data_cleaning",
                "error": str(e),
                "error_type": type(e).__name__,
                "timestamp": datetime.now().isoformat(),
                "execution_time": execution_time
            }
            state["errors"].append(error_info)
            
            # Track error in metadata
            if self.metadata_tracker:
                self.metadata_tracker.track_error("data_cleaning", e, "high")
                self.metadata_tracker.track_processing_step("data_cleaning", "failed", {
                    "error": str(e),
                    "execution_time": execution_time
                })
            
            logger.error(f"Enhanced data cleaning failed: {str(e)}")
        
        return state
    
    def _perform_enhanced_cleaning(self, original_data: Dict[str, Any], relevant_columns: List[str]) -> Dict[str, Any]:
        """Perform comprehensive data cleaning operations."""
        try:
            data_dict = original_data.get("data", {})
            
            # Initialize results
            cleaned_data = {}
            cleaning_summary = {
                "rows_processed": 0,
                "null_values_processed": 0,
                "duplicates_removed": 0,
                "outliers_flagged": 0,
                "data_types_converted": 0
            }
            
            # Process each relevant column
            for col in relevant_columns:
                col_data = data_dict.get(col, [])
                if not col_data:
                    cleaned_data[col] = []
                    continue
                
                # Basic null handling
                non_null_data = [x for x in col_data if x is not None and str(x).strip() != ""]
                cleaning_summary["null_values_processed"] += len(col_data) - len(non_null_data)
                
                # Simple outlier detection for numeric columns
                try:
                    numeric_data = [float(x) for x in non_null_data if str(x).replace('.', '').replace('-', '').isdigit()]
                    if len(numeric_data) > 0:
                        # Basic IQR outlier detection
                        q1 = sorted(numeric_data)[len(numeric_data)//4]
                        q3 = sorted(numeric_data)[3*len(numeric_data)//4]
                        iqr = q3 - q1
                        outlier_threshold = 1.5 * iqr
                        outliers = [x for x in numeric_data if x < q1 - outlier_threshold or x > q3 + outlier_threshold]
                        cleaning_summary["outliers_flagged"] += len(outliers)
                        
                        # Keep outliers but flag them
                        cleaned_data[col] = non_null_data
                    else:
                        cleaned_data[col] = non_null_data
                except Exception:
                    # Non-numeric data
                    cleaned_data[col] = non_null_data
            
            # Calculate overall statistics
            total_rows = max(len(data_dict.get(col, [])) for col in relevant_columns) if relevant_columns else 0
            cleaning_summary["rows_processed"] = total_rows
            
            # Simple duplicate detection based on first column
            if relevant_columns and cleaned_data.get(relevant_columns[0]):
                first_col_data = cleaned_data[relevant_columns[0]]
                unique_values = set(first_col_data)
                cleaning_summary["duplicates_removed"] = len(first_col_data) - len(unique_values)
            
            # Data type detection
            data_types = {}
            for col in relevant_columns:
                col_data = cleaned_data.get(col, [])
                if col_data:
                    sample_value = next((x for x in col_data if x is not None), None)
                    if sample_value is not None:
                        if str(sample_value).replace('.', '').replace('-', '').isdigit():
                            data_types[col] = "numeric"
                        else:
                            data_types[col] = "text"
                    else:
                        data_types[col] = "unknown"
                else:
                    data_types[col] = "empty"
            
            # Calculate cleaning quality score
            null_ratio = cleaning_summary["null_values_processed"] / max(total_rows * len(relevant_columns), 1)
            duplicate_ratio = cleaning_summary["duplicates_removed"] / max(total_rows, 1)
            cleaning_score = max(0, 2.0 - (null_ratio * 2) - (duplicate_ratio * 1))
            
            return {
                "cleaned_data": cleaned_data,
                "cleaning_summary": cleaning_summary,
                "data_types": data_types,
                "row_count": total_rows,
                "null_handling": {"strategy": "removal", "null_ratio": null_ratio},
                "outlier_detection": {"method": "iqr", "outliers_found": cleaning_summary["outliers_flagged"]},
                "duplicate_removal": {"duplicates_found": cleaning_summary["duplicates_removed"]},
                "cleaning_score": cleaning_score
            }
            
        except Exception as e:
            logger.error(f"Enhanced cleaning operation failed: {e}")
            return {
                "cleaned_data": {col: original_data.get("data", {}).get(col, []) for col in relevant_columns},
                "cleaning_summary": {"error": str(e)},
                "data_types": {},
                "row_count": 0,
                "null_handling": {},
                "outlier_detection": {},
                "duplicate_removal": {},
                "cleaning_score": 0.0
            }
    
    def _assess_data_quality(self, state: EnhancedWorkflowState) -> EnhancedWorkflowState:
        """Comprehensive data quality assessment with advanced metrics and validation."""
        logger.info("Conducting comprehensive data quality assessment")
        
        # Update state transition with validation
        state = self._update_state_transition(state, "quality_assessment")
        step_start_time = time.time()
        
        try:
            # Collect quality metrics from previous steps
            filtering_result = state.get("data_filtering_result")
            cleaned_data = state.get("cleaned_data", {})
            original_data = state.get("original_data", {})
            processing_history = state.get("processing_history", [])
            
            # Calculate comprehensive quality scores
            quality_metrics = self._calculate_comprehensive_quality_metrics(
                original_data, cleaned_data, filtering_result, processing_history
            )
            
            # Assess data integrity and completeness
            integrity_scores = self._assess_data_integrity(cleaned_data, original_data)
            
            # Evaluate filtering effectiveness
            filtering_effectiveness = self._evaluate_filtering_effectiveness(filtering_result, cleaned_data)
            
            # Calculate confidence scores for different aspects
            confidence_metrics = self._calculate_confidence_metrics(
                quality_metrics, integrity_scores, filtering_effectiveness
            )
            
            # Generate quality insights and recommendations
            quality_insights = self._generate_quality_insights(
                quality_metrics, integrity_scores, filtering_effectiveness
            )
            
            # Update state with comprehensive quality assessment
            state["quality_scores"].update({
                "overall": quality_metrics["overall_score"],
                "data_completeness": quality_metrics["completeness"],
                "data_consistency": quality_metrics["consistency"],
                "data_accuracy": quality_metrics["accuracy"],
                "filtering_effectiveness": filtering_effectiveness["score"],
                "processing_efficiency": quality_metrics["efficiency"]
            })
            
            state["accuracy_metrics"].update({
                "data_relevance": filtering_result.confidence_score if filtering_result else 0.5,
                "data_cleanliness": quality_metrics["cleanliness"],
                "overall_accuracy": quality_metrics["overall_score"],
                "integrity_score": integrity_scores["overall"],
                "confidence_level": confidence_metrics["overall"]
            })
            
            state["confidence_scores"].update(confidence_metrics)
            
            # Add quality insights to state
            state["insights"].extend(quality_insights["insights"])
            state["recommendations"].extend(quality_insights["recommendations"])
            
            # Add processing history entry
            state["processing_history"].append({
                "step": "quality_assessment",
                "timestamp": datetime.now().isoformat(),
                "status": "completed",
                "duration": time.time() - step_start_time,
                "metrics": {
                    "overall_quality": quality_metrics["overall_score"],
                    "data_integrity": integrity_scores["overall"],
                    "filtering_effectiveness": filtering_effectiveness["score"],
                    "confidence_level": confidence_metrics["overall"]
                }
            })
            
            # Determine if quality meets thresholds for proceeding
            quality_threshold = 0.6  # Minimum quality threshold
            if quality_metrics["overall_score"] >= quality_threshold:
                state["can_rollback"] = True
                logger.info(f"Quality assessment passed - Overall score: {quality_metrics['overall_score']:.3f}")
            else:
                state["recommendations"].append(
                    f"Data quality score ({quality_metrics['overall_score']:.3f}) is below threshold ({quality_threshold}). "
                    "Consider improving data sources or cleaning processes."
                )
                logger.warning(f"Quality assessment concerns - Overall score: {quality_metrics['overall_score']:.3f}")
            
            # Save checkpoint
            if state.get("checkpoint_enabled"):
                asyncio.create_task(self._save_checkpoint(state, "quality_assessment"))
            
        except Exception as e:
            error_info = {
                "step": "quality_assessment",
                "error": str(e),
                "error_type": type(e).__name__,
                "timestamp": datetime.now().isoformat()
            }
            state["errors"].append(error_info)
            logger.error(f"Quality assessment failed: {str(e)}")
            
            # Fallback quality scores
            state["quality_scores"]["overall"] = 0.5
            state["accuracy_metrics"]["overall_accuracy"] = 0.5
        
        return state
    
    def _calculate_comprehensive_quality_metrics(self, 
                                               original_data: Dict[str, Any], 
                                               cleaned_data: Dict[str, Any],
                                               filtering_result: Optional[DataFilteringResult],
                                               processing_history: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate comprehensive quality metrics across multiple dimensions."""
        
        # Data completeness (how much data remains after cleaning)
        original_rows = len(next(iter(original_data.values()), [])) if original_data else 0
        cleaned_rows = len(next(iter(cleaned_data.values()), [])) if cleaned_data else 0
        completeness = (cleaned_rows / original_rows) if original_rows > 0 else 0
        
        # Data consistency (based on successful processing steps)
        successful_steps = sum(1 for step in processing_history if step.get("status") != "error")
        total_steps = len(processing_history) if processing_history else 1
        consistency = successful_steps / total_steps
        
        # Data accuracy (based on filtering confidence and cleaning results)
        filtering_confidence = filtering_result.confidence_score if filtering_result else 0.5
        
        # Calculate null ratio improvement
        original_null_ratio = self._calculate_null_ratio(original_data)
        cleaned_null_ratio = self._calculate_null_ratio(cleaned_data)
        null_improvement = max(0, original_null_ratio - cleaned_null_ratio)
        cleanliness = min(1.0, 0.5 + null_improvement)
        
        # Processing efficiency (based on error count and duration)
        error_count = sum(1 for step in processing_history if step.get("status") == "error")
        efficiency = max(0.1, 1.0 - (error_count * 0.2))
        
        # Calculate weighted overall score
        overall_score = (
            completeness * 0.25 +
            consistency * 0.25 +
            filtering_confidence * 0.25 +
            cleanliness * 0.15 +
            efficiency * 0.10
        )
        
        return {
            "overall_score": round(overall_score, 3),
            "completeness": round(completeness, 3),
            "consistency": round(consistency, 3),
            "accuracy": round(filtering_confidence, 3),
            "cleanliness": round(cleanliness, 3),
            "efficiency": round(efficiency, 3)
        }
    
    def _assess_data_integrity(self, cleaned_data: Dict[str, Any], original_data: Dict[str, Any]) -> Dict[str, float]:
        """Assess data integrity comparing cleaned vs original data."""
        
        # Column integrity (how many columns were preserved)
        original_cols = len(original_data) if original_data else 0
        cleaned_cols = len(cleaned_data) if cleaned_data else 0
        column_integrity = (cleaned_cols / original_cols) if original_cols > 0 else 0
        
        # Row integrity (how many rows were preserved)
        original_rows = len(next(iter(original_data.values()), [])) if original_data else 0
        cleaned_rows = len(next(iter(cleaned_data.values()), [])) if cleaned_data else 0
        row_integrity = (cleaned_rows / original_rows) if original_rows > 0 else 0
        
        # Value integrity (estimate of data preservation)
        value_integrity = min(column_integrity, row_integrity)
        
        # Overall integrity
        overall_integrity = (column_integrity * 0.3 + row_integrity * 0.4 + value_integrity * 0.3)
        
        return {
            "overall": round(overall_integrity, 3),
            "column_preservation": round(column_integrity, 3),
            "row_preservation": round(row_integrity, 3),
            "value_preservation": round(value_integrity, 3)
        }
    
    def _evaluate_filtering_effectiveness(self, filtering_result: Optional[DataFilteringResult], cleaned_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate the effectiveness of the data filtering process."""
        
        if not filtering_result:
            return {"score": 0.5, "reasoning": "No filtering result available"}
        
        relevant_cols = len(filtering_result.relevant_columns)
        irrelevant_cols = len(filtering_result.irrelevant_columns)
        total_cols = relevant_cols + irrelevant_cols
        
        # Calculate filtering precision
        precision = (relevant_cols / total_cols) if total_cols > 0 else 0
        
        # Factor in confidence score
        effectiveness_score = (filtering_result.confidence_score * 0.7 + precision * 0.3)
        
        return {
            "score": round(effectiveness_score, 3),
            "precision": round(precision, 3),
            "relevant_columns": relevant_cols,
            "filtered_columns": irrelevant_cols,
            "confidence": filtering_result.confidence_score,
            "reasoning": filtering_result.reasoning
        }
    
    def _calculate_confidence_metrics(self, 
                                    quality_metrics: Dict[str, float],
                                    integrity_scores: Dict[str, float],
                                    filtering_effectiveness: Dict[str, Any]) -> Dict[str, float]:
        """Calculate confidence metrics for different quality aspects."""
        
        # Data processing confidence
        processing_confidence = min(0.95, quality_metrics["consistency"] * quality_metrics["efficiency"])
        
        # Data reliability confidence  
        reliability_confidence = min(0.95, integrity_scores["overall"] * quality_metrics["completeness"])
        
        # Filtering confidence (already available)
        filtering_confidence = filtering_effectiveness["score"]
        
        # Overall confidence
        overall_confidence = (
            processing_confidence * 0.4 +
            reliability_confidence * 0.3 +
            filtering_confidence * 0.3
        )
        
        return {
            "overall": round(overall_confidence, 3),
            "data_processing": round(processing_confidence, 3),
            "data_reliability": round(reliability_confidence, 3),
            "data_filtering": round(filtering_confidence, 3)
        }
    
    def _generate_quality_insights(self, 
                                 quality_metrics: Dict[str, float],
                                 integrity_scores: Dict[str, float],
                                 filtering_effectiveness: Dict[str, Any]) -> Dict[str, List[str]]:
        """Generate actionable insights based on quality assessment."""
        
        insights = []
        recommendations = []
        
        # Quality insights
        overall_score = quality_metrics["overall_score"]
        if overall_score >= 0.8:
            insights.append(f"Excellent data quality achieved (score: {overall_score:.2f})")
        elif overall_score >= 0.6:
            insights.append(f"Good data quality with room for improvement (score: {overall_score:.2f})")
        else:
            insights.append(f"Data quality needs attention (score: {overall_score:.2f})")
        
        # Completeness insights
        completeness = quality_metrics["completeness"]
        if completeness < 0.7:
            insights.append(f"Significant data loss during processing ({(1-completeness)*100:.1f}% of rows removed)")
            recommendations.append("Review data cleaning parameters to preserve more valid data")
        
        # Filtering insights
        filtering_score = filtering_effectiveness["score"]
        if filtering_score >= 0.8:
            insights.append(f"Highly effective data filtering (confidence: {filtering_score:.2f})")
        elif filtering_score < 0.6:
            insights.append(f"Data filtering may need refinement (confidence: {filtering_score:.2f})")
            recommendations.append("Consider refining filtering criteria or providing more business context")
        
        # Integrity insights
        integrity = integrity_scores["overall"]
        if integrity < 0.7:
            recommendations.append("Monitor data integrity - significant structural changes detected")
        
        return {
            "insights": insights,
            "recommendations": recommendations
        }
    
    def _calculate_null_ratio(self, data: Dict[str, Any]) -> float:
        """Calculate the ratio of null values in the dataset."""
        if not data:
            return 0.0
        
        total_values = 0
        null_values = 0
        
        for col_data in data.values():
            if isinstance(col_data, list):
                total_values += len(col_data)
                null_values += sum(1 for x in col_data if x is None or x == "")
        
        return (null_values / total_values) if total_values > 0 else 0.0
    
    async def _generate_enhanced_dashboard(self, state: EnhancedWorkflowState) -> EnhancedWorkflowState:
        """Generate enhanced dashboard with intelligent components, chart recommendations, and AI insights."""
        logger.info("Generating enhanced dashboard with intelligent analysis and AI dashboard generator integration")
        
        # Update state transition with validation
        state = self._update_state_transition(state, "enhanced_dashboard_generation")
        step_start_time = time.time()
        
        try:
            filtering_result = state.get("data_filtering_result")
            cleaned_data = state.get("cleaned_data", {})
            file_info = state.get("file_info", {})
            user_requirements = state.get("user_requirements", {})
            
            # Import and initialize the AI dashboard generator
            from src.services.ai_dashboard_generator import AIDashboardGenerator
            ai_generator = AIDashboardGenerator()
            
            # Convert cleaned data to the format expected by AI dashboard generator
            dashboard_data = self._prepare_data_for_ai_generator(cleaned_data, file_info, filtering_result)
            
            # Check if we should use AI dashboard generator integration
            use_ai_generator = user_requirements.get("enable_ai_integration", True)
            
            if use_ai_generator and dashboard_data:
                logger.info("Using integrated AI dashboard generator for enhanced chart generation")
                
                # Generate dashboard using AI generator with the cleaned data
                ai_dashboard_result = await self._generate_dashboard_with_ai_generator(
                    ai_generator, dashboard_data, file_info, user_requirements
                )
                
                # Enhance the AI generator results with LangGraph workflow insights
                enhanced_dashboard_config = await self._enhance_ai_dashboard_with_workflow_insights(
                    ai_dashboard_result, state, filtering_result
                )
                
                # Update state with enhanced AI dashboard results
                state["dashboard_config"] = enhanced_dashboard_config
                state["visualization_config"] = enhanced_dashboard_config.get("visualization_config", {})
                state["export_ready"] = True
                
            else:
                logger.info("Using fallback LangGraph dashboard generation")
                
                # Fallback to original LangGraph dashboard generation
                chart_recommendations = await self._generate_intelligent_chart_recommendations(
                    cleaned_data, filtering_result, user_requirements
                )
                
                pivot_recommendations = await self._generate_pivot_table_recommendations(
                    cleaned_data, filtering_result, file_info
                )
                
                visualization_config = await self._create_visualization_config(
                    cleaned_data, chart_recommendations, pivot_recommendations
                )
                
                ai_insights = await self._generate_ai_insights(
                    cleaned_data, filtering_result, chart_recommendations
                )
                
                dashboard_quality = self._calculate_dashboard_quality(
                    chart_recommendations, pivot_recommendations, filtering_result
                )
                
                # Create fallback dashboard configuration
                enhanced_dashboard_config = {
                    "version": "enhanced_langgraph_v2.0",
                    "workflow_id": state["workflow_id"],
                    "generated_at": datetime.now().isoformat(),
                    "generation_method": "langgraph_fallback",
                    
                    # Data filtering results
                    "data_filtering": {
                        "relevant_columns": filtering_result.relevant_columns if filtering_result else [],
                        "irrelevant_columns": filtering_result.irrelevant_columns if filtering_result else [],
                        "metadata_columns": filtering_result.metadata_columns if filtering_result else [],
                        "confidence": filtering_result.confidence_score if filtering_result else 0,
                        "reasoning": filtering_result.reasoning if filtering_result else ""
                    },
                    
                    # Chart and visualization configuration
                    "charts": chart_recommendations,
                    "pivot_tables": pivot_recommendations,
                    "visualization_config": visualization_config,
                    
                    # Quality and metrics
                    "quality_metrics": {
                        "dashboard_score": dashboard_quality,
                        "data_quality": state.get("quality_scores", {}).get("overall", 0),
                        "filtering_effectiveness": filtering_result.confidence_score if filtering_result else 0,
                        "chart_relevance": dashboard_quality.get("chart_relevance", 0),
                        "pivot_usefulness": dashboard_quality.get("pivot_usefulness", 0)
                    },
                    
                    # AI insights
                    "ai_insights": ai_insights,
                    
                    # Processing metadata
                    "processing_metadata": {
                        **state.get("processing_metadata", {}),
                        "dashboard_generation_time": time.time() - step_start_time,
                        "chart_count": len(chart_recommendations),
                        "pivot_count": len(pivot_recommendations),
                        "data_complexity": state.get("processing_metadata", {}).get("data_complexity", 0)
                    }
                }
                
                state["dashboard_config"] = enhanced_dashboard_config
                state["visualization_config"] = visualization_config
                state["export_ready"] = True
            
            # Update pivot recommendations and insights regardless of method used
            if "pivot_tables" in state["dashboard_config"]:
                state["pivot_recommendations"] = state["dashboard_config"]["pivot_tables"]
            
            if "ai_insights" in state["dashboard_config"]:
                insights = state["dashboard_config"]["ai_insights"]
                state["insights"].extend(insights.get("key_insights", []))
                state["recommendations"].extend(insights.get("recommendations", []))
            
            # Update quality scores
            quality_metrics = state["dashboard_config"].get("quality_metrics", {})
            state["quality_scores"]["dashboard"] = quality_metrics.get("dashboard_score", 0)
            state["confidence_scores"]["dashboard_generation"] = quality_metrics.get("confidence", 0.8)
            
            # Add processing history entry
            state["processing_history"].append({
                "step": "enhanced_dashboard_generation",
                "timestamp": datetime.now().isoformat(),
                "status": "completed",
                "duration": time.time() - step_start_time,
                "generation_method": state["dashboard_config"].get("generation_method", "unknown"),
                "metrics": {
                    "charts_generated": len(state["dashboard_config"].get("charts", [])),
                    "pivots_generated": len(state["dashboard_config"].get("pivot_tables", [])),
                    "insights_generated": len(state.get("insights", [])),
                    "dashboard_score": quality_metrics.get("dashboard_score", 0)
                }
            })
            
            # Save checkpoint
            if state.get("checkpoint_enabled"):
                await self._save_checkpoint(state, "enhanced_dashboard_generation")
            
            chart_count = len(state["dashboard_config"].get("charts", []))
            pivot_count = len(state["dashboard_config"].get("pivot_tables", []))
            generation_method = state["dashboard_config"].get("generation_method", "unknown")
            
            logger.info(f"Enhanced dashboard generated successfully using {generation_method} with {chart_count} charts and {pivot_count} pivot tables")
            
        except Exception as e:
            error_info = {
                "step": "enhanced_dashboard_generation",
                "error": str(e),
                "error_type": type(e).__name__,
                "timestamp": datetime.now().isoformat()
            }
            state["errors"].append(error_info)
            logger.error(f"Enhanced dashboard generation failed: {str(e)}")
            
            # Fallback to basic dashboard config
            state["dashboard_config"] = {
                "version": "error_fallback_v1.0",
                "workflow_id": state.get("workflow_id", "unknown"),
                "generated_at": datetime.now().isoformat(),
                "error": str(e),
                "generation_method": "error_fallback",
                "basic_config": True,
                "export_ready": False,
                "charts": [],
                "pivot_tables": [],
                "quality_metrics": {"dashboard_score": 0}
            }
        
        return state

    def _prepare_data_for_ai_generator(self, cleaned_data: Dict[str, Any], file_info: Dict[str, Any], filtering_result: Optional[DataFilteringResult]) -> Optional[bytes]:
        """
        Prepare cleaned data for AI dashboard generator by converting it to Excel-like format.
        
        Args:
            cleaned_data: The cleaned dataset
            file_info: File information metadata
            filtering_result: Data filtering results
            
        Returns:
            bytes: Excel file content for AI generator, or None if conversion fails
        """
        try:
            import pandas as pd
            import io
            
            # Extract relevant data based on filtering results
            if filtering_result and filtering_result.relevant_columns:
                # Use only relevant columns identified by filtering
                relevant_data = {}
                for col in filtering_result.relevant_columns:
                    if col in cleaned_data:
                        relevant_data[col] = cleaned_data[col]
                data_to_convert = relevant_data
            else:
                # Use all cleaned data
                data_to_convert = cleaned_data
            
            # Convert to DataFrame
            if isinstance(data_to_convert, dict):
                # Check if it's in rows format or columns format
                if 'rows' in data_to_convert and isinstance(data_to_convert['rows'], list):
                    # Data is in rows format
                    df = pd.DataFrame(data_to_convert['rows'])
                elif isinstance(data_to_convert, dict) and all(isinstance(v, list) for v in data_to_convert.values()):
                    # Data is in columns format
                    df = pd.DataFrame(data_to_convert)
                else:
                    # Data is in some other format, try to convert
                    df = pd.DataFrame([data_to_convert])
            else:
                # Data is already in a suitable format
                df = pd.DataFrame(data_to_convert)
            
            # Convert DataFrame to Excel bytes
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Sheet1', index=False)
            
            excel_buffer.seek(0)
            return excel_buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Failed to prepare data for AI generator: {str(e)}")
            return None

    async def _generate_dashboard_with_ai_generator(self, ai_generator: 'AIDashboardGenerator', 
                                                  dashboard_data: bytes, file_info: Dict[str, Any], 
                                                  user_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate dashboard using the AI dashboard generator service.
        
        Args:
            ai_generator: The AI dashboard generator instance
            dashboard_data: Excel file data for processing
            file_info: File information metadata
            user_requirements: User requirements and preferences
            
        Returns:
            Dashboard configuration from AI generator
        """
        try:
            filename = file_info.get("filename", "dashboard_data.xlsx")
            
            # Call the AI dashboard generator
            result = await ai_generator.analyze_and_generate_dashboard(
                file_data=dashboard_data,
                filename=filename,
                generate_per_sheet=False  # Generate unified dashboard
            )
            
            return result
            
        except Exception as e:
            logger.error(f"AI dashboard generator failed: {str(e)}")
            # Return empty result to trigger fallback
            return {}

    async def _enhance_ai_dashboard_with_workflow_insights(self, ai_dashboard_result: Dict[str, Any], 
                                                         state: EnhancedWorkflowState, 
                                                         filtering_result: Optional[DataFilteringResult]) -> Dict[str, Any]:
        """
        Enhance AI dashboard generator results with LangGraph workflow insights and metadata.
        
        Args:
            ai_dashboard_result: Result from AI dashboard generator
            state: Current workflow state
            filtering_result: Data filtering results
            
        Returns:
            Enhanced dashboard configuration
        """
        try:
            # Start with AI generator results as base
            enhanced_config = ai_dashboard_result.copy()
            
            # Add LangGraph workflow metadata
            enhanced_config.update({
                "version": "enhanced_ai_langgraph_v2.0",
                "workflow_id": state["workflow_id"],
                "generation_method": "ai_generator_with_langgraph_enhancement",
                "workflow_enhancements": True
            })
            
            # Add data filtering insights from LangGraph workflow
            if filtering_result:
                enhanced_config["data_filtering"] = {
                    "relevant_columns": filtering_result.relevant_columns,
                    "irrelevant_columns": filtering_result.irrelevant_columns,
                    "metadata_columns": filtering_result.metadata_columns,
                    "confidence": filtering_result.confidence_score,
                    "reasoning": filtering_result.reasoning
                }
            
            # Enhance quality metrics with workflow data
            workflow_quality = state.get("quality_scores", {})
            existing_quality = enhanced_config.get("quality_metrics", {})
            enhanced_config["quality_metrics"] = {
                **existing_quality,
                "data_quality": workflow_quality.get("overall", 0),
                "filtering_effectiveness": filtering_result.confidence_score if filtering_result else 0,
                "workflow_quality_score": workflow_quality.get("overall", 0),
                "confidence": state.get("confidence_scores", {}).get("overall", 0.8)
            }
            
            # Add workflow processing metadata
            enhanced_config["processing_metadata"] = {
                **enhanced_config.get("processing_metadata", {}),
                **state.get("processing_metadata", {}),
                "workflow_steps_completed": len(state.get("processing_history", [])),
                "intelligent_filtering_used": filtering_result is not None,
                "data_cleaning_applied": state.get("cleaned_data") is not None,
                "quality_assessment_completed": bool(state.get("quality_scores"))
            }
            
            # Add workflow insights and recommendations
            workflow_insights = state.get("insights", [])
            ai_insights = enhanced_config.get("ai_insights", {})
            
            if isinstance(ai_insights, dict):
                enhanced_config["ai_insights"] = {
                    **ai_insights,
                    "workflow_insights": workflow_insights,
                    "combined_insights": list(set(
                        ai_insights.get("key_insights", []) + workflow_insights
                    ))
                }
            else:
                enhanced_config["ai_insights"] = {
                    "key_insights": workflow_insights,
                    "workflow_insights": workflow_insights
                }
            
            return enhanced_config
            
        except Exception as e:
            logger.error(f"Failed to enhance AI dashboard with workflow insights: {str(e)}")
            # Return original AI result if enhancement fails
            return ai_dashboard_result
    
    def _finalize_enhanced_results(self, state: EnhancedWorkflowState) -> EnhancedWorkflowState:
        """Finalize and prepare the enhanced workflow results for export with comprehensive accuracy scoring."""
        logger.info("Finalizing enhanced workflow results with accuracy scoring")
        
        # Update state transition
        state = self._update_state_transition(state, "finalize_results")
        
        try:
            # Calculate comprehensive accuracy metrics
            accuracy_metrics = None
            accuracy_dashboard = None
            if self.accuracy_scorer:
                accuracy_metrics = self.accuracy_scorer.calculate_accuracy_scores(state)
                accuracy_dashboard = self.accuracy_scorer.generate_accuracy_dashboard()
                
                # Add accuracy metrics to state
                state["accuracy_metrics"] = accuracy_metrics.to_dict()
                state["accuracy_report"] = accuracy_metrics.get_performance_report()
                state["accuracy_dashboard"] = accuracy_dashboard
                
                logger.info(f"Calculated overall accuracy score: {accuracy_metrics.overall_accuracy_score:.3f}")
            
            # Update final state properties
            state["current_step"] = "finalize_results"
            state["should_continue"] = False
            state["export_ready"] = True
            state["workflow_status"] = WorkflowStatus.COMPLETED.value
            state["updated_at"] = datetime.now().isoformat()
            
            # Enhanced final insights with accuracy information
            error_count = len(state.get("errors", []))
            
            if accuracy_metrics:
                overall_accuracy = accuracy_metrics.overall_accuracy_score
                confidence_interval = accuracy_metrics.score_confidence_interval
                
                state["insights"].extend([
                    f"Enhanced workflow completed with overall accuracy: {overall_accuracy:.3f}",
                    f"Accuracy confidence interval: [{confidence_interval[0]:.3f}, {confidence_interval[1]:.3f}]",
                    f"Data quality score: {accuracy_metrics.data_quality_score:.3f}",
                    f"Processing accuracy: {accuracy_metrics.processing_score:.3f}",
                    f"Output quality: {accuracy_metrics.output_quality_score:.3f}"
                ])
                
                # Add accuracy-based recommendations
                accuracy_recommendations = accuracy_metrics._generate_recommendations()
                state["recommendations"].extend([
                    f"Accuracy Improvement: {rec}" for rec in accuracy_recommendations[:3]
                ])
            
            if error_count == 0:
                state["insights"].append("Enhanced workflow completed successfully with no errors")
            else:
                state["insights"].append(f"Enhanced workflow completed with {error_count} errors - see accuracy report for details")
            
            # Add processing summary
            processing_duration = self._calculate_processing_duration(state)
            state["insights"].append(f"Total processing time: {processing_duration:.2f} seconds")
            
            # Add final processing history entry
            state["processing_history"].append({
                "step": "finalize_results",
                "timestamp": datetime.now().isoformat(),
                "status": "completed",
                "duration": processing_duration,
                "final_accuracy": accuracy_metrics.overall_accuracy_score if accuracy_metrics else None,
                "total_errors": error_count,
                "export_ready": True
            })
            
            # Track finalization in metadata
            if self.metadata_tracker:
                self.metadata_tracker.track_processing_step("finalize_results", "completed", {
                    "total_processing_time": processing_duration,
                    "overall_accuracy": accuracy_metrics.overall_accuracy_score if accuracy_metrics else None,
                    "error_count": error_count,
                    "export_ready": True
                })
            
            logger.info("Enhanced workflow finalization completed successfully")
            
        except Exception as e:
            logger.error(f"Error during workflow finalization: {e}")
            state["errors"].append({
                "step": "finalize_results",
                "error": str(e),
                "error_type": "finalization_error",
                "timestamp": datetime.now().isoformat()
            })
            
            # Track error in metadata
            if self.metadata_tracker:
                self.metadata_tracker.track_error("finalize_results", e, "medium")
        
        return state
    
    async def _handle_errors(self, state: EnhancedWorkflowState) -> EnhancedWorkflowState:
        """Comprehensive error handling with recovery, classification, and remediation."""
        logger.warning("Initiating comprehensive error handling and recovery procedures")
        
        # Update state transition
        state = self._update_state_transition(state, "error_handling")
        error_handling_start = time.time()
        
        try:
            # Analyze all errors in the workflow
            errors = state.get("errors", [])
            if not errors:
                logger.info("No errors found - transitioning to completion")
                state["should_continue"] = True
                return state
            
            # Convert raw errors to structured WorkflowError objects
            structured_errors = self._analyze_and_categorize_errors(errors)
            
            # Assess error severity and recoverability
            error_assessment = self._assess_error_impact(structured_errors, state)
            
            # Attempt automatic recovery for recoverable errors
            recovery_results = await self._attempt_error_recovery(structured_errors, state)
            
            # Update error state with recovery results
            state = self._update_error_state(state, structured_errors, recovery_results, error_assessment)
            
            # Determine workflow continuation strategy
            continuation_strategy = self._determine_continuation_strategy(error_assessment, recovery_results)
            
            # Generate error insights and recommendations
            error_insights = self._generate_error_insights(structured_errors, recovery_results, error_assessment)
            
            # Update state with error handling results
            state["processing_metadata"]["error_handling"] = {
                "total_errors": len(structured_errors),
                "critical_errors": len([e for e in structured_errors if e.severity in [ErrorSeverity.HIGH, ErrorSeverity.FATAL]]),
                "recovered_errors": recovery_results["successful_recoveries"],
                "continuation_strategy": continuation_strategy["strategy"],
                "error_handling_duration": time.time() - error_handling_start
            }
            
            # Add error insights to workflow insights
            state["insights"].extend(error_insights["insights"])
            state["recommendations"].extend(error_insights["recommendations"])
            
            # Set workflow continuation based on strategy
            state["should_continue"] = continuation_strategy["can_continue"]
            state["workflow_status"] = continuation_strategy["status"]
            
            # Save recovery checkpoint if significant recovery occurred
            if recovery_results["successful_recoveries"] > 0 and state.get("checkpoint_enabled"):
                await self._save_checkpoint(state, "error_recovery")
            
            # Add processing history entry
            state["processing_history"].append({
                "step": "error_handling",
                "timestamp": datetime.now().isoformat(),
                "status": "completed",
                "duration": time.time() - error_handling_start,
                "metrics": {
                    "errors_processed": len(structured_errors),
                    "errors_recovered": recovery_results["successful_recoveries"],
                    "critical_errors": error_assessment["critical_count"],
                    "workflow_recoverable": continuation_strategy["can_continue"]
                }
            })
            
            logger.info(f"Error handling completed - {recovery_results['successful_recoveries']}/{len(structured_errors)} errors recovered")
            
        except Exception as e:
            logger.error(f"Error handling system failure: {str(e)}")
            
            # Fallback error handling
            state["workflow_status"] = WorkflowStatus.FAILED.value
            state["should_continue"] = False
            state["insights"].append("Critical error in error handling system - workflow terminated")
            
            # Add system error to errors list
            system_error = {
                "step": "error_handling",
                "error": "Error handling system failure",
                "error_type": "system_error",
                "severity": "fatal",
                "timestamp": datetime.now().isoformat(),
                "details": {"exception": str(e)}
            }
            state["errors"].append(system_error)
        
        return state
    
    def _analyze_and_categorize_errors(self, raw_errors: List[Dict[str, Any]]) -> List[WorkflowError]:
        """Analyze and categorize raw errors into structured WorkflowError objects."""
        structured_errors = []
        
        for error_data in raw_errors:
            try:
                # Extract error information
                step = error_data.get("step", "unknown")
                message = error_data.get("error", "Unknown error")
                error_type_str = error_data.get("error_type", "processing_error")
                
                # Determine error type
                error_type = self._classify_error_type(message, error_type_str, error_data)
                
                # Determine severity
                severity = self._assess_error_severity(error_type, message, error_data)
                
                # Create structured error
                workflow_error = WorkflowError.create(
                    error_type=error_type,
                    severity=severity,
                    step=step,
                    message=message,
                    details=error_data
                )
                
                # Determine if auto-recoverable
                workflow_error.auto_recoverable = self._is_auto_recoverable(workflow_error)
                workflow_error.recovery_options = self._get_recovery_options(workflow_error)
                
                structured_errors.append(workflow_error)
                
            except Exception as e:
                logger.error(f"Failed to categorize error: {e}")
                # Create a generic error object
                generic_error = WorkflowError.create(
                    error_type=WorkflowErrorType.PROCESSING_ERROR,
                    severity=ErrorSeverity.MEDIUM,
                    step="error_analysis",
                    message=f"Error categorization failed: {str(e)}",
                    details=error_data
                )
                structured_errors.append(generic_error)
        
        return structured_errors
    
    def _classify_error_type(self, message: str, error_type_str: str, error_data: Dict[str, Any]) -> WorkflowErrorType:
        """Classify error type based on message content and context."""
        message_lower = message.lower()
        
        # API-related errors
        if any(keyword in message_lower for keyword in ["api", "openrouter", "litellm", "rate limit", "quota", "authentication"]):
            return WorkflowErrorType.API_ERROR
        
        # Data-related errors
        elif any(keyword in message_lower for keyword in ["data", "column", "row", "format", "parse", "csv", "excel"]):
            return WorkflowErrorType.DATA_ERROR
        
        # State management errors
        elif any(keyword in message_lower for keyword in ["state", "checkpoint", "persistence", "redis"]):
            return WorkflowErrorType.STATE_ERROR
        
        # Validation errors
        elif any(keyword in message_lower for keyword in ["validation", "invalid", "missing", "required"]):
            return WorkflowErrorType.VALIDATION_ERROR
        
        # Timeout errors
        elif any(keyword in message_lower for keyword in ["timeout", "time out", "deadline", "expired"]):
            return WorkflowErrorType.TIMEOUT_ERROR
        
        # Resource errors
        elif any(keyword in message_lower for keyword in ["memory", "disk", "storage", "resource"]):
            return WorkflowErrorType.RESOURCE_ERROR
        
        # Configuration errors
        elif any(keyword in message_lower for keyword in ["config", "configuration", "setup", "initialization"]):
            return WorkflowErrorType.CONFIGURATION_ERROR
        
        # Default to processing error
        else:
            return WorkflowErrorType.PROCESSING_ERROR
    
    def _assess_error_severity(self, error_type: WorkflowErrorType, message: str, error_data: Dict[str, Any]) -> ErrorSeverity:
        """Assess error severity based on type and impact."""
        message_lower = message.lower()
        
        # Fatal severity indicators
        if any(keyword in message_lower for keyword in ["fatal", "critical", "system failure", "crashed"]):
            return ErrorSeverity.FATAL
        
        # Error type based severity
        if error_type == WorkflowErrorType.STATE_ERROR:
            return ErrorSeverity.HIGH
        elif error_type == WorkflowErrorType.CONFIGURATION_ERROR:
            return ErrorSeverity.HIGH
        elif error_type == WorkflowErrorType.API_ERROR:
            # API errors can often be retried
            return ErrorSeverity.MEDIUM
        elif error_type == WorkflowErrorType.TIMEOUT_ERROR:
            return ErrorSeverity.MEDIUM
        elif error_type == WorkflowErrorType.VALIDATION_ERROR:
            return ErrorSeverity.HIGH
        elif error_type == WorkflowErrorType.DATA_ERROR:
            return ErrorSeverity.MEDIUM
        else:
            return ErrorSeverity.MEDIUM
    
    def _is_auto_recoverable(self, error: WorkflowError) -> bool:
        """Determine if an error can be automatically recovered."""
        # API errors with rate limiting can often be retried
        if error.error_type == WorkflowErrorType.API_ERROR and error.retry_count < 3:
            return True
        
        # Timeout errors can often be retried
        if error.error_type == WorkflowErrorType.TIMEOUT_ERROR and error.retry_count < 2:
            return True
        
        # Some processing errors can be retried
        if (error.error_type == WorkflowErrorType.PROCESSING_ERROR and 
            error.severity != ErrorSeverity.FATAL and error.retry_count < 1):
            return True
        
        return False
    
    def _get_recovery_options(self, error: WorkflowError) -> List[str]:
        """Get available recovery options for an error."""
        options = []
        
        if error.error_type == WorkflowErrorType.API_ERROR:
            options.extend([
                "Retry with exponential backoff",
                "Switch to fallback model",
                "Use cached results if available"
            ])
        
        elif error.error_type == WorkflowErrorType.DATA_ERROR:
            options.extend([
                "Apply data cleaning and retry",
                "Use subset of valid data",
                "Request user intervention"
            ])
        
        elif error.error_type == WorkflowErrorType.TIMEOUT_ERROR:
            options.extend([
                "Retry with increased timeout",
                "Process in smaller chunks",
                "Use simplified processing"
            ])
        
        elif error.error_type == WorkflowErrorType.STATE_ERROR:
            options.extend([
                "Reset to last valid checkpoint",
                "Reinitialize state management",
                "Continue without persistence"
            ])
        
        return options
    
    def _assess_error_impact(self, errors: List[WorkflowError], state: EnhancedWorkflowState) -> Dict[str, Any]:
        """Assess the overall impact of errors on workflow execution."""
        total_errors = len(errors)
        fatal_errors = len([e for e in errors if e.severity == ErrorSeverity.FATAL])
        critical_errors = len([e for e in errors if e.severity == ErrorSeverity.HIGH])
        medium_errors = len([e for e in errors if e.severity == ErrorSeverity.MEDIUM])
        low_errors = len([e for e in errors if e.severity == ErrorSeverity.LOW])
        
        # Calculate overall impact score
        impact_score = (
            fatal_errors * 1.0 +
            critical_errors * 0.7 +
            medium_errors * 0.4 +
            low_errors * 0.1
        ) / max(total_errors, 1)
        
        # Determine if workflow can continue
        can_continue = fatal_errors == 0 and critical_errors <= 2
        
        return {
            "total_errors": total_errors,
            "fatal_count": fatal_errors,
            "critical_count": critical_errors,
            "medium_count": medium_errors,
            "low_count": low_errors,
            "impact_score": round(impact_score, 3),
            "can_continue": can_continue,
            "quality_degradation": min(impact_score * 0.3, 0.5)  # Max 50% quality impact
        }
    
    async def _attempt_error_recovery(self, errors: List[WorkflowError], state: EnhancedWorkflowState) -> Dict[str, Any]:
        """Attempt automatic recovery for recoverable errors."""
        recovery_results = {
            "attempted_recoveries": 0,
            "successful_recoveries": 0,
            "failed_recoveries": 0,
            "recovery_details": []
        }
        
        for error in errors:
            if error.auto_recoverable:
                recovery_results["attempted_recoveries"] += 1
                
                try:
                    # Attempt recovery based on error type
                    recovery_success = await self._execute_error_recovery(error, state)
                    
                    if recovery_success:
                        recovery_results["successful_recoveries"] += 1
                        error.retry_count += 1
                        
                        recovery_results["recovery_details"].append({
                            "error_id": error.error_id,
                            "recovery_method": f"auto_recovery_{error.error_type.value}",
                            "success": True,
                            "timestamp": datetime.now().isoformat()
                        })
                        
                        logger.info(f"Successfully recovered from error: {error.error_id}")
                    else:
                        recovery_results["failed_recoveries"] += 1
                        recovery_results["recovery_details"].append({
                            "error_id": error.error_id,
                            "recovery_method": f"auto_recovery_{error.error_type.value}",
                            "success": False,
                            "timestamp": datetime.now().isoformat()
                        })
                        
                except Exception as recovery_exception:
                    recovery_results["failed_recoveries"] += 1
                    logger.error(f"Recovery attempt failed for error {error.error_id}: {recovery_exception}")
        
        return recovery_results
    
    async def _execute_error_recovery(self, error: WorkflowError, state: EnhancedWorkflowState) -> bool:
        """Execute specific recovery procedures based on error type."""
        
        if error.error_type == WorkflowErrorType.API_ERROR:
            # Wait and retry for API errors
            await asyncio.sleep(min(2 ** error.retry_count, 10))  # Exponential backoff, max 10s
            return True
        
        elif error.error_type == WorkflowErrorType.TIMEOUT_ERROR:
            # Increase timeout tolerance for timeout errors
            await asyncio.sleep(1)
            return True
        
        elif error.error_type == WorkflowErrorType.PROCESSING_ERROR:
            # Reset processing state for processing errors
            if "cleaned_data" in state and state["cleaned_data"]:
                return True  # Data is available for retry
        
        elif error.error_type == WorkflowErrorType.STATE_ERROR:
            # Attempt state recovery
            if self.state_manager:
                try:
                    # Try to load last valid checkpoint
                    checkpoint = await self.state_manager.load_checkpoint(state["workflow_id"])
                    return checkpoint is not None
                except Exception:
                    return False
        
        return False
    
    def _update_error_state(self, state: EnhancedWorkflowState, errors: List[WorkflowError], 
                          recovery_results: Dict[str, Any], error_assessment: Dict[str, Any]) -> EnhancedWorkflowState:
        """Update workflow state with error analysis and recovery results."""
        
        # Update error list with structured errors
        state["errors"] = [asdict(error) for error in errors]
        
        # Update quality scores based on error impact
        quality_degradation = error_assessment["quality_degradation"]
        for key in state["quality_scores"]:
            state["quality_scores"][key] = max(0.1, state["quality_scores"][key] - quality_degradation)
        
        # Update confidence scores
        confidence_impact = min(error_assessment["impact_score"] * 0.2, 0.4)
        for key in state["confidence_scores"]:
            state["confidence_scores"][key] = max(0.1, state["confidence_scores"][key] - confidence_impact)
        
        # Add recovery metadata
        state["processing_metadata"]["error_recovery"] = recovery_results
        
        return state
    
    def _determine_continuation_strategy(self, error_assessment: Dict[str, Any], 
                                       recovery_results: Dict[str, Any]) -> Dict[str, Any]:
        """Determine how the workflow should continue based on error analysis."""
        
        can_continue = error_assessment["can_continue"]
        successful_recoveries = recovery_results["successful_recoveries"]
        total_critical = error_assessment["critical_count"] + error_assessment["fatal_count"]
        
        if error_assessment["fatal_count"] > 0:
            return {
                "strategy": "terminate",
                "can_continue": False,
                "status": WorkflowStatus.FAILED.value,
                "reason": "Fatal errors detected - workflow termination required"
            }
        
        elif total_critical > 0 and successful_recoveries == 0:
            return {
                "strategy": "terminate_with_partial_results",
                "can_continue": False,
                "status": WorkflowStatus.COMPLETED.value,  # Partial completion
                "reason": "Critical errors without recovery - providing partial results"
            }
        
        elif error_assessment["impact_score"] > 0.7:
            return {
                "strategy": "continue_with_degraded_quality",
                "can_continue": True,
                "status": WorkflowStatus.RUNNING.value,
                "reason": "High error impact - continuing with quality warnings"
            }
        
        else:
            return {
                "strategy": "continue_normally",
                "can_continue": True,
                "status": WorkflowStatus.RUNNING.value,
                "reason": "Manageable errors - workflow can continue normally"
            }
    
    def _generate_error_insights(self, errors: List[WorkflowError], recovery_results: Dict[str, Any], 
                               error_assessment: Dict[str, Any]) -> Dict[str, List[str]]:
        """Generate insights and recommendations based on error analysis."""
        
        insights = []
        recommendations = []
        
        # Error summary insights
        total_errors = len(errors)
        if total_errors > 0:
            insights.append(f"Workflow encountered {total_errors} error(s) during processing")
            
            if recovery_results["successful_recoveries"] > 0:
                insights.append(f"Successfully recovered from {recovery_results['successful_recoveries']} error(s)")
        
        # Error type specific insights
        error_types = {}
        for error in errors:
            error_types[error.error_type.value] = error_types.get(error.error_type.value, 0) + 1
        
        for error_type, count in error_types.items():
            if count > 1:
                insights.append(f"Multiple {error_type} errors detected ({count} occurrences)")
        
        # Quality impact insights
        if error_assessment["quality_degradation"] > 0.2:
            insights.append(f"Data quality may be impacted due to processing errors")
            recommendations.append("Review error details and consider data source improvements")
        
        # Recovery recommendations
        if recovery_results["failed_recoveries"] > 0:
            recommendations.append("Some errors could not be automatically recovered - manual intervention may be needed")
        
        if error_assessment["critical_count"] > 0:
            recommendations.append("Critical errors detected - review system configuration and data inputs")
        
        return {
            "insights": insights,
            "recommendations": recommendations
        }
    
    async def resume_workflow(self, workflow_id: str, checkpoint_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Resume a workflow from a checkpoint.
        
        Args:
            workflow_id: The workflow ID to resume
            checkpoint_id: Specific checkpoint ID, or None for latest
            
        Returns:
            Dictionary containing the workflow results
        """
        if not self.state_manager:
            return {
                "status": "error",
                "message": "State persistence not enabled. Cannot resume workflow.",
                "workflow_id": workflow_id
            }
        
        try:
            # Load state from checkpoint
            state = await self._load_checkpoint(workflow_id, checkpoint_id)
            if not state:
                return {
                    "status": "error",
                    "message": f"Checkpoint not found for workflow {workflow_id}",
                    "workflow_id": workflow_id
                }
            
            # Update workflow status
            state["workflow_status"] = WorkflowStatus.RUNNING.value
            state["updated_at"] = datetime.now().isoformat()
            
            logger.info(f"Resuming workflow {workflow_id} from step {state['current_step']}")
            
            # Execute from current state
            result = await self.workflow.ainvoke(state)
            
            # Return structured results
            return {
                "status": "success" if not result.get("errors") else "partial_success",
                "workflow_id": workflow_id,
                "resumed_from": state.get("last_checkpoint_id"),
                "workflow_state": result,
                "dashboard_config": result.get("dashboard_config"),
                "insights": result.get("insights", []),
                "recommendations": result.get("recommendations", []),
                "quality_scores": result.get("quality_scores", {}),
                "confidence_scores": result.get("confidence_scores", {}),
                "processing_history": result.get("processing_history", []),
                "errors": result.get("errors", []),
                "export_ready": result.get("export_ready", False)
            }
            
        except Exception as e:
            logger.error(f"Failed to resume workflow {workflow_id}: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "workflow_id": workflow_id
            }
    
    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """
        Get the current status of a workflow.
        
        Args:
            workflow_id: The workflow ID
            
        Returns:
            Dictionary containing workflow status information
        """
        if not self.state_manager:
            return {"status": "error", "message": "State persistence not enabled"}
        
        try:
            # Get latest checkpoint
            checkpoint = await self.state_manager.load_checkpoint(workflow_id)
            if not checkpoint:
                return {"status": "not_found", "workflow_id": workflow_id}
            
            state = checkpoint.state_data
            
            return {
                "status": "success",
                "workflow_id": workflow_id,
                "workflow_status": state.get("workflow_status"),
                "current_step": state.get("current_step"),
                "started_at": state.get("started_at"),
                "updated_at": state.get("updated_at"),
                "progress": self._calculate_workflow_progress(state),
                "errors": len(state.get("errors", [])),
                "can_rollback": state.get("can_rollback", False),
                "last_checkpoint": checkpoint.checkpoint_id,
                "available_checkpoints": await self.state_manager.list_checkpoints(workflow_id)
            }
            
        except Exception as e:
            logger.error(f"Failed to get workflow status: {e}")
            return {"status": "error", "message": str(e)}
    
    def _calculate_workflow_progress(self, state: EnhancedWorkflowState) -> Dict[str, Any]:
        """Calculate workflow progress percentage and statistics."""
        steps = [
            "initialize", "analyze_requirements", "intelligent_data_filtering",
            "data_cleaning", "quality_assessment", "enhanced_dashboard_generation",
            "finalize_results"
        ]
        
        current_step = state.get("current_step", "")
        try:
            current_index = steps.index(current_step)
            progress_percent = (current_index / len(steps)) * 100
        except ValueError:
            progress_percent = 0
        
        return {
            "percentage": progress_percent,
            "current_step": current_step,
            "total_steps": len(steps),
            "completed_steps": current_index if current_step in steps else 0,
            "estimated_remaining_time": self._estimate_remaining_time(state),
            "processing_time": self._calculate_total_processing_time(state)
        }
    
    def _estimate_remaining_time(self, state: EnhancedWorkflowState) -> float:
        """Estimate remaining processing time in seconds."""
        # Simple estimation based on average step duration
        history = state.get("processing_history", [])
        if len(history) < 2:
            return 0.0
        
        # Calculate average step duration
        total_time = 0.0
        step_count = 0
        
        for i in range(1, len(history)):
            try:
                start_time = datetime.fromisoformat(history[i-1]["timestamp"])
                end_time = datetime.fromisoformat(history[i]["timestamp"])
                step_duration = (end_time - start_time).total_seconds()
                total_time += step_duration
                step_count += 1
            except Exception:
                continue
        
        if step_count == 0:
            return 0.0
        
        avg_step_duration = total_time / step_count
        remaining_steps = 7 - len(history)  # Assuming 7 total steps
        
        return max(0.0, remaining_steps * avg_step_duration)
    
    def _calculate_total_processing_time(self, state: EnhancedWorkflowState) -> float:
        """Calculate total processing time so far."""
        started_at = state.get("started_at")
        updated_at = state.get("updated_at")
        
        if not started_at or not updated_at:
            return 0.0
        
        try:
            start_time = datetime.fromisoformat(started_at)
            end_time = datetime.fromisoformat(updated_at)
            return (end_time - start_time).total_seconds()
        except Exception:
            return 0.0
    
    async def execute_enhanced_workflow(self, 
                                      original_data: Dict[str, Any],
                                      file_info: Dict[str, Any],
                                      user_requirements: Optional[Dict[str, Any]] = None,
                                      workflow_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute the complete enhanced workflow with intelligent data filtering and OpenRouter integration.
        
        Args:
            original_data: The original dataset to process
            file_info: Information about the uploaded file
            user_requirements: Optional user requirements and preferences
            workflow_id: Optional workflow ID for tracking and resumption
            
        Returns:
            Dictionary containing the complete enhanced workflow results
        """
        # Generate or use provided workflow ID
        workflow_id = workflow_id or str(uuid.uuid4())
        current_time = datetime.now().isoformat()
        
        # Initialize enhanced state with full state management
        initial_state = EnhancedWorkflowState(
            # Workflow identification and state management
            workflow_id=workflow_id,
            workflow_status=WorkflowStatus.PENDING.value,
            started_at=current_time,
            updated_at=current_time,
            
            # Input data
            original_data=original_data,
            file_info=file_info,
            user_requirements=user_requirements or {},
            
            # Processing state
            current_step="",
            previous_step=None,
            processing_history=[],
            errors=[],
            
            # Enhanced data filtering
            data_filtering_result=None,
            filtered_data=None,
            
            # Processed data at each step
            cleaned_data=None,
            trend_analysis=None,
            forecast_data=None,
            visualization_config=None,
            
            # Enhanced pivot table analysis
            pivot_recommendations=[],
            generated_pivot_tables={},
            
            # Quality and metrics
            quality_scores={},
            confidence_scores={},
            accuracy_metrics={},
            
            # Final outputs
            dashboard_config=None,
            insights=[],
            recommendations=[],
            export_ready=False,
            
            # Workflow control
            next_nodes=[],
            should_continue=True,
            can_rollback=False,
            checkpoint_enabled=self.enable_state_persistence,
            
            # OpenRouter/LiteLLM integration
            model_provider="openrouter" if self.openrouter_config.is_available else "fallback",
            model_costs={},
            processing_metadata={},
            
            # State management metadata
            state_version=0,
            last_checkpoint_id=None,
            rollback_points=[]
        )
        
        try:
            # Execute the enhanced workflow
            result = await self.workflow.ainvoke(initial_state)
            
            # Return enhanced structured results
            return {
                "status": "success" if not result.get("errors") else "partial_success",
                "workflow_id": workflow_id,
                "workflow_state": result,
                "dashboard_config": result.get("dashboard_config"),
                "data_filtering_result": result.get("data_filtering_result"),
                "insights": result.get("insights", []),
                "recommendations": result.get("recommendations", []),
                "quality_scores": result.get("quality_scores", {}),
                "confidence_scores": result.get("confidence_scores", {}),
                "accuracy_metrics": result.get("accuracy_metrics", {}),
                "processing_history": result.get("processing_history", []),
                "errors": result.get("errors", []),
                "export_ready": result.get("export_ready", False),
                "openrouter_enabled": self.openrouter_config.is_available,
                "processing_metadata": result.get("processing_metadata", {})
            }
            
        except Exception as e:
            logger.error(f"Enhanced workflow execution failed: {str(e)}")
            return {
                "status": "error",
                "workflow_id": workflow_id,
                "message": str(e),
                "workflow_state": initial_state,
                "errors": [{"step": "workflow_execution", "error": str(e)}],
                "openrouter_enabled": self.openrouter_config.is_available
            }

    async def get_workflow_metadata(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive metadata for a workflow.
        
        Args:
            workflow_id: The workflow ID to get metadata for
            
        Returns:
            Complete metadata summary or None if not found
        """
        if not self.metadata_tracker or self.metadata_tracker.workflow_metadata.workflow_id != workflow_id:
            return None
        
        return self.metadata_tracker.get_comprehensive_metadata()

# Enhanced metadata tracking and logging system

@dataclass
class WorkflowMetadata:
    """Comprehensive workflow metadata schema."""
    workflow_id: str
    session_id: Optional[str]
    started_at: str
    updated_at: str
    version: str = "enhanced_v1.0"
    
    # Data source metadata
    data_source: Dict[str, Any] = field(default_factory=dict)
    
    # Processing metadata
    processing_steps: List[Dict[str, Any]] = field(default_factory=list)
    routing_decisions: List[Dict[str, Any]] = field(default_factory=list)
    transformations: List[Dict[str, Any]] = field(default_factory=list)
    
    # Quality metadata
    quality_metrics: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    
    # Error tracking
    errors: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[Dict[str, Any]] = field(default_factory=list)
    
    # Model and resource usage
    model_usage: Dict[str, Any] = field(default_factory=dict)
    resource_usage: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DataTransformation:
    """Schema for tracking data transformations."""
    transformation_id: str
    step: str
    transformation_type: str  # filtering, cleaning, enhancement, etc.
    timestamp: str
    
    # Input/Output tracking
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    transformation_params: Dict[str, Any]
    
    # Quality impact
    quality_impact: Dict[str, float]
    data_changes: Dict[str, Any]
    
    # Performance tracking
    execution_time: float
    memory_usage: Optional[int] = None
    
    @classmethod
    def create(cls, step: str, transformation_type: str, input_schema: Dict[str, Any], 
               output_schema: Dict[str, Any], transformation_params: Dict[str, Any] = None):
        """Create a new data transformation record."""
        return cls(
            transformation_id=f"{step}_{transformation_type}_{int(time.time())}",
            step=step,
            transformation_type=transformation_type,
            timestamp=datetime.now().isoformat(),
            input_schema=input_schema,
            output_schema=output_schema,
            transformation_params=transformation_params or {},
            quality_impact={},
            data_changes={},
            execution_time=0.0
        )

@dataclass
class RoutingDecision:
    """Schema for tracking intelligent routing decisions."""
    decision_id: str
    step: str
    decision_point: str
    timestamp: str
    
    # Decision context
    decision_factors: Dict[str, Any]
    available_routes: List[str]
    chosen_route: str
    reasoning: str
    
    # Decision confidence
    confidence_score: float
    risk_assessment: Dict[str, Any]
    
    # Impact tracking
    expected_impact: Dict[str, Any]
    actual_impact: Optional[Dict[str, Any]] = None
    
    @classmethod
    def create(cls, step: str, decision_point: str, decision_factors: Dict[str, Any],
               available_routes: List[str], chosen_route: str, reasoning: str, confidence_score: float):
        """Create a new routing decision record."""
        return cls(
            decision_id=f"{step}_{decision_point}_{int(time.time())}",
            step=step,
            decision_point=decision_point,
            timestamp=datetime.now().isoformat(),
            decision_factors=decision_factors,
            available_routes=available_routes,
            chosen_route=chosen_route,
            reasoning=reasoning,
            confidence_score=confidence_score,
            risk_assessment={},
            expected_impact={}
        )

class MetadataTracker:
    """Enhanced metadata tracking and logging system."""
    
    def __init__(self, workflow_id: str, session_id: Optional[str] = None):
        self.workflow_metadata = WorkflowMetadata(
            workflow_id=workflow_id,
            session_id=session_id,
            started_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        self.transformations: List[DataTransformation] = []
        self.routing_decisions: List[RoutingDecision] = []
        
    def track_data_source(self, file_info: Dict[str, Any], original_data: Dict[str, Any]):
        """Track metadata about the data source."""
        self.workflow_metadata.data_source = {
            "filename": file_info.get("filename"),
            "file_size": file_info.get("file_size", 0),
            "file_type": file_info.get("file_type"),
            "upload_timestamp": file_info.get("upload_timestamp"),
            "original_columns": len(original_data.get("columns", [])),
            "original_rows": len(next(iter(original_data.get("data", {}).values()), [])),
            "column_types": original_data.get("column_types", {}),
            "data_complexity": self._calculate_source_complexity(original_data)
        }
    
    def track_processing_step(self, step: str, status: str, details: Dict[str, Any] = None):
        """Track a processing step with metadata."""
        step_metadata = {
            "step": step,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "details": details or {},
            "sequence_number": len(self.workflow_metadata.processing_steps) + 1
        }
        self.workflow_metadata.processing_steps.append(step_metadata)
        self._update_timestamp()
    
    def track_transformation(self, transformation: DataTransformation):
        """Track a data transformation."""
        self.transformations.append(transformation)
        self.workflow_metadata.transformations.append({
            "transformation_id": transformation.transformation_id,
            "step": transformation.step,
            "type": transformation.transformation_type,
            "timestamp": transformation.timestamp,
            "quality_impact": transformation.quality_impact,
            "execution_time": transformation.execution_time
        })
        self._update_timestamp()
    
    def track_routing_decision(self, decision: RoutingDecision):
        """Track an intelligent routing decision."""
        self.routing_decisions.append(decision)
        self.workflow_metadata.routing_decisions.append({
            "decision_id": decision.decision_id,
            "step": decision.step,
            "decision_point": decision.decision_point,
            "chosen_route": decision.chosen_route,
            "confidence": decision.confidence_score,
            "timestamp": decision.timestamp
        })
        self._update_timestamp()
    
    def track_quality_metrics(self, step: str, metrics: Dict[str, float]):
        """Track quality metrics for a processing step."""
        if step not in self.workflow_metadata.quality_metrics:
            self.workflow_metadata.quality_metrics[step] = {}
        
        self.workflow_metadata.quality_metrics[step].update({
            **metrics,
            "timestamp": datetime.now().isoformat()
        })
        self._update_timestamp()
    
    def track_performance_metrics(self, step: str, execution_time: float, memory_usage: Optional[int] = None):
        """Track performance metrics for a processing step."""
        if step not in self.workflow_metadata.performance_metrics:
            self.workflow_metadata.performance_metrics[step] = {}
        
        self.workflow_metadata.performance_metrics[step].update({
            "execution_time": execution_time,
            "memory_usage": memory_usage,
            "timestamp": datetime.now().isoformat()
        })
        self._update_timestamp()
    
    def track_model_usage(self, model: str, operation: str, tokens_used: int, cost: float):
        """Track AI model usage and costs."""
        if "operations" not in self.workflow_metadata.model_usage:
            self.workflow_metadata.model_usage["operations"] = []
        
        self.workflow_metadata.model_usage["operations"].append({
            "model": model,
            "operation": operation,
            "tokens_used": tokens_used,
            "cost": cost,
            "timestamp": datetime.now().isoformat()
        })
        
        # Update totals
        if "totals" not in self.workflow_metadata.model_usage:
            self.workflow_metadata.model_usage["totals"] = {"total_tokens": 0, "total_cost": 0.0}
        
        self.workflow_metadata.model_usage["totals"]["total_tokens"] += tokens_used
        self.workflow_metadata.model_usage["totals"]["total_cost"] += cost
        self._update_timestamp()
    
    def track_error(self, step: str, error: Exception, severity: str = "medium"):
        """Track an error with context."""
        error_metadata = {
            "error_id": f"{step}_error_{int(time.time())}",
            "step": step,
            "error_type": type(error).__name__,
            "message": str(error),
            "severity": severity,
            "timestamp": datetime.now().isoformat(),
            "traceback": traceback.format_exc() if error else None
        }
        
        self.workflow_metadata.errors.append(error_metadata)
        self._update_timestamp()
    
    def track_warning(self, step: str, message: str, details: Dict[str, Any] = None):
        """Track a warning with context."""
        warning_metadata = {
            "warning_id": f"{step}_warning_{int(time.time())}",
            "step": step,
            "message": message,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        }
        
        self.workflow_metadata.warnings.append(warning_metadata)
        self._update_timestamp()
    
    def get_comprehensive_metadata(self) -> Dict[str, Any]:
        """Get complete metadata summary."""
        return {
            "workflow_metadata": asdict(self.workflow_metadata),
            "detailed_transformations": [asdict(t) for t in self.transformations],
            "detailed_routing_decisions": [asdict(r) for r in self.routing_decisions],
            "summary_statistics": self._generate_summary_statistics(),
            "data_lineage": self._generate_data_lineage(),
            "quality_evolution": self._generate_quality_evolution()
        }
    
    def _calculate_source_complexity(self, original_data: Dict[str, Any]) -> float:
        """Calculate complexity score for data source."""
        columns = len(original_data.get("columns", []))
        rows = len(next(iter(original_data.get("data", {}).values()), []))
        
        # Basic complexity calculation
        base_score = min(10.0, (columns * 0.2) + (rows / 1000))
        return round(base_score, 2)
    
    def _update_timestamp(self):
        """Update the workflow metadata timestamp."""
        self.workflow_metadata.updated_at = datetime.now().isoformat()
    
    def _generate_summary_statistics(self) -> Dict[str, Any]:
        """Generate summary statistics from tracked metadata."""
        total_transformations = len(self.transformations)
        total_routing_decisions = len(self.routing_decisions)
        total_errors = len(self.workflow_metadata.errors)
        total_warnings = len(self.workflow_metadata.warnings)
        
        # Calculate total processing time
        total_processing_time = sum(
            t.execution_time for t in self.transformations
        )
        
        # Calculate average quality scores
        quality_scores = []
        for step_metrics in self.workflow_metadata.quality_metrics.values():
            if isinstance(step_metrics, dict):
                for key, value in step_metrics.items():
                    if isinstance(value, (int, float)) and key != "timestamp":
                        quality_scores.append(value)
        
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
        
        return {
            "total_transformations": total_transformations,
            "total_routing_decisions": total_routing_decisions,
            "total_errors": total_errors,
            "total_warnings": total_warnings,
            "total_processing_time": round(total_processing_time, 3),
            "average_quality_score": round(avg_quality, 3),
            "workflow_duration": self._calculate_workflow_duration(),
            "success_rate": self._calculate_success_rate()
        }
    
    def _generate_data_lineage(self) -> List[Dict[str, Any]]:
        """Generate data lineage tracking."""
        lineage = []
        
        for transformation in self.transformations:
            lineage.append({
                "step": transformation.step,
                "transformation_type": transformation.transformation_type,
                "input_columns": len(transformation.input_schema.get("columns", [])),
                "output_columns": len(transformation.output_schema.get("columns", [])),
                "data_changes": transformation.data_changes,
                "timestamp": transformation.timestamp
            })
        
        return lineage
    
    def _generate_quality_evolution(self) -> List[Dict[str, Any]]:
        """Generate quality evolution over processing steps."""
        evolution = []
        
        for step, metrics in self.workflow_metadata.quality_metrics.items():
            if isinstance(metrics, dict):
                quality_point = {
                    "step": step,
                    "timestamp": metrics.get("timestamp"),
                    "quality_scores": {k: v for k, v in metrics.items() 
                                     if isinstance(v, (int, float)) and k != "timestamp"}
                }
                evolution.append(quality_point)
        
        return sorted(evolution, key=lambda x: x.get("timestamp", ""))
    
    def _calculate_workflow_duration(self) -> float:
        """Calculate total workflow duration in seconds."""
        try:
            start_time = datetime.fromisoformat(self.workflow_metadata.started_at)
            end_time = datetime.fromisoformat(self.workflow_metadata.updated_at)
            return (end_time - start_time).total_seconds()
        except Exception:
            return 0.0
    
    def _calculate_success_rate(self) -> float:
        """Calculate workflow success rate based on errors."""
        total_operations = len(self.workflow_metadata.processing_steps)
        error_count = len(self.workflow_metadata.errors)
        
        if total_operations == 0:
            return 0.0
        
        return round((total_operations - error_count) / total_operations, 3)

# Enhanced Accuracy Scoring System

@dataclass 
class AccuracyMetrics:
    """Comprehensive accuracy metrics for workflow evaluation."""
    workflow_id: str
    timestamp: str
    
    # Data quality metrics (0-1 scale)
    data_completeness: float
    data_consistency: float  
    data_accuracy: float
    data_validity: float
    
    # Processing accuracy metrics (0-1 scale)
    filtering_accuracy: float
    cleaning_effectiveness: float
    transformation_accuracy: float
    
    # Dashboard generation metrics (0-1 scale)
    chart_relevance: float
    insight_quality: float
    layout_optimization: float
    
    # Performance metrics
    processing_efficiency: float
    resource_utilization: float
    error_rate: float
    
    # Overall scores
    data_quality_score: float
    processing_score: float
    output_quality_score: float
    overall_accuracy_score: float
    
    # Confidence intervals
    confidence_level: float = 0.95
    score_confidence_interval: tuple = (0.0, 1.0)
    
    @classmethod
    def calculate(cls, workflow_state: Dict[str, Any], metadata_tracker: Optional[MetadataTracker] = None):
        """Calculate comprehensive accuracy metrics from workflow state and metadata."""
        workflow_id = workflow_state.get("workflow_id", "unknown")
        timestamp = datetime.now().isoformat()
        
        # Data quality metrics
        data_quality = cls._calculate_data_quality_metrics(workflow_state)
        
        # Processing accuracy metrics
        processing_accuracy = cls._calculate_processing_accuracy_metrics(workflow_state, metadata_tracker)
        
        # Dashboard generation metrics
        dashboard_quality = cls._calculate_dashboard_quality_metrics(workflow_state)
        
        # Performance metrics
        performance = cls._calculate_performance_metrics(workflow_state, metadata_tracker)
        
        # Calculate composite scores
        data_quality_score = (
            data_quality["completeness"] * 0.3 +
            data_quality["consistency"] * 0.25 +
            data_quality["accuracy"] * 0.25 +
            data_quality["validity"] * 0.2
        )
        
        processing_score = (
            processing_accuracy["filtering"] * 0.4 +
            processing_accuracy["cleaning"] * 0.35 +
            processing_accuracy["transformation"] * 0.25
        )
        
        output_quality_score = (
            dashboard_quality["chart_relevance"] * 0.4 +
            dashboard_quality["insight_quality"] * 0.35 +
            dashboard_quality["layout_optimization"] * 0.25
        )
        
        # Overall accuracy score with weighted components
        overall_accuracy_score = (
            data_quality_score * 0.3 +
            processing_score * 0.4 +
            output_quality_score * 0.3
        )
        
        # Calculate confidence interval
        confidence_interval = cls._calculate_confidence_interval(
            overall_accuracy_score, workflow_state, metadata_tracker
        )
        
        return cls(
            workflow_id=workflow_id,
            timestamp=timestamp,
            data_completeness=data_quality["completeness"],
            data_consistency=data_quality["consistency"],
            data_accuracy=data_quality["accuracy"],
            data_validity=data_quality["validity"],
            filtering_accuracy=processing_accuracy["filtering"],
            cleaning_effectiveness=processing_accuracy["cleaning"],
            transformation_accuracy=processing_accuracy["transformation"],
            chart_relevance=dashboard_quality["chart_relevance"],
            insight_quality=dashboard_quality["insight_quality"],
            layout_optimization=dashboard_quality["layout_optimization"],
            processing_efficiency=performance["efficiency"],
            resource_utilization=performance["resource_utilization"],
            error_rate=performance["error_rate"],
            data_quality_score=data_quality_score,
            processing_score=processing_score,
            output_quality_score=output_quality_score,
            overall_accuracy_score=overall_accuracy_score,
            score_confidence_interval=confidence_interval
        )
    
    @staticmethod
    def _calculate_data_quality_metrics(workflow_state: Dict[str, Any]) -> Dict[str, float]:
        """Calculate data quality metrics."""
        original_data = workflow_state.get("original_data", {})
        cleaned_data = workflow_state.get("cleaned_data", {})
        quality_scores = workflow_state.get("quality_scores", {})
        
        # Data completeness (ratio of non-null values)
        completeness = 0.8  # Default baseline
        if cleaned_data and "cleaning_summary" in cleaned_data:
            summary = cleaned_data["cleaning_summary"]
            null_ratio = summary.get("null_ratio", 0.2)
            completeness = max(0.0, 1.0 - null_ratio)
        
        # Data consistency (based on cleaning improvements)
        consistency = quality_scores.get("cleaned", 7.0) / 10.0
        
        # Data accuracy (based on validation and outlier detection)
        accuracy = 0.8  # Default baseline
        if cleaned_data and "outlier_detection" in cleaned_data:
            outlier_ratio = cleaned_data["outlier_detection"].get("outlier_ratio", 0.1)
            accuracy = max(0.0, 1.0 - outlier_ratio * 2)  # Outliers reduce accuracy
        
        # Data validity (based on type consistency and format validation)
        validity = 0.85  # Default baseline
        if "column_types" in original_data:
            # Higher validity if column types are properly identified
            validity = 0.9
        
        return {
            "completeness": round(completeness, 3),
            "consistency": round(consistency, 3),
            "accuracy": round(accuracy, 3),
            "validity": round(validity, 3)
        }
    
    @staticmethod
    def _calculate_processing_accuracy_metrics(workflow_state: Dict[str, Any], 
                                             metadata_tracker: Optional[MetadataTracker] = None) -> Dict[str, float]:
        """Calculate processing accuracy metrics."""
        processing_history = workflow_state.get("processing_history", [])
        errors = workflow_state.get("errors", [])
        
        # Filtering accuracy (based on AI filtering results)
        filtering_accuracy = 0.8  # Default baseline
        filtering_result = workflow_state.get("data_filtering_result")
        if filtering_result:
            confidence = getattr(filtering_result, 'confidence', 0.8)
            filtering_accuracy = min(confidence, 1.0)
        
        # Cleaning effectiveness (based on quality improvement)
        cleaning_effectiveness = 0.75  # Default baseline
        quality_scores = workflow_state.get("quality_scores", {})
        if "cleaned" in quality_scores:
            cleaning_effectiveness = min(quality_scores["cleaned"] / 10.0, 1.0)
        
        # Transformation accuracy (based on successful transformations vs errors)
        transformation_accuracy = 0.8  # Default baseline
        if metadata_tracker:
            total_transformations = len(metadata_tracker.transformations)
            failed_transformations = len([t for t in metadata_tracker.transformations 
                                        if t.quality_impact.get("success", True) == False])
            if total_transformations > 0:
                transformation_accuracy = (total_transformations - failed_transformations) / total_transformations
        else:
            # Fallback: use error rate from processing history
            processing_steps = len([step for step in processing_history if step.get("status") == "completed"])
            error_steps = len([error for error in errors if error.get("step") in [
                "data_cleaning", "intelligent_data_filtering", "quality_assessment"
            ]])
            if processing_steps > 0:
                transformation_accuracy = max(0.0, (processing_steps - error_steps) / processing_steps)
        
        return {
            "filtering": round(filtering_accuracy, 3),
            "cleaning": round(cleaning_effectiveness, 3),
            "transformation": round(transformation_accuracy, 3)
        }
    
    @staticmethod
    def _calculate_dashboard_quality_metrics(workflow_state: Dict[str, Any]) -> Dict[str, float]:
        """Calculate dashboard generation quality metrics."""
        dashboard_config = workflow_state.get("dashboard_config", {})
        insights = workflow_state.get("insights", [])
        
        # Chart relevance (based on chart types and data appropriateness)
        chart_relevance = 0.7  # Default baseline
        charts = dashboard_config.get("charts", [])
        if charts:
            # Higher relevance if multiple chart types are generated
            chart_types = set(chart.get("type") for chart in charts)
            chart_relevance = min(0.6 + len(chart_types) * 0.1, 1.0)
            
            # Boost for confidence scores in charts
            avg_confidence = sum(chart.get("confidence", 0.7) for chart in charts) / len(charts)
            chart_relevance = (chart_relevance + avg_confidence) / 2
        
        # Insight quality (based on number and depth of insights generated)
        insight_quality = 0.6  # Default baseline
        if insights:
            # More insights generally indicate better analysis
            insight_quality = min(0.5 + len(insights) * 0.05, 0.95)
            
            # Quality boost for specific insight types
            quality_insights = [insight for insight in insights if any(keyword in insight.lower() 
                               for keyword in ["trend", "correlation", "pattern", "anomaly", "recommendation"])]
            if quality_insights:
                insight_quality = min(insight_quality + len(quality_insights) * 0.02, 1.0)
        
        # Layout optimization (based on dashboard structure and organization)
        layout_optimization = 0.75  # Default baseline
        if dashboard_config:
            # Check for good dashboard structure
            has_title = bool(dashboard_config.get("title"))
            has_metadata = bool(dashboard_config.get("metadata"))
            has_multiple_charts = len(charts) > 1
            
            optimization_score = 0.5
            if has_title: optimization_score += 0.15
            if has_metadata: optimization_score += 0.1
            if has_multiple_charts: optimization_score += 0.2
            if len(charts) > 3: optimization_score += 0.05  # Bonus for comprehensive dashboards
            
            layout_optimization = min(optimization_score, 1.0)
        
        return {
            "chart_relevance": round(chart_relevance, 3),
            "insight_quality": round(insight_quality, 3),
            "layout_optimization": round(layout_optimization, 3)
        }
    
    @staticmethod
    def _calculate_performance_metrics(workflow_state: Dict[str, Any], 
                                     metadata_tracker: Optional[MetadataTracker] = None) -> Dict[str, float]:
        """Calculate performance metrics."""
        processing_history = workflow_state.get("processing_history", [])
        errors = workflow_state.get("errors", [])
        
        # Processing efficiency (based on execution time vs. data complexity)
        efficiency = 0.8  # Default baseline
        if metadata_tracker:
            total_time = sum(t.execution_time for t in metadata_tracker.transformations)
            data_complexity = metadata_tracker.workflow_metadata.data_source.get("data_complexity", 5.0)
            
            # Expected time based on complexity (simple heuristic)
            expected_time = data_complexity * 2.0  # 2 seconds per complexity point
            if total_time > 0 and expected_time > 0:
                efficiency = min(expected_time / total_time, 1.0)
        
        # Resource utilization (placeholder - would need actual resource monitoring)
        resource_utilization = 0.75  # Default baseline
        
        # Error rate (based on errors vs successful operations)
        error_rate = 0.0
        total_operations = len(processing_history)
        total_errors = len(errors)
        if total_operations > 0:
            error_rate = total_errors / total_operations
        
        return {
            "efficiency": round(efficiency, 3),
            "resource_utilization": round(resource_utilization, 3),
            "error_rate": round(error_rate, 3)
        }
    
    @staticmethod
    def _calculate_confidence_interval(overall_score: float, workflow_state: Dict[str, Any], 
                                     metadata_tracker: Optional[MetadataTracker] = None) -> tuple:
        """Calculate confidence interval for the overall accuracy score."""
        # Simple confidence interval calculation based on data quality and error metrics
        base_confidence = 0.1  # Base uncertainty
        
        # Factors that affect confidence
        errors = workflow_state.get("errors", [])
        processing_steps = len(workflow_state.get("processing_history", []))
        
        # More errors reduce confidence
        error_penalty = len(errors) * 0.02
        
        # More processing steps generally increase confidence (more validation)
        step_bonus = min(processing_steps * 0.005, 0.03)
        
        # Metadata availability increases confidence
        metadata_bonus = 0.02 if metadata_tracker else 0.0
        
        confidence_margin = max(0.05, base_confidence + error_penalty - step_bonus - metadata_bonus)
        
        lower_bound = max(0.0, overall_score - confidence_margin)
        upper_bound = min(1.0, overall_score + confidence_margin)
        
        return (round(lower_bound, 3), round(upper_bound, 3))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary format."""
        return asdict(self)
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate a comprehensive performance report."""
        return {
            "summary": {
                "overall_accuracy": self.overall_accuracy_score,
                "confidence_interval": self.score_confidence_interval,
                "timestamp": self.timestamp
            },
            "component_scores": {
                "data_quality": {
                    "overall": self.data_quality_score,
                    "completeness": self.data_completeness,
                    "consistency": self.data_consistency,
                    "accuracy": self.data_accuracy,
                    "validity": self.data_validity
                },
                "processing": {
                    "overall": self.processing_score,
                    "filtering_accuracy": self.filtering_accuracy,
                    "cleaning_effectiveness": self.cleaning_effectiveness,
                    "transformation_accuracy": self.transformation_accuracy
                },
                "output_quality": {
                    "overall": self.output_quality_score,
                    "chart_relevance": self.chart_relevance,
                    "insight_quality": self.insight_quality,
                    "layout_optimization": self.layout_optimization
                }
            },
            "performance": {
                "processing_efficiency": self.processing_efficiency,
                "resource_utilization": self.resource_utilization,
                "error_rate": self.error_rate
            },
            "recommendations": self._generate_recommendations()
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on accuracy metrics."""
        recommendations = []
        
        if self.data_completeness < 0.8:
            recommendations.append("Consider improving data completeness by addressing missing values")
        
        if self.data_consistency < 0.7:
            recommendations.append("Data consistency could be improved through better cleaning algorithms")
        
        if self.filtering_accuracy < 0.8:
            recommendations.append("AI filtering accuracy may benefit from refined business context")
        
        if self.cleaning_effectiveness < 0.7:
            recommendations.append("Data cleaning process could be enhanced with more sophisticated algorithms")
        
        if self.chart_relevance < 0.7:
            recommendations.append("Dashboard chart selection could be improved with better data analysis")
        
        if self.insight_quality < 0.6:
            recommendations.append("Insight generation could benefit from deeper analytical algorithms")
        
        if self.processing_efficiency < 0.6:
            recommendations.append("Processing efficiency could be improved through optimization")
        
        if self.error_rate > 0.1:
            recommendations.append("Error rate is high - consider improving error handling and validation")
        
        if not recommendations:
            recommendations.append("All metrics are performing well - continue current approach")
        
        return recommendations

class AccuracyScorer:
    """Main class for calculating and managing accuracy scores."""
    
    def __init__(self, metadata_tracker: Optional[MetadataTracker] = None):
        self.metadata_tracker = metadata_tracker
        self.score_history: List[AccuracyMetrics] = []
    
    def calculate_accuracy_scores(self, workflow_state: Dict[str, Any]) -> AccuracyMetrics:
        """Calculate comprehensive accuracy scores for a workflow."""
        metrics = AccuracyMetrics.calculate(workflow_state, self.metadata_tracker)
        self.score_history.append(metrics)
        
        # Log metrics if metadata tracker is available
        if self.metadata_tracker:
            self.metadata_tracker.track_quality_metrics("accuracy_scoring", {
                "overall_accuracy": metrics.overall_accuracy_score,
                "data_quality": metrics.data_quality_score,
                "processing_score": metrics.processing_score,
                "output_quality": metrics.output_quality_score
            })
        
        return metrics
    
    def get_score_trends(self) -> Dict[str, Any]:
        """Analyze score trends over time."""
        if len(self.score_history) < 2:
            return {"message": "Insufficient data for trend analysis"}
        
        recent_scores = self.score_history[-5:]  # Last 5 scores
        
        # Calculate trends
        overall_trend = self._calculate_trend([s.overall_accuracy_score for s in recent_scores])
        data_quality_trend = self._calculate_trend([s.data_quality_score for s in recent_scores])
        processing_trend = self._calculate_trend([s.processing_score for s in recent_scores])
        
        return {
            "trend_analysis": {
                "overall_accuracy_trend": overall_trend,
                "data_quality_trend": data_quality_trend,
                "processing_trend": processing_trend
            },
            "latest_score": recent_scores[-1].overall_accuracy_score,
            "average_score": sum(s.overall_accuracy_score for s in recent_scores) / len(recent_scores),
            "score_volatility": self._calculate_volatility([s.overall_accuracy_score for s in recent_scores])
        }
    
    def _calculate_trend(self, scores: List[float]) -> str:
        """Calculate trend direction from a list of scores."""
        if len(scores) < 2:
            return "insufficient_data"
        
        first_half = scores[:len(scores)//2]
        second_half = scores[len(scores)//2:]
        
        avg_first = sum(first_half) / len(first_half)
        avg_second = sum(second_half) / len(second_half)
        
        difference = avg_second - avg_first
        
        if abs(difference) < 0.05:
            return "stable"
        elif difference > 0:
            return "improving"
        else:
            return "declining"
    
    def _calculate_volatility(self, scores: List[float]) -> float:
        """Calculate score volatility (standard deviation)."""
        if len(scores) < 2:
            return 0.0
        
        avg = sum(scores) / len(scores)
        variance = sum((score - avg) ** 2 for score in scores) / len(scores)
        return round(variance ** 0.5, 3)
    
    def generate_accuracy_dashboard(self) -> Dict[str, Any]:
        """Generate a dashboard visualization for accuracy metrics."""
        if not self.score_history:
            return {"message": "No accuracy data available"}
        
        latest_metrics = self.score_history[-1]
        
        return {
            "title": "Workflow Accuracy Dashboard",
            "timestamp": latest_metrics.timestamp,
            "charts": [
                {
                    "type": "gauge",
                    "title": "Overall Accuracy Score",
                    "value": latest_metrics.overall_accuracy_score,
                    "max_value": 1.0,
                    "color_zones": [
                        {"min": 0.0, "max": 0.6, "color": "red"},
                        {"min": 0.6, "max": 0.8, "color": "yellow"},
                        {"min": 0.8, "max": 1.0, "color": "green"}
                    ]
                },
                {
                    "type": "bar",
                    "title": "Component Scores",
                    "data": {
                        "Data Quality": latest_metrics.data_quality_score,
                        "Processing": latest_metrics.processing_score,
                        "Output Quality": latest_metrics.output_quality_score
                    }
                },
                {
                    "type": "line",
                    "title": "Accuracy Trend",
                    "data": {
                        "timestamps": [m.timestamp for m in self.score_history[-10:]],
                        "scores": [m.overall_accuracy_score for m in self.score_history[-10:]]
                    }
                }
            ],
            "summary_stats": {
                "current_score": latest_metrics.overall_accuracy_score,
                "confidence_interval": latest_metrics.score_confidence_interval,
                "trend": self.get_score_trends().get("trend_analysis", {}).get("overall_accuracy_trend", "unknown")
            },
            "recommendations": latest_metrics._generate_recommendations()
        }