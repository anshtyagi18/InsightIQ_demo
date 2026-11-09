"""
Comparison router for intelligent estimated vs actual data analysis.
Provides endpoints for comparing forecasted/estimated datasets with actual performance data.
Enhanced with AI-powered insights and chart generation similar to the chat system.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import ORJSONResponse
from pydantic import BaseModel
from typing import Dict, List, Any, Optional, Union, cast
import pandas as pd
import logging
import traceback
import json
import io
import hashlib
from datetime import datetime, timezone, timedelta
import uuid
import numpy as np
from dataclasses import dataclass
import asyncio
from concurrent.futures import ThreadPoolExecutor
import functools

from src.services.conversational_analytics_agent import ConversationalAnalyticsAgent
from src.services.database_service import DatabaseAnalyticsService
from src.core.database import cache_manager

logger = logging.getLogger(__name__)

# Initialize database service for persistent storage
db_service = DatabaseAnalyticsService()

# Thread pool for CPU-intensive operations
executor = ThreadPoolExecutor(max_workers=4)

# Remove global in-memory storage - use database instead
# uploaded_files: Dict[str, Dict[str, Any]] = {}

# Create router
router = APIRouter(prefix="/comparison", tags=["comparison"])

# Add caching decorator for expensive operations
def cached_analysis(expire_time: int = 3600):
    """Decorator to cache analysis results"""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Create cache key from function arguments
            cache_key = f"analysis:{func.__name__}:{hash(str(args))}{hash(str(kwargs))}"
            
            # Try to get from cache first
            try:
                cached_result = await cache_manager.get(cache_key)
                if cached_result:
                    logger.info(f"Cache hit for {func.__name__}")
                    return json.loads(cached_result)
            except Exception as e:
                logger.warning(f"Cache read error: {e}")
            
            # If not in cache, compute result
            result = await func(*args, **kwargs)
            
            # Store in cache for next time
            try:
                await cache_manager.set(cache_key, json.dumps(result, default=str), expire=expire_time)
                logger.info(f"Cached result for {func.__name__}")
            except Exception as e:
                logger.warning(f"Cache write error: {e}")
            
            return result
        return wrapper
    return decorator

@dataclass
class ComparisonResult:
    """Result of intelligent comparison analysis."""
    overall_variance: float
    trend_alignment: str
    critical_deviations: List[Dict[str, Any]]
    performance_summary: Dict[str, Any]
    recommendations: List[str]
    insights: List[Dict[str, Any]]
    charts_data: List[Dict[str, Any]]
    kpis: List[Dict[str, Any]]

class SimpleIntelligentComparisonAgent:
    """
    Simple AI-powered agent for comparing estimated vs actual datasets.
    Lightweight implementation without external dependencies.
    """
    
    def __init__(self):
        self.variance_thresholds = {
            'critical': 0.25,  # 25% variance
            'significant': 0.15,  # 15% variance
            'moderate': 0.10,  # 10% variance
            'minor': 0.05   # 5% variance
        }
    
    def _analyze_data_characteristics(self, estimated_df: pd.DataFrame, actual_df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze data characteristics to determine appropriate analysis complexity."""
        try:
            # Basic data metrics
            est_rows, est_cols = estimated_df.shape
            act_rows, act_cols = actual_df.shape
            
            # Count numeric columns
            est_numeric_cols = len(estimated_df.select_dtypes(include=[np.number]).columns)
            act_numeric_cols = len(actual_df.select_dtypes(include=[np.number]).columns)
            
            # Data density (non-null values)
            est_density = estimated_df.count().sum() / (est_rows * est_cols) if est_rows * est_cols > 0 else 0
            act_density = actual_df.count().sum() / (act_rows * act_cols) if act_rows * act_cols > 0 else 0
            
            # Data complexity score
            complexity_score = (
                min(est_rows, act_rows) * 0.3 +  # Row count impact
                min(est_numeric_cols, act_numeric_cols) * 2.0 +  # Numeric columns impact
                (est_density + act_density) * 50  # Data density impact
            )
            
            return {
                'estimated_shape': (est_rows, est_cols),
                'actual_shape': (act_rows, act_cols),
                'numeric_columns': min(est_numeric_cols, act_numeric_cols),
                'data_density': (est_density + act_density) / 2,
                'complexity_score': complexity_score,
                'total_data_points': min(est_rows, act_rows) * min(est_numeric_cols, act_numeric_cols)
            }
        except Exception as e:
            logger.error(f"Error analyzing data characteristics: {str(e)}")
            return {
                'estimated_shape': (0, 0),
                'actual_shape': (0, 0),
                'numeric_columns': 0,
                'data_density': 0,
                'complexity_score': 0,
                'total_data_points': 0
            }
    
    def _determine_analysis_level(self, characteristics: Dict[str, Any]) -> str:
        """Determine appropriate analysis level based on data characteristics."""
        complexity_score = characteristics.get('complexity_score', 0)
        numeric_columns = characteristics.get('numeric_columns', 0)
        total_data_points = characteristics.get('total_data_points', 0)
        
        # Simple rules for analysis level
        if complexity_score < 20 or numeric_columns <= 2 or total_data_points < 50:
            return "basic"
        elif complexity_score < 100 or numeric_columns <= 5 or total_data_points < 200:
            return "standard"
        else:
            return "comprehensive"

    async def compare_datasets(
        self, 
        estimated_df: pd.DataFrame, 
        actual_df: pd.DataFrame,
        comparison_config: Optional[Dict[str, Any]] = None
    ) -> ComparisonResult:
        """
        SMART Main method that adapts analysis complexity based on data characteristics.
        """
        logger.info("[COMPARISON] Starting SMART intelligent dataset comparison")
        
        try:
            # Step 1: Analyze data characteristics to determine appropriate analysis level
            data_characteristics = self._analyze_data_characteristics(estimated_df, actual_df)
            analysis_level = self._determine_analysis_level(data_characteristics)
            
            logger.info(f"[COMPARISON] Data characteristics: {data_characteristics}")
            logger.info(f"[COMPARISON] Selected analysis level: {analysis_level}")
            
            # Step 2: Enhanced column mapping (always needed)
            column_mapping = await self._enhanced_column_mapping(estimated_df, actual_df)
            logger.info(f"[COMPARISON] Enhanced column mapping completed: {column_mapping}")
            
            # Step 3: Run appropriate analysis based on data complexity
            if analysis_level == "basic":
                return await self._run_basic_analysis(estimated_df, actual_df, column_mapping, data_characteristics)
            elif analysis_level == "standard":
                return await self._run_standard_analysis(estimated_df, actual_df, column_mapping, data_characteristics)
            else:  # comprehensive
                return await self._run_comprehensive_analysis(estimated_df, actual_df, column_mapping, data_characteristics)
            
        except Exception as e:
            logger.error(f"[COMPARISON] Error in smart dataset comparison: {str(e)}")
            logger.error(f"[COMPARISON] Traceback: {traceback.format_exc()}")
            
            # Fallback to basic comparison
            logger.info("[COMPARISON] Falling back to basic comparison")
            return await self._fallback_basic_comparison(estimated_df, actual_df)
    
    async def _run_basic_analysis(
        self, 
        estimated_df: pd.DataFrame, 
        actual_df: pd.DataFrame, 
        column_mapping: Dict[str, str],
        data_characteristics: Dict[str, Any]
    ) -> ComparisonResult:
        """Run basic analysis for small/simple datasets."""
        logger.info("[COMPARISON] Running BASIC analysis")
        
        try:
            # Basic variance analysis using column mapping
            variance_analysis = await self._analyze_basic_variance(estimated_df, actual_df, column_mapping)
            
            # Store variance context for trend analysis
            self._current_variance = variance_analysis.get('overall_variance', 0.0)
            self._current_critical_count = len(variance_analysis.get('critical_deviations', []))
            
            # Basic trend alignment using column mapping
            trend_alignment = await self._analyze_trend_alignment(estimated_df, actual_df, column_mapping)
            
            # Generate basic insights
            insights = await self._generate_basic_insights(variance_analysis, trend_alignment)
            
            # Create basic charts (limit to 2-3 charts max)
            charts = await self._create_basic_charts(estimated_df, actual_df, variance_analysis)
            charts = charts[:3]  # Limit to 3 charts maximum
            
            # Generate basic KPIs (limit to 4 KPIs max)
            kpis = await self._generate_basic_kpis(variance_analysis, trend_alignment)
            kpis = kpis[:4]  # Limit to 4 KPIs maximum
            
            # Generate recommendations
            recommendations = await self._generate_recommendations(variance_analysis, insights)
            
            return ComparisonResult(
                overall_variance=variance_analysis.get('overall_variance', 0.0),
                trend_alignment=trend_alignment.get('alignment_status', 'unknown'),
                critical_deviations=variance_analysis.get('critical_deviations', []),
                performance_summary={
                    'analysis_level': 'basic',
                    'data_characteristics': data_characteristics,
                    **variance_analysis.get('summary', {}),
                    'trend_summary': trend_alignment
                },
                recommendations=recommendations,
                insights=insights,
                charts_data=charts,
                kpis=kpis
            )
            
        except Exception as e:
            logger.error(f"[COMPARISON] Error in basic analysis: {str(e)}")
            return await self._fallback_basic_comparison(estimated_df, actual_df)
    
    async def _run_standard_analysis(
        self, 
        estimated_df: pd.DataFrame, 
        actual_df: pd.DataFrame, 
        column_mapping: Dict[str, str],
        data_characteristics: Dict[str, Any]
    ) -> ComparisonResult:
        """Run standard analysis for medium-sized datasets."""
        logger.info("[COMPARISON] Running STANDARD analysis")
        
        try:
            # Standard analysis with limited metrics
            individual_metrics = await self._analyze_all_metrics_individually(
                estimated_df, actual_df, column_mapping
            )
            # Limit to top 5 metrics
            individual_metrics = individual_metrics[:5]
            
            # Enhanced variance analysis
            variance_analysis = await self._analyze_enhanced_variance(estimated_df, actual_df, column_mapping)
            
            # Store variance context for trend analysis
            self._current_variance = variance_analysis.get('overall_variance', 0.0)
            self._current_critical_count = len(variance_analysis.get('critical_deviations', []))
            
            # Basic trend analysis
            trend_deviation_analysis = await self._analyze_trend_deviations_deep(
                estimated_df, actual_df, column_mapping
            )
            
            # Limited chart generation (max 6 charts)
            charts = await self._create_enhanced_charts_deep(
                estimated_df, actual_df, column_mapping, individual_metrics, 
                variance_analysis, trend_deviation_analysis, {}
            )
            charts = charts[:6]  # Limit to 6 charts maximum
            
            # Standard KPIs (max 6 KPIs)
            kpis = await self._generate_comprehensive_kpis_deep(
                individual_metrics, variance_analysis, trend_deviation_analysis, {}
            )
            kpis = kpis[:6]  # Limit to 6 KPIs maximum
            
            # Generate recommendations
            recommendations = await self._generate_enhanced_recommendations_deep(
                {'insights': [], 'high_impact_deviations': []}, {}, variance_analysis, trend_deviation_analysis
            )
            
            return ComparisonResult(
                overall_variance=variance_analysis.get('overall_variance', 0.0),
                trend_alignment=trend_deviation_analysis.get('overall_alignment_status', 'unknown'),
                critical_deviations=variance_analysis.get('critical_deviations', []),
                performance_summary={
                    'analysis_level': 'standard',
                    'data_characteristics': data_characteristics,
                    'individual_metrics': individual_metrics,  # FIXED: Store the actual individual metrics data
                    'individual_metrics_summary': {
                        'total_analyzed': len(individual_metrics),
                        'high_variance_count': sum(1 for m in individual_metrics if abs(m.get('variance_percentage', 0)) > 15)
                    },
                    **variance_analysis.get('summary', {}),
                    'trend_health_summary': trend_deviation_analysis.get('summary', {})
                },
                recommendations=recommendations,
                insights=[],
                charts_data=charts,
                kpis=kpis
            )
            
        except Exception as e:
            logger.error(f"[COMPARISON] Error in standard analysis: {str(e)}")
            return await self._run_basic_analysis(estimated_df, actual_df, column_mapping, data_characteristics)
    
    async def _run_comprehensive_analysis(
        self, 
        estimated_df: pd.DataFrame, 
        actual_df: pd.DataFrame, 
        column_mapping: Dict[str, str],
        data_characteristics: Dict[str, Any]
    ) -> ComparisonResult:
        """Run comprehensive analysis for large/complex datasets."""
        logger.info("[COMPARISON] Running COMPREHENSIVE analysis")
        
        try:
            # Full comprehensive analysis (original logic)
            individual_metrics = await self._analyze_all_metrics_individually(
                estimated_df, actual_df, column_mapping
            )
            
            variance_analysis = await self._analyze_enhanced_variance(estimated_df, actual_df, column_mapping)
            
            # Store variance context for trend analysis
            self._current_variance = variance_analysis.get('overall_variance', 0.0)
            self._current_critical_count = len(variance_analysis.get('critical_deviations', []))
            
            trend_deviation_analysis = await self._analyze_trend_deviations_deep(
                estimated_df, actual_df, column_mapping
            )
            
            granular_insights = await self._extract_granular_insights_deep(
                estimated_df, actual_df, column_mapping, individual_metrics
            )
            
            missing_metrics = await self._detect_missing_metrics_deep(estimated_df, actual_df, column_mapping)
            
            prioritized_insights = await self._prioritize_by_business_impact(
                individual_metrics, variance_analysis, trend_deviation_analysis, granular_insights
            )
            
            enhanced_charts = await self._create_enhanced_charts_deep(
                estimated_df, actual_df, column_mapping, individual_metrics, 
                variance_analysis, trend_deviation_analysis, granular_insights
            )
            
            comprehensive_kpis = await self._generate_comprehensive_kpis_deep(
                individual_metrics, variance_analysis, trend_deviation_analysis, missing_metrics
            )
            
            enhanced_recommendations = await self._generate_enhanced_recommendations_deep(
                prioritized_insights, missing_metrics, variance_analysis, trend_deviation_analysis
            )
            
            return ComparisonResult(
                overall_variance=variance_analysis.get('overall_variance', 0.0),
                trend_alignment=trend_deviation_analysis.get('overall_alignment_status', 'unknown'),
                critical_deviations=prioritized_insights.get('high_impact_deviations', []),
                performance_summary={
                    'analysis_level': 'comprehensive',
                    'data_characteristics': data_characteristics,
                    **variance_analysis.get('summary', {}),
                    'individual_metrics': individual_metrics,  # FIXED: Store the actual individual metrics data
                    'individual_metrics_summary': {
                        'total_analyzed': len(individual_metrics),
                        'high_variance_count': sum(1 for m in individual_metrics if abs(m.get('variance_percentage', 0)) > 15),
                        'trend_misalignment_count': sum(1 for m in individual_metrics if m.get('trend_correlation', 1) < 0.6)
                    },
                    'trend_health_summary': trend_deviation_analysis.get('summary', {}),
                    'missing_metrics_summary': missing_metrics,
                    'granular_insights_summary': granular_insights.get('summary', {}),
                    'business_impact_summary': prioritized_insights.get('summary', {})
                },
                recommendations=enhanced_recommendations,
                insights=prioritized_insights.get('insights', []),
                charts_data=enhanced_charts,
                kpis=comprehensive_kpis
            )
            
        except Exception as e:
            logger.error(f"[COMPARISON] Error in comprehensive analysis: {str(e)}")
            return await self._run_standard_analysis(estimated_df, actual_df, column_mapping, data_characteristics)
    
    async def _fallback_basic_comparison(self, estimated_df: pd.DataFrame, actual_df: pd.DataFrame) -> ComparisonResult:
        """Fallback method for when all other analysis methods fail."""
        logger.info("[COMPARISON] Running FALLBACK basic comparison")
        
        try:
            # Very basic comparison with column mapping
            column_mapping = await self._enhanced_column_mapping(estimated_df, actual_df)
            variance_analysis = await self._analyze_basic_variance(estimated_df, actual_df, column_mapping)
            trend_alignment = await self._analyze_trend_alignment(estimated_df, actual_df, column_mapping)
            
            # Minimal insights
            insights = [{
                'title': 'Basic Comparison Completed',
                'description': 'A basic comparison was performed due to data processing constraints.',
                'type': 'info',
                'severity': 'low'
            }]
            
            # Single basic chart
            charts = [{
                'type': 'bar',
                'title': 'Basic Variance Overview',
                'data': [
                    {'category': 'Overall Variance', 'value': variance_analysis.get('overall_variance', 0)}
                ],
                'config': {
                    'xAxisKey': 'category',
                    'bars': [{'dataKey': 'value', 'name': 'Variance %', 'fill': '#8884d8'}]
                }
            }]
            
            # Basic KPIs
            kpis = [
                {
                    'title': 'Overall Variance',
                    'value': f"{variance_analysis.get('overall_variance', 0):.1f}%",
                    'description': 'Average variance across all metrics',
                    'color': '#ef4444' if variance_analysis.get('overall_variance', 0) > 20 else '#10b981',
                    'textColor': '#ffffff'
                }
            ]
            
            return ComparisonResult(
                overall_variance=variance_analysis.get('overall_variance', 0.0),
                trend_alignment=trend_alignment.get('alignment_status', 'unknown'),
                critical_deviations=variance_analysis.get('critical_deviations', []),
                performance_summary={
                    'analysis_level': 'fallback',
                    'message': 'Basic comparison performed due to processing constraints'
                },
                recommendations=['Review data quality and try again with cleaner datasets'],
                insights=insights,
                charts_data=charts,
                kpis=kpis
            )
            
        except Exception as e:
            logger.error(f"[COMPARISON] Error in fallback comparison: {str(e)}")
            # Return minimal result
            return ComparisonResult(
                overall_variance=0.0,
                trend_alignment='unknown',
                critical_deviations=[],
                performance_summary={'error': 'Comparison failed', 'analysis_level': 'error'},
                recommendations=['Please check your data format and try again'],
                insights=[{
                    'title': 'Comparison Error',
                    'description': 'Unable to process the comparison due to data issues.',
                    'type': 'error',
                    'severity': 'high'
                }],
                charts_data=[],
                kpis=[]
            )

    async def _analyze_basic_variance(self, estimated_df, actual_df, column_mapping=None):
        """Analyze basic variance between datasets using column mapping."""
        try:
            # If no column mapping provided, try to create one
            if column_mapping is None:
                column_mapping = await self._enhanced_column_mapping(estimated_df, actual_df)
            
            logger.info(f"[BASIC_VARIANCE] Using column mapping: {column_mapping}")
            
            # Find numeric columns in both datasets
            est_numeric = estimated_df.select_dtypes(include=[np.number]).columns.tolist()
            act_numeric = actual_df.select_dtypes(include=[np.number]).columns.tolist()
            
            # Also try to convert text columns that might be numeric
            for col in estimated_df.columns:
                if col not in est_numeric:
                    numeric_series = cast(pd.Series, pd.to_numeric(estimated_df[col], errors='coerce'))
                    if numeric_series.notna().sum() > len(estimated_df) * 0.5:
                        est_numeric.append(col)
            
            for col in actual_df.columns:
                if col not in act_numeric:
                    numeric_series = cast(pd.Series, pd.to_numeric(actual_df[col], errors='coerce'))
                    if numeric_series.notna().sum() > len(actual_df) * 0.5:
                        act_numeric.append(col)
            
            logger.info(f"[BASIC_VARIANCE] Estimated numeric columns: {est_numeric}")
            logger.info(f"[BASIC_VARIANCE] Actual numeric columns: {act_numeric}")
            
            # Use column mapping to find analyzable metric pairs
            analyzable_pairs = []
            for est_col, act_col in column_mapping.items():
                if est_col in est_numeric and act_col in act_numeric:
                    analyzable_pairs.append((est_col, act_col))
            
            # Limit to 5 pairs maximum
            analyzable_pairs = analyzable_pairs[:5]
            logger.info(f"[BASIC_VARIANCE] Found {len(analyzable_pairs)} analyzable metric pairs: {analyzable_pairs}")
            
            critical_deviations = []
            total_variance = 0
            analyzed_metrics = 0
            
            for est_col, act_col in analyzable_pairs:
                if est_col in estimated_df.columns and act_col in actual_df.columns:
                    # Convert to numeric with proper handling
                    est_values = cast(pd.Series, pd.to_numeric(estimated_df[est_col], errors='coerce'))
                    act_values = cast(pd.Series, pd.to_numeric(actual_df[act_col], errors='coerce'))
                    
                    # Check if we have sufficient data
                    est_valid = est_values.notna().sum()
                    act_valid = act_values.notna().sum()
                    
                    if est_valid >= 1 and act_valid >= 1:  # At least some data
                        est_sum = float(est_values.sum())
                        act_sum = float(act_values.sum())
                        analyzed_metrics += 1
                        
                        if abs(est_sum) > 0.001:  # Avoid division by zero
                            variance = ((act_sum - est_sum) / est_sum) * 100
                            total_variance += abs(variance)
                            
                            if abs(variance) > self.variance_thresholds['critical'] * 100:
                                critical_deviations.append({
                                    'metric': est_col,  # Use the actual column name, not "vs" format
                                    'metric_name': est_col,  # Add metric_name explicitly 
                                    'estimated_column': est_col,
                                    'actual_column': act_col,
                                    'estimated_value': est_sum,
                                    'actual_value': act_sum,
                                    'variance_percentage': variance,
                                    'severity': 'critical' if abs(variance) > 25 else 'moderate'
                                })
                        logger.info(f"[BASIC_VARIANCE] Analyzed metric pair '{est_col}' vs '{act_col}': {est_valid} estimated, {act_valid} actual data points")
                    else:
                        logger.warning(f"[BASIC_VARIANCE] Skipping '{est_col}' vs '{act_col}': insufficient data (est:{est_valid}, act:{act_valid})")
            
            overall_variance = total_variance / analyzed_metrics if analyzed_metrics > 0 else 0
            
            return {
                'overall_variance': overall_variance,
                'critical_deviations': critical_deviations,
                'summary': {
                    'columns_analyzed': analyzed_metrics,  # Use actual analyzed count
                    'total_metrics_found': len(analyzable_pairs),
                    'deviations_found': len(critical_deviations)
                }
            }
            
        except Exception as e:
            logger.error(f"Error in variance analysis: {str(e)}")
            return {
                'overall_variance': 0.0,
                'critical_deviations': [],
                'summary': {'error': str(e), 'columns_analyzed': 0}
            }

    async def _analyze_trend_alignment(self, estimated_df, actual_df, column_mapping=None):
        """Analyze trend alignment between datasets using column mapping."""
        try:
            # If no column mapping provided, try to create one
            if column_mapping is None:
                column_mapping = await self._enhanced_column_mapping(estimated_df, actual_df)
            
            logger.info(f"[TREND_ALIGNMENT] Using column mapping: {column_mapping}")
            
            # Find numeric columns in both datasets
            est_numeric = estimated_df.select_dtypes(include=[np.number]).columns.tolist()
            act_numeric = actual_df.select_dtypes(include=[np.number]).columns.tolist()
            
            # Also try to convert text columns that might be numeric
            for col in estimated_df.columns:
                if col not in est_numeric:
                    numeric_series = cast(pd.Series, pd.to_numeric(estimated_df[col], errors='coerce'))
                    if numeric_series.notna().sum() > len(estimated_df) * 0.5:
                        est_numeric.append(col)
            
            for col in actual_df.columns:
                if col not in act_numeric:
                    numeric_series = cast(pd.Series, pd.to_numeric(actual_df[col], errors='coerce'))
                    if numeric_series.notna().sum() > len(actual_df) * 0.5:
                        act_numeric.append(col)
            
            trend_details = {
                'metrics_analyzed': 0,
                'correlation_scores': [],
                'trend_explanations': [],
                'data_quality': 'poor'
            }
            
            # Use column mapping to find analyzable metric pairs
            analyzable_pairs = []
            for est_col, act_col in column_mapping.items():
                if est_col in est_numeric and act_col in act_numeric:
                    analyzable_pairs.append((est_col, act_col))
            
            # Limit to 3 pairs maximum for trend analysis
            analyzable_pairs = analyzable_pairs[:3]
            logger.info(f"[TREND_ALIGNMENT] Found {len(analyzable_pairs)} analyzable metric pairs for trend analysis")
            
            if analyzable_pairs:
                correlations = []
                
                for est_col, act_col in analyzable_pairs:
                    if est_col in estimated_df.columns and act_col in actual_df.columns:
                        # Convert to numeric and clean
                        est_values = cast(pd.Series, pd.to_numeric(estimated_df[est_col], errors='coerce')).dropna()
                        act_values = cast(pd.Series, pd.to_numeric(actual_df[act_col], errors='coerce')).dropna()
                        
                        if len(est_values) >= 3 and len(act_values) >= 3:
                            # Align by taking minimum length
                            min_len = min(len(est_values), len(act_values))
                            est_aligned = est_values[:min_len]
                            act_aligned = act_values[:min_len]
                            
                            # Calculate correlation
                            if len(est_aligned) > 1:
                                try:
                                    correlation = np.corrcoef(est_aligned, act_aligned)[0, 1]
                                    if not np.isnan(correlation):
                                        correlations.append(correlation)
                                        trend_details['correlation_scores'].append({
                                            'metric': f"{est_col} vs {act_col}",
                                            'estimated_column': est_col,
                                            'actual_column': act_col,
                                            'correlation': float(correlation),
                                            'data_points': min_len
                                        })
                                        trend_details['metrics_analyzed'] += 1
                                        
                                        # Generate explanation
                                        if correlation > 0.8:
                                            explanation = f"{est_col} vs {act_col}: Strong positive correlation ({correlation:.2f}) - trends align well"
                                        elif correlation > 0.5:
                                            explanation = f"{est_col} vs {act_col}: Moderate correlation ({correlation:.2f}) - some trend alignment"
                                        elif correlation > 0.2:
                                            explanation = f"{est_col} vs {act_col}: Weak correlation ({correlation:.2f}) - limited trend alignment"
                                        else:
                                            explanation = f"{est_col} vs {act_col}: Poor correlation ({correlation:.2f}) - trends diverge significantly"
                                        
                                        trend_details['trend_explanations'].append(explanation)
                                        logger.info(f"[TREND_ALIGNMENT] Analyzed '{est_col}' vs '{act_col}': correlation = {correlation:.3f}")
                                except Exception as corr_error:
                                    logger.warning(f"[TREND_ALIGNMENT] Correlation calculation failed for {est_col} vs {act_col}: {str(corr_error)}")
                
                # Overall assessment - IMPROVED: Consider both correlation AND variance context
                if correlations:
                    avg_correlation = float(np.mean(correlations))
                    correlation_score = max(0.0, min(1.0, avg_correlation))
                    
                    # Get variance context from variance_analysis if available
                    overall_variance = getattr(self, '_current_variance', 0.0)
                    critical_issues_count = getattr(self, '_current_critical_count', 0)
                    
                    # Contextual alignment assessment
                    if avg_correlation > 0.8 and overall_variance < 15 and critical_issues_count < 3:
                        alignment = "strong_alignment"
                        trend_details['data_quality'] = 'excellent'
                    elif avg_correlation > 0.7 and overall_variance < 25 and critical_issues_count < 5:
                        alignment = "good_alignment"
                        trend_details['data_quality'] = 'good'
                    elif avg_correlation > 0.7:  # High correlation but high variance
                        alignment = "mixed_alignment"
                        trend_details['data_quality'] = 'mixed'
                        trend_details['trend_explanations'].append(f"High correlation ({avg_correlation:.2f}) but significant variance ({overall_variance:.1f}%) indicates trends follow similar patterns with different magnitudes")
                    elif avg_correlation > 0.4:
                        alignment = "moderate_alignment"
                        trend_details['data_quality'] = 'moderate'
                    else:
                        alignment = "weak_alignment"
                        trend_details['data_quality'] = 'limited'
                else:
                    alignment = "insufficient_data"
                    correlation_score = 0.0
                    trend_details['trend_explanations'].append("Insufficient numeric data for trend correlation analysis")
            else:
                alignment = "no_numeric_data"
                correlation_score = 0.0
                trend_details['trend_explanations'].append("No numeric columns found for trend analysis")
            
            return {
                'alignment_status': alignment,
                'correlation_score': correlation_score,
                'details': trend_details
            }
            
        except Exception as e:
            logger.error(f"Error in trend analysis: {str(e)}")
            return {
                'alignment_status': 'error',
                'correlation_score': 0.0,
                'details': {
                    'metrics_analyzed': 0,
                    'trend_explanations': [f"Trend analysis failed: {str(e)}"],
                    'data_quality': 'error'
                }
            }

    async def _generate_basic_insights(self, variance_analysis, trend_alignment):
        """Generate enhanced basic insights from the analysis with structured points."""
        insights = []
        
        overall_variance = variance_analysis.get('overall_variance', 0)
        deviations = variance_analysis.get('critical_deviations', [])
        summary = variance_analysis.get('summary', {})
        metrics_analyzed = summary.get('columns_analyzed', 0)
        
        # Data availability insight with structured points
        if metrics_analyzed == 0:
            insights.append({
                'title': 'Limited Data Analysis',
                'description': 'No analyzable numeric metrics were found in the datasets.',
                'points': [
                    'No numeric columns suitable for variance analysis detected',
                    'Data may contain formatting issues or non-numeric values',
                    'Consider checking data quality and column formats',
                    'Verify that both datasets contain comparable numeric fields'
                ],
                'type': 'data_quality',
                'severity': 'high'
            })
        elif metrics_analyzed == 1:
            insights.append({
                'title': 'Single Metric Analysis',
                'description': f'Only 1 metric was analyzable for comparison.',
                'points': [
                    'Limited analysis scope with single metric comparison',
                    'Consider including additional quantitative metrics',
                    'Revenue, costs, volumes, or performance indicators would enhance insights',
                    'More metrics enable comprehensive variance analysis'
                ],
                'type': 'data_scope',
                'severity': 'medium'
            })
        
        # Variance insight with structured breakdown (only if we have data)
        if metrics_analyzed > 0:
            if overall_variance > 20:
                insights.append({
                    'title': 'High Overall Variance Detected',
                    'description': f'The overall variance is {overall_variance:.1f}% across {metrics_analyzed} metric{"s" if metrics_analyzed != 1 else ""}.',
                    'points': [
                        f'Significant variance of {overall_variance:.1f}% indicates forecasting challenges',
                        f'Analysis covers {metrics_analyzed} metric{"s" if metrics_analyzed != 1 else ""} with concerning deviations',
                        'Review forecasting methodology and assumptions',
                        'Consider updating models with recent market data',
                        'Implement more frequent forecast reviews and adjustments'
                    ],
                    'type': 'variance',
                    'severity': 'high'
                })
            elif overall_variance > 10:
                insights.append({
                    'title': 'Moderate Variance Observed',
                    'description': f'The overall variance is {overall_variance:.1f}% across {metrics_analyzed} metric{"s" if metrics_analyzed != 1 else ""}.',
                    'points': [
                        f'Moderate variance of {overall_variance:.1f}% shows room for improvement',
                        f'Performance across {metrics_analyzed} metric{"s" if metrics_analyzed != 1 else ""} demonstrates mixed accuracy',
                        'Fine-tuning forecasting parameters could reduce variance',
                        'Identify specific metrics driving higher deviations',
                        'Monitor trends to prevent variance escalation'
                    ],
                    'type': 'variance',
                    'severity': 'medium'
                })
            else:
                insights.append({
                    'title': 'Good Forecast Accuracy',
                    'description': f'The overall variance is {overall_variance:.1f}% across {metrics_analyzed} metric{"s" if metrics_analyzed != 1 else ""}.',
                    'points': [
                        f'Excellent accuracy with only {overall_variance:.1f}% variance',
                        f'Strong performance across {metrics_analyzed} metric{"s" if metrics_analyzed != 1 else ""} indicates robust forecasting',
                        'Current forecasting approach is working effectively',
                        'Maintain existing methodology and monitoring practices',
                        'Consider documenting successful approaches for future reference'
                    ],
                    'type': 'variance',
                    'severity': 'positive'
                })
        
        # Critical deviations insight with specific metrics and action points
        if len(deviations) > 0:
            metric_names = [d.get('metric', 'Unknown') for d in deviations[:3]]  # Top 3
            metric_list = ', '.join(metric_names)
            deviation_details = []
            
            for dev in deviations[:3]:
                metric_name = dev.get('metric', 'Unknown')
                variance_pct = dev.get('variance_percentage', 0)
                deviation_details.append(f'{metric_name}: {abs(variance_pct):.1f}% deviation')
            
            insights.append({
                'title': f'Critical Deviations in {len(deviations)} Metric{"s" if len(deviations) != 1 else ""}',
                'description': f'Found significant deviations requiring immediate attention.',
                'points': [
                    f'Critical deviations identified in: {metric_list}{"..." if len(deviations) > 3 else ""}',
                    *deviation_details,
                    'Investigate root causes for these specific metrics',
                    'Prioritize corrective actions based on business impact',
                    'Implement enhanced monitoring for flagged metrics'
                ],
                'type': 'deviations',
                'severity': 'high'
            })
        
        # Trend alignment insight with structured breakdown
        trend_details = trend_alignment.get('details', {})
        trend_explanations = trend_details.get('trend_explanations', [])
        if trend_explanations:
            trend_quality = trend_alignment.get('trend_alignment', 'unknown')
            trend_points = []
            
            # Add specific trend insights
            if 'strong' in trend_quality.lower():
                trend_points.extend([
                    'Estimated and actual trends show strong alignment',
                    'Directional forecasting accuracy is excellent',
                    'Trend patterns indicate reliable forecasting methodology'
                ])
            elif 'moderate' in trend_quality.lower():
                trend_points.extend([
                    'Trend alignment shows moderate correlation',
                    'Some directional accuracy with room for improvement',
                    'Consider refining trend analysis parameters'
                ])
            else:
                trend_points.extend([
                    'Trend alignment indicates forecasting challenges',
                    'Directional accuracy needs significant improvement',
                    'Review trend modeling approach and data inputs'
                ])
            
            # Add the first two explanations as bullet points
            trend_points.extend(trend_explanations[:2])
            
            insights.append({
                'title': 'Trend Analysis Results',
                'description': f'Trend alignment analysis reveals {trend_quality} correlation patterns.',
                'points': trend_points,
                'type': 'trend',
                'severity': 'info'
            })
        
        return insights

    async def _create_basic_charts(self, estimated_df, actual_df, variance_analysis):
        """Create basic charts for the comparison."""
        charts = []
        
        try:
            # Chart 1: Variance Overview
            deviations = variance_analysis.get('critical_deviations', [])
            if deviations:
                chart_data = []
                for dev in deviations[:5]:  # Top 5
                    variance_pct = abs(dev.get('variance_percentage', 0))
                    if variance_pct > 0.1:  # Only include meaningful variances
                        chart_data.append({
                            'metric': dev.get('metric', 'Unknown')[:15],  # Truncate long names
                            'variance': float(variance_pct),
                            'estimated': float(dev.get('estimated_value', 0)),
                            'actual': float(dev.get('actual_value', 0))
                        })
                
                if chart_data:
                    charts.append({
                        'type': 'bar',
                        'title': 'Key Variance Analysis',
                        'subtitle': f'Top {len(chart_data)} metrics with significant variance',
                        'description': 'Comparison of estimated vs actual values with variance percentages. Higher variance indicates greater deviation from forecast.',
                        'data': chart_data,
                        'config': {
                            'xAxisKey': 'metric',
                            'bars': [
                                {'dataKey': 'variance', 'name': 'Variance %', 'fill': '#ef4444'},
                                {'dataKey': 'estimated', 'name': 'Estimated', 'fill': '#3b82f6'},
                                {'dataKey': 'actual', 'name': 'Actual', 'fill': '#10b981'}
                            ],
                            'legend': {
                                'enabled': True,
                                'position': 'top',
                                'align': 'center',
                                'icon': 'rect',
                                'itemGap': 20,
                                'textStyle': {
                                    'fontSize': 12
                                }
                            },
                            'tooltip': {
                                'formatter': '{metric}\nVariance: {variance:.1f}%\nEstimated: {estimated:,.0f}\nActual: {actual:,.0f}',
                                'contentStyle': {
                                    'backgroundColor': 'rgba(0, 0, 0, 0.8)',
                                    'border': 'none',
                                    'borderRadius': '8px',
                                    'color': '#fff'
                                }
                            },
                            'grid': {
                                'containLabel': True,
                                'left': '3%',
                                'right': '3%',
                                'bottom': '10%'
                            },
                            'xAxis': {
                                'axisLabel': {
                                    'rotate': 45,
                                    'interval': 0
                                }
                            }
                        }
                    })
            
            # Chart 2: Performance Distribution
            variance_dist = {
                'Low Variance': 0,
                'Medium Variance': 0,
                'High Variance': 0
            }
            
            for dev in deviations:
                variance = abs(dev.get('variance_percentage', 0))
                if variance < 10:
                    variance_dist['Low Variance'] += 1
                elif variance < 25:
                    variance_dist['Medium Variance'] += 1
                else:
                    variance_dist['High Variance'] += 1
            
            total_metrics = sum(variance_dist.values())
            if total_metrics > 0:
                pie_data = []
                for category, count in variance_dist.items():
                    if count > 0:
                        pie_data.append({
                            'category': category,
                            'value': count,
                            'percentage': (count / total_metrics) * 100
                        })
                
                if len(pie_data) > 1:  # Only create pie chart if we have multiple segments
                    # Convert to format expected by frontend
                    pie_chart_data = []
                    for item in pie_data:
                        pie_chart_data.append({
                            'name': item['category'],  # Frontend expects 'name' key
                            'value': item['value'],
                            'percentage': item['percentage']
                        })
                    
                    charts.append({
                        'type': 'pie',
                        'title': 'Variance Distribution',
                        'subtitle': f'{total_metrics} metrics analyzed',
                        'description': 'Distribution of metrics by variance severity. Low variance (<10%) indicates good forecast accuracy, while high variance (>25%) signals significant deviations.',
                        'data': pie_chart_data,
                        'config': {
                            'dataKey': 'value',
                            'nameKey': 'name',
                            'innerRadius': '30%',  # Donut chart
                            'outerRadius': '70%',
                            'padAngle': 2,
                            'cornerRadius': 4,
                            'legend': {
                                'enabled': True,
                                'position': 'right',
                                'align': 'middle',
                                'formatter': '{name}: {value} ({percentage:.0f}%)',
                                'icon': 'circle',
                                'itemGap': 15,
                                'textStyle': {
                                    'fontSize': 12
                                }
                            },
                            'tooltip': {
                                'formatter': '{name}\nCount: {value} metrics\nPercentage: {percentage:.1f}%',
                                'contentStyle': {
                                    'backgroundColor': 'rgba(0, 0, 0, 0.8)',
                                    'border': 'none',
                                    'borderRadius': '8px',
                                    'color': '#fff',
                                    'padding': '10px'
                                }
                            },
                            'label': {
                                'show': True,
                                'position': 'outside',
                                'formatter': '{percentage:.0f}%',
                                'fontSize': 12
                            },
                            'colors': ['#10b981', '#f59e0b', '#ef4444']  # Green, Orange, Red
                        }
                    })
            
            # Chart 3: Overall Performance Summary
            overall_variance = variance_analysis.get('overall_variance', 0)
            if overall_variance > 0:
                accuracy_score = max(0, 100 - overall_variance)
                performance_data = [
                    {
                        'metric': 'Performance Summary',
                        'variance': float(overall_variance),
                        'accuracy': float(accuracy_score),
                        'value': float(accuracy_score)  # Keep for compatibility
                    }
                ]
                
                charts.append({
                    'type': 'bar',
                    'title': 'Overall Performance Metrics',
                    'subtitle': f'Accuracy: {accuracy_score:.1f}% | Variance: {overall_variance:.1f}%',
                    'description': 'Overall forecast performance summary. Accuracy shows how closely estimates matched actuals (higher is better). Variance shows average deviation (lower is better).',
                    'data': performance_data,
                    'config': {
                        'xAxisKey': 'metric',
                        'bars': [
                            {'dataKey': 'accuracy', 'name': 'Accuracy %', 'fill': '#10b981'},
                            {'dataKey': 'variance', 'name': 'Variance %', 'fill': '#ef4444'}
                        ],
                        'legend': {
                            'enabled': True,
                            'position': 'top',
                            'align': 'center',
                            'icon': 'rect',
                            'itemGap': 25,
                            'textStyle': {
                                'fontSize': 12
                            }
                        },
                        'tooltip': {
                            'formatter': 'Forecast {name}: {value:.1f}%',
                            'contentStyle': {
                                'backgroundColor': 'rgba(0, 0, 0, 0.8)',
                                'border': 'none',
                                'borderRadius': '8px',
                                'color': '#fff'
                            }
                        },
                        'grid': {
                            'containLabel': True,
                            'left': '3%',
                            'right': '3%',
                            'top': '15%',
                            'bottom': '10%'
                        },
                        'yAxis': {
                            'name': 'Percentage (%)',
                            'nameLocation': 'middle',
                            'nameGap': 40,
                            'max': 100,
                            'min': 0
                        },
                        'barCategoryGap': '40%'
                    }
                })
            
            # If no charts were created, create a simple summary
            if not charts:
                logger.info("[BASIC_CHARTS] Creating fallback summary chart")
                fallback_data = [
                    {
                        'metric': 'Analysis Complete',
                        'value': 100,
                        'progress': 100
                    }
                ]
                charts.append({
                    'type': 'bar',
                    'title': 'Comparison Summary',
                    'subtitle': 'Basic comparison analysis completed',
                    'description': 'Analysis completed successfully. Review the insights and recommendations sections for detailed findings.',
                    'data': fallback_data,
                    'config': {
                        'xAxisKey': 'metric',
                        'bars': [{'dataKey': 'progress', 'name': 'Progress %', 'fill': '#10b981'}],
                        'legend': {
                            'enabled': True,
                            'position': 'top',
                            'align': 'center'
                        },
                        'grid': {
                            'containLabel': True,
                            'left': '3%',
                            'right': '3%'
                        }
                    }
                })
            
            return charts
            
        except Exception as e:
            logger.error(f"Error creating basic charts: {str(e)}")
            # Return a minimal fallback chart
            return [{
                'type': 'bar',
                'title': 'Analysis Status',
                'subtitle': 'Comparison processing completed',
                'description': 'The comparison analysis has been completed. Check the insights section for available findings.',
                'data': [{'metric': 'Completed', 'value': 100, 'progress': 100}],
                'config': {
                    'xAxisKey': 'metric',
                    'bars': [{'dataKey': 'progress', 'name': 'Progress %', 'fill': '#10b981'}],
                    'legend': {
                        'enabled': True,
                        'position': 'top',
                        'align': 'center'
                    },
                    'grid': {
                        'containLabel': True
                    }
                }
            }]

    async def _generate_basic_kpis(self, variance_analysis, trend_alignment):
        """Generate enhanced basic KPIs for the comparison with proper metric counting."""
        kpis = []
        
        try:
            overall_variance = variance_analysis.get('overall_variance', 0)
            deviations = variance_analysis.get('critical_deviations', [])
            summary = variance_analysis.get('summary', {})
            metrics_analyzed = summary.get('columns_analyzed', 0)
            
            # Metrics Analyzed KPI
            kpis.append({
                'id': 'metrics_analyzed',
                'title': 'Metrics Analyzed',
                'value': str(metrics_analyzed),
                'subtitle': f'Out of {summary.get("total_metrics_found", metrics_analyzed)} Found',
                'trend': 'up' if metrics_analyzed > 0 else 'down',
                'description': f'Number of numeric metrics successfully analyzed for comparison'
            })
            
            # Forecast Accuracy KPI
            if metrics_analyzed > 0:
                accuracy = max(0, 100 - overall_variance)
                kpis.append({
                    'id': 'forecast_accuracy',
                    'title': 'Forecast Accuracy',
                    'value': f'{accuracy:.1f}%',
                    'subtitle': 'Overall Performance',
                    'trend': 'up' if accuracy > 80 else 'down',
                    'description': f'How accurately estimates matched actual results across {metrics_analyzed} metrics'
                })
            else:
                kpis.append({
                    'id': 'forecast_accuracy',
                    'title': 'Forecast Accuracy',
                    'value': 'N/A',
                    'subtitle': 'No Data',
                    'trend': 'down',
                    'description': 'Cannot calculate accuracy - no analyzable numeric metrics found'
                })
            
            # Critical Issues KPI
            critical_count = len([d for d in deviations if d.get('severity') == 'critical'])
            kpis.append({
                'id': 'critical_issues',
                'title': 'Critical Issues',
                'value': str(critical_count),
                'subtitle': 'Need Attention',
                'trend': 'down' if critical_count == 0 else 'up',
                'description': 'Number of critical deviations requiring immediate action'
            })
            
            # Enhanced Trend Alignment KPI with explanations
            alignment = trend_alignment.get('alignment_status', 'unknown')
            correlation_score = trend_alignment.get('correlation_score', 0.0)
            trend_details = trend_alignment.get('details', {})
            trend_metrics_analyzed = trend_details.get('metrics_analyzed', 0)
            
            if trend_metrics_analyzed > 0 and correlation_score > 0:
                trend_score = correlation_score * 100
                trend_subtitle = f'{trend_metrics_analyzed} Metric{"s" if trend_metrics_analyzed != 1 else ""} Compared'
                
                # Build explanation from trend details
                explanations = trend_details.get('trend_explanations', [])
                if explanations:
                    trend_description = '; '.join(explanations[:2])  # First 2 explanations
                else:
                    trend_description = f'Correlation analysis of {trend_metrics_analyzed} metrics'
            else:
                trend_score = 0
                trend_subtitle = 'Not Available'
                trend_description = 'Insufficient data for trend correlation analysis'
            
            kpis.append({
                'id': 'trend_alignment',
                'title': 'Trend Alignment',
                'value': f'{trend_score:.0f}%' if trend_score > 0 else 'N/A',
                'subtitle': trend_subtitle,
                'trend': 'up' if trend_score > 60 else 'down',
                'description': trend_description
            })
            
            return kpis
            
        except Exception as e:
            logger.error(f"Error generating KPIs: {str(e)}")
            return []

    async def _generate_recommendations(self, variance_analysis, insights):
        """Generate specific, actionable recommendations based on the analysis."""
        recommendations = []
        
        overall_variance = variance_analysis.get('overall_variance', 0)
        deviations = variance_analysis.get('critical_deviations', [])
        
        # Get specific metric details for targeted recommendations
        if deviations:
            # Sort by variance to prioritize
            sorted_deviations = sorted(deviations, key=lambda x: abs(x.get('variance_percentage', 0)), reverse=True)
            
            # Generate specific recommendations for top issues
            for i, dev in enumerate(sorted_deviations[:3]):
                metric_name = dev.get('metric', 'Unknown metric')
                variance = abs(dev.get('variance_percentage', 0))
                
                if variance > 30:
                    recommendations.append(
                        f"URGENT: {metric_name} ({variance:.1f}% variance) - Deploy ARIMA model with (p=2,d=1,q=2) parameters by week-end"
                    )
                elif variance > 20:
                    recommendations.append(
                        f"HIGH PRIORITY: {metric_name} ({variance:.1f}% variance) - Implement 3-week moving average with exponential smoothing (α=0.4)"
                    )
                elif variance > 15:
                    recommendations.append(
                        f"MODERATE: {metric_name} ({variance:.1f}% variance) - Increase training data window from 6 to 12 months"
                    )
        
        # Overall variance-based recommendations with specific actions
        if overall_variance > 20:
            recommendations.append(
                f"SYSTEM-WIDE: Overall {overall_variance:.1f}% variance detected - Implement ensemble forecasting combining top 3 models within 14 days"
            )
        elif overall_variance > 10:
            recommendations.append(
                f"OPTIMIZATION: {overall_variance:.1f}% average variance - Schedule bi-weekly model recalibration starting next week"
            )
        elif overall_variance < 10:
            recommendations.append(
                f"MAINTAIN: Excellent {overall_variance:.1f}% variance - Continue current approach with monthly performance reviews"
            )
        
        # Add monitoring and alert recommendations
        if len(deviations) > 3:
            recommendations.append(
                f"MONITORING: Set up real-time alerts for {len(deviations)} critical metrics when variance exceeds 15% threshold"
            )
        
        # Add timeline-based recommendation
        recommendations.append(
            f"TRACKING: Implement weekly variance report starting tomorrow targeting <10% variance within 30 days"
        )
        
        return recommendations

    # NEW ENHANCED METHODS FOR DEEP ANALYSIS

    async def _enhanced_column_mapping(self, estimated_df: pd.DataFrame, actual_df: pd.DataFrame) -> Dict[str, str]:
        """Enhanced case-insensitive column mapping with semantic similarity."""
        logger.info("[ENHANCED_MAPPING] Starting enhanced column mapping")
        
        try:
            column_mapping = {}
            estimated_cols = list(estimated_df.columns)
            actual_cols = list(actual_df.columns)
            
            # Business synonyms for better matching
            business_synonyms = {
                'energy': ['power', 'electricity', 'delivered', 'consumption', 'kwh', 'mwh'],
                'units': ['count', 'number', 'quantity', 'volume', 'pieces'],
                'rating': ['grade', 'score', 'class', 'level', 'tier'],
                'region': ['area', 'zone', 'location', 'territory', 'district'],
                'revenue': ['sales', 'income', 'earnings', 'turnover'],
                'cost': ['expense', 'expenditure', 'spend', 'outlay'],
                'profit': ['margin', 'net income', 'earnings', 'surplus']
            }
            
            def calculate_similarity(col1: str, col2: str) -> float:
                col1_lower = col1.lower().strip()
                col2_lower = col2.lower().strip()
                
                # Exact match
                if col1_lower == col2_lower:
                    return 1.0
                
                # Substring match
                if col1_lower in col2_lower or col2_lower in col1_lower:
                    return 0.8
                
                # Semantic similarity
                for concept, synonyms in business_synonyms.items():
                    if (concept in col1_lower or any(syn in col1_lower for syn in synonyms)):
                        if (concept in col2_lower or any(syn in col2_lower for syn in synonyms)):
                            return 0.9
                
                # Word overlap
                words1 = set(col1_lower.split())
                words2 = set(col2_lower.split())
                if words1 and words2:
                    overlap = len(words1 & words2) / len(words1 | words2)
                    return overlap * 0.7
                
                return 0.0
            
            # Find best matches
            for est_col in estimated_cols:
                best_score = 0.0
                best_match = None
                
                for act_col in actual_cols:
                    score = calculate_similarity(est_col, act_col)
                    if score > best_score and score > 0.4:  # Minimum threshold
                        best_score = score
                        best_match = act_col
                
                if best_match:
                    column_mapping[est_col] = best_match
                    logger.info(f"[ENHANCED_MAPPING] Mapped '{est_col}' -> '{best_match}' (score: {best_score:.2f})")
                else:
                    logger.info(f"[ENHANCED_MAPPING] No match found for estimated column '{est_col}' (best score: {best_score:.2f})")
            
            # Log unmatched actual columns
            matched_actual_cols = set(column_mapping.values())
            unmatched_actual_cols = [col for col in actual_cols if col not in matched_actual_cols]
            for col in unmatched_actual_cols:
                logger.info(f"[ENHANCED_MAPPING] Unmatched actual column: '{col}'")
            
            logger.info(f"[ENHANCED_MAPPING] Completed mapping {len(column_mapping)} column pairs")
            logger.info(f"[ENHANCED_MAPPING] Total columns - Estimated: {len(estimated_cols)}, Actual: {len(actual_cols)}, Mapped: {len(column_mapping)}")
            return column_mapping
            
        except Exception as e:
            logger.error(f"[ENHANCED_MAPPING] Error in enhanced column mapping: {str(e)}")
            return {}

    async def _analyze_all_metrics_individually(
        self, 
        estimated_df: pd.DataFrame, 
        actual_df: pd.DataFrame, 
        column_mapping: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """NEW: Deep analysis of each individual metric with comprehensive comparisons."""
        logger.info("[INDIVIDUAL_METRICS] Starting individual metrics analysis")
        
        try:
            individual_metrics = []
            
            for est_col, act_col in column_mapping.items():
                if (est_col in estimated_df.columns and act_col in actual_df.columns):
                    logger.info(f"[INDIVIDUAL_METRICS] Processing {est_col} -> {act_col}")
                    
                    # Check if columns have numeric data (either already numeric or convertible)
                    est_series = estimated_df[est_col]
                    act_series = actual_df[act_col]
                    
                    # Try to convert to numeric and count valid values
                    est_numeric = cast(pd.Series, pd.to_numeric(est_series, errors='coerce'))
                    act_numeric = cast(pd.Series, pd.to_numeric(act_series, errors='coerce'))
                    
                    est_valid_count = est_numeric.notna().sum()
                    act_valid_count = act_numeric.notna().sum()
                    
                    logger.info(f"[INDIVIDUAL_METRICS] {est_col}: {est_valid_count}/{len(est_series)} valid estimated, {act_valid_count}/{len(act_series)} valid actual")
                    
                    # Only analyze if we have sufficient numeric data
                    if est_valid_count >= 3 and act_valid_count >= 3:  # Minimum 3 valid points
                        # Ensure we have proper Series objects for analysis
                        est_series_clean = pd.Series(est_series) if not isinstance(est_series, pd.Series) else est_series
                        act_series_clean = pd.Series(act_series) if not isinstance(act_series, pd.Series) else act_series
                        
                        metric_analysis = await self._analyze_single_metric_deep(
                            est_series_clean, act_series_clean, est_col, act_col
                        )
                        
                        if metric_analysis:
                            individual_metrics.append(metric_analysis)
                            logger.info(f"[INDIVIDUAL_METRICS] Successfully analyzed {est_col}")
                        else:
                            logger.warning(f"[INDIVIDUAL_METRICS] Analysis failed for {est_col}")
                    else:
                        logger.warning(f"[INDIVIDUAL_METRICS] Skipping {est_col} - insufficient numeric data (need >=3, got est:{est_valid_count}, act:{act_valid_count})")
                else:
                    logger.warning(f"[INDIVIDUAL_METRICS] Column missing - est:{est_col} exists: {est_col in estimated_df.columns}, act:{act_col} exists: {act_col in actual_df.columns}")
            
            logger.info(f"[INDIVIDUAL_METRICS] Analyzed {len(individual_metrics)} individual metrics")
            return individual_metrics
            
        except Exception as e:
            logger.error(f"[INDIVIDUAL_METRICS] Error in individual metrics analysis: {str(e)}")
            return []

    async def _analyze_single_metric_deep(
        self, 
        estimated_series: pd.Series, 
        actual_series: pd.Series, 
        est_col_name: str, 
        act_col_name: str
    ) -> Optional[Dict[str, Any]]:
        """Deep analysis of a single metric with comprehensive statistics."""
        try:
            # Ensure we have Series and convert to numeric
            if not isinstance(estimated_series, pd.Series):
                estimated_series = pd.Series(estimated_series)
            if not isinstance(actual_series, pd.Series):
                actual_series = pd.Series(actual_series)
                
            # Convert to numeric and handle errors
            est_numeric = pd.to_numeric(estimated_series, errors='coerce')
            act_numeric = pd.to_numeric(actual_series, errors='coerce')
            
            # Ensure results are Series
            if not isinstance(est_numeric, pd.Series):
                est_numeric = pd.Series(est_numeric)
            if not isinstance(act_numeric, pd.Series):
                act_numeric = pd.Series(act_numeric)
            
            # Find valid indices where both values are not NaN
            valid_indices = ~(est_numeric.isna() | act_numeric.isna())
            est_clean = est_numeric[valid_indices]
            act_clean = act_numeric[valid_indices]
            
            if len(est_clean) == 0 or len(act_clean) == 0:
                logger.warning(f"[SINGLE_METRIC_DEEP] No valid data for {est_col_name}")
                return None
            
            # Ensure we have the same length for aligned comparison
            min_len = min(int(len(est_clean)), int(len(act_clean)))
            est_aligned = est_clean[:min_len]
            act_aligned = act_clean[:min_len]
            
            # Basic statistics
            est_sum = float(est_aligned.sum())
            act_sum = float(act_aligned.sum())
            est_mean = float(est_aligned.mean())
            act_mean = float(act_aligned.mean())
            est_std = float(est_aligned.std()) if len(est_aligned) > 1 else 0.0
            act_std = float(act_aligned.std()) if len(act_aligned) > 1 else 0.0
            
            # Variance calculations with better handling
            if abs(est_sum) > 0.001:  # Avoid division by very small numbers
                variance_percentage = ((act_sum - est_sum) / est_sum) * 100
            else:
                # Handle case where estimated sum is zero or very small
                if abs(act_sum) < 0.001:
                    variance_percentage = 0.0  # Both are essentially zero
                else:
                    variance_percentage = 100.0 if act_sum > 0 else -100.0  # Significant deviation from zero
            
            # Ensure we have proper Series for function calls
            est_series_safe = pd.Series(est_aligned) if not isinstance(est_aligned, pd.Series) else est_aligned
            act_series_safe = pd.Series(act_aligned) if not isinstance(act_aligned, pd.Series) else act_aligned
            
            # MAPE calculation with aligned data
            mape = self._calculate_mape_deep(est_series_safe, act_series_safe)
            
            # Correlation analysis with aligned data
            correlation = 0.0
            if len(est_aligned) > 1 and len(act_aligned) > 1:
                try:
                    # Calculate correlation with aligned data
                    correlation_matrix = np.corrcoef(est_aligned, act_aligned)
                    correlation = correlation_matrix[0, 1]
                    if np.isnan(correlation) or np.isinf(correlation):
                        correlation = 0.0
                except Exception as e:
                    logger.warning(f"[SINGLE_METRIC_DEEP] Correlation calculation failed for {est_col_name}: {str(e)}")
                    correlation = 0.0
            
            # Accuracy score with better handling
            if np.isnan(mape) or np.isinf(mape):
                accuracy_score = 0.0
            else:
                accuracy_score = max(0.0, min(100.0, 100.0 - mape))
            
            # Trend analysis with aligned data
            trend_analysis = self._analyze_trend_patterns_deep(est_series_safe, act_series_safe)
            
            # Outlier detection with aligned data
            outliers = self._detect_outliers_deep(est_series_safe, act_series_safe)
            
            # Business impact assessment
            business_impact = self._assess_business_impact_deep(est_col_name, variance_percentage)
            
            # Ensure all values are finite and valid
            result = {
                'metric_name': est_col_name,
                'matched_column': act_col_name,
                'estimated_total': est_sum,
                'actual_total': act_sum,
                'estimated_mean': est_mean,
                'actual_mean': act_mean,
                'estimated_std': est_std,
                'actual_std': act_std,
                'variance_percentage': variance_percentage,
                'mape': mape if not (np.isnan(mape) or np.isinf(mape)) else 0.0,
                'trend_correlation': correlation,
                'accuracy_score': accuracy_score,
                'trend_analysis': trend_analysis,
                'outliers_detected': outliers,
                'business_impact': business_impact,
                'deviation_severity': self._categorize_variance_severity_deep(variance_percentage),
                'data_points_compared': len(est_aligned),
                'data_quality': 'Good' if len(est_aligned) > 10 else 'Limited' if len(est_aligned) > 3 else 'Poor'
            }
            
            logger.info(f"[SINGLE_METRIC_DEEP] Analyzed {est_col_name}: {len(est_aligned)} points, variance: {variance_percentage:.2f}%, accuracy: {accuracy_score:.1f}%")
            return result
            
        except Exception as e:
            logger.error(f"[SINGLE_METRIC_DEEP] Error analyzing metric {est_col_name}: {str(e)}")
            return None

    def _calculate_mape_deep(self, est_series: pd.Series, act_series: pd.Series) -> float:
        """Calculate Mean Absolute Percentage Error with enhanced handling."""
        try:
            if len(est_series) == 0 or len(act_series) == 0:
                return 100.0  # Return 100% error instead of infinity
            
            # Ensure series are aligned and same length
            min_len = min(len(est_series), len(act_series))
            est_aligned = est_series[:min_len].copy()
            act_aligned = act_series[:min_len].copy()
            
            # Remove pairs where estimated value is zero or very close to zero
            # Use a small threshold to avoid division by very small numbers
            threshold = 0.001
            non_zero_mask = np.abs(est_aligned) > threshold
            
            if not non_zero_mask.any():
                # If all estimated values are zero/very small, use alternative metric
                # Calculate based on absolute differences relative to actual values
                if np.abs(act_aligned).sum() > threshold:
                    return min(100.0, float(np.mean(np.abs(act_aligned))) * 100.0)
                else:
                    return 0.0  # Both series are essentially zero
            
            est_filtered = est_aligned[non_zero_mask]
            act_filtered = act_aligned[non_zero_mask]
            
            # Calculate MAPE with safeguards
            percentage_errors = np.abs((act_filtered - est_filtered) / est_filtered) * 100
            
            # Cap individual errors at 1000% to avoid extreme outliers
            percentage_errors = np.minimum(percentage_errors, 1000.0)
            
            mape = np.mean(percentage_errors)
            
            # Ensure result is finite and reasonable
            if np.isnan(mape) or np.isinf(mape):
                return 100.0
            
            return min(float(mape), 1000.0)  # Cap at 1000% maximum error
            
        except Exception as e:
            logger.error(f"Error calculating MAPE: {str(e)}")
            return 100.0  # Return 100% error instead of infinity

    def _analyze_trend_patterns_deep(self, est_series: pd.Series, act_series: pd.Series) -> Dict[str, Any]:
        """Deep analysis of trend patterns."""
        try:
            trend_info = {
                'estimated_trend': 'stable',
                'actual_trend': 'stable',
                'trend_alignment': 'unknown',
                'trend_strength': 0.0,
                'divergence_points': []
            }
            
            if len(est_series) > 2:
                x = np.arange(len(est_series))
                est_slope = np.polyfit(x, est_series, 1)[0]
                
                if est_slope > 0.1:
                    trend_info['estimated_trend'] = 'increasing'
                elif est_slope < -0.1:
                    trend_info['estimated_trend'] = 'decreasing'
                else:
                    trend_info['estimated_trend'] = 'stable'
            
            if len(act_series) > 2:
                x = np.arange(len(act_series))
                act_slope = np.polyfit(x, act_series, 1)[0]
                
                if act_slope > 0.1:
                    trend_info['actual_trend'] = 'increasing'
                elif act_slope < -0.1:
                    trend_info['actual_trend'] = 'decreasing'
                else:
                    trend_info['actual_trend'] = 'stable'
            
            # Determine alignment
            if trend_info['estimated_trend'] == trend_info['actual_trend']:
                trend_info['trend_alignment'] = 'aligned'
                trend_info['trend_strength'] = 1.0
            else:
                trend_info['trend_alignment'] = 'misaligned'
                trend_info['trend_strength'] = 0.0
            
            # Detect significant divergence points
            if len(est_series) == len(act_series) and len(est_series) > 3:
                diff_series = abs(act_series - est_series)
                threshold = diff_series.mean() + 2 * diff_series.std()
                divergence_indices = diff_series[diff_series > threshold].index.tolist()
                trend_info['divergence_points'] = divergence_indices[:5]  # Limit to 5 points
            
            return trend_info
            
        except Exception as e:
            logger.error(f"Error in deep trend analysis: {str(e)}")
            return {'estimated_trend': 'unknown', 'actual_trend': 'unknown', 'trend_alignment': 'unknown', 'trend_strength': 0.0, 'divergence_points': []}

    def _detect_outliers_deep(self, est_series: pd.Series, act_series: pd.Series) -> Dict[str, Any]:
        """Enhanced outlier detection."""
        try:
            outliers_info = {
                'estimated_outliers_count': 0,
                'actual_outliers_count': 0,
                'outlier_impact': 'low',
                'outlier_indices': []
            }
            
            def detect_outliers_iqr(series):
                if len(series) < 4:
                    return pd.Series([], dtype=series.dtype)
                Q1 = series.quantile(0.25)
                Q3 = series.quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                return series[(series < lower_bound) | (series > upper_bound)]
            
            est_outliers = detect_outliers_iqr(est_series)
            act_outliers = detect_outliers_iqr(act_series)
            
            outliers_info['estimated_outliers_count'] = len(est_outliers)
            outliers_info['actual_outliers_count'] = len(act_outliers)
            # Safely access index only if we have Series objects
            est_indices = list(est_outliers.index) if isinstance(est_outliers, pd.Series) else []
            act_indices = list(act_outliers.index) if isinstance(act_outliers, pd.Series) else []
            outliers_info['outlier_indices'] = est_indices + act_indices
            
            total_outliers = len(est_outliers) + len(act_outliers)
            total_points = len(est_series) + len(act_series)
            
            if total_points > 0:
                outlier_ratio = total_outliers / total_points
                if outlier_ratio > 0.1:
                    outliers_info['outlier_impact'] = 'high'
                elif outlier_ratio > 0.05:
                    outliers_info['outlier_impact'] = 'medium'
                else:
                    outliers_info['outlier_impact'] = 'low'
            
            return outliers_info
            
        except Exception as e:
            logger.error(f"Error in deep outlier detection: {str(e)}")
            return {'estimated_outliers_count': 0, 'actual_outliers_count': 0, 'outlier_impact': 'unknown', 'outlier_indices': []}

    def _assess_business_impact_deep(self, column_name: str, variance_pct: float) -> str:
        """Enhanced business impact assessment."""
        try:
            col_lower = column_name.lower()
            abs_variance = abs(variance_pct)
            
            # Critical business metrics
            if any(keyword in col_lower for keyword in ['revenue', 'sales', 'profit', 'income']):
                if abs_variance > 20:
                    return "Critical - High Financial Impact"
                elif abs_variance > 10:
                    return "High - Significant Financial Impact"
                else:
                    return "Medium - Financial Impact"
            
            # Operational metrics
            elif any(keyword in col_lower for keyword in ['units', 'quantity', 'volume', 'energy', 'delivered']):
                if abs_variance > 25:
                    return "High - Major Operational Impact"
                elif abs_variance > 15:
                    return "Medium - Operational Impact"
                else:
                    return "Low - Minor Operational Impact"
            
            # Performance metrics
            elif any(keyword in col_lower for keyword in ['rating', 'score', 'performance', 'efficiency']):
                if abs_variance > 15:
                    return "Medium - Performance Impact"
                else:
                    return "Low - Performance Impact"
            
            # Cost metrics
            elif any(keyword in col_lower for keyword in ['cost', 'expense', 'spend']):
                if abs_variance > 20:
                    return "Critical - Cost Overrun Impact"
                elif abs_variance > 10:
                    return "High - Cost Impact"
                else:
                    return "Medium - Cost Impact"
            
            # Default assessment
            else:
                if abs_variance > 30:
                    return "High - General Impact"
                elif abs_variance > 15:
                    return "Medium - General Impact"
                else:
                    return "Low - General Impact"
                    
        except Exception:
            return "Unknown Impact"

    def _categorize_variance_severity_deep(self, variance_pct: float) -> str:
        """Enhanced variance severity categorization."""
        try:
            abs_variance = abs(variance_pct)
            
            if abs_variance > 50:
                return 'critical'
            elif abs_variance > 25:
                return 'high'
            elif abs_variance > 15:
                return 'significant'
            elif abs_variance > 10:
                return 'moderate'
            elif abs_variance > 5:
                return 'minor'
            else:
                return 'minimal'
                
        except Exception:
                         return 'unknown'

    # Continue with remaining enhanced methods
    
    async def _analyze_enhanced_variance(
        self, 
        estimated_df: pd.DataFrame, 
        actual_df: pd.DataFrame, 
        column_mapping: Dict[str, str]
    ) -> Dict[str, Any]:
        """Enhanced variance analysis with comprehensive insights."""
        logger.info("[ENHANCED_VARIANCE] Starting enhanced variance analysis")
        
        try:
            variance_results = {
                'overall_variance': 0.0,
                'column_variances': {},
                'critical_deviations': [],
                'variance_distribution': {},
                'accuracy_metrics': {},
                'estimated_columns_count': len(estimated_df.columns),  # Track total columns
                'actual_columns_count': len(actual_df.columns),        # Track total columns
                'summary': {}
            }
            
            column_variances = []
            critical_deviations = []
            accuracy_scores = []
            
            for est_col, act_col in column_mapping.items():
                if (est_col in estimated_df.columns and act_col in actual_df.columns):
                    if (pd.api.types.is_numeric_dtype(estimated_df[est_col]) and 
                        pd.api.types.is_numeric_dtype(actual_df[act_col])):
                        
                        # Get detailed variance analysis
                        est_clean = cast(pd.Series, pd.to_numeric(estimated_df[est_col], errors='coerce')).dropna()
                        act_clean = cast(pd.Series, pd.to_numeric(actual_df[act_col], errors='coerce')).dropna()
                        
                        if len(est_clean) > 0 and len(act_clean) > 0:
                            est_sum = est_clean.sum()
                            act_sum = act_clean.sum()
                            
                            if est_sum != 0:
                                variance_pct = ((act_sum - est_sum) / est_sum) * 100
                            else:
                                variance_pct = 0 if act_sum == 0 else float('inf')
                            
                            mape = self._calculate_mape_deep(est_clean, act_clean)
                            accuracy_score = max(0, 100 - mape) if not np.isnan(mape) and mape != float('inf') else 0
                            
                            variance_info = {
                                'variance_percentage': float(variance_pct),
                                'mape': float(mape) if not np.isnan(mape) else 0.0,
                                'accuracy_score': float(accuracy_score),
                                'estimated_sum': float(est_sum),
                                'actual_sum': float(act_sum)
                            }
                            
                            variance_results['column_variances'][f"{est_col}_vs_{act_col}"] = variance_info
                            column_variances.append(variance_pct)
                            accuracy_scores.append(accuracy_score)
                            
                            # Check for critical deviations
                            if abs(variance_pct) > self.variance_thresholds['critical'] * 100:
                                critical_deviations.append({
                                    'columns': f"{est_col} vs {act_col}",
                                    'metric': est_col,  # Add single metric name for consistency
                                    'metric_name': est_col,  # Add metric_name field explicitly
                                    'estimated_column': est_col,
                                    'actual_column': act_col,
                                    'variance_percentage': float(variance_pct),
                                    'severity': self._categorize_variance_severity_deep(variance_pct),
                                    'business_impact': self._assess_business_impact_deep(est_col, variance_pct),
                                    'estimated_total': float(est_sum),
                                    'actual_total': float(act_sum),
                                    'estimated_value': float(est_sum),  # Add for consistency
                                    'actual_value': float(act_sum),     # Add for consistency
                                    'mape': float(mape) if not np.isnan(mape) else 0.0,
                                    'accuracy_score': float(accuracy_score)
                                })
            
            # Calculate enhanced statistics
            if column_variances:
                variance_results['overall_variance'] = np.mean([abs(v) for v in column_variances if not np.isinf(v)])
                valid_variances = [v for v in column_variances if not np.isinf(v)]
                if valid_variances:
                    variance_results['variance_distribution'] = {
                        'mean': float(np.mean(valid_variances)),
                        'median': float(np.median(valid_variances)),
                        'std': float(np.std(valid_variances)),
                        'min': float(np.min(valid_variances)),
                        'max': float(np.max(valid_variances))
                    }
            
            if accuracy_scores:
                variance_results['accuracy_metrics'] = {
                    'average_accuracy': float(np.mean(accuracy_scores)),
                    'best_accuracy': float(np.max(accuracy_scores)),
                    'worst_accuracy': float(np.min(accuracy_scores)),
                    'accuracy_std': float(np.std(accuracy_scores))
                }
            
            variance_results['critical_deviations'] = critical_deviations
            variance_results['summary'] = {
                'total_comparisons': len(variance_results['column_variances']),
                'critical_deviations_count': len(critical_deviations),
                'average_variance': variance_results['overall_variance'],
                'high_impact_metrics': len([d for d in critical_deviations if 'Critical' in d.get('business_impact', '')])
            }
            
            logger.info(f"[ENHANCED_VARIANCE] Enhanced analysis completed. Overall variance: {variance_results['overall_variance']:.2f}%")
            return variance_results
            
        except Exception as e:
            logger.error(f"[ENHANCED_VARIANCE] Error in enhanced variance analysis: {str(e)}")
            return {
                'overall_variance': 0.0,
                'column_variances': {},
                'critical_deviations': [],
                'summary': {'error': str(e)}
            }

    async def _analyze_trend_deviations_deep(
        self, 
        estimated_df: pd.DataFrame, 
        actual_df: pd.DataFrame, 
        column_mapping: Dict[str, str]
    ) -> Dict[str, Any]:
        """NEW: Deep trend deviation analysis with correlation coefficients and divergence detection."""
        logger.info("[TREND_DEVIATIONS] Starting deep trend deviation analysis")
        
        try:
            trend_results = {
                'overall_alignment_status': 'unknown',
                'metric_trend_correlations': {},
                'divergence_periods': [],
                'correlation_distribution': {},
                'summary': {}
            }
            
            correlations = []
            all_divergences = []
            
            for est_col, act_col in column_mapping.items():
                if (pd.api.types.is_numeric_dtype(estimated_df[est_col]) and 
                    pd.api.types.is_numeric_dtype(actual_df[act_col])):
                    
                    est_clean = cast(pd.Series, pd.to_numeric(estimated_df[est_col], errors='coerce')).dropna()
                    act_clean = cast(pd.Series, pd.to_numeric(actual_df[act_col], errors='coerce')).dropna()
                    
                    if len(est_clean) > 2 and len(act_clean) > 2:
                        # Calculate correlation
                        min_len = min(len(est_clean), len(act_clean))
                        try:
                            correlation = np.corrcoef(est_clean[:min_len], act_clean[:min_len])[0, 1]
                            if np.isnan(correlation):
                                correlation = 0.0
                        except:
                            correlation = 0.0
                        
                        # Analyze trend patterns
                        trend_analysis = self._analyze_trend_patterns_deep(est_clean, act_clean)
                        
                        # Detect divergence periods
                        divergences = self._detect_divergence_periods_deep(est_clean, act_clean, est_col)
                        
                        trend_info = {
                            'correlation_coefficient': float(correlation),
                            'trend_analysis': trend_analysis,
                            'divergence_periods': divergences,
                            'correlation_interpretation': self._interpret_correlation_deep(correlation)
                        }
                        
                        trend_results['metric_trend_correlations'][f"{est_col}_vs_{act_col}"] = trend_info
                        correlations.append(correlation)
                        all_divergences.extend(divergences)
            
            # Calculate overall alignment status and categorize correlations
            if correlations:
                valid_correlations = [c for c in correlations if not np.isnan(c)]
                avg_correlation = np.mean(valid_correlations) if valid_correlations else 0.0
                
                # Determine overall alignment status - IMPROVED: Consider variance context
                variance_context = getattr(self, '_current_variance', 0.0)
                critical_issues = getattr(self, '_current_critical_count', 0)
                
                if avg_correlation > 0.85 and variance_context < 15 and critical_issues < 3:
                    trend_results['overall_alignment_status'] = 'strong_alignment'
                elif avg_correlation > 0.75 and variance_context < 25 and critical_issues < 5:
                    trend_results['overall_alignment_status'] = 'good_alignment'
                elif avg_correlation > 0.7:  # High correlation but concerning variance
                    trend_results['overall_alignment_status'] = 'mixed_alignment'
                elif avg_correlation > 0.5:
                    trend_results['overall_alignment_status'] = 'moderate_alignment'
                elif avg_correlation > 0.3:
                    trend_results['overall_alignment_status'] = 'weak_alignment'
                else:
                    trend_results['overall_alignment_status'] = 'poor_alignment'
                
                # **FIXED**: Properly categorize correlations into buckets
                correlation_buckets = {
                    'very_strong': len([c for c in valid_correlations if abs(c) >= 0.9]),
                    'strong': len([c for c in valid_correlations if 0.7 <= abs(c) < 0.9]),
                    'moderate': len([c for c in valid_correlations if 0.5 <= abs(c) < 0.7]),
                    'weak': len([c for c in valid_correlations if 0.3 <= abs(c) < 0.5]),
                    'very_weak': len([c for c in valid_correlations if abs(c) < 0.3])
                }
                
                trend_results['correlation_distribution'] = {
                    **correlation_buckets,
                    'mean': float(avg_correlation),
                    'median': float(np.median(valid_correlations)),
                    'std': float(np.std(valid_correlations)),
                    'min': float(np.min(valid_correlations)),
                    'max': float(np.max(valid_correlations))
                }
                
                logger.info(f"[TREND_DEVIATIONS] Correlation buckets: {correlation_buckets}")
            else:
                trend_results['correlation_distribution'] = {
                    'very_strong': 0, 'strong': 0, 'moderate': 0, 'weak': 0, 'very_weak': 0,
                    'mean': 0.0, 'median': 0.0, 'std': 0.0, 'min': 0.0, 'max': 0.0
                }
            
            trend_results['divergence_periods'] = all_divergences[:10]  # Limit to top 10
            trend_results['summary'] = {
                'metrics_analyzed': len(correlations),
                'average_correlation': float(np.mean([c for c in correlations if not np.isnan(c)])) if correlations else 0.0,
                'divergence_periods_found': len(all_divergences),
                'strong_correlations_count': trend_results['correlation_distribution']['very_strong'] + trend_results['correlation_distribution']['strong'],
                'weak_correlations_count': trend_results['correlation_distribution']['weak'] + trend_results['correlation_distribution']['very_weak']
            }
            
            logger.info(f"[TREND_DEVIATIONS] Analysis completed. Overall status: {trend_results['overall_alignment_status']}")
            logger.info(f"[TREND_DEVIATIONS] Metrics analyzed: {len(correlations)}, Strong correlations: {trend_results['summary']['strong_correlations_count']}")
            return trend_results
            
        except Exception as e:
            logger.error(f"[TREND_DEVIATIONS] Error in trend deviation analysis: {str(e)}")
            return {
                'overall_alignment_status': 'unknown',
                'metric_trend_correlations': {},
                'divergence_periods': [],
                'correlation_distribution': {
                    'very_strong': 0, 'strong': 0, 'moderate': 0, 'weak': 0, 'very_weak': 0,
                    'mean': 0.0, 'median': 0.0, 'std': 0.0, 'min': 0.0, 'max': 0.0
                },
                'summary': {'error': str(e), 'metrics_analyzed': 0, 'strong_correlations_count': 0, 'weak_correlations_count': 0}
            }

    def _detect_divergence_periods_deep(self, est_series: pd.Series, act_series: pd.Series, metric_name: str) -> List[Dict[str, Any]]:
        """Detect periods where estimated and actual trends diverge significantly."""
        try:
            divergences = []
            
            if len(est_series) != len(act_series) or len(est_series) < 5:
                return divergences
            
            # Calculate rolling differences
            diff_series = act_series - est_series
            rolling_mean = diff_series.rolling(window=3, center=True).mean()
            rolling_std = diff_series.rolling(window=3, center=True).std()
            
            # Detect significant deviations (beyond 2 standard deviations)
            threshold_multiplier = 2.0
            significant_deviations = abs(rolling_mean) > (threshold_multiplier * rolling_std)
            
            # Group consecutive deviations into periods
            in_divergence = False
            start_idx = None
            
            for i, is_deviation in enumerate(significant_deviations.fillna(False)):
                if is_deviation and not in_divergence:
                    in_divergence = True
                    start_idx = i
                elif not is_deviation and in_divergence:
                    in_divergence = False
                    if start_idx is not None and i > start_idx:
                        avg_dev = rolling_mean.iloc[start_idx:i].mean()
                        max_dev = abs(rolling_mean.iloc[start_idx:i]).max()
                        
                        divergences.append({
                            'metric': metric_name,
                            'start_period': int(start_idx),
                            'end_period': int(i - 1),
                            'duration': int(i - start_idx),
                            'avg_deviation': float(avg_dev) if not np.isnan(avg_dev) else 0.0,
                            'max_deviation': float(max_dev) if not np.isnan(max_dev) else 0.0,
                            'severity': self._categorize_divergence_severity_deep(max_dev)
                        })
            
            # Handle case where divergence continues to the end
            if in_divergence and start_idx is not None:
                avg_dev = rolling_mean.iloc[start_idx:].mean()
                max_dev = abs(rolling_mean.iloc[start_idx:]).max()
                
                divergences.append({
                    'metric': metric_name,
                    'start_period': int(start_idx),
                    'end_period': int(len(est_series) - 1),
                    'duration': int(len(est_series) - start_idx),
                    'avg_deviation': float(avg_dev) if not np.isnan(avg_dev) else 0.0,
                    'max_deviation': float(max_dev) if not np.isnan(max_dev) else 0.0,
                    'severity': self._categorize_divergence_severity_deep(max_dev)
                })
            
            return divergences
            
        except Exception as e:
            logger.error(f"Error detecting divergence periods for {metric_name}: {str(e)}")
            return []

    def _categorize_divergence_severity_deep(self, max_deviation: float) -> str:
        """Categorize the severity of trend divergence."""
        try:
            if np.isnan(max_deviation):
                return 'unknown'
                
            abs_deviation = abs(max_deviation)
            if abs_deviation > 100:
                return 'critical'
            elif abs_deviation > 50:
                return 'high'
            elif abs_deviation > 20:
                return 'moderate'
            else:
                return 'low'
        except Exception:
            return 'unknown'

    def _interpret_correlation_deep(self, correlation: float) -> str:
        """Provide human-readable interpretation of correlation coefficient."""
        try:
            if np.isnan(correlation):
                return "No correlation could be calculated"
                
            abs_corr = abs(correlation)
            
            if abs_corr >= 0.9:
                strength = "very strong"
            elif abs_corr >= 0.7:
                strength = "strong"
            elif abs_corr >= 0.5:
                strength = "moderate"
            elif abs_corr >= 0.3:
                strength = "weak"
            else:
                strength = "very weak"
            
            direction = "positive" if correlation >= 0 else "negative"
            
            return f"{strength} {direction} correlation (r={correlation:.3f})"
            
        except Exception:
            return f"correlation coefficient: {correlation:.3f}"

    async def _extract_granular_insights_deep(
        self, 
        estimated_df: pd.DataFrame, 
        actual_df: pd.DataFrame, 
        column_mapping: Dict[str, str],
        individual_metrics: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """NEW: Extract granular insights by regions, products, or categories."""
        logger.info("[GRANULAR_INSIGHTS] Starting granular insights extraction")
        
        try:
            granular_insights = {
                'insights_by_category': {},
                'regional_analysis': {},
                'product_analysis': {},
                'temporal_analysis': {},
                'summary': {}
            }
            
            # Find categorical columns for grouping
            categorical_columns = []
            for est_col, act_col in column_mapping.items():
                if (est_col in estimated_df.columns and act_col in actual_df.columns):
                    if not pd.api.types.is_numeric_dtype(estimated_df[est_col]):
                        # Check if it's a reasonable categorical column
                        unique_values = estimated_df[est_col].nunique()
                        if 2 <= unique_values <= 20:  # Reasonable number of categories
                            categorical_columns.append((est_col, act_col))
            
            # Analyze by categories
            for est_cat_col, act_cat_col in categorical_columns[:3]:  # Limit to 3 categorical analyses
                category_insights = await self._analyze_by_category_deep(
                    estimated_df, actual_df, column_mapping, est_cat_col, act_cat_col, individual_metrics
                )
                granular_insights['insights_by_category'][est_cat_col] = category_insights
            
            # Regional analysis (look for region-like columns)
            regional_insights = await self._analyze_regional_patterns_deep(
                estimated_df, actual_df, column_mapping, individual_metrics
            )
            granular_insights['regional_analysis'] = regional_insights
            
            # Product analysis (look for product-like columns)
            product_insights = await self._analyze_product_patterns_deep(
                estimated_df, actual_df, column_mapping, individual_metrics
            )
            granular_insights['product_analysis'] = product_insights
            
            # Identify highest and lowest performing segments
            performance_summary = await self._summarize_segment_performance_deep(granular_insights)
            granular_insights['summary'] = performance_summary
            
            logger.info(f"[GRANULAR_INSIGHTS] Granular insights extraction completed")
            return granular_insights
            
        except Exception as e:
            logger.error(f"[GRANULAR_INSIGHTS] Error in granular insights extraction: {str(e)}")
            return {
                'insights_by_category': {},
                'summary': {'error': str(e)}
            }

    async def _analyze_by_category_deep(
        self, 
        estimated_df: pd.DataFrame, 
        actual_df: pd.DataFrame, 
        column_mapping: Dict[str, str],
        est_cat_col: str,
        act_cat_col: str,
        individual_metrics: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze performance by specific category."""
        try:
            category_analysis = {
                'category_name': est_cat_col,
                'category_performance': {},
                'highest_deviation_category': None,
                'lowest_deviation_category': None,
                'insights': []
            }
            
            # Get unique categories
            est_categories = estimated_df[est_cat_col].dropna().unique()
            act_categories = actual_df[act_cat_col].dropna().unique()
            common_categories = list(set(est_categories) & set(act_categories))
            
            category_deviations = {}
            
            # Analyze each category
            for category in common_categories[:10]:  # Limit to 10 categories
                est_category_data = estimated_df[estimated_df[est_cat_col] == category]
                act_category_data = actual_df[actual_df[act_cat_col] == category]
                
                # Calculate metrics for this category
                category_metrics = []
                for est_col, act_col in column_mapping.items():
                    if (pd.api.types.is_numeric_dtype(estimated_df[est_col]) and 
                        pd.api.types.is_numeric_dtype(actual_df[act_col])):
                        
                        est_values = cast(pd.Series, pd.to_numeric(est_category_data[est_col], errors='coerce')).dropna()
                        act_values = cast(pd.Series, pd.to_numeric(act_category_data[act_col], errors='coerce')).dropna()
                        
                        if len(est_values) > 0 and len(act_values) > 0:
                            est_sum = est_values.sum()
                            act_sum = act_values.sum()
                            
                            if est_sum != 0:
                                variance_pct = ((act_sum - est_sum) / est_sum) * 100
                                category_metrics.append({
                                    'metric': est_col,
                                    'variance_percentage': variance_pct,
                                    'estimated_total': est_sum,
                                    'actual_total': act_sum
                                })
                
                if category_metrics:
                    avg_variance = np.mean([abs(m['variance_percentage']) for m in category_metrics])
                    category_deviations[str(category)] = avg_variance
                    
                    category_analysis['category_performance'][str(category)] = {
                        'average_variance': float(avg_variance),
                        'metrics': category_metrics,
                        'data_points': len(est_category_data)
                    }
            
            # Find highest and lowest deviation categories
            if category_deviations:
                highest_dev_cat = max(category_deviations.items(), key=lambda x: x[1])
                lowest_dev_cat = min(category_deviations.items(), key=lambda x: x[1])
                
                category_analysis['highest_deviation_category'] = {
                    'category': highest_dev_cat[0],
                    'deviation': highest_dev_cat[1]
                }
                category_analysis['lowest_deviation_category'] = {
                    'category': lowest_dev_cat[0],
                    'deviation': lowest_dev_cat[1]
                }
                
                # Generate insights
                if highest_dev_cat[1] > 20:
                    category_analysis['insights'].append(f"Category '{highest_dev_cat[0]}' shows significant deviation ({highest_dev_cat[1]:.1f}%) requiring immediate attention")
                
                if lowest_dev_cat[1] < 5:
                    category_analysis['insights'].append(f"Category '{lowest_dev_cat[0]}' demonstrates excellent forecast accuracy ({lowest_dev_cat[1]:.1f}% deviation)")
            
            return category_analysis
            
        except Exception as e:
            logger.error(f"Error in category analysis for {est_cat_col}: {str(e)}")
            return {'category_name': est_cat_col, 'error': str(e)}

    async def _analyze_regional_patterns_deep(self, estimated_df, actual_df, column_mapping, individual_metrics):
        """Analyze regional patterns if regional data is available."""
        # Simplified placeholder - could be enhanced based on specific regional columns
        return {
            'regions_analyzed': 0,
            'insights': ["Regional analysis requires specific geographical identifiers"]
        }

    async def _analyze_product_patterns_deep(self, estimated_df, actual_df, column_mapping, individual_metrics):
        """Analyze product patterns if product data is available."""
        # Simplified placeholder - could be enhanced based on specific product columns
        return {
            'products_analyzed': 0,
            'insights': ["Product analysis requires specific product identifiers"]
        }

    async def _summarize_segment_performance_deep(self, granular_insights):
        """Summarize overall segment performance."""
        try:
            summary = {
                'categories_analyzed': len(granular_insights.get('insights_by_category', {})),
                'key_findings': [],
                'recommendations': []
            }
            
            # Extract key findings from category analysis
            for category_name, category_data in granular_insights.get('insights_by_category', {}).items():
                if 'highest_deviation_category' in category_data and category_data['highest_deviation_category']:
                    highest = category_data['highest_deviation_category']
                    summary['key_findings'].append(f"In {category_name}, '{highest['category']}' has highest deviation ({highest['deviation']:.1f}%)")
                
                if 'lowest_deviation_category' in category_data and category_data['lowest_deviation_category']:
                    lowest = category_data['lowest_deviation_category']
                    summary['key_findings'].append(f"In {category_name}, '{lowest['category']}' has best accuracy ({lowest['deviation']:.1f}%)")
            
            return summary
            
        except Exception as e:
            logger.error(f"Error summarizing segment performance: {str(e)}")
            return {'error': str(e)}

    async def _detect_missing_metrics_deep(
        self, 
        estimated_df: pd.DataFrame, 
        actual_df: pd.DataFrame, 
        column_mapping: Dict[str, str]
    ) -> Dict[str, Any]:
        """NEW: Detect missing metrics between estimated and actual datasets."""
        logger.info("[MISSING_METRICS] Starting missing metrics detection")
        
        try:
            # Get all numeric columns from both datasets
            est_numeric_cols = set(estimated_df.select_dtypes(include=[np.number]).columns)
            act_numeric_cols = set(actual_df.select_dtypes(include=[np.number]).columns)
            
            # Find columns that exist in one dataset but not the other
            est_only = est_numeric_cols - set(column_mapping.keys())
            act_only = act_numeric_cols - set(column_mapping.values())
            
            # Identify unmapped columns that could potentially be important
            missing_from_actual = []
            missing_from_estimated = []
            
            # Columns in estimated but not matched to actual
            for col in est_only:
                col_data = estimated_df[col].dropna()
                if len(col_data) > 0 and col_data.sum() > 0:  # Has meaningful data
                    missing_from_actual.append({
                        'column_name': col,
                        'estimated_total': float(col_data.sum()),
                        'estimated_mean': float(col_data.mean()),
                        'potential_impact': self._assess_business_impact_deep(col, 0)
                    })
            
            # Columns in actual but not matched to estimated
            for col in act_only:
                col_data = actual_df[col].dropna()
                if len(col_data) > 0 and col_data.sum() > 0:  # Has meaningful data
                    missing_from_estimated.append({
                        'column_name': col,
                        'actual_total': float(col_data.sum()),
                        'actual_mean': float(col_data.mean()),
                        'potential_impact': self._assess_business_impact_deep(col, 0)
                    })
            
            # Generate insights about missing metrics
            insights = []
            if missing_from_actual:
                insights.append(f"Found {len(missing_from_actual)} metrics in estimated data that have no corresponding actual values")
            if missing_from_estimated:
                insights.append(f"Found {len(missing_from_estimated)} metrics in actual data that have no corresponding estimated values")
            
            # Identify high-impact missing metrics
            high_impact_missing = []
            for metric in missing_from_actual + missing_from_estimated:
                if metric['potential_impact'] in ['high', 'critical']:
                    high_impact_missing.append(metric)
            
            return {
                'missing_from_actual': missing_from_actual,
                'missing_from_estimated': missing_from_estimated,
                'high_impact_missing': high_impact_missing,
                'total_missing_count': len(missing_from_actual) + len(missing_from_estimated),
                'insights': insights,
                'summary': {
                    'est_only_count': len(missing_from_actual),
                    'act_only_count': len(missing_from_estimated),
                    'high_impact_count': len(high_impact_missing)
                }
            }
            
        except Exception as e:
            logger.error(f"[MISSING_METRICS] Error detecting missing metrics: {str(e)}")
            return {
                'missing_from_actual': [],
                'missing_from_estimated': [],
                'high_impact_missing': [],
                'total_missing_count': 0,
                'insights': [f"Error in missing metrics detection: {str(e)}"],
                'summary': {'error': str(e)}
            }

    async def _prioritize_by_business_impact(
        self,
        individual_metrics: List[Dict[str, Any]],
        variance_analysis: Dict[str, Any],
        trend_deviation_analysis: Dict[str, Any],
        granular_insights: Dict[str, Any]
    ) -> Dict[str, Any]:
        """NEW: Prioritize insights by business impact for actionable recommendations."""
        logger.info("[BUSINESS_IMPACT] Starting business impact prioritization")
        
        try:
            high_impact_deviations = []
            medium_impact_deviations = []
            low_impact_deviations = []
            
            # Process individual metrics by impact
            for metric in individual_metrics:
                impact_level = metric.get('business_impact', 'low')
                variance_pct = abs(metric.get('variance_percentage', 0))
                severity = metric.get('deviation_severity', 'minor')
                
                deviation_item = {
                    'metric_name': metric.get('metric_name'),
                    'variance_percentage': variance_pct,
                    'business_impact': impact_level,
                    'severity': severity,
                    'trend_correlation': metric.get('trend_correlation', 0),
                    'accuracy_score': metric.get('accuracy_score', 0),
                    'recommendation_priority': 'high' if (impact_level in ['high', 'critical'] and variance_pct > 15) else 'medium' if variance_pct > 10 else 'low'
                }
                
                # Categorize by combined impact and severity
                if (impact_level in ['high', 'critical'] and severity in ['critical', 'significant']) or variance_pct > 25:
                    high_impact_deviations.append(deviation_item)
                elif (impact_level == 'medium' and severity in ['significant', 'moderate']) or variance_pct > 10:
                    medium_impact_deviations.append(deviation_item)
                else:
                    low_impact_deviations.append(deviation_item)
            
            # Sort each category by variance percentage (descending)
            high_impact_deviations.sort(key=lambda x: abs(x['variance_percentage']), reverse=True)
            medium_impact_deviations.sort(key=lambda x: abs(x['variance_percentage']), reverse=True)
            low_impact_deviations.sort(key=lambda x: abs(x['variance_percentage']), reverse=True)
            
            # Generate actionable insights in the correct format for frontend
            actionable_insights = []
            
            # High impact insights
            for deviation in high_impact_deviations[:3]:  # Top 3 high impact
                # Create structured points for critical issues
                critical_points = [
                    f'Metric: {deviation["metric_name"]}',
                    f'Variance: {deviation["variance_percentage"]:.1f}% deviation from estimates',
                    f'Business Impact: {deviation["business_impact"].title()} - General Impact priority metric',
                    f'Severity: {deviation["severity"].title()}',
                    f'Trend Alignment: {"Poor - requires investigation" if deviation["trend_correlation"] < 0.6 else "Acceptable"}',
                    f'Accuracy Score: {deviation["accuracy_score"]:.1f}%',
                    f'Recommendation Priority: {deviation["recommendation_priority"].title()}',
                    'Review forecasting methodology for this metric',
                    'Investigate potential data quality issues',
                    'Adjust model parameters based on recent performance',
                    'Implement enhanced monitoring until variance reduces',
                    'Expected Outcome: Reduce variance to <10% within next review cycle'
                ]
                
                insight = {
                    'title': f'🚨 Critical Issue: {deviation["metric_name"]}',
                    'description': f'Critical deviation detected requiring immediate attention',
                    'points': critical_points,
                    'type': 'critical_deviation',
                    'severity': 'high'
                }
                actionable_insights.append(insight)
            
            # Medium impact insights with structured points
            for deviation in medium_impact_deviations[:2]:  # Top 2 medium impact
                # Create structured points for moderate issues
                moderate_points = [
                    f'Metric: {deviation["metric_name"]}',
                    f'Variance: {deviation["variance_percentage"]:.1f}% deviation from estimates',
                    f'Business Impact: Medium - monitor closely',
                    f'Severity: {deviation["severity"].title()}',
                    f'Trend Alignment: {"Acceptable" if deviation["trend_correlation"] >= 0.6 else "Needs monitoring"}',
                    f'Accuracy Score: {deviation["accuracy_score"]:.1f}%',
                    f'Recommendation Priority: {deviation["recommendation_priority"].title()}',
                    'Schedule review in next planning cycle',
                    'Monitor trend alignment over time',
                    'Consider model calibration adjustments',
                    'Document any external factors affecting this metric',
                    'Expected Outcome: Maintain variance below 15% threshold'
                ]
                
                insight = {
                    'title': f'⚠️ Monitor: {deviation["metric_name"]}',
                    'description': f'Moderate deviation requiring monitoring and review',
                    'points': moderate_points,
                    'type': 'moderate_deviation',
                    'severity': 'medium'
                }
                actionable_insights.append(insight)
            
            # Add a summary insight if no critical issues
            if len(high_impact_deviations) == 0 and len(medium_impact_deviations) == 0:
                summary_insight = {
                    'title': '✅ Performance Summary',
                    'description': f"""**Overall performance within acceptable ranges**

📊 **Performance Overview**:
• **Total Metrics Analyzed**: {len(individual_metrics)}
• **High Impact Issues**: {len(high_impact_deviations)} (None detected)
• **Medium Impact Issues**: {len(medium_impact_deviations)} (None detected)
• **Low Impact Variations**: {len(low_impact_deviations)}

🎯 **Key Findings**:
• All critical metrics performing within acceptable variance thresholds
• No immediate corrective actions required
• Forecasting models appear well-calibrated
• Continue standard monitoring procedures

📋 **Recommended Actions**:
• Maintain current forecasting methodology
• Continue quarterly performance reviews
• Monitor for any emerging patterns in low-impact variations
• Document successful practices for future reference

🎯 **Status**: All systems performing optimally""",
                    'type': 'performance_summary',
                    'severity': 'positive'
                }
                actionable_insights.append(summary_insight)
            elif len(actionable_insights) == 0:
                # Fallback insight if no insights were generated
                fallback_insight = {
                    'title': '📊 Analysis Complete',
                    'description': f"""**Comparison analysis completed successfully**

📊 **Analysis Summary**:
• **Total Metrics Processed**: {len(individual_metrics)}
• **Analysis Level**: Business Impact Prioritization
• **Issues Identified**: {len(high_impact_deviations) + len(medium_impact_deviations)}

🔍 **Results**:
• Comprehensive variance analysis completed
• Trend correlation assessment performed
• Business impact evaluation conducted
• Recommendations generated based on findings

📋 **Next Steps**:
• Review detailed analysis results
• Implement any recommended actions
• Schedule follow-up analysis as needed""",
                    'type': 'analysis_complete',
                    'severity': 'info'
                }
                actionable_insights.append(fallback_insight)
            
            return {
                'high_impact_deviations': high_impact_deviations,
                'medium_impact_deviations': medium_impact_deviations,
                'low_impact_deviations': low_impact_deviations,
                'insights': actionable_insights,
                'summary': {
                    'high_impact_count': len(high_impact_deviations),
                    'medium_impact_count': len(medium_impact_deviations),
                    'low_impact_count': len(low_impact_deviations),
                    'total_issues': len(high_impact_deviations) + len(medium_impact_deviations) + len(low_impact_deviations),
                    'immediate_attention_required': len(high_impact_deviations)
                }
            }
            
        except Exception as e:
            logger.error(f"[BUSINESS_IMPACT] Error in business impact prioritization: {str(e)}")
            return {
                'high_impact_deviations': [],
                'medium_impact_deviations': [],
                'low_impact_deviations': [],
                'insights': [],
                'summary': {'error': str(e)}
            }

    async def _create_enhanced_charts_deep(
        self,
        estimated_df: pd.DataFrame,
        actual_df: pd.DataFrame,
        column_mapping: Dict[str, str],
        individual_metrics: List[Dict[str, Any]],
        variance_analysis: Dict[str, Any],
        trend_deviation_analysis: Dict[str, Any],
        granular_insights: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """NEW: Create comprehensive enhanced charts for deep analysis visualization with premium aesthetics."""
        logger.info("[ENHANCED_CHARTS] Starting enhanced chart generation")
        
        try:
            charts = []
            
            # Premium color palettes with gradients
            color_schemes = {
                'blue': {
                    'primary': '#3b82f6',
                    'secondary': '#60a5fa', 
                    'tertiary': '#93c5fd',
                    'gradient': ['#3b82f6', '#2563eb', '#1d4ed8', '#1e40af']
                },
                'green': {
                    'primary': '#10b981',
                    'secondary': '#34d399',
                    'tertiary': '#6ee7b7',
                    'gradient': ['#10b981', '#059669', '#047857', '#065f46']
                },
                'red': {
                    'primary': '#ef4444',
                    'secondary': '#f87171',
                    'tertiary': '#fca5a5',
                    'gradient': ['#ef4444', '#dc2626', '#b91c1c', '#991b1b']
                },
                'purple': {
                    'primary': '#8b5cf6',
                    'secondary': '#a78bfa',
                    'tertiary': '#c4b5fd',
                    'gradient': ['#8b5cf6', '#7c3aed', '#6d28d9', '#5b21b6']
                },
                'orange': {
                    'primary': '#f59e0b',
                    'secondary': '#fbbf24',
                    'tertiary': '#fcd34d',
                    'gradient': ['#f59e0b', '#d97706', '#b45309', '#92400e']
                }
            }
            
            # 1. **ENHANCED** Individual Metric Comparison Charts with premium styling
            valid_charts_created = 0
            logger.info(f"[ENHANCED_CHARTS] Starting chart generation for {len(individual_metrics)} metrics")
            
            for metric_idx, metric in enumerate(individual_metrics[:6]):  # Limit to top 6 metrics
                metric_name = metric.get('metric_name', 'Unknown')
                est_col = metric_name
                act_col = metric.get('matched_column', metric_name)
                
                if est_col in estimated_df.columns and act_col in actual_df.columns:
                    # Line comparison chart for each metric
                    metric_chart_data = []
                    
                    # Get raw data and convert to numeric
                    est_raw = estimated_df[est_col].copy()
                    act_raw = actual_df[act_col].copy()
                    
                    # Convert to numeric and handle errors
                    est_data = pd.to_numeric(est_raw, errors='coerce')
                    act_data = pd.to_numeric(act_raw, errors='coerce')
                    
                    # Remove NaN values but keep indices aligned
                    # Ensure we have Series for proper boolean operations
                    est_series = pd.Series(est_data) if not isinstance(est_data, pd.Series) else est_data
                    act_series = pd.Series(act_data) if not isinstance(act_data, pd.Series) else act_data
                    
                    # Create boolean mask using pandas operations
                    valid_indices = ~(pd.isna(est_series) | pd.isna(act_series))
                    est_clean = est_series[valid_indices]
                    act_clean = act_series[valid_indices]
                    
                    # Ensure we have meaningful data
                    if len(est_clean) > 0 and len(act_clean) > 0:
                        # Sample data points for visualization (max 100 points)
                        sample_size = min(len(est_clean), 100)
                        if len(est_clean) > sample_size:
                            # Sample evenly across the dataset
                            indices = np.linspace(0, len(est_clean) - 1, sample_size, dtype=int)
                            # Ensure we have Series objects for iloc access
                            est_series = pd.Series(est_clean) if not isinstance(est_clean, pd.Series) else est_clean
                            act_series = pd.Series(act_clean) if not isinstance(act_clean, pd.Series) else act_clean
                            
                            est_sampled = est_series.iloc[indices]
                            act_sampled = act_series.iloc[indices]
                        else:
                            est_sampled = est_clean
                            act_sampled = act_clean
                        
                        # Create chart data with proper validation
                        for i, (est_val, act_val) in enumerate(zip(est_sampled, act_sampled)):
                            if not (pd.isna(est_val) or pd.isna(act_val)):
                                metric_chart_data.append({
                                    'period': f'Period {i + 1}',  # Frontend expects 'period' key
                                    'index': i + 1,
                                    'estimated': float(est_val),
                                    'actual': float(act_val),
                                    'estimated_trend': float(est_val),  # Frontend expects 'estimated_trend'
                                    'actual_trend': float(act_val),     # Frontend expects 'actual_trend'
                                    'variance': float(act_val - est_val)
                                })
                        
                        # Only add chart if we have valid data points
                        if len(metric_chart_data) >= 3:  # Minimum 3 points for meaningful chart
                            # Validate that we have actual numeric data
                            has_valid_data = any(
                                isinstance(point.get('estimated'), (int, float)) and 
                                isinstance(point.get('actual'), (int, float)) and
                                not (pd.isna(point.get('estimated')) or pd.isna(point.get('actual')))
                                for point in metric_chart_data
                            )
                            
                            if has_valid_data:
                                # Select color scheme based on performance
                                variance_pct = abs(metric.get('variance_percentage', 0))
                                if variance_pct > 25:
                                    scheme = color_schemes['red']
                                elif variance_pct > 15:
                                    scheme = color_schemes['orange']
                                else:
                                    scheme = color_schemes['green']
                                
                                charts.append({
                                    'type': 'line',
                                    'title': f'{metric_name} - Estimated vs Actual Trend',
                                    'subtitle': f'Variance: {metric.get("variance_percentage", 0):.1f}% | Correlation: {metric.get("trend_correlation", 0):.2f} | Points: {len(metric_chart_data)}',
                                    'description': f'Time-series comparison showing how {metric_name} estimates tracked against actual values. Line separation indicates forecast accuracy.',
                                    'data': metric_chart_data,
                                    'config': {
                                        'xAxisKey': 'period',  # Frontend expects 'period'
                                        'lines': [
                                            {
                                                'dataKey': 'estimated_trend', 
                                                'name': 'Estimated', 
                                                'stroke': color_schemes['blue']['primary'],
                                                'strokeWidth': 3,
                                                'dot': {'fill': color_schemes['blue']['secondary'], 'r': 5},
                                                'activeDot': {'r': 8, 'fill': color_schemes['blue']['primary']},
                                                'strokeDasharray': ''
                                            },
                                            {
                                                'dataKey': 'actual_trend', 
                                                'name': 'Actual', 
                                                'stroke': scheme['primary'],
                                                'strokeWidth': 3,
                                                'dot': {'fill': scheme['secondary'], 'r': 5},
                                                'activeDot': {'r': 8, 'fill': scheme['primary']},
                                                'strokeDasharray': ''
                                            }
                                        ],
                                        'legend': {
                                            'show': True,
                                            'position': 'top',
                                            'align': 'center',
                                            'iconType': 'line',
                                            'formatter': '{name}',
                                            'wrapperStyle': {'paddingTop': '10px'}
                                        },
                                        'tooltip': {
                                            'formatter': '${name}: {value:,.0f}',
                                            'contentStyle': {
                                                'backgroundColor': 'rgba(0, 0, 0, 0.8)',
                                                'border': 'none',
                                                'borderRadius': '8px',
                                                'color': '#fff'
                                            }
                                        },
                                        'grid': {
                                            'strokeDasharray': '3 3',
                                            'stroke': '#e5e7eb'
                                        },
                                        'animation': {
                                            'duration': 1000,
                                            'easing': 'easeInOutQuad'
                                        },
                                        'area': {
                                            'estimated_trend': {
                                                'fill': color_schemes['blue']['tertiary'],
                                                'fillOpacity': 0.1
                                            },
                                            'actual_trend': {
                                                'fill': scheme['tertiary'],
                                                'fillOpacity': 0.1
                                            }
                                        }
                                    },
                                    'chart_rationale': f'Shows point-by-point comparison for {metric_name} to identify specific periods of divergence'
                                })
                                valid_charts_created += 1
                                logger.info(f"[ENHANCED_CHARTS] Created line chart #{valid_charts_created} for {metric_name} ({len(metric_chart_data)} data points)")
                            else:
                                logger.warning(f"[ENHANCED_CHARTS] Skipping line chart for {metric_name} - no valid numeric data")
                    
                    # Bar chart for metric totals comparison with validation
                    estimated_total = metric.get('estimated_total', 0)
                    actual_total = metric.get('actual_total', 0)
                    
                    # Ensure we have meaningful totals (not just zeros)
                    if abs(estimated_total) > 0.01 or abs(actual_total) > 0.01:
                        # Validate that totals are finite numbers
                        if (isinstance(estimated_total, (int, float)) and not pd.isna(estimated_total) and 
                            isinstance(actual_total, (int, float)) and not pd.isna(actual_total)):
                            
                            # Calculate performance for color coding
                            accuracy_score = metric.get('accuracy_score', 0)
                            performance_color = color_schemes['green']['primary'] if accuracy_score > 85 else color_schemes['orange']['primary'] if accuracy_score > 70 else color_schemes['red']['primary']
                            
                            bar_data = [
                                {
                                    'metric': f'{metric_name} Comparison',
                                    'estimated': float(estimated_total),
                                    'actual': float(actual_total),
                                    'variance': abs(float(estimated_total - actual_total)) if estimated_total != 0 else 0
                                }
                            ]
                            
                            charts.append({
                                'type': 'bar',
                                'title': f'{metric_name} - Total Values Comparison',
                                'subtitle': f'Accuracy Score: {metric.get("accuracy_score", 0):.1f}% | Est: {estimated_total:,.0f} | Act: {actual_total:,.0f}',
                                'description': f'Aggregate comparison showing total estimated vs actual values for {metric_name}. Variance bar shows absolute difference.',
                                'data': bar_data,
                                'config': {
                                    'xAxisKey': 'metric',
                                    'bars': [
                                        {
                                            'dataKey': 'estimated', 
                                            'name': 'Estimated', 
                                            'fill': color_schemes['blue']['gradient'][0],
                                            'radius': [8, 8, 0, 0]
                                        },
                                        {
                                            'dataKey': 'actual', 
                                            'name': 'Actual', 
                                            'fill': performance_color,
                                            'radius': [8, 8, 0, 0]
                                        },
                                        {
                                            'dataKey': 'variance', 
                                            'name': 'Variance', 
                                            'fill': color_schemes['red']['gradient'][1],
                                            'radius': [8, 8, 0, 0]
                                        }
                                    ],
                                    'legend': {
                                        'show': True,
                                        'position': 'bottom',
                                        'align': 'center',
                                        'iconType': 'rect',
                                        'formatter': '{name}',
                                        'wrapperStyle': {'paddingTop': '15px'}
                                    },
                                    'tooltip': {
                                        'formatter': '{name}: {value:,.0f}',
                                        'contentStyle': {
                                            'backgroundColor': 'rgba(0, 0, 0, 0.8)',
                                            'border': 'none',
                                            'borderRadius': '8px',
                                            'color': '#fff'
                                        }
                                    },
                                    'animation': {
                                        'duration': 800,
                                        'easing': 'easeOutBack'
                                    },
                                    'barCategoryGap': '20%'
                                },
                                'chart_rationale': f'Compares total {metric_name} values to understand overall magnitude differences'
                            })
                            valid_charts_created += 1
                            logger.info(f"[ENHANCED_CHARTS] Created bar chart #{valid_charts_created} for {metric_name} totals")
                        else:
                            logger.warning(f"[ENHANCED_CHARTS] Skipping bar chart for {metric_name} - invalid total values: est={estimated_total}, act={actual_total}")
            
            # 2. Variance Overview Chart - Enhanced with better filtering
            variance_overview_data = []
            if individual_metrics:
                for metric in individual_metrics:
                    variance_val = metric.get('variance_percentage', 0)
                    # Include all metrics, even with zero variance for complete picture
                    variance_overview_data.append({
                        'metric': metric.get('metric_name', 'Unknown')[:15],  # Truncate long names
                        'variance': abs(float(variance_val)),  # Frontend expects 'variance' key
                        'variance_percentage': abs(float(variance_val)),
                        'severity': metric.get('deviation_severity', 'minor'),
                        'business_impact': metric.get('business_impact', 'low'),
                        'accuracy_score': metric.get('accuracy_score', 0)
                    })
                
                if variance_overview_data:
                    # Sort by variance for better visualization
                    variance_overview_data.sort(key=lambda x: x['variance_percentage'], reverse=True)
                    
                    # Add color coding based on variance severity
                    for item in variance_overview_data:
                        variance_val = item['variance_percentage']
                        if variance_val > 25:
                            item['fill'] = color_schemes['red']['gradient'][0]
                        elif variance_val > 15:
                            item['fill'] = color_schemes['orange']['gradient'][0]
                        elif variance_val > 8:
                            item['fill'] = color_schemes['orange']['gradient'][2]
                        else:
                            item['fill'] = color_schemes['green']['gradient'][0]
                    
                    charts.append({
                        'type': 'bar',
                        'title': 'Variance Overview - All Metrics',
                        'subtitle': f'Variance percentage by metric ({len(variance_overview_data)} metrics analyzed)',
                        'description': 'Comprehensive variance analysis across all metrics. Color coding indicates severity: Red (>25%), Orange (15-25%), Light Orange (8-15%), Green (<8%).',
                        'data': variance_overview_data,
                        'config': {
                            'xAxisKey': 'metric',
                            'bars': [{
                                'dataKey': 'variance', 
                                'name': 'Variance %',
                                'fill': '#ef4444',  # Default fill
                                'radius': [4, 4, 0, 0]
                            }],
                            'legend': {
                                'show': True,
                                'position': 'top-right',
                                'align': 'right',
                                'iconType': 'rect',
                                'formatter': '{name}',
                                'data': [
                                    {'value': '>25%', 'type': 'rect', 'color': color_schemes['red']['gradient'][0]},
                                    {'value': '15-25%', 'type': 'rect', 'color': color_schemes['orange']['gradient'][0]},
                                    {'value': '8-15%', 'type': 'rect', 'color': color_schemes['orange']['gradient'][2]},
                                    {'value': '<8%', 'type': 'rect', 'color': color_schemes['green']['gradient'][0]}
                                ]
                            },
                            'tooltip': {
                                'formatter': '{name}: {value:.1f}%',
                                'contentStyle': {
                                    'backgroundColor': 'rgba(0, 0, 0, 0.8)',
                                    'border': 'none',
                                    'borderRadius': '8px',
                                    'color': '#fff'
                                }
                            },
                            'animation': {
                                'duration': 1200,
                                'easing': 'easeOutQuart',
                                'animationBegin': 0,
                                'animationDuration': 1200
                            },
                            'grid': {
                                'containLabel': True,
                                'left': '3%',
                                'right': '3%'
                            },
                            'xAxis': {
                                'axisLabel': {
                                    'rotate': 45,
                                    'interval': 0
                                }
                            }
                        },
                        'chart_rationale': 'Provides holistic view of all metric variances for quick identification of problematic areas'
                    })
            
            # 3. Accuracy vs Variance Scatter Plot - More meaningful analysis
            accuracy_variance_data = []
            if individual_metrics:
                for metric in individual_metrics:
                    accuracy = metric.get('accuracy_score', 0)
                    variance = abs(metric.get('variance_percentage', 0))
                    correlation = metric.get('trend_correlation', 0)
                    
                    accuracy_variance_data.append({
                        'metric': metric.get('metric_name', 'Unknown')[:15],
                        'x': float(variance),  # Frontend expects 'x' key
                        'y': float(accuracy),  # Frontend expects 'y' key
                        'value': float(accuracy),  # Frontend expects 'value' key for scatter points
                        'accuracy': float(accuracy),
                        'variance': float(variance),
                        'correlation': float(correlation * 100),  # Convert to percentage
                        'category': 'Excellent' if accuracy > 90 else 'Good' if accuracy > 75 else 'Fair' if accuracy > 60 else 'Poor'
                    })
                
                if accuracy_variance_data:
                    # Add color coding based on performance quadrant
                    for item in accuracy_variance_data:
                        if item['accuracy'] > 85 and item['variance'] < 10:
                            item['fill'] = color_schemes['green']['gradient'][0]
                            item['size'] = 100
                        elif item['accuracy'] > 70 and item['variance'] < 20:
                            item['fill'] = color_schemes['blue']['gradient'][0]
                            item['size'] = 80
                        elif item['accuracy'] > 50:
                            item['fill'] = color_schemes['orange']['gradient'][0]
                            item['size'] = 70
                        else:
                            item['fill'] = color_schemes['red']['gradient'][0]
                            item['size'] = 90
                    
                    charts.append({
                        'type': 'scatter',
                        'title': 'Accuracy vs Variance Analysis',
                        'subtitle': 'Accuracy Score (%) vs Variance (%) - Upper left quadrant is ideal',
                        'description': 'Scatter plot showing the relationship between forecast accuracy and variance. Ideal metrics appear in the upper-left quadrant (high accuracy, low variance).',
                        'data': accuracy_variance_data,
                        'config': {
                            'xAxisKey': 'x',  # Frontend expects 'x'
                            'yAxisKey': 'y',  # Frontend expects 'y'
                            'scatter': {'fill': '#8b5cf6'},
                            'legend': {
                                'show': True,
                                'position': 'right',
                                'align': 'middle',
                                'data': [
                                    {'value': 'Excellent (>85% acc, <10% var)', 'type': 'circle', 'color': color_schemes['green']['gradient'][0]},
                                    {'value': 'Good (>70% acc, <20% var)', 'type': 'circle', 'color': color_schemes['blue']['gradient'][0]},
                                    {'value': 'Fair (>50% acc)', 'type': 'circle', 'color': color_schemes['orange']['gradient'][0]},
                                    {'value': 'Poor (<50% acc)', 'type': 'circle', 'color': color_schemes['red']['gradient'][0]}
                                ]
                            },
                            'tooltip': {
                                'formatter': '{metric}\nAccuracy: {accuracy:.1f}%\nVariance: {variance:.1f}%',
                                'contentStyle': {
                                    'backgroundColor': 'rgba(0, 0, 0, 0.8)',
                                    'border': 'none',
                                    'borderRadius': '8px',
                                    'color': '#fff'
                                }
                            },
                            'grid': {
                                'strokeDasharray': '3 3',
                                'stroke': '#e5e7eb'
                            },
                            'xAxis': {
                                'name': 'Variance (%)',
                                'nameLocation': 'middle',
                                'nameGap': 30
                            },
                            'yAxis': {
                                'name': 'Accuracy (%)',
                                'nameLocation': 'middle',
                                'nameGap': 40
                            },
                            'referenceLines': [
                                {
                                    'x': 10,
                                    'stroke': color_schemes['green']['gradient'][2],
                                    'strokeDasharray': '5 5',
                                    'label': 'Target Variance'
                                },
                                {
                                    'y': 85,
                                    'stroke': color_schemes['green']['gradient'][2],
                                    'strokeDasharray': '5 5',
                                    'label': 'Target Accuracy'
                                }
                            ]
                        },
                        'chart_rationale': 'Identifies metrics with high accuracy and low variance (ideal quadrant) vs problematic metrics'
                    })
            
            # 4. Business Impact Priority Chart - Enhanced
            impact_priority_data = []
            if individual_metrics:
                severity_counts = {}
                for severity in ['critical', 'significant', 'moderate', 'minor']:
                    count = sum(1 for m in individual_metrics if m.get('deviation_severity') == severity)
                    severity_counts[severity] = count  # Include zeros for complete picture
                
                # Create chart data with colors
                color_map = {
                    'Critical': '#dc2626',
                    'Significant': '#ea580c', 
                    'Moderate': '#d97706',
                    'Minor': '#65a30d'
                }
                
                total_metrics = len(individual_metrics)
                for severity, count in severity_counts.items():
                    if total_metrics > 0:  # Avoid division by zero
                        impact_priority_data.append({
                            'name': severity.title(),  # Frontend expects 'name' key
                            'value': count,  # Frontend expects 'value' key
                            'count': count,
                            'percentage': (count / total_metrics) * 100,
                            'fill': color_map.get(severity.title(), '#6b7280')
                        })
                
                if impact_priority_data and total_metrics > 0:
                    charts.append({
                        'type': 'pie',
                        'title': 'Deviation Severity Distribution',
                        'subtitle': f'Distribution across {total_metrics} analyzed metrics',
                        'description': 'Shows the breakdown of metrics by deviation severity. Critical issues require immediate attention, while minor issues can be monitored.',
                        'data': impact_priority_data,
                        'config': {
                            'dataKey': 'value',
                            'nameKey': 'name',
                            'colors': [item['fill'] for item in impact_priority_data],
                            'innerRadius': '30%',  # Donut chart
                            'outerRadius': '80%',
                            'padAngle': 2,  # Space between segments
                            'cornerRadius': 4,  # Rounded corners
                            'legend': {
                                'show': True,
                                'position': 'right',
                                'align': 'middle',
                                'formatter': '{name}: {value} ({percentage:.1f}%)',
                                'icon': 'circle'
                            },
                            'tooltip': {
                                'formatter': '{name}: {value} metrics ({percentage:.1f}%)',
                                'contentStyle': {
                                    'backgroundColor': 'rgba(0, 0, 0, 0.8)',
                                    'border': 'none',
                                    'borderRadius': '8px',
                                    'color': '#fff'
                                }
                            },
                            'animation': {
                                'duration': 1500,
                                'easing': 'easeOutElastic'
                            },
                            'label': {
                                'show': True,
                                'position': 'outside',
                                'formatter': '{percentage:.0f}%'
                            }
                        },
                        'chart_rationale': 'Shows the distribution of deviation severity to understand overall forecast health'
                    })
            
            # 5. FIXED: Trend Correlation Analysis - Enhanced with better data validation
            correlation_analysis_data = []
            if individual_metrics:
                for metric in individual_metrics:
                    correlation = metric.get('trend_correlation', 0)
                    metric_name = metric.get('metric_name', 'Unknown')[:15]
                    
                    # FIXED: Only include metrics with valid correlation data
                    if correlation is not None and not pd.isna(correlation) and isinstance(correlation, (int, float)):
                        correlation_analysis_data.append({
                            'metric': metric_name,
                            'correlation': float(correlation * 100),  # Frontend expects 'correlation' key
                            'correlation_percentage': float(correlation * 100),
                            'correlation_strength': 'Very Strong' if correlation > 0.8 else 'Strong' if correlation > 0.6 else 'Moderate' if correlation > 0.4 else 'Weak' if correlation > 0.2 else 'Very Weak',
                            'color': '#10b981' if correlation > 0.7 else '#f59e0b' if correlation > 0.4 else '#ef4444',
                            'variance': abs(metric.get('variance_percentage', 0)),  # Add variance for context
                            'accuracy': metric.get('accuracy_score', 0)  # Add accuracy for context
                        })
                
                # FIXED: Only create chart if we have meaningful correlation data
                if correlation_analysis_data and len(correlation_analysis_data) > 0:
                    # Sort by correlation for better visualization
                    correlation_analysis_data.sort(key=lambda x: x['correlation_percentage'], reverse=True)
                    
                    # Add gradient colors based on correlation strength
                    for idx, item in enumerate(correlation_analysis_data):
                        correlation = item['correlation_percentage']
                        if correlation > 80:
                            item['barFill'] = color_schemes['green']['gradient'][idx % 4]
                        elif correlation > 60:
                            item['barFill'] = color_schemes['blue']['gradient'][idx % 4]
                        elif correlation > 40:
                            item['barFill'] = color_schemes['orange']['gradient'][idx % 4]
                        else:
                            item['barFill'] = color_schemes['red']['gradient'][idx % 4]
                    
                    charts.append({
                        'type': 'bar',
                        'title': 'Trend Correlation Analysis',
                        'subtitle': f'How well estimated trends match actual trends ({len(correlation_analysis_data)} metrics with correlation data)',
                        'description': 'Measures how closely estimated patterns follow actual patterns. Higher correlation indicates better trend prediction. Values above 80% show strong alignment.',
                        'data': correlation_analysis_data,
                        'config': {
                            'xAxisKey': 'metric',
                            'bars': [{
                                'dataKey': 'correlation', 
                                'name': 'Correlation %',
                                'fill': '#3b82f6',  # Default
                                'radius': [4, 4, 0, 0]
                            }],
                            'legend': {
                                'show': True,
                                'position': 'top',
                                'align': 'center',
                                'data': [
                                    {'value': 'Very Strong (>80%)', 'type': 'rect', 'color': color_schemes['green']['primary']},
                                    {'value': 'Strong (60-80%)', 'type': 'rect', 'color': color_schemes['blue']['primary']},
                                    {'value': 'Moderate (40-60%)', 'type': 'rect', 'color': color_schemes['orange']['primary']},
                                    {'value': 'Weak (<40%)', 'type': 'rect', 'color': color_schemes['red']['primary']}
                                ]
                            },
                            'tooltip': {
                                'formatter': '{name}: {value:.1f}%\nVariance: {variance:.1f}%\nAccuracy: {accuracy:.1f}%',
                                'contentStyle': {
                                    'backgroundColor': 'rgba(0, 0, 0, 0.8)',
                                    'border': 'none',
                                    'borderRadius': '8px',
                                    'color': '#fff'
                                }
                            },
                            'grid': {
                                'containLabel': True,
                                'left': '3%',
                                'right': '3%'
                            },
                            'xAxis': {
                                'axisLabel': {
                                    'rotate': 45,
                                    'interval': 0
                                }
                            },
                            'yAxis': {
                                'max': 100,
                                'min': 0
                            },
                            'animation': {
                                'duration': 1000,
                                'easing': 'easeOutQuint'
                            },
                            'referenceLines': [
                                {
                                    'y': 80,
                                    'stroke': color_schemes['green']['gradient'][2],
                                    'strokeDasharray': '5 5',
                                    'label': 'Strong Correlation'
                                },
                                {
                                    'y': 60,
                                    'stroke': color_schemes['orange']['gradient'][2], 
                                    'strokeDasharray': '5 5',
                                    'label': 'Moderate Correlation'
                                }
                            ]
                        },
                        'chart_rationale': 'Shows which metrics have strong trend alignment vs those that need forecasting model improvements'
                    })
                    logger.info(f"[ENHANCED_CHARTS] Created trend correlation chart with {len(correlation_analysis_data)} metrics")
                else:
                    logger.warning("[ENHANCED_CHARTS] No valid correlation data found for trend correlation chart")
            
            # 6. Category Performance Analysis (if available) - Enhanced
            if granular_insights.get('insights_by_category'):
                category_performance_data = []
                for category_name, category_data in granular_insights['insights_by_category'].items():
                    if 'category_performance' in category_data:
                        for cat_name, cat_perf in category_data['category_performance'].items():
                            avg_variance = cat_perf.get('average_variance', 0)
                            data_points = cat_perf.get('data_points', 0)
                            
                            # Include categories with meaningful data
                            if data_points > 0:  # At least some data points
                                category_performance_data.append({
                                    'category_type': category_name,
                                    'category_value': str(cat_name)[:20],  # Truncate long names
                                    'avg_variance': abs(float(avg_variance)),
                                    'data_points': int(data_points),
                                    'performance_grade': 'Excellent' if abs(avg_variance) < 5 else 'Good' if abs(avg_variance) < 15 else 'Fair' if abs(avg_variance) < 30 else 'Poor'
                                })
                
                if category_performance_data:
                    # Sort by variance for better visualization
                    category_performance_data.sort(key=lambda x: x['avg_variance'], reverse=True)
                    
                    # Add performance-based coloring to categories
                    for item in category_performance_data[:10]:
                        variance = item['avg_variance']
                        if variance < 5:
                            item['fill'] = color_schemes['green']['gradient'][0]
                        elif variance < 15:
                            item['fill'] = color_schemes['blue']['gradient'][0]
                        elif variance < 30:
                            item['fill'] = color_schemes['orange']['gradient'][0]
                        else:
                            item['fill'] = color_schemes['red']['gradient'][0]
                    
                    charts.append({
                        'type': 'bar',
                        'title': 'Category-wise Performance Analysis',
                        'subtitle': f'Average variance by category segments (Top {min(len(category_performance_data), 10)} categories)',
                        'description': 'Breaks down forecast accuracy by category or segment. Helps identify which categories need model improvements or have systematic forecasting challenges.',
                        'data': category_performance_data[:10],  # Limit to top 10
                        'config': {
                            'xAxisKey': 'category_value',
                            'bars': [{
                                'dataKey': 'avg_variance', 
                                'name': 'Avg Variance %',
                                'fill': '#f59e0b',  # Default
                                'radius': [8, 8, 0, 0]
                            }],
                            'legend': {
                                'show': True,
                                'position': 'top',
                                'align': 'right',
                                'data': [
                                    {'value': 'Excellent (<5%)', 'type': 'rect', 'color': color_schemes['green']['gradient'][0]},
                                    {'value': 'Good (5-15%)', 'type': 'rect', 'color': color_schemes['blue']['gradient'][0]},
                                    {'value': 'Fair (15-30%)', 'type': 'rect', 'color': color_schemes['orange']['gradient'][0]},
                                    {'value': 'Poor (>30%)', 'type': 'rect', 'color': color_schemes['red']['gradient'][0]}
                                ]
                            },
                            'tooltip': {
                                'formatter': '{category_value}\nAvg Variance: {avg_variance:.1f}%\nData Points: {data_points}',
                                'contentStyle': {
                                    'backgroundColor': 'rgba(0, 0, 0, 0.8)',
                                    'border': 'none',
                                    'borderRadius': '8px',
                                    'color': '#fff'
                                }
                            },
                            'grid': {
                                'containLabel': True,
                                'left': '3%',
                                'right': '3%',
                                'bottom': '15%'
                            },
                            'xAxis': {
                                'axisLabel': {
                                    'rotate': 45,
                                    'interval': 0
                                }
                            },
                            'animation': {
                                'duration': 1200,
                                'easing': 'easeOutBack'
                            },
                            'layout': 'horizontal'  # Consider horizontal layout for long category names
                        },
                        'chart_rationale': 'Identifies which categories/segments have the highest forecasting challenges'
                    })
            
            # Final validation: Remove any charts with empty or invalid data
            valid_charts = []
            for chart in charts:
                data = chart.get('data', [])
                if data and len(data) > 0:
                    # Check if data contains valid values
                    has_valid_values = False
                    for item in data:
                        if isinstance(item, dict):
                            # Check for numeric values in the data
                            for key, value in item.items():
                                if isinstance(value, (int, float)) and not pd.isna(value):
                                    if abs(value) > 0.001:  # Not essentially zero
                                        has_valid_values = True
                                        break
                        if has_valid_values:
                            break
                    
                    if has_valid_values:
                        valid_charts.append(chart)
                    else:
                        logger.warning(f"[ENHANCED_CHARTS] Removing chart '{chart.get('title', 'untitled')}' - no valid numeric data")
                else:
                    logger.warning(f"[ENHANCED_CHARTS] Removing chart '{chart.get('title', 'untitled')}' - empty data array")
            
            # If no valid charts, create a simple summary chart
            if not valid_charts and individual_metrics:
                logger.info("[ENHANCED_CHARTS] Creating fallback summary chart")
                summary_data = []
                for i, metric in enumerate(individual_metrics[:5]):  # Top 5 metrics
                    metric_name = metric.get('metric_name', f'Metric {i+1}')[:15]  # Truncate name
                    variance = abs(metric.get('variance_percentage', 0))
                    if variance > 0:
                        summary_data.append({
                            'metric': metric_name,
                            'variance': float(variance),
                            'status': 'High' if variance > 20 else 'Medium' if variance > 10 else 'Low'
                        })
                
                if summary_data:
                    # Add color coding to summary data
                    for item in summary_data:
                        if item['status'] == 'High':
                            item['fill'] = color_schemes['red']['gradient'][0]
                        elif item['status'] == 'Medium':
                            item['fill'] = color_schemes['orange']['gradient'][0]
                        else:
                            item['fill'] = color_schemes['green']['gradient'][0]
                    
                    valid_charts.append({
                        'type': 'bar',
                        'title': 'Variance Summary by Metric',
                        'subtitle': f'Top {len(summary_data)} metrics with variance analysis',
                        'description': 'Summary view of variance levels across key metrics. Color coding helps quickly identify which metrics need attention.',
                        'data': summary_data,
                        'config': {
                            'xAxisKey': 'metric',
                            'bars': [{
                                'dataKey': 'variance', 
                                'name': 'Variance %',
                                'fill': '#6366f1',  # Default
                                'radius': [4, 4, 0, 0]
                            }],
                            'legend': {
                                'show': True,
                                'position': 'top',
                                'align': 'center',
                                'data': [
                                    {'value': 'High (>20%)', 'type': 'rect', 'color': color_schemes['red']['gradient'][0]},
                                    {'value': 'Medium (10-20%)', 'type': 'rect', 'color': color_schemes['orange']['gradient'][0]},
                                    {'value': 'Low (<10%)', 'type': 'rect', 'color': color_schemes['green']['gradient'][0]}
                                ]
                            },
                            'tooltip': {
                                'formatter': '{name}: {value:.1f}%\nStatus: {status}',
                                'contentStyle': {
                                    'backgroundColor': 'rgba(0, 0, 0, 0.8)',
                                    'border': 'none',
                                    'borderRadius': '8px',
                                    'color': '#fff'
                                }
                            },
                            'grid': {
                                'containLabel': True,
                                'strokeDasharray': '3 3',
                                'stroke': '#e5e7eb'
                            },
                            'animation': {
                                'duration': 1000,
                                'easing': 'easeOutCubic'
                            }
                        }
                    })
            
            # **TRANSPARENCY**: Enhanced chart generation summary
            total_charts = len(valid_charts)
            logger.info(f"[ENHANCED_CHARTS] Chart generation complete:")
            logger.info(f"[ENHANCED_CHARTS] - Total valid charts created: {total_charts}")
            logger.info(f"[ENHANCED_CHARTS] - Individual metric charts: {valid_charts_created}")
            logger.info(f"[ENHANCED_CHARTS] - Overview/summary charts: {total_charts - valid_charts_created}")
            logger.info(f"[ENHANCED_CHARTS] - Metrics analyzed: {len(individual_metrics)}")
            logger.info(f"[ENHANCED_CHARTS] - Charts filtered out: {len(charts) - len(valid_charts)}")
            
            # Log chart details for transparency
            for i, chart in enumerate(valid_charts):
                data_points = len(chart.get('data', []))
                chart_type = chart.get('type', 'unknown')
                title = chart.get('title', 'untitled')
                logger.info(f"[ENHANCED_CHARTS] Chart {i+1}: {chart_type} - '{title[:50]}...' - {data_points} data points")
            
            return valid_charts
            
        except Exception as e:
            logger.error(f"[ENHANCED_CHARTS] Error creating enhanced charts: {str(e)}")
            return []

    async def _generate_comprehensive_kpis_deep(
        self,
        individual_metrics: List[Dict[str, Any]],
        variance_analysis: Dict[str, Any],
        trend_deviation_analysis: Dict[str, Any],
        missing_metrics: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """NEW: Generate comprehensive KPIs based on deep analysis results."""
        logger.info("[COMPREHENSIVE_KPIS] Starting comprehensive KPIs generation")
        
        try:
            kpis = []
            
            # Extract data from individual metrics
            accuracy_scores = [m.get('accuracy_score', 0) for m in individual_metrics if m.get('accuracy_score') is not None]
            variances = [abs(m.get('variance_percentage', 0)) for m in individual_metrics if m.get('variance_percentage') is not None]
            correlations = [m.get('trend_correlation', 0) for m in individual_metrics if m.get('trend_correlation') is not None and not np.isnan(m.get('trend_correlation', 0))]
            
            # 1. Overall Forecast Accuracy
            overall_accuracy = np.mean(accuracy_scores) if accuracy_scores else 0
            kpis.append({
                'title': 'Overall Forecast Accuracy',
                'value': f'{overall_accuracy:.1f}%',
                'trend': 'up' if overall_accuracy > 80 else 'down',
                'color': '#10b981' if overall_accuracy > 85 else '#f59e0b' if overall_accuracy > 70 else '#ef4444',
                'textColor': '#ffffff',
                'description': f'Average accuracy across {len(accuracy_scores)} analyzed metrics'
            })
            
            # 2. Average Absolute Variance
            avg_variance = np.mean(variances) if variances else 0
            kpis.append({
                'title': 'Average Absolute Variance',
                'value': f'{avg_variance:.1f}%',
                'trend': 'down' if avg_variance < 10 else 'up',
                'color': '#10b981' if avg_variance < 8 else '#f59e0b' if avg_variance < 15 else '#ef4444',
                'textColor': '#ffffff',
                'description': f'Mean absolute deviation across {len(variances)} metrics'
            })
            
            # 3. FIXED: Trend Alignment Score - Only show real data
            if correlations and len(correlations) > 0:
                avg_correlation = np.mean(correlations)
                trend_score = avg_correlation * 100
                kpis.append({
                    'title': 'Trend Alignment Score',
                    'value': f'{trend_score:.1f}%',
                    'trend': 'up' if trend_score > 75 else 'down',
                    'color': '#10b981' if trend_score > 80 else '#f59e0b' if trend_score > 60 else '#ef4444',
                    'textColor': '#ffffff',
                    'description': f'Average correlation strength across {len(correlations)} trends'
                })
            else:
                # No trend analysis possible - show N/A
                kpis.append({
                    'title': 'Trend Alignment Score',
                    'value': 'N/A',
                    'trend': 'neutral',
                    'color': '#6b7280',
                    'textColor': '#ffffff',
                    'description': 'Not Available - Insufficient trend data for analysis'
                })
            
            # 4. Critical Issues Count
            critical_count = sum(1 for m in individual_metrics if m.get('deviation_severity') == 'critical')
            kpis.append({
                'title': 'Critical Issues',
                'value': str(critical_count),
                'trend': 'down' if critical_count == 0 else 'up',
                'color': '#10b981' if critical_count == 0 else '#f59e0b' if critical_count < 3 else '#ef4444',
                'textColor': '#ffffff',
                'description': f'Metrics requiring immediate attention'
            })
            
            # 5. Data Alignment Quality - FIXED CALCULATION
            # Use the actual column mapping to calculate alignment quality
            mapped_cols = len(individual_metrics)  # This represents successfully mapped AND analyzed columns
            est_cols = variance_analysis.get('estimated_columns_count', mapped_cols)  # Total estimated columns
            act_cols = variance_analysis.get('actual_columns_count', mapped_cols)     # Total actual columns
            
            # Alignment quality based on successful column mapping
            if est_cols > 0 and act_cols > 0:
                # Calculate based on the smaller dataset (more conservative)
                total_possible_mappings = min(est_cols, act_cols)
                alignment_quality = (mapped_cols / total_possible_mappings * 100) if total_possible_mappings > 0 else 0
            else:
                alignment_quality = 100 if mapped_cols > 0 else 0
            
            kpis.append({
                'title': 'Data Alignment Quality',
                'value': f'{alignment_quality:.1f}%',
                'trend': 'up' if alignment_quality > 80 else 'down',
                'color': '#10b981' if alignment_quality > 90 else '#f59e0b' if alignment_quality > 70 else '#ef4444',
                'textColor': '#ffffff',
                'description': f'{mapped_cols}/{min(est_cols, act_cols)} columns successfully aligned and analyzed'
            })
            
            # 6. Missing Metrics Alert
            missing_count = missing_metrics.get('total_missing_count', 0)
            high_impact_missing = missing_metrics.get('summary', {}).get('high_impact_count', 0)
            
            kpis.append({
                'title': 'Missing Metrics',
                'value': f'{missing_count} ({high_impact_missing} critical)',
                'trend': 'down' if missing_count == 0 else 'up',
                'color': '#10b981' if missing_count == 0 else '#f59e0b' if high_impact_missing == 0 else '#ef4444',
                'textColor': '#ffffff',
                'description': 'Metrics present in one dataset but not the other'
            })
            
            # 7. Forecast Health Score (Composite) - REALISTIC CALCULATION
            if individual_metrics:
                # Composite score based on actual data analysis
                health_components = []
                if accuracy_scores:
                    health_components.append(np.mean(accuracy_scores))
                if variances:
                    health_components.append(max(0.0, 100.0 - float(np.mean(variances))))  # Invert variance
                if correlations:
                    health_components.append(np.mean(correlations) * 100)
                
                health_score = np.mean(health_components) if health_components else 0
                
                kpis.append({
                    'title': 'Forecast Health Score',
                    'value': f'{health_score:.1f}%',
                    'trend': 'up' if health_score > 70 else 'down',
                    'color': '#10b981' if health_score > 80 else '#f59e0b' if health_score > 60 else '#ef4444',
                    'textColor': '#ffffff',
                    'description': 'Composite score based on accuracy, variance, and trend alignment'
                })
            
            # 8. Column-wise Accuracy Distribution
            if individual_metrics:
                high_accuracy_count = sum(1 for m in individual_metrics if m.get('accuracy_score', 0) > 80)
                medium_accuracy_count = sum(1 for m in individual_metrics if 60 <= m.get('accuracy_score', 0) <= 80)
                low_accuracy_count = len(individual_metrics) - high_accuracy_count - medium_accuracy_count
                
                kpis.append({
                    'title': 'High Accuracy Metrics',
                    'value': f'{high_accuracy_count}/{len(individual_metrics)}',
                    'trend': 'up' if high_accuracy_count > len(individual_metrics) / 2 else 'down',
                    'color': '#10b981' if high_accuracy_count > len(individual_metrics) * 0.7 else '#f59e0b',
                    'textColor': '#ffffff',
                    'description': f'Metrics with >80% accuracy (Medium: {medium_accuracy_count}, Low: {low_accuracy_count})'
                })
            
            logger.info(f"[COMPREHENSIVE_KPIS] Generated {len(kpis)} comprehensive KPIs")
            return kpis
            
        except Exception as e:
            logger.error(f"[COMPREHENSIVE_KPIS] Error generating comprehensive KPIs: {str(e)}")
            return []

    async def _generate_enhanced_recommendations_deep(
        self,
        prioritized_insights: Dict[str, Any],
        missing_metrics: Dict[str, Any],
        variance_analysis: Dict[str, Any],
        trend_deviation_analysis: Dict[str, Any]
    ) -> List[str]:
        """NEW: Generate enhanced recommendations with specific actionable steps."""
        logger.info("[ENHANCED_RECOMMENDATIONS] Starting enhanced recommendations generation")
        
        try:
            recommendations = []
            
            # High priority recommendations based on business impact
            high_impact_deviations = prioritized_insights.get('high_impact_deviations', [])
            if high_impact_deviations:
                for deviation in high_impact_deviations[:3]:  # Top 3 critical issues
                    recommendations.append(
                        f"🚨 CRITICAL: {deviation['metric_name']} shows {deviation['variance_percentage']:.1f}% deviation. "
                        f"Immediate review of forecasting model parameters required for this {deviation['business_impact']} impact metric."
                    )
            
            # Trend alignment recommendations
            trend_status = trend_deviation_analysis.get('overall_alignment_status', 'unknown')
            if trend_status in ['weak_alignment', 'poor_alignment']:
                recommendations.append(
                    f"📈 TREND ALERT: Overall trend alignment is {trend_status.replace('_', ' ')}. "
                    f"Consider reviewing seasonal patterns and incorporating recent market changes into forecasting models."
                )
            
            # Missing metrics recommendations
            high_impact_missing = missing_metrics.get('high_impact_missing', [])
            if high_impact_missing:
                missing_names = [m['column_name'] for m in high_impact_missing[:3]]
                recommendations.append(
                    f"📊 DATA GAP: High-impact metrics missing from comparison: {', '.join(missing_names)}. "
                    f"Ensure data collection processes capture these critical metrics for future analysis."
                )
            
            # Data quality recommendations
            total_missing = missing_metrics.get('total_missing_count', 0)
            if total_missing > 5:
                recommendations.append(
                    f"🔧 DATA QUALITY: {total_missing} metrics couldn't be matched between datasets. "
                    f"Standardize column naming conventions and data collection processes across systems."
                )
            
            # Model performance recommendations
            medium_impact_count = prioritized_insights.get('summary', {}).get('medium_impact_count', 0)
            if medium_impact_count > 3:
                recommendations.append(
                    f"⚙️ MODEL TUNING: {medium_impact_count} metrics show moderate deviations. "
                    f"Schedule quarterly model recalibration to improve forecasting accuracy."
                )
            
            # Operational recommendations
            critical_count = prioritized_insights.get('summary', {}).get('immediate_attention_required', 0)
            if critical_count == 0:
                recommendations.append(
                    f"✅ MAINTENANCE: No critical issues detected. Continue monitoring and maintain current forecasting methodology. "
                    f"Consider implementing automated variance alerts for early detection."
                )
            
            # Category-specific recommendations (if available)
            granular_summary = prioritized_insights.get('granular_summary', {})
            if granular_summary and granular_summary.get('categories_analyzed', 0) > 0:
                recommendations.append(
                    f"🎯 SEGMENTED ANALYSIS: Category-wise analysis available for {granular_summary['categories_analyzed']} segments. "
                    f"Focus improvement efforts on underperforming categories identified in detailed analysis."
                )
            
            # Forecasting methodology recommendations
            if len(recommendations) < 3:  # Add general recommendations if specific issues are minimal
                recommendations.extend([
                    f"📋 BEST PRACTICE: Implement regular forecast accuracy reviews (monthly/quarterly) to maintain model performance.",
                    f"🔄 CONTINUOUS IMPROVEMENT: Consider ensemble forecasting methods to reduce variance in high-impact metrics.",
                    f"📈 MONITORING: Set up automated alerts for variance thresholds to enable proactive forecast adjustments."
                ])
            
            logger.info(f"[ENHANCED_RECOMMENDATIONS] Generated {len(recommendations)} enhanced recommendations")
            return recommendations
            
        except Exception as e:
            logger.error(f"[ENHANCED_RECOMMENDATIONS] Error generating enhanced recommendations: {str(e)}")
            return [f"⚠️ Error generating recommendations: {str(e)}"]

def make_json_serializable(obj):
    """Convert object to JSON-serializable format."""
    try:
        if hasattr(obj, '__dict__'):
            # Handle objects with __dict__ (like custom classes)
            result = {}
            for key, value in obj.__dict__.items():
                result[key] = make_json_serializable(value)
            return result
        elif isinstance(obj, (list, tuple)):
            return [make_json_serializable(item) for item in obj]
        elif isinstance(obj, dict):
            return {str(key): make_json_serializable(value) for key, value in obj.items()}
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, (np.integer, np.floating)):
            return obj.item()
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (np.bool_, bool)):
            return bool(obj)
        elif pd.isna(obj):
            return None
        elif obj is None:
            return None
        elif isinstance(obj, (str, int, float)):
            return obj
        else:
            # Fallback: convert to string for unknown types
            return str(obj)
    except Exception as e:
        logger.warning(f"JSON serialization fallback for {type(obj)}: {str(e)}")
        return str(obj)

# Pydantic models for request/response
class ComparisonRequest(BaseModel):
    estimated_file_id: Optional[str] = None
    actual_file_id: Optional[str] = None
    comparison_config: Optional[Dict[str, Any]] = {}

class ComparisonResponse(BaseModel):
    success: bool
    comparison_id: str
    analysis_result: Dict[str, Any]
    generated_at: str

# Keep minimal in-memory cache for active sessions (cleared periodically)
_temp_file_cache: Dict[str, Dict[str, Any]] = {}
_temp_result_cache: Dict[str, Dict[str, Any]] = {}

@router.get("/health")
async def health_check():
    """Health check endpoint for comparison service."""
    return {
        "status": "healthy",
        "service": "comparison-analytics",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "features": [
            "dual-file-upload",
            "multi-sheet-excel",
            "intelligent-comparison",
            "variance-analysis",
            "excel-sheet-detection"
        ]
    }

@router.post("/upload-dual-files")
async def upload_dual_files(
    estimated_file: UploadFile = File(...),
    actual_file: UploadFile = File(...),
    estimated_sheet: Optional[str] = Form(None),
    actual_sheet: Optional[str] = Form(None)
):
    """Upload both estimated and actual files for comparison."""
    logger.info("[COMPARISON] Starting dual file upload")
    
    try:
        # Validate files
        if not estimated_file or not estimated_file.filename:
            logger.error("[COMPARISON] Estimated file missing")
            return ORJSONResponse(
                status_code=400,
                content={"success": False, "detail": "Estimated file is required"}
            )
        if not actual_file or not actual_file.filename:
            logger.error("[COMPARISON] Actual file missing")
            return ORJSONResponse(
                status_code=400,
                content={"success": False, "detail": "Actual file is required"}
            )
        
        logger.info(f"[COMPARISON] Processing estimated file: {estimated_file.filename}")
        logger.info(f"[COMPARISON] Processing actual file: {actual_file.filename}")
        
        # Read estimated file with better error handling
        try:
            estimated_contents = await estimated_file.read()
            estimated_df = await read_file_to_dataframe(
                estimated_contents, estimated_file.filename, estimated_sheet
            )
            logger.info(f"[COMPARISON] Estimated file read successfully: {estimated_df.shape}")
        except Exception as e:
            logger.error(f"[COMPARISON] Error reading estimated file: {str(e)}")
            return ORJSONResponse(
                status_code=400,
                content={"success": False, "detail": f"Failed to read estimated file: {str(e)}"}
            )
        
        # Read actual file with better error handling
        try:
            actual_contents = await actual_file.read()
            actual_df = await read_file_to_dataframe(
                actual_contents, actual_file.filename, actual_sheet
            )
            logger.info(f"[COMPARISON] Actual file read successfully: {actual_df.shape}")
        except Exception as e:
            logger.error(f"[COMPARISON] Error reading actual file: {str(e)}")
            return ORJSONResponse(
                status_code=400,
                content={"success": False, "detail": f"Failed to read actual file: {str(e)}"}
            )
        
        # Store files with unique IDs
        estimated_id = str(uuid.uuid4())
        actual_id = str(uuid.uuid4())
        
        # Safe serialization for columns
        estimated_columns = [str(col) for col in estimated_df.columns]
        actual_columns = [str(col) for col in actual_df.columns]
        
        # Store estimated file in database
        estimated_file_info = {
            'filename': estimated_file.filename,
            'file_type': 'estimated',
            'sheet': estimated_sheet,
            'row_count': len(estimated_df),
            'column_count': len(estimated_df.columns),
            'columns': estimated_columns
        }
        
        await db_service.store_file_upload(
            session_id=estimated_id,
            file_info={
                **estimated_file_info,
                'filename': estimated_file.filename,
                'file_hash': hashlib.md5(estimated_contents).hexdigest(),
                'content_type': estimated_file.content_type,
                'size_bytes': len(estimated_contents),
                'file_path': ''  # No physical path for uploaded files
            }
        )
        
        # Store actual file in database
        actual_file_info = {
            'filename': actual_file.filename,
            'file_type': 'actual',
            'sheet': actual_sheet,
            'row_count': len(actual_df),
            'column_count': len(actual_df.columns),
            'columns': actual_columns
        }
        
        await db_service.store_file_upload(
            session_id=actual_id,
            file_info={
                **actual_file_info,
                'filename': actual_file.filename,
                'file_hash': hashlib.md5(actual_contents).hexdigest(),
                'content_type': actual_file.content_type,
                'size_bytes': len(actual_contents),
                'file_path': ''  # No physical path for uploaded files
            }
        )
        
        # Keep temporary cache for immediate use (files will expire from cache)
        _temp_file_cache[estimated_id] = {
            'filename': estimated_file.filename,
            'dataframe': estimated_df,
            'file_type': 'estimated',
            'sheet': estimated_sheet,
            'uploaded_at': datetime.now(timezone.utc),
            'row_count': len(estimated_df),
            'column_count': len(estimated_df.columns),
            'columns': estimated_columns
        }
        
        _temp_file_cache[actual_id] = {
            'filename': actual_file.filename,
            'dataframe': actual_df,
            'file_type': 'actual',
            'sheet': actual_sheet,
            'uploaded_at': datetime.now(timezone.utc),
            'row_count': len(actual_df),
            'column_count': len(actual_df.columns),
            'columns': actual_columns
        }
        
        logger.info(f"[COMPARISON] Files uploaded successfully")
        logger.info(f"[COMPARISON] Estimated: {estimated_df.shape[0]} rows, {estimated_df.shape[1]} columns")
        logger.info(f"[COMPARISON] Actual: {actual_df.shape[0]} rows, {actual_df.shape[1]} columns")
        
        response_data = {
            "success": True,
            "estimated_file_id": estimated_id,
            "actual_file_id": actual_id,
            "estimated_info": {
                "filename": estimated_file.filename,
                "rows": len(estimated_df),
                "columns": len(estimated_df.columns),
                "column_names": estimated_columns
            },
            "actual_info": {
                "filename": actual_file.filename,
                "rows": len(actual_df),
                "columns": len(actual_df.columns),
                "column_names": actual_columns
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Ensure JSON serializable response
        return ORJSONResponse(content=make_json_serializable(response_data))
        
    except Exception as e:
        logger.error(f"[COMPARISON] Unexpected error uploading dual files: {str(e)}")
        logger.error(f"[COMPARISON] Traceback: {traceback.format_exc()}")
        return ORJSONResponse(
            status_code=500,
            content={"success": False, "detail": f"Internal server error: {str(e)}"}
        )

@router.post("/upload-multi-sheet")
async def upload_multi_sheet_file(
    file: UploadFile = File(...),
    estimated_sheet: str = Form(...),
    actual_sheet: str = Form(...)
):
    """Upload a single file with multiple sheets containing estimated and actual data."""
    logger.info("[COMPARISON] Starting multi-sheet file upload")
    
    try:
        # Validate file
        if not file or not file.filename:
            raise HTTPException(status_code=400, detail="File is required")
        
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="Multi-sheet upload requires Excel files")
        
        logger.info(f"[COMPARISON] Processing multi-sheet file: {file.filename}")
        
        # Read file contents
        contents = await file.read()
        
        # First, check if the sheets exist
        try:
            available_sheets = await get_excel_sheet_names(contents, file.filename)
            logger.info(f"[COMPARISON] Available sheets: {available_sheets}")
            
            # Check if requested sheets exist
            if estimated_sheet not in available_sheets:
                error_msg = f"Sheet '{estimated_sheet}' not found. Available sheets: {', '.join(available_sheets)}"
                logger.error(f"[COMPARISON] {error_msg}")
                raise HTTPException(status_code=400, detail=error_msg)
            
            if actual_sheet not in available_sheets:
                error_msg = f"Sheet '{actual_sheet}' not found. Available sheets: {', '.join(available_sheets)}"
                logger.error(f"[COMPARISON] {error_msg}")
                raise HTTPException(status_code=400, detail=error_msg)
                
            if estimated_sheet == actual_sheet:
                error_msg = "Estimated and actual sheets must be different"
                logger.error(f"[COMPARISON] {error_msg}")
                raise HTTPException(status_code=400, detail=error_msg)
                
        except HTTPException:
            raise  # Re-raise HTTP exceptions
        except Exception as sheet_check_error:
            logger.error(f"[COMPARISON] Error checking sheets: {str(sheet_check_error)}")
            raise HTTPException(status_code=400, detail=f"Failed to read Excel sheets: {str(sheet_check_error)}")
        
        # Read both sheets
        estimated_df = await read_file_to_dataframe(contents, file.filename, estimated_sheet)
        actual_df = await read_file_to_dataframe(contents, file.filename, actual_sheet)
        
        # Store files with unique IDs
        estimated_id = str(uuid.uuid4())
        actual_id = str(uuid.uuid4())
        
        # Store estimated file in database
        estimated_file_info = {
            'filename': f"{file.filename} - {estimated_sheet}",
            'file_type': 'estimated',
            'sheet': estimated_sheet,
            'row_count': len(estimated_df),
            'column_count': len(estimated_df.columns),
            'columns': list(estimated_df.columns)
        }
        
        await db_service.store_file_upload(
            session_id=estimated_id,
            file_info={
                **estimated_file_info,
                'filename': f"{file.filename} - {estimated_sheet}",
                'file_hash': hashlib.md5(contents).hexdigest(),
                'content_type': file.content_type,
                'size_bytes': len(contents)
            }
        )
        
        # Store actual file in database
        actual_file_info = {
            'filename': f"{file.filename} - {actual_sheet}",
            'file_type': 'actual',
            'sheet': actual_sheet,
            'row_count': len(actual_df),
            'column_count': len(actual_df.columns),
            'columns': list(actual_df.columns)
        }
        
        await db_service.store_file_upload(
            session_id=actual_id,
            file_info={
                **actual_file_info,
                'filename': f"{file.filename} - {actual_sheet}",
                'file_hash': hashlib.md5(contents).hexdigest(),
                'content_type': file.content_type,
                'size_bytes': len(contents)
            }
        )
        
        # Keep temporary cache for immediate use
        _temp_file_cache[estimated_id] = {
            'filename': f"{file.filename} - {estimated_sheet}",
            'dataframe': estimated_df,
            'file_type': 'estimated',
            'sheet': estimated_sheet,
            'uploaded_at': datetime.now(timezone.utc),
            'row_count': len(estimated_df),
            'column_count': len(estimated_df.columns),
            'columns': list(estimated_df.columns)
        }
        
        _temp_file_cache[actual_id] = {
            'filename': f"{file.filename} - {actual_sheet}",
            'dataframe': actual_df,
            'file_type': 'actual',
            'sheet': actual_sheet,
            'uploaded_at': datetime.now(timezone.utc),
            'row_count': len(actual_df),
            'column_count': len(actual_df.columns),
            'columns': list(actual_df.columns)
        }
        
        logger.info(f"[COMPARISON] Multi-sheet file processed successfully")
        
        return ORJSONResponse(content={
            "success": True,
            "estimated_file_id": estimated_id,
            "actual_file_id": actual_id,
            "file_info": {
                "filename": file.filename,
                "estimated_sheet": estimated_sheet,
                "actual_sheet": actual_sheet
            },
            "estimated_info": {
                "rows": len(estimated_df),
                "columns": len(estimated_df.columns),
                "column_names": list(estimated_df.columns)
            },
            "actual_info": {
                "rows": len(actual_df),
                "columns": len(actual_df.columns),
                "column_names": list(actual_df.columns)
            }
        })
        
    except Exception as e:
        logger.error(f"[COMPARISON] Error uploading multi-sheet file: {str(e)}")
        logger.error(f"[COMPARISON] Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to upload multi-sheet file: {str(e)}")

@router.post("/analyze")
async def analyze_comparison(request: ComparisonRequest):
    """Perform intelligent comparison analysis with AI-powered insights and charts."""
    start_time = datetime.now(timezone.utc).timestamp()
    logger.info("[COMPARISON] Starting AI-powered comparison analysis")
    
    # Set longer timeout for complex analysis operations
    config = request.comparison_config or {}
    analysis_timeout = config.get('analysis_timeout', 90000)
    logger.info(f"[COMPARISON] Analysis timeout set to {analysis_timeout}ms")
    
    try:
        # Validate file IDs
        if not request.estimated_file_id:
            raise HTTPException(status_code=400, detail="Estimated file ID is required")
        if not request.actual_file_id:
            raise HTTPException(status_code=400, detail="Actual file ID is required")
        
        # Try to get files from temporary cache first, then from database
        estimated_data = _temp_file_cache.get(request.estimated_file_id)
        actual_data = _temp_file_cache.get(request.actual_file_id)
        
        # If not in cache, retrieve from database
        if not estimated_data:
            estimated_data = await db_service.get_file_upload(request.estimated_file_id)
            if not estimated_data:
                raise HTTPException(status_code=404, detail="Estimated file not found")
        
        if not actual_data:
            actual_data = await db_service.get_file_upload(request.actual_file_id)
            if not actual_data:
                raise HTTPException(status_code=404, detail="Actual file not found")
        
        estimated_df = estimated_data.get('dataframe')
        actual_df = actual_data.get('dataframe')
        
        # Check if dataframes are available
        if estimated_df is None:
            raise HTTPException(
                status_code=400, 
                detail="Estimated data not available in cache. Please re-upload the file."
            )
        
        if actual_df is None:
            raise HTTPException(
                status_code=400, 
                detail="Actual data not available in cache. Please re-upload the file."
            )
        
        logger.info(f"[COMPARISON] Analyzing datasets:")
        logger.info(f"[COMPARISON] Estimated: {estimated_df.shape}")
        logger.info(f"[COMPARISON] Actual: {actual_df.shape}")
        
        # Check cache first for performance optimization
        cache_key = f"comparison_analysis:{hashlib.md5(f'{request.estimated_file_id}:{request.actual_file_id}'.encode()).hexdigest()}"
        try:
            cached_result = await cache_manager.get(cache_key)
            if cached_result and config.get("enable_caching", True):
                logger.info(f"[COMPARISON] Using cached analysis result")
                cached_data = json.loads(cached_result)
                comparison_id = str(uuid.uuid4())  # Generate new ID for this request
                cached_data['_cached'] = True
                cached_data['_cache_hit_time'] = datetime.now(timezone.utc).isoformat()
                
                return ORJSONResponse(content={
                    "success": True,
                    "comparison_id": comparison_id,
                    "analysis_result": cached_data,
                    "cached": True,
                    "generated_at": datetime.now(timezone.utc).isoformat()
                })
        except Exception as e:
            logger.warning(f"[COMPARISON] Cache check failed: {e}")
        
        # Step 1: Create comparison agent
        comparison_agent = SimpleIntelligentComparisonAgent()
        
        # Step 2: Perform core comparison analysis
        comparison_result = await comparison_agent.compare_datasets(
            estimated_df=estimated_df,
            actual_df=actual_df,
            comparison_config=request.comparison_config
        )
        
        # Step 3: Use the enhanced analysis that was already generated by SimpleIntelligentComparisonAgent
        # The comparison_result already contains comprehensive charts and KPIs from the deep analysis
        enhanced_charts = comparison_result.charts_data or []
        comprehensive_kpis = comparison_result.kpis or []
        
        # Step 4: Create conversational agent for additional AI insights
        try:
            conversational_agent = ConversationalAnalyticsAgent()
            
            # Analyze both datasets for enhanced insights
            estimated_analysis = await conversational_agent.analyze_uploaded_data(
                estimated_df, estimated_data['filename']
            )
            actual_analysis = await conversational_agent.analyze_uploaded_data(
                actual_df, actual_data['filename']
            )
            
            # Generate additional AI insights to complement the deep analysis
            ai_insights = await generate_ai_comparison_insights(comparison_result, estimated_analysis, actual_analysis)
            
            logger.info(f"[INSIGHTS] Generated {len(ai_insights)} AI-powered insights")
            logger.info(f"[CHARTS] No critical deviations found, skipping variance chart" if not comparison_result.critical_deviations else f"[CHARTS] Using {len(enhanced_charts)} enhanced charts from deep analysis")
            logger.info(f"[KPIS] Generated {len(comprehensive_kpis)} comprehensive KPIs")
            
        except Exception as e:
            logger.warning(f"[COMPARISON] Could not run conversational agent: {str(e)}")
            estimated_analysis = None
            actual_analysis = None
            ai_insights = [{
                'title': 'Enhanced Deep Analysis Complete',
                'description': f'Analyzed {estimated_data["filename"]} vs {actual_data["filename"]} using comprehensive deep comparison with individual metric analysis, trend correlation, and business impact prioritization.',
                'type': 'success',
                'severity': 'info'
            }]
        
        # Generate comparison ID and store result
        comparison_id = str(uuid.uuid4())
        
        # Convert result to serializable format
        serializable_result = {
            'overall_variance': comparison_result.overall_variance,
            'trend_alignment': comparison_result.trend_alignment,
            'critical_deviations': make_json_serializable(comparison_result.critical_deviations),
            'performance_summary': make_json_serializable(comparison_result.performance_summary),
            'recommendations': comparison_result.recommendations,
            'insights': make_json_serializable(comparison_result.insights),
            'charts_data': make_json_serializable(enhanced_charts),  # Use enhanced charts
            'kpis': make_json_serializable(comprehensive_kpis),  # Use comprehensive KPIs
            'ai_insights': make_json_serializable(ai_insights),  # New AI insights
            'data_analysis': {
                'estimated': make_json_serializable(estimated_analysis.__dict__ if estimated_analysis else {}),
                'actual': make_json_serializable(actual_analysis.__dict__ if actual_analysis else {})
            }
        }
        
        # Store comparison result in database
        await db_service.store_comparison_result(
            comparison_id=comparison_id,
            analysis_result=serializable_result,
            metadata={
                'estimated_file_id': request.estimated_file_id,
                'actual_file_id': request.actual_file_id,
                'estimated_file': estimated_data.get('filename', 'Unknown'),
                'actual_file': actual_data.get('filename', 'Unknown'),
                'config': request.comparison_config
            }
        )
        
        # Keep temporary cache for immediate retrieval
        _temp_result_cache[comparison_id] = {
            'result': serializable_result,
            'metadata': {
                'estimated_file': estimated_data.get('filename', 'Unknown'),
                'actual_file': actual_data.get('filename', 'Unknown'),
                'analyzed_at': datetime.now(timezone.utc),
                'config': request.comparison_config
            }
        }
        
        # Cache the analysis result for future requests (expire in 2 hours)
        try:
            await cache_manager.set(cache_key, json.dumps(serializable_result, default=str), expire=7200)
            logger.info(f"[COMPARISON] Analysis result cached for future use")
        except Exception as e:
            logger.warning(f"[COMPARISON] Failed to cache analysis result: {e}")
        
        logger.info(f"[COMPARISON] AI-powered analysis completed successfully. ID: {comparison_id}")
        
        return ORJSONResponse(content={
            "success": True,
            "comparison_id": comparison_id,
            "analysis_result": serializable_result,
            "analysis_time": f"{(datetime.now(timezone.utc).timestamp() - start_time) * 1000:.0f}ms",
            "generated_at": datetime.now(timezone.utc).isoformat()
        })
        
    except Exception as e:
        logger.error(f"[COMPARISON] Error in comparison analysis: {str(e)}")
        logger.error(f"[COMPARISON] Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze comparison: {str(e)}")

@router.get("/result/{comparison_id}")
async def get_comparison_result(comparison_id: str):
    """Get stored comparison analysis result."""
    try:
        # Try temporary cache first
        result = _temp_result_cache.get(comparison_id)
        
        # If not in cache, retrieve from database
        if not result:
            result = await db_service.get_comparison_result(comparison_id)
            if not result:
                raise HTTPException(status_code=404, detail="Comparison result not found")
        
        return ORJSONResponse(content=result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[COMPARISON] Error getting comparison result: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get comparison result: {str(e)}")

@router.get("/file-info/{file_id}")
async def get_file_info(file_id: str):
    """Get information about uploaded file."""
    try:
        # Try temporary cache first
        file_info = _temp_file_cache.get(file_id)
        
        # If not in cache, retrieve from database
        if not file_info:
            file_info = await db_service.get_file_upload(file_id)
            if not file_info:
                raise HTTPException(status_code=404, detail="File not found")
        
        # Create a copy and remove dataframe from response (too large)
        response_info = file_info.copy()
        response_info.pop('dataframe', None)
        
        return ORJSONResponse(content=response_info)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[COMPARISON] Error getting file info: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get file info: {str(e)}")

@router.post("/detect-excel-sheets")
async def detect_excel_sheets(file: UploadFile = File(...)):
    """Detect available sheets in an Excel file before upload."""
    try:
        # Validate file
        if not file or not file.filename:
            raise HTTPException(status_code=400, detail="File is required")
        
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="Only Excel files are supported for sheet detection")
        
        logger.info(f"[COMPARISON] Detecting sheets in: {file.filename}")
        
        # Read file contents
        contents = await file.read()
        
        # Get available sheet names
        sheet_names = await get_excel_sheet_names(contents, file.filename)
        
        # Try to auto-detect estimated and actual sheets
        estimated_match = find_best_sheet_match(sheet_names, "estimated")
        actual_match = find_best_sheet_match(sheet_names, "actual")
        
        logger.info(f"[COMPARISON] Detected {len(sheet_names)} sheets in {file.filename}")
        logger.info(f"[COMPARISON] Auto-detected estimated: {estimated_match}, actual: {actual_match}")
        
        return ORJSONResponse(content={
            "success": True,
            "filename": file.filename,
            "sheet_names": sheet_names,
            "suggested_mapping": {
                "estimated": estimated_match,
                "actual": actual_match
            },
            "total_sheets": len(sheet_names)
        })
        
    except Exception as e:
        logger.error(f"[COMPARISON] Error detecting Excel sheets: {str(e)}")
        logger.error(f"[COMPARISON] Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to detect Excel sheets: {str(e)}")

@router.get("/list-excel-sheets/{file_id}")
async def list_excel_sheets(file_id: str):
    """List available sheets in an uploaded Excel file."""
    try:
        # Check if file exists in our cache first, then database
        file_info = None
        if file_id in _temp_file_cache:
            cache_entry = _temp_file_cache[file_id]
            if cache_entry.get('ttl', datetime.now(timezone.utc)) > datetime.now(timezone.utc):
                file_info = cache_entry
        
        # If not in cache, try database
        if not file_info:
            file_info = await db_service.get_file_upload(file_id)
            if not file_info:
                raise HTTPException(status_code=404, detail="File not found. Please upload the file first.")
        filename = file_info.get('filename', 'unknown')
        
        # We need the original file contents, but we only have the DataFrame
        # Return error for now - this endpoint needs the original file content
        return {
            "message": "Sheet listing requires the original file content. Please use the /detect-excel-sheets endpoint before upload.",
            "filename": filename,
            "file_id": file_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[COMPARISON] Error listing Excel sheets: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list Excel sheets: {str(e)}")

# Enhanced helper functions for AI integration

async def generate_enhanced_comparison_charts(
    estimated_df: pd.DataFrame,
    actual_df: pd.DataFrame,
    comparison_result: ComparisonResult,
    estimated_analysis,
    actual_analysis
) -> List[Dict[str, Any]]:
    """Generate enhanced charts using conversational agent approach."""
    charts = []
    
    try:
        # Chart 1: Variance Overview (Enhanced)
        variance_chart = await create_enhanced_variance_chart(comparison_result, estimated_analysis, actual_analysis)
        if variance_chart:
            charts.append(variance_chart)
        
        # Chart 2: Side-by-side Comparison with AI insights
        comparison_chart = await create_ai_comparison_chart(estimated_df, actual_df, estimated_analysis, actual_analysis)
        if comparison_chart:
            charts.append(comparison_chart)
        
        # Chart 3: Trend Analysis Chart
        trend_chart = await create_trend_analysis_chart(estimated_df, actual_df, comparison_result)
        if trend_chart:
            charts.append(trend_chart)
        
        # Chart 4: Performance Dashboard Style Chart
        performance_chart = await create_performance_dashboard_chart(comparison_result, estimated_analysis, actual_analysis)
        if performance_chart:
            charts.append(performance_chart)
        
        logger.info(f"[CHARTS] Generated {len(charts)} enhanced comparison charts")
        return charts
        
    except Exception as e:
        logger.error(f"[CHARTS] Error generating enhanced charts: {str(e)}")
        return comparison_result.charts_data or []

async def create_enhanced_variance_chart(comparison_result, estimated_analysis, actual_analysis) -> Optional[Dict[str, Any]]:
    """Create an enhanced variance chart with AI insights."""
    try:
        if not comparison_result.critical_deviations or len(comparison_result.critical_deviations) == 0:
            logger.info("[CHARTS] No critical deviations found, skipping variance chart")
            return None
        
        chart_data = []
        for deviation in comparison_result.critical_deviations[:6]:  # Top 6 deviations
            metric = deviation.get("metric", "Unknown")
            variance = abs(deviation.get("variance_percentage", 0))
            estimated = deviation.get("estimated_value", 0)
            actual = deviation.get("actual_value", 0)
            
            # Skip if values are invalid or zero
            if variance == 0 or (estimated == 0 and actual == 0):
                continue
                
            chart_data.append({
                "metric": metric,
                "variance": variance,
                "severity": deviation.get("severity", "low"),
                "estimated": estimated,
                "actual": actual
            })
        
        # Only return chart if we have meaningful data
        if len(chart_data) == 0:
            logger.info("[CHARTS] No meaningful variance data, skipping variance chart")
            return None
        
        # Add color coding to each data point based on severity
        for item in chart_data:
            variance = item['variance']
            if variance > 25:
                item['fill'] = '#dc2626'  # Dark red
            elif variance > 15:
                item['fill'] = '#ea580c'  # Orange
            elif variance > 8:
                item['fill'] = '#d97706'  # Amber
            else:
                item['fill'] = '#65a30d'  # Green
        
        return {
            "id": "enhanced_variance_overview",
            "type": "bar",
            "title": "Variance Analysis - Top Deviations",
            "subtitle": f"Showing {len(chart_data)} metrics with highest variance",
            "data": chart_data,
            "config": {
                "height": 400,
                "xAxis": {
                    "name": "Metrics",
                    "nameLocation": "middle",
                    "nameGap": 35,
                    "axisLabel": {
                        "rotate": 45,
                        "interval": 0
                    }
                },
                "yAxis": {
                    "name": "Variance %",
                    "nameLocation": "middle",
                    "nameGap": 40
                },
                "bars": [{
                    "dataKey": "variance",
                    "name": "Variance %",
                    "radius": [8, 8, 0, 0]
                }],
                "legend": {
                    "enabled": True,
                    "position": "top-right",
                    "data": [
                        {"value": ">25% Critical", "type": "rect", "color": "#dc2626"},
                        {"value": "15-25% High", "type": "rect", "color": "#ea580c"},
                        {"value": "8-15% Medium", "type": "rect", "color": "#d97706"},
                        {"value": "<8% Low", "type": "rect", "color": "#65a30d"}
                    ]
                },
                "tooltip": {
                    "formatter": "{metric}\nVariance: {variance:.1f}%\nEstimated: {estimated:,.0f}\nActual: {actual:,.0f}",
                    "contentStyle": {
                        "backgroundColor": "rgba(0, 0, 0, 0.8)",
                        "border": "none",
                        "borderRadius": "8px",
                        "color": "#fff"
                    }
                },
                "animation": {
                    "duration": 1000,
                    "easing": "easeOutBack"
                },
                "grid": {
                    "containLabel": True,
                    "left": "3%",
                    "right": "3%",
                    "bottom": "15%"
                },
                "colors": ["#ef4444", "#f97316", "#eab308", "#22c55e"]
            }
        }
    except Exception as e:
        logger.error(f"[CHARTS] Error creating enhanced variance chart: {str(e)}")
        return None

async def create_ai_comparison_chart(estimated_df, actual_df, estimated_analysis, actual_analysis) -> Optional[Dict[str, Any]]:
    """Create AI-powered comparison chart similar to chat system."""
    try:
        # Get the most relevant numeric columns
        est_numeric = estimated_analysis.numerical_columns[:3] if estimated_analysis and estimated_analysis.numerical_columns else []
        act_numeric = actual_analysis.numerical_columns[:3] if actual_analysis and actual_analysis.numerical_columns else []
        
        if not est_numeric or not act_numeric:
            logger.info("[CHARTS] No matching numeric columns found, skipping comparison chart")
            return None
        
        chart_data = []
        
        # Create comparison data for top metrics
        for i, (est_col, act_col) in enumerate(zip(est_numeric, act_numeric)):
            if est_col in estimated_df.columns and act_col in actual_df.columns:
                try:
                    # Clean and calculate sums
                    est_values = cast(pd.Series, pd.to_numeric(estimated_df[est_col], errors='coerce')).dropna()
                    act_values = cast(pd.Series, pd.to_numeric(actual_df[act_col], errors='coerce')).dropna()
                    
                    if len(est_values) == 0 or len(act_values) == 0:
                        continue
                        
                    est_sum = float(est_values.sum())
                    act_sum = float(act_values.sum())
                    
                    # Skip if both values are zero or very small
                    if abs(est_sum) < 0.01 and abs(act_sum) < 0.01:
                        continue
                    
                    variance = ((act_sum - est_sum) / est_sum * 100) if est_sum != 0 else 0
                    
                    chart_data.append({
                        "metric": f"Metric {i+1}",
                        "estimated": round(est_sum, 2),
                        "actual": round(act_sum, 2),
                        "variance": round(variance, 2)
                    })
                except Exception as col_error:
                    logger.warning(f"[CHARTS] Error processing columns {est_col}/{act_col}: {str(col_error)}")
                    continue
        
        # Only return chart if we have meaningful data
        if len(chart_data) == 0:
            logger.info("[CHARTS] No meaningful comparison data, skipping comparison chart")
            return None
        
        return {
            "id": "ai_comparison_overview",
            "type": "bar",
            "title": "Estimated vs Actual Performance",
            "subtitle": f"AI-powered comparison of {len(chart_data)} key metrics",
            "data": chart_data,
            "config": {
                "height": 400,
                "xAxis": {
                    "name": "Metrics",
                    "nameLocation": "middle",
                    "nameGap": 35
                },
                "yAxis": {
                    "name": "Values",
                    "nameLocation": "middle", 
                    "nameGap": 50,
                    "axisLabel": {
                        "formatter": "{value:,.0f}"
                    }
                },
                "bars": [
                    {
                        "dataKey": "estimated",
                        "name": "Estimated",
                        "fill": "#3b82f6",
                        "radius": [8, 8, 0, 0]
                    },
                    {
                        "dataKey": "actual",
                        "name": "Actual", 
                        "fill": "#10b981",
                        "radius": [8, 8, 0, 0]
                    },
                    {
                        "dataKey": "variance",
                        "name": "Variance %",
                        "fill": "#ef4444",
                        "radius": [8, 8, 0, 0],
                        "yAxisIndex": 1  # Use secondary axis for variance
                    }
                ],
                "legend": {
                    "enabled": True,
                    "position": "top",
                    "align": "center",
                    "icon": "rect",
                    "itemGap": 20,
                    "textStyle": {
                        "fontSize": 12
                    }
                },
                "tooltip": {
                    "formatter": "{metric}\nEstimated: {estimated:,.0f}\nActual: {actual:,.0f}\nVariance: {variance:.1f}%",
                    "contentStyle": {
                        "backgroundColor": "rgba(0, 0, 0, 0.85)",
                        "border": "1px solid #333",
                        "borderRadius": "8px",
                        "color": "#fff",
                        "padding": "10px"
                    }
                },
                "animation": {
                    "duration": 1200,
                    "easing": "easeOutElastic"
                },
                "grid": {
                    "containLabel": True,
                    "left": "5%",
                    "right": "5%",
                    "bottom": "10%",
                    "top": "15%"
                },
                "barCategoryGap": "30%",
                "yAxis2": {
                    "name": "Variance %",
                    "nameLocation": "middle",
                    "nameGap": 40,
                    "position": "right",
                    "axisLabel": {
                        "formatter": "{value}%"
                    }
                },
                "colors": ["#3b82f6", "#10b981", "#ef4444"]
            }
        }
    except Exception as e:
        logger.error(f"[CHARTS] Error creating AI comparison chart: {str(e)}")
        return None

async def create_trend_analysis_chart(estimated_df, actual_df, comparison_result) -> Optional[Dict[str, Any]]:
    """Create trend analysis chart."""
    try:
        # Check if we have enough data points for trends
        min_rows = min(len(estimated_df), len(actual_df))
        if min_rows < 2:
            logger.info("[CHARTS] Insufficient data for trend analysis, skipping trend chart")
            return None
        
        chart_data = []
        
        # Create time series data based on available data
        num_points = min(10, min_rows)  # Use up to 10 data points
        
        # Try to find numeric columns for trend analysis
        est_numeric = [col for col in estimated_df.columns if pd.api.types.is_numeric_dtype(estimated_df[col])]
        act_numeric = [col for col in actual_df.columns if pd.api.types.is_numeric_dtype(actual_df[col])]
        
        if not est_numeric or not act_numeric:
            logger.info("[CHARTS] No numeric columns for trend analysis, skipping trend chart")
            return None
        
        try:
            # Use first numeric column for trend analysis
            est_col = est_numeric[0]
            act_col = act_numeric[0]
            
            est_values = cast(pd.Series, pd.to_numeric(estimated_df[est_col], errors='coerce')).dropna()
            act_values = cast(pd.Series, pd.to_numeric(actual_df[act_col], errors='coerce')).dropna()
            
            if len(est_values) < 2 or len(act_values) < 2:
                logger.info("[CHARTS] Insufficient valid data for trend analysis")
                return None
            
            # Create trend data points
            for i in range(num_points):
                est_idx = min(i, len(est_values) - 1)
                act_idx = min(i, len(act_values) - 1)
                
                est_val = float(est_values.iloc[est_idx])
                act_val = float(act_values.iloc[act_idx])
                variance = ((act_val - est_val) / est_val * 100) if est_val != 0 else 0
                
                chart_data.append({
                    "period": f"Period {i+1}",
                    "estimated_trend": round(est_val, 2),
                    "actual_trend": round(act_val, 2),
                    "variance": round(variance, 2)
                })
                
        except Exception as trend_error:
            logger.warning(f"[CHARTS] Error calculating trends: {str(trend_error)}")
            return None
        
        # Only return if we have meaningful trend data
        if len(chart_data) == 0:
            logger.info("[CHARTS] No meaningful trend data generated")
            return None
        
        return {
            "id": "trend_analysis",
            "type": "line",
            "title": "Trend Analysis Over Time",
            "subtitle": f"Performance trends across {len(chart_data)} time periods",
            "data": chart_data,
            "config": {
                "height": 400,
                "xAxis": {
                    "name": "Time Period",
                    "nameLocation": "middle",
                    "nameGap": 35,
                    "boundaryGap": False
                },
                "yAxis": {
                    "name": "Performance",
                    "nameLocation": "middle",
                    "nameGap": 50,
                    "axisLabel": {
                        "formatter": "{value:,.0f}"
                    }
                },
                "lines": [
                    {
                        "dataKey": "estimated_trend",
                        "name": "Estimated",
                        "stroke": "#3b82f6",
                        "strokeWidth": 3,
                        "dot": {"fill": "#60a5fa", "r": 5},
                        "activeDot": {"r": 8, "fill": "#3b82f6"},
                        "smooth": True
                    },
                    {
                        "dataKey": "actual_trend",
                        "name": "Actual",
                        "stroke": "#10b981",
                        "strokeWidth": 3,
                        "dot": {"fill": "#34d399", "r": 5},
                        "activeDot": {"r": 8, "fill": "#10b981"},
                        "smooth": True
                    },
                    {
                        "dataKey": "variance",
                        "name": "Variance %",
                        "stroke": "#ef4444",
                        "strokeWidth": 2,
                        "strokeDasharray": "5 5",
                        "dot": {"fill": "#f87171", "r": 4},
                        "yAxisIndex": 1
                    }
                ],
                "legend": {
                    "enabled": True,
                    "position": "top",
                    "align": "center",
                    "iconType": "line",
                    "itemGap": 25,
                    "textStyle": {
                        "fontSize": 12
                    }
                },
                "tooltip": {
                    "trigger": "axis",
                    "formatter": "{period}\nEstimated: {estimated_trend:,.0f}\nActual: {actual_trend:,.0f}\nVariance: {variance:.1f}%",
                    "contentStyle": {
                        "backgroundColor": "rgba(0, 0, 0, 0.85)",
                        "border": "1px solid #333",
                        "borderRadius": "8px",
                        "color": "#fff",
                        "padding": "10px"
                    }
                },
                "animation": {
                    "duration": 1500,
                    "easing": "easeInOutQuart"
                },
                "grid": {
                    "containLabel": True,
                    "left": "5%",
                    "right": "5%",
                    "bottom": "10%",
                    "top": "15%",
                    "strokeDasharray": "3 3",
                    "stroke": "#e5e7eb"
                },
                "area": {
                    "estimated_trend": {
                        "fill": "rgba(59, 130, 246, 0.1)",
                        "smooth": True
                    },
                    "actual_trend": {
                        "fill": "rgba(16, 185, 129, 0.1)",
                        "smooth": True
                    }
                },
                "yAxis2": {
                    "name": "Variance %",
                    "nameLocation": "middle",
                    "nameGap": 40,
                    "position": "right",
                    "axisLabel": {
                        "formatter": "{value}%"
                    },
                    "splitLine": {
                        "show": False
                    }
                },
                "colors": ["#3b82f6", "#10b981", "#ef4444"]
            }
        }
    except Exception as e:
        logger.error(f"[CHARTS] Error creating trend analysis chart: {str(e)}")
        return None

async def create_performance_dashboard_chart(comparison_result, estimated_analysis, actual_analysis) -> Optional[Dict[str, Any]]:
    """Create performance dashboard style chart."""
    try:
        # Create pie chart showing variance distribution
        variance_distribution = {
            "Low Variance (< 10%)": 0,
            "Medium Variance (10-25%)": 0,
            "High Variance (> 25%)": 0
        }
        
        for deviation in comparison_result.critical_deviations:
            variance = abs(deviation.get("variance_percentage", 0))
            if variance < 10:
                variance_distribution["Low Variance (< 10%)"] += 1
            elif variance < 25:
                variance_distribution["Medium Variance (10-25%)"] += 1
            else:
                variance_distribution["High Variance (> 25%)"] += 1
        
        chart_data = [
            {"name": category, "value": count}
            for category, count in variance_distribution.items()
            if count > 0
        ]
        
        # Calculate total for percentage display
        total_count = sum(item['value'] for item in chart_data)
        
        # Add percentage to each item
        for item in chart_data:
            item['percentage'] = (item['value'] / total_count * 100) if total_count > 0 else 0
        
        return {
            "id": "performance_distribution",
            "type": "pie",
            "title": "Variance Distribution Analysis",
            "subtitle": f"Distribution of {total_count} metrics by variance severity",
            "data": chart_data,
            "config": {
                "height": 350,
                "innerRadius": "35%",  # Donut chart
                "outerRadius": "75%",
                "padAngle": 3,  # Space between segments
                "cornerRadius": 8,  # Rounded corners
                "dataKey": "value",
                "nameKey": "name",
                "legend": {
                    "enabled": True,
                    "position": "right",
                    "align": "middle",
                    "formatter": "{name}: {value} ({percentage:.1f}%)",
                    "icon": "circle",
                    "itemGap": 15,
                    "textStyle": {
                        "fontSize": 12
                    }
                },
                "tooltip": {
                    "formatter": "{name}\nCount: {value} metrics\nPercentage: {percentage:.1f}%",
                    "contentStyle": {
                        "backgroundColor": "rgba(0, 0, 0, 0.85)",
                        "border": "1px solid #333",
                        "borderRadius": "8px",
                        "color": "#fff",
                        "padding": "10px"
                    }
                },
                "label": {
                    "show": True,
                    "position": "outside",
                    "formatter": "{percentage:.0f}%",
                    "fontSize": 14,
                    "fontWeight": "bold"
                },
                "animation": {
                    "duration": 1200,
                    "easing": "easeOutBack",
                    "animationBegin": 0,
                    "animationDuration": 1200
                },
                "emphasis": {
                    "scale": 1.1,
                    "scaleSize": 10,
                    "shadowBlur": 10,
                    "shadowOffsetX": 0,
                    "shadowColor": "rgba(0, 0, 0, 0.5)"
                },
                "colors": ["#10b981", "#f59e0b", "#ef4444"]
            }
        }
    except Exception as e:
        logger.error(f"[CHARTS] Error creating performance dashboard chart: {str(e)}")
        return None

async def generate_ai_comparison_insights(comparison_result, estimated_analysis, actual_analysis) -> List[Dict[str, Any]]:
    """Generate actual AI-powered insights using LiteLLM service for accurate, contextual analysis."""
    
    try:
        # Import the AI service
        from src.services.litellm_service import LiteLLMService
        
        ai_service = LiteLLMService()
        
        if not ai_service.is_available():
            logger.warning("[AI_INSIGHTS] LiteLLM service not available, using fallback insights")
            return await _generate_fallback_statistical_insights(comparison_result, estimated_analysis, actual_analysis)
        
        # Extract comprehensive data for AI analysis
        performance_summary = comparison_result.performance_summary or {}
        individual_metrics = performance_summary.get('individual_metrics', [])
        individual_metrics_summary = performance_summary.get('individual_metrics_summary', {})
        trend_health_summary = performance_summary.get('trend_health_summary', {})
        
        # Get key statistics for AI context
        total_analyzed = (
            individual_metrics_summary.get('total_analyzed', 0) or 
            len(comparison_result.critical_deviations or []) or
            len(individual_metrics)
        )
        
        high_variance_count = (
            individual_metrics_summary.get('high_variance_count', 0) or
            len([d for d in (comparison_result.critical_deviations or []) if abs(d.get('variance_percentage', 0)) > 15])
        )
        
        overall_accuracy = max(0, 100 - abs(comparison_result.overall_variance))
        
        # Get top 3 critical deviations for context
        critical_metrics = []
        critical_details = []
        for dev in (comparison_result.critical_deviations or [])[:3]:
            # Try multiple fallbacks to get the actual column name
            metric_name = (
                dev.get('metric_name') or 
                dev.get('metric') or 
                dev.get('column_name') or
                dev.get('est_col_name') or
                dev.get('name') or
                'Unknown'
            )
            # Never use generic names like "Metric_9", instead show the actual issue
            if metric_name == 'Unknown' and dev.get('index') is not None:
                metric_name = f"Column at index {dev.get('index')}"
            variance = abs(dev.get('variance_percentage', 0))
            # Try multiple fields to get actual values
            estimated_val = (
                dev.get('estimated_value') or 
                dev.get('estimated_total') or 
                dev.get('est_value') or 
                0
            )
            actual_val = (
                dev.get('actual_value') or 
                dev.get('actual_total') or 
                dev.get('act_value') or 
                0
            )
            critical_metrics.append(f"{metric_name} ({variance:.1f}% variance)")
            critical_details.append({
                'name': metric_name,
                'variance': variance,
                'estimated': float(estimated_val),
                'actual': float(actual_val),
                'business_impact': dev.get('business_impact', 'Unknown')
            })
        
        # Get specific details from individual metrics for more context
        metric_patterns = []
        for metric in (individual_metrics or [])[:5]:
            metric_patterns.append({
                'name': metric.get('metric_name', 'Unknown'),
                'variance': abs(metric.get('variance_percentage', 0)),
                'accuracy': metric.get('accuracy_score', 0),
                'trend_correlation': metric.get('trend_correlation', 0),
                'business_impact': metric.get('business_impact', 'Unknown'),
                'outliers': metric.get('outliers_detected', {}).get('outlier_impact', 'low')
            })
        
        # Log critical details for debugging
        logger.info(f"[AI_INSIGHTS] Critical details being sent to AI: {json.dumps(critical_details[:1], indent=2)}")
        
        # Prepare AI prompt with structured data context and specific metric details
        ai_prompt = f"""
You are an expert business analyst providing actionable insights for forecast vs actual comparison.

ANALYSIS SUMMARY:
- Total metrics analyzed: {total_analyzed}
- Overall forecast accuracy: {overall_accuracy:.1f}%
- Overall variance: {comparison_result.overall_variance:.1f}%
- Trend alignment: {comparison_result.trend_alignment.replace('_', ' ').title()}
- High variance metrics: {high_variance_count}
- Critical metrics: {', '.join(critical_metrics) if critical_metrics else 'None'}

CRITICAL METRIC DETAILS (IMPORTANT - USE THESE EXACT VALUES):
{json.dumps(critical_details, indent=2)}

INDIVIDUAL METRIC PATTERNS:
{json.dumps(metric_patterns, indent=2)}

TASK:
Generate 1-3 highly specific, actionable insights based on the actual data above. Each insight must:
1. Use the EXACT metric names and values from CRITICAL METRIC DETAILS section
2. Include the ACTUAL estimated and actual values (not zero) from the data provided
3. Provide concrete actions (not generic "review" or "re-evaluate")
4. Include specific thresholds, timeframes, or parameters
5. Suggest specific techniques or methods that could help

CRITICAL: When you see a metric in CRITICAL METRIC DETAILS like:
{{"name": "Metric_3", "variance": 55.7, "estimated": 1234.0, "actual": 2234.0}}
You MUST use these exact values, NOT "Est: 0, Act: 0"

You MUST return your response as valid JSON only with this exact structure:
{{
  "insights": [
    {{
      "title": "High Variance in [actual metric name] 🚨",
      "description": "[Metric name] shows a high variance of [X]% with an estimated value of [actual estimated value] and actual value of [actual actual value]. This indicates a significant deviation from the forecasted value.",
      "points": [
        "Specific metric: [metric name] shows [X]% variance (Est: [actual estimated value], Act: [actual actual value])",
        "Root cause hypothesis: [specific hypothesis based on the variance pattern]",
        "Specific technique: Implement [specific method/model] with [parameters]",
        "Timeline: Complete by [specific timeframe] to reduce variance to <[X]%",
        "Expected outcome: Reduce [metric] variance from [X]% to [Y]% within [timeframe]"
      ],
      "type": "ai_analysis",
      "severity": "high|medium|low",
      "recommendation": "Specific action: [Do X with Y parameters by Z timeline]"
    }}
  ]
}}
"""

        # Define expected JSON format for AI response
        response_format = {
            "insights": [
                {
                    "title": "Brief title with emoji",
                    "description": "2-3 sentence description",
                    "points": ["finding 1", "finding 2", "recommendation"],
                    "type": "ai_analysis",
                    "severity": "high/medium/low",
                    "recommendation": "Specific next action"
                }
            ]
        }
        
        # Generate AI insights with structured response
        logger.info("[AI_INSIGHTS] Generating actual AI insights from data analysis")
        ai_response = await ai_service.generate_structured_response(
            prompt=ai_prompt,
            response_format=response_format
        )
        
        # Parse AI response with structured format
        try:
            # Parse the structured response
            response_data = json.loads(ai_response.content)
            
            # Extract insights from the structured response
            ai_insights = response_data.get('insights', [])
            
            # Validate and ensure we have proper insight structure
            validated_insights = []
            for insight in ai_insights[:3]:  # Limit to max 3 insights
                if isinstance(insight, dict) and all(key in insight for key in ['title', 'description']):
                    # Ensure required fields with better defaults
                    validated_insight = {
                        'title': str(insight.get('title', '📊 AI Analysis')),
                        'description': str(insight.get('description', 'Analysis completed')),
                        'points': insight.get('points', []) if isinstance(insight.get('points'), list) else [],
                        'type': str(insight.get('type', 'ai_analysis')),
                        'severity': str(insight.get('severity', 'medium')),
                        'recommendation': str(insight.get('recommendation', 'Review the analysis results'))
                    }
                    # Ensure points are strings
                    validated_insight['points'] = [str(p) for p in validated_insight['points']]
                    validated_insights.append(validated_insight)
            
            if validated_insights:
                logger.info(f"[AI_INSIGHTS] Successfully generated {len(validated_insights)} AI insights using {ai_response.model_used}")
                return validated_insights
            else:
                logger.warning("[AI_INSIGHTS] AI response didn't contain valid insights, using fallback")
                
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            logger.warning(f"[AI_INSIGHTS] Failed to parse AI response: {e}, response was: {ai_response.content[:200]}... Using fallback")
        
        # Fallback to statistical insights if AI parsing fails
        return await _generate_fallback_statistical_insights(comparison_result, estimated_analysis, actual_analysis)
        
    except Exception as e:
        logger.error(f"[AI_INSIGHTS] Error generating AI insights: {str(e)}")
        return await _generate_fallback_statistical_insights(comparison_result, estimated_analysis, actual_analysis)


async def _generate_fallback_statistical_insights(comparison_result, estimated_analysis, actual_analysis) -> List[Dict[str, Any]]:
    """Generate fallback statistical insights when AI is not available."""
    insights = []
    
    try:
        # Extract basic data
        performance_summary = comparison_result.performance_summary or {}
        individual_metrics_summary = performance_summary.get('individual_metrics_summary', {})
        individual_metrics = performance_summary.get('individual_metrics', [])
        
        total_analyzed = individual_metrics_summary.get('total_analyzed', 0) or len(comparison_result.critical_deviations or [])
        high_variance_count = individual_metrics_summary.get('high_variance_count', 0)
        overall_accuracy = max(0, 100 - abs(comparison_result.overall_variance))
        
        # Get specific metric details for targeted insights
        critical_metrics_details = []
        for dev in (comparison_result.critical_deviations or [])[:3]:
            metric_name = dev.get('metric_name') or dev.get('metric', 'Unknown')
            variance = abs(dev.get('variance_percentage', 0))
            # Try multiple fields to get actual values
            estimated_val = (
                dev.get('estimated_value') or 
                dev.get('estimated_total') or 
                dev.get('est_value') or 
                0
            )
            actual_val = (
                dev.get('actual_value') or 
                dev.get('actual_total') or 
                dev.get('act_value') or 
                0
            )
            business_impact = dev.get('business_impact', 'Unknown')
            critical_metrics_details.append({
                'name': metric_name,
                'variance': variance,
                'estimated': float(estimated_val),
                'actual': float(actual_val),
                'impact': business_impact
            })
        
        # Generate main statistical insight with specific details
        severity = 'low' if overall_accuracy >= 90 else 'medium' if overall_accuracy >= 75 else 'high'
        status = "OPTIMAL" if overall_accuracy >= 90 and high_variance_count == 0 else \
                 "MODERATE" if overall_accuracy >= 75 else "ATTENTION"
        
        # Create specific points based on actual metrics
        main_points = [
            f'Analyzed {total_analyzed} metrics with statistical variance detection',
            f'Overall forecast accuracy: {overall_accuracy:.1f}%',
            f'{high_variance_count} metrics exceed variance thresholds'
        ]
        
        # Add specific metric details to points
        if critical_metrics_details:
            for i, metric in enumerate(critical_metrics_details[:2]):
                main_points.append(
                    f'{metric["name"]}: {metric["variance"]:.1f}% variance '
                    f'(Est: {metric["estimated"]:,.0f}, Act: {metric["actual"]:,.0f})'
                )
        
        main_points.append(f'Trend alignment: {comparison_result.trend_alignment.replace("_", " ").title()}')
        
        # Generate specific recommendation based on actual data
        if high_variance_count > 0 and critical_metrics_details:
            top_metric = critical_metrics_details[0]
            specific_rec = (
                f'Priority Action: Focus on {top_metric["name"]} with {top_metric["variance"]:.1f}% variance. '
                f'Target: Reduce variance to <10% within 30 days through model recalibration.'
            )
        else:
            specific_rec = 'Continue monitoring with weekly variance reports. Set alerts for metrics exceeding 15% threshold.'
        
        insights.append({
            'title': f'📊 Statistical Analysis: {status} Performance',
            'description': f'Statistical analysis of {total_analyzed} metrics shows {overall_accuracy:.1f}% forecast accuracy with {high_variance_count} metrics requiring attention.',
            'points': main_points,
            'type': 'statistical_analysis',
            'severity': severity,
            'recommendation': specific_rec
        })
        
        # Add detailed breakdown if there are issues
        if high_variance_count > 0 and total_analyzed > 0 and critical_metrics_details:
            # Build specific action points
            action_points = []
            
            for i, metric in enumerate(critical_metrics_details[:3]):
                if metric['variance'] > 25:
                    action = f'{metric["name"]}: Implement exponential smoothing with alpha=0.3'
                elif metric['variance'] > 15:
                    action = f'{metric["name"]}: Apply moving average (MA-7) for trend stabilization'
                else:
                    action = f'{metric["name"]}: Minor adjustment - increase sample size by 20%'
                action_points.append(action)
            
            # Add timeline and monitoring recommendations
            action_points.extend([
                f'Set up automated alerts for variances exceeding 15% (currently {high_variance_count} metrics)',
                'Schedule weekly model performance review starting next Monday',
                'Target: Achieve <10% variance for all critical metrics within 45 days'
            ])
            
            insights.append({
                'title': f'⚠️ Action Plan for {len(critical_metrics_details)} High-Variance Metrics',
                'description': f'Specific corrective actions required for {high_variance_count} metrics with variance exceeding acceptable thresholds.',
                'points': action_points,
                'type': 'variance_analysis',
                'severity': 'high' if high_variance_count > total_analyzed // 2 else 'medium',
                'recommendation': f'Immediate: Start with {critical_metrics_details[0]["name"]} ({critical_metrics_details[0]["variance"]:.1f}% variance) using suggested technique'
            })
        
        # Add performance optimization insight if accuracy is moderate
        if 60 < overall_accuracy < 85 and individual_metrics:
            # Calculate specific improvement potential
            improvement_target = min(90, overall_accuracy + 15)
            timeline_days = 30 if overall_accuracy > 75 else 45
            
            optimization_points = [
                f'Current accuracy: {overall_accuracy:.1f}% - Target: {improvement_target:.1f}%',
                f'Improvement potential: {improvement_target - overall_accuracy:.1f}% over {timeline_days} days',
                'Quick wins: Address top 3 high-variance metrics first (80% of impact)',
                'Implement ensemble forecasting combining 3 models (ARIMA, XGBoost, Prophet)',
                f'Expected ROI: {(improvement_target - overall_accuracy) * 2:.0f}% reduction in forecast errors'
            ]
            
            insights.append({
                'title': '🎯 Performance Optimization Roadmap',
                'description': f'Structured plan to improve forecast accuracy from {overall_accuracy:.1f}% to {improvement_target:.1f}% within {timeline_days} days.',
                'points': optimization_points,
                'type': 'optimization_plan',
                'severity': 'medium',
                'recommendation': f'Week 1: Implement suggested techniques for top 3 metrics. Week 2-3: Deploy ensemble model. Week 4+: Fine-tune and monitor.'
            })
        
        logger.info(f"[FALLBACK_INSIGHTS] Generated {len(insights)} specific statistical insights")
        return insights
        
    except Exception as e:
        logger.error(f"[FALLBACK_INSIGHTS] Error generating fallback insights: {str(e)}")
        # Return minimal insight
        return [{
            'title': '📊 Analysis Complete',
            'description': f'Statistical comparison completed. Forecast accuracy: {max(0, 100 - abs(comparison_result.overall_variance)):.1f}%',
            'points': [
                f'Overall variance: {abs(comparison_result.overall_variance):.1f}%',
                f'Trend alignment: {comparison_result.trend_alignment.replace("_", " ").title()}'
            ],
            'type': 'basic_analysis',
            'severity': 'medium',
            'recommendation': 'Review detailed analysis for specific recommendations'
        }]

async def generate_comprehensive_comparison_kpis(comparison_result, estimated_analysis, actual_analysis) -> List[Dict[str, Any]]:
    """Generate comprehensive KPIs leveraging deep analysis results from SimpleIntelligentComparisonAgent."""
    kpis = []
    
    try:
        # Extract detailed data from performance summary
        performance_summary = comparison_result.performance_summary or {}
        individual_metrics_summary = performance_summary.get('individual_metrics_summary', {})
        trend_health_summary = performance_summary.get('trend_health_summary', {})
        business_impact_summary = performance_summary.get('business_impact_summary', {})
        missing_metrics_summary = performance_summary.get('missing_metrics_summary', {})
        
        # Extract specific metrics for KPI calculation
        total_analyzed = individual_metrics_summary.get('total_analyzed', 0)
        high_variance_count = individual_metrics_summary.get('high_variance_count', 0)
        avg_accuracy = individual_metrics_summary.get('average_accuracy_score', 0)
        avg_correlation = individual_metrics_summary.get('average_correlation', 0)
        
        # KPI 1: Overall Forecast Accuracy (from deep analysis)
        accuracy = avg_accuracy if avg_accuracy > 0 else max(0, 100 - abs(comparison_result.overall_variance))
        kpis.append({
            "id": "overall_forecast_accuracy",
            "title": "Forecast Accuracy",
            "value": f"{accuracy:.1f}%",
            "subtitle": f"Across {total_analyzed} metrics",
            "trend": "up" if accuracy > 80 else "down",
            "color": "green" if accuracy > 85 else "orange" if accuracy > 70 else "red",
            "description": "AI-calculated precision of estimates vs actual results using MAPE analysis"
        })
        
        # KPI 2: Average Absolute Variance (from enhanced analysis)
        avg_variance = abs(comparison_result.overall_variance)
        kpis.append({
            "id": "average_variance",
            "title": "Average Variance",
            "value": f"{avg_variance:.1f}%",
            "subtitle": "Mean deviation",
            "trend": "down" if avg_variance < 10 else "up",
            "color": "green" if avg_variance < 8 else "orange" if avg_variance < 15 else "red",
            "description": "Mean absolute percentage error across all analyzed metrics"
        })
        
        # KPI 3: Trend Alignment Score (from correlation analysis) - FIXED CONTRADICTION
        # Only show trend alignment if we actually analyzed metrics with trend data
        metrics_with_trends = trend_health_summary.get('summary', {}).get('metrics_analyzed', 0)
        if metrics_with_trends > 0 and avg_correlation > 0:
            # We have actual trend correlation data
            trend_score = avg_correlation * 100
            trend_subtitle = comparison_result.trend_alignment.replace('_', ' ').title()
            trend_description = f"Correlation strength between estimated and actual trends across {metrics_with_trends} metrics"
        else:
            # No trend analysis was possible - show "Not Available"
            trend_score = None
            trend_subtitle = "Not Available"
            trend_description = "No time series or chronological fields detected to compare patterns across time"
        
        kpis.append({
            "id": "trend_alignment_score",
            "title": "Trend Alignment",
            "value": f"{trend_score:.1f}%" if trend_score is not None else "N/A",
            "subtitle": trend_subtitle,
            "trend": "up" if trend_score and trend_score > 75 else "neutral" if trend_score is None else "down",
            "color": "green" if trend_score and trend_score > 80 else "orange" if trend_score and trend_score > 60 else "gray" if trend_score is None else "red",
            "description": trend_description
        })
        
        # KPI 4: Critical Issues Count (from business impact analysis)
        critical_count = business_impact_summary.get('immediate_attention_required', 0) or len([d for d in comparison_result.critical_deviations if d.get("severity") == "critical"])
        kpis.append({
            "id": "critical_issues",
            "title": "Critical Issues",
            "value": str(critical_count),
            "subtitle": "Need immediate action",
            "trend": "down" if critical_count == 0 else "up",
            "color": "green" if critical_count == 0 else "orange" if critical_count < 3 else "red",
            "description": "High-impact metrics requiring immediate attention and model recalibration"
        })
        
        # KPI 5: Data Alignment Quality (from column mapping analysis) - FIXED
        mapped_columns = total_analyzed
        # Use the column counts from the performance summary if available
        estimated_cols = performance_summary.get('estimated_columns_count', mapped_columns)
        actual_cols = performance_summary.get('actual_columns_count', mapped_columns)
        
        # **TRANSPARENCY**: Log which columns were mapped for clarity
        logger.info(f"[DATA_ALIGNMENT] Column counts - Estimated: {estimated_cols}, Actual: {actual_cols}, Mapped: {mapped_columns}")
        
        # Calculate alignment based on the smaller dataset (conservative approach)
        # Initialize alignment_quality as numeric to avoid None comparisons
        alignment_quality = 0.0
        
        if estimated_cols > 0 and actual_cols > 0:
            total_possible = min(estimated_cols, actual_cols)
            alignment_quality = (mapped_columns / total_possible * 100) if total_possible > 0 else 0.0
            logger.info(f"[DATA_ALIGNMENT] Alignment calculation: {mapped_columns}/{total_possible} = {alignment_quality:.1f}%")
        else:
            total_possible = max(estimated_cols, actual_cols)  # Define total_possible in else branch
            alignment_quality = 100.0 if mapped_columns > 0 else 0.0
        kpis.append({
            "id": "data_alignment_quality",
            "title": "Data Alignment Quality",
            "value": f"{alignment_quality:.1f}%",
            "subtitle": f"{mapped_columns}/{total_possible if total_possible is not None else 0} columns aligned",
            "trend": "up" if alignment_quality and alignment_quality > 85 else "down",
            "color": "green" if alignment_quality and alignment_quality > 90 else "orange" if alignment_quality and alignment_quality > 75 else "red",
            "description": "Success rate of semantic column matching and data alignment"
        })
        
        # KPI 6: Missing Metrics Alert (from missing metrics analysis)
        missing_count = missing_metrics_summary.get('total_missing_count', 0) if missing_metrics_summary else 0
        high_impact_missing = missing_metrics_summary.get('high_impact_count', 0) if missing_metrics_summary else 0
        kpis.append({
            "id": "missing_metrics_alert",
            "title": "Missing Metrics",
            "value": f"{missing_count}",
            "subtitle": f"({high_impact_missing} critical)",
            "trend": "down" if missing_count == 0 else "up",
            "color": "green" if missing_count == 0 else "orange" if high_impact_missing == 0 else "red",
            "description": "Metrics present in one dataset but missing from the other"
        })
        
        # KPI 7: Forecast Health Score (composite metric)
        health_components = []
        if accuracy > 0:
            health_components.append(accuracy)
        if avg_variance is not None and avg_variance < 100:
            # Normalize variance to 0-100 scale and invert it
            normalized_variance = max(0.0, min(100.0, 100.0 - float(avg_variance)))
            health_components.append(normalized_variance)
        if trend_score is not None and trend_score > 0:
            # Ensure trend score is also on 0-100 scale
            normalized_trend = min(100.0, float(trend_score))
            health_components.append(normalized_trend)
        
        health_score = sum(health_components) / len(health_components) if health_components else 0.0
        kpis.append({
            "id": "forecast_health_score",
            "title": "Forecast Health Score",
            "value": f"{health_score:.1f}%",
            "subtitle": "Composite performance",
            "trend": "up" if health_score > 75 else "down",
            "color": "green" if health_score > 80 else "orange" if health_score > 65 else "red",
            "description": "Composite score combining accuracy, variance, and trend alignment"
        })
        
        # KPI 8: High Accuracy Metrics Count (metric distribution)
        high_accuracy_count = total_analyzed - high_variance_count  # Simplified calculation
        kpis.append({
            "id": "high_accuracy_metrics",
            "title": "High Accuracy Metrics",
            "value": f"{high_accuracy_count}/{total_analyzed}",
            "subtitle": f"{(high_accuracy_count/max(1, total_analyzed)*100):.0f}% of total",
            "trend": "up" if high_accuracy_count > total_analyzed * 0.7 else "down",
            "color": "green" if high_accuracy_count > total_analyzed * 0.8 else "orange" if high_accuracy_count > total_analyzed * 0.6 else "red",
            "description": "Number of metrics performing above 80% accuracy threshold"
        })
        
        logger.info(f"[COMPREHENSIVE_KPIS] Generated {len(kpis)} comprehensive KPIs with deep analysis data")
        return kpis
        
    except Exception as e:
        logger.error(f"[COMPREHENSIVE_KPIS] Error generating comprehensive KPIs: {str(e)}")
        logger.error(f"[COMPREHENSIVE_KPIS] Traceback: {traceback.format_exc()}")
        return [
            {
                "id": "basic_accuracy",
                "title": "Forecast Accuracy",
                "value": f"{max(0, 100 - abs(comparison_result.overall_variance)):.1f}%",
                "subtitle": "Basic calculation",
                "trend": "up" if comparison_result.overall_variance < 10 else "down",
                "color": "green" if comparison_result.overall_variance < 10 else "orange",
                "description": "Basic accuracy metric from overall variance"
            }
        ]

# Helper functions
async def read_file_to_dataframe(
    contents: bytes, 
    filename: str, 
    sheet_name: Optional[str] = None
) -> pd.DataFrame:
    """Read file contents to pandas DataFrame with robust error handling."""
    try:
        logger.info(f"[COMPARISON] Reading file: {filename}, size: {len(contents)} bytes")
        
        if filename.lower().endswith('.csv'):
            try:
                # Try UTF-8 first
                content_str = contents.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    # Fallback to latin-1
                    content_str = contents.decode('latin-1')
                except UnicodeDecodeError:
                    # Final fallback to utf-8 with errors ignored
                    content_str = contents.decode('utf-8', errors='ignore')
            
            df = pd.read_csv(io.StringIO(content_str))
            
        elif filename.lower().endswith(('.xlsx', '.xls')):
            try:
                if sheet_name:
                    df = pd.read_excel(io.BytesIO(contents), sheet_name=sheet_name, engine='openpyxl')
                else:
                    df = pd.read_excel(io.BytesIO(contents), engine='openpyxl')
            except Exception as excel_error:
                logger.warning(f"[COMPARISON] OpenPyXl failed, trying xlrd: {str(excel_error)}")
                # Fallback to xlrd for older Excel files
                try:
                    if sheet_name:
                        df = pd.read_excel(io.BytesIO(contents), sheet_name=sheet_name, engine='xlrd')
                    else:
                        df = pd.read_excel(io.BytesIO(contents), engine='xlrd')
                except Exception as xlrd_error:
                    logger.error(f"[COMPARISON] Both engines failed. OpenPyXl: {str(excel_error)}, xlrd: {str(xlrd_error)}")
                    raise ValueError(f"Failed to read Excel file with both engines. Please check the file format and sheet names.")
        else:
            raise ValueError(f"Unsupported file format: {filename}. Supported formats: CSV, Excel (.xlsx, .xls)")
        
        # Validate the dataframe
        if df.empty:
            raise ValueError(f"File {filename} is empty or contains no data")
        
        if len(df.columns) == 0:
            raise ValueError(f"File {filename} has no columns")
        
        # Clean column names to ensure they're JSON serializable
        df.columns = [str(col).strip() for col in df.columns]
        
        logger.info(f"[COMPARISON] Successfully read file: {filename}, shape: {df.shape}")
        logger.info(f"[COMPARISON] Columns: {list(df.columns)}")
        
        return df
        
    except Exception as e:
        error_msg = f"Failed to read file {filename}: {str(e)}"
        logger.error(f"[COMPARISON] {error_msg}")
        logger.error(f"[COMPARISON] Traceback: {traceback.format_exc()}")
        raise ValueError(error_msg)

async def get_excel_sheet_names(contents: bytes, filename: str) -> List[str]:
    """Get list of sheet names from an Excel file."""
    try:
        logger.info(f"[COMPARISON] Getting sheet names from: {filename}")
        
        # Try openpyxl first
        try:
            excel_file = pd.ExcelFile(io.BytesIO(contents), engine='openpyxl')
            sheet_names = excel_file.sheet_names
            logger.info(f"[COMPARISON] Found sheets with openpyxl: {sheet_names}")
            return sheet_names
        except Exception as openpyxl_error:
            logger.warning(f"[COMPARISON] OpenpyXl failed for sheet detection: {str(openpyxl_error)}")
            
            # Fallback to xlrd
            try:
                excel_file = pd.ExcelFile(io.BytesIO(contents), engine='xlrd')
                sheet_names = excel_file.sheet_names
                logger.info(f"[COMPARISON] Found sheets with xlrd: {sheet_names}")
                return sheet_names
            except Exception as xlrd_error:
                logger.error(f"[COMPARISON] Both engines failed for sheet detection. OpenpyXl: {str(openpyxl_error)}, xlrd: {str(xlrd_error)}")
                raise ValueError(f"Failed to detect sheet names with both engines.")
        
    except Exception as e:
        error_msg = f"Failed to get sheet names from {filename}: {str(e)}"
        logger.error(f"[COMPARISON] {error_msg}")
        raise ValueError(error_msg)

def find_best_sheet_match(available_sheets: List[str], target_type: str) -> Optional[str]:
    """Find the best matching sheet name for estimated or actual data."""
    target_type = target_type.lower()
    
    # Define matching patterns for each type
    if target_type == "estimated":
        patterns = ["estimated", "estimate", "forecast", "planned", "budget", "target", "expected"]
    elif target_type == "actual":
        patterns = ["actual", "real", "result", "outcome", "performance", "achieved"]
    else:
        return None
    
    # Try exact matches first
    for sheet in available_sheets:
        sheet_lower = sheet.lower()
        for pattern in patterns:
            if pattern in sheet_lower:
                logger.info(f"[COMPARISON] Found {target_type} sheet match: {sheet}")
                return sheet
    
    # If no pattern match, return None (user will need to specify)
    logger.warning(f"[COMPARISON] No automatic {target_type} sheet match found in: {available_sheets}")
    return None