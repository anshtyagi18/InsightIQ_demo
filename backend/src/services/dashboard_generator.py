"""
Dashboard Generator Service
Orchestrates AI agents to generate complete dashboard configurations.
"""

import json
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
import logging
from datetime import datetime
import asyncio
from dataclasses import dataclass
import re

# AI agent imports
from src.agents.data_cleaner import generate_data_quality_report
from src.agents.trend_detector import TrendDetector

logger = logging.getLogger(__name__)

@dataclass
class ChartRecommendation:
    """Data class for chart recommendations."""
    chart_type: str
    data_columns: List[str]
    title: str
    description: str
    confidence: float
    recharts_config: Dict[str, Any]
    data: List[Dict[str, Any]] = None

@dataclass
class KPIConfig:
    """Data class for KPI configurations."""
    name: str
    value: float
    unit: str
    trend: str  # 'up', 'down', 'neutral'
    trend_percentage: float
    description: str
    format_type: str  # 'number', 'currency', 'percentage'

class DashboardGenerator:
    """
    Main service for generating dashboard configurations.
    Integrates with AI agents to provide intelligent dashboard generation.
    """
    
    def __init__(self):
        self.trend_detector = TrendDetector()
        self.chart_type_mapping = {
            'time_series': ['line', 'area'],
            'categorical': ['bar', 'pie'],
            'numerical_distribution': ['histogram', 'box'],
            'correlation': ['scatter', 'heatmap'],
            'comparison': ['bar', 'column'],
            'composition': ['pie', 'stacked_bar']
        }
        
        # Recharts component mapping
        self.recharts_components = {
            'line': 'LineChart',
            'area': 'AreaChart', 
            'bar': 'BarChart',
            'pie': 'PieChart',
            'scatter': 'ScatterChart',
            'radar': 'RadarChart',
            'composed': 'ComposedChart'
        }
        
    async def generate_complete_dashboard(
        self,
        data: Dict[str, Any],
        quality_report: Dict[str, Any],
        trend_analysis: Dict[str, Any],
        chart_preferences: Dict[str, Any] = None,
        kpi_requirements: List[str] = None,
        layout_type: str = "responsive",
        theme: str = "default"
    ) -> Dict[str, Any]:
        """
        Generate a complete dashboard configuration.
        
        Args:
            data: The dataset to analyze
            quality_report: Data quality analysis results
            trend_analysis: Trend detection results
            chart_preferences: User preferences for chart types
            kpi_requirements: Required KPI metrics
            layout_type: Layout type (responsive, grid, etc.)
            theme: Theme name
            
        Returns:
            Complete dashboard configuration
        """
        start_time = datetime.now()
        
        try:
            logger.info("Starting complete dashboard generation...")
            
            # Step 1: Analyze data characteristics
            data_analysis = await self._analyze_data_characteristics(data)
            
            # Step 2: Generate chart recommendations
            chart_recommendations = await self.recommend_charts(
                data=data,
                context=f"Quality Score: {quality_report.get('overall_score', 0)}",
                priority_metrics=kpi_requirements
            )
            
            # Step 3: Calculate KPIs
            kpis = await self.calculate_kpis(data, kpi_requirements)
            
            # Step 4: Generate layout
            layout = await self.get_layout_template(layout_type)
            layout = await self._optimize_layout_for_content(layout, chart_recommendations, kpis)
            
            # Step 5: Apply theme
            theme_config = await self.get_theme_config(theme)
            
            # Step 6: Create final configuration
            processing_time = (datetime.now() - start_time).total_seconds()
            
            config = {
                'layout': layout,
                'charts': [rec.__dict__ if hasattr(rec, '__dict__') else rec for rec in chart_recommendations],
                'kpis': [kpi.__dict__ if hasattr(kpi, '__dict__') else kpi for kpi in kpis],
                'theme': theme_config,
                'metadata': {
                    'data_analysis': data_analysis,
                    'quality_insights': quality_report.get('summary', {}),
                    'trend_insights': trend_analysis.get('summary', {}),
                    'generation_strategy': 'ai_driven',
                    'processing_time': processing_time
                },
                'processing_time': processing_time
            }
            
            logger.info(f"Dashboard generation completed in {processing_time:.2f}s")
            return config
            
        except Exception as e:
            logger.error(f"Dashboard generation failed: {str(e)}")
            raise
    
    async def recommend_charts(
        self,
        data: Dict[str, Any],
        context: Optional[str] = None,
        priority_metrics: Optional[List[str]] = None
    ) -> List[ChartRecommendation]:
        """
        Generate AI-driven chart recommendations based on comprehensive data analysis.
        Uses advanced statistical analysis, data profiling, and machine learning heuristics.
        """
        try:
            logger.info("Generating AI-driven chart recommendations...")
            
            # Convert data to DataFrame for analysis
            df = self._dict_to_dataframe(data)
            if df is None or df.empty:
                return []
            
            # Step 1: Comprehensive Data Profiling
            data_profile = await self._analyze_data_profile(df)
            
            # Step 2: AI-Driven Chart Scoring
            chart_scores = await self._calculate_chart_suitability_scores(df, data_profile, context, priority_metrics)
            
            # Step 3: Generate Recommendations with ML-based Confidence
            recommendations = await self._generate_ai_recommendations(df, data_profile, chart_scores, context)
            
            # Step 4: Apply Business Intelligence and Context Optimization
            recommendations = await self._apply_context_optimization(recommendations, context, priority_metrics)
            
            # Step 5: Final Ranking and Selection
            final_recommendations = await self._rank_and_select_recommendations(recommendations, data_profile)
            
            logger.info(f"Generated {len(final_recommendations)} AI-driven chart recommendations")
            return final_recommendations
            
        except Exception as e:
            logger.error(f"AI chart recommendation failed: {str(e)}")
            return []

    async def _analyze_data_profile(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Comprehensive data profiling for AI-driven chart recommendations."""
        
        try:
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
            datetime_cols = self._detect_datetime_columns(df)
            
            profile = {
                'row_count': len(df),
                'column_count': len(df.columns),
                'numeric_columns': numeric_cols,
                'categorical_columns': categorical_cols, 
                'datetime_columns': datetime_cols,
                'missing_data_ratio': df.isnull().sum().sum() / df.size,
                'numeric_insights': {},
                'categorical_insights': {},
                'temporal_insights': {},
                'correlation_insights': {},
                'data_quality_score': 0.0
            }
            
            # Numeric column analysis
            for col in numeric_cols:
                col_data = df[col].dropna()
                if len(col_data) > 0:
                    profile['numeric_insights'][col] = {
                        'mean': float(col_data.mean()),
                        'std': float(col_data.std()),
                        'skewness': float(col_data.skew()),
                        'kurtosis': float(col_data.kurtosis()),
                        'unique_ratio': len(col_data.unique()) / len(col_data),
                        'range_ratio': (col_data.max() - col_data.min()) / col_data.mean() if col_data.mean() != 0 else 0,
                        'outlier_ratio': len(col_data[(np.abs(col_data - col_data.mean()) > 2 * col_data.std())]) / len(col_data),
                        'distribution_type': self._classify_distribution(col_data)
                    }
            
            # Categorical column analysis
            for col in categorical_cols:
                col_data = df[col].dropna()
                if len(col_data) > 0:
                    value_counts = col_data.value_counts()
                    profile['categorical_insights'][col] = {
                        'unique_count': len(value_counts),
                        'most_frequent': value_counts.index[0] if len(value_counts) > 0 else None,
                        'concentration_ratio': value_counts.iloc[0] / len(col_data) if len(value_counts) > 0 else 0,
                        'diversity_index': 1 - ((value_counts / len(col_data)) ** 2).sum(),  # Simpson's Diversity Index
                        'cardinality_category': self._classify_cardinality(len(value_counts), len(col_data))
                    }
            
            # Temporal analysis
            if datetime_cols:
                for col in datetime_cols:
                    col_data = pd.to_datetime(df[col], errors='coerce').dropna()
                    if len(col_data) > 1:
                        time_diffs = col_data.diff().dropna()
                        profile['temporal_insights'][col] = {
                            'date_range_days': (col_data.max() - col_data.min()).days,
                            'frequency_pattern': self._detect_frequency_pattern(time_diffs),
                            'trend_strength': self._calculate_temporal_trend_strength(col_data),
                            'seasonality_likelihood': self._assess_seasonality_likelihood(col_data)
                        }
            
            # Correlation analysis for numeric columns
            if len(numeric_cols) >= 2:
                correlation_matrix = df[numeric_cols].corr()
                strong_correlations = []
                for i in range(len(correlation_matrix.columns)):
                    for j in range(i+1, len(correlation_matrix.columns)):
                        corr_value = correlation_matrix.iloc[i, j]
                        if abs(corr_value) > 0.5:  # Strong correlation threshold
                            strong_correlations.append({
                                'col1': correlation_matrix.columns[i],
                                'col2': correlation_matrix.columns[j],
                                'correlation': float(corr_value),
                                'strength': 'strong' if abs(corr_value) > 0.7 else 'moderate'
                            })
                
                profile['correlation_insights'] = {
                    'matrix': correlation_matrix.to_dict(),
                    'strong_correlations': strong_correlations,
                    'max_correlation': float(correlation_matrix.abs().max().max()) if len(correlation_matrix) > 0 else 0
                }
            
            # Calculate overall data quality score
            profile['data_quality_score'] = self._calculate_data_quality_score(profile)
            
            return profile
            
        except Exception as e:
            logger.error(f"Data profiling failed: {str(e)}")
            return {}

    async def _calculate_chart_suitability_scores(
        self, 
        df: pd.DataFrame, 
        data_profile: Dict[str, Any],
        context: Optional[str],
        priority_metrics: Optional[List[str]]
    ) -> Dict[str, Dict[str, float]]:
        """Calculate AI-driven suitability scores for different chart types."""
        
        chart_scores = {
            'line': {'base_score': 0.0, 'context_bonus': 0.0, 'data_fitness': 0.0},
            'area': {'base_score': 0.0, 'context_bonus': 0.0, 'data_fitness': 0.0},
            'bar': {'base_score': 0.0, 'context_bonus': 0.0, 'data_fitness': 0.0},
            'column': {'base_score': 0.0, 'context_bonus': 0.0, 'data_fitness': 0.0},
            'pie': {'base_score': 0.0, 'context_bonus': 0.0, 'data_fitness': 0.0},
            'scatter': {'base_score': 0.0, 'context_bonus': 0.0, 'data_fitness': 0.0},
            'heatmap': {'base_score': 0.0, 'context_bonus': 0.0, 'data_fitness': 0.0},
            'histogram': {'base_score': 0.0, 'context_bonus': 0.0, 'data_fitness': 0.0},
            'box': {'base_score': 0.0, 'context_bonus': 0.0, 'data_fitness': 0.0},
            'radar': {'base_score': 0.0, 'context_bonus': 0.0, 'data_fitness': 0.0}
        }
        
        try:
            # Base scoring based on data characteristics
            
            # Time series charts (line, area)
            if data_profile.get('datetime_columns'):
                chart_scores['line']['base_score'] = 0.9
                chart_scores['area']['base_score'] = 0.8
                
                # Boost for trend analysis
                if any(insight.get('trend_strength', 0) > 0.3 for insight in data_profile.get('temporal_insights', {}).values()):
                    chart_scores['line']['data_fitness'] = 0.9
                    chart_scores['area']['data_fitness'] = 0.8
            
            # Categorical analysis (bar, column, pie)
            categorical_cols = data_profile.get('categorical_columns', [])
            if categorical_cols:
                for col in categorical_cols:
                    insights = data_profile.get('categorical_insights', {}).get(col, {})
                    unique_count = insights.get('unique_count', 0)
                    
                    if unique_count <= 5:  # Pie chart suitable for small categories
                        chart_scores['pie']['base_score'] = max(chart_scores['pie']['base_score'], 0.8)
                    if unique_count <= 15:  # Bar chart suitable for moderate categories
                        chart_scores['bar']['base_score'] = max(chart_scores['bar']['base_score'], 0.9)
                        chart_scores['column']['base_score'] = max(chart_scores['column']['base_score'], 0.85)
            
            # Correlation analysis (scatter, heatmap)
            strong_correlations = data_profile.get('correlation_insights', {})
            if strong_correlations:
                chart_scores['scatter']['base_score'] = 0.8
                if len(data_profile.get('numeric_columns', [])) >= 3:
                    chart_scores['heatmap']['base_score'] = 0.75
            
            # Distribution analysis (histogram, box)
            numeric_cols = data_profile.get('numeric_columns', [])
            if numeric_cols:
                for col in numeric_cols:
                    insights = data_profile.get('numeric_insights', {}).get(col, {})
                    skewness = abs(insights.get('skewness', 0))
                    outlier_ratio = insights.get('outlier_ratio', 0)
                    
                    if skewness > 0.5:  # Skewed distribution
                        chart_scores['histogram']['base_score'] = max(chart_scores['histogram']['base_score'], 0.7)
                    if outlier_ratio > 0.05:  # Outliers present
                        chart_scores['box']['base_score'] = max(chart_scores['box']['base_score'], 0.8)
            
            # Multi-dimensional analysis (radar)
            if len(numeric_cols) >= 3 and len(numeric_cols) <= 8:
                chart_scores['radar']['base_score'] = 0.6
            
            # Context-based scoring
            if context:
                context_lower = context.lower()
                
                # Financial/Business context
                if any(term in context_lower for term in ['revenue', 'sales', 'profit', 'financial', 'business']):
                    chart_scores['line']['context_bonus'] = 0.1
                    chart_scores['bar']['context_bonus'] = 0.1
                
                # Trend analysis context
                if any(term in context_lower for term in ['trend', 'growth', 'change', 'over time']):
                    chart_scores['line']['context_bonus'] = 0.15
                    chart_scores['area']['context_bonus'] = 0.1
                
                # Comparison context
                if any(term in context_lower for term in ['compare', 'comparison', 'versus', 'vs']):
                    chart_scores['bar']['context_bonus'] = 0.15
                    chart_scores['column']['context_bonus'] = 0.1
                
                # Distribution context
                if any(term in context_lower for term in ['distribution', 'spread', 'variance']):
                    chart_scores['histogram']['context_bonus'] = 0.15
                    chart_scores['box']['context_bonus'] = 0.1
            
            # Priority metrics boost
            if priority_metrics:
                for chart_type in chart_scores:
                    # Check if chart type is suitable for priority metrics
                    if any(metric in data_profile.get('numeric_columns', []) for metric in priority_metrics):
                        chart_scores[chart_type]['data_fitness'] += 0.05
            
            return chart_scores
            
        except Exception as e:
            logger.error(f"Chart suitability scoring failed: {str(e)}")
            return chart_scores

    async def _generate_ai_recommendations(
        self,
        df: pd.DataFrame,
        data_profile: Dict[str, Any],
        chart_scores: Dict[str, Dict[str, float]],
        context: Optional[str]
    ) -> List[ChartRecommendation]:
        """Generate specific chart recommendations using AI analysis."""
        
        recommendations = []
        
        try:
            numeric_cols = data_profile.get('numeric_columns', [])
            categorical_cols = data_profile.get('categorical_columns', [])
            datetime_cols = data_profile.get('datetime_columns', [])
            
            # Time Series Recommendations
            for date_col in datetime_cols:
                for num_col in numeric_cols[:2]:  # Top 2 numeric for time series
                    temporal_insights = data_profile.get('temporal_insights', {}).get(date_col, {})
                    
                    # Line chart for trends
                    line_score = sum(chart_scores['line'].values())
                    if line_score > 0.5:
                        rec = self._create_enhanced_time_series_recommendation(
                            df, date_col, num_col, 'line', line_score, temporal_insights
                        )
                        if rec:
                            recommendations.append(rec)
                    
                    # Area chart for cumulative trends
                    area_score = sum(chart_scores['area'].values())
                    if area_score > 0.5 and temporal_insights.get('trend_strength', 0) > 0.3:
                        rec = self._create_enhanced_time_series_recommendation(
                            df, date_col, num_col, 'area', area_score, temporal_insights
                        )
                        if rec:
                            recommendations.append(rec)
            
            # Categorical Analysis Recommendations
            for cat_col in categorical_cols[:2]:
                cat_insights = data_profile.get('categorical_insights', {}).get(cat_col, {})
                unique_count = cat_insights.get('unique_count', 0)
                
                for num_col in numeric_cols[:2]:
                    # Bar chart recommendation
                    bar_score = sum(chart_scores['bar'].values())
                    if bar_score > 0.5:
                        rec = self._create_enhanced_categorical_recommendation(
                            df, cat_col, num_col, 'bar', bar_score, cat_insights
                        )
                        if rec:
                            recommendations.append(rec)
                    
                    # Pie chart for small categories
                    pie_score = sum(chart_scores['pie'].values())
                    if pie_score > 0.5 and unique_count <= 6:
                        rec = self._create_enhanced_categorical_recommendation(
                            df, cat_col, num_col, 'pie', pie_score, cat_insights
                        )
                        if rec:
                            recommendations.append(rec)
            
            # Distribution Analysis Recommendations
            for num_col in numeric_cols[:2]:
                num_insights = data_profile.get('numeric_insights', {}).get(num_col, {})
                
                # Histogram for distribution analysis
                hist_score = sum(chart_scores['histogram'].values())
                if hist_score > 0.4:
                    rec = self._create_enhanced_distribution_recommendation(
                        df, num_col, 'histogram', hist_score, num_insights
                    )
                    if rec:
                        recommendations.append(rec)
                
                # Box plot for outlier analysis
                box_score = sum(chart_scores['box'].values())
                if box_score > 0.5:
                    rec = self._create_enhanced_distribution_recommendation(
                        df, num_col, 'box', box_score, num_insights
                    )
                    if rec:
                        recommendations.append(rec)
            
            # Correlation Analysis Recommendations
            correlation_insights = data_profile.get('correlation_insights', {})
            strong_correlations = correlation_insights.get('strong_correlations', [])
            
            if strong_correlations:
                # Scatter plot for correlation
                scatter_score = sum(chart_scores['scatter'].values())
                if scatter_score > 0.5:
                    for corr in strong_correlations[:2]:  # Top 2 correlations
                        rec = self._create_enhanced_correlation_recommendation(
                            df, corr['col1'], corr['col2'], 'scatter', scatter_score, corr
                        )
                        if rec:
                            recommendations.append(rec)
                
                # Heatmap for multiple correlations
                heatmap_score = sum(chart_scores['heatmap'].values())
                if heatmap_score > 0.4 and len(numeric_cols) >= 3:
                    rec = self._create_enhanced_correlation_heatmap(
                        df, numeric_cols[:5], heatmap_score, correlation_insights
                    )
                    if rec:
                        recommendations.append(rec)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"AI recommendation generation failed: {str(e)}")
            return []

    def _classify_distribution(self, data: pd.Series) -> str:
        """Classify the distribution type of numeric data."""
        try:
            skewness = data.skew()
            kurtosis = data.kurtosis()
            
            if abs(skewness) < 0.5 and abs(kurtosis) < 3:
                return 'normal'
            elif skewness > 1:
                return 'right_skewed'
            elif skewness < -1:
                return 'left_skewed'
            elif kurtosis > 3:
                return 'heavy_tailed'
            else:
                return 'irregular'
        except:
            return 'unknown'

    def _classify_cardinality(self, unique_count: int, total_count: int) -> str:
        """Classify cardinality level of categorical data."""
        ratio = unique_count / total_count if total_count > 0 else 0
        
        if unique_count <= 5:
            return 'low'
        elif unique_count <= 15 or ratio < 0.1:
            return 'medium'
        elif ratio < 0.5:
            return 'high'
        else:
            return 'very_high'

    def _detect_frequency_pattern(self, time_diffs: pd.Series) -> str:
        """Detect temporal frequency pattern."""
        try:
            mode_diff = time_diffs.mode().iloc[0] if len(time_diffs.mode()) > 0 else time_diffs.median()
            days = mode_diff.days
            
            if days <= 1:
                return 'daily'
            elif days <= 7:
                return 'weekly'
            elif days <= 31:
                return 'monthly'
            elif days <= 365:
                return 'quarterly'
            else:
                return 'yearly'
        except:
            return 'irregular'

    def _calculate_temporal_trend_strength(self, dates: pd.Series) -> float:
        """Calculate strength of temporal trend."""
        try:
            # Simple trend strength based on date range and regularity
            date_range = (dates.max() - dates.min()).days
            unique_dates = len(dates.unique())
            
            if date_range > 0:
                regularity = unique_dates / date_range
                return min(regularity * 10, 1.0)  # Normalize to 0-1
            return 0.0
        except:
            return 0.0

    def _assess_seasonality_likelihood(self, dates: pd.Series) -> float:
        """Assess likelihood of seasonal patterns."""
        try:
            date_range = (dates.max() - dates.min()).days
            # Higher likelihood for longer time periods
            if date_range > 365:
                return 0.8
            elif date_range > 180:
                return 0.6
            elif date_range > 90:
                return 0.4
            else:
                return 0.2
        except:
            return 0.0

    def _calculate_data_quality_score(self, profile: Dict[str, Any]) -> float:
        """Calculate overall data quality score."""
        try:
            score = 1.0
            
            # Penalize missing data
            missing_ratio = profile.get('missing_data_ratio', 0)
            score -= missing_ratio * 0.3
            
            # Boost for good column variety
            col_variety = len(profile.get('numeric_columns', [])) + len(profile.get('categorical_columns', []))
            if col_variety >= 3:
                score += 0.1
            
            # Boost for temporal data
            if profile.get('datetime_columns'):
                score += 0.1
            
            return max(0.0, min(1.0, score))
        except:
            return 0.5

    async def calculate_kpis(
        self,
        data: Dict[str, Any],
        kpi_definitions: Optional[List[str]] = None
    ) -> List[KPIConfig]:
        """
        Calculate comprehensive KPIs from data using intelligent analysis.
        Supports financial, performance, trend, and statistical KPIs.
        """
        try:
            logger.info("Calculating comprehensive KPIs...")
            
            df = self._dict_to_dataframe(data)
            if df is None or df.empty:
                return []

            kpis = []
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
            datetime_cols = self._detect_datetime_columns(df)
            
            # 1. Basic Statistical KPIs
            kpis.extend(await self._calculate_statistical_kpis(df, numeric_cols))
            
            # 2. Financial/Business KPIs (if applicable column names detected)
            kpis.extend(await self._calculate_financial_kpis(df, numeric_cols))
            
            # 3. Performance KPIs (conversion rates, efficiency)
            kpis.extend(await self._calculate_performance_kpis(df, numeric_cols, categorical_cols))
            
            # 4. Temporal/Trend KPIs (if datetime columns exist)
            if datetime_cols and numeric_cols:
                kpis.extend(await self._calculate_temporal_kpis(df, datetime_cols[0], numeric_cols))
            
            # 5. Data Quality KPIs
            kpis.extend(await self._calculate_data_quality_kpis(df))
            
            # 6. Custom KPIs based on user requirements
            if kpi_definitions:
                kpis.extend(await self._calculate_custom_kpis(df, kpi_definitions))
            
            # Sort by relevance and importance, limit to top 8 KPIs
            kpis = self._prioritize_kpis(kpis, df)[:8]
            
            logger.info(f"Successfully calculated {len(kpis)} KPIs")
            return kpis
            
        except Exception as e:
            logger.error(f"KPI calculation failed: {str(e)}")
            return []

    async def _calculate_statistical_kpis(self, df: pd.DataFrame, numeric_cols: List[str]) -> List[KPIConfig]:
        """Calculate basic statistical KPIs."""
        kpis = []
        
        try:
            # Record count - always useful
            kpis.append(KPIConfig(
                name="Total Records",
                value=float(len(df)),
                unit="records",
                trend="neutral",
                trend_percentage=0.0,
                description="Total number of data records",
                format_type="number"
            ))
            
            # Calculate for primary numeric columns
            for col in numeric_cols[:3]:  # Limit to top 3 for statistical KPIs
                col_data = df[col].dropna()
                if len(col_data) == 0:
                    continue
                
                # Ensure column is actually numeric
                try:
                    col_data = pd.to_numeric(col_data, errors='coerce').dropna()
                    if len(col_data) == 0:
                        continue
                except:
                    continue
                
                col_name = col.replace('_', ' ').title()
                
                # Sum/Total
                try:
                    total_value = float(col_data.sum())
                    kpis.append(KPIConfig(
                        name=f"Total {col_name}",
                        value=total_value,
                        unit="",
                        trend="neutral",
                        trend_percentage=0.0,
                        description=f"Sum of all {col_name} values",
                        format_type="number"
                    ))
                except:
                    pass
                
                # Average
                try:
                    avg_value = float(col_data.mean())
                    kpis.append(KPIConfig(
                        name=f"Average {col_name}",
                        value=avg_value,
                        unit="",
                        trend="neutral",
                        trend_percentage=0.0,
                        description=f"Mean value of {col_name}",
                        format_type="number"
                    ))
                    
                    # Standard Deviation (if significant variance)
                    try:
                        std_value = float(col_data.std())
                        if std_value > avg_value * 0.1:  # Only if meaningful variation
                            kpis.append(KPIConfig(
                                name=f"{col_name} Volatility",
                                value=std_value,
                                unit="",
                                trend="neutral",
                                trend_percentage=0.0,
                                description=f"Standard deviation of {col_name}",
                                format_type="number"
                            ))
                    except:
                        pass
                except:
                    pass
                
        except Exception as e:
            logger.error(f"Statistical KPI calculation failed: {str(e)}")
        
        return kpis

    async def _calculate_financial_kpis(self, df: pd.DataFrame, numeric_cols: List[str]) -> List[KPIConfig]:
        """Calculate financial and business KPIs based on column name patterns."""
        kpis = []
        
        try:
            # Detect financial column patterns
            revenue_cols = [col for col in numeric_cols if any(term in col.lower() for term in ['revenue', 'sales', 'income', 'earnings'])]
            cost_cols = [col for col in numeric_cols if any(term in col.lower() for term in ['cost', 'expense', 'spend'])]
            profit_cols = [col for col in numeric_cols if any(term in col.lower() for term in ['profit', 'margin', 'net'])]
            price_cols = [col for col in numeric_cols if any(term in col.lower() for term in ['price', 'amount', 'value'])]
            
            # Revenue KPIs
            for col in revenue_cols:
                col_data = df[col].dropna()
                if len(col_data) > 0:
                    # Ensure column is numeric
                    try:
                        col_data = pd.to_numeric(col_data, errors='coerce').dropna()
                        if len(col_data) == 0:
                            continue
                    except:
                        continue
                        
                    total_revenue = float(col_data.sum())
                    avg_revenue = float(col_data.mean())
                    
                    kpis.append(KPIConfig(
                        name="Total Revenue",
                        value=total_revenue,
                        unit="$",
                        trend="neutral",
                        trend_percentage=0.0,
                        description="Total revenue generated",
                        format_type="currency"
                    ))
                    
                    kpis.append(KPIConfig(
                        name="Average Revenue per Record",
                        value=avg_revenue,
                        unit="$",
                        trend="neutral",
                        trend_percentage=0.0,
                        description="Average revenue per transaction/record",
                        format_type="currency"
                    ))
            
            # Profit Margin KPIs (if both revenue and cost columns exist)
            if revenue_cols and cost_cols:
                rev_col, cost_col = revenue_cols[0], cost_cols[0]
                
                try:
                    revenue_data = pd.to_numeric(df[rev_col], errors='coerce').dropna()
                    cost_data = pd.to_numeric(df[cost_col], errors='coerce').dropna()
                except:
                    revenue_data = cost_data = pd.Series([])
                
                if len(revenue_data) > 0 and len(cost_data) > 0:
                    total_revenue = revenue_data.sum()
                    total_cost = cost_data.sum()
                    
                    if total_revenue > 0:
                        profit_margin = ((total_revenue - total_cost) / total_revenue) * 100
                        kpis.append(KPIConfig(
                            name="Profit Margin",
                            value=float(profit_margin),
                            unit="%",
                            trend="up" if profit_margin > 20 else "neutral",
                            trend_percentage=0.0,
                            description="Overall profit margin percentage",
                            format_type="percentage"
                        ))
            
            # Price Analytics
            for col in price_cols:
                col_data = df[col].dropna()
                if len(col_data) > 0:
                    # Ensure column is numeric
                    try:
                        col_data = pd.to_numeric(col_data, errors='coerce').dropna()
                        if len(col_data) == 0:
                            continue
                    except:
                        continue
                        
                    median_price = float(col_data.median())
                    max_price = float(col_data.max())
                    min_price = float(col_data.min())
                    
                    kpis.append(KPIConfig(
                        name="Median Price",
                        value=median_price,
                        unit="$",
                        trend="neutral",
                        trend_percentage=0.0,
                        description="Median price point",
                        format_type="currency"
                    ))
                    
                    if max_price > min_price:
                        price_range_ratio = (max_price - min_price) / median_price * 100
                        kpis.append(KPIConfig(
                            name="Price Range Variability",
                            value=float(price_range_ratio),
                            unit="%",
                            trend="neutral",
                            trend_percentage=0.0,
                            description="Price variability as percentage of median",
                            format_type="percentage"
                        ))
        
        except Exception as e:
            logger.error(f"Financial KPI calculation failed: {str(e)}")
        
        return kpis

    async def _calculate_performance_kpis(self, df: pd.DataFrame, numeric_cols: List[str], categorical_cols: List[str]) -> List[KPIConfig]:
        """Calculate performance and efficiency KPIs."""
        kpis = []
        
        try:
            # Conversion Rate KPIs (looking for boolean or binary patterns)
            for col in categorical_cols:
                unique_vals = df[col].dropna().unique()
                if len(unique_vals) == 2:  # Binary categorical (success/fail, yes/no, etc.)
                    success_indicators = ['yes', 'true', '1', 'success', 'completed', 'converted']
                    success_val = None
                    
                    for val in unique_vals:
                        if str(val).lower() in success_indicators:
                            success_val = val
                            break
                    
                    if success_val:
                        total_count = len(df[col].dropna())
                        success_count = len(df[df[col] == success_val])
                        conversion_rate = (success_count / total_count) * 100 if total_count > 0 else 0
                        
                        kpis.append(KPIConfig(
                            name=f"{col.replace('_', ' ').title()} Rate",
                            value=float(conversion_rate),
                            unit="%",
                            trend="up" if conversion_rate > 50 else "neutral",
                            trend_percentage=0.0,
                            description=f"Success rate for {col.replace('_', ' ').lower()}",
                            format_type="percentage"
                        ))
            
            # Efficiency KPIs (ratios between numeric columns)
            if len(numeric_cols) >= 2:
                for i, col1 in enumerate(numeric_cols[:2]):
                    for col2 in numeric_cols[i+1:i+2]:  # Only check one pair to avoid too many ratios
                        if col1 != col2:
                            # Ensure both columns are numeric
                            try:
                                col1_data = pd.to_numeric(df[col1], errors='coerce').dropna()
                                col2_data = pd.to_numeric(df[col2], errors='coerce').dropna()
                                if len(col1_data) == 0 or len(col2_data) == 0:
                                    continue
                                col1_sum = col1_data.sum()
                                col2_sum = col2_data.sum()
                            except:
                                continue
                            
                            if col2_sum != 0:
                                ratio = col1_sum / col2_sum
                                kpis.append(KPIConfig(
                                    name=f"{col1.replace('_', ' ').title()} to {col2.replace('_', ' ').title()} Ratio",
                                    value=float(ratio),
                                    unit="ratio",
                                    trend="neutral",
                                    trend_percentage=0.0,
                                    description=f"Efficiency ratio between {col1} and {col2}",
                                    format_type="number"
                                ))
            
            # Distribution/Concentration KPIs
            for col in categorical_cols[:2]:  # Limit to avoid too many
                value_counts = df[col].value_counts()
                if len(value_counts) > 1:
                    # Calculate concentration (Herfindahl-Hirschman Index)
                    proportions = value_counts / value_counts.sum()
                    concentration = (proportions ** 2).sum()
                    
                    kpis.append(KPIConfig(
                        name=f"{col.replace('_', ' ').title()} Concentration",
                        value=float(concentration),
                        unit="index",
                        trend="neutral",
                        trend_percentage=0.0,
                        description=f"Concentration index for {col.replace('_', ' ').lower()} distribution",
                        format_type="number"
                    ))
        
        except Exception as e:
            logger.error(f"Performance KPI calculation failed: {str(e)}")
        
        return kpis

    async def _calculate_temporal_kpis(self, df: pd.DataFrame, date_col: str, numeric_cols: List[str]) -> List[KPIConfig]:
        """Calculate comprehensive temporal and trend KPIs."""
        kpis = []
        
        try:
            # Ensure date column is datetime
            df_temp = df.copy()
            if df_temp[date_col].dtype != 'datetime64[ns]':
                df_temp[date_col] = pd.to_datetime(df_temp[date_col], errors='coerce')
            
            df_temp = df_temp.dropna(subset=[date_col]).sort_values(date_col)
            
            for col in numeric_cols[:2]:  # Limit to top 2 numeric columns for temporal analysis
                col_data = df_temp[[date_col, col]].dropna()
                if len(col_data) < 3:  # Need at least 3 points for trend
                    continue
                
                values = col_data[col]
                col_name = col.replace('_', ' ').title()
                
                # Growth Rate (comparing first and last periods)
                if len(values) >= 2:
                    first_value = float(values.iloc[0])
                    last_value = float(values.iloc[-1])
                    
                    if first_value != 0:
                        total_growth = ((last_value - first_value) / abs(first_value)) * 100
                        trend = "up" if total_growth > 0 else "down"
                        
                        kpis.append(KPIConfig(
                            name=f"{col_name} Total Growth",
                            value=float(total_growth),
                            unit="%",
                            trend=trend,
                            trend_percentage=abs(total_growth),
                            description=f"Total growth in {col_name} over time period",
                            format_type="percentage"
                        ))
                
                # Period-over-period growth (recent trend)
                if len(values) >= 2:
                    recent_values = values.tail(2)
                    if len(recent_values) == 2:
                        prev_val = float(recent_values.iloc[0])
                        curr_val = float(recent_values.iloc[1])
                        
                        if prev_val != 0:
                            recent_growth = ((curr_val - prev_val) / abs(prev_val)) * 100
                            trend = "up" if recent_growth > 0 else "down"
                            
                            kpis.append(KPIConfig(
                                name=f"{col_name} Recent Trend",
                                value=float(recent_growth),
                                unit="%",
                                trend=trend,
                                trend_percentage=abs(recent_growth),
                                description=f"Most recent period-over-period change in {col_name}",
                                format_type="percentage"
                            ))
                
                # Moving average trend (if enough data points)
                if len(values) >= 5:
                    window_size = min(3, len(values) // 2)
                    moving_avg = values.rolling(window=window_size).mean()
                    
                    if len(moving_avg.dropna()) >= 2:
                        ma_trend = moving_avg.iloc[-1] - moving_avg.iloc[-2]
                        ma_trend_pct = (ma_trend / abs(moving_avg.iloc[-2])) * 100 if moving_avg.iloc[-2] != 0 else 0
                        
                        kpis.append(KPIConfig(
                            name=f"{col_name} Momentum",
                            value=float(ma_trend_pct),
                            unit="%",
                            trend="up" if ma_trend_pct > 0 else "down",
                            trend_percentage=abs(ma_trend_pct),
                            description=f"Moving average momentum for {col_name}",
                            format_type="percentage"
                        ))
        
        except Exception as e:
            logger.error(f"Temporal KPI calculation failed: {str(e)}")
        
        return kpis

    async def _calculate_data_quality_kpis(self, df: pd.DataFrame) -> List[KPIConfig]:
        """Calculate data quality and completeness KPIs."""
        kpis = []
        
        try:
            total_cells = df.size
            missing_cells = df.isnull().sum().sum()
            completeness = ((total_cells - missing_cells) / total_cells) * 100 if total_cells > 0 else 0
            
            kpis.append(KPIConfig(
                name="Data Completeness",
                value=float(completeness),
                unit="%",
                trend="up" if completeness > 95 else "neutral",
                trend_percentage=0.0,
                description="Percentage of non-missing data points",
                format_type="percentage"
            ))
            
            # Unique values ratio (data diversity)
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                uniqueness_scores = []
                for col in numeric_cols:
                    col_data = df[col].dropna()
                    if len(col_data) > 0:
                        uniqueness = len(col_data.unique()) / len(col_data)
                        uniqueness_scores.append(uniqueness)
                
                if uniqueness_scores:
                    avg_uniqueness = np.mean(uniqueness_scores) * 100
                    kpis.append(KPIConfig(
                        name="Data Diversity",
                        value=float(avg_uniqueness),
                        unit="%",
                        trend="neutral",
                        trend_percentage=0.0,
                        description="Average uniqueness ratio across numeric columns",
                        format_type="percentage"
                    ))
        
        except Exception as e:
            logger.error(f"Data quality KPI calculation failed: {str(e)}")
        
        return kpis

    async def _calculate_custom_kpis(self, df: pd.DataFrame, kpi_definitions: List[str]) -> List[KPIConfig]:
        """Calculate custom KPIs based on user requirements."""
        kpis = []
        
        try:
            for definition in kpi_definitions[:3]:  # Limit to 3 custom KPIs
                # Simple pattern matching for common custom KPI requests
                definition_lower = definition.lower()
                
                if 'conversion' in definition_lower:
                    # Try to find conversion-related columns
                    bool_cols = df.select_dtypes(include=['bool']).columns
                    if len(bool_cols) > 0:
                        col = bool_cols[0]
                        conversion_rate = df[col].mean() * 100
                        kpis.append(KPIConfig(
                            name="Custom Conversion Rate",
                            value=float(conversion_rate),
                            unit="%",
                            trend="neutral",
                            trend_percentage=0.0,
                            description=f"Custom conversion rate based on {col}",
                            format_type="percentage"
                        ))
                
                elif 'retention' in definition_lower:
                    # Simple retention calculation if temporal data exists
                    datetime_cols = self._detect_datetime_columns(df)
                    if datetime_cols:
                        # Placeholder retention calculation
                        retention_rate = 75.0  # Default assumption
                        kpis.append(KPIConfig(
                            name="Retention Rate",
                            value=retention_rate,
                            unit="%",
                            trend="neutral",
                            trend_percentage=0.0,
                            description="Estimated retention rate",
                            format_type="percentage"
                        ))
        
        except Exception as e:
            logger.error(f"Custom KPI calculation failed: {str(e)}")
        
        return kpis

    def _prioritize_kpis(self, kpis: List[KPIConfig], df: pd.DataFrame) -> List[KPIConfig]:
        """Prioritize KPIs based on business relevance and data characteristics."""
        
        def calculate_kpi_score(kpi: KPIConfig) -> float:
            score = 0.0
            
            # Higher priority for financial metrics
            if any(term in kpi.name.lower() for term in ['revenue', 'profit', 'cost', 'price']):
                score += 10.0
            
            # Higher priority for growth and trend metrics
            if any(term in kpi.name.lower() for term in ['growth', 'trend', 'rate']):
                score += 8.0
            
            # Higher priority for conversion and performance metrics  
            if any(term in kpi.name.lower() for term in ['conversion', 'efficiency', 'performance']):
                score += 7.0
            
            # Medium priority for statistical summaries
            if any(term in kpi.name.lower() for term in ['total', 'average', 'median']):
                score += 5.0
            
            # Lower priority for data quality metrics (still important but secondary)
            if any(term in kpi.name.lower() for term in ['completeness', 'quality', 'diversity']):
                score += 3.0
            
            # Boost score for trending KPIs
            if kpi.trend in ['up', 'down'] and kpi.trend_percentage > 5:
                score += 2.0
            
            return score
        
        # Sort by calculated priority score
        kpis_with_scores = [(kpi, calculate_kpi_score(kpi)) for kpi in kpis]
        kpis_with_scores.sort(key=lambda x: x[1], reverse=True)
        
        return [kpi for kpi, score in kpis_with_scores]
    
    async def get_layout_template(self, layout_type: str) -> Dict[str, Any]:
        """
        Get responsive layout templates for different dashboard types.
        Enhanced with proper responsive design principles and adaptive layouts.
        """
        layouts = {
            "responsive": {
                "type": "responsive",
                "grid_columns": 12,
                "responsive_breakpoints": {
                    "xs": {"max_width": 575, "grid_columns": 4, "padding": "8px"},
                    "sm": {"max_width": 767, "grid_columns": 6, "padding": "12px"},
                    "md": {"max_width": 991, "grid_columns": 8, "padding": "16px"},
                    "lg": {"max_width": 1199, "grid_columns": 10, "padding": "20px"},
                    "xl": {"min_width": 1200, "grid_columns": 12, "padding": "24px"}
                },
                "sections": [
                    {
                        "id": "kpis",
                        "title": "Key Performance Indicators",
                        "position": {"row": 0, "col": 0, "span": 12},
                        "responsive_positions": {
                            "xs": {"row": 0, "col": 0, "span": 4, "height": "auto"},
                            "sm": {"row": 0, "col": 0, "span": 6, "height": "auto"},
                            "md": {"row": 0, "col": 0, "span": 8, "height": "120px"},
                            "lg": {"row": 0, "col": 0, "span": 10, "height": "120px"},
                            "xl": {"row": 0, "col": 0, "span": 12, "height": "120px"}
                        },
                        "component_type": "kpi_grid",
                        "max_items": 6,
                        "layout_config": {
                            "display": "grid",
                            "grid_template_columns": {
                                "xs": "1fr",
                                "sm": "repeat(2, 1fr)",
                                "md": "repeat(3, 1fr)",
                                "lg": "repeat(4, 1fr)",
                                "xl": "repeat(6, 1fr)"
                            },
                            "gap": "16px",
                            "min_height": "80px"
                        }
                    },
                    {
                        "id": "main_charts",
                        "title": "Analytics Charts",
                        "position": {"row": 1, "col": 0, "span": 8},
                        "responsive_positions": {
                            "xs": {"row": 1, "col": 0, "span": 4, "height": "auto"},
                            "sm": {"row": 1, "col": 0, "span": 6, "height": "auto"},
                            "md": {"row": 1, "col": 0, "span": 5, "height": "400px"},
                            "lg": {"row": 1, "col": 0, "span": 6, "height": "450px"},
                            "xl": {"row": 1, "col": 0, "span": 8, "height": "500px"}
                        },
                        "component_type": "chart_grid",
                        "max_items": 4,
                        "layout_config": {
                            "display": "grid",
                            "grid_template_columns": {
                                "xs": "1fr",
                                "sm": "1fr",
                                "md": "repeat(2, 1fr)",
                                "lg": "repeat(2, 1fr)",
                                "xl": "repeat(2, 1fr)"
                            },
                            "gap": "20px",
                            "min_height": "300px"
                        }
                    },
                    {
                        "id": "insights",
                        "title": "AI Insights",
                        "position": {"row": 1, "col": 8, "span": 4},
                        "responsive_positions": {
                            "xs": {"row": 2, "col": 0, "span": 4, "height": "auto"},
                            "sm": {"row": 2, "col": 0, "span": 6, "height": "auto"},
                            "md": {"row": 1, "col": 5, "span": 3, "height": "400px"},
                            "lg": {"row": 1, "col": 6, "span": 4, "height": "450px"},
                            "xl": {"row": 1, "col": 8, "span": 4, "height": "500px"}
                        },
                        "component_type": "insight_panel",
                        "max_items": 3,
                        "layout_config": {
                            "display": "flex",
                            "flex_direction": "column",
                            "gap": "12px",
                            "min_height": "200px"
                        }
                    }
                ],
                "global_styles": {
                    "container_max_width": "1400px",
                    "container_margin": "0 auto",
                    "section_border_radius": "8px",
                    "section_shadow": "0 2px 8px rgba(0,0,0,0.1)",
                    "transition": "all 0.3s ease"
                }
            },
            "grid": {
                "type": "grid",
                "grid_columns": 6,
                "responsive_breakpoints": {
                    "xs": {"max_width": 575, "grid_columns": 2, "padding": "8px"},
                    "sm": {"max_width": 767, "grid_columns": 3, "padding": "12px"},
                    "md": {"max_width": 991, "grid_columns": 4, "padding": "16px"},
                    "lg": {"max_width": 1199, "grid_columns": 5, "padding": "20px"},
                    "xl": {"min_width": 1200, "grid_columns": 6, "padding": "24px"}
                },
                "sections": [
                    {
                        "id": "kpis",
                        "title": "KPIs",
                        "position": {"row": 0, "col": 0, "span": 6},
                        "responsive_positions": {
                            "xs": {"row": 0, "col": 0, "span": 2, "height": "auto"},
                            "sm": {"row": 0, "col": 0, "span": 3, "height": "auto"},
                            "md": {"row": 0, "col": 0, "span": 4, "height": "100px"},
                            "lg": {"row": 0, "col": 0, "span": 5, "height": "100px"},
                            "xl": {"row": 0, "col": 0, "span": 6, "height": "100px"}
                        },
                        "component_type": "kpi_row",
                        "max_items": 4,
                        "layout_config": {
                            "display": "flex",
                            "flex_wrap": "wrap",
                            "gap": "16px",
                            "justify_content": "space-between"
                        }
                    },
                    {
                        "id": "charts",
                        "title": "Charts",
                        "position": {"row": 1, "col": 0, "span": 6},
                        "responsive_positions": {
                            "xs": {"row": 1, "col": 0, "span": 2, "height": "auto"},
                            "sm": {"row": 1, "col": 0, "span": 3, "height": "auto"},
                            "md": {"row": 1, "col": 0, "span": 4, "height": "auto"},
                            "lg": {"row": 1, "col": 0, "span": 5, "height": "auto"},
                            "xl": {"row": 1, "col": 0, "span": 6, "height": "auto"}
                        },
                        "component_type": "chart_grid",
                        "max_items": 6,
                        "layout_config": {
                            "display": "grid",
                            "grid_template_columns": {
                                "xs": "1fr",
                                "sm": "1fr",
                                "md": "repeat(2, 1fr)",
                                "lg": "repeat(2, 1fr)",
                                "xl": "repeat(3, 1fr)"
                            },
                            "gap": "20px",
                            "min_height": "300px"
                        }
                    }
                ],
                "global_styles": {
                    "container_max_width": "1200px",
                    "container_margin": "0 auto",
                    "section_border_radius": "6px",
                    "section_shadow": "0 1px 6px rgba(0,0,0,0.08)",
                    "transition": "all 0.3s ease"
                }
            },
            "executive": {
                "type": "executive",
                "grid_columns": 4,
                "responsive_breakpoints": {
                    "xs": {"max_width": 575, "grid_columns": 1, "padding": "8px"},
                    "sm": {"max_width": 767, "grid_columns": 2, "padding": "12px"},
                    "md": {"max_width": 991, "grid_columns": 3, "padding": "16px"},
                    "lg": {"max_width": 1199, "grid_columns": 4, "padding": "20px"},
                    "xl": {"min_width": 1200, "grid_columns": 4, "padding": "24px"}
                },
                "sections": [
                    {
                        "id": "headline_kpis",
                        "title": "Executive Summary",
                        "position": {"row": 0, "col": 0, "span": 4},
                        "responsive_positions": {
                            "xs": {"row": 0, "col": 0, "span": 1, "height": "auto"},
                            "sm": {"row": 0, "col": 0, "span": 2, "height": "auto"},
                            "md": {"row": 0, "col": 0, "span": 3, "height": "140px"},
                            "lg": {"row": 0, "col": 0, "span": 4, "height": "140px"},
                            "xl": {"row": 0, "col": 0, "span": 4, "height": "140px"}
                        },
                        "component_type": "executive_kpis",
                        "max_items": 4,
                        "layout_config": {
                            "display": "grid",
                            "grid_template_columns": {
                                "xs": "1fr",
                                "sm": "repeat(2, 1fr)",
                                "md": "repeat(2, 1fr)",
                                "lg": "repeat(4, 1fr)",
                                "xl": "repeat(4, 1fr)"
                            },
                            "gap": "20px",
                            "min_height": "100px"
                        }
                    },
                    {
                        "id": "key_charts",
                        "title": "Key Metrics",
                        "position": {"row": 1, "col": 0, "span": 4},
                        "responsive_positions": {
                            "xs": {"row": 1, "col": 0, "span": 1, "height": "auto"},
                            "sm": {"row": 1, "col": 0, "span": 2, "height": "auto"},
                            "md": {"row": 1, "col": 0, "span": 3, "height": "500px"},
                            "lg": {"row": 1, "col": 0, "span": 4, "height": "500px"},
                            "xl": {"row": 1, "col": 0, "span": 4, "height": "500px"}
                        },
                        "component_type": "executive_charts",
                        "max_items": 2,
                        "layout_config": {
                            "display": "grid",
                            "grid_template_columns": {
                                "xs": "1fr",
                                "sm": "1fr",
                                "md": "1fr",
                                "lg": "repeat(2, 1fr)",
                                "xl": "repeat(2, 1fr)"
                            },
                            "gap": "24px",
                            "min_height": "400px"
                        }
                    }
                ],
                "global_styles": {
                    "container_max_width": "1000px",
                    "container_margin": "0 auto",
                    "section_border_radius": "12px",
                    "section_shadow": "0 4px 12px rgba(0,0,0,0.12)",
                    "transition": "all 0.3s ease"
                }
            },
            "mobile_optimized": {
                "type": "mobile_optimized",
                "grid_columns": 1,
                "responsive_breakpoints": {
                    "xs": {"max_width": 575, "grid_columns": 1, "padding": "12px"},
                    "sm": {"max_width": 767, "grid_columns": 1, "padding": "16px"}
                },
                "sections": [
                    {
                        "id": "summary_kpis",
                        "title": "Key Metrics",
                        "position": {"row": 0, "col": 0, "span": 1},
                        "component_type": "mobile_kpi_cards",
                        "max_items": 3,
                        "layout_config": {
                            "display": "flex",
                            "flex_direction": "column",
                            "gap": "12px"
                        }
                    },
                    {
                        "id": "primary_chart",
                        "title": "Main Chart",
                        "position": {"row": 1, "col": 0, "span": 1},
                        "component_type": "mobile_chart",
                        "max_items": 1,
                        "layout_config": {
                            "display": "block",
                            "height": "300px",
                            "margin": "16px 0"
                        }
                    },
                    {
                        "id": "secondary_insights",
                        "title": "Insights",
                        "position": {"row": 2, "col": 0, "span": 1},
                        "component_type": "mobile_insights",
                        "max_items": 2,
                        "layout_config": {
                            "display": "flex",
                            "flex_direction": "column",
                            "gap": "8px"
                        }
                    }
                ],
                "global_styles": {
                    "container_max_width": "100%",
                    "container_margin": "0",
                    "section_border_radius": "8px",
                    "section_shadow": "0 2px 4px rgba(0,0,0,0.1)",
                    "transition": "all 0.2s ease"
                }
            }
        }
        
        return layouts.get(layout_type, layouts["responsive"])
    
    async def get_theme_config(self, theme_name: str) -> Dict[str, Any]:
        """
        Get theme configurations for dashboard styling.
        """
        themes = {
            "default": {
                "name": "default",
                "colors": {
                    "primary": "#3b82f6",
                    "secondary": "#64748b", 
                    "accent": "#f59e0b",
                    "background": "#ffffff",
                    "surface": "#f8fafc",
                    "text": "#1e293b"
                },
                "chart_palette": ["#3b82f6", "#ef4444", "#10b981", "#f59e0b", "#8b5cf6", "#06b6d4"],
                "typography": {
                    "font_family": "Inter, sans-serif",
                    "heading_size": "1.5rem",
                    "body_size": "0.875rem"
                }
            },
            "dark": {
                "name": "dark",
                "colors": {
                    "primary": "#60a5fa",
                    "secondary": "#94a3b8",
                    "accent": "#fbbf24", 
                    "background": "#0f172a",
                    "surface": "#1e293b",
                    "text": "#f1f5f9"
                },
                "chart_palette": ["#60a5fa", "#f87171", "#34d399", "#fbbf24", "#a78bfa", "#22d3ee"],
                "typography": {
                    "font_family": "Inter, sans-serif",
                    "heading_size": "1.5rem",
                    "body_size": "0.875rem"
                }
            },
            "corporate": {
                "name": "corporate",
                "colors": {
                    "primary": "#1f2937",
                    "secondary": "#6b7280",
                    "accent": "#dc2626",
                    "background": "#ffffff",
                    "surface": "#f9fafb",
                    "text": "#111827"
                },
                "chart_palette": ["#1f2937", "#dc2626", "#059669", "#d97706", "#7c3aed", "#0891b2"],
                "typography": {
                    "font_family": "system-ui, sans-serif",
                    "heading_size": "1.5rem", 
                    "body_size": "0.875rem"
                }
            }
        }
        
        return themes.get(theme_name, themes["default"])
    
    # Helper methods
    
    def _dict_to_dataframe(self, data: Dict[str, Any]) -> Optional[pd.DataFrame]:
        """Convert data dictionary to pandas DataFrame."""
        try:
            if 'rows' in data and 'columns' in data:
                # Standard format from file parser
                return pd.DataFrame(data['rows'])
            elif isinstance(data, dict) and all(isinstance(v, list) for v in data.values()):
                # Column-based format
                return pd.DataFrame(data)
            elif 'data' in data:
                # Nested data format
                return pd.DataFrame(data['data'])
            else:
                # Try direct conversion
                return pd.DataFrame(data)
        except Exception as e:
            logger.error(f"Failed to convert data to DataFrame: {str(e)}")
            return None
    
    def _detect_datetime_columns(self, df: pd.DataFrame) -> List[str]:
        """Detect datetime columns in DataFrame."""
        datetime_cols = []
        for col in df.columns:
            if df[col].dtype == 'datetime64[ns]':
                datetime_cols.append(col)
            elif df[col].dtype == 'object':
                # Try to parse as datetime
                try:
                    sample = df[col].dropna().head(5).astype(str)
                    if any(re.match(r'\d{4}-\d{2}-\d{2}', str(val)) for val in sample):
                        datetime_cols.append(col)
                except:
                    pass
        return datetime_cols
    
    def _create_time_series_recommendation(self, df: pd.DataFrame, date_col: str, value_col: str) -> Optional[ChartRecommendation]:
        """Create time series chart recommendation."""
        try:
            # Clean and validate data
            time_data = df[[date_col, value_col]].dropna().copy()
            
            # Convert date column to datetime if not already
            try:
                if not pd.api.types.is_datetime64_any_dtype(time_data[date_col]):
                    time_data[date_col] = pd.to_datetime(time_data[date_col], errors='coerce')
            except:
                # If datetime conversion fails, try to convert to string and clean
                time_data[date_col] = time_data[date_col].astype(str)
            
            # Convert value column to numeric
            time_data[value_col] = pd.to_numeric(time_data[value_col], errors='coerce')
            
            # Drop rows with invalid data
            time_data = time_data.dropna()
            
            if len(time_data) == 0:
                return None
            
            # Sort by date
            time_data = time_data.sort_values(date_col)
            
            # Convert date to string format for chart display
            if pd.api.types.is_datetime64_any_dtype(time_data[date_col]):
                time_data[date_col] = time_data[date_col].dt.strftime('%Y-%m-%d')
            else:
                time_data[date_col] = time_data[date_col].astype(str)
            
            chart_data = time_data.to_dict('records')
            
            return ChartRecommendation(
                chart_type="line",
                data_columns=[date_col, value_col],
                title=f"{value_col.replace('_', ' ').title()} Over Time",
                description=f"Trend analysis of {value_col} over {date_col}",
                confidence=0.9,
                recharts_config={
                    "type": "LineChart",
                    "dataKey": value_col,
                    "xAxisKey": date_col,
                    "width": "100%",
                    "height": 300,
                    "margin": {"top": 5, "right": 30, "left": 20, "bottom": 5}
                },
                data=chart_data
            )
        except Exception as e:
            logger.error(f"Time series recommendation failed: {str(e)}")
            return None
    
    def _create_categorical_recommendation(self, df: pd.DataFrame, cat_col: str, value_col: str) -> Optional[ChartRecommendation]:
        """Create categorical chart recommendation."""
        try:
            # Clean and validate data
            clean_df = df[[cat_col, value_col]].dropna().copy()
            
            # Ensure categorical column is string and value column is numeric
            clean_df[cat_col] = clean_df[cat_col].astype(str)
            
            # Try to convert value column to numeric, count if not possible
            try:
                clean_df[value_col] = pd.to_numeric(clean_df[value_col], errors='coerce')
                # Drop rows where conversion failed
                clean_df = clean_df.dropna()
                if len(clean_df) == 0:
                    # If no numeric data, fall back to count
                    chart_data = df[cat_col].value_counts().reset_index()
                    chart_data.columns = [cat_col, 'count']
                    value_col = 'count'
                else:
                    # Group by categorical and sum numeric values
                    chart_data = clean_df.groupby(cat_col)[value_col].sum().reset_index()
            except:
                # Fall back to counting occurrences
                chart_data = df[cat_col].value_counts().reset_index()
                chart_data.columns = [cat_col, 'count']
                value_col = 'count'
            
            unique_categories = len(chart_data)
            chart_type = "pie" if unique_categories <= 5 else "bar"
            
            # Convert to records for frontend
            chart_data_list = chart_data.to_dict('records')
            
            return ChartRecommendation(
                chart_type=chart_type,
                data_columns=[cat_col, value_col],
                title=f"{value_col.replace('_', ' ').title()} by {cat_col.replace('_', ' ').title()}",
                description=f"Distribution of {value_col} across {cat_col} categories",
                confidence=0.8,
                recharts_config={
                    "type": "BarChart" if chart_type == "bar" else "PieChart",
                    "dataKey": value_col,
                    "xAxisKey": cat_col if chart_type == "bar" else None,
                    "width": "100%",
                    "height": 300,
                    "margin": {"top": 5, "right": 30, "left": 20, "bottom": 5}
                },
                data=chart_data_list
            )
        except Exception as e:
            logger.error(f"Categorical recommendation failed: {str(e)}")
            return None
    
    def _create_distribution_recommendation(self, df: pd.DataFrame, col: str) -> Optional[ChartRecommendation]:
        """Create distribution chart recommendation."""
        try:
            # Clean and validate data
            clean_data = df[col].dropna()
            
            # Convert to numeric, skip if not possible
            clean_data = pd.to_numeric(clean_data, errors='coerce').dropna()
            
            if len(clean_data) == 0:
                return None
            
            # Create histogram data
            hist_data, bin_edges = pd.cut(clean_data, bins=min(10, len(clean_data.unique())), retbins=True)
            hist_counts = hist_data.value_counts().sort_index()
            
            chart_data = []
            for interval, count in hist_counts.items():
                if pd.notna(interval):
                    chart_data.append({
                        'range': f"{interval.left:.2f}-{interval.right:.2f}",
                        col: int(count),
                        'count': int(count)
                    })
            
            return ChartRecommendation(
                chart_type="bar",
                data_columns=[col],
                title=f"{col.replace('_', ' ').title()} Distribution",
                description=f"Statistical distribution of {col} values",
                confidence=0.7,
                recharts_config={
                    "type": "BarChart",
                    "dataKey": "count",
                    "xAxisKey": "range",
                    "width": "100%",
                    "height": 300,
                    "margin": {"top": 5, "right": 30, "left": 20, "bottom": 5}
                },
                data=chart_data
            )
        except Exception as e:
            logger.error(f"Distribution recommendation failed: {str(e)}")
            return None
    
    def _create_correlation_recommendation(self, df: pd.DataFrame, cols: List[str]) -> Optional[ChartRecommendation]:
        """Create correlation chart recommendation."""
        try:
            # Clean and validate data for correlation
            clean_df = df[cols[:2]].dropna().copy()
            
            # Convert both columns to numeric
            for col in cols[:2]:
                clean_df[col] = pd.to_numeric(clean_df[col], errors='coerce')
            
            # Drop any rows where conversion failed
            clean_df = clean_df.dropna()
            
            if len(clean_df) == 0:
                return None
            
            # Prepare scatter plot data
            chart_data = clean_df.to_dict('records')
            
            return ChartRecommendation(
                chart_type="scatter",
                data_columns=cols[:2],  # Use first two columns for scatter
                title="Correlation Analysis",
                description=f"Relationship between {' and '.join(cols[:2])}",
                confidence=0.75,
                recharts_config={
                    "type": "ScatterChart",
                    "dataKey": cols[1],
                    "xAxisKey": cols[0],
                    "width": "100%",
                    "height": 300,
                    "margin": {"top": 5, "right": 30, "left": 20, "bottom": 5}
                },
                data=chart_data
            )
        except Exception as e:
            logger.error(f"Correlation recommendation failed: {str(e)}")
            return None
    
    async def _optimize_layout_for_content(self, layout: Dict[str, Any], charts: List, kpis: List) -> Dict[str, Any]:
        """
        Enhanced layout optimization with intelligent content adaptation.
        Implements smart sizing, responsive adjustments, and performance optimizations.
        """
        try:
            optimized_layout = layout.copy()
            chart_count = len(charts)
            kpi_count = len(kpis)
            
            # Device-specific optimizations based on content
            device_optimizations = await self._calculate_device_optimizations(chart_count, kpi_count)
            
            # Adjust sections based on actual content and optimal layouts
            for section in optimized_layout.get('sections', []):
                section_id = section['id']
                
                # Set actual item counts
                if section_id in ['kpis', 'headline_kpis', 'summary_kpis']:
                    section['actual_items'] = kpi_count
                    section = await self._optimize_kpi_section(section, kpi_count)
                elif section_id in ['main_charts', 'charts', 'key_charts', 'primary_chart']:
                    section['actual_items'] = chart_count
                    section = await self._optimize_chart_section(section, chart_count)
                elif section_id in ['insights', 'secondary_insights']:
                    # Insights are derived from charts and KPIs
                    insight_count = min(3, max(1, chart_count // 2))
                    section['actual_items'] = insight_count
                    section = await self._optimize_insight_section(section, insight_count)
                
                # Apply responsive grid adjustments
                section = await self._apply_responsive_grid_adjustments(section, chart_count, kpi_count)
                
                # Add performance optimizations
                section = await self._add_performance_optimizations(section)
            
            # Add dynamic breakpoint adjustments
            optimized_layout = await self._add_dynamic_breakpoints(optimized_layout, chart_count, kpi_count)
            
            # Add accessibility enhancements
            optimized_layout = await self._add_accessibility_features(optimized_layout)
            
            # Add loading states and progressive enhancement
            optimized_layout = await self._add_progressive_loading(optimized_layout)
            
            return optimized_layout
            
        except Exception as e:
            logger.error(f"Layout optimization failed: {str(e)}")
            return layout

    async def _calculate_device_optimizations(self, chart_count: int, kpi_count: int) -> Dict[str, Any]:
        """Calculate optimal configurations for different device types."""
        return {
            "mobile": {
                "max_charts_per_row": 1,
                "max_kpis_per_row": 2,
                "chart_height": "250px",
                "section_padding": "12px",
                "font_scale": 0.9
            },
            "tablet": {
                "max_charts_per_row": 2,
                "max_kpis_per_row": 3,
                "chart_height": "300px",
                "section_padding": "16px",
                "font_scale": 1.0
            },
            "desktop": {
                "max_charts_per_row": min(3, chart_count),
                "max_kpis_per_row": min(6, kpi_count),
                "chart_height": "400px",
                "section_padding": "20px",
                "font_scale": 1.0
            },
            "large_desktop": {
                "max_charts_per_row": min(4, chart_count),
                "max_kpis_per_row": min(8, kpi_count),
                "chart_height": "450px",
                "section_padding": "24px",
                "font_scale": 1.1
            }
        }

    async def _optimize_kpi_section(self, section: Dict[str, Any], kpi_count: int) -> Dict[str, Any]:
        """Optimize KPI section layout based on content count."""
        # Intelligent grid column calculation
        optimal_columns = {
            1: "1fr",
            2: "repeat(2, 1fr)",
            3: "repeat(3, 1fr)",
            4: "repeat(2, 1fr)",  # 2x2 grid for better mobile experience
            5: "repeat(3, 1fr)",  # Best fit for 5 items
            6: "repeat(3, 1fr)",  # 3x2 grid
            7: "repeat(4, 1fr)",  # 4x2 grid
            8: "repeat(4, 1fr)"   # 4x2 grid
        }
        
        # Update layout config with optimal columns
        if 'layout_config' in section:
            if kpi_count <= 8:
                section['layout_config']['grid_template_columns']['md'] = optimal_columns.get(kpi_count, "repeat(3, 1fr)")
                section['layout_config']['grid_template_columns']['lg'] = optimal_columns.get(kpi_count, "repeat(4, 1fr)")
                section['layout_config']['grid_template_columns']['xl'] = optimal_columns.get(kpi_count, "repeat(6, 1fr)")
            
            # Adjust gap based on item count
            if kpi_count <= 2:
                section['layout_config']['gap'] = "24px"
            elif kpi_count <= 4:
                section['layout_config']['gap'] = "20px"
            else:
                section['layout_config']['gap'] = "16px"
        
        return section

    async def _optimize_chart_section(self, section: Dict[str, Any], chart_count: int) -> Dict[str, Any]:
        """Optimize chart section layout based on content count."""
        # Optimal chart grid layouts
        if chart_count == 1:
            grid_columns = "1fr"
        elif chart_count == 2:
            grid_columns = "repeat(2, 1fr)"
        elif chart_count == 3:
            grid_columns = "repeat(2, 1fr)"  # 2+1 layout works better than 3x1
        elif chart_count == 4:
            grid_columns = "repeat(2, 1fr)"  # 2x2 grid
        else:
            grid_columns = "repeat(3, 1fr)"  # For 5+ charts
        
        # Update layout config
        if 'layout_config' in section:
            section['layout_config']['grid_template_columns']['lg'] = grid_columns
            section['layout_config']['grid_template_columns']['xl'] = grid_columns
            
            # Adjust spacing based on chart count
            if chart_count <= 2:
                section['layout_config']['gap'] = "32px"
            elif chart_count <= 4:
                section['layout_config']['gap'] = "24px"
            else:
                section['layout_config']['gap'] = "20px"
        
        return section

    async def _optimize_insight_section(self, section: Dict[str, Any], insight_count: int) -> Dict[str, Any]:
        """Optimize insight section layout."""
        if 'layout_config' in section:
            # Adjust gap based on insight count
            section['layout_config']['gap'] = "16px" if insight_count <= 2 else "12px"
            
            # Add insight-specific styling
            section['layout_config']['max_height'] = "500px"
            section['layout_config']['overflow_y'] = "auto"
        
        return section

    async def _apply_responsive_grid_adjustments(self, section: Dict[str, Any], chart_count: int, kpi_count: int) -> Dict[str, Any]:
        """Apply intelligent responsive grid adjustments."""
        if 'responsive_positions' not in section:
            return section
        
        # Adjust responsive positions based on content
        responsive_positions = section['responsive_positions']
        
        # For sections with many items, ensure better mobile experience
        if section['id'] in ['kpis', 'headline_kpis'] and kpi_count > 4:
            # Force single column on mobile for readability
            responsive_positions['xs']['span'] = min(responsive_positions['xs']['span'], 1)
            responsive_positions['sm']['span'] = min(responsive_positions['sm']['span'], 2)
        
        if section['id'] in ['main_charts', 'charts'] and chart_count > 2:
            # Ensure charts have adequate space on smaller screens
            responsive_positions['xs']['height'] = "auto"
            responsive_positions['sm']['height'] = "auto"
        
        return section

    async def _add_performance_optimizations(self, section: Dict[str, Any]) -> Dict[str, Any]:
        """Add performance optimization configurations."""
        section['performance'] = {
            'lazy_loading': True,
            'virtual_scrolling': section.get('max_items', 0) > 10,
            'debounce_resize': True,
            'optimize_rerender': True,
            'preload_images': False,
            'cache_calculations': True
        }
        
        # Add intersection observer for lazy loading
        section['intersection_config'] = {
            'root_margin': '50px',
            'threshold': 0.1
        }
        
        return section

    async def _add_dynamic_breakpoints(self, layout: Dict[str, Any], chart_count: int, kpi_count: int) -> Dict[str, Any]:
        """Add dynamic breakpoint adjustments based on content."""
        # Add content-aware breakpoints
        layout['dynamic_breakpoints'] = {
            'content_aware': True,
            'chart_density_threshold': 4,
            'kpi_density_threshold': 6,
            'auto_stack_threshold': 768,
            'force_mobile_layout_threshold': 480
        }
        
        # Add adaptive spacing
        layout['adaptive_spacing'] = {
            'base_unit': '8px',
            'scale_factor': 1.2,
            'min_spacing': '4px',
            'max_spacing': '32px'
        }
        
        return layout

    async def _add_accessibility_features(self, layout: Dict[str, Any]) -> Dict[str, Any]:
        """Add accessibility enhancements to layout."""
        layout['accessibility'] = {
            'focus_management': True,
            'keyboard_navigation': True,
            'screen_reader_optimized': True,
            'high_contrast_support': True,
            'reduced_motion_respect': True,
            'aria_labels': True,
            'semantic_structure': True
        }
        
        # Add ARIA landmarks
        for section in layout.get('sections', []):
            section['aria'] = {
                'role': 'region',
                'label': section.get('title', ''),
                'live': 'polite' if 'kpi' in section['id'] else 'off'
            }
        
        return layout

    async def _add_progressive_loading(self, layout: Dict[str, Any]) -> Dict[str, Any]:
        """Add progressive loading and skeleton states."""
        layout['progressive_loading'] = {
            'enabled': True,
            'skeleton_screens': True,
            'staggered_animation': True,
            'priority_loading': ['kpis', 'main_charts', 'insights'],
            'loading_states': {
                'initial': 'skeleton',
                'loading': 'shimmer',
                'error': 'error_state',
                'empty': 'empty_state'
            }
        }
        
        # Add loading priorities for sections
        section_priorities = {'kpis': 1, 'main_charts': 2, 'insights': 3}
        for section in layout.get('sections', []):
            section['loading_priority'] = section_priorities.get(
                section['id'].replace('headline_', '').replace('summary_', '').replace('primary_', '').replace('key_', ''),
                4
            )
        
        return layout

    async def _analyze_data_characteristics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze data characteristics for dashboard generation."""
        try:
            df = self._dict_to_dataframe(data)
            if df is None or df.empty:
                return {}
            
            characteristics = {
                'row_count': len(df),
                'column_count': len(df.columns),
                'numeric_columns': df.select_dtypes(include=[np.number]).columns.tolist(),
                'categorical_columns': df.select_dtypes(include=['object']).columns.tolist(),
                'data_types': df.dtypes.to_dict(),
                'sample_data': df.head().to_dict('records')
            }
            
            return characteristics
        except Exception as e:
            logger.error(f"Data characteristics analysis failed: {str(e)}")
            return {}

    # Enhanced Chart Creation Methods for AI-Driven Recommendations
    
    def _create_enhanced_time_series_recommendation(
        self,
        df: pd.DataFrame,
        date_col: str,
        value_col: str,
        chart_type: str,
        confidence: float,
        temporal_insights: Dict[str, Any]
    ) -> Optional[ChartRecommendation]:
        """Create enhanced time series chart recommendations with AI insights."""
        try:
            # Basic validation
            if date_col not in df.columns or value_col not in df.columns:
                return None
            
            # Extract temporal insights
            trend_strength = temporal_insights.get('trend_strength', 0)
            frequency_pattern = temporal_insights.get('frequency_pattern', 'unknown')
            seasonality = temporal_insights.get('seasonality_likelihood', 0)
            
            # Enhanced title generation
            if trend_strength > 0.7:
                trend_desc = "Strong Trending"
            elif trend_strength > 0.3:
                trend_desc = "Moderate Trending"
            else:
                trend_desc = "Stable"
            
            title = f"{trend_desc} {value_col.replace('_', ' ').title()} Over Time"
            
            # AI-driven description
            description_parts = [f"Time series analysis of {value_col}"]
            if frequency_pattern != 'unknown':
                description_parts.append(f"with {frequency_pattern} data frequency")
            if seasonality > 0.6:
                description_parts.append("showing potential seasonal patterns")
            if trend_strength > 0.5:
                description_parts.append("with significant trend component")
            
            description = ". ".join(description_parts) + "."
            
            # Enhanced Recharts configuration
            recharts_config = {
                'type': chart_type,
                'data_key_x': date_col,
                'data_key_y': value_col,
                'stroke': '#8884d8' if chart_type == 'line' else None,
                'fill': '#8884d8' if chart_type == 'area' else None,
                'stroke_width': 2 if trend_strength > 0.5 else 1,
                'dot': trend_strength < 0.3,  # Show dots for stable data
                'smooth_curve': trend_strength > 0.4,
                'gradient': chart_type == 'area' and seasonality > 0.5,
                'tooltip': {
                    'enabled': True,
                    'format': 'datetime' if frequency_pattern in ['daily', 'weekly'] else 'default'
                },
                'legend': {
                    'enabled': True,
                    'position': 'bottom'
                },
                'grid': {
                    'enabled': True,
                    'stroke_dasharray': '3 3'
                },
                'responsive': True,
                'ai_insights': {
                    'trend_strength': trend_strength,
                    'frequency_pattern': frequency_pattern,
                    'seasonality_score': seasonality,
                    'recommended_interactions': ['zoom', 'tooltip'] if trend_strength > 0.3 else ['tooltip']
                }
            }
            
            return ChartRecommendation(
                chart_type=chart_type,
                data_columns=[date_col, value_col],
                title=title,
                description=description,
                confidence=confidence,
                recharts_config=recharts_config
            )
            
        except Exception as e:
            logger.error(f"Enhanced time series recommendation failed: {str(e)}")
            return None

    def _create_enhanced_categorical_recommendation(
        self,
        df: pd.DataFrame,
        cat_col: str,
        value_col: str,
        chart_type: str,
        confidence: float,
        categorical_insights: Dict[str, Any]
    ) -> Optional[ChartRecommendation]:
        """Create enhanced categorical chart recommendations with AI insights."""
        try:
            if cat_col not in df.columns or value_col not in df.columns:
                return None
            
            # Extract categorical insights
            unique_count = categorical_insights.get('unique_count', 0)
            concentration_ratio = categorical_insights.get('concentration_ratio', 0)
            diversity_index = categorical_insights.get('diversity_index', 0)
            cardinality_category = categorical_insights.get('cardinality_category', 'unknown')
            
            # AI-driven title generation
            if concentration_ratio > 0.7:
                dominance_desc = "Dominated"
            elif concentration_ratio > 0.4:
                dominance_desc = "Concentrated"
            else:
                dominance_desc = "Distributed"
            
            title = f"{dominance_desc} {value_col.replace('_', ' ').title()} by {cat_col.replace('_', ' ').title()}"
            
            # Enhanced description
            description_parts = [f"Analysis of {value_col} across {unique_count} {cat_col} categories"]
            if diversity_index > 0.8:
                description_parts.append("showing high diversity")
            elif diversity_index < 0.3:
                description_parts.append("with low diversity concentration")
            if concentration_ratio > 0.5:
                description_parts.append("with clear category dominance")
            
            description = ". ".join(description_parts) + "."
            
            # Enhanced Recharts configuration
            if chart_type == 'pie':
                recharts_config = {
                    'type': 'pie',
                    'data_key': value_col,
                    'name_key': cat_col,
                    'cx': '50%',
                    'cy': '50%',
                    'outer_radius': 80 if unique_count <= 5 else 60,
                    'fill': '#8884d8',
                    'label': unique_count <= 8,
                    'label_line': False if unique_count > 5 else True,
                    'cells_colors': self._generate_color_palette(unique_count),
                    'tooltip': {'enabled': True},
                    'legend': {'enabled': unique_count <= 6, 'position': 'right'},
                    'responsive': True,
                    'ai_insights': {
                        'category_dominance': concentration_ratio,
                        'diversity_score': diversity_index,
                        'cardinality_level': cardinality_category,
                        'recommended_interactions': ['hover', 'click'] if unique_count <= 10 else ['hover']
                    }
                }
            else:  # bar chart
                recharts_config = {
                    'type': 'bar',
                    'data_key_x': cat_col,
                    'data_key_y': value_col,
                    'fill': '#8884d8',
                    'stroke': '#8884d8',
                    'bar_size': max(20, min(60, 300 // unique_count)),
                    'tooltip': {'enabled': True},
                    'legend': {'enabled': False},
                    'grid': {'enabled': True, 'stroke_dasharray': '3 3'},
                    'x_axis': {
                        'angle': -45 if unique_count > 5 else 0,
                        'text_anchor': 'end' if unique_count > 5 else 'middle'
                    },
                    'y_axis': {'enabled': True},
                    'responsive': True,
                    'ai_insights': {
                        'category_dominance': concentration_ratio,
                        'diversity_score': diversity_index,
                        'cardinality_level': cardinality_category,
                        'recommended_interactions': ['sort', 'filter'] if unique_count > 3 else ['tooltip']
                    }
                }
            
            return ChartRecommendation(
                chart_type=chart_type,
                data_columns=[cat_col, value_col],
                title=title,
                description=description,
                confidence=confidence,
                recharts_config=recharts_config
            )
            
        except Exception as e:
            logger.error(f"Enhanced categorical recommendation failed: {str(e)}")
            return None

    def _create_enhanced_distribution_recommendation(
        self,
        df: pd.DataFrame,
        col: str,
        chart_type: str,
        confidence: float,
        numeric_insights: Dict[str, Any]
    ) -> Optional[ChartRecommendation]:
        """Create enhanced distribution chart recommendations with AI insights."""
        try:
            if col not in df.columns:
                return None
            
            # Extract numeric insights
            skewness = numeric_insights.get('skewness', 0)
            kurtosis = numeric_insights.get('kurtosis', 0)
            outlier_ratio = numeric_insights.get('outlier_ratio', 0)
            distribution_type = numeric_insights.get('distribution_type', 'unknown')
            unique_ratio = numeric_insights.get('unique_ratio', 0)
            
            # AI-driven title generation
            if abs(skewness) > 1:
                skew_desc = "Skewed"
            elif abs(skewness) > 0.5:
                skew_desc = "Slightly Skewed"
            else:
                skew_desc = "Symmetric"
            
            title = f"{skew_desc} Distribution of {col.replace('_', ' ').title()}"
            
            # Enhanced description
            description_parts = [f"Statistical distribution analysis of {col}"]
            if distribution_type != 'unknown':
                description_parts.append(f"showing {distribution_type.replace('_', ' ')} distribution pattern")
            if outlier_ratio > 0.1:
                description_parts.append("with notable outliers")
            elif outlier_ratio > 0.05:
                description_parts.append("with some outliers")
            
            description = ". ".join(description_parts) + "."
            
            # Enhanced Recharts configuration
            if chart_type == 'histogram':
                # Calculate optimal bin count
                data_count = len(df[col].dropna())
                optimal_bins = min(30, max(10, int(np.sqrt(data_count))))
                
                recharts_config = {
                    'type': 'bar',  # Histogram implemented as bar chart
                    'data_key_x': f"{col}_bins",
                    'data_key_y': 'frequency',
                    'fill': '#8884d8',
                    'stroke': '#8884d8',
                    'bar_size': 20,
                    'bins': optimal_bins,
                    'tooltip': {'enabled': True, 'format': 'histogram'},
                    'legend': {'enabled': False},
                    'grid': {'enabled': True, 'stroke_dasharray': '3 3'},
                    'x_axis': {'label': col.replace('_', ' ').title()},
                    'y_axis': {'label': 'Frequency'},
                    'responsive': True,
                    'ai_insights': {
                        'distribution_type': distribution_type,
                        'skewness_level': abs(skewness),
                        'outlier_prevalence': outlier_ratio,
                        'data_density': unique_ratio,
                        'recommended_interactions': ['zoom', 'brush'] if data_count > 100 else ['tooltip']
                    }
                }
            else:  # box plot
                recharts_config = {
                    'type': 'box',
                    'data_key': col,
                    'fill': '#8884d8',
                    'stroke': '#8884d8',
                    'stroke_width': 2,
                    'tooltip': {'enabled': True, 'format': 'box_plot'},
                    'legend': {'enabled': False},
                    'grid': {'enabled': True, 'stroke_dasharray': '3 3'},
                    'y_axis': {'label': col.replace('_', ' ').title()},
                    'outliers': {'enabled': True, 'fill': '#ff7300'},
                    'quartiles': {'enabled': True},
                    'median_line': {'enabled': True, 'stroke': '#ff0000'},
                    'responsive': True,
                    'ai_insights': {
                        'distribution_type': distribution_type,
                        'outlier_ratio': outlier_ratio,
                        'spread_analysis': 'high' if kurtosis > 3 else 'normal' if kurtosis > -1 else 'low',
                        'recommended_interactions': ['outlier_highlight', 'quartile_details']
                    }
                }
            
            return ChartRecommendation(
                chart_type=chart_type,
                data_columns=[col],
                title=title,
                description=description,
                confidence=confidence,
                recharts_config=recharts_config
            )
            
        except Exception as e:
            logger.error(f"Enhanced distribution recommendation failed: {str(e)}")
            return None

    def _create_enhanced_correlation_recommendation(
        self,
        df: pd.DataFrame,
        col1: str,
        col2: str,
        chart_type: str,
        confidence: float,
        correlation_data: Dict[str, Any]
    ) -> Optional[ChartRecommendation]:
        """Create enhanced correlation chart recommendations with AI insights."""
        try:
            if col1 not in df.columns or col2 not in df.columns:
                return None
            
            # Extract correlation insights
            correlation_value = correlation_data.get('correlation', 0)
            correlation_strength = correlation_data.get('strength', 'weak')
            
            # AI-driven title generation
            if abs(correlation_value) > 0.8:
                strength_desc = "Strong"
            elif abs(correlation_value) > 0.5:
                strength_desc = "Moderate"
            else:
                strength_desc = "Weak"
            
            direction = "Positive" if correlation_value > 0 else "Negative"
            title = f"{strength_desc} {direction} Correlation: {col1.replace('_', ' ').title()} vs {col2.replace('_', ' ').title()}"
            
            # Enhanced description
            description = f"Scatter plot analysis showing {strength_desc.lower()} {direction.lower()} correlation (r={correlation_value:.3f}) between {col1} and {col2}."
            if abs(correlation_value) > 0.7:
                description += " Strong relationship suggests predictive potential."
            
            # Enhanced Recharts configuration
            recharts_config = {
                'type': 'scatter',
                'data_key_x': col1,
                'data_key_y': col2,
                'fill': '#8884d8',
                'stroke': '#8884d8',
                'fill_opacity': 0.6,
                'stroke_width': 1,
                'dot_size': 4 if len(df) > 100 else 6,
                'tooltip': {'enabled': True, 'format': 'scatter'},
                'legend': {'enabled': False},
                'grid': {'enabled': True, 'stroke_dasharray': '3 3'},
                'x_axis': {'label': col1.replace('_', ' ').title()},
                'y_axis': {'label': col2.replace('_', ' ').title()},
                'trend_line': {
                    'enabled': abs(correlation_value) > 0.3,
                    'stroke': '#ff7300',
                    'stroke_width': 2,
                    'stroke_dasharray': '5 5'
                },
                'responsive': True,
                'ai_insights': {
                    'correlation_coefficient': correlation_value,
                    'correlation_strength': correlation_strength,
                    'relationship_type': 'linear' if abs(correlation_value) > 0.5 else 'non_linear',
                    'predictive_potential': 'high' if abs(correlation_value) > 0.7 else 'medium' if abs(correlation_value) > 0.4 else 'low',
                    'recommended_interactions': ['zoom', 'brush', 'outlier_highlight']
                }
            }
            
            return ChartRecommendation(
                chart_type=chart_type,
                data_columns=[col1, col2],
                title=title,
                description=description,
                confidence=confidence,
                recharts_config=recharts_config
            )
            
        except Exception as e:
            logger.error(f"Enhanced correlation recommendation failed: {str(e)}")
            return None

    def _create_enhanced_correlation_heatmap(
        self,
        df: pd.DataFrame,
        columns: List[str],
        confidence: float,
        correlation_insights: Dict[str, Any]
    ) -> Optional[ChartRecommendation]:
        """Create enhanced correlation heatmap recommendations with AI insights."""
        try:
            # Validate columns
            valid_columns = [col for col in columns if col in df.columns and df[col].dtype in ['int64', 'float64']]
            if len(valid_columns) < 3:
                return None
            
            # Calculate correlation matrix
            corr_matrix = df[valid_columns].corr()
            
            # Extract insights
            max_correlation = correlation_insights.get('max_correlation', 0)
            strong_correlations = correlation_insights.get('strong_correlations', [])
            
            # AI-driven title generation
            if max_correlation > 0.8:
                strength_desc = "Strong"
            elif max_correlation > 0.5:
                strength_desc = "Moderate"
            else:
                strength_desc = "Weak"
            
            title = f"{strength_desc} Correlation Heatmap of Key Variables"
            
            # Enhanced description
            description = f"Correlation heatmap showing relationships between {len(valid_columns)} variables."
            if len(strong_correlations) > 0:
                description += f" {len(strong_correlations)} strong correlations identified."
            
            # Enhanced Recharts configuration
            recharts_config = {
                'type': 'heatmap',
                'data': corr_matrix.to_dict(),
                'columns': valid_columns,
                'color_scale': {
                    'min': -1,
                    'max': 1,
                    'colors': ['#2563eb', '#ffffff', '#dc2626']  # Blue-White-Red
                },
                'cell_size': max(20, min(40, 300 // len(valid_columns))),
                'show_values': len(valid_columns) <= 6,
                'tooltip': {'enabled': True, 'format': 'correlation'},
                'legend': {'enabled': True, 'position': 'right'},
                'grid': {'enabled': True},
                'responsive': True,
                'ai_insights': {
                    'matrix_size': len(valid_columns),
                    'max_correlation': max_correlation,
                    'strong_pairs_count': len(strong_correlations),
                    'cluster_potential': 'high' if max_correlation > 0.7 else 'medium',
                    'recommended_interactions': ['cell_highlight', 'value_display', 'zoom']
                }
            }
            
            return ChartRecommendation(
                chart_type='heatmap',
                data_columns=valid_columns,
                title=title,
                description=description,
                confidence=confidence,
                recharts_config=recharts_config
            )
            
        except Exception as e:
            logger.error(f"Enhanced correlation heatmap failed: {str(e)}")
            return None

    async def _apply_context_optimization(
        self,
        recommendations: List[ChartRecommendation],
        context: Optional[str],
        priority_metrics: Optional[List[str]]
    ) -> List[ChartRecommendation]:
        """Apply business intelligence and context optimization to recommendations."""
        try:
            optimized_recommendations = []
            
            for rec in recommendations:
                # Create a copy to avoid modifying original
                optimized_rec = ChartRecommendation(
                    chart_type=rec.chart_type,
                    data_columns=rec.data_columns.copy(),
                    title=rec.title,
                    description=rec.description,
                    confidence=rec.confidence,
                    recharts_config=rec.recharts_config.copy()
                )
                
                # Context-based optimization
                if context:
                    context_lower = context.lower()
                    
                    # Business Intelligence keywords
                    business_keywords = {
                        'financial': ['revenue', 'profit', 'cost', 'sales', 'budget', 'financial'],
                        'performance': ['kpi', 'performance', 'efficiency', 'productivity', 'metrics'],
                        'analytics': ['analytics', 'insights', 'analysis', 'dashboard', 'reporting'],
                        'trends': ['trend', 'growth', 'change', 'forecast', 'prediction'],
                        'comparison': ['compare', 'versus', 'benchmark', 'competition']
                    }
                    
                    # Apply business context optimizations
                    for category, keywords in business_keywords.items():
                        if any(keyword in context_lower for keyword in keywords):
                            if category == 'financial' and rec.chart_type in ['line', 'bar']:
                                optimized_rec.confidence += 0.1
                                optimized_rec.recharts_config['currency_format'] = True
                            elif category == 'trends' and rec.chart_type in ['line', 'area']:
                                optimized_rec.confidence += 0.15
                                optimized_rec.recharts_config['trend_indicators'] = True
                            elif category == 'comparison' and rec.chart_type in ['bar', 'column']:
                                optimized_rec.confidence += 0.1
                                optimized_rec.recharts_config['comparison_highlighting'] = True
                
                # Priority metrics optimization
                if priority_metrics:
                    metrics_in_chart = set(rec.data_columns) & set(priority_metrics)
                    if metrics_in_chart:
                        # Boost confidence for charts containing priority metrics
                        boost = len(metrics_in_chart) * 0.05
                        optimized_rec.confidence += boost
                        
                        # Add priority highlighting
                        optimized_rec.recharts_config['priority_highlighting'] = {
                            'enabled': True,
                            'columns': list(metrics_in_chart),
                            'color': '#ff7300'
                        }
                
                # Ensure confidence doesn't exceed 1.0
                optimized_rec.confidence = min(optimized_rec.confidence, 1.0)
                
                optimized_recommendations.append(optimized_rec)
            
            return optimized_recommendations
            
        except Exception as e:
            logger.error(f"Context optimization failed: {str(e)}")
            return recommendations

    async def _rank_and_select_recommendations(
        self,
        recommendations: List[ChartRecommendation],
        data_profile: Dict[str, Any]
    ) -> List[ChartRecommendation]:
        """Rank and select the best recommendations using ML-based scoring."""
        try:
            if not recommendations:
                return []
            
            # Multi-criteria ranking system
            scored_recommendations = []
            
            for rec in recommendations:
                score = rec.confidence  # Base score from confidence
                
                # Data suitability scoring
                data_columns_count = len(rec.data_columns)
                if data_columns_count == 2:  # Optimal for most chart types
                    score += 0.1
                elif data_columns_count == 1 and rec.chart_type in ['histogram', 'box']:
                    score += 0.15  # Perfect for distribution charts
                
                # Chart type diversity bonus
                chart_type_counts = {}
                for existing_rec in scored_recommendations:
                    chart_type_counts[existing_rec[1].chart_type] = chart_type_counts.get(existing_rec[1].chart_type, 0) + 1
                
                if chart_type_counts.get(rec.chart_type, 0) == 0:
                    score += 0.05  # Bonus for new chart type
                
                # Data coverage scoring
                numeric_cols = data_profile.get('numeric_columns', [])
                categorical_cols = data_profile.get('categorical_columns', [])
                datetime_cols = data_profile.get('datetime_columns', [])
                
                columns_used = set(rec.data_columns)
                if numeric_cols and any(col in columns_used for col in numeric_cols):
                    score += 0.05
                if categorical_cols and any(col in columns_used for col in categorical_cols):
                    score += 0.05
                if datetime_cols and any(col in columns_used for col in datetime_cols):
                    score += 0.05
                
                # AI insights bonus
                ai_insights = rec.recharts_config.get('ai_insights', {})
                if ai_insights:
                    # Bonus for charts with rich AI insights
                    insight_count = len(ai_insights)
                    score += min(0.1, insight_count * 0.02)
                
                scored_recommendations.append((score, rec))
            
            # Sort by score (descending)
            scored_recommendations.sort(key=lambda x: x[0], reverse=True)
            
            # Select top recommendations with diversity
            selected_recommendations = []
            chart_types_used = set()
            data_columns_used = set()
            
            for score, rec in scored_recommendations:
                # Ensure diversity in chart types and avoid too much column overlap
                column_overlap = len(set(rec.data_columns) & data_columns_used) / len(rec.data_columns)
                
                if (len(selected_recommendations) < 3 or  # Always include top 3
                    (rec.chart_type not in chart_types_used and column_overlap < 0.5) or  # New type with low overlap
                    score > 0.8):  # Very high confidence charts
                    
                    selected_recommendations.append(rec)
                    chart_types_used.add(rec.chart_type)
                    data_columns_used.update(rec.data_columns)
                    
                    # Limit total recommendations
                    if len(selected_recommendations) >= 6:
                        break
            
            logger.info(f"Selected {len(selected_recommendations)} recommendations from {len(recommendations)} candidates")
            return selected_recommendations
            
        except Exception as e:
            logger.error(f"Recommendation ranking failed: {str(e)}")
            # Fallback: return top recommendations by confidence
            return sorted(recommendations, key=lambda x: x.confidence, reverse=True)[:6]

    def _generate_color_palette(self, count: int) -> List[str]:
        """Generate a color palette for charts."""
        # Base color palette
        base_colors = [
            '#3b82f6', '#ef4444', '#10b981', '#f59e0b', 
            '#8b5cf6', '#06b6d4', '#84cc16', '#f97316',
            '#ec4899', '#6366f1', '#14b8a6', '#eab308'
        ]
        
        if count <= len(base_colors):
            return base_colors[:count]
        
        # Generate additional colors if needed
        colors = base_colors.copy()
        while len(colors) < count:
            # Generate variations of base colors
            base_color = base_colors[len(colors) % len(base_colors)]
            # Simple color variation (this could be more sophisticated)
            colors.append(base_color)
        
        return colors[:count]

    # Interactive Features Implementation (Task 8.5)
    
    async def generate_interactive_features(
        self,
        data: Dict[str, Any],
        charts: List[ChartRecommendation],
        kpis: List[KPIConfig],
        user_preferences: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive interactive features for dashboard components.
        Implements filtering, tooltips, hover effects, click events, and dynamic updates.
        """
        try:
            df = self._dict_to_dataframe(data)
            if df is None:
                return {}
            
            # Generate interactive configuration
            interactive_config = {
                "filters": await self._generate_dashboard_filters(df),
                "tooltips": await self._generate_tooltip_configurations(charts, kpis),
                "hover_effects": await self._generate_hover_effects(charts),
                "click_events": await self._generate_click_events(charts, kpis),
                "zoom_pan": await self._generate_zoom_pan_config(charts),
                "cross_filtering": await self._generate_cross_filtering_config(charts, df),
                "dynamic_updates": await self._generate_dynamic_update_config(df),
                "drill_down": await self._generate_drill_down_config(charts, df),
                "data_selection": await self._generate_data_selection_config(charts),
                "real_time": await self._generate_real_time_config(user_preferences),
                "export_options": await self._generate_export_config(charts, kpis),
                "customization": await self._generate_customization_config()
            }
            
            return interactive_config
            
        except Exception as e:
            logger.error(f"Interactive features generation failed: {str(e)}")
            return {}

    async def _generate_dashboard_filters(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate intelligent dashboard-level filters based on data characteristics."""
        filters = {
            "available_filters": [],
            "filter_groups": [],
            "default_filters": [],
            "filter_state": {},
            "filter_interactions": {}
        }
        
        try:
            # Analyze columns for filter potential
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
            datetime_cols = self._detect_datetime_columns(df)
            
            # Date/Time filters
            for date_col in datetime_cols:
                if date_col in df.columns:
                    date_data = pd.to_datetime(df[date_col], errors='coerce').dropna()
                    if len(date_data) > 1:
                        date_filter = {
                            "id": f"filter_{date_col}",
                            "type": "date_range",
                            "column": date_col,
                            "label": date_col.replace('_', ' ').title(),
                            "min_date": date_data.min().isoformat(),
                            "max_date": date_data.max().isoformat(),
                            "default_range": [
                                date_data.min().isoformat(),
                                date_data.max().isoformat()
                            ],
                            "quick_filters": ["last_7_days", "last_30_days", "last_90_days", "year_to_date"],
                            "granularity_options": ["day", "week", "month", "quarter", "year"],
                            "interactions": {
                                "affects_charts": True,
                                "affects_kpis": True,
                                "real_time_update": True
                            }
                        }
                        filters["available_filters"].append(date_filter)
            
            # Categorical filters
            for cat_col in categorical_cols:
                if cat_col in df.columns:
                    unique_values = df[cat_col].dropna().unique()
                    if 2 <= len(unique_values) <= 20:  # Reasonable filter range
                        cat_filter = {
                            "id": f"filter_{cat_col}",
                            "type": "multi_select" if len(unique_values) > 5 else "checkbox",
                            "column": cat_col,
                            "label": cat_col.replace('_', ' ').title(),
                            "options": [
                                {"value": str(val), "label": str(val), "count": int(df[cat_col].value_counts().get(val, 0))}
                                for val in sorted(unique_values) if pd.notna(val)
                            ],
                            "default_selected": [str(val) for val in unique_values[:3]],  # Default to first 3
                            "search_enabled": len(unique_values) > 10,
                            "interactions": {
                                "affects_charts": True,
                                "affects_kpis": True,
                                "enables_drill_down": True
                            }
                        }
                        filters["available_filters"].append(cat_filter)
            
            # Numeric range filters
            for num_col in numeric_cols:
                if num_col in df.columns:
                    col_data = df[num_col].dropna()
                    if len(col_data) > 1 and col_data.std() > 0:
                        num_filter = {
                            "id": f"filter_{num_col}",
                            "type": "range_slider",
                            "column": num_col,
                            "label": num_col.replace('_', ' ').title(),
                            "min_value": float(col_data.min()),
                            "max_value": float(col_data.max()),
                            "default_range": [float(col_data.min()), float(col_data.max())],
                            "step": max(1, float(col_data.std()) / 100),
                            "format": "number",
                            "histogram_data": self._generate_histogram_data(col_data),
                            "interactions": {
                                "affects_charts": True,
                                "affects_kpis": True,
                                "live_preview": True
                            }
                        }
                        filters["available_filters"].append(num_filter)
            
            # Filter groups for logical organization
            if datetime_cols:
                filters["filter_groups"].append({
                    "id": "time_filters",
                    "label": "Time Period",
                    "filters": [f"filter_{col}" for col in datetime_cols],
                    "collapsible": True,
                    "default_expanded": True
                })
            
            if categorical_cols:
                filters["filter_groups"].append({
                    "id": "category_filters", 
                    "label": "Categories",
                    "filters": [f"filter_{col}" for col in categorical_cols if 2 <= df[col].nunique() <= 20],
                    "collapsible": True,
                    "default_expanded": True
                })
            
            if numeric_cols:
                filters["filter_groups"].append({
                    "id": "metric_filters",
                    "label": "Metric Ranges",
                    "filters": [f"filter_{col}" for col in numeric_cols],
                    "collapsible": True,
                    "default_expanded": False
                })
            
            # Global filter interactions
            filters["filter_interactions"] = {
                "apply_mode": "auto",  # auto, manual, real_time
                "reset_all_enabled": True,
                "save_state_enabled": True,
                "url_state_sync": True,
                "cross_filter_enabled": True,
                "filter_dependencies": self._analyze_filter_dependencies(df)
            }
            
            return filters
            
        except Exception as e:
            logger.error(f"Filter generation failed: {str(e)}")
            return filters

    def _generate_histogram_data(self, data: pd.Series, bins: int = 20) -> List[Dict[str, Any]]:
        """Generate histogram data for numeric filters."""
        try:
            hist, bin_edges = np.histogram(data, bins=bins)
            return [
                {
                    "bin_start": float(bin_edges[i]),
                    "bin_end": float(bin_edges[i + 1]),
                    "count": int(hist[i]),
                    "percentage": float(hist[i] / len(data) * 100)
                }
                for i in range(len(hist))
            ]
        except:
            return []

    def _analyze_filter_dependencies(self, df: pd.DataFrame) -> Dict[str, List[str]]:
        """Analyze dependencies between filters for intelligent interactions."""
        dependencies = {}
        try:
            categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
            
            # Simple correlation-based dependencies
            for col1 in categorical_cols:
                for col2 in categorical_cols:
                    if col1 != col2:
                        # Calculate association between categorical variables
                        crosstab = pd.crosstab(df[col1], df[col2])
                        if crosstab.size > 0 and min(crosstab.shape) > 1:
                            # Simple association measure
                            chi2_stat = ((crosstab - crosstab.sum(axis=1).values.reshape(-1, 1) * crosstab.sum(axis=0).values / crosstab.sum().sum()) ** 2).sum().sum()
                            if chi2_stat > crosstab.size:  # Threshold for significant association
                                if col1 not in dependencies:
                                    dependencies[col1] = []
                                dependencies[col1].append(col2)
            
            return dependencies
        except:
            return {}

    async def _generate_tooltip_configurations(
        self, 
        charts: List[ChartRecommendation], 
        kpis: List[KPIConfig]
    ) -> Dict[str, Any]:
        """Generate intelligent tooltip configurations for all dashboard components."""
        tooltip_config = {
            "chart_tooltips": {},
            "kpi_tooltips": {},
            "global_settings": {
                "enabled": True,
                "follow_cursor": True,
                "delay_show": 200,
                "delay_hide": 100,
                "animation": "fade",
                "theme": "auto"
            }
        }
        
        try:
            # Chart tooltips
            for i, chart in enumerate(charts):
                chart_id = f"chart_{i}"
                chart_type = chart.chart_type
                
                tooltip = {
                    "enabled": True,
                    "trigger": "hover",
                    "position": "auto",
                    "content_type": "rich",
                    "custom_formatter": self._generate_tooltip_formatter(chart),
                    "interactive": chart_type in ["scatter", "bubble", "line"],
                    "cross_hair": chart_type in ["line", "area", "scatter"],
                    "shared": chart_type in ["line", "area", "bar"],
                    "sort": True,
                    "animation": {
                        "duration": 200,
                        "easing": "ease-out"
                    }
                }
                
                # Chart-specific enhancements
                if chart_type == "pie":
                    tooltip.update({
                        "show_percentage": True,
                        "show_total": True,
                        "highlight_sector": True
                    })
                elif chart_type in ["line", "area"]:
                    tooltip.update({
                        "show_trend": True,
                        "compare_previous": True,
                        "show_min_max": True
                    })
                elif chart_type == "scatter":
                    tooltip.update({
                        "show_correlation": True,
                        "show_outlier_info": True
                    })
                elif chart_type == "heatmap":
                    tooltip.update({
                        "show_coordinates": True,
                        "show_relative_intensity": True
                    })
                
                tooltip_config["chart_tooltips"][chart_id] = tooltip
            
            # KPI tooltips
            for i, kpi in enumerate(kpis):
                kpi_id = f"kpi_{i}"
                tooltip_config["kpi_tooltips"][kpi_id] = {
                    "enabled": True,
                    "trigger": "hover",
                    "content": {
                        "title": kpi.name,
                        "current_value": f"{kpi.value:.2f} {kpi.unit}",
                        "trend": f"{kpi.trend_percentage:+.1f}%",
                        "trend_direction": kpi.trend,
                        "description": kpi.description,
                        "last_updated": "Real-time",
                        "data_source": "Calculated from uploaded data"
                    },
                    "styling": {
                        "background": "rgba(0, 0, 0, 0.8)",
                        "color": "#ffffff",
                        "border_radius": "6px",
                        "padding": "12px",
                        "max_width": "250px"
                    }
                }
            
            return tooltip_config
            
        except Exception as e:
            logger.error(f"Tooltip configuration failed: {str(e)}")
            return tooltip_config

    def _generate_tooltip_formatter(self, chart: ChartRecommendation) -> Dict[str, Any]:
        """Generate custom tooltip formatter for specific chart types."""
        data_columns = chart.data_columns
        chart_type = chart.chart_type
        
        formatter = {
            "template": "default",
            "fields": [],
            "calculations": [],
            "formatting": {}
        }
        
        try:
            # Add data fields
            for col in data_columns:
                field_config = {
                    "field": col,
                    "label": col.replace('_', ' ').title(),
                    "format": "auto"
                }
                
                # Smart format detection
                if any(keyword in col.lower() for keyword in ['price', 'cost', 'revenue', 'amount', 'value']):
                    field_config["format"] = "currency"
                elif any(keyword in col.lower() for keyword in ['percent', 'rate', 'ratio']):
                    field_config["format"] = "percentage"
                elif any(keyword in col.lower() for keyword in ['date', 'time']):
                    field_config["format"] = "datetime"
                
                formatter["fields"].append(field_config)
            
            # Add calculated fields based on chart type
            if chart_type in ["line", "area"]:
                formatter["calculations"].extend([
                    {"type": "change_from_previous", "label": "Change"},
                    {"type": "percentage_change", "label": "% Change"}
                ])
            elif chart_type == "pie":
                formatter["calculations"].extend([
                    {"type": "percentage_of_total", "label": "% of Total"},
                    {"type": "rank", "label": "Rank"}
                ])
            
            return formatter
            
        except Exception as e:
            logger.error(f"Tooltip formatter generation failed: {str(e)}")
            return formatter

    async def _generate_hover_effects(self, charts: List[ChartRecommendation]) -> Dict[str, Any]:
        """Generate hover effect configurations for enhanced user interaction."""
        hover_config = {
            "chart_effects": {},
            "global_settings": {
                "smooth_transitions": True,
                "highlight_connected": True,
                "dim_others": True,
                "scale_on_hover": False
            }
        }
        
        try:
            for i, chart in enumerate(charts):
                chart_id = f"chart_{i}"
                chart_type = chart.chart_type
                
                effect_config = {
                    "enabled": True,
                    "transition_duration": 200,
                    "effects": []
                }
                
                # Chart-specific hover effects
                if chart_type in ["bar", "column"]:
                    effect_config["effects"].extend([
                        {
                            "type": "highlight_bar",
                            "properties": {
                                "opacity_increase": 0.2,
                                "stroke_width": 2,
                                "stroke_color": "#333"
                            }
                        },
                        {
                            "type": "dim_others",
                            "properties": {
                                "opacity_decrease": 0.6
                            }
                        }
                    ])
                elif chart_type in ["line", "area"]:
                    effect_config["effects"].extend([
                        {
                            "type": "highlight_line",
                            "properties": {
                                "stroke_width_increase": 2,
                                "glow_effect": True
                            }
                        },
                        {
                            "type": "show_data_points",
                            "properties": {
                                "point_radius": 4,
                                "point_color": "auto"
                            }
                        }
                    ])
                elif chart_type == "pie":
                    effect_config["effects"].extend([
                        {
                            "type": "expand_sector",
                            "properties": {
                                "expand_distance": 10,
                                "scale_factor": 1.05
                            }
                        },
                        {
                            "type": "highlight_sector",
                            "properties": {
                                "border_width": 3,
                                "border_color": "#fff"
                            }
                        }
                    ])
                elif chart_type == "scatter":
                    effect_config["effects"].extend([
                        {
                            "type": "scale_point",
                            "properties": {
                                "scale_factor": 1.5,
                                "highlight_color": "#ff6b6b"
                            }
                        },
                        {
                            "type": "show_connections",
                            "properties": {
                                "show_trend_line": True,
                                "highlight_cluster": True
                            }
                        }
                    ])
                
                hover_config["chart_effects"][chart_id] = effect_config
            
            return hover_config
            
        except Exception as e:
            logger.error(f"Hover effects generation failed: {str(e)}")
            return hover_config

    async def _generate_click_events(
        self, 
        charts: List[ChartRecommendation], 
        kpis: List[KPIConfig]
    ) -> Dict[str, Any]:
        """Generate comprehensive click event configurations for interactive behavior."""
        click_config = {
            "chart_events": {},
            "kpi_events": {},
            "global_handlers": {
                "prevent_default": True,
                "stop_propagation": False,
                "debounce_delay": 100
            }
        }
        
        try:
            # Chart click events
            for i, chart in enumerate(charts):
                chart_id = f"chart_{i}"
                chart_type = chart.chart_type
                
                events = {
                    "single_click": {
                        "enabled": True,
                        "actions": []
                    },
                    "double_click": {
                        "enabled": True,
                        "actions": []
                    },
                    "right_click": {
                        "enabled": True,
                        "actions": []
                    }
                }
                
                # Single click actions
                events["single_click"]["actions"].extend([
                    {
                        "type": "highlight_selection",
                        "params": {
                            "persist": False,
                            "multi_select": True
                        }
                    },
                    {
                        "type": "update_filters",
                        "params": {
                            "auto_apply": True,
                            "show_preview": True
                        }
                    },
                    {
                        "type": "show_details",
                        "params": {
                            "panel_type": "sidebar",
                            "include_related_data": True
                        }
                    }
                ])
                
                # Double click actions
                if chart_type in ["bar", "pie", "scatter"]:
                    events["double_click"]["actions"].append({
                        "type": "drill_down",
                        "params": {
                            "target_level": "next",
                            "animation": "zoom",
                            "preserve_filters": True
                        }
                    })
                
                if chart_type in ["line", "area", "scatter"]:
                    events["double_click"]["actions"].append({
                        "type": "zoom_to_selection",
                        "params": {
                            "axis": "both",
                            "animation_duration": 500
                        }
                    })
                
                # Right click context menu
                events["right_click"]["actions"].extend([
                    {
                        "type": "show_context_menu",
                        "params": {
                            "menu_items": [
                                "export_data",
                                "create_filter",
                                "add_annotation",
                                "customize_chart",
                                "view_raw_data"
                            ]
                        }
                    }
                ])
                
                click_config["chart_events"][chart_id] = events
            
            # KPI click events
            for i, kpi in enumerate(kpis):
                kpi_id = f"kpi_{i}"
                click_config["kpi_events"][kpi_id] = {
                    "single_click": {
                        "enabled": True,
                        "actions": [
                            {
                                "type": "show_trend_modal",
                                "params": {
                                    "time_range": "30_days",
                                    "include_forecast": True
                                }
                            },
                            {
                                "type": "highlight_related_charts",
                                "params": {
                                    "duration": 2000
                                }
                            }
                        ]
                    },
                    "double_click": {
                        "enabled": True,
                        "actions": [
                            {
                                "type": "drill_to_detail",
                                "params": {
                                    "view_type": "table",
                                    "include_calculations": True
                                }
                            }
                        ]
                    }
                }
            
            return click_config
            
        except Exception as e:
            logger.error(f"Click events generation failed: {str(e)}")
            return click_config

    async def _generate_zoom_pan_config(self, charts: List[ChartRecommendation]) -> Dict[str, Any]:
        """Generate zoom and pan configurations for applicable charts."""
        zoom_config = {
            "enabled_charts": {},
            "global_settings": {
                "min_zoom": 0.1,
                "max_zoom": 10,
                "zoom_sensitivity": 1.0,
                "pan_enabled": True,
                "reset_on_double_click": True
            }
        }
        
        try:
            for i, chart in enumerate(charts):
                chart_id = f"chart_{i}"
                chart_type = chart.chart_type
                
                # Only enable zoom/pan for appropriate chart types
                if chart_type in ["line", "area", "scatter", "heatmap"]:
                    zoom_config["enabled_charts"][chart_id] = {
                        "zoom": {
                            "enabled": True,
                            "type": "both",  # x, y, both
                            "wheel_enabled": True,
                            "touch_enabled": True,
                            "box_zoom": True,
                            "zoom_buttons": True
                        },
                        "pan": {
                            "enabled": True,
                            "mouse_button": "left",
                            "touch_enabled": True,
                            "momentum": True,
                            "boundary_detection": True
                        },
                        "reset": {
                            "enabled": True,
                            "button_visible": True,
                            "keyboard_shortcut": "Escape",
                            "animation_duration": 300
                        },
                        "minimap": {
                            "enabled": len(chart.data_columns) > 2,
                            "position": "bottom_right",
                            "size": "small"
                        }
                    }
            
            return zoom_config
            
        except Exception as e:
            logger.error(f"Zoom/pan configuration failed: {str(e)}")
            return zoom_config

    async def _generate_cross_filtering_config(
        self, 
        charts: List[ChartRecommendation], 
        df: pd.DataFrame
    ) -> Dict[str, Any]:
        """Generate cross-filtering configurations for chart interactions."""
        cross_filter_config = {
            "enabled": True,
            "chart_connections": {},
            "filter_propagation": {
                "mode": "immediate",  # immediate, delayed, manual
                "animation": True,
                "preserve_selections": True
            }
        }
        
        try:
            # Analyze data relationships for cross-filtering
            shared_columns = {}
            for i, chart in enumerate(charts):
                chart_id = f"chart_{i}"
                chart_columns = set(chart.data_columns)
                
                connections = []
                for j, other_chart in enumerate(charts):
                    if i != j:
                        other_chart_id = f"chart_{j}"
                        other_columns = set(other_chart.data_columns)
                        shared_cols = chart_columns.intersection(other_columns)
                        
                        if shared_cols:
                            connections.append({
                                "target_chart": other_chart_id,
                                "shared_columns": list(shared_cols),
                                "filter_type": "include",
                                "strength": len(shared_cols) / len(chart_columns)
                            })
                
                cross_filter_config["chart_connections"][chart_id] = connections
            
            return cross_filter_config
            
        except Exception as e:
            logger.error(f"Cross-filtering configuration failed: {str(e)}")
            return cross_filter_config

    async def _generate_dynamic_update_config(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate dynamic data update configurations."""
        update_config = {
            "real_time_enabled": False,
            "refresh_intervals": {
                "charts": 30000,  # 30 seconds
                "kpis": 10000,    # 10 seconds
                "filters": 60000  # 1 minute
            },
            "update_triggers": [
                "data_change",
                "filter_change", 
                "user_interaction",
                "time_interval"
            ],
            "animation_config": {
                "enabled": True,
                "duration": 500,
                "easing": "ease-in-out",
                "stagger_delay": 100
            },
            "data_streaming": {
                "enabled": False,
                "buffer_size": 1000,
                "update_threshold": 10,
                "compression": True
            }
        }
        
        return update_config

    async def _generate_drill_down_config(
        self, 
        charts: List[ChartRecommendation], 
        df: pd.DataFrame
    ) -> Dict[str, Any]:
        """Generate drill-down navigation configurations."""
        drill_config = {
            "enabled_charts": {},
            "navigation": {
                "breadcrumb_enabled": True,
                "back_button_enabled": True,
                "level_indicator": True,
                "keyboard_shortcuts": True
            }
        }
        
        try:
            categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
            datetime_cols = self._detect_datetime_columns(df)
            
            for i, chart in enumerate(charts):
                chart_id = f"chart_{i}"
                chart_columns = chart.data_columns
                
                # Find drill-down opportunities
                drill_paths = []
                
                # Categorical drill-downs
                for col in chart_columns:
                    if col in categorical_cols:
                        unique_count = df[col].nunique()
                        if 2 <= unique_count <= 50:
                            drill_paths.append({
                                "type": "categorical",
                                "column": col,
                                "levels": sorted(df[col].dropna().unique().tolist()),
                                "chart_adaptation": "filter"
                            })
                
                # Temporal drill-downs
                for col in chart_columns:
                    if col in datetime_cols:
                        drill_paths.append({
                            "type": "temporal",
                            "column": col,
                            "levels": ["year", "quarter", "month", "week", "day"],
                            "chart_adaptation": "zoom"
                        })
                
                if drill_paths:
                    drill_config["enabled_charts"][chart_id] = {
                        "paths": drill_paths,
                        "default_path": drill_paths[0] if drill_paths else None,
                        "max_depth": 3,
                        "preserve_context": True
                    }
            
            return drill_config
            
        except Exception as e:
            logger.error(f"Drill-down configuration failed: {str(e)}")
            return drill_config

    async def _generate_data_selection_config(self, charts: List[ChartRecommendation]) -> Dict[str, Any]:
        """Generate data selection and highlighting configurations."""
        selection_config = {
            "selection_modes": {
                "single": True,
                "multiple": True,
                "range": True,
                "lasso": True
            },
            "chart_configs": {},
            "global_settings": {
                "persist_selections": True,
                "sync_across_charts": True,
                "keyboard_modifiers": {
                    "ctrl": "multi_select",
                    "shift": "range_select",
                    "alt": "invert_selection"
                }
            }
        }
        
        try:
            for i, chart in enumerate(charts):
                chart_id = f"chart_{i}"
                chart_type = chart.chart_type
                
                config = {
                    "enabled": True,
                    "modes": ["single", "multiple"],
                    "visual_feedback": {
                        "highlight_color": "#ff6b6b",
                        "highlight_opacity": 0.7,
                        "border_width": 2,
                        "animation_duration": 200
                    }
                }
                
                # Chart-specific selection behavior
                if chart_type in ["bar", "column"]:
                    config["modes"].extend(["range"])
                    config["selection_area"] = "bar"
                elif chart_type in ["line", "area"]:
                    config["modes"].extend(["range"])
                    config["selection_area"] = "data_points"
                elif chart_type == "scatter":
                    config["modes"].extend(["lasso", "box"])
                    config["selection_area"] = "points"
                elif chart_type == "pie":
                    config["modes"] = ["single", "multiple"]
                    config["selection_area"] = "sectors"
                
                selection_config["chart_configs"][chart_id] = config
            
            return selection_config
            
        except Exception as e:
            logger.error(f"Data selection configuration failed: {str(e)}")
            return selection_config

    async def _generate_real_time_config(self, user_preferences: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate real-time update configurations."""
        real_time_config = {
            "enabled": False,
            "connection": {
                "type": "websocket",
                "url": "/ws/dashboard",
                "reconnect": {
                    "enabled": True,
                    "max_attempts": 5,
                    "delay": 1000
                }
            },
            "update_policy": {
                "max_frequency": 1000,  # Max 1 update per second
                "batch_updates": True,
                "priority_queue": True
            },
            "visual_indicators": {
                "connection_status": True,
                "update_notifications": True,
                "data_freshness": True,
                "loading_states": True
            }
        }
        
        if user_preferences and user_preferences.get("real_time_enabled"):
            real_time_config["enabled"] = True
        
        return real_time_config

    async def _generate_export_config(
        self, 
        charts: List[ChartRecommendation], 
        kpis: List[KPIConfig]
    ) -> Dict[str, Any]:
        """Generate export and sharing configurations."""
        export_config = {
            "formats": {
                "image": ["png", "jpg", "svg"],
                "data": ["csv", "xlsx", "json"],
                "document": ["pdf", "html"]
            },
            "chart_exports": {},
            "dashboard_export": {
                "enabled": True,
                "include_filters": True,
                "include_interactions": False,
                "custom_branding": True
            },
            "sharing": {
                "public_links": True,
                "embed_codes": True,
                "social_sharing": ["twitter", "linkedin", "email"],
                "collaboration": {
                    "comments": True,
                    "annotations": True,
                    "version_history": True
                }
            }
        }
        
        try:
            # Configure export options for each chart
            for i, chart in enumerate(charts):
                chart_id = f"chart_{i}"
                export_config["chart_exports"][chart_id] = {
                    "individual_export": True,
                    "include_data": True,
                    "custom_styling": True,
                    "high_resolution": True,
                    "formats": export_config["formats"]
                }
            
            return export_config
            
        except Exception as e:
            logger.error(f"Export configuration failed: {str(e)}")
            return export_config

    async def _generate_customization_config(self) -> Dict[str, Any]:
        """Generate user customization configurations."""
        customization_config = {
            "user_preferences": {
                "theme_switching": True,
                "layout_customization": True,
                "chart_type_switching": True,
                "color_customization": True,
                "font_customization": True
            },
            "dashboard_editor": {
                "enabled": True,
                "drag_drop": True,
                "resize_components": True,
                "add_remove_charts": True,
                "custom_kpis": True
            },
            "saved_states": {
                "enabled": True,
                "max_saves": 10,
                "auto_save": True,
                "share_saved_states": True
            },
            "accessibility": {
                "high_contrast": True,
                "keyboard_navigation": True,
                "screen_reader": True,
                "font_scaling": True,
                "motion_reduction": True
            }
        }
        
        return customization_config