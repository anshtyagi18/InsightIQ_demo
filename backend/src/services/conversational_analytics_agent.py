import pandas as pd
import json
import logging
from typing import Dict, List, Any, Optional, Tuple, cast
from dataclasses import dataclass, asdict
from datetime import datetime, time, date
import asyncio
import numpy as np
try:
    from scipy import stats
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    logging.warning("scipy not available, some statistical features will be limited")

# JSON encoder for handling numpy types and other non-serializable objects
def convert_for_json(obj):
    """Convert numpy types and other non-serializable objects to JSON-compatible types."""
    # Handle None and NaN values first
    if obj is None:
        return None
    
    # Check for NaN values (works for both numpy and regular floats)
    try:
        if pd.isna(obj) or (isinstance(obj, (float, np.floating)) and (np.isnan(obj) or np.isinf(obj))):
            return None
    except (TypeError, ValueError):
        pass
    
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        # Double-check for NaN/inf after conversion
        val = float(obj)
        if np.isnan(val) or np.isinf(val):
            return None
        return val
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, np.ndarray):
        # Handle arrays by converting each element
        result = []
        for item in obj.flatten():
            result.append(convert_for_json(item))
        return result
    elif isinstance(obj, pd.Series):
        # Convert pandas Series to list, handling NaN values
        return [convert_for_json(item) for item in obj.tolist()]
    elif isinstance(obj, pd.DataFrame):
        # Convert DataFrame to records, filling NaN with None
        return obj.fillna(None).to_dict('records')
    elif isinstance(obj, (pd.Timestamp, datetime, np.datetime64)):
        # Convert timestamps to ISO format string
        try:
            if isinstance(obj, np.datetime64):
                obj = pd.Timestamp(obj)
            elif isinstance(obj, pd.Timestamp):
                return obj.isoformat()
            elif isinstance(obj, datetime):
                return obj.isoformat()
            return str(obj)
        except:
            return str(obj)
    elif isinstance(obj, (time, date)):
        # Convert time and date objects to string
        return str(obj)
    elif isinstance(obj, (list, tuple)):
        return [convert_for_json(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: convert_for_json(value) for key, value in obj.items()}
    elif hasattr(obj, 'dtype'):  # Handle pandas series/other numpy-based objects
        if 'int' in str(obj.dtype):
            return int(obj)
        elif 'float' in str(obj.dtype):
            val = float(obj)
            if np.isnan(val) or np.isinf(val):
                return None
            return val
        elif 'bool' in str(obj.dtype):
            return bool(obj)
        elif 'datetime' in str(obj.dtype):
            # Handle pandas datetime types
            try:
                return pd.Timestamp(obj).isoformat()
            except:
                return str(obj)
    
    # Handle pandas Timedelta objects
    if isinstance(obj, pd.Timedelta):
        return obj.total_seconds()
    
    # Handle any remaining pandas/numpy timestamp types
    if str(type(obj)).startswith('<class \'pandas._libs.tslibs.timestamps.Timestamp'):
        try:
            return obj.isoformat()
        except:
            return str(obj)
    
    return obj

@dataclass
class DataAnalysis:
    """Analysis of uploaded data structure and content."""
    data_type: str  # financial, sales, operational, etc.
    key_metrics: List[str]
    temporal_columns: List[str]
    categorical_columns: List[str]
    numerical_columns: List[str]
    data_quality_score: float
    potential_insights: List[str]
    recommended_chart_types: List[str]
    data_summary: str

@dataclass
class UserPreference:
    """User preferences for analytics generation."""
    preferred_chart_types: List[str]
    key_metrics_to_focus: List[str]
    custom_legends: Dict[str, str]
    data_granularity: str  # daily, weekly, monthly, all
    visualization_style: str  # minimal, detailed, executive
    specific_questions: List[str]
    color_preferences: Optional[str] = None

@dataclass
class ChatMessage:
    """Chat message structure."""
    role: str  # 'agent' or 'user'
    content: str
    timestamp: datetime
    message_type: str  # 'question', 'response', 'analysis', 'suggestion'
    data_context: Optional[Dict[str, Any]] = None

class ConversationalAnalyticsAgent:
    """AI agent that chats with users to understand their analytics preferences."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.conversation_history: List[ChatMessage] = []
        self.data_analysis: Optional[DataAnalysis] = None
        self.user_preferences: Optional[UserPreference] = None
        self.current_phase = "analysis"  # analysis, questioning, preference_gathering, generation
        
    async def analyze_uploaded_data(self, df: pd.DataFrame, filename: str) -> DataAnalysis:
        """Analyze the uploaded data to understand its structure and content."""
        try:
            self.logger.info(f"[ANALYSIS] Starting comprehensive data analysis for file: {filename}")
            
            # ENHANCED: Check if it's an Excel file with multiple sheets  
            sheet_analysis = {}
            # Note: For now, we'll focus on the main dataframe provided
            # Excel multi-sheet analysis can be added when file path is available
            
            # ENHANCED: Comprehensive column analysis
            column_analysis = await self._analyze_columns_comprehensive(df)
            
            # ENHANCED: Row pattern analysis  
            row_patterns = await self._analyze_row_patterns(df)
            
            # Basic data structure analysis (existing)
            numerical_columns = df.select_dtypes(include=['number']).columns.tolist()
            categorical_columns = df.select_dtypes(include=['object', 'category']).columns.tolist()
            temporal_columns = self._identify_temporal_columns(df)
            
            # Data quality assessment
            data_quality_score = self._calculate_data_quality(df)
            
            # ENHANCED: Identify data type and key metrics with AI assistance
            data_type, key_metrics = await self._identify_data_type_and_metrics_enhanced(df, filename, column_analysis)
            
            # ENHANCED: Generate comprehensive insights
            potential_insights = await self._generate_comprehensive_insights(df, data_type, column_analysis, row_patterns)
            
            # ENHANCED: AI-powered chart recommendations with reasoning
            recommended_chart_types = await self._recommend_chart_types_with_ai(df, data_type, column_analysis)
            
            # ENHANCED: Create detailed data summary
            data_summary = await self._create_enhanced_data_summary(df, data_type, key_metrics, column_analysis, sheet_analysis)
            
            # Convert all data to JSON-safe types before creating DataAnalysis
            self.data_analysis = DataAnalysis(
                data_type=str(data_type),
                key_metrics=convert_for_json(key_metrics),
                temporal_columns=convert_for_json(temporal_columns),
                categorical_columns=convert_for_json(categorical_columns),
                numerical_columns=convert_for_json(numerical_columns),
                data_quality_score=convert_for_json(data_quality_score),
                potential_insights=convert_for_json(potential_insights),
                recommended_chart_types=convert_for_json(recommended_chart_types),
                data_summary=str(data_summary)
            )
            
            # ENHANCED: Add comprehensive analysis message to conversation
            analysis_message = await self._create_comprehensive_analysis_message(
                df, data_summary, column_analysis, row_patterns, sheet_analysis
            )
            
            # Convert data context to JSON-safe types
            safe_data_context = convert_for_json({
                **asdict(self.data_analysis),
                "column_analysis": column_analysis,
                "row_patterns": row_patterns,
                "sheet_analysis": sheet_analysis
            })
            
            self._add_message(
                role="agent",
                content=analysis_message,
                message_type="analysis",
                data_context=safe_data_context
            )
            
            self.current_phase = "questioning"
            return self.data_analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing data: {str(e)}")
            raise
    
    def _identify_temporal_columns(self, df: pd.DataFrame) -> List[str]:
        """Identify columns that contain temporal data."""
        temporal_columns = []
        for col in df.columns:
            if any(keyword in str(col).lower() for keyword in ['date', 'time', 'year', 'month', 'day', 'created', 'updated']):
                temporal_columns.append(str(col))
            else:
                # Try to parse as datetime
                try:
                    pd.to_datetime(df[col].dropna().head(10))
                    temporal_columns.append(str(col))
                except:
                    continue
        return temporal_columns
    
    def _calculate_data_quality(self, df: pd.DataFrame) -> float:
        """Calculate data quality score (0-1)."""
        total_cells = df.size
        missing_cells = df.isnull().sum().sum()
        completeness = (total_cells - missing_cells) / total_cells
        
        # Additional quality checks
        duplicate_rows = df.duplicated().sum() / len(df)
        consistency_score = 1 - duplicate_rows
        
        return (completeness + consistency_score) / 2
    
    def _identify_data_type_and_metrics(self, df: pd.DataFrame, filename: str) -> Tuple[str, List[str]]:
        """Identify the type of data and key metrics."""
        filename_lower = filename.lower()
        columns_lower = [str(col).lower() for col in df.columns]
        
        # Financial data indicators
        financial_keywords = ['revenue', 'sales', 'profit', 'cost', 'amount', 'price', 'payment', 'invoice']
        # HR data indicators  
        hr_keywords = ['employee', 'salary', 'department', 'hire', 'performance', 'attendance']
        # Marketing data indicators
        marketing_keywords = ['campaign', 'clicks', 'impressions', 'conversion', 'roi', 'engagement']
        # Inventory/Operational data indicators
        inventory_keywords = ['stock', 'inventory', 'quantity', 'product', 'warehouse', 'supplier', 'units', 'total', 'vehicle', 'bus', 'transport', 'charging', 'soc']
        
        # Identify proper metrics (exclude identifier/serial columns)
        identifier_patterns = ['s.no', 's no', 'serial', 'index', 'row', 'id', 'key', 'ref', 'reference', 'number']
        
        # Strong metric indicators
        strong_metric_keywords = ['total', 'amount', 'value', 'sum', 'revenue', 'sales', 'profit', 'cost', 'price', 'units', 'quantity', 'count', 'score', 'rating', 'percentage', 'rate', 'volume', 'budget', 'target', 'actual', 'soc']
        
        # Find actual business metrics
        key_metrics = []
        for col in df.columns:
            col_lower = str(col).lower().replace(' ', '').replace('.', '').replace('-', '').replace('_', '')
            
            # Skip obvious identifier columns
            if any(pattern.replace(' ', '').replace('.', '') in col_lower for pattern in identifier_patterns):
                continue
                
            # Check for strong metric indicators
            if any(keyword in col_lower for keyword in strong_metric_keywords):
                key_metrics.append(col)
                continue
                
            # For numerical columns, check if they're meaningful metrics
            if col in df.select_dtypes(include=['number']).columns:
                # Skip if it looks like sequential numbering
                if df[col].nunique() == len(df) and df[col].min() == 1:
                    continue  # Likely serial number
                    
                unique_count = df[col].nunique()
                total_rows = len(df)
                
                # Skip if it's likely a sequential ID (unique values == row count and starts from 1)
                if unique_count == total_rows and df[col].min() == 1:
                    continue  # Likely a serial number
                    
                # Skip if it's almost all unique values (likely an ID)
                if unique_count > total_rows * 0.9:
                    continue  # Likely an identifier
                    
                # Only add if it has meaningful variation and aggregatable values
                if unique_count < total_rows * 0.8 and df[col].max() > 1:
                    key_metrics.append(col)
            
            # ENHANCED: Check non-numeric columns that might contain numeric data with special characters
            elif col not in df.select_dtypes(include=['number']).columns:
                # Check if it's a non-numeric column that should be numeric (contains "—" or other special chars)
                if any(keyword in col_lower for keyword in strong_metric_keywords):
                    # Try to clean and convert the column
                    try:
                        # Clean the data by replacing common non-numeric characters
                        cleaned_series = df[col].astype(str).replace({
                            '—': '0',
                            '-': '0', 
                            'nan': '0',
                            'NaN': '0',
                            '': '0',
                            'null': '0',
                            'NULL': '0'
                        })
                        
                        # Try to convert to numeric
                        numeric_series = cast(pd.Series, pd.to_numeric(cleaned_series, errors='coerce'))
                        
                        # If most values convert successfully, consider it a valid metric
                        non_na_count = numeric_series.notna().sum()
                        if non_na_count > len(df) * 0.5:  # More than half the values are convertible
                            key_metrics.append(col)
                            self.logger.info(f"   ✅ Added cleaned metric column: {col} (converted from text with special chars)")
                    except Exception as e:
                        self.logger.warning(f"   ⚠️ Could not clean column {col}: {str(e)}")
                        pass
        
        # Determine data type
        if any(keyword in filename_lower or any(keyword in col for col in columns_lower) for keyword in financial_keywords):
            data_type = "financial"
            # Add financial-specific metrics
            financial_metrics = [col for col in df.columns if any(keyword in str(col).lower() for keyword in financial_keywords)]
            key_metrics.extend([m for m in financial_metrics if m not in key_metrics])
        elif any(keyword in filename_lower or any(keyword in col for col in columns_lower) for keyword in hr_keywords):
            data_type = "hr"
            hr_metrics = [col for col in df.columns if any(keyword in str(col).lower() for keyword in hr_keywords)]
            key_metrics.extend([m for m in hr_metrics if m not in key_metrics])
        elif any(keyword in filename_lower or any(keyword in col for col in columns_lower) for keyword in marketing_keywords):
            data_type = "marketing"
            marketing_metrics = [col for col in df.columns if any(keyword in str(col).lower() for keyword in marketing_keywords)]
            key_metrics.extend([m for m in marketing_metrics if m not in key_metrics])
        elif any(keyword in filename_lower or any(keyword in col for col in columns_lower) for keyword in inventory_keywords):
            data_type = "operational"
            operational_metrics = [col for col in df.columns if any(keyword in str(col).lower() for keyword in inventory_keywords)]
            key_metrics.extend([m for m in operational_metrics if m not in key_metrics])
        else:
            data_type = "general"
        
        return data_type, key_metrics[:5]  # Return top 5 metrics
    
    def _generate_potential_insights(self, df: pd.DataFrame, data_type: str) -> List[str]:
        """Generate potential insights based on data type and structure."""
        insights = []
        
        if data_type == "financial":
            insights.extend([
                "Revenue trends and growth patterns",
                "Profitability analysis by product/region",
                "Cost structure breakdown",
                "Seasonal revenue patterns"
            ])
        elif data_type == "hr":
            insights.extend([
                "Employee performance distribution",
                "Department-wise headcount analysis",
                "Salary benchmarking",
                "Retention and turnover patterns"
            ])
        elif data_type == "marketing":
            insights.extend([
                "Campaign performance comparison",
                "Conversion funnel analysis",
                "ROI optimization opportunities",
                "Engagement trend analysis"
            ])
        elif data_type == "inventory":
            insights.extend([
                "Stock level optimization",
                "Product performance analysis",
                "Supplier performance metrics",
                "Demand forecasting insights"
            ])
        else:
            insights.extend([
                "Data distribution patterns",
                "Correlation analysis between variables",
                "Trend identification",
                "Outlier detection and analysis"
            ])
            
        return insights[:4]  # Limit to top 4 insights
    
    def _recommend_chart_types(self, df: pd.DataFrame, data_type: str) -> List[str]:
        """Recommend chart types based on data structure and type."""
        recommendations = []
        
        # Check data characteristics
        temporal_columns = self._identify_temporal_columns(df)
        has_temporal = len(temporal_columns) > 0
        has_categorical = len(df.select_dtypes(include=['object', 'category']).columns) > 0
        has_numerical = len(df.select_dtypes(include=['number']).columns) > 0
        
        if has_temporal:
            recommendations.extend(["line", "area"])
        
        if has_categorical and has_numerical:
            recommendations.extend(["bar", "column", "pie"])
            
        if len(df.select_dtypes(include=['number']).columns) >= 2:
            recommendations.extend(["scatter", "bubble"])
            
        # Add heatmap for correlation analysis
        if len(df.select_dtypes(include=['number']).columns) >= 3:
            recommendations.append("heatmap")
            
        return list(set(recommendations))  # Remove duplicates
    
    def _create_data_summary(self, df: pd.DataFrame, data_type: str, key_metrics: List[str]) -> str:
        """Create a human-readable summary of the data."""
        rows, cols = df.shape
        temporal_columns = self._identify_temporal_columns(df)
        
        summary = f"You've uploaded {data_type} data with {rows:,} records and {cols} columns. "
        
        if key_metrics:
            summary += f"Key metrics include: {', '.join(key_metrics[:3])}. "
            
        if temporal_columns:
            summary += f"Time-based analysis is possible with columns like {', '.join(temporal_columns[:2])}. "
            
        summary += "Let me help you create the perfect visualizations for your needs!"
        
        return summary
    
    async def get_initial_questions(self) -> List[str]:
        """Generate initial questions to ask the user based on comprehensive data analysis."""
        if not self.data_analysis:
            return ["Let me analyze your data first!"]
        
        # Generate smart initial question based on data type and analysis
        try:
            from src.services.litellm_service import LiteLLMService
            
            # Create context-aware first question
            prompt = f"""
Based on this {self.data_analysis.data_type} dataset analysis, create ONE engaging opening question that:
1. Shows I understand their data 
2. Offers specific value propositions
3. Gives them clear direction on what we can achieve together

Data Context:
- Data type: {self.data_analysis.data_type}  
- Key metrics: {', '.join(self.data_analysis.key_metrics[:3])}
- Potential insights: {', '.join(self.data_analysis.potential_insights[:2])}

Create a conversational question that suggests concrete next steps. Be specific and actionable.

Respond with just the question text (no quotes or JSON):
"""

            llm_service = LiteLLMService()
            ai_response = await llm_service.generate_response(
                prompt=prompt,
                temperature=0.7,
                max_tokens=150
            )
            
            smart_question = ai_response.content.strip().strip('"')
            
        except Exception as e:
            self.logger.warning(f"AI question generation failed: {str(e)}")
            smart_question = f"I've found some great opportunities in your {self.data_analysis.data_type} data! What's your main goal - tracking performance trends, comparing different segments, or identifying optimization opportunities?"
        
        # Prepare the full question set for reference
        questions = [
            smart_question,
            f"Which of these key metrics should we prioritize? {', '.join(self.data_analysis.key_metrics[:4])}",
            f"What time frame interests you most? (e.g., recent trends, seasonal patterns, historical overview)",
            "What's your preferred dashboard style? (executive summary, detailed analysis, or comprehensive deep-dive)",
            f"Any specific insights you're hoping to discover? I can help with: {', '.join(self.data_analysis.potential_insights[:3])}"
        ]
        
        # Add the smart opening question to conversation
        self._add_message(
            role="agent",
            content=smart_question,
            message_type="question"
        )
        
        return questions
    
    async def process_user_response(self, user_message: str) -> Dict[str, Any]:
        """Process user response and generate follow-up questions or move to next phase."""
        # Add user message to conversation
        self._add_message(
            role="user",
            content=user_message,
            message_type="response"
        )
        
        # Check if we should generate proactive suggestions
        user_message_count = len([msg for msg in self.conversation_history if msg.role == "user"])
        
        # FIXED: Only suggest dashboard after 5+ exchanges AND only if user indicates readiness
        readiness_indicators = ['generate', 'create', 'proceed', 'ready', 'yes', 'continue', 'build', 'make', 'show me']
        user_indicates_readiness = any(word in user_message.lower() for word in readiness_indicators)
        
        if user_message_count >= 5 and self.current_phase in ["questioning", "preference_gathering"] and user_indicates_readiness:
            suggestion_response = await self._generate_proactive_dashboard_suggestion(user_message)
            if suggestion_response:
                return suggestion_response
        
        # Analyze the response and determine next action  
        response_data = await self._analyze_user_response(user_message)
        
        return response_data
    
    async def _handle_data_structure_query(self, message: str) -> Dict[str, Any]:
        """Handle direct questions about data structure, columns, headers, etc."""
        try:
            if not self.data_analysis:
                response = "I haven't analyzed your data yet. Please upload a file first."
            else:
                # Get column information
                all_columns = []
                if hasattr(self.data_analysis, 'categorical_columns'):
                    all_columns.extend(self.data_analysis.categorical_columns)
                if hasattr(self.data_analysis, 'numerical_columns'):
                    all_columns.extend(self.data_analysis.numerical_columns)
                if hasattr(self.data_analysis, 'temporal_columns'):
                    all_columns.extend(self.data_analysis.temporal_columns)
                
                # Remove duplicates and None values
                all_columns = list(set([col for col in all_columns if col]))
                
                if all_columns:
                    response = f"[DATA] **Column Names in Your Data:**\n\n"
                    for i, col in enumerate(all_columns, 1):
                        response += f"{i}. **{col}**\n"
                    
                    response += f"\n[SUMMARY] **Data Summary:**\n"
                    response += f"• Total columns: {len(all_columns)}\n"
                    response += f"• Data type: {self.data_analysis.data_type}\n"
                    
                    if self.data_analysis.categorical_columns:
                        response += f"• Categorical columns: {', '.join(self.data_analysis.categorical_columns)}\n"
                    if self.data_analysis.numerical_columns:
                        response += f"• Numerical columns: {', '.join(self.data_analysis.numerical_columns)}\n"
                    if self.data_analysis.temporal_columns:
                        response += f"• Date/Time columns: {', '.join(self.data_analysis.temporal_columns)}\n"
                        
                    response += f"\n[READY] Ready to create visualizations with this data!"
                else:
                    response = "I found your data but couldn't identify clear column names. Let me help you explore the data structure differently."
            
            # Add response to conversation
            self._add_message(
                role="agent",
                content=response,
                message_type="response"
            )
            
            return {
                "response": response,
                "next_question": "What specific insights would you like to discover from this data?",
                "preferences_detected": {},
                "phase": self.current_phase,
                "suggestion": None
            }
            
        except Exception as e:
            self.logger.error(f"Error handling data structure query: {str(e)}")
            response = "I had trouble accessing your data structure. Could you try uploading the file again?"
            return {
                "response": response,
                "next_question": None,
                "preferences_detected": {},
                "phase": self.current_phase,
                "suggestion": None
            }
    
    async def _analyze_user_response(self, message: str) -> Dict[str, Any]:
        """Analyze user response using AI to understand preferences."""
        try:
            from src.services.litellm_service import LiteLLMService
            
            # Get conversation context
            conversation_length = len([msg for msg in self.conversation_history if msg.role == "user"])
            
            # Prepare AI prompt
            data_summary = self.data_analysis.data_summary if self.data_analysis else "uploaded data"
            key_metrics = ", ".join(self.data_analysis.key_metrics) if self.data_analysis else "various metrics"
            
            # Check if user is asking about data structure/columns directly
            if any(keyword in message.lower() for keyword in ['column', 'header', 'field', 'what data', 'what are']):
                return await self._handle_data_structure_query(message)
            
            # Enhanced AI prompt with better column awareness
            available_columns = {
                "categorical": self.data_analysis.categorical_columns if self.data_analysis else [],
                "numerical": self.data_analysis.numerical_columns if self.data_analysis else [],
                "temporal": self.data_analysis.temporal_columns if self.data_analysis else []
            }
            
            prompt = f"""
You are an analytics assistant helping a user create dashboards from their data.

AVAILABLE DATA COLUMNS:
- Categorical/Text columns: {', '.join(available_columns['categorical'])}
- Numerical columns: {', '.join(available_columns['numerical'])}
- Date/Time columns: {', '.join(available_columns['temporal'])}

Data summary: {data_summary}
Key metrics identified: {key_metrics}
User request: "{message}"
Conversation length: {conversation_length}

CRITICAL INSTRUCTIONS:
1. ALWAYS use the EXACT column names from the available columns above
2. For requests like "total X by Y" - identify X as a numerical column and Y as categorical/temporal
3. For filtering requests like "only for AA names" - identify which column contains this filter criteria
4. Be specific about which exact columns will be used for the visualization
5. If the user mentions terms that don't match exact column names, suggest the closest matching columns

EXAMPLES:
- "total units by date" → use [exact numerical column name] aggregated by [exact date column name]
- "show sales by region" → use [exact sales column] grouped by [exact region column]  
- "only for AA names" → filter [exact name column] where values contain "AA"

Respond naturally but ALWAYS specify the exact column names you will use.
Keep response under 200 words and be conversational but precise.
"""

            # Get AI response
            llm_service = LiteLLMService()
            ai_response = await llm_service.generate_response(
                prompt=prompt,
                temperature=0.3,  # Lower temperature for more consistent responses
                max_tokens=500
            )
            
            # Handle AI response as plain text
            response_content = ai_response.content.strip()
            
            # Add AI response to conversation
            self._add_message(
                role="agent",
                content=response_content,
                message_type="response"
            )
            
            # Analyze the conversation to determine next steps
            message_lower = message.lower()
            
            # Detect preferences from user message
            preferences_detected = {}
            
            # Enhanced chart preferences detection
            if any(word in message_lower for word in ['line', 'trend', 'timeline', 'over time', 'progression', 'growth']):
                preferences_detected["chart_preference"] = ["line"]
            elif any(word in message_lower for word in ['bar', 'compare', 'comparison', 'versus', 'vs', 'by']):
                preferences_detected["chart_preference"] = ["bar"]
            elif any(word in message_lower for word in ['pie', 'distribution', 'breakdown', 'proportion', 'percentage']):
                preferences_detected["chart_preference"] = ["pie"]
            elif any(word in message_lower for word in ['scatter', 'correlation', 'relationship']):
                preferences_detected["chart_preference"] = ["scatter"]
                
            # Enhanced granularity detection
            if any(word in message_lower for word in ['daily', 'day', 'each day']):
                preferences_detected["granularity"] = "daily"
            elif any(word in message_lower for word in ['weekly', 'week', 'each week']):
                preferences_detected["granularity"] = "weekly"
            elif any(word in message_lower for word in ['monthly', 'month', 'each month']):
                preferences_detected["granularity"] = "monthly"
            elif any(word in message_lower for word in ['yearly', 'year', 'annual']):
                preferences_detected["granularity"] = "yearly"
            
            # Enhanced filtering detection
            if any(word in message_lower for word in ['only', 'where', 'filter', 'containing', 'with', 'having']):
                preferences_detected["filtering_requested"] = True
                # Extract the filter criteria from the message
                filter_terms = []
                for word in message.split():
                    if len(word) > 2 and word.upper() == word and word.isalpha():  # Likely abbreviations like "AA"
                        filter_terms.append(word)
                if filter_terms:
                    preferences_detected["filter_criteria"] = filter_terms
            
            # Detect specific requests for visualization generation
            generate_indicators = ['generate', 'create', 'proceed', 'ready', 'yes', 'continue', 'build', 'make', 'show me', 'graph', 'chart', 'plot', 'visualize']
            
            # Generate next question or suggest dashboard generation
            next_question = None
            suggestion = None
            show_generate_button = False
            
            # Check if user is asking for specific visualization or ready to generate
            if any(word in message_lower for word in generate_indicators):
                suggestion = "Perfect! I'll create that visualization using the exact columns from your data."
                show_generate_button = True
                self.current_phase = "generating"
                
                # If user is ready to generate, call the dashboard generation
                if hasattr(self, 'original_dataframe') and self.original_dataframe is not None:
                    try:
                        dashboard_result = await self.generate_dashboard_from_conversation()
                        # Update the response to include dashboard generation success
                        response_content = f"{response_content}\n\n[GENERATING] Creating your custom dashboard now with the specified data columns..."
                        return {
                            "response": response_content,
                            "next_question": next_question,
                            "suggestion": suggestion,
                            "preferences_detected": preferences_detected,
                            "phase": self.current_phase,
                            "show_generate_button": show_generate_button,
                            "dashboard_generated": True,
                            "dashboard_result": dashboard_result
                        }
                    except Exception as e:
                        self.logger.error(f"Dashboard generation failed: {str(e)}")
                        response_content = f"{response_content}\n\n[WARNING] I'm ready to generate your dashboard, but encountered a technical issue. Let me try again..."
                        
            elif conversation_length >= 3:  # After 3 exchanges, offer to generate
                next_question = "Ready to generate your dashboard with these specific visualizations? Just say 'yes' or tell me about any other charts you'd like to see."
            else:
                next_question = "What specific insights are you most interested in seeing from your data?"
            
            return {
                "response": response_content,
                "next_question": next_question,
                "suggestion": suggestion,
                "preferences_detected": preferences_detected,
                "phase": self.current_phase,
                "show_generate_button": show_generate_button
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing user response: {str(e)}")
            # Fallback to keyword analysis
            return self._fallback_keyword_analysis(message, len([msg for msg in self.conversation_history if msg.role == "user"]))
    
    def _fallback_keyword_analysis(self, message: str, conversation_length: int) -> Dict[str, Any]:
        """Fallback keyword-based analysis when AI is unavailable."""
        message_lower = message.lower()
        
        response = {
            "next_question": None,
            "preferences_detected": {},
            "phase": self.current_phase,
            "suggestion": None
        }
        
        # Detect visualization preferences
        if any(word in message_lower for word in ['trend', 'timeline', 'over time', 'growth']):
            response["preferences_detected"]["chart_preference"] = ["line", "area"]
            
        if any(word in message_lower for word in ['compare', 'comparison', 'versus', 'vs']):
            response["preferences_detected"]["chart_preference"] = ["bar", "column"]
            
        if any(word in message_lower for word in ['distribution', 'breakdown', 'proportion']):
            response["preferences_detected"]["chart_preference"] = ["pie", "donut"]
            
        # Detect granularity preferences
        if any(word in message_lower for word in ['daily', 'day by day']):
            response["preferences_detected"]["granularity"] = "daily"
        elif any(word in message_lower for word in ['weekly', 'week']):
            response["preferences_detected"]["granularity"] = "weekly"
        elif any(word in message_lower for word in ['monthly', 'month']):
            response["preferences_detected"]["granularity"] = "monthly"
            
        # Generate follow-up based on conversation length
        if conversation_length < 5:  # FIXED: Increased from 3 to 5
            response["next_question"] = self._generate_follow_up_question(response["preferences_detected"])
            response["phase"] = "questioning"
        else:
            # Only suggest dashboard if user indicates readiness
            readiness_indicators = ['generate', 'create', 'proceed', 'ready', 'yes', 'continue', 'build', 'make', 'show me']
            if any(word in message_lower for word in readiness_indicators):
                response["phase"] = "preference_gathering"
                response["suggestion"] = "I think I have enough information to create your custom analytics. Shall we proceed?"
                self.current_phase = "preference_gathering"
            else:
                response["next_question"] = "What specific visualization would you like me to create for you?"
                response["phase"] = "questioning"
            
        return response
    
    def _generate_follow_up_question(self, detected_preferences: Dict[str, Any]) -> str:
        """Generate appropriate follow-up question based on detected preferences."""
        if "chart_preference" in detected_preferences:
            return "Great choice! Would you like me to focus on specific metrics or show all key indicators?"
        elif "granularity" in detected_preferences:
            return "Perfect! What visualization style do you prefer - clean and minimal or detailed with all data points?"
        else:
            return "What specific insights are you hoping to discover from this data?"
    
    def compile_user_preferences(self) -> UserPreference:
        """Compile user preferences from conversation history."""
        # Analyze all user messages to extract preferences
        user_messages = [msg for msg in self.conversation_history if msg.role == "user"]
        
        # Initialize with defaults based on data analysis
        preferences = UserPreference(
            preferred_chart_types=self.data_analysis.recommended_chart_types[:3] if self.data_analysis else ["bar", "line"],
            key_metrics_to_focus=self.data_analysis.key_metrics[:4] if self.data_analysis else [],
            custom_legends={},
            data_granularity="all",
            visualization_style="detailed",
            specific_questions=[]
        )
        
        # Extract preferences from conversation
        for msg in user_messages:
            content_lower = msg.content.lower()
            
            # Enhanced chart preferences detection
            if any(word in content_lower for word in ['trend', 'timeline', 'over time', 'progression', 'growth']):
                if "line" not in preferences.preferred_chart_types:
                    preferences.preferred_chart_types.insert(0, "line")
                    
            if any(word in content_lower for word in ['compare', 'comparison', 'versus', 'vs', 'by']):
                if "bar" not in preferences.preferred_chart_types:
                    preferences.preferred_chart_types.insert(0, "bar")
            
            if any(word in content_lower for word in ['pie', 'distribution', 'breakdown', 'proportion']):
                if "pie" not in preferences.preferred_chart_types:
                    preferences.preferred_chart_types.insert(0, "pie")
                    
            # Enhanced granularity detection
            if any(word in content_lower for word in ['daily', 'day', 'each day']):
                preferences.data_granularity = "daily"
            elif any(word in content_lower for word in ['weekly', 'week', 'each week']):
                preferences.data_granularity = "weekly" 
            elif any(word in content_lower for word in ['monthly', 'month', 'each month']):
                preferences.data_granularity = "monthly"
            elif any(word in content_lower for word in ['yearly', 'year', 'annual']):
                preferences.data_granularity = "yearly"
                
            # Extract specific questions/goals - ENHANCED to capture all types of requests
            visualization_keywords = [
                "want to see", "show me", "i want", "need to", "looking for", "goal", 
                "chart", "graph", "plot", "visualize", "display", "analyze", 
                "by date", "by time", "over time", "trend", "comparison", "compare",
                "total", "sum", "count", "breakdown", "distribution", "create"
            ]
            
            # ENHANCED: Detect filtering requests with more patterns
            filtering_keywords = [
                "only for", "only where", "where", "containing", "with", "having", 
                "including", "equals", "is", "filter", "exclude", "include",
                "for data", "for names", "for values", "specific", "particular",
                "that contain", "starting with", "ending with"
            ]
            
            # Capture ALL user requests that seem to be asking for visualizations or data manipulation
            if (any(keyword in content_lower for keyword in visualization_keywords) or 
                any(keyword in content_lower for keyword in filtering_keywords) or
                len(msg.content.split()) > 3):  # Capture longer, descriptive requests
                
                preferences.specific_questions.append(msg.content)
                self.logger.info(f"[PREFERENCES] Captured user request: '{msg.content}'")
                
                # Parse for specific column mentions
                if self.data_analysis:
                    all_columns = (self.data_analysis.categorical_columns + 
                                 self.data_analysis.numerical_columns + 
                                 self.data_analysis.temporal_columns)
                    
                    mentioned_columns = []
                    for col in all_columns:
                        if col and col.lower() in content_lower:
                            mentioned_columns.append(col)
                            
                    if mentioned_columns:
                        self.logger.info(f"[PREFERENCES] Found column mentions: {mentioned_columns}")
                        if mentioned_columns[0] not in preferences.key_metrics_to_focus:
                            preferences.key_metrics_to_focus.append(mentioned_columns[0])
        
        self.user_preferences = preferences
        return preferences
    
    def _add_message(self, role: str, content: str, message_type: str, data_context: Optional[Dict[str, Any]] = None):
        """Add message to conversation history."""
        message = ChatMessage(
            role=role,
            content=content,
            timestamp=datetime.now(),
            message_type=message_type,
            data_context=data_context
        )
        self.conversation_history.append(message)
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get conversation history in serializable format."""
        return [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
                "message_type": msg.message_type,
                "data_context": msg.data_context
            }
            for msg in self.conversation_history
        ]
    
    def get_current_phase(self) -> str:
        """Get current conversation phase."""
        return self.current_phase
    
    def reset_conversation(self):
        """Reset conversation for new data upload."""
        self.conversation_history = []
        self.data_analysis = None
        self.user_preferences = None
        self.current_phase = "analysis" 

    async def _analyze_excel_sheets(self, excel_file) -> Dict[str, Any]:
        """Analyze multiple sheets in an Excel file."""
        sheet_analysis = {
            "total_sheets": len(excel_file.sheet_names),
            "sheet_names": excel_file.sheet_names,
            "sheet_details": {}
        }
        
        try:
            for sheet_name in excel_file.sheet_names:
                sheet_df = pd.read_excel(excel_file, sheet_name=sheet_name)
                sheet_analysis["sheet_details"][sheet_name] = {
                    "rows": len(sheet_df),
                    "columns": len(sheet_df.columns),
                    "column_names": sheet_df.columns.tolist(),
                    "data_types": sheet_df.dtypes.astype(str).to_dict(),
                    "sample_data": sheet_df.head(3).to_dict('records') if len(sheet_df) > 0 else []
                }
        except Exception as e:
            self.logger.warning(f"Error analyzing sheets: {str(e)}")
            
        return sheet_analysis

    async def _analyze_columns_comprehensive(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Perform comprehensive analysis of each column."""
        column_analysis = {}
        
        for col in df.columns:
            series = df[col]
            col_analysis = {
                "name": col,
                "data_type": str(series.dtype),
                "non_null_count": series.count(),
                "null_count": series.isnull().sum(),
                "null_percentage": (series.isnull().sum() / len(series)) * 100,
                "unique_count": series.nunique(),
                "unique_percentage": (series.nunique() / len(series)) * 100,
                "sample_values": convert_for_json(series.dropna().head(10).tolist()),
                "unique_values": convert_for_json(series.unique()[:20].tolist()) if series.nunique() <= 50 else f"Too many unique values ({series.nunique()})"
            }
            
            # Specific analysis based on data type
            if pd.api.types.is_numeric_dtype(series):
                col_analysis.update({
                    "min_value": convert_for_json(series.min()),
                    "max_value": convert_for_json(series.max()),
                    "mean": convert_for_json(series.mean()),
                    "median": convert_for_json(series.median()),
                    "std_dev": convert_for_json(series.std()),
                    "has_outliers": False  # Default to False
                })
                
                # Calculate outliers safely
                if SCIPY_AVAILABLE and len(series.dropna()) > 0:
                    try:
                        clean_series = series.dropna()
                        if len(clean_series) > 3:  # Need at least 3 values for zscore
                            z_scores = np.abs(stats.zscore(clean_series))
                            outlier_count = len(clean_series[z_scores > 3])
                            col_analysis["has_outliers"] = outlier_count > 0
                    except Exception as e:
                        self.logger.warning(f"Failed to calculate outliers for column {col}: {str(e)}")
                        col_analysis["has_outliers"] = False
                    
            elif pd.api.types.is_datetime64_any_dtype(series):
                try:
                    min_date = series.min()
                    max_date = series.max()
                    col_analysis.update({
                        "date_range": f"{convert_for_json(min_date)} to {convert_for_json(max_date)}",
                        "date_span_days": (max_date - min_date).days if series.notna().any() else 0
                    })
                except Exception as e:
                    # Fallback for datetime conversion issues
                    col_analysis.update({
                        "date_range": "Date range available",
                        "date_span_days": 0
                    })
            else:
                # Categorical analysis
                value_counts = series.value_counts().head(10)
                col_analysis.update({
                    "most_frequent": convert_for_json(value_counts.to_dict()),
                    "category_distribution": "Even" if series.nunique() > len(series) * 0.8 else "Concentrated"
                })
            
            # Business context hints
            col_analysis["business_hints"] = self._identify_business_context(col, series)
            
            column_analysis[col] = col_analysis
            
        return column_analysis

    async def _analyze_row_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze patterns in row data."""
        patterns = {
            "total_rows": len(df),
            "duplicate_rows": df.duplicated().sum(),
            "completely_empty_rows": df.isnull().all(axis=1).sum(),
            "mostly_empty_rows": (df.isnull().sum(axis=1) > len(df.columns) * 0.8).sum(),
            "data_density": ((df.notna().sum().sum()) / (len(df) * len(df.columns))) * 100
        }
        
        # Sample rows for pattern detection
        if len(df) > 0:
            patterns["sample_first_rows"] = convert_for_json(df.head(3).to_dict('records'))
            patterns["sample_random_rows"] = convert_for_json(df.sample(min(3, len(df))).to_dict('records'))
            
        # Check for hierarchical data patterns
        patterns["potential_hierarchy"] = self._detect_hierarchical_patterns(df)
        
        return patterns

    def _identify_business_context(self, column_name: str, series: pd.Series) -> List[str]:
        """Identify business context hints for a column."""
        hints = []
        col_lower = column_name.lower()
        
        # Financial indicators
        if any(word in col_lower for word in ['revenue', 'sales', 'profit', 'cost', 'price', 'amount', 'payment']):
            hints.append("Financial metric")
        
        # Time indicators
        if any(word in col_lower for word in ['date', 'time', 'created', 'updated', 'timestamp']):
            hints.append("Temporal data")
            
        # Identifier indicators
        if any(word in col_lower for word in ['id', 'key', 'code', 'number']) and series.nunique() > len(series) * 0.9:
            hints.append("Unique identifier")
            
        # Category indicators
        if series.nunique() < 50 and pd.api.types.is_object_dtype(series):
            hints.append("Categorical data")
            
        # Measurement indicators
        if any(word in col_lower for word in ['count', 'total', 'sum', 'avg', 'percentage', 'rate']):
            hints.append("Measurement/KPI")
            
        return hints

    def _detect_hierarchical_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Detect if data has hierarchical structure."""
        hierarchy_hints = {
            "has_parent_child": False,
            "has_categories": False,
            "has_nested_structure": False
        }
        
        # Look for parent-child relationships
        for col in df.columns:
            col_lower = col.lower()
            if any(word in col_lower for word in ['parent', 'child', 'level', 'hierarchy']):
                hierarchy_hints["has_parent_child"] = True
                
        # Look for categorical breakdown
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns
        if len(categorical_cols) >= 2:
            hierarchy_hints["has_categories"] = True
            
        return hierarchy_hints

    async def _identify_data_type_and_metrics_enhanced(self, df: pd.DataFrame, filename: str, column_analysis: Dict[str, Any]) -> Tuple[str, List[str]]:
        """Enhanced identification using AI analysis of column names and content."""
        try:
            from src.services.litellm_service import LiteLLMService
            
            # Prepare column information for AI
            column_info = []
            for col, analysis in column_analysis.items():
                column_info.append({
                    "name": col,
                    "type": analysis["data_type"],
                    "business_hints": analysis["business_hints"],
                    "sample_values": analysis["sample_values"][:5],
                    "unique_count": analysis["unique_count"]
                })
            
            prompt = f"""
Analyze this dataset to determine its business domain and key metrics:

Filename: {filename}
Columns: {json.dumps(column_info, indent=2)}

Determine:
1. Business domain (financial, hr, marketing, inventory, sales, operational, etc.)
2. Key metrics for KPIs (3-5 most important measurable columns)
3. Primary purpose of this dataset
"""

            # Define the expected JSON structure
            response_format = {
                "data_type": "domain_name",
                "key_metrics": ["metric1", "metric2", "metric3"],
                "reasoning": "explanation of analysis",
                "confidence": 0.95
            }

            llm_service = LiteLLMService()
            if not llm_service.is_available():
                self.logger.warning("LiteLLM service not available, using fallback analysis")
                return self._identify_data_type_and_metrics(df, filename)
            
            ai_response = await llm_service.generate_structured_response(
                prompt=prompt,
                response_format=response_format
            )
            
            # Check if AI response contains an error
            if ai_response.error:
                self.logger.warning(f"AI response contains error: {ai_response.error}")
                return self._identify_data_type_and_metrics(df, filename)
            
            # Try to parse JSON response, with better error handling
            try:
                result = json.loads(ai_response.content)
                return result.get("data_type", "operational"), result.get("key_metrics", [])
            except json.JSONDecodeError as json_err:
                self.logger.warning(f"Failed to parse AI response as JSON: {json_err}")
                self.logger.debug(f"Raw AI response content: {ai_response.content[:500]}...")
                # Try to extract basic info from text response if possible
                return self._identify_data_type_and_metrics(df, filename)
            
        except Exception as e:
            self.logger.warning(f"AI analysis failed, using fallback: {str(e)}")
            # Always fall back to the simple method if AI fails
            return self._identify_data_type_and_metrics(df, filename)

    async def _generate_comprehensive_insights(self, df: pd.DataFrame, data_type: str, column_analysis: Dict[str, Any], row_patterns: Dict[str, Any]) -> List[str]:
        """Generate comprehensive insights using AI analysis."""
        try:
            from src.services.litellm_service import LiteLLMService
            
            # Prepare data summary for AI
            data_summary = {
                "rows": len(df),
                "columns": len(df.columns),
                "data_type": data_type,
                "data_density": row_patterns["data_density"],
                "key_columns": list(column_analysis.keys())[:10],
                "column_types": {col: analysis["data_type"] for col, analysis in column_analysis.items()}
            }
            
            prompt = f"""
Based on this {data_type} dataset analysis, generate specific, actionable insights:

Dataset Summary: {json.dumps(data_summary, indent=2)}

Generate 5-7 specific insights that would be valuable for business analysis, such as:
- Trends that could be analyzed
- Performance metrics that could be tracked  
- Comparisons that would be meaningful
- Patterns that might exist in the data
- Key questions this data could answer
"""

            # Define the expected response format
            response_format = ["insight1", "insight2", "insight3", "insight4", "insight5"]

            llm_service = LiteLLMService()
            if not llm_service.is_available():
                self.logger.warning("LiteLLM service not available, using fallback insights")
                return self._generate_potential_insights(df, data_type)
            
            ai_response = await llm_service.generate_structured_response(
                prompt=prompt,
                response_format=response_format
            )
            
            # Check if AI response contains an error
            if ai_response.error:
                self.logger.warning(f"AI insights response contains error: {ai_response.error}")
                return self._generate_potential_insights(df, data_type)
            
            # Try to parse JSON response with better error handling
            try:
                insights = json.loads(ai_response.content)
                return insights if isinstance(insights, list) else []
            except json.JSONDecodeError as json_err:
                self.logger.warning(f"Failed to parse AI insights as JSON: {json_err}")
                self.logger.debug(f"Raw AI insights content: {ai_response.content[:500]}...")
                return self._generate_potential_insights(df, data_type)
            
        except Exception as e:
            self.logger.warning(f"AI insights generation failed, using fallback: {str(e)}")
            return self._generate_potential_insights(df, data_type)

    async def _recommend_chart_types_with_ai(self, df: pd.DataFrame, data_type: str, column_analysis: Dict[str, Any]) -> List[str]:
        """Get AI-powered chart recommendations with reasoning."""
        try:
            from src.services.litellm_service import LiteLLMService
            
            # Identify key column patterns
            temporal_cols = [col for col, analysis in column_analysis.items() if "Temporal data" in analysis.get("business_hints", [])]
            numerical_cols = [col for col, analysis in column_analysis.items() if analysis["data_type"].startswith(('int', 'float'))]
            categorical_cols = [col for col, analysis in column_analysis.items() if "Categorical data" in analysis.get("business_hints", [])]
            
            prompt = f"""
Recommend optimal chart types for this {data_type} dataset:

Available Data:
- Temporal columns: {temporal_cols}
- Numerical columns: {numerical_cols}  
- Categorical columns: {categorical_cols}
- Total rows: {len(df)}

Recommend 4-6 chart types that would be most effective for this data, considering:
- What story the data tells best
- What business insights are most valuable
- What visualizations would be most engaging
"""

            # Define the expected response format
            response_format = ["line", "bar", "pie", "area", "scatter", "heatmap"]

            llm_service = LiteLLMService()
            if not llm_service.is_available():
                self.logger.warning("LiteLLM service not available, using fallback chart recommendations")
                return self._recommend_chart_types(df, data_type)
            
            ai_response = await llm_service.generate_structured_response(
                prompt=prompt,
                response_format=response_format
            )
            
            # Check if AI response contains an error
            if ai_response.error:
                self.logger.warning(f"AI chart recommendations response contains error: {ai_response.error}")
                return self._recommend_chart_types(df, data_type)
            
            # Try to parse JSON response with better error handling
            try:
                chart_types = json.loads(ai_response.content)
                return chart_types if isinstance(chart_types, list) else []
            except json.JSONDecodeError as json_err:
                self.logger.warning(f"Failed to parse AI chart recommendations as JSON: {json_err}")
                self.logger.debug(f"Raw AI chart content: {ai_response.content[:500]}...")
                return self._recommend_chart_types(df, data_type)
            
        except Exception as e:
            self.logger.warning(f"AI chart recommendations failed, using fallback: {str(e)}")
            return self._recommend_chart_types(df, data_type)

    async def _create_enhanced_data_summary(self, df: pd.DataFrame, data_type: str, key_metrics: List[str], 
                                          column_analysis: Dict[str, Any], sheet_analysis: Dict[str, Any]) -> str:
        """Create a comprehensive data summary."""
        summary_parts = []
        
        # Basic info
        summary_parts.append(f"[ANALYSIS] I've analyzed your {data_type} dataset with {len(df):,} rows and {len(df.columns)} columns.")
        
        # Sheet info for Excel files
        if sheet_analysis and sheet_analysis.get("total_sheets", 0) > 1:
            summary_parts.append(f"[SHEETS] This Excel file contains {sheet_analysis['total_sheets']} sheets: {', '.join(sheet_analysis['sheet_names'])}.")
        
        # Data quality
        non_null_percentage = ((df.notna().sum().sum()) / (len(df) * len(df.columns))) * 100
        summary_parts.append(f"[QUALITY] Data quality is {'excellent' if non_null_percentage > 90 else 'good' if non_null_percentage > 70 else 'moderate'} ({non_null_percentage:.1f}% complete).")
        
        # Key metrics
        if key_metrics:
            summary_parts.append(f"[METRICS] Key metrics identified: {', '.join(key_metrics[:4])}.")
        
        # Column insights
        numerical_count = len([col for col, analysis in column_analysis.items() if analysis["data_type"].startswith(('int', 'float'))])
        categorical_count = len([col for col, analysis in column_analysis.items() if "Categorical data" in analysis.get("business_hints", [])])
        temporal_count = len([col for col, analysis in column_analysis.items() if "Temporal data" in analysis.get("business_hints", [])])
        
        if temporal_count > 0:
            summary_parts.append(f"[TIME] Time-based analysis is available with {temporal_count} temporal column(s).")
        if numerical_count > 0:
            summary_parts.append(f"[KPI] {numerical_count} numerical metrics ready for KPI tracking.")
        if categorical_count > 0:
            summary_parts.append(f"[SEGMENTS] {categorical_count} categorical dimensions for segmentation.")
        
        summary_parts.append("[READY] I'm ready to help you create the perfect visualizations!")
        
        return " ".join(summary_parts)

    async def _create_comprehensive_analysis_message(self, df: pd.DataFrame, data_summary: str, 
                                                   column_analysis: Dict[str, Any], row_patterns: Dict[str, Any], 
                                                   sheet_analysis: Dict[str, Any]) -> str:
        """Create a comprehensive analysis message for the user."""
        message_parts = [data_summary]
        
        message_parts.append("\n\n[DETAILS] **Detailed Analysis:**")
        
        # Most interesting columns
        interesting_cols = []
        for col, analysis in column_analysis.items():
            if analysis.get("business_hints") and len(analysis["business_hints"]) > 0:
                hints_text = ", ".join(analysis["business_hints"])
                interesting_cols.append(f"• **{col}**: {hints_text}")
        
        if interesting_cols:
            message_parts.append("\n**Key Columns Detected:**")
            message_parts.extend(interesting_cols[:5])  # Show top 5
        
        # Data patterns
        message_parts.append(f"\n**Data Patterns:**")
        message_parts.append(f"• Data density: {row_patterns['data_density']:.1f}%")
        
        if row_patterns['duplicate_rows'] > 0:
            message_parts.append(f"• Found {row_patterns['duplicate_rows']} duplicate rows")
            
        if row_patterns['potential_hierarchy']['has_categories']:
            message_parts.append(f"• Hierarchical data structure detected")
        
        # Suggested approach
        message_parts.append(f"\n[INSIGHTS] **My Recommended Approach:**")
        message_parts.append(f"Based on this analysis, I suggest we create:")
        message_parts.append(f"1. **KPI Dashboard** - Track your key {data_summary.split('dataset')[0].strip()} metrics")
        message_parts.append(f"2. **Trend Analysis** - Show performance over time") 
        message_parts.append(f"3. **Comparative Views** - Compare different segments")
        message_parts.append(f"4. **Detailed Breakdowns** - Drill into specific areas")
        
        message_parts.append(f"\n[QUESTION] **What would you like to focus on first?** I can customize everything based on your needs!")
        
        return "\n".join(message_parts)

    async def _generate_proactive_dashboard_suggestion(self, user_message: str) -> Optional[Dict[str, Any]]:
        """Generate proactive dashboard suggestions based on conversation context."""
        try:
            from src.services.litellm_service import LiteLLMService
            
            # Gather conversation context
            user_messages = [msg.content for msg in self.conversation_history if msg.role == "user"]
            conversation_context = " | ".join(user_messages)
            
            # Get data context
            data_context = self.data_analysis
            if not data_context:
                return None
                
            prompt = f"""
Based on this conversation and data analysis, create a specific dashboard proposal:

DATA ANALYSIS:
- Data type: {data_context.data_type}
- Key metrics: {', '.join(data_context.key_metrics)}
- Available insights: {', '.join(data_context.potential_insights[:4])}
- Recommended charts: {', '.join(data_context.recommended_chart_types)}

USER CONVERSATION: {conversation_context}

Create a specific dashboard proposal with:
1. 3-4 concrete KPIs to track (with brief explanations)
2. 4-5 specific chart recommendations (chart type + what it shows)
3. Layout suggestions (how to organize the dashboard)

Be specific about what data will be visualized and why. Show that you understand their needs.

Format as a conversational message that:
- Summarizes what you learned from them
- Presents the concrete proposal  
- Asks for their confirmation or changes
- Offers to proceed with generation

Respond with just the message text:
"""

            llm_service = LiteLLMService()
            ai_response = await llm_service.generate_response(
                prompt=prompt,
                temperature=0.7,
                max_tokens=600
            )
            
            suggestion_message = ai_response.content.strip()
            
            # Add the suggestion to conversation
            self._add_message(
                role="agent",
                content=suggestion_message,
                message_type="suggestion"
            )
            
            # Update phase to preference gathering
            self.current_phase = "preference_gathering"
            
            return {
                "response": suggestion_message,
                "conversation_history": self.get_conversation_history(),
                "phase": self.current_phase,
                "suggestion": "Ready to generate your custom dashboard based on this proposal. Should I proceed or would you like any changes?",
                "show_generate_button": True  # Signal to frontend to show generate button
            }
            
        except Exception as e:
            self.logger.error(f"Error generating proactive suggestion: {str(e)}")
            return None

    async def generate_dashboard_from_conversation(self) -> Dict[str, Any]:
        """Generate dashboard based on conversation history and user preferences."""
        try:
            self.logger.info("[DASHBOARD] Starting dashboard generation from conversation")
            
            # Compile user preferences from conversation
            preferences = self.compile_user_preferences()
            
            # Convert UserPreference dataclass to dictionary for the dashboard generator
            preferences_dict = {
                "preferred_chart_types": preferences.preferred_chart_types,
                "key_metrics_to_focus": preferences.key_metrics_to_focus,
                "data_granularity": preferences.data_granularity,
                "specific_questions": preferences.specific_questions,
                "visualization_style": preferences.visualization_style,
                "custom_legends": preferences.custom_legends,
                "color_preferences": preferences.color_preferences
            }
            
            # Import dashboard generator
            from src.services.ai_dashboard_generator import AIDashboardGenerator
            
            # Get the original dataframe (assume it's still available)
            if not hasattr(self, 'original_dataframe') or self.original_dataframe is None:
                return {
                    "success": False,
                    "error": "Original data is no longer available. Please re-upload your file."
                }
            
            # Initialize dashboard generator
            dashboard_generator = AIDashboardGenerator()
            
            # Generate dashboard with user preferences using the dataframe directly
            dashboard_result = await dashboard_generator.generate_dashboard_from_dataframe(
                df=self.original_dataframe,
                filename="chat_data",
                user_preferences=preferences_dict
            )
            
            # Update conversation phase
            self.current_phase = "completed"
            
            # Add success message to conversation
            success_message = "[SUCCESS] **Dashboard Generated Successfully!** Your custom analytics dashboard has been created based on our conversation. You can now explore your data with the visualizations we discussed."
            
            self._add_message(
                role="agent",
                content=success_message,
                message_type="completion"
            )
            
            self.logger.info("[DASHBOARD] Dashboard generation completed successfully")
            
            return {
                "success": True,
                "dashboard_data": dashboard_result,
                "response": success_message,
                "phase": self.current_phase,
                "conversation_history": self.get_conversation_history()
            }
            
        except Exception as e:
            error_message = f"I encountered an issue while generating your dashboard: {str(e)}. Let me try a different approach."
            
            self.logger.error(f"[DASHBOARD] Dashboard generation failed: {str(e)}")
            
            self._add_message(
                role="agent",
                content=error_message,
                message_type="error"
            )
            
            return {
                "success": False,
                "error": error_message,
                "phase": self.current_phase,
                "conversation_history": self.get_conversation_history()
            }

    def set_original_dataframe(self, df: pd.DataFrame):
        """Store the original dataframe for dashboard generation."""
        self.original_dataframe = df
        self.logger.info(f"[DATA] Stored original dataframe with {len(df)} rows and {len(df.columns)} columns") 