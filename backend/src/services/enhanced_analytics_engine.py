"""
Enhanced Analytics Engine with A2A, ADK-python, and Context7 Integration

This module provides advanced analytics capabilities for dashboard generation,
leveraging agent-to-agent communication and enhanced AI models.
"""

import asyncio
import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, asdict
import json
from datetime import datetime
import io
from src.core.adk_config import ADKConfig
from src.services.litellm_service import litellm_service, generate_ai_response, generate_structured_ai_response
from src.agents.intelligent_data_filter import classify_column_patterns, DataFilteringResult
import re

# Statistical analysis imports
try:
    from scipy import stats
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler
    from sklearn.decomposition import PCA
    ADVANCED_STATS_AVAILABLE = True
except ImportError:
    ADVANCED_STATS_AVAILABLE = False
    logging.warning("Advanced statistics libraries not available")

# Local imports
logger = logging.getLogger(__name__)
adk_config = ADKConfig()


@dataclass
class DataInsight:
    """Represents a data insight with confidence score."""
    insight_type: str
    title: str
    description: str
    confidence: float
    data_evidence: Dict[str, Any]
    recommendation: str
    visualization_suggestion: str


@dataclass
class EnhancedChartRecommendation:
    """Enhanced chart recommendation with business context."""
    chart_type: str
    data_columns: List[str]
    title: str
    description: str
    business_context: str
    confidence: float
    ai_reasoning: str
    statistical_basis: str
    interactivity_features: List[str]
    recharts_config: Dict[str, Any]
    data: List[Dict[str, Any]]
    kpi_connection: Optional[str] = None


@dataclass
class BusinessPattern:
    """Represents a detected business pattern."""
    pattern_type: str
    description: str
    columns_involved: List[str]
    confidence: float
    business_impact: str
    recommended_visualizations: List[str]


