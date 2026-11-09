"""
Chat router for conversational analytics.
Provides endpoints for AI-guided analytics configuration through chat interface.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse, ORJSONResponse
from pydantic import BaseModel
from typing import Dict, List, Any, Optional, Union, cast
import pandas as pd
import logging
import traceback
import json
import io
from datetime import datetime, timezone
import uuid
import numpy as np

from src.services.conversational_analytics_agent import ConversationalAnalyticsAgent, DataAnalysis, UserPreference
from src.services.enhanced_analytics_engine import EnhancedAnalyticsEngine

# Removed safe_log_message function - using plain text logging only

def make_json_serializable(obj: Any) -> Any:
    """Convert objects to JSON serializable format."""
    if isinstance(obj, (dict, list)):
        if isinstance(obj, dict):
            return {k: make_json_serializable(v) for k, v in obj.items()}
        else:
            return [make_json_serializable(item) for item in obj]
    elif hasattr(obj, '__dict__'):
        return make_json_serializable(obj.__dict__)
    elif isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    else:
        return str(obj)

# Create router
router = APIRouter(prefix="/chat", tags=["chat"])
logger = logging.getLogger(__name__)

# Store active chat sessions (in production, use Redis or similar)
active_sessions: Dict[str, Dict[str, Any]] = {}

# Pydantic models for request/response
class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: Dict[str, Any]
    conversation_history: List[Dict[str, Any]]
    phase: str
    preferences_detected: Dict[str, Any] = {}
    next_question: Optional[str] = None
    suggestion: Optional[str] = None

class CustomAnalyticsRequest(BaseModel):
    session_id: Optional[str] = None

class SessionResetRequest(BaseModel):
    session_id: Optional[str] = None

@router.post("/start-chat")
async def start_chat_session(file: UploadFile = File(...)):
    """Start a new chat session after data upload."""
    logger.info("[CHAT] Starting new chat session")
    try:
        # Validate file
        if not file or not file.filename:
            logger.error("[CHAT] No file provided or filename missing")
            raise HTTPException(status_code=400, detail="No file selected")
            
        logger.info(f"[CHAT] Processing file: {file.filename}")
        
        # Read the uploaded file
        contents = await file.read()
        logger.info(f"[CHAT] File read successfully, size: {len(contents)} bytes")
        
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
        elif file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(io.BytesIO(contents))
        else:
            logger.error(f"[CHAT] Unsupported file format: {file.filename}")
            raise HTTPException(status_code=400, detail="Unsupported file format. Please upload CSV or Excel files.")
            
        logger.info(f"[CHAT] DataFrame created: {df.shape[0]} rows, {df.shape[1]} columns")
        
        # Create new chat agent
        agent = ConversationalAnalyticsAgent()
        logger.info("[CHAT] ConversationalAnalyticsAgent created")
        
        # Store the original dataframe in the agent for dashboard generation
        agent.set_original_dataframe(df)
        
        # Analyze the data
        logger.info("[CHAT] Starting data analysis...")
        data_analysis = await agent.analyze_uploaded_data(df, file.filename)
        logger.info("[CHAT] Data analysis completed")
        
        # Generate initial questions
        logger.info("[CHAT] Generating initial questions...")
        initial_questions = await agent.get_initial_questions()
        logger.info(f"[CHAT] Generated {len(initial_questions)} initial questions")
        
        # Store session
        session_id = str(uuid.uuid4())
        active_sessions[session_id] = {
            'agent': agent,
            'dataframe': df,
            'filename': file.filename,
            'created_at': datetime.now()
        }
        logger.info(f"[CHAT] Session created with ID: {session_id}")
        
        result = {
            "session_id": session_id,
            "data_analysis": {
                "data_type": data_analysis.data_type,
                "data_summary": data_analysis.data_summary,
                "key_metrics": data_analysis.key_metrics,
                "potential_insights": data_analysis.potential_insights,
                "recommended_chart_types": data_analysis.recommended_chart_types,
                "data_quality_score": data_analysis.data_quality_score
            },
            "initial_questions": initial_questions,
            "conversation_history": agent.get_conversation_history(),
            "phase": agent.get_current_phase()
        }
        
        logger.info("[CHAT] Chat session started successfully")
        return result
        
    except Exception as e:
        logger.error(f"[CHAT] Error starting chat session: {str(e)}")
        logger.error(f"[CHAT] Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to start chat session: {str(e)}")

@router.post("/send-message")
async def send_message(chat_message: ChatMessage):
    """Send a message to the chat agent."""
    logger.info(f"[CHAT] Received message: {chat_message.message[:100]}...")
    try:
        if not chat_message.message:
            logger.error("[CHAT] Empty message received")
            raise HTTPException(status_code=400, detail="Message is required")
            
        session_id = chat_message.session_id
        logger.info(f"[CHAT] Session ID: {session_id}")
        
        if not session_id or session_id not in active_sessions:
            logger.error(f"[CHAT] Invalid session ID: {session_id}")
            logger.error(f"[CHAT] Active sessions: {list(active_sessions.keys())}")
            raise HTTPException(status_code=400, detail="Invalid or expired chat session")
            
        agent = active_sessions[session_id]['agent']
        logger.info("[CHAT] Agent retrieved, processing user response...")
        
        # Process user response
        response = await agent.process_user_response(chat_message.message)
        logger.info(f"[CHAT] Response processed: {str(response)[:500]}...")
        
        # Check if dashboard was generated during conversation
        if response.get("dashboard_generated"):
            logger.info("[CHAT] Dashboard was generated during conversation")
            
            # Extract dashboard data from the result
            dashboard_result = response.get("dashboard_result", {})
            dashboard_data = None
            
            if dashboard_result.get("success") and dashboard_result.get("dashboard_data"):
                dashboard_data = dashboard_result["dashboard_data"]
                logger.info(f"[CHAT] Dashboard data extracted: {len(dashboard_data.get('charts', []))} charts, {len(dashboard_data.get('kpis', []))} KPIs")
            else:
                logger.warning("[CHAT] Dashboard generation completed but no dashboard data found")
            
            try:
                content = {
                    "success": True,
                    "dashboard_generated": True,
                    "dashboard_id": str(uuid.uuid4()),  # Generate dashboard ID for frontend
                    "dashboard_data": make_json_serializable(dashboard_data) if dashboard_data else None,
                    "response": response.get("response", "Dashboard generated successfully!"),
                    "conversation_history": make_json_serializable(agent.get_conversation_history()),
                    "phase": agent.get_current_phase(),
                    "preferences_detected": response.get("preferences_detected", {}),
                    "next_question": response.get("next_question"),
                    "suggestion": response.get("suggestion"),
                    "generated_at": datetime.now(timezone.utc).isoformat()
                }
                return ORJSONResponse(content=content)
            except Exception as serialization_error:
                logger.error(f"[CHAT] Error serializing dashboard response: {str(serialization_error)}")
                logger.error(f"[CHAT] Serialization traceback: {traceback.format_exc()}")
                # Return a simplified response instead of failing completely
                return ORJSONResponse(content={
                    "success": True,
                    "dashboard_generated": True,
                    "dashboard_id": str(uuid.uuid4()),
                    "response": "Dashboard generated successfully, but some details could not be serialized.",
                    "phase": agent.get_current_phase(),
                    "generated_at": datetime.now(timezone.utc).isoformat()
                })
        
        try:
            result = ChatResponse(
                response=response,
                conversation_history=make_json_serializable(agent.get_conversation_history()),
                phase=agent.get_current_phase(),
                preferences_detected=response.get("preferences_detected", {}),
                next_question=response.get("next_question"),
                suggestion=response.get("suggestion")
            )
            
            logger.info("[CHAT] Message processed successfully")
            return result
        except Exception as response_error:
            logger.error(f"[CHAT] Error creating ChatResponse: {str(response_error)}")
            logger.error(f"[CHAT] Response error traceback: {traceback.format_exc()}")
            # Return a simpler response structure
            return {
                "response": response,
                "conversation_history": make_json_serializable(agent.get_conversation_history()),
                "phase": agent.get_current_phase(),
                "preferences_detected": response.get("preferences_detected", {}),
                "next_question": response.get("next_question"),
                "suggestion": response.get("suggestion")
            }
        
    except Exception as e:
        logger.error(f"[CHAT] Error processing message: {str(e)}")
        logger.error(f"[CHAT] Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to process message: {str(e)}")

@router.post("/generate-dashboard")
async def generate_dashboard_from_chat(request: CustomAnalyticsRequest):
    """Generate dashboard based on chat conversation."""
    try:
        session_id = request.session_id
        
        if not session_id or session_id not in active_sessions:
            raise HTTPException(status_code=400, detail="Invalid or expired chat session")
            
        agent = active_sessions[session_id]['agent']
        
        # Generate dashboard using the conversation context
        dashboard_result = await agent.generate_dashboard_from_conversation()
        
        if dashboard_result["success"]:
            return {
                "success": True,
                "dashboard_id": str(uuid.uuid4()),  # Generate a dashboard ID
                "dashboard_data": dashboard_result["dashboard_data"],
                "response": dashboard_result["response"],
                "conversation_history": dashboard_result["conversation_history"],
                "phase": dashboard_result["phase"]
            }
        else:
            raise HTTPException(status_code=500, detail=dashboard_result["error"])
        
    except Exception as e:
        logger.error(f"Error generating dashboard from chat: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to generate dashboard: {str(e)}")

@router.post("/generate-custom-analytics")
async def generate_custom_analytics(request: CustomAnalyticsRequest):
    """Generate custom analytics based on user preferences gathered from chat."""
    try:
        session_id = request.session_id
        
        if not session_id or session_id not in active_sessions:
            raise HTTPException(status_code=400, detail="Invalid or expired chat session")
            
        session_data = active_sessions[session_id]
        agent = session_data['agent']
        df = session_data['dataframe']
        filename = session_data['filename']
        
        # Compile user preferences from conversation
        user_preferences = agent.compile_user_preferences()
        
        # Create enhanced analytics engine with user preferences
        analytics_engine = EnhancedAnalyticsEngine()
        
        # Generate custom analytics based on preferences
        analytics_results = await generate_custom_analytics_with_preferences(
            analytics_engine, df, user_preferences, agent.data_analysis
        )
        
        # Update phase to generation complete
        agent.current_phase = "generation"
        agent._add_message(
            role="agent",
            content="Perfect! I've generated your custom analytics based on our conversation. Your visualizations are ready!",
            message_type="completion"
        )
        
        return {
            "analytics": analytics_results,
            "user_preferences": {
                "preferred_chart_types": user_preferences.preferred_chart_types,
                "key_metrics_to_focus": user_preferences.key_metrics_to_focus,
                "data_granularity": user_preferences.data_granularity,
                "visualization_style": user_preferences.visualization_style,
                "specific_questions": user_preferences.specific_questions
            },
            "conversation_summary": agent.get_conversation_history(),
            "phase": agent.get_current_phase()
        }
        
    except Exception as e:
        logger.error(f"Error generating custom analytics: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to generate analytics: {str(e)}")

@router.get("/get-conversation")
async def get_conversation(session_id: str):
    """Get current conversation history."""
    try:
        if not session_id or session_id not in active_sessions:
            raise HTTPException(status_code=400, detail="Invalid or expired chat session")
            
        agent = active_sessions[session_id]['agent']
        
        return {
            "conversation_history": agent.get_conversation_history(),
            "phase": agent.get_current_phase(),
            "data_analysis": agent.data_analysis.__dict__ if agent.data_analysis else None,
            "preferences": agent.user_preferences.__dict__ if agent.user_preferences else None
        }
        
    except Exception as e:
        logger.error(f"Error getting conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get conversation: {str(e)}")

@router.post("/reset-chat")
async def reset_chat(request: SessionResetRequest):
    """Reset chat session for new data upload."""
    try:
        session_id = request.session_id
        
        if session_id and session_id in active_sessions:
            # Reset the agent
            active_sessions[session_id]['agent'].reset_conversation()
            
            # Clear session data
            del active_sessions[session_id]
                
        return {"message": "Chat session reset successfully"}
        
    except Exception as e:
        logger.error(f"Error resetting chat: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to reset chat: {str(e)}")

# Helper functions
async def generate_custom_analytics_with_preferences(
    analytics_engine: EnhancedAnalyticsEngine, 
    df: pd.DataFrame, 
    preferences: UserPreference,
    data_analysis: DataAnalysis
) -> dict:
    """Generate analytics customized based on user preferences."""
    try:
        logger.info("[CUSTOM] Generating analytics with user preferences")
        
        # Filter metrics based on user preferences
        focused_columns = preferences.key_metrics_to_focus if preferences.key_metrics_to_focus else data_analysis.key_metrics
        
        # Apply data granularity filtering
        filtered_df = apply_granularity_filter(df, preferences.data_granularity, data_analysis.temporal_columns)
        
        # Generate KPIs focused on user's preferred metrics
        custom_kpis = await generate_custom_kpis(filtered_df, focused_columns, preferences.visualization_style)
        
        # Generate charts with preferred types
        custom_charts = await generate_custom_charts(
            filtered_df, 
            focused_columns, 
            preferences.preferred_chart_types,
            preferences.custom_legends
        )
        
        # Generate insights based on user's specific questions
        custom_insights = await generate_targeted_insights(
            filtered_df, 
            focused_columns, 
            preferences.specific_questions,
            data_analysis.data_type
        )
        
        return {
            "kpis": custom_kpis,
            "charts": custom_charts,
            "insights": custom_insights,
            "data_summary": {
                "total_records": len(filtered_df),
                "focused_metrics": focused_columns,
                "granularity": preferences.data_granularity,
                "chart_types_used": preferences.preferred_chart_types
            }
        }
        
    except Exception as e:
        logger.error(f"Error generating custom analytics: {str(e)}")
        raise

def apply_granularity_filter(df: pd.DataFrame, granularity: str, temporal_columns: list) -> pd.DataFrame:
    """Apply data granularity filtering based on user preference."""
    if granularity == "all" or not temporal_columns:
        return df
        
    # Find the best temporal column
    date_col = temporal_columns[0] if temporal_columns else None
    if not date_col:
        return df
        
    try:
        # Convert to datetime
        df[date_col] = pd.to_datetime(df[date_col])
        
        if granularity == "daily":
            # Keep all data (daily granularity)
            return df
        elif granularity == "weekly":
            # Group by week
            df['week'] = df[date_col].dt.to_period('W')
            return df.groupby('week').agg({col: 'sum' if pd.api.types.is_numeric_dtype(df[col]) else 'first' 
                                          for col in df.columns if col not in ['week', date_col]}).reset_index()
        elif granularity == "monthly":
            # Group by month
            df['month'] = df[date_col].dt.to_period('M')
            return df.groupby('month').agg({col: 'sum' if pd.api.types.is_numeric_dtype(df[col]) else 'first' 
                                           for col in df.columns if col not in ['month', date_col]}).reset_index()
    except:
        # If date conversion fails, return original dataframe
        return df
        
    return df

async def generate_custom_kpis(df: pd.DataFrame, focused_columns: list, style: str) -> list:
    """Generate KPIs focused on user's preferred metrics."""
    kpis = []
    
    for col in focused_columns[:4]:  # Limit to 4 main KPIs
        if col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
            col_data = df[col].dropna()
            
            if len(col_data) > 0:
                if style == "executive":
                    # Simple, high-level KPIs
                    kpi = {
                        "id": f"custom_kpi_{col}",
                        "title": col.replace('_', ' ').title(),
                        "value": f"{col_data.sum():,.0f}",
                        "subtitle": "Total",
                        "trend": "neutral",
                        "description": f"Total {col.replace('_', ' ').lower()}"
                    }
                else:
                    # Detailed KPIs
                    avg_val = col_data.mean()
                    total_val = col_data.sum()
                    
                    kpi = {
                        "id": f"custom_kpi_{col}",
                        "title": col.replace('_', ' ').title(),
                        "value": f"{total_val:,.0f}",
                        "subtitle": f"Avg: {avg_val:,.0f}",
                        "trend": "up" if len(col_data) > 1 and col_data.iloc[-1] > col_data.iloc[0] else "down",
                        "description": f"Total and average {col.replace('_', ' ').lower()}"
                    }
                
                kpis.append(kpi)
    
    return kpis

