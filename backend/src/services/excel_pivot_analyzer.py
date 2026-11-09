"""
Excel Pivot Table Analyzer Service
Analyzes Excel data, detects existing pivot tables, and creates new ones using AI guidance.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
import logging
from dataclasses import dataclass
import json
from google import genai
from google.genai import types
import os

logger = logging.getLogger(__name__)

@dataclass
class PivotTableRecommendation:
    """Data class for pivot table recommendations."""
    rows: List[str]
    columns: List[str]
    values: List[str]
    aggfunc: str
    title: str
    description: str
    confidence: float
    business_value: str

@dataclass 
class PivotTableData:
    """Data class for pivot table results."""
    pivot_df: pd.DataFrame
    recommendation: PivotTableRecommendation
    summary_stats: Dict[str, Any]

class ExcelPivotAnalyzer:
    """
    AI-powered Excel pivot table analyzer that:
    1. Detects existing pivot tables in Excel files
    2. Analyzes data structure and business context
    3. Recommends optimal pivot table configurations
    4. Creates pivot tables for better chart generation
    """
    
    def __init__(self):
        self.client = self._initialize_genai_client()
        
    def _initialize_genai_client(self):
        """Initialize Google GenAI client with proper configuration."""
        try:
            # Check if we should use Vertex AI or Gemini Developer API
            use_vertex = os.getenv('GOOGLE_GENAI_USE_VERTEXAI', '0') == '1'
            
            if use_vertex:
                project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
                location = os.getenv('GOOGLE_CLOUD_LOCATION', 'us-central1')
                if not project_id:
                    raise ValueError("GOOGLE_CLOUD_PROJECT not set for Vertex AI")
                
                client = genai.Client(vertexai=True, project=project_id, location=location)
                logger.info(f"Initialized Vertex AI client for project {project_id}")
            else:
                api_key = os.getenv('GOOGLE_API_KEY')
                if not api_key:
                    raise ValueError("GOOGLE_API_KEY not set for Gemini Developer API")
                
                client = genai.Client(api_key=api_key)
                logger.info("Initialized Gemini Developer API client")
                
            return client
        except Exception as e:
            logger.error(f"Failed to initialize GenAI client: {str(e)}")
            return None
    
    async def analyze_excel_data(self, data: Dict[str, Any], original_filename: str = None) -> Dict[str, Any]:
        """
        Comprehensive analysis of Excel data to determine optimal pivot table strategy.
        
        Args:
            data: Parsed Excel data from file_parser
            original_filename: Original Excel filename for context
            
        Returns:
            Analysis results with pivot table recommendations
        """
        try:
            logger.info("Starting AI-powered Excel data analysis...")
            
            # Convert data to DataFrame for analysis
            df = self._prepare_dataframe(data)
            if df is None or df.empty:
                return {"error": "No valid data to analyze"}
            
            # Step 1: Detect existing pivot tables
            existing_pivots = await self._detect_existing_pivot_tables(data, original_filename)
            
            # Step 2: Analyze data structure and business context
            data_analysis = await self._analyze_data_structure(df, original_filename)
            
            # Step 3: Generate AI-driven pivot table recommendations
            pivot_recommendations = await self._generate_pivot_recommendations(df, data_analysis, existing_pivots)
            
            # Step 4: Create recommended pivot tables
            created_pivots = await self._create_pivot_tables(df, pivot_recommendations)
            
            # Step 5: Generate final analysis report
            analysis_report = {
                "original_data_shape": df.shape,
                "existing_pivot_tables": existing_pivots,
                "data_analysis": data_analysis,
                "pivot_recommendations": [rec.__dict__ for rec in pivot_recommendations],
                "created_pivot_tables": len(created_pivots),
                "pivot_data": created_pivots,
                "ai_insights": data_analysis.get("ai_insights", {}),
                "recommendation_strategy": "ai_driven_pivot_analysis"
            }
            
            logger.info(f"Excel analysis completed: {len(pivot_recommendations)} recommendations, {len(created_pivots)} pivots created")
            return analysis_report
            
        except Exception as e:
            logger.error(f"Excel data analysis failed: {str(e)}")
            return {"error": f"Analysis failed: {str(e)}"}
    
    def _prepare_dataframe(self, data: Dict[str, Any]) -> Optional[pd.DataFrame]:
        """Convert parsed data to pandas DataFrame."""
        try:
            if isinstance(data, dict) and 'data' in data:
                data = data['data']
            
            if isinstance(data, list) and len(data) > 0:
                df = pd.DataFrame(data)
            elif isinstance(data, dict):
                df = pd.DataFrame([data])
            else:
                return None
                
            # Clean column names
            df.columns = df.columns.astype(str)
            
            # Remove completely empty rows and columns
            df = df.dropna(how='all').dropna(axis=1, how='all')
            
            return df
        except Exception as e:
            logger.error(f"DataFrame preparation failed: {str(e)}")
            return None
    
    async def _detect_existing_pivot_tables(self, data: Dict[str, Any], filename: str = None) -> List[Dict[str, Any]]:
        """Use AI to detect if the Excel file already contains pivot tables."""
        if not self.client:
            return []
            
        try:
            # Analyze data structure to detect pivot table patterns
            df = self._prepare_dataframe(data)
            if df is None:
                return []
            
            # Create context for AI analysis
            data_summary = {
                "columns": list(df.columns),
                "shape": df.shape,
                "sample_data": df.head(3).to_dict('records') if len(df) > 0 else [],
                "filename": filename or "unknown"
            }
            
            prompt = f"""
            Analyze this Excel data structure to detect if it contains existing pivot tables or pivot-like summaries:
            
            Data Summary: {json.dumps(data_summary, indent=2)}
            
            Look for patterns that indicate pivot tables:
            - Aggregated/summarized data (totals, counts, averages)
            - Hierarchical column structures
            - Cross-tabulated data
            - Grouped data with subtotals
            
            Return a JSON response with:
            {{
                "has_pivot_tables": true/false,
                "detected_pivots": [
                    {{
                        "type": "existing_pivot|summary_table|crosstab",
                        "description": "Brief description",
                        "row_groups": ["column1", "column2"],
                        "value_columns": ["column3"],
                        "confidence": 0.0-1.0
                    }}
                ],
                "raw_data_detected": true/false,
                "recommendation": "Should we create new pivot tables or work with existing data?"
            }}
            """
            
            response = self.client.models.generate_content(
                model='gemini-2.0-flash-001',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type='application/json',
                    temperature=0.1,
                    max_output_tokens=2000
                )
            )
            
            result = json.loads(response.text)
            logger.info(f"Pivot detection analysis: {result.get('has_pivot_tables', False)} existing pivots found")
            
            return result.get('detected_pivots', [])
            
        except Exception as e:
            logger.error(f"Pivot table detection failed: {str(e)}")
            return []
    
    async def _analyze_data_structure(self, df: pd.DataFrame, filename: str = None) -> Dict[str, Any]:
        """Use AI to analyze data structure and business context."""
        if not self.client:
            return {"error": "GenAI client not available"}
            
        try:
            # Prepare data analysis context
            analysis_context = {
                "filename": filename or "unknown",
                "shape": df.shape,
                "columns": list(df.columns),
                "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
                "sample_data": df.head(5).to_dict('records'),
                "null_counts": df.isnull().sum().to_dict(),
                "unique_counts": {col: df[col].nunique() if df[col].dtype in ['object', 'string'] else None 
                                for col in df.columns}
            }
            
            prompt = f"""
            Analyze this Excel dataset to understand its business context and optimal pivot table strategy:
            
            Dataset Analysis: {json.dumps(analysis_context, indent=2, default=str)}
            
            Please provide comprehensive analysis in JSON format:
            {{
                "business_domain": "e.g., sales, finance, operations, hr, marketing",
                "data_type": "transactional|summary|time_series|categorical|mixed",
                "key_dimensions": ["columns that would make good pivot rows"],
                "key_metrics": ["columns that would make good pivot values"],
                "time_columns": ["date/time columns if any"],
                "categorical_columns": ["columns with categories/groups"],
                "numeric_columns": ["columns with numbers for aggregation"],
                "data_quality": {{
                    "completeness": 0.0-1.0,
                    "consistency": 0.0-1.0,
                    "issues": ["list of data quality issues"]
                }},
                "pivot_potential": {{
                    "high_value_pivots": ["descriptions of most valuable pivot tables"],
                    "dimension_relationships": ["how dimensions relate to each other"],
                    "aggregation_opportunities": ["what metrics can be meaningfully aggregated"]
                }},
                "ai_insights": {{
                    "business_value": "What business questions can this data answer?",
                    "recommended_approach": "How should we pivot this data for best insights?",
                    "chart_opportunities": "What types of charts would be most valuable?"
                }}
            }}
            """
            
            response = self.client.models.generate_content(
                model='gemini-2.0-flash-001',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type='application/json',
                    temperature=0.2,
                    max_output_tokens=3000
                )
            )
            
            analysis = json.loads(response.text)
            logger.info(f"Data structure analysis completed for {analysis.get('business_domain', 'unknown')} domain")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Data structure analysis failed: {str(e)}")
            return {"error": f"Analysis failed: {str(e)}"}
    
    async def _generate_pivot_recommendations(self, df: pd.DataFrame, data_analysis: Dict[str, Any], existing_pivots: List[Dict[str, Any]]) -> List[PivotTableRecommendation]:
        """Generate AI-driven pivot table recommendations."""
        if not self.client:
            return []
            
        try:
            # Prepare context for pivot recommendations
            pivot_context = {
                "data_analysis": data_analysis,
                "existing_pivots": existing_pivots,
                "available_columns": list(df.columns),
                "data_shape": df.shape
            }
            
            prompt = f"""
            Based on this data analysis, recommend optimal pivot table configurations:
            
            Context: {json.dumps(pivot_context, indent=2)}
            
            Generate 2-4 high-value pivot table recommendations in JSON format:
            {{
                "recommendations": [
                    {{
                        "rows": ["column1", "column2"],
                        "columns": ["column3"],
                        "values": ["column4", "column5"],
                        "aggfunc": "sum|count|mean|max|min",
                        "title": "Descriptive title for this pivot",
                        "description": "What insights this pivot provides",
                        "confidence": 0.0-1.0,
                        "business_value": "Why this pivot is valuable for business decisions",
                        "chart_suitability": "What chart types work best with this pivot"
                    }}
                ]
            }}
            
            Focus on:
            - Business value and actionable insights
            - Optimal dimension/metric combinations  
            - Chart-friendly data structures
            - Avoiding over-aggregation or under-aggregation
            """
            
            response = self.client.models.generate_content(
                model='gemini-2.0-flash-001',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type='application/json',
                    temperature=0.3,
                    max_output_tokens=2500
                )
            )
            
            result = json.loads(response.text)
            recommendations = []
            
            for rec_data in result.get('recommendations', []):
                try:
                    recommendation = PivotTableRecommendation(
                        rows=rec_data.get('rows', []),
                        columns=rec_data.get('columns', []),
                        values=rec_data.get('values', []),
                        aggfunc=rec_data.get('aggfunc', 'sum'),
                        title=rec_data.get('title', 'Pivot Table'),
                        description=rec_data.get('description', ''),
                        confidence=rec_data.get('confidence', 0.5),
                        business_value=rec_data.get('business_value', '')
                    )
                    recommendations.append(recommendation)
                except Exception as e:
                    logger.warning(f"Skipping invalid recommendation: {e}")
                    continue
            
            logger.info(f"Generated {len(recommendations)} pivot table recommendations")
            return recommendations
            
        except Exception as e:
            logger.error(f"Pivot recommendation generation failed: {str(e)}")
            return []
    
    async def _create_pivot_tables(self, df: pd.DataFrame, recommendations: List[PivotTableRecommendation]) -> List[PivotTableData]:
        """Create actual pivot tables based on AI recommendations."""
        created_pivots = []
        
        for rec in recommendations:
            try:
                # Validate columns exist in dataframe
                all_columns = rec.rows + rec.columns + rec.values
                missing_columns = [col for col in all_columns if col not in df.columns]
                
                if missing_columns:
                    logger.warning(f"Skipping pivot '{rec.title}' - missing columns: {missing_columns}")
                    continue
                
                # Create pivot table
                pivot_df = pd.pivot_table(
                    df,
                    values=rec.values,
                    index=rec.rows if rec.rows else None,
                    columns=rec.columns if rec.columns else None,
                    aggfunc=rec.aggfunc,
                    fill_value=0,
                    margins=True,
                    margins_name='Total'
                )
                
                # Calculate summary statistics
                summary_stats = {
                    "shape": pivot_df.shape,
                    "total_cells": pivot_df.size,
                    "non_zero_cells": (pivot_df != 0).sum().sum() if hasattr(pivot_df, 'sum') else 0,
                    "value_ranges": {}
                }
                
                # Add value ranges for numeric columns
                for col in rec.values:
                    if col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
                        summary_stats["value_ranges"][col] = {
                            "min": float(df[col].min()),
                            "max": float(df[col].max()),
                            "mean": float(df[col].mean())
                        }
                
                pivot_data = PivotTableData(
                    pivot_df=pivot_df,
                    recommendation=rec,
                    summary_stats=summary_stats
                )
                
                created_pivots.append(pivot_data)
                logger.info(f"Created pivot table '{rec.title}' with shape {pivot_df.shape}")
                
            except Exception as e:
                logger.error(f"Failed to create pivot table '{rec.title}': {str(e)}")
                continue
        
        return created_pivots
    
    def get_pivot_table_data_for_charts(self, pivot_data: PivotTableData) -> Dict[str, Any]:
        """Convert pivot table to chart-ready data format."""
        try:
            pivot_df = pivot_data.pivot_df
            
            # Convert pivot table to chart-friendly format
            if isinstance(pivot_df.index, pd.MultiIndex):
                # Handle multi-level index
                chart_data = []
                for idx in pivot_df.index:
                    if idx == 'Total':  # Skip totals row
                        continue
                    row_data = {}
                    if isinstance(idx, tuple):
                        for i, level_name in enumerate(pivot_df.index.names):
                            row_data[level_name or f'level_{i}'] = idx[i]
                    else:
                        row_data[pivot_df.index.name or 'category'] = idx
                    
                    # Add values
                    for col in pivot_df.columns:
                        if col != 'Total':  # Skip totals column
                            if isinstance(col, tuple):
                                col_name = '_'.join(str(c) for c in col)
                            else:
                                col_name = str(col)
                            row_data[col_name] = pivot_df.loc[idx, col]
                    
                    chart_data.append(row_data)
            else:
                # Handle single-level index
                chart_data = []
                for idx in pivot_df.index:
                    if idx == 'Total':  # Skip totals row
                        continue
                    row_data = {pivot_df.index.name or 'category': idx}
                    
                    for col in pivot_df.columns:
                        if col != 'Total':  # Skip totals column
                            row_data[str(col)] = pivot_df.loc[idx, col]
                    
                    chart_data.append(row_data)
            
            return {
                "data": chart_data,
                "metadata": {
                    "pivot_title": pivot_data.recommendation.title,
                    "rows": pivot_data.recommendation.rows,
                    "columns": pivot_data.recommendation.columns,
                    "values": pivot_data.recommendation.values,
                    "aggfunc": pivot_data.recommendation.aggfunc,
                    "business_value": pivot_data.recommendation.business_value,
                    "chart_columns": list(chart_data[0].keys()) if chart_data else []
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to convert pivot to chart data: {str(e)}")
            return {"data": [], "metadata": {}} 