class EnhancedAnalyticsEngine:
    """Enhanced analytics engine with advanced AI integration."""
    
    def __init__(self):
        """Initialize the enhanced analytics engine."""
        self.litellm_service = litellm_service
        self.config = adk_config
        
        # Chart type mapping for different business scenarios
        self.business_chart_mapping = {
            "revenue_analysis": ["line", "area", "bar", "waterfall"],
            "performance_comparison": ["bar", "radar", "heatmap"],
            "trend_analysis": ["line", "area", "scatter"],
            "distribution_analysis": ["histogram", "box", "violin"],
            "composition_analysis": ["pie", "stacked_bar", "treemap"],
            "correlation_analysis": ["scatter", "heatmap", "bubble"],
            "geographical_analysis": ["map", "choropleth", "bubble_map"],
            "time_series": ["line", "area", "candlestick"],
            "forecasting": ["line", "area", "forecast_cone"]
        }
        
        # Advanced interactivity features
        self.interactivity_features = {
            "drill_down": "Enable drilling down into data segments",
            "cross_filtering": "Connect charts for cross-filtering",
            "zoom_pan": "Allow zooming and panning on time series",
            "hover_details": "Rich hover tooltips with context",
            "brushing": "Select data ranges across charts",
            "animation": "Smooth transitions and animations",
            "real_time": "Real-time data updates"
        }
    
    async def analyze_and_generate_enhanced_dashboard(
        self, 
        df: pd.DataFrame, 
        filename: str,
        business_context: Optional[str] = None,
        fast_mode: bool = True
    ) -> Dict[str, Any]:
        """
        Generate enhanced dashboard with advanced analytics and AI insights.
        
        Args:
            df: Input DataFrame
            filename: Source filename
            business_context: Optional business context
            fast_mode: If True, reduce AI calls for faster processing (default: True)
            
        Returns:
            Complete dashboard configuration
        """
        try:
            logger.info(f"Starting enhanced analytics for {filename} (fast_mode={fast_mode})")
            
            # Step 0: Intelligent Data Filtering (NEW)
            logger.info("Step 0/6: INTELLIGENT DATA FILTERING & COLUMN ANALYSIS")
            logger.info("=" * 80)
            
            # Convert DataFrame to dictionary format for filtering
            df_dict = {
                'columns': df.columns.tolist(),
                'rows': df.to_dict('records')
            }
            
            # Apply intelligent data filtering
            filtering_response = classify_column_patterns(df_dict)
            
            if filtering_response.get('status') == 'success':
                filtering_result_dict = filtering_response.get('filtering_result', {})
                filtering_result = DataFilteringResult(**filtering_result_dict)
                
                logger.info(f"ORIGINAL DATASET:")
                logger.info(f"   - Total Columns: {len(df.columns)}")
                logger.info(f"   - Total Rows: {len(df)}")
                logger.info(f"   - Original Columns: {list(df.columns)}")
                
                logger.info(safe_log_message(f"\n🔍 INTELLIGENT FILTERING RESULTS:"))
                logger.info(f"   - Relevant Columns (for charts/KPIs): {len(filtering_result.relevant_columns)}")
                logger.info(f"   - Irrelevant Columns (filtered out): {len(filtering_result.irrelevant_columns)}")
                logger.info(f"   - Metadata Columns (for context): {len(filtering_result.metadata_columns)}")
                logger.info(f"   - Overall Confidence: {filtering_result.confidence_score:.2f}")
                logger.info(f"   - Data Retention: {filtering_result.data_retention_percentage:.1f}%")
                
                if filtering_result.irrelevant_columns:
                    safe_message = safe_log_message(f"\n[X] FILTERED OUT (Irrelevant for Analytics):")
                    logger.info(safe_message)
                    for col in filtering_result.irrelevant_columns:
                        # Handle both dictionary and dataclass objects in column_classifications
                        col_classification = None
                        for c in filtering_result.column_classifications:
                            if isinstance(c, dict):
                                if c.get('column_name') == col:
                                    col_classification = c
                                    break
                            else:
                                # Assume it's a dataclass with column_name attribute
                                if hasattr(c, 'column_name') and c.column_name == col:
                                    col_classification = asdict(c) if hasattr(c, '__dataclass_fields__') else c
                                    break
                        
                        if col_classification:
                            safe_message = safe_log_message(f"   - '{col}' -> {col_classification['data_type']} (confidence: {col_classification['confidence']:.2f})")
                            logger.info(safe_message)
                            logger.info(f"     Reason: {col_classification['reasoning']}")
                            logger.info(f"     Sample: {col_classification['sample_values'][:3]}")
                
                if filtering_result.relevant_columns:
                    safe_message = safe_log_message(f"\n[OK] INCLUDED (Relevant for Analytics):")
                    logger.info(safe_message)
                    for col in filtering_result.relevant_columns:
                        col_classification = None
                        for c in filtering_result.column_classifications:
                            if isinstance(c, dict):
                                if c.get('column_name') == col:
                                    col_classification = c
                                    break
                            else:
                                # Assume it's a dataclass with column_name attribute  
                                if hasattr(c, 'column_name') and c.column_name == col:
                                    col_classification = asdict(c) if hasattr(c, '__dataclass_fields__') else c
                                    break
                        
                        if col_classification:
                            safe_message = safe_log_message(f"   - '{col}' -> {col_classification['data_type']} (confidence: {col_classification['confidence']:.2f})")
                            logger.info(safe_message)
                
                # Filter the DataFrame to only include relevant columns
                if filtering_result.relevant_columns:
                    df_filtered = df[filtering_result.relevant_columns].copy()
                    safe_message = safe_log_message(f"\n[TARGET] FILTERED DATASET FOR ANALYSIS:")
                    logger.info(safe_message)
                    logger.info(f"   - Columns After Filtering: {len(df_filtered.columns)}")
                    logger.info(f"   - Columns Used: {list(df_filtered.columns)}")
                    logger.info(f"   - Rows: {len(df_filtered)} (unchanged)")
                else:
                    logger.warning("[WARNING] No relevant columns found! Using original dataset as fallback.")
                    df_filtered = df.copy()
            else:
                logger.error(safe_log_message(f"⚠️ Filtering failed: {filtering_response.get('message', 'Unknown error')}"))
                logger.info("Using original dataset without filtering.")
                df_filtered = df.copy()
                filtering_result = DataFilteringResult(
                    relevant_columns=list(df.columns),
                    irrelevant_columns=[],
                    metadata_columns=[],
                    column_classifications=[],
                    confidence_score=0.0,
                    filtering_summary="Filtering failed, using original data",
                    total_columns_analyzed=len(df.columns),
                    columns_filtered=0,
                    data_retention_percentage=100.0
                )
            
            logger.info("=" * 80)
            
            if fast_mode:
                # Fast mode: Rule-based analysis with minimal AI calls
                logger.info("Step 1/6: Performing fast data analysis...")
                data_profile = await self._perform_fast_data_analysis(df_filtered)
                
                logger.info("Step 2/6: Detecting business patterns...")
                business_patterns = self._detect_business_patterns_fast(df_filtered, business_context)
                
                logger.info("Step 3/6: Generating charts...")
                enhanced_charts = await self._generate_charts_fast(df_filtered, business_patterns, data_profile)
                
                logger.info("Step 4/6: Generating KPIs...")
                enhanced_kpis = self._generate_kpis_fast(df_filtered, business_patterns)
                
                logger.info("Step 5/6: Creating insights...")
                statistical_insights = self._generate_basic_insights(df_filtered, data_profile)
                ai_narrative = f"Intelligent analysis of {filename} with {len(df_filtered)} rows and {len(df_filtered.columns)} relevant columns (filtered from {len(df.columns)} original columns)."
                
                logger.info("Step 6/6: Optimizing layout...")
                optimized_layout = self._create_standard_layout(enhanced_charts, enhanced_kpis)
            else:
                # Full mode: AI-powered analysis (slower but more comprehensive)
                data_profile = await self._perform_deep_data_analysis(df_filtered)
                business_patterns = await self._detect_business_patterns(df_filtered, business_context)
                enhanced_charts = await self._generate_ai_enhanced_charts(df_filtered, business_patterns, data_profile)
                enhanced_kpis = await self._generate_enhanced_kpis(df_filtered, business_patterns)
                statistical_insights = await self._generate_statistical_insights(df_filtered, data_profile)
                ai_narrative = await self._generate_ai_narrative(df_filtered, business_patterns, statistical_insights)
                optimized_layout = await self._optimize_dashboard_layout(enhanced_charts, enhanced_kpis)
            
            # Build enhanced dashboard configuration
            dashboard_config = {
                "title": f"Enhanced Analytics Dashboard: {filename}",
                "description": f"AI-powered comprehensive analysis with {len(enhanced_charts)} interactive visualizations from {len(df_filtered.columns)} relevant columns",
                "metadata": {
                    "analysis_type": "enhanced_ai_analytics_with_intelligent_filtering",
                    "ai_provider": self.config.get_model_config().get("provider", "unknown"),
                    "original_rows": len(df),
                    "original_columns": len(df.columns),
                    "filtered_columns": len(df_filtered.columns),
                    "filtering_confidence": filtering_result.confidence_score,
                    "data_retention_percentage": filtering_result.data_retention_percentage,
                    "irrelevant_columns_filtered": len(filtering_result.irrelevant_columns),
                    "business_patterns_detected": len(business_patterns),
                    "insights_generated": len(statistical_insights),
                    "analysis_timestamp": datetime.now().isoformat(),
                    "filtering_summary": filtering_result.filtering_summary
                },
                "charts": [self._convert_chart_to_dict(chart) for chart in enhanced_charts],
                "kpis": enhanced_kpis,
                "insights": {
                    "ai_narrative": ai_narrative,
                    "business_patterns": [asdict(pattern) for pattern in business_patterns],
                    "statistical_insights": [asdict(insight) for insight in statistical_insights],
                    "data_profile": data_profile,
                    "data_filtering": {
                        "summary": filtering_result.filtering_summary,
                        "relevant_columns": filtering_result.relevant_columns,
                        "irrelevant_columns": filtering_result.irrelevant_columns,
                        "metadata_columns": filtering_result.metadata_columns,
                        "confidence_score": filtering_result.confidence_score,
                        "data_retention_percentage": filtering_result.data_retention_percentage,
                        "column_classifications": [
                            asdict(classification) if hasattr(classification, '__dataclass_fields__') else classification 
                            for classification in filtering_result.column_classifications
                        ]
                    },
                    "recommendations": await self._generate_actionable_recommendations(business_patterns, statistical_insights)
                },
                "layout": optimized_layout,
                "theme": {
                    "color_palette": "business_professional",
                    "chart_style": "interactive_modern",
                    "interactivity": "enhanced",
                    "accessibility": "wcag_aa_compliant"
                },
                "advanced_features": {
                    "real_time_capable": True,
                    "export_options": ["pdf", "png", "html", "excel", "powerpoint"],
                    "collaboration_ready": True,
                    "mobile_optimized": True
                }
            }
            
            logger.info(safe_log_message(f"✅ Enhanced dashboard generated with {len(enhanced_charts)} charts and {len(statistical_insights)} insights"))
            logger.info(safe_log_message(f"📊 Data filtering applied: {len(filtering_result.irrelevant_columns)} columns filtered out, {filtering_result.data_retention_percentage:.1f}% data retained"))
            return dashboard_config
            
        except Exception as e:
            logger.error(f"Enhanced analytics failed: {str(e)}")
            raise
    
    def _convert_to_json_safe(self, obj: Any) -> Any:
        """Convert object to JSON-safe format."""
        if isinstance(obj, dict):
            return {str(k): self._convert_to_json_safe(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._convert_to_json_safe(item) for item in obj]
        elif isinstance(obj, (pd.Timestamp, datetime)):
            return obj.isoformat() if obj is not pd.NaT else None
        elif isinstance(obj, (np.integer, np.floating)):
            return float(obj) if not pd.isna(obj) else None
        elif pd.isna(obj):
            return None
        else:
            return str(obj)
    
    async def _perform_deep_data_analysis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Perform comprehensive data analysis."""
        try:
            logger.info("\n" + "[ANALYSIS]" * 20)
            logger.info("[ANALYSIS] ENHANCED AI: DEEP DATA ANALYSIS")
            logger.info("[ANALYSIS]" * 20)
            
            logger.info(f"[CHART] Enhanced Analytics Input:")
            logger.info(f"   - DataFrame Shape: {df.shape}")
            logger.info(f"   - Column Names: {list(df.columns)}")
            logger.info(f"   - Data Types: {df.dtypes.to_dict()}")
            
            analysis = {
                "data_quality": {
                    "completeness": (1 - df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100,
                    "duplicates": df.duplicated().sum(),
                    "unique_ratios": {col: df[col].nunique() / len(df) for col in df.columns}
                },
                "column_analysis": {},
                "relationships": {},
                "outliers": {},
                "distributions": {}
            }
            
            logger.info(f"\n[TREND] DATA QUALITY ASSESSMENT:")
            logger.info(f"   - Completeness: {analysis['data_quality']['completeness']:.1f}%")
            logger.info(f"   - Duplicate Rows: {analysis['data_quality']['duplicates']}")
            logger.info(f"   - Average Unique Ratio: {sum(analysis['data_quality']['unique_ratios'].values()) / len(df.columns):.3f}")
            
            # Analyze each column
            logger.info(f"\n[SEARCH] ENHANCED COLUMN-BY-COLUMN ANALYSIS:")
            for col in df.columns:
                try:
                    col_name = str(col)  # Ensure column name is string
                    col_series = df[col]
                    
                    logger.info(f"\n   [PIN] Enhanced Analysis - Column: '{col_name}'")
                    
                    col_analysis = {
                        "type": self._determine_column_type(col_series),
                        "missing_rate": float(col_series.isnull().sum() / len(df) * 100),
                        "unique_count": int(col_series.nunique()),
                        "cardinality": ("high" if col_series.nunique() / len(df) > 0.95 
                                      else "medium" if col_series.nunique() / len(df) > 0.1 
                                      else "low")
                    }
                    
                    logger.info(f"      - Column Type: {col_analysis['type']}")
                    logger.info(f"      - Missing Rate: {col_analysis['missing_rate']:.1f}%")
                    logger.info(f"      - Unique Values: {col_analysis['unique_count']}")
                    logger.info(f"      - Cardinality: {col_analysis['cardinality']}")
                    
                    if pd.api.types.is_numeric_dtype(col_series):
                        try:
                            clean_series = col_series.dropna()
                            if len(clean_series) > 0:
                                mean_val = float(clean_series.mean())
                                std_val = float(clean_series.std())
                                skewness_val = float(clean_series.skew()) if not pd.isna(clean_series.skew()) else 0.0
                                outlier_count = self._detect_outliers(clean_series)
                                
                                col_analysis.update({
                                    "mean": mean_val,
                                    "std": std_val,
                                    "skewness": skewness_val,
                                    "outlier_count": outlier_count
                                })
                                
                                logger.info(f"      - Statistical Summary:")
                                logger.info(f"        • Mean: {mean_val:,.2f}")
                                logger.info(f"        • Standard Deviation: {std_val:,.2f}")
                                logger.info(f"        • Skewness: {skewness_val:.3f}")
                                logger.info(f"        • Outliers Detected: {outlier_count}")
                                
                                # Business context interpretation
                                if 'revenue' in col_name.lower() or 'sales' in col_name.lower() or 'amount' in col_name.lower():
                                    logger.info(f"      🤖 AI Business Context: REVENUE/FINANCIAL DATA")
                                    logger.info(f"         - Recommended for: KPIs, Revenue Charts, Trend Analysis")
                                elif 'quantity' in col_name.lower() or 'qty' in col_name.lower() or 'count' in col_name.lower():
                                    logger.info(f"      🤖 AI Business Context: QUANTITY/VOLUME DATA")
                                    logger.info(f"         - Recommended for: Volume KPIs, Distribution Analysis")
                                else:
                                    logger.info(f"      🤖 AI Business Context: GENERAL METRIC")
                                    logger.info(f"         - Recommended for: Comparative Analysis, Overview Charts")
                                    
                            else:
                                col_analysis.update({
                                    "mean": 0.0, "std": 0.0, "skewness": 0.0, "outlier_count": 0
                                })
                                logger.info(f"      ⚠️ No valid numeric data for statistical analysis")
                        except Exception as e:
                            logger.warning(f"      ❌ Error analyzing numeric column {col_name}: {e}")
                            col_analysis.update({
                                "mean": 0.0, "std": 0.0, "skewness": 0.0, "outlier_count": 0
                            })
                    
                    elif col_analysis["type"] == "categorical":
                        top_values = col_series.value_counts().head(5)
                        logger.info(f"      - Top Categories: {top_values.to_dict()}")
                        
                        # Business context for categorical data
                        if any(pattern in col_name.lower() for pattern in ['location', 'city', 'region', 'country']):
                            logger.info(f"      🤖 AI Business Context: GEOGRAPHICAL DATA")
                            logger.info(f"         - Recommended for: Geographic Breakdown Charts, Location-based KPIs")
                        elif any(pattern in col_name.lower() for pattern in ['category', 'type', 'class', 'segment']):
                            logger.info(f"      🤖 AI Business Context: CATEGORY/CLASSIFICATION DATA")
                            logger.info(f"         - Recommended for: Distribution Charts, Category Analysis")
                        elif any(pattern in col_name.lower() for pattern in ['id', 'key', 'code', 'ref']):
                            logger.info(f"      🤖 AI Business Context: IDENTIFIER DATA")
                            logger.info(f"         - Recommended action: EXCLUDE from charts (used for joining/filtering)")
                        else:
                            logger.info(f"      🤖 AI Business Context: GENERAL CATEGORICAL DATA")
                            logger.info(f"         - Recommended for: Distribution Analysis, Grouping")
                    
                    analysis["column_analysis"][col_name] = col_analysis
                    
                except Exception as e:
                    logger.warning(f"      ❌ Error analyzing column {col}: {e}")
                    continue
            
            # Detect correlations for numeric columns
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            logger.info(f"\n🔗 CORRELATION ANALYSIS:")
            logger.info(f"   - Numeric Columns for Correlation: {list(numeric_cols)}")
            
            if len(numeric_cols) > 1:
                correlation_matrix = df[numeric_cols].corr()
                strong_correlations = []
                for i in range(len(correlation_matrix.columns)):
                    for j in range(i+1, len(correlation_matrix.columns)):
                        corr_value = correlation_matrix.iloc[i, j]
                        if abs(corr_value) > 0.7:
                            strong_correlations.append({
                                "col1": correlation_matrix.columns[i],
                                "col2": correlation_matrix.columns[j],
                                "correlation": float(corr_value)
                            })
                            logger.info(f"   🔗 Strong Correlation Found: {correlation_matrix.columns[i]} ↔ {correlation_matrix.columns[j]} (r={corr_value:.3f})")
                
                analysis["relationships"]["strong_correlations"] = strong_correlations
                
                if strong_correlations:
                    logger.info(f"   ✅ Total Strong Correlations: {len(strong_correlations)}")
                    logger.info(f"   🤖 AI Recommendation: Use correlated variables for advanced insights and predictive modeling")
                else:
                    logger.info(f"   📊 No strong correlations detected (threshold: |r| > 0.7)")
            else:
                logger.info(f"   ⏭️ Insufficient numeric columns for correlation analysis")
            
            logger.info("🔬" * 60)
            logger.info("✅ ENHANCED DEEP DATA ANALYSIS COMPLETED")
            logger.info("🔬" * 60)
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Enhanced deep data analysis failed: {e}")
            return {"error": str(e)}
    
    async def _detect_business_patterns(self, df: pd.DataFrame, context: Optional[str]) -> List[BusinessPattern]:
        """Detect business patterns using AI analysis."""
        try:
            logger.info("\n" + "🤖" * 60)
            logger.info("🤖 AI MODEL: BUSINESS PATTERN DETECTION")
            logger.info("🤖" * 60)
            
            logger.info(f"📋 AI Pattern Detection Input:")
            logger.info(f"   - Business Context: {context}")
            logger.info(f"   - DataFrame Shape: {df.shape}")
            logger.info(f"   - Available Columns: {list(df.columns)}")
            
            # Prepare data summary for AI analysis with safe serialization
            sample_data = df.head(5).copy()
            
            # Convert datetime columns to strings for JSON serialization
            for col in sample_data.columns:
                if pd.api.types.is_datetime64_any_dtype(sample_data[col]):
                    sample_data[col] = sample_data[col].astype(str)
                elif sample_data[col].dtype == 'object':
                    # Handle mixed types in object columns
                    sample_data[col] = sample_data[col].astype(str)
            
            # Get statistics only for numeric columns
            numeric_df = df.select_dtypes(include=[np.number])
            statistics = {}
            if len(numeric_df.columns) > 0:
                stats_dict = numeric_df.describe().to_dict()
                # Convert numpy types to Python types for JSON serialization
                for col, col_stats in stats_dict.items():
                    statistics[col] = {k: float(v) if not pd.isna(v) else None for k, v in col_stats.items()}
            
            data_summary = {
                "columns": [str(col) for col in df.columns],
                "dtypes": {str(col): str(dtype) for col, dtype in df.dtypes.items()},
                "sample_data": self._convert_to_json_safe(sample_data.to_dict()),
                "statistics": statistics
            }
            
            logger.info(f"\n📊 Sending to AI Model:")
            logger.info(f"   - Column Names: {data_summary['columns']}")
            logger.info(f"   - Data Types: {data_summary['dtypes']}")
            logger.info(f"   - Numeric Statistics Available: {len(statistics)} columns")
            logger.info(f"   - Sample Data Size: {len(sample_data)} rows")
            
            pattern_detection_prompt = f"""
Analyze this dataset and identify business patterns that would be valuable for dashboard visualization:

Data Context: {context or 'General business data analysis'}
Columns: {data_summary['columns']}
Data Types: {data_summary['dtypes']}
Sample Data: {json.dumps(data_summary['sample_data'], indent=2)[:1000]}...

Identify 3-5 key business patterns such as:
1. Revenue/Performance trends
2. Categorical comparisons
3. Time-based patterns
4. Geographical patterns
5. Customer/Product segmentation patterns
6. Operational efficiency patterns

For each pattern, provide:
- Pattern type
- Description
- Columns involved
- Business impact
- Recommended visualization types
"""
            
            logger.info(f"\n🤖 CALLING AI MODEL FOR PATTERN DETECTION...")
            logger.info(f"   - Prompt Length: {len(pattern_detection_prompt)} characters")
            logger.info(f"   - Expected Response: JSON with business patterns")
            
            response_format = {
                "patterns": [
                    {
                        "pattern_type": "string",
                        "description": "string",
                        "columns_involved": ["string"],
                        "confidence": "float",
                        "business_impact": "string",
                        "recommended_visualizations": ["string"]
                    }
                ]
            }
            
            try:
                # Call AI model for pattern detection
                if self.litellm_service and await self.litellm_service.is_available():
                    logger.info(f"   ✅ AI Service Available - Making Pattern Detection Call")
                    
                    ai_response = await self.litellm_service.generate_response(
                        pattern_detection_prompt,
                        response_format=response_format,
                        max_tokens=2000,
                        temperature=0.3
                    )
                    
                    logger.info(f"   ✅ AI MODEL RESPONSE RECEIVED")
                    logger.info(f"      - Response Length: {len(str(ai_response))} characters")
                    
                    # Parse AI response
                    if isinstance(ai_response, dict) and "patterns" in ai_response:
                        patterns_data = ai_response["patterns"]
                        logger.info(f"      - Patterns Detected by AI: {len(patterns_data)}")
                        
                        patterns = []
                        for i, pattern_data in enumerate(patterns_data, 1):
                            logger.info(f"\n   📊 AI Pattern #{i}:")
                            logger.info(f"      - Type: {pattern_data.get('pattern_type', 'unknown')}")
                            logger.info(f"      - Description: {pattern_data.get('description', 'N/A')[:100]}...")
                            logger.info(f"      - Columns: {pattern_data.get('columns_involved', [])}")
                            logger.info(f"      - Confidence: {pattern_data.get('confidence', 0):.2f}")
                            logger.info(f"      - Business Impact: {pattern_data.get('business_impact', 'N/A')[:100]}...")
                            logger.info(f"      - Recommended Charts: {pattern_data.get('recommended_visualizations', [])}")
                            
                            # Validate that columns exist in the dataframe
                            valid_columns = [col for col in pattern_data.get('columns_involved', []) if col in df.columns]
                            if valid_columns:
                                pattern = BusinessPattern(
                                    pattern_type=pattern_data.get('pattern_type', 'general'),
                                    description=pattern_data.get('description', ''),
                                    columns_involved=valid_columns,
                                    confidence=float(pattern_data.get('confidence', 0.5)),
                                    business_impact=pattern_data.get('business_impact', ''),
                                    recommended_visualizations=pattern_data.get('recommended_visualizations', ['bar'])
                                )
                                patterns.append(pattern)
                                logger.info(f"      ✅ Pattern validated and added")
                            else:
                                logger.warning(f"      ❌ Pattern skipped - no valid columns found")
                        
                        logger.info(f"\n🎯 AI PATTERN DETECTION SUMMARY:")
                        logger.info(f"   - Total Patterns from AI: {len(patterns_data)}")
                        logger.info(f"   - Valid Patterns Added: {len(patterns)}")
                        logger.info(f"   - Average AI Confidence: {sum(p.confidence for p in patterns) / max(len(patterns), 1):.2f}")
                        
                        logger.info("🤖" * 60)
                        logger.info("✅ AI BUSINESS PATTERN DETECTION COMPLETED")
                        logger.info("🤖" * 60)
                        
                        return patterns
                    else:
                        logger.warning(f"   ⚠️ Unexpected AI response format: {type(ai_response)}")
                        
                else:
                    logger.warning(f"   ❌ AI Service Not Available - Using Fallback Pattern Detection")
                    
            except Exception as e:
                logger.error(f"   ❌ AI Pattern Detection Failed: {e}")
                logger.info(f"   🔄 Falling back to rule-based pattern detection")
            
            # Fallback to rule-based detection
            logger.info(f"\n🔄 USING FALLBACK PATTERN DETECTION:")
            fallback_patterns = self._generate_fallback_patterns(df)
            logger.info(f"   - Fallback Patterns Generated: {len(fallback_patterns)}")
            for i, pattern in enumerate(fallback_patterns, 1):
                logger.info(f"      {i}. {pattern.pattern_type}: {pattern.description}")
            
            return fallback_patterns
            
        except Exception as e:
            logger.error(f"❌ Business pattern detection failed: {e}")
            return self._generate_fallback_patterns(df)
    
    async def _generate_ai_enhanced_charts(
        self, 
        df: pd.DataFrame, 
        patterns: List[BusinessPattern], 
        data_profile: Dict[str, Any]
    ) -> List[EnhancedChartRecommendation]:
        """Generate enhanced chart recommendations using AI insights."""
        try:
            charts = []
            
            for pattern in patterns:
                # Validate columns exist in dataframe
                valid_columns = [col for col in pattern.columns_involved if col in df.columns]
                if not valid_columns:
                    continue
                
                # Generate chart for each pattern
                chart_recommendation = await self._generate_pattern_chart(df, pattern, valid_columns)
                if chart_recommendation:
                    charts.append(chart_recommendation)
            
            # Add supplementary charts based on data characteristics
            supplementary_charts = await self._generate_supplementary_charts(df, data_profile)
            charts.extend(supplementary_charts)
            
            # Ensure we have at least 4-6 charts for a comprehensive dashboard
            if len(charts) < 4:
                additional_charts = await self._generate_additional_charts(df, 4 - len(charts))
                charts.extend(additional_charts)
            
            logger.info(f"Generated {len(charts)} enhanced chart recommendations")
            return charts[:8]  # Limit to 8 charts for optimal dashboard performance
            
        except Exception as e:
            logger.error(f"Enhanced chart generation failed: {e}")
            return []
    
    async def _generate_pattern_chart(
        self, 
        df: pd.DataFrame, 
        pattern: BusinessPattern, 
        columns: List[str]
    ) -> Optional[EnhancedChartRecommendation]:
        """Generate a chart for a specific business pattern."""
        try:
            # Determine best chart type for pattern
            chart_type = self._select_optimal_chart_type(pattern, df[columns])
            
            # Prepare chart data
            chart_data = self._prepare_chart_data(df, columns, chart_type)
            
            # Generate AI reasoning for chart
            reasoning_prompt = f"""
Explain why a {chart_type} chart is optimal for visualizing this business pattern:

Pattern: {pattern.description}
Data columns: {columns}
Pattern type: {pattern.pattern_type}
Business impact: {pattern.business_impact}

Provide a concise explanation of:
1. Why this chart type is most effective
2. What insights it will reveal
3. How it supports business decision-making
"""
            
            ai_reasoning = await generate_ai_response(reasoning_prompt)
            
            # Build enhanced chart recommendation
            chart = EnhancedChartRecommendation(
                chart_type=chart_type,
                data_columns=columns,
                title=f"{pattern.pattern_type.replace('_', ' ').title()} Analysis",
                description=pattern.description,
                business_context=pattern.business_impact,
                confidence=pattern.confidence,
                ai_reasoning=ai_reasoning,
                statistical_basis=f"Based on {len(chart_data)} data points with {pattern.confidence:.1%} confidence",
                interactivity_features=self._get_interactivity_features(chart_type),
                recharts_config=self._build_enhanced_recharts_config(chart_type, columns),
                data=chart_data[:100]  # Limit data points for performance
            )
            
            return chart
            
        except Exception as e:
            logger.error(f"Pattern chart generation failed: {e}")
            return None
    
    async def _generate_enhanced_kpis(self, df: pd.DataFrame, patterns: List[BusinessPattern]) -> List[Dict[str, Any]]:
        """Generate enhanced KPIs with business context and improved accuracy."""
        try:
            kpis = []
            
            # Get numeric columns for KPI calculation
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            
            # Determine KPI types based on column names and patterns
            financial_cols = [col for col in numeric_cols if any(term in str(col).lower() 
                            for term in ['revenue', 'sales', 'amount', 'price', 'cost', 'profit', 'income'])]
            performance_cols = [col for col in numeric_cols if any(term in str(col).lower() 
                              for term in ['score', 'rating', 'performance', 'efficiency', 'rate'])]
            count_cols = [col for col in numeric_cols if any(term in str(col).lower() 
                         for term in ['count', 'number', 'quantity', 'total'])]
            
            # Process KPIs by category
            processed_cols = set()
            
            # Financial KPIs (highest priority)
            for col in financial_cols[:3]:
                if col in processed_cols:
                    continue
                kpi = self._create_financial_kpi(df, col, patterns)
                if kpi:
                    kpis.append(kpi)
                    processed_cols.add(col)
            
            # Performance KPIs
            for col in performance_cols[:2]:
                if col in processed_cols or len(kpis) >= 6:
                    continue
                kpi = self._create_performance_kpi(df, col, patterns)
                if kpi:
                    kpis.append(kpi)
                    processed_cols.add(col)
            
            # Count/Volume KPIs
            for col in count_cols[:2]:
                if col in processed_cols or len(kpis) >= 6:
                    continue
                kpi = self._create_volume_kpi(df, col, patterns)
                if kpi:
                    kpis.append(kpi)
                    processed_cols.add(col)
            
            # Fill remaining slots with general numeric KPIs
            remaining_cols = [col for col in numeric_cols if col not in processed_cols]
            for col in remaining_cols[:max(0, 6 - len(kpis))]:
                kpi = self._create_general_kpi(df, col, patterns)
                if kpi:
                    kpis.append(kpi)
            
            # Ensure we have at least one KPI
            if not kpis and numeric_cols:
                fallback_kpi = self._create_general_kpi(df, numeric_cols[0], patterns)
                if fallback_kpi:
                    kpis.append(fallback_kpi)
            
            return kpis[:6]  # Limit to 6 KPIs
            
        except Exception as e:
            logger.error(f"Enhanced KPI generation failed: {e}")
            return self._create_fallback_kpis(df)

    def _create_financial_kpi(self, df: pd.DataFrame, col: str, patterns: List[BusinessPattern]) -> Optional[Dict[str, Any]]:
        """Create a financial KPI with proper formatting and analysis."""
        try:
            col_data = df[col].dropna()
            if len(col_data) == 0:
                return None
            
            total_value = float(col_data.sum())
            average_value = float(col_data.mean())
            
            # Calculate trend
            trend_info = self._calculate_trend(col_data)
            
            # Format display name
            display_name = self._format_legend_name(str(col))
            
            # Determine business context
            business_context = self._get_pattern_context(col, patterns)
            if not business_context:
                if 'revenue' in str(col).lower() or 'sales' in str(col).lower():
                    business_context = "Key revenue metric driving business growth"
                elif 'cost' in str(col).lower():
                    business_context = "Cost management indicator for operational efficiency"
                else:
                    business_context = f"Financial metric for {display_name.lower()} analysis"
            
            return {
                "id": f"kpi_financial_{col}",
                "title": display_name,
                "value": total_value,
                "formatted_value": self._format_financial_value(total_value),
                "secondary_value": average_value,
                "secondary_formatted": self._format_financial_value(average_value),
                "secondary_label": "Average",
                "trend_percentage": trend_info["percentage"],
                "trend_direction": trend_info["direction"],
                "description": f"Total {display_name.lower()} across all records",
                "business_context": business_context,
                "confidence": 0.95,
                "format_type": "currency",
                "metadata": {
                    "data_points": int(len(col_data)),
                    "data_quality": self._assess_data_quality(col_data),
                    "category": "financial"
                }
            }
            
        except Exception as e:
            logger.warning(f"Failed to create financial KPI for {col}: {e}")
            return None

    def _create_performance_kpi(self, df: pd.DataFrame, col: str, patterns: List[BusinessPattern]) -> Optional[Dict[str, Any]]:
        """Create a performance KPI with appropriate scaling and context."""
        try:
            col_data = df[col].dropna()
            if len(col_data) == 0:
                return None
            
            # For performance metrics, average is often more meaningful than sum
            if 'score' in str(col).lower() or 'rating' in str(col).lower():
                primary_value = float(col_data.mean())
                secondary_value = float(col_data.max())
                secondary_label = "Best"
            else:
                primary_value = float(col_data.sum())
                secondary_value = float(col_data.mean())
                secondary_label = "Average"
            
            trend_info = self._calculate_trend(col_data)
            display_name = self._format_legend_name(str(col))
            business_context = self._get_pattern_context(col, patterns) or f"Performance indicator for {display_name.lower()}"
            
            return {
                "id": f"kpi_performance_{col}",
                "title": display_name,
                "value": primary_value,
                "formatted_value": self._format_performance_value(primary_value),
                "secondary_value": secondary_value,
                "secondary_formatted": self._format_performance_value(secondary_value),
                "secondary_label": secondary_label,
                "trend_percentage": trend_info["percentage"],
                "trend_direction": trend_info["direction"],
                "description": f"{display_name} performance metrics",
                "business_context": business_context,
                "confidence": 0.9,
                "format_type": "percentage" if 'rate' in str(col).lower() else "number",
                "metadata": {
                    "data_points": int(len(col_data)),
                    "data_quality": self._assess_data_quality(col_data),
                    "category": "performance"
                }
            }
            
        except Exception as e:
            logger.warning(f"Failed to create performance KPI for {col}: {e}")
            return None

    def _create_volume_kpi(self, df: pd.DataFrame, col: str, patterns: List[BusinessPattern]) -> Optional[Dict[str, Any]]:
        """Create a volume/count KPI with meaningful aggregations."""
        try:
            col_data = df[col].dropna()
            if len(col_data) == 0:
                return None
            
            total_value = float(col_data.sum())
            average_value = float(col_data.mean())
            
            trend_info = self._calculate_trend(col_data)
            display_name = self._format_legend_name(str(col))
            business_context = self._get_pattern_context(col, patterns) or f"Volume metric for {display_name.lower()}"
            
            return {
                "id": f"kpi_volume_{col}",
                "title": display_name,
                "value": total_value,
                "formatted_value": self._format_volume_value(total_value),
                "secondary_value": average_value,
                "secondary_formatted": self._format_volume_value(average_value),
                "secondary_label": "Average",
                "trend_percentage": trend_info["percentage"],
                "trend_direction": trend_info["direction"],
                "description": f"Total {display_name.lower()} volume",
                "business_context": business_context,
                "confidence": 0.85,
                "format_type": "number",
                "metadata": {
                    "data_points": int(len(col_data)),
                    "data_quality": self._assess_data_quality(col_data),
                    "category": "volume"
                }
            }
            
        except Exception as e:
            logger.warning(f"Failed to create volume KPI for {col}: {e}")
            return None

    def _create_general_kpi(self, df: pd.DataFrame, col: str, patterns: List[BusinessPattern]) -> Optional[Dict[str, Any]]:
        """Create a general KPI for any numeric column."""
        try:
            col_data = df[col].dropna()
            if len(col_data) == 0:
                return None
            
            primary_value = float(col_data.sum())
            secondary_value = float(col_data.mean())
            
            trend_info = self._calculate_trend(col_data)
            display_name = self._format_legend_name(str(col))
            business_context = self._get_pattern_context(col, patterns) or f"Metric for {display_name.lower()}"
            
            return {
                "id": f"kpi_general_{col}",
                "title": display_name,
                "value": primary_value,
                "formatted_value": self._format_kpi_value(primary_value),
                "secondary_value": secondary_value,
                "secondary_formatted": self._format_kpi_value(secondary_value),
                "secondary_label": "Average",
                "trend_percentage": trend_info["percentage"],
                "trend_direction": trend_info["direction"],
                "description": f"Summary statistics for {display_name.lower()}",
                "business_context": business_context,
                "confidence": 0.8,
                "format_type": "number",
                "metadata": {
                    "data_points": int(len(col_data)),
                    "data_quality": self._assess_data_quality(col_data),
                    "category": "general"
                }
            }
            
        except Exception as e:
            logger.warning(f"Failed to create general KPI for {col}: {e}")
            return None

    def _calculate_trend(self, series: pd.Series) -> Dict[str, Any]:
        """Calculate trend information for a time series."""
        try:
            if len(series) < 2:
                return {"percentage": 0, "direction": "neutral"}
            
            # Split data into first and second half
            mid_point = len(series) // 2
            first_half = series.iloc[:mid_point]
            second_half = series.iloc[mid_point:]
            
            first_mean = first_half.mean()
            second_mean = second_half.mean()
            
            if pd.isna(first_mean) or pd.isna(second_mean) or first_mean == 0:
                return {"percentage": 0, "direction": "neutral"}
            
            percentage_change = ((second_mean - first_mean) / abs(first_mean)) * 100
            
            if abs(percentage_change) < 1:  # Less than 1% change
                direction = "neutral"
            elif percentage_change > 0:
                direction = "up"
            else:
                direction = "down"
            
            return {
                "percentage": float(abs(percentage_change)),
                "direction": direction
            }
            
        except Exception as e:
            logger.warning(f"Trend calculation failed: {e}")
            return {"percentage": 0, "direction": "neutral"}

    def _get_pattern_context(self, col: str, patterns: List[BusinessPattern]) -> Optional[str]:
        """Get business context for a column from detected patterns."""
        col_str = str(col)
        for pattern in patterns:
            if col_str in [str(c) for c in pattern.columns_involved]:
                return pattern.business_impact
        return None

    def _assess_data_quality(self, series: pd.Series) -> str:
        """Assess the quality of data in a series."""
        try:
            if len(series) == 0:
                return "no_data"
            
            null_percentage = series.isnull().sum() / len(series)
            
            if null_percentage > 0.5:
                return "poor"
            elif null_percentage > 0.2:
                return "medium"
            else:
                return "high"
                
        except Exception:
            return "unknown"

    def _format_financial_value(self, value: float) -> str:
        """Format financial values with appropriate currency symbols and scaling."""
        try:
            abs_value = abs(value)
            if abs_value >= 1_000_000_000:
                return f"${value/1_000_000_000:.1f}B"
            elif abs_value >= 1_000_000:
                return f"${value/1_000_000:.1f}M"
            elif abs_value >= 1_000:
                return f"${value/1_000:.1f}K"
            else:
                return f"${value:.0f}"
        except Exception:
            return str(value)

    def _format_performance_value(self, value: float) -> str:
        """Format performance values appropriately."""
        try:
            if 0 <= value <= 10:  # Likely a score out of 10
                return f"{value:.1f}/10"
            elif 0 <= value <= 100:  # Likely a percentage or score out of 100
                return f"{value:.1f}%"
            else:
                return f"{value:.2f}"
        except Exception:
            return str(value)

    def _format_volume_value(self, value: float) -> str:
        """Format volume/count values."""
        try:
            abs_value = abs(value)
            if abs_value >= 1_000_000:
                return f"{value/1_000_000:.1f}M"
            elif abs_value >= 1_000:
                return f"{value/1_000:.1f}K"
            else:
                return f"{value:.0f}"
        except Exception:
            return str(value)

    def _create_fallback_kpis(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Create basic fallback KPIs when advanced generation fails."""
        try:
            kpis = [
                {
                    "id": "kpi_fallback_records",
                    "title": "Total Records",
                    "value": len(df),
                    "formatted_value": self._format_volume_value(len(df)),
                    "trend_percentage": 0,
                    "trend_direction": "neutral",
                    "description": "Total number of records in dataset",
                    "business_context": "Data volume indicator",
                    "confidence": 1.0,
                    "format_type": "number",
                    "metadata": {
                        "data_points": len(df),
                        "data_quality": "high",
                        "category": "general"
                    }
                },
                {
                    "id": "kpi_fallback_columns",
                    "title": "Data Columns",
                    "value": len(df.columns),
                    "formatted_value": str(len(df.columns)),
                    "trend_percentage": 0,
                    "trend_direction": "neutral",
                    "description": "Number of data columns available",
                    "business_context": "Data richness indicator",
                    "confidence": 1.0,
                    "format_type": "number",
                    "metadata": {
                        "data_points": len(df.columns),
                        "data_quality": "high",
                        "category": "general"
                    }
                }
            ]
            
            # Add a numeric column KPI if available
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            if numeric_cols:
                col = numeric_cols[0]
                col_data = df[col].dropna()
                if len(col_data) > 0:
                    kpis.append({
                        "id": f"kpi_fallback_{col}",
                        "title": self._format_legend_name(str(col)),
                        "value": float(col_data.sum()),
                        "formatted_value": self._format_kpi_value(float(col_data.sum())),
                        "trend_percentage": 0,
                        "trend_direction": "neutral",
                        "description": f"Total {self._format_legend_name(str(col)).lower()}",
                        "business_context": "Primary numeric metric",
                        "confidence": 0.7,
                        "format_type": "number",
                        "metadata": {
                            "data_points": int(len(col_data)),
                            "data_quality": self._assess_data_quality(col_data),
                            "category": "general"
                        }
                    })
            
            return kpis
            
        except Exception as e:
            logger.error(f"Fallback KPI creation failed: {e}")
            return []
    
    async def _generate_statistical_insights(self, df: pd.DataFrame, data_profile: Dict[str, Any]) -> List[DataInsight]:
        """Generate statistical insights about the data."""
        try:
            insights = []
            
            # Data quality insights
            if data_profile.get("data_quality", {}).get("completeness", 0) < 90:
                insights.append(DataInsight(
                    insight_type="data_quality",
                    title="Data Completeness Alert",
                    description=f"Dataset has {data_profile['data_quality']['completeness']:.1f}% completeness",
                    confidence=0.95,
                    data_evidence={"completeness_rate": data_profile["data_quality"]["completeness"]},
                    recommendation="Consider data cleaning or imputation strategies",
                    visualization_suggestion="Show data quality metrics in a separate panel"
                ))
            
            # Strong correlation insights
            strong_correlations = data_profile.get("relationships", {}).get("strong_correlations", [])
            if strong_correlations:
                for corr in strong_correlations[:2]:  # Limit to top 2
                    insights.append(DataInsight(
                        insight_type="correlation",
                        title=f"Strong Correlation Detected",
                        description=f"{corr['col1']} and {corr['col2']} have a correlation of {corr['correlation']:.2f}",
                        confidence=abs(corr['correlation']),
                        data_evidence=corr,
                        recommendation="Consider using one variable to predict the other or investigate causation",
                        visualization_suggestion="Create a scatter plot to visualize this relationship"
                    ))
            
            # Distribution insights
            for col, analysis in data_profile.get("column_analysis", {}).items():
                if analysis.get("type") == "numeric" and analysis.get("skewness"):
                    skewness = analysis["skewness"]
                    if abs(skewness) > 1:
                        insights.append(DataInsight(
                            insight_type="distribution",
                            title=f"Skewed Distribution in {col}",
                            description=f"{col} shows {'positive' if skewness > 0 else 'negative'} skewness ({skewness:.2f})",
                            confidence=min(abs(skewness) / 2, 0.95),
                            data_evidence={"skewness": skewness, "column": col},
                            recommendation="Consider data transformation for modeling or highlight outliers",
                            visualization_suggestion="Use a histogram or box plot to show distribution shape"
                        ))
            
            return insights[:5]  # Limit to 5 key insights
            
        except Exception as e:
            logger.error(f"Statistical insights generation failed: {e}")
            return []
    
    async def _generate_ai_narrative(
        self, 
        df: pd.DataFrame, 
        patterns: List[BusinessPattern], 
        insights: List[DataInsight]
    ) -> str:
        """Generate AI-powered narrative summary of the analysis."""
        try:
            narrative_prompt = f"""
Create a comprehensive executive summary of this data analysis:

Dataset Overview:
- {len(df)} records with {len(df.columns)} variables
- Key columns: {list(df.columns)[:10]}

Business Patterns Identified:
{json.dumps([{'type': p.pattern_type, 'description': p.description, 'impact': p.business_impact} for p in patterns[:3]], indent=2)}

Statistical Insights:
{json.dumps([{'type': i.insight_type, 'title': i.title, 'recommendation': i.recommendation} for i in insights[:3]], indent=2)}

Write a clear, executive-level summary that:
1. Highlights the most important findings
2. Explains business implications
3. Provides actionable recommendations
4. Maintains a professional, analytical tone

Keep it under 300 words and focus on business value.
"""
            
            narrative = await generate_ai_response(narrative_prompt)
            return narrative
            
        except Exception as e:
            logger.error(f"AI narrative generation failed: {e}")
            return f"Analysis of {len(df)} records revealed {len(patterns)} key business patterns and {len(insights)} statistical insights. The data shows strong potential for operational optimization and strategic decision-making."
    
    # Helper methods
    def _determine_column_type(self, series: pd.Series) -> str:
        """Determine the semantic type of a column."""
        if pd.api.types.is_numeric_dtype(series):
            return "numeric"
        elif pd.api.types.is_datetime64_any_dtype(series):
            return "datetime"
        elif series.dtype == 'bool':
            return "boolean"
        else:
            return "categorical"
    
    def _detect_outliers(self, series: pd.Series) -> int:
        """Detect outliers using IQR method."""
        try:
            Q1 = series.quantile(0.25)
            Q3 = series.quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            return len(series[(series < lower_bound) | (series > upper_bound)])
        except:
            return 0
    
    def _generate_fallback_patterns(self, df: pd.DataFrame) -> List[BusinessPattern]:
        """Generate fallback business patterns when AI analysis fails."""
        patterns = []
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
        
        if numeric_cols and categorical_cols:
            patterns.append(BusinessPattern(
                pattern_type="performance_comparison",
                description=f"Comparison of {numeric_cols[0]} across {categorical_cols[0]} categories",
                columns_involved=[numeric_cols[0], categorical_cols[0]],
                confidence=0.8,
                business_impact="Identify top performing categories",
                recommended_visualizations=["bar", "pie"]
            ))
        
        if len(numeric_cols) >= 2:
            patterns.append(BusinessPattern(
                pattern_type="correlation_analysis",
                description=f"Relationship between {numeric_cols[0]} and {numeric_cols[1]}",
                columns_involved=numeric_cols[:2],
                confidence=0.7,
                business_impact="Understand metric relationships",
                recommended_visualizations=["scatter", "line"]
            ))
        
        return patterns
    
    def _select_optimal_chart_type(self, pattern: BusinessPattern, data: pd.DataFrame) -> str:
        """Select optimal chart type based on business pattern and data characteristics."""
        try:
            pattern_type = pattern.pattern_type.lower()
            columns = pattern.columns_involved
            
            # Get data characteristics
            numeric_cols = [col for col in columns if pd.api.types.is_numeric_dtype(data[col])]
            categorical_cols = [col for col in columns if not pd.api.types.is_numeric_dtype(data[col])]
            
            # Enhanced decision logic based on pattern and data characteristics
            if pattern_type in ["categorical_analysis", "distribution_analysis"]:
                # For categorical analysis, prefer pie charts if we have 1 categorical + 1 numeric
                if len(categorical_cols) >= 1 and len(numeric_cols) >= 1:
                    # Check if categorical data is suitable for pie chart
                    cat_col = categorical_cols[0]
                    unique_categories = data[cat_col].nunique()
                    if 2 <= unique_categories <= 8:  # Good range for pie charts
                        return "pie"
                    else:
                        return "bar"  # Too many categories for pie chart
                elif len(categorical_cols) >= 1:
                    # Only categorical data, use bar chart
                    return "bar"
                else:
                    return "bar"  # Default for distribution
            
            elif pattern_type in ["financial_metrics", "performance_comparison"]:
                # Financial and performance data often work well with bar charts
                if len(categorical_cols) >= 1 and len(numeric_cols) >= 1:
                    return "bar"
                elif len(numeric_cols) >= 2:
                    return "scatter"  # For comparing two metrics
                else:
                    return "bar"
            
            elif pattern_type in ["temporal_trends", "time_series"]:
                # Time-based data should use line or area charts
                has_time_column = any('date' in str(col).lower() or 'time' in str(col).lower() 
                                    for col in columns)
                if has_time_column and len(numeric_cols) >= 1:
                    return "line"
                elif len(numeric_cols) >= 2:
                    return "line"  # Assume sequential data
                else:
                    return "area"
            
            elif pattern_type in ["correlation_analysis"]:
                # Correlation analysis works best with scatter plots
                if len(numeric_cols) >= 2:
                    return "scatter"
                else:
                    return "bar"
            
            else:
                # General fallback logic based on data types
                if len(categorical_cols) >= 1 and len(numeric_cols) >= 1:
                    # Check if suitable for pie chart
                    cat_col = categorical_cols[0]
                    unique_categories = data[cat_col].nunique()
                    if 2 <= unique_categories <= 6:
                        return "pie"
                    else:
                        return "bar"
                elif len(numeric_cols) >= 2:
                    return "scatter"
                elif len(numeric_cols) == 1:
                    return "bar"
                else:
                    return "bar"  # Default fallback
            
        except Exception as e:
            logger.warning(f"Chart type selection failed: {e}")
            # Safe fallback
            return "bar"
    
    def _prepare_chart_data(self, df: pd.DataFrame, columns: List[str], chart_type: str) -> List[Dict[str, Any]]:
        """Prepare data for chart visualization with improved accuracy and validation."""
        try:
            # Filter columns to only include those that exist in the dataframe
            valid_columns = [str(col) for col in columns if str(col) in df.columns]
            if not valid_columns:
                return [{"name": "No Data", "value": 0}]
            
            # Identify numeric and categorical columns with better type checking
            numeric_cols = []
            categorical_cols = []
            
            for col in valid_columns:
                try:
                    # Check if column contains meaningful numeric data
                    if pd.api.types.is_numeric_dtype(df[col]):
                        non_null_data = df[col].dropna()
                        # Ensure we have at least 1 non-null value and it's not all zeros
                        if len(non_null_data) > 0 and not (non_null_data == 0).all():
                            numeric_cols.append(col)
                        else:
                            # Try to see if it's meaningful categorical data
                            if df[col].nunique() <= 20:  # Reasonable number of categories
                                categorical_cols.append(col)
                    elif df[col].dtype == 'object' or df[col].dtype.name == 'category':
                        # Validate categorical data
                        unique_count = df[col].nunique()
                        if 1 < unique_count <= 50:  # Reasonable range for categories
                            categorical_cols.append(col)
                except Exception as e:
                    logger.warning(f"Error processing column {col}: {e}")
                    continue
            
            # Improved chart-specific data preparation
            if chart_type in ["pie"]:
                return self._prepare_pie_chart_data(df, categorical_cols, numeric_cols, valid_columns)
            elif chart_type in ["bar"]:
                return self._prepare_bar_chart_data(df, categorical_cols, numeric_cols, valid_columns)
            elif chart_type in ["line", "area"]:
                return self._prepare_line_area_chart_data(df, categorical_cols, numeric_cols, valid_columns)
            elif chart_type == "scatter":
                return self._prepare_scatter_chart_data(df, numeric_cols)
            else:
                # Default: create meaningful summary data
                return self._prepare_default_chart_data(df, valid_columns)
            
        except Exception as e:
            logger.warning(f"Chart data preparation failed: {e}")
            return [{"name": "Data Available", "value": len(df)}]

    def _prepare_pie_chart_data(self, df: pd.DataFrame, categorical_cols: List[str], 
                              numeric_cols: List[str], valid_columns: List[str]) -> List[Dict[str, Any]]:
        """Prepare data specifically optimized for pie charts."""
        try:
            if categorical_cols and numeric_cols:
                # Group by category and sum numeric values
                cat_col = categorical_cols[0]
                num_col = numeric_cols[0]
                
                # Clean and group data
                grouped = df.groupby(cat_col)[num_col].sum().sort_values(ascending=False)
                
                # Filter out zero/negative values for pie charts
                grouped = grouped[grouped > 0]
                
                # Limit to top 8 categories and format names
                top_categories = grouped.head(8)
                
                chart_data = []
                for category, value in top_categories.items():
                    formatted_name = self._format_legend_name(str(category))
                    chart_data.append({
                        "name": formatted_name,
                        "value": float(value),
                        "percentage": float((value / top_categories.sum()) * 100)
                    })
                
                return chart_data
                
            elif categorical_cols:
                # Use value counts for categorical data
                cat_col = categorical_cols[0]
                value_counts = df[cat_col].value_counts().head(8)
                
                chart_data = []
                total = value_counts.sum()
                for category, count in value_counts.items():
                    formatted_name = self._format_legend_name(str(category))
                    chart_data.append({
                        "name": formatted_name,
                        "value": int(count),
                        "percentage": float((count / total) * 100)
                    })
                
                return chart_data
            else:
                return [{"name": "Total Records", "value": len(df), "percentage": 100.0}]
                
        except Exception as e:
            logger.warning(f"Pie chart data preparation failed: {e}")
            return [{"name": "Data", "value": len(df), "percentage": 100.0}]

    def _prepare_bar_chart_data(self, df: pd.DataFrame, categorical_cols: List[str], 
                              numeric_cols: List[str], valid_columns: List[str]) -> List[Dict[str, Any]]:
        """Prepare data specifically optimized for bar charts."""
        try:
            if categorical_cols and numeric_cols:
                cat_col = categorical_cols[0]
                num_col = numeric_cols[0]
                
                # Group and aggregate data
                grouped = df.groupby(cat_col)[num_col].agg(['sum', 'mean', 'count']).reset_index()
                grouped = grouped.sort_values('sum', ascending=False).head(12)
                
                chart_data = []
                for _, row in grouped.iterrows():
                    formatted_name = self._format_legend_name(str(row[cat_col]))
                    chart_data.append({
                        "name": formatted_name,
                        "value": float(row['sum']),
                        "average": float(row['mean']),
                        "count": int(row['count'])
                    })
                
                return chart_data
                
            elif categorical_cols:
                cat_col = categorical_cols[0]
                value_counts = df[cat_col].value_counts().head(12)
                
                chart_data = []
                for category, count in value_counts.items():
                    formatted_name = self._format_legend_name(str(category))
                    chart_data.append({
                        "name": formatted_name,
                        "value": int(count)
                    })
                
                return chart_data
                
            elif numeric_cols:
                # Create aggregated metrics for numeric data
                chart_data = []
                for col in numeric_cols[:5]:
                    col_data = df[col].dropna()
                    if len(col_data) > 0:
                        formatted_name = self._format_legend_name(str(col))
                        chart_data.append({
                            "name": f"Total {formatted_name}",
                            "value": float(col_data.sum())
                        })
                        if len(col_data) > 1:
                            chart_data.append({
                                "name": f"Avg {formatted_name}",
                                "value": float(col_data.mean())
                            })
                
                return chart_data
            else:
                return [{"name": "Total Records", "value": len(df)}]
                
        except Exception as e:
            logger.warning(f"Bar chart data preparation failed: {e}")
            return [{"name": "Data Available", "value": len(df)}]

    def _prepare_line_area_chart_data(self, df: pd.DataFrame, categorical_cols: List[str], 
                                    numeric_cols: List[str], valid_columns: List[str]) -> List[Dict[str, Any]]:
        """Prepare data specifically optimized for line and area charts."""
        try:
            chart_data = []
            
            if len(valid_columns) >= 2:
                x_col = valid_columns[0]
                y_col = valid_columns[1] if valid_columns[1] in numeric_cols else (numeric_cols[0] if numeric_cols else None)
                
                if y_col is None:
                    # If no numeric column available, create index-based data
                    for i in range(min(50, len(df))):
                        chart_data.append({
                            "x": i + 1,
                            "y": i + 1,
                            "label": f"Point {i + 1}"
                        })
                    return chart_data
                
                # Sort data if x_col appears to be temporal or ordinal
                df_sorted = df.copy()
                if pd.api.types.is_datetime64_any_dtype(df[x_col]) or 'date' in str(x_col).lower():
                    df_sorted = df_sorted.sort_values(x_col)
                
                # Sample data if too large
                sample_size = min(100, len(df_sorted))
                if len(df_sorted) > sample_size:
                    df_sample = df_sorted.sample(n=sample_size).sort_index()
                else:
                    df_sample = df_sorted
                
                for i, (_, row) in enumerate(df_sample.iterrows()):
                    x_val = row[x_col]
                    y_val = row[y_col]
                    
                    # Format x value
                    if pd.api.types.is_datetime64_any_dtype(df[x_col]):
                        x_formatted = x_val.strftime('%Y-%m-%d') if pd.notna(x_val) else f"Point {i+1}"
                    elif pd.api.types.is_numeric_dtype(df[x_col]):
                        x_formatted = float(x_val) if pd.notna(x_val) else i
                    else:
                        x_formatted = self._format_legend_name(str(x_val)) if pd.notna(x_val) else f"Point {i+1}"
                    
                    # Format y value
                    y_formatted = float(y_val) if pd.notna(y_val) and pd.api.types.is_numeric_dtype(df[y_col]) else 0
                    
                    chart_data.append({
                        "x": x_formatted,
                        "y": y_formatted,
                        "label": f"{self._format_legend_name(str(x_col))}: {x_formatted}"
                    })
                
                return chart_data
            else:
                # Simple sequential data
                for i in range(min(50, len(df))):
                    chart_data.append({
                        "x": i + 1,
                        "y": i + 1,
                        "label": f"Data Point {i + 1}"
                    })
                return chart_data
                
        except Exception as e:
            logger.warning(f"Line/Area chart data preparation failed: {e}")
            return [{"x": 1, "y": 1, "label": "Data Point 1"}]

    def _prepare_scatter_chart_data(self, df: pd.DataFrame, numeric_cols: List[str]) -> List[Dict[str, Any]]:
        """Prepare data specifically optimized for scatter plots."""
        try:
            if len(numeric_cols) >= 2:
                x_col, y_col = numeric_cols[0], numeric_cols[1]
                
                # Clean data and remove outliers
                df_clean = df[[x_col, y_col]].dropna()
                
                # Remove extreme outliers (beyond 3 standard deviations)
                for col in [x_col, y_col]:
                    mean_val = df_clean[col].mean()
                    std_val = df_clean[col].std()
                    lower_bound = mean_val - 3 * std_val
                    upper_bound = mean_val + 3 * std_val
                    df_clean = df_clean[(df_clean[col] >= lower_bound) & (df_clean[col] <= upper_bound)]
                
                # Sample data if too large
                if len(df_clean) > 200:
                    df_clean = df_clean.sample(n=200)
                
                chart_data = []
                for _, row in df_clean.iterrows():
                    chart_data.append({
                        "x": float(row[x_col]),
                        "y": float(row[y_col]),
                        "x_label": self._format_legend_name(str(x_col)),
                        "y_label": self._format_legend_name(str(y_col))
                    })
                
                return chart_data
            else:
                return [{"x": 0, "y": 0, "x_label": "X", "y_label": "Y"}]
                
        except Exception as e:
            logger.warning(f"Scatter chart data preparation failed: {e}")
            return [{"x": 0, "y": 0, "x_label": "X", "y_label": "Y"}]

    def _prepare_default_chart_data(self, df: pd.DataFrame, valid_columns: List[str]) -> List[Dict[str, Any]]:
        """Prepare default chart data when other methods fail."""
        try:
            # Create summary statistics for each column
            chart_data = []
            numeric_cols = [col for col in valid_columns if pd.api.types.is_numeric_dtype(df[col])]
            
            for col in numeric_cols[:6]:  # Limit to 6 columns
                col_data = df[col].dropna()
                if len(col_data) > 0:
                    formatted_name = self._format_legend_name(str(col))
                    chart_data.append({
                        "name": formatted_name,
                        "value": float(col_data.sum()),
                        "average": float(col_data.mean()),
                        "max": float(col_data.max()),
                        "min": float(col_data.min())
                    })
            
            if not chart_data:
                chart_data = [{"name": "Total Records", "value": len(df)}]
            
            return chart_data
            
        except Exception as e:
            logger.warning(f"Default chart data preparation failed: {e}")
            return [{"name": "Data Available", "value": len(df)}]

    def _format_legend_name(self, name: str) -> str:
        """Format column names for better legend display."""
        if not name or pd.isna(name):
            return "Unknown"
        
        # Convert to string and clean
        formatted = str(name).strip()
        
        # Replace underscores and common separators with spaces
        formatted = re.sub(r'[_\-\.]+', ' ', formatted)
        
        # Handle camelCase
        formatted = re.sub(r'([a-z])([A-Z])', r'\1 \2', formatted)
        
        # Title case and clean up spaces
        formatted = ' '.join(word.capitalize() for word in formatted.split())
        
        # Handle common abbreviations
        abbreviations = {
            'Id': 'ID',
            'Url': 'URL',
            'Api': 'API',
            'Sql': 'SQL',
            'Http': 'HTTP',
            'Uuid': 'UUID',
            'Json': 'JSON'
        }
        
        for abbr, replacement in abbreviations.items():
            formatted = re.sub(r'\b' + abbr + r'\b', replacement, formatted)
        
        # Limit length for display
        if len(formatted) > 30:
            formatted = formatted[:27] + "..."
        
        return formatted
    
    def _get_interactivity_features(self, chart_type: str) -> List[str]:
        """Get recommended interactivity features for a chart type."""
        base_features = ["hover_details", "animation"]
        
        if chart_type in ["line", "area"]:
            return base_features + ["zoom_pan", "brushing"]
        elif chart_type == "bar":
            return base_features + ["drill_down"]
        elif chart_type == "scatter":
            return base_features + ["zoom_pan", "brushing"]
        elif chart_type == "pie":
            return base_features + ["drill_down"]
        else:
            return base_features
    
    def _build_enhanced_recharts_config(self, chart_type: str, columns: List[str]) -> Dict[str, Any]:
        """Build enhanced Recharts configuration with improved legends and formatting."""
        # Format column names for better display
        formatted_columns = [self._format_legend_name(str(col)) for col in columns]
        
        base_config = {
            "height": 400,
            "margin": {"top": 20, "right": 30, "left": 20, "bottom": 60},
            "animation": True,
            "legend": {
                "enabled": True,
                "position": "bottom",
                "align": "center",
                "verticalAlign": "bottom",
                "wrapperStyle": {"fontSize": "12px", "paddingTop": "10px"}
            },
            "tooltip": {
                "enabled": True,
                "cursor": True,
                "contentStyle": {
                    "backgroundColor": "rgba(17, 24, 39, 0.95)",
                    "border": "1px solid rgba(55, 65, 81, 0.5)",
                    "borderRadius": "6px",
                    "color": "#ffffff"
                }
            },
            "grid": {
                "enabled": True,
                "strokeDasharray": "3 3",
                "opacity": 0.3
            }
        }
        
        if chart_type == "line":
            return {
                **base_config,
                "type": "LineChart",
                "dataKey": "y",
                "xAxisKey": "x",
                "xaxis_title": formatted_columns[0] if len(formatted_columns) > 0 else "X",
                "yaxis_title": formatted_columns[1] if len(formatted_columns) > 1 else "Y",
                "line": {
                    "type": "monotone",
                    "strokeWidth": 3,
                    "dot": {"r": 4, "strokeWidth": 2},
                    "activeDot": {"r": 6, "strokeWidth": 2}
                }
            }
        elif chart_type == "bar":
            return {
                **base_config,
                "type": "BarChart",
                "dataKey": "value",
                "xAxisKey": "name",
                "xaxis_title": "Categories",
                "yaxis_title": formatted_columns[1] if len(formatted_columns) > 1 else "Values",
                "bar": {
                    "radius": [4, 4, 0, 0],
                    "fillOpacity": 0.8
                }
            }
        elif chart_type == "pie":
            return {
                **base_config,
                "type": "PieChart",
                "dataKey": "value",
                "nameKey": "name",
                "cx": "50%",
                "cy": "45%",
                "outerRadius": 100,
                "innerRadius": 0,
                "legend": {
                    "enabled": True,
                    "position": "right",
                    "align": "middle",
                    "verticalAlign": "middle",
                    "wrapperStyle": {"fontSize": "11px", "lineHeight": "16px"}
                },
                "label": {
                    "enabled": True,
                    "position": "outside",
                    "formatter": "percent"
                },
                "tooltip": {
                    "enabled": True,
                    "formatter": "value_and_percent"
                }
            }
        elif chart_type == "area":
            return {
                **base_config,
                "type": "AreaChart",
                "dataKey": "y",
                "xAxisKey": "x",
                "xaxis_title": formatted_columns[0] if len(formatted_columns) > 0 else "X",
                "yaxis_title": formatted_columns[1] if len(formatted_columns) > 1 else "Y",
                "area": {
                    "type": "monotone",
                    "strokeWidth": 3,
                    "fillOpacity": 0.3,
                    "dot": {"r": 4, "strokeWidth": 2},
                    "activeDot": {"r": 6, "strokeWidth": 2}
                }
            }
        elif chart_type == "scatter":
            return {
                **base_config,
                "type": "ScatterChart",
                "dataKey": "y",
                "xAxisKey": "x",
                "xaxis_title": formatted_columns[0] if len(formatted_columns) > 0 else "X",
                "yaxis_title": formatted_columns[1] if len(formatted_columns) > 1 else "Y",
                "scatter": {
                    "fill": "#8884d8",
                    "fillOpacity": 0.6,
                    "strokeWidth": 1
                }
            }
        else:
            return base_config
    
    def _format_kpi_value(self, value: float) -> str:
        """Format KPI value for display."""
        if abs(value) >= 1_000_000:
            return f"{value/1_000_000:.1f}M"
        elif abs(value) >= 1_000:
            return f"{value/1_000:.1f}K"
        else:
            return f"{value:.0f}"
    
    async def _generate_supplementary_charts(self, df: pd.DataFrame, data_profile: Dict[str, Any]) -> List[EnhancedChartRecommendation]:
        """Generate additional charts based on data characteristics."""
        charts = []
        
        # Add correlation heatmap if multiple numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if len(numeric_cols) > 2:
            # Implementation for correlation heatmap
            pass
        
        # Add distribution chart for key numeric column
        if numeric_cols:
            # Implementation for distribution chart
            pass
        
        return charts
    
    async def _generate_additional_charts(self, df: pd.DataFrame, count_needed: int) -> List[EnhancedChartRecommendation]:
        """Generate additional charts to reach minimum count."""
        charts = []
        
        # Simple fallback chart generation
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
        
        for i in range(min(count_needed, len(numeric_cols))):
            col = numeric_cols[i]
            chart_data = [{"name": "Total", "value": float(df[col].sum())}]
            
            chart = EnhancedChartRecommendation(
                chart_type="bar",
                data_columns=[col],
                title=f"{col.replace('_', ' ').title()} Summary",
                description=f"Overview of {col.replace('_', ' ').lower()} values",
                business_context="Additional metric for comprehensive analysis",
                confidence=0.6,
                ai_reasoning="Auto-generated supplementary chart for dashboard completeness",
                statistical_basis=f"Based on {len(df)} data points",
                interactivity_features=["hover_details"],
                recharts_config=self._build_enhanced_recharts_config("bar", [col]),
                data=chart_data
            )
            charts.append(chart)
        
        return charts
    
    async def _optimize_dashboard_layout(self, charts: List[EnhancedChartRecommendation], kpis: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Optimize dashboard layout based on content."""
        return {
            "type": "enhanced_grid",
            "responsive": True,
            "sections": [
                {"type": "kpi_overview", "span": 12, "charts": len(kpis)},
                {"type": "primary_charts", "span": 8, "charts": len(charts[:4])},
                {"type": "secondary_charts", "span": 4, "charts": len(charts[4:])},
                {"type": "insights_panel", "span": 12}
            ],
            "breakpoints": {
                "lg": {"cols": 12, "rowHeight": 300},
                "md": {"cols": 8, "rowHeight": 250},
                "sm": {"cols": 4, "rowHeight": 200}
            }
        }
    
    async def _generate_actionable_recommendations(self, patterns: List[BusinessPattern], insights: List[DataInsight]) -> List[str]:
        """Generate actionable business recommendations."""
        recommendations = []
        
        for pattern in patterns[:3]:
            recommendations.append(f"Focus on {pattern.pattern_type.replace('_', ' ')}: {pattern.business_impact}")
        
        for insight in insights[:2]:
            recommendations.append(f"Address {insight.insight_type}: {insight.recommendation}")
        
        return recommendations
    
    def _convert_chart_to_dict(self, chart: EnhancedChartRecommendation) -> Dict[str, Any]:
        """Convert enhanced chart recommendation to dictionary."""
        return {
            "chart_type": chart.chart_type,
            "data_columns": chart.data_columns,
            "title": chart.title,
            "description": chart.description,
            "business_context": chart.business_context,
            "confidence": chart.confidence,
            "ai_reasoning": chart.ai_reasoning,
            "statistical_basis": chart.statistical_basis,
            "interactivity_features": chart.interactivity_features,
            "recharts_config": chart.recharts_config,
            "data": chart.data,
            "kpi_connection": chart.kpi_connection
        }
    
    # ========== FAST MODE METHODS (Optimized for Speed) ==========
    
    async def _perform_fast_data_analysis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Perform quick data analysis without AI calls."""
        try:
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
            datetime_cols = df.select_dtypes(include=['datetime64[ns]', 'datetime64']).columns.tolist()
            
            return {
                "data_quality": {
                    "completeness": float((1 - df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100),
                    "duplicates": int(df.duplicated().sum()),
                    "total_rows": len(df),
                    "total_columns": len(df.columns)
                },
                "column_types": {
                    "numeric": len(numeric_cols),
                    "categorical": len(categorical_cols),
                    "datetime": len(datetime_cols)
                },
                "column_names": {
                    "numeric": numeric_cols,
                    "categorical": categorical_cols,
                    "datetime": datetime_cols
                }
            }
        except Exception as e:
            logger.error(f"Fast data analysis failed: {e}")
            return {"error": str(e)}
    
    def _detect_business_patterns_fast(self, df: pd.DataFrame, context: Optional[str]) -> List[BusinessPattern]:
        """Detect business patterns using rule-based analysis (no AI)."""
        try:
            patterns = []
            
            # Pattern 1: Revenue/Sales patterns
            revenue_cols = [col for col in df.columns if any(term in str(col).lower() for term in ['revenue', 'sales', 'amount', 'total', 'value', 'price'])]
            if revenue_cols:
                patterns.append(BusinessPattern(
                    pattern_type="financial_metrics",
                    description=f"Financial data detected in columns: {', '.join(revenue_cols[:3])}",
                    columns_involved=revenue_cols[:3],
                    confidence=0.9,
                    business_impact="Key financial indicators for business performance tracking",
                    recommended_visualizations=["bar", "line", "pie"]
                ))
            
            # Pattern 2: Time series patterns
            time_cols = [col for col in df.columns if any(term in str(col).lower() for term in ['date', 'time', 'month', 'year', 'period'])]
            if time_cols and revenue_cols:
                patterns.append(BusinessPattern(
                    pattern_type="temporal_trends",
                    description=f"Time-based analysis available for {time_cols[0]} vs {revenue_cols[0]}",
                    columns_involved=[time_cols[0], revenue_cols[0]],
                    confidence=0.8,
                    business_impact="Track performance trends over time",
                    recommended_visualizations=["line", "area"]
                ))
            
            # Pattern 3: Category patterns (optimized for pie charts)
            category_cols = [col for col in df.columns if any(term in str(col).lower() for term in ['category', 'type', 'region', 'location', 'department', 'product'])]
            if category_cols and revenue_cols:
                patterns.append(BusinessPattern(
                    pattern_type="categorical_analysis",
                    description=f"Category breakdown: {category_cols[0]} performance analysis",
                    columns_involved=[category_cols[0], revenue_cols[0]],
                    confidence=0.85,
                    business_impact="Identify top performing categories/segments",
                    recommended_visualizations=["pie", "bar"]
                ))
            
            # Pattern 4: Distribution patterns (pie chart focused)
            if category_cols:
                patterns.append(BusinessPattern(
                    pattern_type="distribution_analysis",
                    description=f"Distribution breakdown of {category_cols[0]}",
                    columns_involved=[category_cols[0]],
                    confidence=0.8,
                    business_impact="Understand data distribution across categories",
                    recommended_visualizations=["pie", "bar"]
                ))
            
            # Fallback: General analysis
            if not patterns:
                numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                if numeric_cols:
                    patterns.append(BusinessPattern(
                        pattern_type="general_metrics",
                        description=f"General data analysis for {len(numeric_cols)} numeric columns",
                        columns_involved=numeric_cols[:3],
                        confidence=0.7,
                        business_impact="Overall data insights and metrics overview",
                        recommended_visualizations=["bar", "line"]
                    ))
            
            return patterns
            
        except Exception as e:
            logger.error(f"Fast pattern detection failed: {e}")
            return self._generate_fallback_patterns(df)
    
    async def _generate_charts_fast(self, df: pd.DataFrame, patterns: List[BusinessPattern], data_profile: Dict[str, Any]) -> List[EnhancedChartRecommendation]:
        """Generate charts quickly using rule-based logic."""
        try:
            charts = []
            
            for pattern in patterns[:4]:  # Limit to 4 charts for fast processing
                chart_type = self._select_optimal_chart_type(pattern, df)
                columns = pattern.columns_involved[:2]  # Max 2 columns per chart
                
                # Prepare chart data
                chart_data = self._prepare_chart_data(df, columns, chart_type)
                
                # Create chart with simple reasoning
                chart = EnhancedChartRecommendation(
                    chart_type=chart_type,
                    data_columns=columns,
                    title=f"{pattern.pattern_type.replace('_', ' ').title()}",
                    description=pattern.description,
                    business_context=pattern.business_impact,
                    confidence=pattern.confidence,
                    ai_reasoning=f"Rule-based selection: {chart_type} optimal for {pattern.pattern_type}",
                    statistical_basis=f"Based on {len(df)} records",
                    interactivity_features=self._get_interactivity_features(chart_type),
                    recharts_config=self._build_enhanced_recharts_config(chart_type, columns),
                    data=chart_data
                )
                charts.append(chart)
            
            # Ensure minimum 3 charts
            if len(charts) < 3:
                additional_charts = await self._generate_additional_charts(df, 3 - len(charts))
                charts.extend(additional_charts)
            
            return charts
            
        except Exception as e:
            logger.error(f"Fast chart generation failed: {e}")
            return []
    
    def _generate_kpis_fast(self, df: pd.DataFrame, patterns: List[BusinessPattern]) -> List[Dict[str, Any]]:
        """Generate KPIs quickly using rule-based logic."""
        try:
            kpis = []
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            
            # Generate up to 6 KPIs
            for i, col in enumerate(numeric_cols[:6]):
                try:
                    col_name = str(col)
                    col_data = df[col].dropna()
                    
                    if len(col_data) == 0:
                        continue
                    
                    kpi_value = float(col_data.sum())
                    
                    # Simple trend calculation
                    trend_percentage = 0
                    trend_direction = "neutral"
                    if len(col_data) > 1:
                        first_half = col_data.iloc[:len(col_data)//2].mean()
                        second_half = col_data.iloc[len(col_data)//2:].mean()
                        if first_half > 0:
                            trend_percentage = ((second_half - first_half) / first_half) * 100
                            trend_direction = "up" if trend_percentage > 0 else "down"
                    
                    # Determine format type
                    format_type = "currency" if any(term in col_name.lower() for term in ['revenue', 'sales', 'amount', 'price', 'cost']) else "number"
                    
                    kpi = {
                        "name": col_name.replace('_', ' ').title(),
                        "value": kpi_value,
                        "trend_percentage": abs(trend_percentage),
                        "trend": trend_direction,
                        "description": f"Total {col_name.replace('_', ' ').lower()} across all records",
                        "format_type": format_type
                    }
                    kpis.append(kpi)
                    
                except Exception as e:
                    logger.warning(f"Error generating KPI for column {col}: {e}")
                    continue
            
            return kpis
            
        except Exception as e:
            logger.error(f"Fast KPI generation failed: {e}")
            return []
    
    def _generate_basic_insights(self, df: pd.DataFrame, data_profile: Dict[str, Any]) -> List[DataInsight]:
        """Generate basic insights without AI calls."""
        try:
            insights = []
            
            # Data quality insight
            completeness = data_profile.get("data_quality", {}).get("completeness", 0)
            if completeness < 90:
                insights.append(DataInsight(
                    insight_type="data_quality",
                    title="Data Completeness Alert",
                    description=f"Dataset is {completeness:.1f}% complete. Consider cleaning missing values.",
                    confidence=0.9,
                    data_evidence={"completeness": completeness},
                    recommendation="Review and handle missing data appropriately",
                    visualization_suggestion="data_quality_chart"
                ))
            
            # Data size insight
            insights.append(DataInsight(
                insight_type="data_overview",
                title="Dataset Overview",
                description=f"Analysis of {len(df)} records across {len(df.columns)} dimensions",
                confidence=1.0,
                data_evidence={"rows": len(df), "columns": len(df.columns)},
                recommendation="Explore individual metrics and trends in the charts below",
                visualization_suggestion="overview_dashboard"
            ))
            
            return insights
            
        except Exception as e:
            logger.error(f"Basic insights generation failed: {e}")
            return []
    
    def _create_standard_layout(self, charts: List[EnhancedChartRecommendation], kpis: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a standard dashboard layout without AI optimization."""
        return {
            "type": "standard_grid",
            "responsive": True,
            "sections": [
                {"type": "kpi_overview", "span": 12, "charts": len(kpis)},
                {"type": "main_charts", "span": 12, "charts": len(charts)}
            ],
            "breakpoints": {
                "lg": {"cols": 12, "rowHeight": 300},
                "md": {"cols": 8, "rowHeight": 250},
                "sm": {"cols": 4, "rowHeight": 200}
            }
        }

# Import safe Unicode utilities
from src.core.unicode_utils import safe_log_message, safe_str