async def generate_custom_charts(df: pd.DataFrame, focused_columns: list, preferred_types: list, custom_legends: dict) -> list:
    """Generate charts with user's preferred types and custom legends."""
    charts = []
    
    for i, chart_type in enumerate(preferred_types[:3]):  # Limit to 3 charts
        if i < len(focused_columns):
            col = focused_columns[i]
            if col in df.columns:
                
                # Prepare chart data based on type
                if chart_type in ["line", "area"]:
                    # Time series chart
                    chart_data = prepare_time_series_data(df, col)
                elif chart_type in ["bar", "column"]:
                    # Bar chart
                    chart_data = prepare_bar_chart_data(df, col)
                elif chart_type in ["pie", "donut"]:
                    # Pie chart
                    chart_data = prepare_pie_chart_data(df, col)
                else:
                    # Default to bar chart
                    chart_data = prepare_bar_chart_data(df, col)
                
                # Apply custom legends if provided
                legend_name = custom_legends.get(col, col.replace('_', ' ').title())
                
                chart = {
                    "id": f"custom_chart_{i+1}",
                    "type": chart_type,
                    "title": f"{legend_name} Analysis",
                    "data": chart_data,
                    "config": {
                        "height": 400,
                        "legend": {"enabled": True, "name": legend_name},
                        "xAxis": {"name": "Period" if chart_type in ["line", "area"] else "Category"},
                        "yAxis": {"name": legend_name}
                    }
                }
                
                charts.append(chart)
    
    return charts

