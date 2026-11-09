"""
AI-Powered Dashboard Generation Service

This service implements a Google ADK-inspired approach for intelligent dashboard generation.
It uses AI models to analyze Excel data, detect existing pivot tables, create new ones when needed,
and generate appropriate visualizations based on data characteristics.
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, cast
from dataclasses import dataclass
from datetime import datetime
import json
import io
import asyncio
from pathlib import Path
import traceback
from difflib import SequenceMatcher
import re

# Configure logger to handle Unicode characters properly
logger = logging.getLogger(__name__)

# Import safe Unicode utilities
from src.core.unicode_utils import safe_log_message, safe_str

# Helper function for safe logging of strings with special characters
def safe_log_string(text: str) -> str:
    """Convert string to ASCII-safe format for logging in Windows environments."""
    return safe_str(text)

@dataclass
class PivotTableRecommendation:
    """Data class for pivot table recommendations."""
    name: str
    rows: List[str]
    columns: List[str]
    values: List[str]
    aggregation: str  # sum, count, average, etc.
    confidence: float
    reasoning: str
    suggested_charts: List[str]

@dataclass
class ChartRecommendation:
    """Enhanced chart recommendation with AI insights."""
    chart_type: str
    data_columns: List[str]
    title: str
    description: str
    confidence: float
    ai_reasoning: str
    recharts_config: Dict[str, Any]
    data: List[Dict[str, Any]]
    pivot_table_source: Optional[str] = None

@dataclass
class ExcelAnalysisResult:
    """Result of Excel file analysis."""
    sheets: List[str]
    existing_pivot_tables: List[str]
    data_characteristics: Dict[str, Any]
    recommended_pivot_tables: List[PivotTableRecommendation]
    chart_recommendations: List[ChartRecommendation]
    ai_insights: str

class AIAgent:
    """Base AI Agent class inspired by Google ADK."""
    
    def __init__(self, name: str, model: str, instruction: str):
        self.name = name
        self.model = model
        self.instruction = instruction
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the LiteLLM client."""
        try:
            # Use the LiteLLM service instead of direct GenAI client
            from ..services.litellm_service import litellm_service
            
            self.client = litellm_service
            logger.info(f"Initialized {self.name} agent with LiteLLM service for model {self.model}")
        except Exception as e:
            logger.warning(f"LiteLLM service not available for {self.name}: {str(e)}")
            self.client = None
    
    async def generate_response(self, prompt: str, data_context: str = "") -> str:
        """Generate AI response with context."""
        if not self.client:
            logger.warning(f"No AI client available for {self.name}, using fallback")
            return self._fallback_response(prompt)
        
        try:
            full_prompt = f"""
{self.instruction}

Context: {data_context}

Task: {prompt}

Please provide a detailed analysis and recommendations.
"""
            
            # Use LiteLLM service with async call
            response = await self.client.generate_response(
                prompt=full_prompt,
                model=None,  # Use default model from configuration
                temperature=0.3,
                max_tokens=2048
            )
            
            return response.content
            
        except Exception as e:
            logger.error(f"AI generation failed for {self.name}: {str(e)}")
            return self._fallback_response(prompt)
    
    def _fallback_response(self, prompt: str) -> str:
        """Fallback response when AI is not available."""
        return f"AI analysis not available. Manual analysis needed for: {prompt[:100]}..."