def prepare_time_series_data(df: pd.DataFrame, column: str) -> List[Dict[str, Union[str, float]]]:
    """Prepare data for time series charts with robust data cleaning."""
    data: List[Dict[str, Union[str, float]]] = []
    
    try:
        # Get the column data as a Series
        col_data = df[column].copy()
        
        # Ensure we have a pandas Series
        if not isinstance(col_data, pd.Series):
            col_data = pd.Series(col_data)
        
        # ENHANCED: Clean special characters from data before processing
        if not pd.api.types.is_numeric_dtype(col_data):
            # Clean common non-numeric characters that appear in data
            col_data = col_data.astype(str).replace({
                '—': '0',      # Em dash
                '–': '0',      # En dash  
                '-': '0',      # Regular dash (when used as placeholder)
                'nan': '0',
                'NaN': '0',
                'null': '0',
                'NULL': '0',
                '': '0',
                'None': '0'
            })
            
            # Convert to numeric, coercing errors to NaN
            col_data = pd.to_numeric(col_data, errors='coerce')
        
        # Ensure we still have a Series after operations
        if not isinstance(col_data, pd.Series):
            col_data = pd.Series(col_data)
            
        # Drop NaN values
        col_data = col_data.dropna()
        
        if len(col_data) == 0:
            return [{"x": "No Data", "y": 0.0}]
        
        # Create time series data points
        for i, value in enumerate(col_data):
            try:
                y_value = float(value) if not pd.isna(value) else 0.0
                
                # Handle infinite values
                if np.isinf(y_value):
                    y_value = 0.0
                    
                data.append({
                    "x": f"Period {i+1}",
                    "y": y_value
                })
            except (ValueError, TypeError) as e:
                logger.warning(f"Skipping invalid value in {column}: {value} - {str(e)}")
                continue
        
        if not data:
            return [{"x": "No Data", "y": 0.0}]
            
        return data[:50]  # Limit data points
        
    except Exception as e:
        logger.error(f"Error preparing time series data for {column}: {str(e)}")
        return [{"x": "Error", "y": 0.0}]

def prepare_bar_chart_data(df: pd.DataFrame, column: str) -> List[Dict[str, Union[str, float]]]:
    """Prepare data for bar charts with proper data cleaning."""
    try:
        if pd.api.types.is_numeric_dtype(df[column]):
            # Clean numeric data
            col_data = pd.to_numeric(df[column], errors='coerce')
            
            # Ensure we have a Series
            if not isinstance(col_data, pd.Series):
                col_data = pd.Series(col_data)
                
            col_data = col_data.dropna()
            
            if len(col_data) == 0:
                return [{"name": "No Data", "value": 0.0}]
            
            # Create quartile-based distribution
            try:
                # Use quantile on the Series
                q1, q2, q3, q4 = col_data.quantile([0.25, 0.5, 0.75, 1.0])
                
                data: List[Dict[str, Union[str, float]]] = []
                
                # Calculate sums using pandas operations
                data.append({"name": "Q1 (Low)", "value": float(col_data[col_data <= q1].sum())})
                data.append({"name": "Q2 (Med-Low)", "value": float(col_data[(col_data > q1) & (col_data <= q2)].sum())})
                data.append({"name": "Q3 (Med-High)", "value": float(col_data[(col_data > q2) & (col_data <= q3)].sum())})
                data.append({"name": "Q4 (High)", "value": float(col_data[col_data > q3].sum())})
                
                return data
            except Exception:
                # Fallback to simple sum
                return [{"name": "Total", "value": float(col_data.sum())}]
        else:
            # For categorical data, count values and clean
            col_data = df[column]
            
            # Ensure we have a Series
            if not isinstance(col_data, pd.Series):
                col_data = pd.Series(col_data)
                
            col_data = col_data.dropna()
            
            # Remove problematic characters
            col_data = col_data.astype(str).replace(['—', '–', '-', 'NaN', 'nan', ''], pd.NA).dropna()
            
            if len(col_data) == 0:
                return [{"name": "No Data", "value": 0.0}]
            
            value_counts = col_data.value_counts().head(10)
            return [{"name": str(k), "value": float(v)} for k, v in value_counts.items()]
            
    except Exception as e:
        logger.error(f"Error preparing bar chart data for column {column}: {str(e)}")
        return [{"name": "Error", "value": 0.0}]