class AIDashboardGenerator:
    """Main AI-powered dashboard generator using Google ADK principles."""
    
    def __init__(self):
        """Initialize the AI Dashboard Generator."""
        pass
    
    async def analyze_and_generate_dashboard(self, file_data: bytes, filename: str, 
                                            generate_per_sheet: bool = True) -> Dict[str, Any]:
        """
        Main method to analyze Excel file and generate dashboard configuration.
        
        Args:
            file_data: Excel file as bytes
            filename: Name of the file
            generate_per_sheet: If True, generate separate analysis for each sheet
        
        Uses advanced analytics when AI is available, falls back to rule-based analysis otherwise.
        """
        try:
            logger.info(f"Starting dashboard generation for {filename} (per_sheet={generate_per_sheet})")
            
            # Parse Excel file to extract data
            excel_data = await self._parse_excel_file(file_data, filename)
            
            if generate_per_sheet and len(excel_data['sheets']) > 1:
                # Generate separate dashboard for each sheet
                return await self._generate_multi_sheet_dashboard(excel_data, filename)
            else:
                # Generate single dashboard using primary sheet (legacy behavior)
                return await self._generate_single_sheet_dashboard(excel_data, filename, file_data)
                
        except Exception as e:
            logger.error(f"Dashboard generation failed: {str(e)}")
            # Fall back to rule-based generation
            return await self._generate_fallback_dashboard(file_data, filename)
    
    def _check_ai_availability(self) -> bool:
        """Check if AI services are available."""
        try:
            import os
            # Check for any available AI API keys
            api_keys = [
                'GOOGLE_API_KEY',
                'OPENAI_API_KEY', 
                'ANTHROPIC_API_KEY',
                'PERPLEXITY_API_KEY',
                'OPENROUTER_API_KEY',
                'MISTRAL_API_KEY',
                'XAI_API_KEY'
            ]
            
            for key in api_keys:
                if os.getenv(key):
                    logger.info(f"AI services available using {key}")
                    return True
            
            logger.info("No AI API keys found - using fallback mode")
            return False
        except:
            return False
    
    async def _generate_fallback_dashboard(self, file_data: bytes, filename: str) -> Dict[str, Any]:
        """Generate dashboard using rule-based analysis when AI is not available."""
        try:
            logger.info("\n" + "=" * 80)
            logger.info("STARTING AI DASHBOARD GENERATION PROCESS")
            logger.info("=" * 80)
            
            logger.info(f"Dashboard Generation Request:")
            logger.info(f"   - Filename: {filename}")
            logger.info(f"   - File Size: {len(file_data)} bytes ({len(file_data)/1024/1024:.2f} MB)")
            logger.info(f"   - Generation Mode: Rule-based analysis (AI fallback)")
            
            # Parse Excel file
            excel_data = await self._parse_excel_file(file_data, filename)
            
            # Get the primary dataframe
            primary_sheet = None
            primary_df = None
            
            for sheet_name, df in excel_data['sheets'].items():
                if df is not None and len(df) > 0:
                    primary_sheet = sheet_name
                    primary_df = df
                    break
            
            if primary_df is None:
                raise ValueError("No valid data sheets found in Excel file")
            
            logger.info(f"\nPRIMARY DATA SOURCE SELECTED:")
            logger.info(f"   - Sheet Name: '{primary_sheet}'")
            logger.info(f"   - Data Shape: {len(primary_df)} rows × {len(primary_df.columns)} columns")
            logger.info(f"   - Memory Usage: {primary_df.memory_usage(deep=True).sum() / 1024:.2f} KB")
            
            # Enhanced intelligent analysis of data structure
            logger.info(f"Analyzing data structure. Columns: {list(primary_df.columns)}")
            
            # Smart column classification
            column_analysis = self._analyze_column_types(primary_df)
            numeric_cols = column_analysis['numeric']
            categorical_cols = column_analysis['categorical'] 
            date_cols = column_analysis['date']
            business_cols = column_analysis['business_context']
            
            logger.info(f"Column analysis - Numeric: {numeric_cols}, Categorical: {categorical_cols}, Date: {date_cols}")
            logger.info(f"Business context detected: {business_cols}")
            
            # Generate intelligent charts based on business context
            charts = self._generate_intelligent_charts(primary_df, numeric_cols, categorical_cols, date_cols, business_cols)
            
            # Generate intelligent KPIs based on business context
            kpis = self._generate_intelligent_kpis(primary_df, numeric_cols, business_cols)
            
            logger.info(f"\nFINAL DASHBOARD ASSEMBLY:")
            logger.info(f"   - Charts Generated: {len(charts)}")
            logger.info(f"   - KPIs Generated: {len(kpis)}")
            logger.info(f"   - Chart Types: {[chart.get('chart_type', 'unknown') for chart in charts]}")
            logger.info(f"   - Average Chart Confidence: {sum(chart.get('confidence', 0) for chart in charts) / max(len(charts), 1):.2f}")
            
            # Build dashboard configuration
            dashboard_config = {
                "title": f"Dashboard: {filename}",
                "description": f"Automated analysis of {primary_sheet}",
                "layout": {
                    "columns": 2,
                    "responsive": True,
                    "chartHeight": 400
                },
                "theme": {
                    "primaryColor": "#1f77b4",
                    "secondaryColor": "#ff7f0e",
                    "backgroundColor": "#ffffff",
                    "textColor": "#333333"
                },
                "charts": charts,
                "kpis": kpis,
                "insights": {
                    "summary": f"Analysis of {len(primary_df)} records with {len(numeric_cols)} numeric metrics and {len(categorical_cols)} categorical dimensions.",
                    "data_source": {
                        "filename": filename,
                        "primary_sheet": primary_sheet,
                        "rows": len(primary_df),
                        "columns": len(primary_df.columns)
                    },
                    "note": "Dashboard generated using rule-based analysis. Enable AI features for advanced insights."
                }
            }
            
            logger.info(f"Successfully generated fallback dashboard with {len(charts)} charts")
            return dashboard_config
            
        except Exception as e:
            logger.error(f"Fallback dashboard generation failed: {str(e)}")
            raise

    async def _parse_excel_file(self, file_data: bytes, filename: str) -> Dict[str, Any]:
        """Parse Excel file and extract all sheets with intelligent layout detection."""
        try:
            import tempfile
            import os
            from src.services.excel_layout_analyzer import ExcelLayoutAnalyzer
            
            # Save to temp file for layout analyzer
            with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp_file:
                tmp_file.write(file_data)
                tmp_path = tmp_file.name
            
            try:
                # Read all sheets
                excel_file = pd.ExcelFile(io.BytesIO(file_data))
                sheets = {}
                analyzer = ExcelLayoutAnalyzer()
                
                for sheet_name in excel_file.sheet_names:
                    try:
                        # Use layout analyzer for intelligent parsing
                        normalized_result = analyzer.analyze_and_normalize(tmp_path, sheet_name)
                        df = normalized_result.dataframe
                        
                        # Basic data cleaning
                        df = df.dropna(how='all').dropna(axis=1, how='all')
                        sheets[sheet_name] = df
                        
                        logger.info(f"Loaded sheet '{sheet_name}': {len(df)} rows × {len(df.columns)} columns")
                        logger.info(f"  Layout: {normalized_result.original_layout} "
                                  f"(confidence: {normalized_result.confidence:.1f}%)")
                        if normalized_result.transformations_applied:
                            logger.info(f"  Transformations: {', '.join(normalized_result.transformations_applied)}")
                            
                    except Exception as e:
                        logger.warning(f"Layout analyzer failed for sheet '{sheet_name}', using standard read: {str(e)}")
                        # Fallback to standard pandas read
                        try:
                            df = pd.read_excel(excel_file, sheet_name=sheet_name)
                            df = df.dropna(how='all').dropna(axis=1, how='all')
                            sheets[sheet_name] = df
                            logger.info(f"Loaded sheet '{sheet_name}' (fallback): {len(df)} rows × {len(df.columns)} columns")
                        except Exception as fallback_e:
                            logger.warning(f"Failed to load sheet '{sheet_name}': {str(fallback_e)}")
                            continue
            finally:
                # Clean up temp file
                try:
                    os.unlink(tmp_path)
                except:
                    pass
            
            return {
                'filename': filename,
                'sheets': sheets,
                'sheet_names': list(sheets.keys())
            }
            
        except Exception as e:
            logger.error(f"Failed to parse Excel file: {str(e)}")
            raise
    
    def _analyze_column_types(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Intelligently analyze column types and business context from headers."""
        try:
            logger.info("=" * 80)
            logger.info("STARTING DETAILED COLUMN ANALYSIS")
            logger.info("=" * 80)
            
            analysis = {
                'numeric': [],
                'categorical': [],
                'date': [],
                'business_context': {}
            }
            
            # Business context patterns
            revenue_patterns = ['revenue', 'sales', 'income', 'amount', 'value', 'price', 'cost', 'total', 'sum', 'charge', 'billing', 'fee', 'profit', 'margin', 'earnings', 'money', 'dollar', 'payment', 'fare']
            quantity_patterns = ['quantity', 'qty', 'count', 'number', 'units', 'volume', 'capacity', 'load', 'weight', 'distance', 'miles', 'km', 'soc', 'level', 'percentage', '%', 'metric', 'measure', 'score', 'rating', 'hours', 'duration', 'length', 'height', 'width', 'size']
            location_patterns = ['location', 'region', 'city', 'state', 'country', 'area', 'zone', 'hub', 'branch', 'depot', 'station', 'terminal', 'route', 'stop', 'place', 'address', 'district', 'province']
            category_patterns = ['category', 'type', 'class', 'group', 'segment', 'department', 'division', 'vehicle', 'driver', 'operator', 'status', 'model', 'fleet', 'brand', 'variant', 'kind', 'classification', 'tier', 'grade']
            time_patterns = ['date', 'time', 'month', 'year', 'day', 'week', 'period', 'quarter', 'hour', 'minute', 'timestamp', 'schedule', 'arrival', 'departure', 'start', 'end', 'duration', 'created', 'updated', 'modified']
            id_patterns = ['id', 'key', 'code', 'ref', 'reference', 'vin', 'license', 'plate', 'registration', 'uuid', 'guid', 'identifier']
            serial_patterns = ['s.no', 'sno', 'sr.no', 'srno', 'serial', 'index', 'row', 'seq', 'sequence', 'no.', 'num', '#']
            
            for col in df.columns:
                col_lower = str(col).lower().strip()
                col_data = df[col]
                
                # Skip serial number columns
                is_serial_number = False
                if any(pattern in col_lower for pattern in serial_patterns):
                    is_serial_number = True
                elif col_data.dtype in ['int64', 'float64']:
                    unique_count = col_data.nunique()
                    total_rows = len(col_data.dropna())
                    if total_rows > 0:
                        min_val = col_data.min()
                        max_val = col_data.max()
                        if (unique_count == total_rows and min_val == 1 and max_val == total_rows) or \
                           (unique_count > total_rows * 0.95 and min_val <= 1):
                            is_serial_number = True
                
                if is_serial_number:
                    analysis['business_context'][col] = 'serial_number'
                    continue
                
                # Classify meaningful columns - Enhanced numeric detection
                is_numeric_column = False
                
                if col_data.dtype in ['int64', 'float64']:
                    is_numeric_column = True
                elif col_data.dtype == 'object':
                    # Smart numeric detection for object columns
                    # Check if column contains mostly numeric values
                    sample_values = col_data.dropna().head(20)
                    if len(sample_values) > 0:
                        # Try to convert sample to numeric, count successful conversions
                        converted_count = 0
                        for val in sample_values:
                            try:
                                # Clean common non-numeric symbols first
                                clean_val = str(val).replace('—', '').replace('–', '').replace('-', '').strip()
                                if clean_val and clean_val.lower() not in ['nan', 'null', 'none', '']:
                                    float(clean_val)
                                    converted_count += 1
                            except:
                                continue
                        
                        # If >70% of sample values can be converted to numeric, treat as numeric
                        if converted_count / len(sample_values) > 0.7:
                            is_numeric_column = True
                            logger.info(f"   Detected '{col}' as numeric column (object type with {converted_count}/{len(sample_values)} numeric values)")
                
                if is_numeric_column:
                    analysis['numeric'].append(col)
                    
                    if any(pattern in col_lower for pattern in revenue_patterns):
                        analysis['business_context'][col] = 'revenue'
                    elif any(pattern in col_lower for pattern in quantity_patterns):
                        analysis['business_context'][col] = 'quantity'
                    else:
                        analysis['business_context'][col] = 'metric'
                        
                elif col_data.dtype == 'object':
                    # Enhanced date detection
                    is_date_column = False
                    if any(pattern in col_lower for pattern in time_patterns):
                        # Try multiple date parsing approaches
                        sample_data = col_data.dropna().head(10)
                        if len(sample_data) > 0:
                            date_success_count = 0
                            for sample_val in sample_data:
                                try:
                                    # Try different date parsing methods
                                    sample_str = str(sample_val).strip()
                                    if sample_str and sample_str.lower() not in ['nan', 'null', 'none', '']:
                                        # Try pandas to_datetime with multiple formats
                                        pd.to_datetime(sample_str, errors='raise')
                                        date_success_count += 1
                                except:
                                    try:
                                        # Try with different date formats
                                        from datetime import datetime
                                        # Common date formats
                                        date_formats = [
                                            '%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', 
                                            '%Y-%m-%d %H:%M:%S', '%m/%d/%Y %H:%M:%S',
                                            '%d-%m-%Y', '%Y/%m/%d', '%d.%m.%Y'
                                        ]
                                        for fmt in date_formats:
                                            try:
                                                datetime.strptime(sample_str, fmt)
                                                date_success_count += 1
                                                break
                                            except:
                                                continue
                                    except:
                                        continue
                            
                            # If >60% of samples can be parsed as dates, treat as date column
                            if date_success_count / len(sample_data) > 0.6:
                                is_date_column = True
                                logger.info(f"   Detected '{col}' as date column ({date_success_count}/{len(sample_data)} valid dates)")
                    
                    if is_date_column:
                        analysis['date'].append(col)
                        analysis['business_context'][col] = 'temporal'
                    else:
                        analysis['categorical'].append(col)
                        if any(pattern in col_lower for pattern in location_patterns):
                            analysis['business_context'][col] = 'location'
                        elif any(pattern in col_lower for pattern in category_patterns):
                            analysis['business_context'][col] = 'category'
                        elif any(pattern in col_lower for pattern in id_patterns):
                            analysis['business_context'][col] = 'identifier'
                        else:
                            analysis['business_context'][col] = 'categorical'
                            
                elif col_data.dtype in ['datetime64[ns]', 'datetime64']:
                    analysis['date'].append(col)
                    analysis['business_context'][col] = 'temporal'
                    logger.info(f"   Detected '{col}' as datetime column (dtype: {col_data.dtype})")
            
            logger.info(f"\nFINAL COLUMN ANALYSIS SUMMARY:")
            # Use safe logging for column names with Unicode characters
            safe_numeric = [safe_log_string(col) for col in analysis['numeric']]
            safe_categorical = [safe_log_string(col) for col in analysis['categorical']]
            safe_date = [safe_log_string(col) for col in analysis['date']]
            logger.info(f"   Numeric Columns ({len(analysis['numeric'])}): {safe_numeric}")
            logger.info(f"   Categorical Columns ({len(analysis['categorical'])}): {safe_categorical}")
            logger.info(f"   Date Columns ({len(analysis['date'])}): {safe_date}")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Column analysis failed: {str(e)}")
            # Fallback analysis
            return {
                'numeric': df.select_dtypes(include=[np.number]).columns.tolist(),
                'categorical': df.select_dtypes(include=['object']).columns.tolist(),
                'date': [col for col in df.columns if 'date' in str(col).lower() or 'time' in str(col).lower()],
                'business_context': {}
            }
    
    def _generate_intelligent_charts(self, df: pd.DataFrame, numeric_cols: List[str], 
                                   categorical_cols: List[str], date_cols: List[str], 
                                   business_cols: Dict[str, str]) -> List[Dict[str, Any]]:
        """Generate charts intelligently based on business context and data patterns."""
        charts = []
        
        try:
            logger.info("\n" + "=" * 70)
            logger.info("STARTING INTELLIGENT CHART GENERATION")
            logger.info("=" * 70)
            
            # Categorize columns by business context
            revenue_cols = [col for col, context in business_cols.items() if context == 'revenue']
            location_cols = [col for col, context in business_cols.items() if context == 'location']
            category_cols = [col for col, context in business_cols.items() if context == 'category']
            temporal_cols = [col for col, context in business_cols.items() if context == 'temporal']
            
            # Priority 1: Revenue by location bar chart
            if revenue_cols and location_cols:
                revenue_col = revenue_cols[0]
                location_col = location_cols[0]
                
                location_revenue = df.groupby(location_col)[revenue_col].sum().sort_values(ascending=False).head(10)
                location_data = [
                    {"name": str(location), "value": float(revenue)}
                    for location, revenue in location_revenue.items()
                ]
                
                chart = {
                    "chart_type": "bar",
                    "title": f"Revenue by {location_col}",
                    "description": f"Revenue breakdown across different {location_col.lower()}s",
                    "data_columns": ["name", "value"],
                    "confidence": 0.95,
                    "data": location_data,
                    "recharts_config": {
                        "type": "BarChart",
                        "dataKey": "value",
                        "xAxisKey": "name",
                        "height": 350,
                        "margin": {"top": 20, "right": 30, "left": 20, "bottom": 60}
                    }
                }
                charts.append(chart)
            
            # Priority 2: General bar charts
            if numeric_cols and categorical_cols:
                num_col = numeric_cols[0]
                cat_col = categorical_cols[0]
                
                # Clean and convert numeric data before aggregation
                df_clean = df.copy()
                
                # Convert numeric column to actual numeric values, handling mixed types
                if df_clean[num_col].dtype == 'object':
                    # Clean the numeric column: replace symbols with 0 and convert to numeric
                    df_clean[num_col] = df_clean[num_col].replace(['—', '–', 'N/A', 'n/a', 'NA', '', 'null', 'None'], '0')
                    df_clean[num_col] = cast(pd.Series, pd.to_numeric(df_clean[num_col], errors='coerce')).fillna(0)
                
                top_performers = df_clean.groupby(cat_col)[num_col].sum().sort_values(ascending=False).head(10)
                performer_data = [
                    {"name": str(name), "value": float(value)}
                    for name, value in top_performers.items()
                ]
                
                chart = {
                    "chart_type": "bar",
                    "title": f"Top {cat_col} by {num_col}",
                    "description": f"Highest performing {cat_col.lower()}s based on {num_col.lower()}",
                    "data_columns": ["name", "value"],
                    "confidence": 0.85,
                    "data": performer_data,
                    "recharts_config": {
                        "type": "BarChart",
                        "dataKey": "value",
                        "xAxisKey": "name",
                        "height": 350,
                        "margin": {"top": 20, "right": 30, "left": 20, "bottom": 60}
                    }
                }
                charts.append(chart)
            
            # Priority 3: Time series if available
            if temporal_cols and numeric_cols:
                time_col = temporal_cols[0]
                metric_col = numeric_cols[0]
                
                try:
                    df_temp = df.copy()
                    if df_temp[time_col].dtype == 'object':
                        df_temp[time_col] = pd.to_datetime(df_temp[time_col], errors='coerce')
                    
                    time_series = df_temp.groupby(df_temp[time_col].dt.to_period('M'))[metric_col].sum().reset_index()
                    time_series[time_col] = time_series[time_col].astype(str)
                    
                    time_data = [
                        {"period": str(period), "value": float(value)}
                        for period, value in zip(time_series[time_col], time_series[metric_col])
                    ]
                    
                    chart = {
                        "chart_type": "line",
                        "title": f"{metric_col} Trend Over Time",
                        "description": f"Time series analysis of {metric_col.lower()} trends",
                        "data_columns": ["period", "value"],
                        "confidence": 0.88,
                        "data": time_data,
                        "recharts_config": {
                            "type": "LineChart",
                            "dataKey": "value",
                            "xAxisKey": "period",
                            "height": 350,
                            "margin": {"top": 20, "right": 30, "left": 20, "bottom": 60}
                        }
                    }
                    charts.append(chart)
                except Exception as e:
                    logger.warning(f"Failed to generate time series chart: {e}")
            
            logger.info(f"\nCHART GENERATION COMPLETED:")
            logger.info(f"   - Total Charts Generated: {len(charts)}")
            logger.info(f"   - Chart Types: {[chart.get('chart_type', 'unknown') for chart in charts]}")
            
            return charts
            
        except Exception as e:
            logger.error(f"Chart generation failed: {str(e)}")
            return []
    
    def _generate_intelligent_kpis(self, df: pd.DataFrame, numeric_cols: List[str], 
                                 business_cols: Dict[str, str], user_preferences: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Generate intelligent KPIs based on business context, data patterns, and user preferences."""
        try:
            logger.info("\n" + "=" * 60)
            logger.info("STARTING INTELLIGENT KPI GENERATION")
            logger.info("=" * 60)
            
            # Check if user has specific preferences for KPIs
            if user_preferences and (user_preferences.get('user_question') or user_preferences.get('specific_questions')):
                logger.info("Generating context-aware KPIs based on user request")
                return self._generate_preference_based_kpis(df, user_preferences, numeric_cols, business_cols)
            
            kpis = []
            
            # Categorize numeric columns by business context
            revenue_cols = [col for col, context in business_cols.items() if context == 'revenue']
            quantity_cols = [col for col, context in business_cols.items() if context == 'quantity']
            metric_cols = [col for col, context in business_cols.items() if context == 'metric']
            
            # Revenue KPIs
            for col in revenue_cols[:2]:
                try:
                    # Clean data before calculations
                    df_temp = df.copy()
                    df_temp[col] = df_temp[col].astype(str).replace(['—', '–', '-', 'nan', 'NaN', 'null', 'NULL', ''], '0')
                    df_temp[col] = pd.to_numeric(df_temp[col], errors='coerce')
                    
                    total_revenue = df_temp[col].sum()
                    avg_revenue = df_temp[col].mean()
                    
                    kpi = {
                        "id": f"kpi_total_{str(col).lower().replace(' ', '_')}",
                        "title": f"Total {col}",
                        "value": f"{total_revenue:,.0f}",
                        "description": f"Total {col.lower()} across all entries",
                        "trend": "neutral",
                        "change": f"Avg: {avg_revenue:,.0f}"
                    }
                    kpis.append(kpi)
                except Exception as e:
                    logger.warning(f"Failed to generate KPI for revenue column '{col}': {e}")
            
            # Quantity KPIs
            for col in quantity_cols[:2]:
                try:
                    # Clean data before calculations
                    df_temp = df.copy()
                    df_temp[col] = df_temp[col].astype(str).replace(['—', '–', '-', 'nan', 'NaN', 'null', 'NULL', ''], '0')
                    df_temp[col] = pd.to_numeric(df_temp[col], errors='coerce')
                    
                    total_qty = df_temp[col].sum()
                    avg_qty = df_temp[col].mean()
                    
                    kpi = {
                        "id": f"kpi_total_{str(col).lower().replace(' ', '_')}",
                        "title": f"Total {col}",
                        "value": f"{total_qty:,.0f}",
                        "description": f"Total {col.lower()} across all entries",
                        "trend": "neutral",
                        "change": f"Avg: {avg_qty:.1f}"
                    }
                    kpis.append(kpi)
                except Exception as e:
                    logger.warning(f"Failed to generate KPI for quantity column '{col}': {e}")
            
            # Record count KPI
            total_records = len(df)
            record_kpi = {
                "id": "kpi_total_records",
                "title": "Total Records",
                "value": f"{total_records:,}",
                "description": "Number of data entries",
                "trend": "neutral",
                "change": f"{len(df.columns)} columns"
            }
            kpis.append(record_kpi)
            
            logger.info(f"\nKPI GENERATION COMPLETED:")
            logger.info(f"   - Total KPIs Generated: {len(kpis)}")
            
            return kpis[:6]
            
        except Exception as e:
            logger.error(f"KPI generation failed: {str(e)}")
            return []

    def _generate_preference_based_kpis(self, df: pd.DataFrame, user_preferences: Dict[str, Any],
                                      numeric_cols: List[str], business_cols: Dict[str, str]) -> List[Dict[str, Any]]:
        """Generate KPIs based on user's specific question/request."""
        try:
            logger.info("\n" + "=" * 50)
            logger.info("GENERATING PREFERENCE-BASED KPIs")
            logger.info("=" * 50)
            
            kpis = []
            
            # Get user question from either format
            user_question = user_preferences.get('user_question', '')
            if not user_question and user_preferences.get('specific_questions'):
                # Take the first specific question
                specific_questions = user_preferences.get('specific_questions', [])
                if specific_questions:
                    user_question = specific_questions[0] if isinstance(specific_questions, list) else str(specific_questions)
            
            user_question = user_question.lower() if user_question else ''
            
            logger.info(f"User question: {safe_log_string(user_question)}")
            
            # Parse the user's request to extract what they want to analyze
            metric_column = None
            dimension_column = None
            
            # Use enhanced column matching for metric detection
            metric_keywords = ['energy delivered', 'energy', 'total units', 'units', 'cost', 'revenue', 'amount', 'kwh']
            for keyword in metric_keywords:
                if keyword in user_question:
                    metric_column = self._find_best_column_match(keyword, df.columns.tolist(), "metric")
                    if metric_column:
                        logger.info(f"Identified metric column: {safe_log_string(metric_column)}")
                        break
            
            # Use enhanced column matching for dimension detection
            dimension_keywords = ['rating', 'category', 'type', 'vehicle', 'way', 'location', 'station']
            for keyword in dimension_keywords:
                if keyword in user_question:
                    dimension_column = self._find_best_column_match(keyword, df.columns.tolist(), "dimension")
                    if dimension_column and dimension_column != metric_column:
                        logger.info(f"Identified dimension column: {safe_log_string(dimension_column)}")
                        break
            
            # Fallback: if no dimension found but we have a metric, try to find any categorical column
            if metric_column and not dimension_column:
                categorical_cols_list = [col for col in df.columns if not pd.api.types.is_numeric_dtype(df[col])]
                if categorical_cols_list:
                    dimension_column = categorical_cols_list[0]
                    logger.info(f"Using fallback dimension column: {safe_log_string(dimension_column)}")
            
            # Generate contextual KPIs based on identified columns
            if metric_column:
                # Clean the metric data
                df_temp = df.copy()
                df_temp[metric_column] = df_temp[metric_column].astype(str).replace(['—', '–', '-', 'nan', 'NaN', 'null', 'NULL', ''], '0')
                df_temp[metric_column] = pd.to_numeric(df_temp[metric_column], errors='coerce')
                df_temp = df_temp.dropna(subset=[metric_column])
                
                if len(df_temp) > 0:
                    # Total KPI
                    total_value = df_temp[metric_column].sum()
                    kpi_total = {
                        "id": f"kpi_total_{metric_column.lower().replace(' ', '_').replace('(', '').replace(')', '')}",
                        "title": f"Total {metric_column}",
                        "value": f"{total_value:,.2f}" if total_value < 1000 else f"{total_value:,.0f}",
                        "description": f"Total {metric_column.lower()} across all records",
                        "trend": "neutral",
                        "change": f"Records: {len(df_temp):,}"
                    }
                    kpis.append(kpi_total)
                    
                    # Average KPI
                    avg_value = df_temp[metric_column].mean()
                    kpi_avg = {
                        "id": f"kpi_avg_{metric_column.lower().replace(' ', '_').replace('(', '').replace(')', '')}",
                        "title": f"Average {metric_column}",
                        "value": f"{avg_value:,.2f}" if avg_value < 1000 else f"{avg_value:,.0f}",
                        "description": f"Average {metric_column.lower()} per record",
                        "trend": "neutral",
                        "change": f"Max: {df_temp[metric_column].max():,.0f}"
                    }
                    kpis.append(kpi_avg)
                    
                    # If dimension column exists, add dimension-specific KPIs
                    if dimension_column and dimension_column in df_temp.columns:
                        # Unique values count
                        unique_count = df_temp[dimension_column].nunique()
                        kpi_unique = {
                            "id": f"kpi_unique_{dimension_column.lower().replace(' ', '_')}",
                            "title": f"Unique {dimension_column}",
                            "value": f"{unique_count:,}",
                            "description": f"Number of unique {dimension_column.lower()} values",
                            "trend": "neutral",
                            "change": f"Categories"
                        }
                        kpis.append(kpi_unique)
                        
                        # Top performer KPI
                        top_performer = df_temp.groupby(dimension_column)[metric_column].sum().idxmax()
                        top_value = df_temp.groupby(dimension_column)[metric_column].sum().max()
                        kpi_top = {
                            "id": f"kpi_top_{dimension_column.lower().replace(' ', '_')}",
                            "title": f"Top {dimension_column}",
                            "value": str(top_performer)[:20] + ("..." if len(str(top_performer)) > 20 else ""),
                            "description": f"Highest {metric_column.lower()} by {dimension_column.lower()}",
                            "trend": "positive",
                            "change": f"{top_value:,.0f}"
                        }
                        kpis.append(kpi_top)
            
            # If no specific columns identified, add general summary KPIs
            if not kpis:
                logger.info("No specific columns identified, generating general summary KPIs")
                
                # Total records
                total_records = len(df)
                kpi_records = {
                    "id": "kpi_total_records",
                    "title": "Total Records",
                    "value": f"{total_records:,}",
                    "description": "Total number of data entries",
                    "trend": "neutral",
                    "change": f"{len(df.columns)} columns"
                }
                kpis.append(kpi_records)
                
                # Add first numeric column summary if available
                if numeric_cols:
                    first_num_col = numeric_cols[0]
                    df_temp = df.copy()
                    df_temp[first_num_col] = pd.to_numeric(df_temp[first_num_col], errors='coerce')
                    df_temp = df_temp.dropna(subset=[first_num_col])
                    
                    if len(df_temp) > 0:
                        total_val = df_temp[first_num_col].sum()
                        kpi_summary = {
                            "id": f"kpi_summary_{first_num_col.lower().replace(' ', '_')}",
                            "title": f"Total {first_num_col}",
                            "value": f"{total_val:,.0f}",
                            "description": f"Summary of {first_num_col.lower()}",
                            "trend": "neutral",
                            "change": f"Avg: {df_temp[first_num_col].mean():,.0f}"
                        }
                        kpis.append(kpi_summary)
            
            logger.info(f"Generated {len(kpis)} preference-based KPIs")
            logger.info(f"KPIs: {[kpi['title'] for kpi in kpis]}")
            
            return kpis[:6]  # Limit to 6 KPIs
            
        except Exception as e:
            logger.error(f"Preference-based KPI generation failed: {str(e)}")
            # Fallback to simple record count
            return [{
                "id": "kpi_fallback_records",
                "title": "Total Records",
                "value": f"{len(df):,}",
                "description": "Number of data entries",
                "trend": "neutral",
                "change": "Data available"
            }]
    
    async def _generate_single_sheet_dashboard(self, excel_data: Dict[str, Any], filename: str, file_data: bytes = None) -> Dict[str, Any]:
        """Generate dashboard from primary sheet only (legacy behavior)."""
        try:
            # Get the primary dataframe for analysis
            primary_sheet = None
            primary_df = None
            
            # Find the best sheet for analysis
            for sheet_name, df in excel_data['sheets'].items():
                if df is not None and len(df) > 0:
                    primary_sheet = sheet_name
                    primary_df = df
                    break
            
            if primary_df is None:
                raise ValueError("No valid data sheets found in Excel file")
            
            logger.info(f"Using sheet '{primary_sheet}' with {len(primary_df)} rows for analysis")
            
            # Check if AI is available
            ai_available = self._check_ai_availability()
                    
            if ai_available:
                logger.info("AI available - attempting enhanced analytics")
                
                try:
                    from src.services.enhanced_analytics_engine import EnhancedAnalyticsEngine
                    enhanced_engine = EnhancedAnalyticsEngine()
                    
                    dashboard_config = await enhanced_engine.analyze_and_generate_enhanced_dashboard(
                        primary_df, filename, f"Excel data analysis for {primary_sheet}", fast_mode=True
                    )
                    
                    dashboard_config["insights"]["data_source"] = {
                        "filename": filename,
                        "primary_sheet": primary_sheet,
                        "rows": len(primary_df),
                        "columns": len(primary_df.columns),
                        "analysis_engine": "enhanced_ai_analytics"
                    }
                    
                    logger.info("Successfully generated enhanced AI dashboard")
                    return dashboard_config
                    
                except Exception as e:
                    logger.warning(f"Enhanced analytics failed, falling back: {str(e)}")
                    
            else:
                logger.info("AI not available, using rule-based dashboard generation")
                
            return await self._generate_fallback_dashboard(file_data, filename)

        except Exception as e:
            logger.error(f"Dashboard generation failed: {str(e)}")
            return await self._generate_fallback_dashboard(file_data, filename)
    
    async def _generate_multi_sheet_dashboard(self, excel_data: Dict[str, Any], filename: str) -> Dict[str, Any]:
        """Generate dashboard with separate analysis for each Excel sheet."""
        try:
            logger.info(f"Generating multi-sheet dashboard for {len(excel_data['sheets'])} sheets")
            
            sheets_analysis = {}
            all_charts = []
            all_kpis = []
            total_rows = 0
            
            # Analyze each sheet separately
            for sheet_name, df in excel_data['sheets'].items():
                if df is None or len(df) == 0:
                    logger.warning(f"Skipping empty sheet: {sheet_name}")
                    continue
                
                logger.info(f"Analyzing sheet '{sheet_name}' with {len(df)} rows")
                total_rows += len(df)
                
                try:
                    # Basic analysis for each sheet
                    column_analysis = self._analyze_column_types(df)
                    charts = self._generate_intelligent_charts(
                        df, column_analysis['numeric'], column_analysis['categorical'], 
                        column_analysis['date'], column_analysis['business_context']
                    )
                    kpis = self._generate_intelligent_kpis(
                        df, column_analysis['numeric'], column_analysis['business_context'], None
                    )
                    
                    # Prefix titles with sheet name
                    for chart in charts:
                        chart['title'] = f"[{sheet_name}] {chart['title']}"
                        chart['sheet_source'] = sheet_name
                    
                    for kpi in kpis:
                        kpi['title'] = f"[{sheet_name}] {kpi['title']}"
                        kpi['sheet_source'] = sheet_name
                    
                    sheets_analysis[sheet_name] = {
                        "rows": len(df),
                        "columns": len(df.columns),
                        "charts_count": len(charts),
                        "kpis_count": len(kpis)
                    }
                    
                    all_charts.extend(charts)
                    all_kpis.extend(kpis)
                    
                except Exception as e:
                    logger.error(f"Failed to analyze sheet '{sheet_name}': {e}")
                    continue
            
            # Create comprehensive dashboard
            dashboard_config = {
                "title": f"Multi-Sheet Dashboard: {filename}",
                "description": f"Comprehensive analysis of {len(excel_data['sheets'])} sheets with {total_rows} total records",
                "layout": {
                    "type": "multi_sheet_grid",
                    "responsive": True,
                    "sheet_navigation": True
                },
                "theme": {
                    "name": "multi_sheet_modern",
                    "colors": {
                        "primary": "#2563eb",
                        "secondary": "#64748b", 
                        "accent": "#06b6d4",
                        "background": "#ffffff",
                        "surface": "#f8fafc"
                    }
                },
                "charts": all_charts,
                "kpis": all_kpis,
                "insights": {
                    "summary": f"Multi-sheet analysis reveals data across {len(excel_data['sheets'])} worksheets.",
                    "sheets_summary": sheets_analysis,
                    "data_source": {
                        "filename": filename,
                        "total_sheets": len(excel_data['sheets']),
                        "total_rows": total_rows,
                        "analysis_type": "multi_sheet"
                    }
                }
            }
            
            logger.info(f"Multi-sheet dashboard generated: {len(all_charts)} total charts, {len(all_kpis)} total KPIs")
            return dashboard_config
            
        except Exception as e:
            logger.error(f"Multi-sheet dashboard generation failed: {e}")
            return await self._generate_single_sheet_dashboard(excel_data, filename)

    async def generate_dashboard_from_dataframe(self, df: pd.DataFrame, filename: str = "dashboard", 
                                               user_preferences: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate a complete dashboard configuration from a dataframe."""
        try:
            logger.info(f"\nGENERATING DASHBOARD FROM DATAFRAME WITH USER PREFERENCES")
            logger.info(f"   - DataFrame Shape: {df.shape}")
            logger.info(f"   - Filename: {filename}")
            
            if user_preferences:
                logger.info("User Preferences Received:")
                # Use safe logging for preferences that might contain Unicode characters
                safe_prefs = {k: (safe_log_string(str(v)) if isinstance(v, (str, list)) else v) 
                             for k, v in user_preferences.items()}
                logger.info(f"   - Preferences: {safe_prefs}")
            
            # Analyze column types and business context
            column_analysis = self._analyze_column_types(df)
            numeric_cols = column_analysis['numeric']
            categorical_cols = column_analysis['categorical']
            date_cols = column_analysis['date']
            business_cols = column_analysis['business_context']
            
            # Use safe logging for column names with Unicode characters
            safe_columns = [safe_log_string(col) for col in df.columns.tolist()]
            safe_numeric = [safe_log_string(col) for col in numeric_cols]
            safe_categorical = [safe_log_string(col) for col in categorical_cols]
            safe_date = [safe_log_string(col) for col in date_cols]
            
            logger.info(f"Analyzing data structure. Columns: {safe_columns}")
            logger.info(f"Column analysis - Numeric: {safe_numeric}, Categorical: {safe_categorical}, Date: {safe_date}")
            # Skip business context logging since it contains complex dict with Unicode keys
            logger.info(f"Business context detected: {len(business_cols)} column mappings")
            
            # Check if we have multiple sheets in the data
            has_multiple_sheets = isinstance(df, dict) and 'sheets' in df
            
            if has_multiple_sheets:
                logger.info("Detected multiple sheets in data")
                return await self._generate_multi_sheet_dashboard(df, filename)
            
            # Generate charts based on user preferences if available
            charts = []
            
            # Special handling for Smart Metric Selector mode
            if user_preferences and user_preferences.get('smart_metric_mode'):
                logger.info("Smart Metric Selector mode - enhancing chart generation for selected metrics")
                charts = self._generate_smart_metric_charts(df, numeric_cols, categorical_cols, date_cols, business_cols, user_preferences)
            elif user_preferences and user_preferences.get('specific_questions'):
                # User has specific requests - only generate what they asked for
                logger.info("User has specific chart requests - generating only requested charts")
                charts = self._generate_preference_based_charts(df, user_preferences, numeric_cols, categorical_cols, date_cols, business_cols)
            elif user_preferences and user_preferences.get('preferred_chart_types'):
                # User has chart type preferences but no specific questions
                charts = self._generate_preference_based_charts(df, user_preferences, numeric_cols, categorical_cols, date_cols, business_cols)
                
                # Only add additional charts if user doesn't have specific requests
                if len(numeric_cols) > 1:
                    additional_charts = self._generate_correlation_charts(df, numeric_cols)
                    charts.extend(additional_charts)
                
                if date_cols and numeric_cols:
                    time_series_charts = self._generate_time_series_charts(df, date_cols[0], numeric_cols)
                    charts.extend(time_series_charts)
            else:
                # No specific preferences - generate intelligent defaults
                charts = self._generate_intelligent_charts(df, numeric_cols, categorical_cols, date_cols, business_cols)
            
            # Generate intelligent KPIs based on business context and user preferences
            kpis = self._generate_intelligent_kpis(df, numeric_cols, business_cols, user_preferences)
            
            logger.info(f"\nDASHBOARD GENERATED SUCCESSFULLY:")
            logger.info(f"   - Total Charts: {len(charts)}")
            logger.info(f"   - Total KPIs: {len(kpis)}")
            logger.info(f"   - User Requests Fulfilled: {len([c for c in charts if c.get('user_requested', False)])}")
            
            # Build dashboard configuration
            dashboard_config = {
                "title": f"Dashboard: {filename}",
                "description": f"Custom analysis based on user preferences" if user_preferences else f"Automated analysis of {filename}",
                "layout": {
                    "columns": min(3, max(2, len(charts) // 2)),  # Dynamic columns based on chart count
                    "responsive": True,
                    "chartHeight": 400,
                    "chartSpacing": 20
                },
                "theme": {
                    "primaryColor": "#1f77b4",
                    "secondaryColor": "#ff7f0e",
                    "backgroundColor": "#ffffff",
                    "textColor": "#333333"
                },
                "charts": charts,
                "kpis": kpis,
                "insights": {
                    "summary": f"Analysis of {len(df)} records with {len(numeric_cols)} numeric metrics and {len(categorical_cols)} categorical dimensions.",
                    "data_source": {
                        "filename": filename,
                        "rows": len(df),
                        "columns": len(df.columns),
                        "analysis_engine": "preference_based" if user_preferences else "rule_based",
                        "has_multiple_sheets": has_multiple_sheets
                    },
                    "user_preferences": user_preferences if user_preferences else {}
                }
            }
            
            logger.info(f"Successfully generated dashboard with {len(charts)} charts")
            return dashboard_config
            
        except Exception as e:
            logger.error(f"Dashboard generation from dataframe failed: {str(e)}")
            raise

    def _generate_correlation_charts(self, df: pd.DataFrame, numeric_cols: List[str]) -> List[Dict[str, Any]]:
        """Generate correlation charts between numeric columns."""
        charts = []
        try:
            # Generate scatter plots for numeric column pairs
            for i in range(len(numeric_cols)):
                for j in range(i + 1, len(numeric_cols)):
                    col1, col2 = numeric_cols[i], numeric_cols[j]
                    
                    # Clean and prepare data
                    df_temp = df.copy()
                    df_temp[col1] = pd.to_numeric(df_temp[col1], errors='coerce')
                    df_temp[col2] = pd.to_numeric(df_temp[col2], errors='coerce')
                    
                    # Remove rows with NaN values
                    df_temp = df_temp.dropna(subset=[col1, col2])
                    
                    if len(df_temp) > 0:
                        scatter_data = [
                            {"x": float(x), "y": float(y)}
                            for x, y in zip(df_temp[col1], df_temp[col2])
                        ]
                        
                        chart = {
                            "chart_type": "scatter",
                            "title": f"Correlation: {col1} vs {col2}",
                            "description": f"Scatter plot showing relationship between {col1} and {col2}",
                            "data_columns": ["x", "y"],
                            "confidence": 0.85,
                            "data": scatter_data,
                            "recharts_config": {
                                "type": "ScatterChart",
                                "dataKey": "y",
                                "xAxisKey": "x",
                                "height": 400,
                                "margin": {"top": 20, "right": 30, "left": 20, "bottom": 60},
                                "fill": "#8884d8"
                            }
                        }
                        charts.append(chart)
            
            return charts
        except Exception as e:
            logger.error(f"Correlation chart generation failed: {str(e)}")
            return []

    def _generate_time_series_charts(self, df: pd.DataFrame, date_col: str, numeric_cols: List[str]) -> List[Dict[str, Any]]:
        """Generate time series charts for numeric columns."""
        charts = []
        try:
            # Convert date column to datetime
            df_temp = df.copy()
            df_temp[date_col] = pd.to_datetime(df_temp[date_col], errors='coerce')
            
            # Generate time series for each numeric column
            for num_col in numeric_cols:
                # Clean numeric data
                df_temp[num_col] = pd.to_numeric(df_temp[num_col], errors='coerce')
                
                # Group by date and calculate mean
                time_series = df_temp.groupby(df_temp[date_col].dt.to_period('D'))[num_col].mean().reset_index()
                time_series[date_col] = time_series[date_col].astype(str)
                
                time_data = [
                    {"date": str(date), "value": float(value)}
                    for date, value in zip(time_series[date_col], time_series[num_col])
                ]
                
                if time_data:
                    chart = {
                        "chart_type": "line",
                        "title": f"{num_col} Over Time",
                        "description": f"Time series analysis of {num_col}",
                        "data_columns": ["date", "value"],
                        "confidence": 0.85,
                        "data": time_data,
                        "recharts_config": {
                            "type": "LineChart",
                            "dataKey": "value",
                            "xAxisKey": "date",
                            "height": 400,
                            "margin": {"top": 20, "right": 30, "left": 20, "bottom": 60},
                            "stroke": "#8884d8",
                            "dot": {"r": 4},
                            "activeDot": {"r": 6}
                        }
                    }
                    charts.append(chart)
            
            return charts
        except Exception as e:
            logger.error(f"Time series chart generation failed: {str(e)}")
            return []

    def _generate_smart_metric_charts(self, df: pd.DataFrame, numeric_cols: List[str], 
                                     categorical_cols: List[str], date_cols: List[str], 
                                     business_cols: Dict[str, str], 
                                     user_preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate charts specifically for Smart Metric Selector mode with enhanced column detection and paired analysis."""
        charts = []
        try:
            logger.info("Generating charts for Smart Metric Selector mode")
            
            # Get all available columns (including those not detected as categorical)
            all_columns = df.columns.tolist()
            
            # Re-analyze columns with more lenient criteria for Smart Metric mode
            enhanced_categorical = categorical_cols.copy()
            enhanced_numeric = numeric_cols.copy()
            
            # Enhanced column detection for Smart Metric mode
            for col in all_columns:
                if col not in enhanced_numeric and col not in enhanced_categorical and col not in date_cols:
                    # Try to convert to numeric first
                    try:
                        pd.to_numeric(df[col], errors='raise')
                        enhanced_numeric.append(col)
                        logger.info(f"Enhanced detection: '{col}' treated as numeric for Smart Metric mode")
                    except:
                        # Check if it can work as categorical
                        unique_count = df[col].nunique()
                        total_rows = len(df.dropna())
                        
                        # If column has reasonable number of unique values (not too many), treat as categorical
                        if unique_count < total_rows * 0.8 and unique_count > 1:
                            enhanced_categorical.append(col)
                            logger.info(f"Enhanced detection: '{col}' treated as categorical for Smart Metric mode")
            
            # ========= PRIORITY: PROCESS METRIC PAIRS IF PROVIDED =========
            metric_pairs = user_preferences.get('metric_pairs', [])
            
            if metric_pairs:
                logger.info(f"Processing {len(metric_pairs)} metric pairs from user preferences")
                
                for i, pair in enumerate(metric_pairs):
                    try:
                        # Extract column names from pair
                        x_col = pair.get('xAxis')
                        y_col = pair.get('yAxis')
                        chart_type = pair.get('chartType', 'auto')
                        pair_id = pair.get('id', f"pair_{i}")
                        pair_name = pair.get('name', f"{x_col} vs {y_col}")
                        
                        logger.info(f"Processing metric pair {i+1}: {pair_name} ({x_col} -> {y_col}, type: {chart_type})")
                        
                        # Validate columns exist in dataframe
                        if x_col not in df.columns:
                            logger.warning(f"X-axis column '{x_col}' not found in dataframe")
                            continue
                        if y_col not in df.columns:
                            logger.warning(f"Y-axis column '{y_col}' not found in dataframe")
                            continue
                        
                        # Generate chart for this specific pair
                        chart = self._generate_chart_for_metric_pair(
                            df, x_col, y_col, chart_type, 
                            enhanced_numeric, enhanced_categorical, date_cols, 
                            pair_id
                        )
                        
                        if chart:
                            # Override title with custom name if provided
                            if pair_name and pair_name != f"{x_col} vs {y_col}":
                                chart['title'] = pair_name
                            
                            charts.append(chart)
                            logger.info(f"Successfully generated chart for pair: {pair_name}")
                        else:
                            logger.warning(f"Failed to generate chart for pair: {pair_name}")
                    
                    except Exception as e:
                        logger.error(f"Error processing metric pair {i}: {str(e)}")
                        continue
                
                logger.info(f"Generated {len(charts)} charts from {len(metric_pairs)} metric pairs")
                return charts
            
            # ========= FALLBACK: LEGACY BEHAVIOR FOR EXACTLY 2 SELECTED METRICS =========
            # This section handles the old "exactly 2 columns" logic for backward compatibility
            elif len(all_columns) == 2:
                col1, col2 = all_columns[0], all_columns[1]
                logger.info(f"Smart Metric Selector: Generating paired analysis for '{col1}' and '{col2}' (legacy mode)")
                
                # Generate chart using the new method
                chart = self._generate_chart_for_metric_pair(
                    df, col1, col2, 'auto', 
                    enhanced_numeric, enhanced_categorical, date_cols
                )
                
                if chart:
                    charts.append(chart)
                    logger.info(f"Generated legacy paired chart: {col1} vs {col2}")
                
                # If no paired chart was generated, fall back to individual distribution charts
                if len(charts) == 0:
                    logger.info("No paired chart generated, creating individual distribution charts")
                    for col in [col1, col2]:
                        if col in enhanced_numeric:
                            try:
                                col_data = pd.to_numeric(df[col], errors='coerce').dropna()
                                if len(col_data) > 0:
                                    # Create distribution data
                                    hist_data = []
                                    percentiles = [10, 25, 50, 75, 90]
                                    for pct in percentiles:
                                        value = col_data.quantile(pct / 100)
                                        hist_data.append({
                                            "range": f"P{pct}",
                                            "value": float(value)
                                        })
                                    
                                    chart = {
                                        "chart_type": "line",
                                        "title": f"{col} Distribution",
                                        "description": f"Percentile distribution of {col} values",
                                        "data_columns": ["range", "value"],
                                        "confidence": 0.80,
                                        "data": hist_data,
                                        "smart_metric_generated": True,
                                        "recharts_config": {
                                            "type": "LineChart",
                                            "dataKey": "value",
                                            "xAxisKey": "range",
                                            "height": 300,
                                            "margin": {"top": 20, "right": 30, "left": 20, "bottom": 60},
                                            "stroke": "#8884d8",
                                            "dot": {"r": 4}
                                        }
                                    }
                                    charts.append(chart)
                            except Exception as e:
                                logger.error(f"Failed to generate distribution for {col}: {str(e)}")
                        
                        elif col in enhanced_categorical:
                            try:
                                value_counts = df[col].value_counts().head(8)
                                if len(value_counts) > 1:
                                    freq_data = []
                                    for value, count in value_counts.items():
                                        freq_data.append({
                                            "name": str(value),
                                            "value": int(count)
                                        })
                                    
                                    chart = {
                                        "chart_type": "bar",
                                        "title": f"{col} Distribution",
                                        "description": f"Frequency distribution of {col} categories",
                                        "data_columns": ["name", "value"],
                                        "confidence": 0.80,
                                        "data": freq_data,
                                        "smart_metric_generated": True,
                                        "recharts_config": {
                                            "type": "BarChart",
                                            "dataKey": "value",
                                            "xAxisKey": "name",
                                            "height": 300,
                                            "margin": {"top": 20, "right": 30, "left": 20, "bottom": 60},
                                            "fill": "#82ca9d"
                                        }
                                    }
                                    charts.append(chart)
                            except Exception as e:
                                logger.error(f"Failed to generate categorical distribution for {col}: {str(e)}")
            
            # ========= MULTI-COLUMN FALLBACK: Generate standard intelligent charts for multiple columns =========
            else:
                logger.info(f"Smart Metric Selector: Generating intelligent charts for {len(all_columns)} columns")
                # Use the standard intelligent chart generation for multiple columns
                charts = self._generate_intelligent_charts(df, enhanced_numeric, enhanced_categorical, date_cols, business_cols)
            
            logger.info(f"Smart Metric Selector generated {len(charts)} total charts")
            return charts
            
        except Exception as e:
            logger.error(f"Smart Metric Selector chart generation failed: {str(e)}")
            return []

    def _generate_chart_for_metric_pair(self, df: pd.DataFrame, x_col: str, y_col: str, 
                                       chart_type: str, enhanced_numeric: List[str], 
                                       enhanced_categorical: List[str], date_cols: List[str],
                                       pair_id: str = None) -> Dict[str, Any]:
        """Generate a single chart for a specific metric pair (X-axis and Y-axis columns)."""
        try:
            # Determine column types
            x_is_numeric = x_col in enhanced_numeric
            y_is_numeric = y_col in enhanced_numeric
            x_is_categorical = x_col in enhanced_categorical
            y_is_categorical = y_col in enhanced_categorical
            x_is_date = x_col in date_cols
            y_is_date = y_col in date_cols
            
            logger.info(f"Processing metric pair: {x_col} ({self._get_column_type(x_col, enhanced_numeric, enhanced_categorical, date_cols)}) -> {y_col} ({self._get_column_type(y_col, enhanced_numeric, enhanced_categorical, date_cols)})")
            
            # Auto-select chart type if set to 'auto'
            if chart_type == 'auto':
                if x_is_date and y_is_numeric:
                    chart_type = 'line'
                elif x_is_categorical and y_is_numeric:
                    chart_type = 'bar'
                elif x_is_numeric and y_is_numeric:
                    chart_type = 'scatter'
                else:
                    chart_type = 'bar'  # Default fallback
            
            # CASE 1: Date (X-axis) + Numeric (Y-axis) = Line Chart
            if x_is_date and y_is_numeric:
                return self._generate_time_series_pair_chart(df, x_col, y_col, chart_type, pair_id)
            
            # CASE 2: Categorical (X-axis) + Numeric (Y-axis) = Bar Chart
            elif x_is_categorical and y_is_numeric:
                return self._generate_categorical_numeric_pair_chart(df, x_col, y_col, chart_type, pair_id)
            
            # CASE 3: Numeric (X-axis) + Numeric (Y-axis) = Scatter Plot
            elif x_is_numeric and y_is_numeric:
                return self._generate_numeric_numeric_pair_chart(df, x_col, y_col, chart_type, pair_id)
            
            # CASE 4: Both Categorical = Cross-tabulation
            elif x_is_categorical and y_is_categorical:
                return self._generate_categorical_categorical_pair_chart(df, x_col, y_col, chart_type, pair_id)
            
            # CASE 5: Fallback - try to force one interpretation
            else:
                logger.warning(f"Unusual column type combination for {x_col} and {y_col}, attempting categorical-numeric interpretation")
                return self._generate_categorical_numeric_pair_chart(df, x_col, y_col, 'bar', pair_id)
                
        except Exception as e:
            logger.error(f"Failed to generate chart for metric pair {x_col} -> {y_col}: {str(e)}")
            return None

    def _get_column_type(self, col: str, numeric_cols: List[str], categorical_cols: List[str], date_cols: List[str]) -> str:
        """Helper to get the type of a column for logging."""
        if col in numeric_cols:
            return "numeric"
        elif col in categorical_cols:
            return "categorical"
        elif col in date_cols:
            return "date"
        else:
            return "unknown"

    def _generate_time_series_pair_chart(self, df: pd.DataFrame, x_col: str, y_col: str, 
                                        chart_type: str, pair_id: str = None) -> Dict[str, Any]:
        """Generate time series chart for date (X) + numeric (Y) pair."""
        try:
            df_clean = df[[x_col, y_col]].copy()
            df_clean[x_col] = pd.to_datetime(df_clean[x_col], errors='coerce')
            df_clean[y_col] = pd.to_numeric(df_clean[y_col], errors='coerce')
            df_clean = df_clean.dropna()
            
            if len(df_clean) == 0:
                logger.warning(f"No valid data for time series {x_col} -> {y_col}")
                return None
            
            # Sort by date and aggregate if needed
            df_clean = df_clean.sort_values(x_col)
            
            # Group by date if we have multiple entries per date
            if df_clean[x_col].nunique() < len(df_clean):
                df_grouped = df_clean.groupby(x_col)[y_col].agg(['sum', 'mean', 'count']).reset_index()
                agg_col = 'sum' if df_grouped['sum'].sum() > 0 else 'mean'
                chart_data = []
                for _, row in df_grouped.head(50).iterrows():  # Limit to 50 points
                    chart_data.append({
                        "date": row[x_col].strftime("%Y-%m-%d"),
                        "value": float(row[agg_col])
                    })
            else:
                chart_data = []
                for _, row in df_clean.head(50).iterrows():  # Limit to 50 points
                    chart_data.append({
                        "date": row[x_col].strftime("%Y-%m-%d"),
                        "value": float(row[y_col])
                    })
            
            if chart_data:
                return {
                    "id": f"timeseries_{pair_id}" if pair_id else f"timeseries_{len(chart_data)}",
                    "chart_type": "line",
                    "title": f"{y_col} Over Time",
                    "description": f"Time series showing {y_col} (Y-axis) over {x_col} (X-axis)",
                    "data_columns": ["date", "value"],
                    "confidence": 0.95,
                    "data": chart_data,
                    "smart_metric_generated": True,
                    "paired_analysis": True,
                    "x_axis_label": x_col,
                    "y_axis_label": y_col,
                    "recharts_config": {
                        "type": "LineChart",
                        "dataKey": "value",
                        "xAxisKey": "date",
                        "height": 400,
                        "margin": {"top": 20, "right": 30, "left": 20, "bottom": 60},
                        "stroke": "#8884d8",
                        "dot": {"r": 4},
                        "activeDot": {"r": 6}
                    }
                }
        except Exception as e:
            logger.error(f"Failed to generate time series chart for {x_col} -> {y_col}: {str(e)}")
            return None

    def _generate_categorical_numeric_pair_chart(self, df: pd.DataFrame, x_col: str, y_col: str, 
                                               chart_type: str, pair_id: str = None) -> Dict[str, Any]:
        """Generate bar chart for categorical (X) + numeric (Y) pair."""
        try:
            df_clean = df[[x_col, y_col]].copy()
            df_clean[y_col] = pd.to_numeric(df_clean[y_col], errors='coerce')
            df_clean = df_clean.dropna()
            
            if len(df_clean) == 0:
                logger.warning(f"No valid data for categorical-numeric pair {x_col} -> {y_col}")
                return None
            
            # Group by categorical column and aggregate numeric column
            grouped_data = df_clean.groupby(x_col)[y_col].agg(['sum', 'mean', 'count']).reset_index()
            
            # Choose best aggregation
            if grouped_data['sum'].sum() > 0:
                agg_col = 'sum'
                title_suffix = "Total"
            else:
                agg_col = 'mean'
                title_suffix = "Average"
            
            # Prepare chart data
            chart_data = []
            for _, row in grouped_data.head(15).iterrows():
                if pd.notna(row[agg_col]) and row[agg_col] != 0:
                    chart_data.append({
                        "name": str(row[x_col]),
                        "value": float(row[agg_col])
                    })
            
            if chart_data:
                return {
                    "id": f"bar_{pair_id}" if pair_id else f"bar_{len(chart_data)}",
                    "chart_type": "bar",
                    "title": f"{title_suffix} {y_col} by {x_col}",
                    "description": f"Bar chart showing {y_col} (Y-axis) grouped by {x_col} (X-axis)",
                    "data_columns": ["name", "value"],
                    "confidence": 0.95,
                    "data": chart_data,
                    "smart_metric_generated": True,
                    "paired_analysis": True,
                    "x_axis_label": x_col,
                    "y_axis_label": y_col,
                    "recharts_config": {
                        "type": "BarChart",
                        "dataKey": "value",
                        "xAxisKey": "name",
                        "height": 400,
                        "margin": {"top": 20, "right": 30, "left": 20, "bottom": 60},
                        "fill": "#8884d8"
                    }
                }
        except Exception as e:
            logger.error(f"Failed to generate categorical-numeric chart for {x_col} -> {y_col}: {str(e)}")
            return None

    def _generate_numeric_numeric_pair_chart(self, df: pd.DataFrame, x_col: str, y_col: str, 
                                           chart_type: str, pair_id: str = None) -> Dict[str, Any]:
        """Generate scatter plot for numeric (X) + numeric (Y) pair."""
        try:
            df_clean = df[[x_col, y_col]].copy()
            df_clean[x_col] = pd.to_numeric(df_clean[x_col], errors='coerce')
            df_clean[y_col] = pd.to_numeric(df_clean[y_col], errors='coerce')
            df_clean = df_clean.dropna()
            
            if len(df_clean) == 0:
                logger.warning(f"No valid data for numeric-numeric pair {x_col} -> {y_col}")
                return None
            
            # Create paired data points
            chart_data = []
            for i, (_, row) in enumerate(df_clean.head(50).iterrows()):  # Limit to 50 points for performance
                chart_data.append({
                    "x": float(row[x_col]),
                    "y": float(row[y_col]),
                    "name": f"Point {i+1}"
                })
            
            if chart_data:
                return {
                    "id": f"scatter_{pair_id}" if pair_id else f"scatter_{len(chart_data)}",
                    "chart_type": "scatter",
                    "title": f"{y_col} vs {x_col} Correlation",
                    "description": f"Scatter plot showing the relationship between {x_col} (X-axis) and {y_col} (Y-axis)",
                    "data_columns": ["x", "y"],
                    "confidence": 0.95,
                    "data": chart_data,
                    "smart_metric_generated": True,
                    "paired_analysis": True,
                    "x_axis_label": x_col,
                    "y_axis_label": y_col,
                    "recharts_config": {
                        "type": "ScatterChart",
                        "dataKey": "y",
                        "xAxisKey": "x",
                        "height": 400,
                        "margin": {"top": 20, "right": 30, "left": 20, "bottom": 60},
                        "fill": "#8884d8"
                    }
                }
        except Exception as e:
            logger.error(f"Failed to generate numeric-numeric chart for {x_col} -> {y_col}: {str(e)}")
            return None

    def _generate_categorical_categorical_pair_chart(self, df: pd.DataFrame, x_col: str, y_col: str, 
                                                   chart_type: str, pair_id: str = None) -> Dict[str, Any]:
        """Generate cross-tabulation chart for categorical (X) + categorical (Y) pair."""
        try:
            df_clean = df[[x_col, y_col]].copy().dropna()
            
            if len(df_clean) == 0:
                logger.warning(f"No valid data for categorical-categorical pair {x_col} -> {y_col}")
                return None
            
            # Create cross-tabulation
            crosstab = pd.crosstab(df_clean[x_col], df_clean[y_col])
            
            # Convert to chart format
            chart_data = []
            for x_val in crosstab.index[:10]:  # Limit categories
                for y_val in crosstab.columns[:5]:  # Limit subcategories
                    count = crosstab.loc[x_val, y_val]
                    if count > 0:
                        chart_data.append({
                            "name": f"{x_val} - {y_val}",
                            "value": int(count),
                            "category": str(x_val),
                            "subcategory": str(y_val)
                        })
            
            if chart_data:
                return {
                    "id": f"crosstab_{pair_id}" if pair_id else f"crosstab_{len(chart_data)}",
                    "chart_type": "bar",
                    "title": f"{x_col} vs {y_col} Cross-Analysis",
                    "description": f"Cross-tabulation showing the relationship between {x_col} and {y_col}",
                    "data_columns": ["name", "value"],
                    "confidence": 0.90,
                    "data": chart_data,
                    "smart_metric_generated": True,
                    "paired_analysis": True,
                    "x_axis_label": f"{x_col} - {y_col}",
                    "y_axis_label": "Count",
                    "recharts_config": {
                        "type": "BarChart",
                        "dataKey": "value",
                        "xAxisKey": "name",
                        "height": 400,
                        "margin": {"top": 20, "right": 30, "left": 20, "bottom": 80},
                        "fill": "#82ca9d"
                    }
                }
        except Exception as e:
            logger.error(f"Failed to generate categorical-categorical chart for {x_col} -> {y_col}: {str(e)}")
            return None

    def _find_best_column_match(self, search_text: str, available_columns: List[str], 
                               search_type: str = "general") -> Optional[str]:
        """Enhanced fuzzy matching for column names with multiple strategies - VERSATILE & FLEXIBLE."""
        search_lower = search_text.lower().strip()
        
        # Strategy 0: Exact case-insensitive match (highest priority)
        for col in available_columns:
            if col.lower() == search_lower:
                return col
        
        # Strategy 1: Case-insensitive key phrase matching with word boundaries
        search_words = re.findall(r'\w+', search_lower)
        for col in available_columns:
            col_lower = col.lower()
            # Check if all search words are found in the column name
            if all(word in col_lower for word in search_words):
                return col
        
        # Strategy 2: Direct substring matching (both ways) - FLEXIBLE
        for col in available_columns:
            col_lower = col.lower()
            if search_lower in col_lower or col_lower in search_lower:
                return col
        
        # Strategy 2.5: Clean and match - handle symbols, numbers, special chars
        def clean_for_matching(text):
            # Remove special characters but keep spaces and alphanumeric
            cleaned = re.sub(r'[^\w\s]', ' ', text.lower())
            # Normalize multiple spaces
            cleaned = re.sub(r'\s+', ' ', cleaned).strip()
            return cleaned
        
        search_clean = clean_for_matching(search_text)
        search_clean_words = search_clean.split()
        
        for col in available_columns:
            col_clean = clean_for_matching(col)
            col_clean_words = col_clean.split()
            
            # Check if cleaned versions match
            if search_clean == col_clean:
                return col
            
            # Check if all cleaned search words are in cleaned column words
            if all(sword in col_clean_words for sword in search_clean_words):
                return col
            
            # Check if majority of words match (for partial matches)
            if len(search_clean_words) > 1:
                match_count = sum(1 for sword in search_clean_words if sword in col_clean_words)
                if match_count >= len(search_clean_words) * 0.7:  # 70% word match
                    return col
        
        # Strategy 3: Handle common variations, plurals, and EXTENSIVE synonyms - VERSATILE
        search_variations = [search_lower]
        
        # Handle plurals
        if search_lower.endswith('s') and len(search_lower) > 3:
            search_variations.append(search_lower[:-1])  # Remove plural 's'
        else:
            search_variations.append(search_lower + 's')  # Add plural 's'
        
        # Handle common word endings
        if search_lower.endswith('ed'):
            search_variations.append(search_lower[:-2])  # Remove 'ed'
            search_variations.append(search_lower[:-2] + 'ing')  # Add 'ing'
        
        # COMPREHENSIVE synonym mapping - VERSATILE for any domain
        synonym_groups = {
            # Vehicle/Transport domain
            'vehicle': ['car', 'auto', 'bus', 'transport', 'cab', 'taxi', 'truck', 'van'],
            'car': ['vehicle', 'auto', 'cab', 'taxi'],
            'bus': ['vehicle', 'transport', 'coach'],
            'number': ['no', 'num', 'id', 'identifier', 'code'],
            'plate': ['registration', 'reg', 'license'],
            
            # Energy/Power domain
            'energy': ['power', 'electricity', 'kwh', 'kilowatt', 'consumption', 'usage'],
            'power': ['energy', 'electricity', 'watt', 'kilowatt'],
            'delivered': ['consumed', 'used', 'supplied', 'charged', 'generated'],
            'consumed': ['delivered', 'used', 'utilized', 'spent'],
            'units': ['kwh', 'kilowatt', 'energy', 'consumption'],
            
            # Financial domain
            'cost': ['price', 'amount', 'total', 'fee', 'charge', 'expense'],
            'revenue': ['sales', 'income', 'earnings', 'total', 'amount'],
            'amount': ['total', 'sum', 'value', 'cost', 'price'],
            'sales': ['revenue', 'income', 'total'],
            
            # Time/Date domain
            'date': ['time', 'timestamp', 'day', 'period'],
            'time': ['date', 'timestamp', 'period', 'hour'],
            'month': ['period', 'date', 'time'],
            'year': ['period', 'date', 'time'],
            
            # Location domain
            'location': ['place', 'area', 'region', 'zone', 'site'],
            'station': ['stop', 'point', 'location', 'terminal'],
            'region': ['area', 'zone', 'location', 'territory'],
            
            # Rating/Performance domain
            'rating': ['score', 'grade', 'rank', 'level', 'way'],
            'score': ['rating', 'grade', 'rank', 'points'],
            'performance': ['efficiency', 'output', 'result'],
            
            # General business terms
            'category': ['type', 'class', 'group', 'kind'],
            'type': ['category', 'class', 'kind', 'sort'],
            'status': ['state', 'condition', 'situation'],
            'count': ['number', 'quantity', 'total', 'sum'],
            'total': ['sum', 'amount', 'count', 'aggregate'],
            'percentage': ['percent', 'pct', 'ratio', 'rate'],
            'average': ['mean', 'avg', 'typical'],
        }
        
        # Add synonyms based on words in search text
        search_words = search_lower.split()
        for word in search_words:
            if word in synonym_groups:
                search_variations.extend(synonym_groups[word])
        
        # Also check if any column words are synonyms for search words
        for col in available_columns:
            col_words = col.lower().split()
            for col_word in col_words:
                if col_word in synonym_groups:
                    if any(search_word in synonym_groups[col_word] for search_word in search_words):
                        return col
        
        # Match variations against columns
        for variation in search_variations:
            for col in available_columns:
                col_lower = col.lower()
                if variation in col_lower:
                    return col
        
        # Strategy 3: Key word matching for specific types
        if search_type == "metric":
            # Enhanced metric detection patterns with semantic mapping
            metric_mappings = {
                'energy delivered': ['energy delivered', 'total units', 'units', 'kwh', 'energy'],
                'energy': ['energy delivered', 'total units', 'units', 'kwh', 'energy'],
                'units': ['total units', 'units', 'energy delivered', 'kwh'],
                'total units': ['total units', 'units', 'energy delivered'],
                'cost': ['cost', 'price', 'amount', 'total', 'fee'],
                'revenue': ['revenue', 'sales', 'income', 'total'],
                'amount': ['amount', 'total', 'sum', 'value']
            }
            
            # First try direct semantic mapping
            for search_term, candidates in metric_mappings.items():
                if search_term in search_lower:
                    for candidate in candidates:
                        for col in available_columns:
                            col_lower = col.lower()
                            if candidate in col_lower:
                                return col
            
            # Enhanced metric detection patterns
            metric_patterns = [
                ['energy', 'deliver'], ['total', 'unit'], ['amount'], ['cost'], 
                ['revenue'], ['sales'], ['value'], ['count'], ['sum'], 
                ['kwh'], ['kilowatt'], ['power'], ['electricity']
            ]
            
            for pattern in metric_patterns:
                if all(word in search_lower for word in pattern):
                    # Find columns that contain all words in the pattern
                    for col in available_columns:
                        col_lower = col.lower()
                        if all(word in col_lower for word in pattern):
                            return col
            
            # Fallback: find any numeric-looking column with key words
            search_words = search_lower.split()
            for word in search_words:
                if len(word) > 2:  # Ignore very short words
                    for col in available_columns:
                        col_lower = col.lower()
                        if word in col_lower and any(char.isdigit() or char in '()%$₹' for char in col):
                            return col
        
        elif search_type == "dimension":
            # Enhanced dimension detection with better vehicle handling
            dimension_patterns = {
                'vehicle': ['vehicle', 'car', 'auto', 'transport', 'bus', 'way', 'plate', 'number'],
                'rating': ['rating', 'rate', 'score', 'way'],  # Added 'way' for Bus-Way
                'date': ['date', 'time', 'day', 'month', 'year'],
                'location': ['location', 'place', 'station', 'point'],
                'category': ['category', 'type', 'class', 'group'],
                'status': ['status', 'state', 'condition'],
                'identifier': ['id', 'code', 'number', 'plate', 'serial']
            }
            
            # Special handling for compound phrases like "vehicle number plate"
            if 'vehicle' in search_lower and ('number' in search_lower or 'plate' in search_lower):
                # Look specifically for columns containing all these terms
                for col in available_columns:
                    col_lower = col.lower()
                    if 'vehicle' in col_lower and ('number' in col_lower or 'plate' in col_lower):
                        return col
            
            # Special handling for "number plate" without vehicle
            if 'number' in search_lower and 'plate' in search_lower:
                for col in available_columns:
                    col_lower = col.lower()
                    if 'number' in col_lower and 'plate' in col_lower:
                        return col
                    if 'plate' in col_lower:  # Fallback to just plate
                        return col
            
            for pattern_key, pattern_words in dimension_patterns.items():
                if any(word in search_lower for word in pattern_words):
                    # First try to find exact multi-word matches
                    for col in available_columns:
                        col_lower = col.lower()
                        matching_words = [word for word in pattern_words if word in col_lower]
                        if len(matching_words) >= min(2, len([w for w in pattern_words if w in search_lower])):
                            return col
                    
                    # Then try single word matches
                    for col in available_columns:
                        col_lower = col.lower()
                        if any(word in col_lower for word in pattern_words):
                            return col
            
            # Special fallback for "rating" - if no rating column found, try any categorical column
            if 'rating' in search_lower:
                # Look for any categorical-looking column
                categorical_indicators = ['way', 'type', 'category', 'class', 'group', 'status']
                for col in available_columns:
                    col_lower = col.lower()
                    if any(indicator in col_lower for indicator in categorical_indicators):
                        return col
        
        # Strategy 4: Similarity scoring for close matches - FLEXIBLE
        best_match = None
        best_score = 0.0
        
        for col in available_columns:
            # Calculate similarity score
            similarity = SequenceMatcher(None, search_lower, col.lower()).ratio()
            
            # Boost score for word overlap
            search_words = set(search_lower.split())
            col_words = set(re.findall(r'\b\w+\b', col.lower()))
            word_overlap = len(search_words.intersection(col_words)) / max(len(search_words), 1)
            
            # Additional scoring: boost for partial matches in either direction
            partial_score = 0.0
            if len(search_lower) > 3 and search_lower in col.lower():
                partial_score += 0.3
            if len(col) > 3 and col.lower() in search_lower:
                partial_score += 0.3
            
            # Boost for common prefixes/suffixes
            if search_lower.startswith(col.lower()[:min(4, len(col))]) or col.lower().startswith(search_lower[:min(4, len(search_lower))]):
                partial_score += 0.2
            
            combined_score = similarity * 0.5 + word_overlap * 0.3 + partial_score * 0.2
            
            if combined_score > best_score and combined_score > 0.4:  # Lowered threshold for more flexibility
                best_score = combined_score
                best_match = col
        
        # Strategy 5: ULTRA-FLEXIBLE fallback - match by data type if no semantic match
        if not best_match and search_type in ["metric", "dimension"]:
            logger.info(f"Using ultra-flexible fallback matching for {search_type}")
            
            if search_type == "metric":
                # Look for any numeric column
                for col in available_columns:
                    if any(char.isdigit() or char in '()%$₹€£¥' for char in col):
                        logger.info(f"Ultra-flexible: Found numeric-looking column for metric: {col}")
                        return col
                        
            elif search_type == "dimension":
                # Look for any categorical/text column
                for col in available_columns:
                    # Prefer shorter column names (likely to be categorical)
                    if len(col) <= 30 and not any(char.isdigit() for char in col[-5:]):  # No numbers at end
                        logger.info(f"Ultra-flexible: Found categorical-looking column for dimension: {col}")
                        return col
        
        # Strategy 6: LAST RESORT - if still no match, be SUPER flexible
        if not best_match and len(available_columns) > 0:
            logger.warning(f"No good match found for '{search_text}', using best available option")
            # Return the first column that's not obviously wrong
            for col in available_columns:
                if len(col) > 0:  # Any non-empty column name
                    logger.info(f"Last resort: Using column '{col}' for '{search_text}'")
                    return col
        
        return best_match

    def _generate_preference_based_charts(self, df: pd.DataFrame, user_preferences: Dict[str, Any],
                                        numeric_cols: List[str], categorical_cols: List[str], 
                                        date_cols: List[str], business_cols: Dict[str, str]) -> List[Dict[str, Any]]:
        """Generate charts based on user preferences and specific questions."""
        charts = []
        
        try:
            logger.info("\nGENERATING PREFERENCE-BASED CHARTS")
            
            # Handle specific questions first
            if user_preferences.get('specific_questions'):
                for question in user_preferences['specific_questions']:
                    # Enhanced parsing for multiple distributions
                    logger.info(f"Processing question: {question}")
                    
                    # Extract chart types mentioned in the question
                    chart_types = []
                    question_lower = question.lower()
                    if 'pie chart' in question_lower or 'pie' in question_lower:
                        chart_types.append('pie')
                    if 'bar graph' in question_lower or 'bar chart' in question_lower or 'bar' in question_lower:
                        chart_types.append('bar')
                    if 'histogram' in question_lower:
                        chart_types.append('histogram')
                    
                    # If no specific chart types mentioned, default to pie
                    if not chart_types:
                        chart_types = ['pie']
                    
                    # ENHANCED: Parse compound requests with "and" 
                    distributions = []
                    
                    # Check for compound requests like "total units by vehicle number and total units by bus-way"
                    if ' and ' in question_lower and question_lower.count(' by ') >= 2:
                        # Split on "and" and process each part separately
                        parts = question_lower.split(' and ')
                        logger.info(f"Found compound request with {len(parts)} parts: {parts}")
                        
                        for part in parts:
                            part = part.strip()
                            # Process each part as a separate "X by Y" request
                            if ' by ' in part:
                                by_parts = part.split(' by ')
                                if len(by_parts) >= 2:
                                    # Extract metric and dimension for this part
                                    metric_part = by_parts[0].strip()
                                    dimension_part = by_parts[1].strip()
                                    
                                    # Clean up metric part
                                    chart_words = ['pie chart', 'bar graph', 'bar chart', 'histogram', 'chart', 'graph', 'pie', 'bar']
                                    for chart_word in chart_words:
                                        metric_part = metric_part.replace(chart_word, '').strip()
                                    
                                    # Remove leading words
                                    start_words = ['give me a', 'give me', 'show me a', 'show me', 'create a', 'create', 'generate a', 'generate']
                                    for start_word in start_words:
                                        if metric_part.startswith(start_word):
                                            metric_part = metric_part[len(start_word):].strip()
                                    
                                    if metric_part and dimension_part:
                                        distributions.append((metric_part, dimension_part))
                                        logger.info(f"Extracted distribution: '{metric_part}' by '{dimension_part}'")
                    
                    # If no compound request found, use original single parsing logic
                    if not distributions and ' by ' in question_lower:
                        # Find the "by" part first
                        by_parts = question_lower.split(' by ')
                        if len(by_parts) >= 2:
                            # The dimension is everything after the last "by"
                            dimension_part = by_parts[-1].strip()
                            
                            # The metric is everything before, but clean out chart type words
                            metric_part = by_parts[0].strip()
                            
                            # Remove chart type words from metric part
                            chart_words = ['pie chart', 'bar graph', 'bar chart', 'histogram', 'chart', 'graph', 'pie', 'bar']
                            for chart_word in chart_words:
                                metric_part = metric_part.replace(chart_word, '').strip()
                            
                            # Clean up connecting words
                            metric_part = metric_part.replace(' and ', ' ').replace(' on ', ' ').strip()
                            
                            # Remove leading words like "give me a", "show me", etc.
                            start_words = ['give me a', 'give me', 'show me a', 'show me', 'create a', 'create', 'generate a', 'generate']
                            for start_word in start_words:
                                if metric_part.startswith(start_word):
                                    metric_part = metric_part[len(start_word):].strip()
                            
                            if metric_part and dimension_part:
                                distributions.append((metric_part, dimension_part))
                    
                    # Fallback: if no "by" pattern found, try to extract from context
                    if not distributions:
                        # Look for common patterns like "energy delivered" or "total units"
                        metric_candidates = ['energy delivered', 'total units', 'energy', 'units', 'cost', 'revenue', 'amount']
                        dimension_candidates = ['rating', 'category', 'type', 'vehicle', 'location', 'station']
                        
                        found_metric = None
                        found_dimension = None
                        
                        for metric in metric_candidates:
                            if metric in question_lower:
                                found_metric = metric
                                break
                        
                        for dimension in dimension_candidates:
                            if dimension in question_lower:
                                found_dimension = dimension
                                break
                        
                        if found_metric and found_dimension:
                            distributions.append((found_metric, found_dimension))
                        elif found_metric:
                            # Try to infer dimension from available categorical columns
                            if categorical_cols:
                                distributions.append((found_metric, categorical_cols[0]))
                    
                    # If still no distributions found, create a default one
                    if not distributions and numeric_cols and categorical_cols:
                        distributions.append((numeric_cols[0], categorical_cols[0]))
                    
                    logger.info(f"Detected {len(distributions)} data distributions: {distributions}")
                    logger.info(f"Detected chart types: {chart_types}")
                    logger.info(f"Will generate {len(distributions) * len(chart_types)} charts total")
                    
                    # Generate charts for each distribution
                    charts_generated_for_question = 0
                    for dist_idx, (metric_text, dimension_text) in enumerate(distributions, 1):
                        logger.info(f"\n--- Processing Distribution {dist_idx}/{len(distributions)}: '{metric_text}' by '{dimension_text}' ---")
                        # Enhanced column detection using new fuzzy matching
                        all_columns = df.columns.tolist()
                        
                        # ENHANCED: Parse filtering conditions from the question
                        filters = self._parse_filtering_conditions(question, df)
                        logger.info(f"Parsed filters: {filters}")
                        
                        # Clean dimension text by removing filter conditions
                        clean_dimension_text = self._clean_dimension_text(dimension_text)
                        
                        # Enhanced column detection with detailed logging
                        logger.info(f"Searching for metric: '{metric_text}'")
                        logger.info(f"Searching for dimension: '{dimension_text}' → cleaned: '{clean_dimension_text}'")
                        logger.info(f"Available columns: {all_columns}")
                        
                        # Use enhanced matching for metric column
                        metric_col = self._find_best_column_match(metric_text, all_columns, "metric")
                        logger.info(f"Metric column match result: '{metric_col}'")
                        
                        # Use enhanced matching for dimension column with cleaned text
                        dimension_col = self._find_best_column_match(clean_dimension_text, all_columns, "dimension")
                        logger.info(f"Dimension column match result: '{dimension_col}'")
                        
                        # If dimension not found, try more aggressive matching
                        if not dimension_col:
                            logger.info(f"Trying more aggressive matching for dimension: '{dimension_text}'")
                            # Try word-by-word matching
                            dimension_words = dimension_text.lower().split()
                            for col in all_columns:
                                col_lower = col.lower()
                                if all(word in col_lower for word in dimension_words):
                                    dimension_col = col
                                    logger.info(f"Found dimension via word matching: '{dimension_col}'")
                                    break
                        
                        # Safe logging with ASCII conversion
                        safe_columns = [safe_log_string(col) for col in all_columns]
                        logger.info(f"Found columns - Metric: {safe_log_string(metric_col) if metric_col else None}, Dimension: {safe_log_string(dimension_col) if dimension_col else None}")
                        
                        if metric_col and dimension_col:
                            logger.info(f"Generating charts for {safe_log_string(metric_col)} by {safe_log_string(dimension_col)}")
                            
                            # Enhanced data cleaning and processing
                            logger.info(f"Original data shape: {df.shape}")
                            
                            # ENHANCED: Apply data filters BEFORE processing
                            filtered_df = self._apply_data_filters(df, filters, all_columns)
                            logger.info(f"After filtering: {filtered_df.shape}")
                            
                            # Create a working copy from filtered data
                            work_df = filtered_df[[metric_col, dimension_col]].copy()
                            
                            # Clean metric column more carefully
                            if work_df[metric_col].dtype == 'object':
                                logger.info(f"Converting object column to numeric")
                                # First, handle common non-numeric representations
                                work_df[metric_col] = work_df[metric_col].astype(str)
                                work_df[metric_col] = work_df[metric_col].replace({
                                    '—': '0', '–': '0', '-': '0', 'N/A': '0', 'n/a': '0', 
                                    'NA': '0', 'null': '0', 'None': '0', 'nan': '0', '': '0'
                                })
                                
                                # Convert to numeric, but keep track of conversion issues
                                original_count = len(work_df)
                                work_df[metric_col] = pd.to_numeric(work_df[metric_col], errors='coerce')
                                
                                # Fill NaN values with 0 instead of dropping them
                                nan_count = work_df[metric_col].isna().sum()
                                if nan_count > 0:
                                    logger.warning(f"Found {nan_count} non-numeric values in metric column, setting to 0")
                                    work_df[metric_col] = work_df[metric_col].fillna(0)
                            
                            # Clean dimension column with Excel-like normalization
                            work_df[dimension_col] = work_df[dimension_col].astype(str)
                            
                            # Remove empty/null values
                            work_df = work_df[work_df[dimension_col].str.strip() != '']
                            work_df = work_df[work_df[dimension_col] != 'nan']
                            work_df = work_df[work_df[dimension_col] != 'None']
                            work_df = work_df[work_df[dimension_col] != 'null']
                            work_df = work_df[work_df[dimension_col] != 'NaN']
                            
                            # Excel-like data normalization: handle case inconsistencies and whitespace
                            def normalize_text(text):
                                if pd.isna(text) or str(text).lower() in ['nan', 'none', 'null', '']:
                                    return None
                                # Strip whitespace and normalize case
                                normalized = str(text).strip()
                                # Handle common variations (optional: you can make this more aggressive)
                                # For now, just normalize whitespace and case
                                normalized = ' '.join(normalized.split())  # Remove extra whitespace
                                return normalized
                            
                            # Apply normalization
                            work_df[dimension_col] = work_df[dimension_col].apply(normalize_text)
                            work_df = work_df.dropna(subset=[dimension_col])
                            
                            # Group similar values (case-insensitive grouping like Excel pivot tables)
                            dimension_mapping = {}
                            for value in work_df[dimension_col].unique():
                                value_lower = value.lower()
                                # Find if we already have a similar value
                                found_match = False
                                for existing_key, existing_values in dimension_mapping.items():
                                    if any(existing_val.lower() == value_lower for existing_val in existing_values):
                                        dimension_mapping[existing_key].append(value)
                                        found_match = True
                                        break
                                
                                if not found_match:
                                    # Use the first occurrence as the canonical form
                                    dimension_mapping[value] = [value]
                            
                            # Create reverse mapping for normalization
                            value_to_canonical = {}
                            for canonical, variations in dimension_mapping.items():
                                for variation in variations:
                                    value_to_canonical[variation] = canonical
                            
                            # Apply canonical mapping
                            work_df[dimension_col] = work_df[dimension_col].map(value_to_canonical)
                            
                            # Handle date columns specially
                            if dimension_col in date_cols:
                                logger.info(f"Processing date column")
                                try:
                                    # Convert to datetime and then format for display
                                    work_df[dimension_col] = pd.to_datetime(work_df[dimension_col], errors='coerce')
                                    # Remove rows where date conversion failed
                                    work_df = work_df.dropna(subset=[dimension_col])
                                    # Format dates for better display (group by date only, not time)
                                    work_df[dimension_col] = work_df[dimension_col].dt.strftime('%Y-%m-%d')
                                    logger.info(f"Successfully converted {len(work_df)} date values")
                                except Exception as e:
                                    logger.warning(f"Date conversion failed: {e}, treating as categorical")
                            
                            logger.info(f"Cleaned data shape: {work_df.shape}")
                            
                            if len(work_df) == 0:
                                logger.warning(f"No valid data found after cleaning")
                                continue
                            
                            # Group by dimension and sum the metric with improved accuracy
                            try:
                                # Ensure we have clean data before grouping
                                work_df = work_df.dropna(subset=[metric_col, dimension_col])
                                
                                # Debug logging
                                logger.info(f"Before grouping - unique dimensions: {work_df[dimension_col].nunique()}")
                                logger.info(f"Sample dimension values: {work_df[dimension_col].head(10).tolist()}")
                                
                                # Use precise aggregation like Excel pivot tables
                                grouped_data = work_df.groupby(dimension_col, as_index=False).agg({
                                    metric_col: ['sum', 'count', 'mean']
                                }).round(3)
                                
                                # Flatten column names
                                grouped_data.columns = [dimension_col, 'total', 'count', 'average']
                                
                                # Sort by total value for better visualization
                                grouped_data = grouped_data.sort_values('total', ascending=False)
                                
                                logger.info(f"Grouped data shape: {grouped_data.shape}")
                                logger.info(f"Sample grouped data:\n{grouped_data.head()}")
                                
                                # Convert to chart data format with improved precision
                                chart_data = []
                                total_across_all = 0
                                
                                for _, row in grouped_data.iterrows():
                                    value = float(row['total']) if pd.notna(row['total']) else 0.0
                                    total_across_all += value
                                    
                                    # Clean up dimension name for display
                                    dimension_name = str(row[dimension_col]).strip()
                                    if len(dimension_name) > 50:  # Truncate very long names
                                        dimension_name = dimension_name[:47] + "..."
                                    
                                    chart_data.append({
                                        'name': dimension_name,
                                        'value': round(value, 2),
                                        'count': int(row['count']) if pd.notna(row['count']) else 0,
                                        'percentage': 0  # Will calculate after we have total
                                    })
                                
                                # Calculate percentages for pie charts
                                if total_across_all > 0:
                                    for item in chart_data:
                                        item['percentage'] = round((item['value'] / total_across_all) * 100, 1)
                                
                                # Filter out very small slices to avoid cluttered charts (like Excel does)
                                if len(chart_data) > 10:  # Only filter if we have many categories
                                    significant_data = [item for item in chart_data if item['percentage'] >= 1.0]
                                    others_data = [item for item in chart_data if item['percentage'] < 1.0]
                                    
                                    if others_data:
                                        others_total = sum(item['value'] for item in others_data)
                                        others_count = sum(item['count'] for item in others_data)
                                        significant_data.append({
                                            'name': f'Others ({len(others_data)} items)',
                                            'value': round(others_total, 2),
                                            'count': others_count,
                                            'percentage': round((others_total / total_across_all) * 100, 1)
                                        })
                                    
                                    chart_data = significant_data
                                
                                logger.info(f"Generated chart data with {len(chart_data)} data points")
                                logger.info(f"Total value across all categories: {total_across_all}")
                                
                            except Exception as e:
                                logger.error(f"Error during data grouping: {e}")
                                import traceback
                                logger.error(f"Traceback: {traceback.format_exc()}")
                                continue
                            
                            # Generate requested chart types for this distribution
                            for chart_type in chart_types:
                                logger.info(f"Creating {chart_type} chart for '{metric_col}' by '{dimension_col}'")
                                # ENHANCED: Create filter-aware titles and descriptions
                                base_title = f"{safe_log_string(metric_col)} by {safe_log_string(dimension_col)}"
                                base_description = f"Distribution of {safe_log_string(metric_col)} across {safe_log_string(dimension_col)}"
                                
                                # Add filter information if filters were applied
                                if filters['applied'] and filters.get('applied_filters'):
                                    filter_descriptions = []
                                    for applied_filter in filters['applied_filters']:
                                        filter_desc = f"{applied_filter['condition']} in {applied_filter['column']}"
                                        filter_descriptions.append(filter_desc)
                                    
                                    filter_text = " | ".join(filter_descriptions)
                                    enhanced_title = f"{base_title} (Filtered: {filter_text})"
                                    enhanced_description = f"{base_description}. Filtered data: {filter_text}. Showing {filters['filtered_rows']} of {filters['original_rows']} records."
                                else:
                                    enhanced_title = base_title
                                    enhanced_description = base_description
                                
                                if chart_type == 'pie':
                                    chart = {
                                        "id": f"pie_{len(charts) + 1}",
                                        "title": enhanced_title,
                                        "chart_type": "pie",
                                        "data": chart_data,
                                        "data_columns": ["name", "value"],
                                        "confidence": 0.95,
                                        "description": enhanced_description,
                                        "recharts_config": {
                                            "dataKey": "value",
                                            "xAxisKey": "name",
                                            "height": 300,
                                            "margin": {"top": 5, "right": 30, "left": 20, "bottom": 5}
                                        },
                                        "user_requested": True,
                                        "filters_applied": filters['applied'],
                                        "filter_info": filters.get('applied_filters', []) if filters['applied'] else None
                                    }
                                    charts.append(chart)
                                    charts_generated_for_question += 1
                                    logger.info(f"[SUCCESS] Generated pie chart successfully ({charts_generated_for_question} total so far)")
                                
                                elif chart_type == 'bar':
                                    chart = {
                                        "id": f"bar_{len(charts) + 1}",
                                        "title": enhanced_title,
                                        "chart_type": "bar",
                                        "data": chart_data,
                                        "data_columns": ["name", "value"],
                                        "confidence": 0.95,
                                        "description": enhanced_description,
                                        "recharts_config": {
                                            "dataKey": "value",
                                            "xAxisKey": "name",
                                            "height": 300,
                                            "margin": {"top": 5, "right": 30, "left": 20, "bottom": 5}
                                        },
                                        "user_requested": True,
                                        "filters_applied": filters['applied'],
                                        "filter_info": filters.get('applied_filters', []) if filters['applied'] else None
                                    }
                                    charts.append(chart)
                                    charts_generated_for_question += 1
                                    logger.info(f"[SUCCESS] Generated bar chart successfully ({charts_generated_for_question} total so far)")
                                
                                elif chart_type == 'histogram':
                                    # For histogram, we use the metric values directly
                                    values = work_df[metric_col].values
                                    hist, bin_edges = np.histogram(values, bins=10)
                                    
                                    histogram_data = []
                                    for i in range(len(hist)):
                                        histogram_data.append({
                                            'name': f"{bin_edges[i]:.1f}-{bin_edges[i+1]:.1f}",
                                            'value': int(hist[i])
                                        })
                                    
                                    chart = {
                                        "id": f"histogram_{len(charts) + 1}",
                                        "title": f"Distribution of {safe_log_string(metric_col)}",
                                        "chart_type": "bar",
                                        "data": histogram_data,
                                        "data_columns": ["name", "value"],
                                        "confidence": 0.95,
                                        "description": f"Histogram showing distribution of {safe_log_string(metric_col)}",
                                        "recharts_config": {
                                            "dataKey": "value",
                                            "xAxisKey": "name",
                                            "height": 300,
                                            "margin": {"top": 5, "right": 30, "left": 20, "bottom": 5}
                                        },
                                        "user_requested": True
                                    }
                                    charts.append(chart)
                                    charts_generated_for_question += 1
                                    logger.info(f"[SUCCESS] Generated histogram successfully ({charts_generated_for_question} total so far)")
                        else:
                            logger.warning(f"Could not find columns for {metric_text} by {dimension_text}")
                            logger.info(f"Available columns: {safe_columns}")
                    
                    logger.info(f"\n[COMPLETE] USER-REQUESTED CHARTS COMPLETE: Generated {charts_generated_for_question} charts for this question")
                    logger.info(f"[SUMMARY] Total charts generated so far: {len(charts)}")
                    
                    # Add summary of what was generated
                    chart_summary = []
                    for chart in charts[-charts_generated_for_question:]:  # Get the charts just generated
                        chart_summary.append(f"  - {chart['chart_type'].upper()}: {chart['title']}")
                    if chart_summary:
                        logger.info("Charts generated:")
                        for summary_line in chart_summary:
                            logger.info(summary_line)
                    
            return charts
            
        except Exception as e:
            logger.error(f"Error in preference-based chart generation: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return []

    def _parse_filtering_conditions(self, question: str, df: pd.DataFrame) -> Dict[str, Any]:
        """Parse filtering conditions from user questions like 'only for AA names' or 'where Z column equals something'."""
        filters = {
            'conditions': [],
            'applied': False,
            'original_rows': len(df),
            'filtered_rows': 0
        }
        
        question_lower = question.lower()
        
        # Enhanced patterns for complex filtering requests
        complex_filter_patterns = [
            # "but for only [specific value]" - handles complex names with spaces and commas
            r'but for only\s+([^,\n]+(?:,\s*[^,\n]+)*)(?:\s+in\s+the\s+([\w\s]+?)\s+column)?',
            # "only for [specific value]" - handles complex names with spaces and commas
            r'only for\s+([^,\n]+(?:,\s*[^,\n]+)*)(?:\s+in\s+the\s+([\w\s]+?)\s+column)?',
            # "where [column] equals [value]"
            r'where\s+([\w\s]+?)\s+(?:is|equals?)\s+([^,\n]+(?:,\s*[^,\n]+)*)',
            # "for [specific location/name]" - handles complex names with spaces and commas
            r'for\s+([^,\n]+(?:,\s*[^,\n]+)*)(?:\s+in\s+the\s+([\w\s]+?)\s+column)?',
        ]
        
        # Simple patterns for basic filtering
        simple_filter_patterns = [
            r'containing\s+([^,\n]+)',      # "containing AA"
            r'with\s+([^,\n]+)',           # "with AA"
            r'having\s+([^,\n]+)',         # "having AA"
            r'including\s+([^,\n]+)',      # "including AA"
        ]
        
        # Extract complex filtering conditions first (higher priority)
        for pattern in complex_filter_patterns:
            matches = re.findall(pattern, question_lower)
            for match in matches:
                if isinstance(match, tuple) and len(match) == 2:
                    value, column_hint = match
                    # Clean up the value and column hint
                    value = value.strip()
                    column_hint = column_hint.strip() if column_hint else None
                    
                    filters['conditions'].append({
                        'type': 'contains',  # Use contains for complex names
                        'value': value,
                        'column_hint': column_hint,
                        'pattern': 'complex_filter',
                        'priority': 'high'
                    })
                    logger.info(f"Parsed complex filter: '{value}' in column '{column_hint}'")
                else:
                    # Single value match
                    value = match.strip() if isinstance(match, str) else str(match).strip()
                    filters['conditions'].append({
                        'type': 'contains',
                        'value': value,
                        'column_hint': None,
                        'pattern': 'complex_filter_single',
                        'priority': 'high'
                    })
                    logger.info(f"Parsed complex filter: '{value}'")
        
        # Extract simple filtering conditions (lower priority)
        for pattern in simple_filter_patterns:
            matches = re.findall(pattern, question_lower)
            for match in matches:
                value = match.strip() if isinstance(match, str) else str(match).strip()
                filters['conditions'].append({
                    'type': 'contains',
                    'value': value,
                    'column_hint': None,
                    'pattern': 'simple_filter',
                    'priority': 'medium'
                })
                logger.info(f"Parsed simple filter: '{value}'")
        
        return filters

    def _clean_dimension_text(self, dimension_text: str) -> str:
        """Clean dimension text by removing filter conditions and keeping only the core dimension."""
        if not dimension_text:
            return dimension_text
        
        # Convert to lowercase for processing
        text_lower = dimension_text.lower()
        
        # Remove common filter phrases that shouldn't be part of the dimension
        filter_phrases_to_remove = [
            r'\s+but for only\s+[^,\n]+',  # "but for only ThunderPlus EV Charge Hub, Suryapet"
            r'\s+only for\s+[^,\n]+',     # "only for ThunderPlus EV Charge Hub, Suryapet"
            r'\s+for only\s+[^,\n]+',     # "for only ThunderPlus EV Charge Hub, Suryapet"
            r'\s+where\s+[^,\n]+',        # "where status equals active"
            r'\s+containing\s+[^,\n]+',   # "containing transport"
            r'\s+with\s+[^,\n]+',         # "with specific values"
            r'\s+in the\s+[\w\s]+\s+column',  # "in the charging station column"
        ]
        
        cleaned_text = text_lower
        for pattern in filter_phrases_to_remove:
            cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.IGNORECASE)
        
        # Clean up extra whitespace
        cleaned_text = ' '.join(cleaned_text.split())
        
        # If we removed too much, fall back to extracting key terms
        if not cleaned_text or len(cleaned_text) < 3:
            # Extract the main dimension terms (before any filter conditions)
            main_terms = []
            words = dimension_text.lower().split()
            
            # Stop at filter keywords
            filter_keywords = ['but', 'only', 'for', 'where', 'containing', 'with', 'in']
            for word in words:
                if word in filter_keywords:
                    break
                main_terms.append(word)
            
            cleaned_text = ' '.join(main_terms) if main_terms else dimension_text.lower()
        
        logger.info(f"Cleaned dimension: '{dimension_text}' -> '{cleaned_text}'")
        return cleaned_text.strip()

    def _apply_data_filters(self, df: pd.DataFrame, filters: Dict[str, Any], 
                           available_columns: List[str]) -> pd.DataFrame:
        """Apply parsed filtering conditions to the dataframe."""
        if not filters['conditions']:
            return df
        
        filtered_df = df.copy()
        applied_filters = []
        
        # Sort conditions by priority (high priority first)
        sorted_conditions = sorted(filters['conditions'], 
                                 key=lambda x: {'high': 0, 'medium': 1, 'low': 2}.get(x.get('priority', 'low'), 2))
        
        for condition in sorted_conditions:
            filter_value = condition['value'].strip()
            filter_type = condition['type']
            column_hint = condition.get('column_hint')
            priority = condition.get('priority', 'medium')
            
            # Skip very short filters that are likely parsing errors
            if len(filter_value) < 3:
                logger.warning(f"Skipping very short filter: '{filter_value}' (likely parsing error)")
                continue
            
            filter_value_lower = filter_value.lower()
            logger.info(f"Processing filter: '{filter_value}' (type: {filter_type}, priority: {priority})")
            
            # Find the best column to apply the filter to
            target_column = None
            
            if column_hint:
                # Try to match the column hint to actual columns
                target_column = self._find_best_column_match(column_hint, available_columns, "dimension")
                logger.info(f"Column hint '{column_hint}' matched to: {target_column}")
            
            if not target_column:
                # Search all categorical columns for the filter value
                categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
                best_match_score = 0
                
                for col in categorical_cols:
                    if col in available_columns:
                        col_values = df[col].astype(str).str.lower()
                        
                        if filter_type == 'contains':
                            # Check how many values contain the filter
                            matches = col_values.str.contains(filter_value_lower, na=False, regex=False)
                            match_count = matches.sum()
                            
                            if match_count > 0:
                                # Calculate match score based on how specific the filter is
                                total_unique = col_values.nunique()
                                match_score = match_count / total_unique if total_unique > 0 else 0
                                
                                if match_score > best_match_score:
                                    best_match_score = match_score
                                    target_column = col
                                    logger.info(f"Found better match in column '{col}': {match_count} matches, score: {match_score:.3f}")
                        
                        elif filter_type == 'exact_match':
                            if (col_values == filter_value_lower).any():
                                target_column = col
                                logger.info(f"Found exact match in column '{col}'")
                                break
            
            # Apply the filter if we found a target column
            if target_column and target_column in filtered_df.columns:
                original_count = len(filtered_df)
                
                if filter_type == 'contains':
                    mask = filtered_df[target_column].astype(str).str.lower().str.contains(filter_value_lower, na=False, regex=False)
                    filtered_df = filtered_df[mask]
                elif filter_type == 'exact_match':
                    mask = filtered_df[target_column].astype(str).str.lower() == filter_value_lower
                    filtered_df = filtered_df[mask]
                
                filtered_count = len(filtered_df)
                applied_filters.append({
                    'column': target_column,
                    'condition': f"{filter_type}: {filter_value}",
                    'rows_before': original_count,
                    'rows_after': filtered_count,
                    'rows_filtered': original_count - filtered_count
                })
                
                logger.info(f"Applied filter '{filter_value}' to column '{target_column}': {original_count} -> {filtered_count} rows")
            else:
                logger.warning(f"Could not find suitable column for filter: '{filter_value}'")
        
        # Update filters metadata
        filters['applied'] = len(applied_filters) > 0
        filters['filtered_rows'] = len(filtered_df)
        filters['applied_filters'] = applied_filters
        
        return filtered_df