def prepare_pie_chart_data(df: pd.DataFrame, column: str) -> List[Dict[str, Union[str, float]]]:
    """Prepare data for pie charts with proper data cleaning."""
    try:
        if pd.api.types.is_numeric_dtype(df[column]):
            # Clean numeric data and remove em dashes
            col_data = df[column].copy()
            
            # Ensure we have a Series
            if not isinstance(col_data, pd.Series):
                col_data = pd.Series(col_data)
            
            # Handle non-numeric strings that might be mixed in
            if not pd.api.types.is_numeric_dtype(col_data):
                col_data = col_data.astype(str).replace({
                    '—': '0',      # Em dash
                    '–': '0',      # En dash  
                    '-': '0',      # Regular dash (when used as placeholder)
                    'nan': '0',
                    'NaN': '0',
                    'null': '0',
                    'NULL': '0',
                    '': '0',
                    'None': '0'
                })
                col_data = pd.to_numeric(col_data, errors='coerce')
            
            # Ensure we still have a Series after conversion
            if not isinstance(col_data, pd.Series):
                col_data = pd.Series(col_data)
                
            col_data = col_data.dropna()
            
            if len(col_data) == 0:
                return [{"name": "No Data", "value": 0.0}]
            
            # For numeric data, create distribution
            try:
                # Use quantile on the Series
                q1, q2, q3 = col_data.quantile([0.33, 0.66, 1.0])
                
                return [
                    {"name": "Low", "value": float(col_data[col_data <= q1].sum())},
                    {"name": "Medium", "value": float(col_data[(col_data > q1) & (col_data <= q2)].sum())},
                    {"name": "High", "value": float(col_data[col_data > q2].sum())}
                ]
            except Exception:
                # Fallback to total
                return [{"name": "Total", "value": float(col_data.sum())}]
        else:
            # For categorical data, show top categories and clean
            col_data = df[column]
            
            # Ensure we have a Series
            if not isinstance(col_data, pd.Series):
                col_data = pd.Series(col_data)
                
            col_data = col_data.dropna()
            
            # Remove problematic characters
            col_data = col_data.astype(str).replace(['—', '–', '-', 'NaN', 'nan', ''], pd.NA).dropna()
            
            if len(col_data) == 0:
                return [{"name": "No Data", "value": 0.0}]
            
            value_counts = col_data.value_counts().head(5)
            return [{"name": str(k), "value": float(v)} for k, v in value_counts.items()]
            
    except Exception as e:
        logger.error(f"Error preparing pie chart data for column {column}: {str(e)}")
        return [{"name": "Error", "value": 0.0}]

async def generate_targeted_insights(
    df: pd.DataFrame, 
    focused_columns: List[str], 
    questions: List[str], 
    data_type: str
) -> List[Dict[str, Any]]:
    """Generate insights targeted to user's specific questions."""
    insights: List[Dict[str, Any]] = []
    
    # Generate generic insights for now (can be enhanced with LLM)
    if questions:
        for question in questions[:3]:
            insights.append({
                "title": "Custom Analysis",
                "description": f"Based on your question: '{question}', here are the key findings from your {data_type} data.",
                "metrics": focused_columns[:2],
                "recommendation": f"Focus on {focused_columns[0] if focused_columns else 'key metrics'} for better insights."
            })
    else:
        # Default insights
        insights.append({
            "title": f"{data_type.title()} Data Overview",
            "description": f"Your {data_type} data shows patterns across {len(focused_columns)} key metrics.",
            "metrics": focused_columns[:3],
            "recommendation": "Consider analyzing trends over time for better decision making."
        })
    
    return insights 