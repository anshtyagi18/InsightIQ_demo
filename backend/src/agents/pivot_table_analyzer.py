"""
Enhanced Pivot Table Analysis Agent

This agent generates intelligent pivot table recommendations for cleaner dashboard 
visualizations and better data insights using Google ADK.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from google.adk.agents import Agent
from google.adk.tools import FunctionTool
import logging
from itertools import combinations
from datetime import datetime, timedelta
from scipy import stats
import re

logger = logging.getLogger(__name__)


def analyze_data_structure(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze the data structure to understand column types and relationships.
    
    Args:
        data: Dictionary containing the dataset information with 'rows' and 'columns'
        
    Returns:
        Dictionary with data structure analysis including column types and recommendations
    """
    try:
        rows = data.get('rows', [])
        columns = data.get('columns', [])
        
        if not rows or not columns:
            return {
                'status': 'error',
                'message': 'Invalid data format - missing rows or columns'
            }
        
        # Convert to pandas DataFrame for analysis
        df = pd.DataFrame(rows)
        
        column_analysis = {}
        categorical_columns = []
        numerical_columns = []
        date_columns = []
        
        for column in columns:
            if column not in df.columns:
                continue
                
            series = df[column].dropna()
            if series.empty:
                column_analysis[column] = {
                    'type': 'empty',
                    'suitable_for': [],
                    'unique_count': 0,
                    'null_count': df[column].isnull().sum()
                }
                continue
            
            # Determine column type and characteristics
            col_info = _analyze_column_characteristics(series)
            column_analysis[column] = col_info
            
            # Categorize columns for pivot table recommendations
            if col_info['type'] == 'categorical':
                categorical_columns.append(column)
            elif col_info['type'] == 'numerical':
                numerical_columns.append(column)
            elif col_info['type'] == 'date':
                date_columns.append(column)
        
        return {
            'status': 'success',
            'total_rows': len(rows),
            'total_columns': len(columns),
            'column_analysis': column_analysis,
            'categorical_columns': categorical_columns,
            'numerical_columns': numerical_columns,
            'date_columns': date_columns,
            'pivot_readiness_score': _calculate_pivot_readiness(column_analysis),
            'recommendations': _generate_structure_recommendations(
                categorical_columns, numerical_columns, date_columns
            )
        }
        
    except Exception as e:
        logger.error(f"Error in analyze_data_structure: {str(e)}")
        return {
            'status': 'error',
            'message': f"Failed to analyze data structure: {str(e)}"
        }


def generate_pivot_recommendations(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate intelligent pivot table recommendations based on data characteristics.
    
    Args:
        data: Dictionary containing the dataset information
        
    Returns:
        Dictionary with 3-5 optimal pivot table recommendations
    """
    try:
        # First analyze the data structure
        structure_analysis = analyze_data_structure(data)
        
        if structure_analysis['status'] == 'error':
            return structure_analysis
        
        categorical_columns = structure_analysis['categorical_columns']
        numerical_columns = structure_analysis['numerical_columns']
        date_columns = structure_analysis['date_columns']
        column_analysis = structure_analysis['column_analysis']
        
        if not numerical_columns:
            return {
                'status': 'warning',
                'message': 'No numerical columns found for aggregation',
                'recommendations': []
            }
        
        if not categorical_columns and not date_columns:
            return {
                'status': 'warning',
                'message': 'No categorical or date columns found for grouping',
                'recommendations': []
            }
        
        # Generate pivot table recommendations
        recommendations = []
        
        # Strategy 1: Single categorical dimension with primary numerical column
        if categorical_columns and numerical_columns:
            primary_cat = _select_best_categorical_column(categorical_columns, column_analysis)
            primary_num = _select_best_numerical_column(numerical_columns, column_analysis)
            
            recommendations.append({
                'id': 1,
                'title': 'Basic Summary Table',
                'description': f'Summarize {primary_num} by {primary_cat}',
                'index': [primary_cat],
                'columns': [],
                'values': [primary_num],
                'aggfunc': 'sum',
                'confidence': 0.9,
                'business_relevance': 'High - Simple aggregation for quick insights'
            })
        
        # Strategy 2: Cross-tabulation with two categorical dimensions
        if len(categorical_columns) >= 2:
            cat1, cat2 = _select_best_categorical_pair(categorical_columns, column_analysis)
            primary_num = _select_best_numerical_column(numerical_columns, column_analysis)
            
            recommendations.append({
                'id': 2,
                'title': 'Cross-tabulation Analysis',
                'description': f'Compare {primary_num} across {cat1} and {cat2}',
                'index': [cat1],
                'columns': [cat2],
                'values': [primary_num],
                'aggfunc': 'mean',
                'confidence': 0.85,
                'business_relevance': 'High - Reveals relationships between dimensions'
            })
        
        # Strategy 3: Time-based analysis if date columns exist
        if date_columns and numerical_columns:
            primary_date = date_columns[0]
            primary_num = _select_best_numerical_column(numerical_columns, column_analysis)
            
            recommendations.append({
                'id': 3,
                'title': 'Time Series Summary',
                'description': f'Track {primary_num} over time ({primary_date})',
                'index': [primary_date],
                'columns': [],
                'values': [primary_num],
                'aggfunc': 'sum',
                'confidence': 0.8,
                'business_relevance': 'High - Temporal trends and patterns'
            })
        
        # Strategy 4: Multi-dimensional analysis
        if len(categorical_columns) >= 1 and len(numerical_columns) >= 2:
            primary_cat = _select_best_categorical_column(categorical_columns, column_analysis)
            top_nums = numerical_columns[:2]
            
            recommendations.append({
                'id': 4,
                'title': 'Multi-metric Dashboard',
                'description': f'Multiple metrics ({", ".join(top_nums)}) by {primary_cat}',
                'index': [primary_cat],
                'columns': [],
                'values': top_nums,
                'aggfunc': 'mean',
                'confidence': 0.75,
                'business_relevance': 'Medium - Comprehensive view of key metrics'
            })
        
        # Strategy 5: Advanced hierarchical analysis
        if len(categorical_columns) >= 2 and numerical_columns:
            top_cats = categorical_columns[:2]
            primary_num = _select_best_numerical_column(numerical_columns, column_analysis)
            
            recommendations.append({
                'id': 5,
                'title': 'Hierarchical Breakdown',
                'description': f'Hierarchical view of {primary_num} by {" and ".join(top_cats)}',
                'index': top_cats,
                'columns': [],
                'values': [primary_num],
                'aggfunc': 'sum',
                'confidence': 0.7,
                'business_relevance': 'Medium - Detailed hierarchical insights'
            })
        
        # Sort by confidence and take top 5
        recommendations.sort(key=lambda x: x['confidence'], reverse=True)
        recommendations = recommendations[:5]
        
        return {
            'status': 'success',
            'total_recommendations': len(recommendations),
            'recommendations': recommendations,
            'data_characteristics': {
                'categorical_count': len(categorical_columns),
                'numerical_count': len(numerical_columns),
                'date_count': len(date_columns)
            }
        }
        
    except Exception as e:
        logger.error(f"Error in generate_pivot_recommendations: {str(e)}")
        return {
            'status': 'error',
            'message': f"Failed to generate pivot recommendations: {str(e)}"
        }


# Helper functions

def _analyze_column_characteristics(series: pd.Series) -> Dict[str, Any]:
    """Analyze characteristics of a pandas Series to determine its type and suitability."""
    unique_count = series.nunique()
    total_count = len(series)
    unique_ratio = unique_count / total_count if total_count > 0 else 0
    
    # Determine data type
    if pd.api.types.is_datetime64_any_dtype(series):
        col_type = 'date'
        suitable_for = ['index', 'columns']
    elif pd.api.types.is_numeric_dtype(series):
        if unique_ratio > 0.8:  # High cardinality numeric - likely continuous
            col_type = 'numerical'
            suitable_for = ['values']
        else:  # Low cardinality numeric - could be categorical
            col_type = 'categorical'
            suitable_for = ['index', 'columns']
    else:
        # String/object type
        if unique_ratio > 0.5:  # High cardinality - likely identifiers
            col_type = 'identifier'
            suitable_for = []
        else:  # Low cardinality - good for grouping
            col_type = 'categorical'
            suitable_for = ['index', 'columns']
    
    return {
        'type': col_type,
        'unique_count': unique_count,
        'unique_ratio': unique_ratio,
        'suitable_for': suitable_for,
        'null_count': series.isnull().sum(),
        'sample_values': series.dropna().head(3).tolist()
    }


def _calculate_pivot_readiness(column_analysis: Dict[str, Any]) -> float:
    """Calculate a score indicating how suitable the data is for pivot table analysis."""
    if not column_analysis:
        return 0.0
    
    categorical_count = sum(1 for info in column_analysis.values() if info['type'] == 'categorical')
    numerical_count = sum(1 for info in column_analysis.values() if info['type'] == 'numerical')
    date_count = sum(1 for info in column_analysis.values() if info['type'] == 'date')
    
    # Basic requirements: at least 1 grouping column and 1 value column
    has_grouping = categorical_count > 0 or date_count > 0
    has_values = numerical_count > 0
    
    if not (has_grouping and has_values):
        return 0.2
    
    # Score based on variety of column types
    score = 0.5  # Base score
    score += min(categorical_count * 0.15, 0.3)  # Bonus for categorical columns
    score += min(numerical_count * 0.1, 0.2)     # Bonus for numerical columns
    score += min(date_count * 0.2, 0.2)          # Bonus for date columns
    
    return min(score, 1.0)


def _generate_structure_recommendations(categorical_cols: List[str], 
                                      numerical_cols: List[str], 
                                      date_cols: List[str]) -> List[str]:
    """Generate recommendations based on data structure analysis."""
    recommendations = []
    
    if not numerical_cols:
        recommendations.append("No numerical columns found - pivot tables require numerical data for aggregation")
    elif len(numerical_cols) == 1:
        recommendations.append(f"Single numerical column '{numerical_cols[0]}' available for aggregation")
    else:
        recommendations.append(f"Multiple numerical columns available: {numerical_cols[:3]}")
    
    if not categorical_cols and not date_cols:
        recommendations.append("No categorical or date columns for grouping - consider data transformation")
    elif len(categorical_cols) >= 2:
        recommendations.append(f"Good categorical variety for cross-tabulation: {categorical_cols[:3]}")
    
    if date_cols:
        recommendations.append(f"Time-based analysis possible with: {date_cols}")
    
    if len(categorical_cols) + len(date_cols) >= 2 and len(numerical_cols) >= 1:
        recommendations.append("Excellent data structure for comprehensive pivot table analysis")
    
    return recommendations


def _select_best_categorical_column(categorical_columns: List[str], 
                                  column_analysis: Dict[str, Any]) -> str:
    """Select the best categorical column for pivot table index."""
    if not categorical_columns:
        return None
    
    # Score columns based on unique count (prefer moderate cardinality)
    scored_columns = []
    for col in categorical_columns:
        info = column_analysis.get(col, {})
        unique_count = info.get('unique_count', 0)
        
        # Prefer columns with 2-20 unique values
        if 2 <= unique_count <= 20:
            score = 1.0
        elif unique_count < 2:
            score = 0.1
        else:
            score = max(0.2, 1.0 - (unique_count - 20) * 0.02)
        
        scored_columns.append((col, score))
    
    # Return column with highest score
    scored_columns.sort(key=lambda x: x[1], reverse=True)
    return scored_columns[0][0]


def _select_best_numerical_column(numerical_columns: List[str], 
                                column_analysis: Dict[str, Any]) -> str:
    """Select the best numerical column for aggregation."""
    if not numerical_columns:
        return None
    
    # For now, return the first numerical column
    # In future versions, could consider variance, distribution, etc.
    return numerical_columns[0]


def _select_best_categorical_pair(categorical_columns: List[str], 
                                column_analysis: Dict[str, Any]) -> Tuple[str, str]:
    """Select the best pair of categorical columns for cross-tabulation."""
    if len(categorical_columns) < 2:
        return None, None
    
    # Score all pairs based on combined cardinality
    best_pair = None
    best_score = 0
    
    for col1, col2 in combinations(categorical_columns[:4], 2):  # Limit to first 4 to avoid too many combinations
        info1 = column_analysis.get(col1, {})
        info2 = column_analysis.get(col2, {})
        
        unique1 = info1.get('unique_count', 0)
        unique2 = info2.get('unique_count', 0)
        
        # Prefer pairs with moderate total cardinality
        total_combinations = unique1 * unique2
        if 4 <= total_combinations <= 100:
            score = 1.0
        elif total_combinations < 4:
            score = 0.3
        else:
            score = max(0.1, 1.0 - (total_combinations - 100) * 0.01)
        
        if score > best_score:
            best_score = score
            best_pair = (col1, col2)
    
    return best_pair if best_pair else (categorical_columns[0], categorical_columns[1])


def apply_business_intelligence_heuristics(data: Dict[str, Any], recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Apply advanced business intelligence heuristics to enhance pivot table insights.
    
    Args:
        data: Dictionary containing the dataset information
        recommendations: List of initial pivot table recommendations
        
    Returns:
        Enhanced recommendations with BI insights and scoring
    """
    try:
        rows = data.get('rows', [])
        if not rows:
            return {'status': 'error', 'message': 'No data rows provided'}
        
        df = pd.DataFrame(rows)
        enhanced_recommendations = []
        
        for rec in recommendations:
            enhanced_rec = rec.copy()
            
            # Apply BI heuristics
            bi_insights = _apply_bi_analysis(df, rec)
            enhanced_rec.update(bi_insights)
            
            # Calculate business relevance score
            business_score = _calculate_business_relevance_score(df, rec)
            enhanced_rec['business_score'] = business_score
            
            # Add KPI alignment
            kpi_alignment = _detect_kpi_alignment(rec)
            enhanced_rec['kpi_alignment'] = kpi_alignment
            
            # Add temporal intelligence if applicable
            temporal_insights = _analyze_temporal_patterns(df, rec)
            if temporal_insights:
                enhanced_rec['temporal_insights'] = temporal_insights
            
            enhanced_recommendations.append(enhanced_rec)
        
        # Sort by enhanced business score
        enhanced_recommendations.sort(key=lambda x: x.get('business_score', 0), reverse=True)
        
        return {
            'status': 'success',
            'enhanced_recommendations': enhanced_recommendations,
            'bi_summary': _generate_bi_summary(df, enhanced_recommendations)
        }
        
    except Exception as e:
        logger.error(f"Error in apply_business_intelligence_heuristics: {str(e)}")
        return {
            'status': 'error',
            'message': f"Failed to apply BI heuristics: {str(e)}"
        }


def _apply_bi_analysis(df: pd.DataFrame, recommendation: Dict[str, Any]) -> Dict[str, Any]:
    """Apply comprehensive business intelligence analysis to a pivot recommendation."""
    bi_insights = {}
    
    # Outlier detection
    values_cols = recommendation.get('values', [])
    if values_cols:
        outliers = _detect_outliers(df, values_cols[0])
        bi_insights['outlier_analysis'] = outliers
    
    # Data quality assessment
    quality_score = _assess_data_quality(df, recommendation)
    bi_insights['data_quality_score'] = quality_score
    
    # Cross-dimensional correlation
    correlations = _analyze_cross_dimensional_correlation(df, recommendation)
    bi_insights['correlations'] = correlations
    
    # Business pattern recognition
    patterns = _recognize_business_patterns(df, recommendation)
    bi_insights['business_patterns'] = patterns
    
    return bi_insights


def _calculate_business_relevance_score(df: pd.DataFrame, recommendation: Dict[str, Any]) -> float:
    """Calculate enhanced business relevance score using BI heuristics."""
    score = recommendation.get('confidence', 0.5)
    
    # Boost score for KPI-aligned columns
    kpi_boost = _get_kpi_boost(recommendation)
    score += kpi_boost
    
    # Boost for temporal analysis
    if any('date' in str(col).lower() or 'time' in str(col).lower() 
           for col in recommendation.get('index', []) + recommendation.get('columns', [])):
        score += 0.15
    
    # Boost for cross-dimensional analysis
    if len(recommendation.get('index', [])) + len(recommendation.get('columns', [])) >= 2:
        score += 0.1
    
    # Data quality factor
    quality_factor = _get_data_quality_factor(df, recommendation)
    score *= quality_factor
    
    return min(score, 1.0)


def _detect_kpi_alignment(recommendation: Dict[str, Any]) -> Dict[str, Any]:
    """Detect alignment with common business KPIs."""
    kpi_patterns = {
        'revenue': ['revenue', 'sales', 'income', 'earnings', 'amount', 'value', 'price'],
        'performance': ['performance', 'efficiency', 'productivity', 'throughput', 'utilization'],
        'quality': ['quality', 'satisfaction', 'rating', 'score', 'error', 'defect'],
        'growth': ['growth', 'increase', 'trend', 'change', 'delta'],
        'time': ['time', 'duration', 'period', 'date', 'timestamp']
    }
    
    alignment = {'detected_kpis': [], 'confidence': 0.0}
    
    all_columns = (recommendation.get('index', []) + 
                  recommendation.get('columns', []) + 
                  recommendation.get('values', []))
    
    for kpi, patterns in kpi_patterns.items():
        for col in all_columns:
            if any(pattern in str(col).lower() for pattern in patterns):
                alignment['detected_kpis'].append(kpi)
                alignment['confidence'] += 0.2
                break
    
    alignment['confidence'] = min(alignment['confidence'], 1.0)
    return alignment


def _analyze_temporal_patterns(df: pd.DataFrame, recommendation: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Analyze temporal patterns in the data for time-based insights."""
    date_columns = []
    all_columns = recommendation.get('index', []) + recommendation.get('columns', [])
    
    for col in all_columns:
        if col in df.columns:
            try:
                pd.to_datetime(df[col].dropna().head())
                date_columns.append(col)
            except:
                # Check if column name suggests temporal data
                if any(word in str(col).lower() for word in ['date', 'time', 'year', 'month', 'day']):
                    date_columns.append(col)
    
    if not date_columns:
        return None
    
    insights = {
        'has_temporal_dimension': True,
        'temporal_columns': date_columns,
        'recommended_time_aggregations': []
    }
    
    # Suggest appropriate time aggregations
    for col in date_columns:
        if col in df.columns:
            try:
                date_series = pd.to_datetime(df[col].dropna())
                date_range = date_series.max() - date_series.min()
                
                if date_range.days > 365:
                    insights['recommended_time_aggregations'].append('yearly')
                elif date_range.days > 90:
                    insights['recommended_time_aggregations'].append('monthly')
                elif date_range.days > 7:
                    insights['recommended_time_aggregations'].append('weekly')
                else:
                    insights['recommended_time_aggregations'].append('daily')
            except:
                insights['recommended_time_aggregations'].append('categorical')
    
    return insights


def _detect_outliers(df: pd.DataFrame, column: str) -> Dict[str, Any]:
    """Detect outliers in numerical data using statistical methods."""
    if column not in df.columns:
        return {'status': 'error', 'message': f'Column {column} not found'}
    
    series = df[column].dropna()
    if not pd.api.types.is_numeric_dtype(series):
        return {'status': 'warning', 'message': 'Non-numerical data'}
    
    # Use IQR method for outlier detection
    Q1 = series.quantile(0.25)
    Q3 = series.quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    
    outliers = series[(series < lower_bound) | (series > upper_bound)]
    
    return {
        'status': 'success',
        'outlier_count': len(outliers),
        'outlier_percentage': len(outliers) / len(series) * 100,
        'bounds': {'lower': lower_bound, 'upper': upper_bound},
        'recommendation': 'Consider filtering outliers for cleaner visualizations' if len(outliers) > 0 else 'No significant outliers detected'
    }


def _assess_data_quality(df: pd.DataFrame, recommendation: Dict[str, Any]) -> float:
    """Assess data quality for pivot table reliability."""
    all_columns = (recommendation.get('index', []) + 
                  recommendation.get('columns', []) + 
                  recommendation.get('values', []))
    
    quality_score = 1.0
    
    for col in all_columns:
        if col in df.columns:
            series = df[col]
            null_ratio = series.isnull().sum() / len(series)
            
            # Penalize high null ratios
            if null_ratio > 0.5:
                quality_score *= 0.5
            elif null_ratio > 0.2:
                quality_score *= 0.8
            elif null_ratio > 0.1:
                quality_score *= 0.9
    
    return quality_score


def _analyze_cross_dimensional_correlation(df: pd.DataFrame, recommendation: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze correlations between dimensions in the pivot table."""
    index_cols = recommendation.get('index', [])
    column_cols = recommendation.get('columns', [])
    value_cols = recommendation.get('values', [])
    
    correlations = {'numerical_correlations': {}, 'categorical_associations': {}}
    
    # Numerical correlations
    numerical_cols = [col for col in index_cols + column_cols + value_cols 
                     if col in df.columns and pd.api.types.is_numeric_dtype(df[col])]
    
    if len(numerical_cols) >= 2:
        for i, col1 in enumerate(numerical_cols):
            for col2 in numerical_cols[i+1:]:
                try:
                    corr = df[col1].corr(df[col2])
                    if not pd.isna(corr):
                        correlations['numerical_correlations'][f'{col1}_vs_{col2}'] = round(corr, 3)
                except:
                    pass
    
    return correlations


def _recognize_business_patterns(df: pd.DataFrame, recommendation: Dict[str, Any]) -> List[str]:
    """Recognize common business intelligence patterns in the data."""
    patterns = []
    
    # Pattern 1: Revenue/Sales analysis
    value_cols = recommendation.get('values', [])
    if any('sales' in str(col).lower() or 'revenue' in str(col).lower() or 'amount' in str(col).lower() 
           for col in value_cols):
        patterns.append('Revenue Analysis Pattern')
    
    # Pattern 2: Time series pattern
    index_cols = recommendation.get('index', [])
    if any('date' in str(col).lower() or 'time' in str(col).lower() or 'year' in str(col).lower()
           for col in index_cols):
        patterns.append('Time Series Analysis Pattern')
    
    # Pattern 3: Geographic analysis
    all_cols = index_cols + recommendation.get('columns', [])
    if any(word in str(col).lower() for col in all_cols 
           for word in ['region', 'country', 'state', 'city', 'location']):
        patterns.append('Geographic Analysis Pattern')
    
    # Pattern 4: Product/Category analysis
    if any(word in str(col).lower() for col in all_cols 
           for word in ['product', 'category', 'type', 'segment']):
        patterns.append('Product/Category Analysis Pattern')
    
    return patterns


def _get_kpi_boost(recommendation: Dict[str, Any]) -> float:
    """Get boost score based on KPI alignment."""
    kpi_alignment = _detect_kpi_alignment(recommendation)
    return min(kpi_alignment['confidence'] * 0.2, 0.3)


def _get_data_quality_factor(df: pd.DataFrame, recommendation: Dict[str, Any]) -> float:
    """Get data quality factor for score adjustment."""
    return _assess_data_quality(df, recommendation)


def _generate_bi_summary(df: pd.DataFrame, recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate a summary of business intelligence insights."""
    summary = {
        'total_recommendations': len(recommendations),
        'avg_business_score': np.mean([r.get('business_score', 0) for r in recommendations]),
        'detected_patterns': set(),
        'kpi_coverage': set()
    }
    
    for rec in recommendations:
        # Collect patterns
        patterns = rec.get('business_patterns', [])
        summary['detected_patterns'].update(patterns)
        
        # Collect KPIs
        kpis = rec.get('kpi_alignment', {}).get('detected_kpis', [])
        summary['kpi_coverage'].update(kpis)
    
    summary['detected_patterns'] = list(summary['detected_patterns'])
    summary['kpi_coverage'] = list(summary['kpi_coverage'])
    
    return summary


def optimize_pivot_performance(data: Dict[str, Any], recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Optimize pivot table recommendations for better performance and memory usage.
    
    Args:
        data: Dictionary containing the dataset information
        recommendations: List of pivot table recommendations to optimize
        
    Returns:
        Dictionary with optimized recommendations and performance metadata
    """
    try:
        rows = data.get('rows', [])
        if not rows:
            return {'status': 'error', 'message': 'No data rows provided'}
        
        df = pd.DataFrame(rows)
        data_size = len(df)
        
        optimized_recommendations = []
        
        for rec in recommendations:
            optimized_rec = rec.copy()
            
            # Apply performance optimizations
            perf_optimizations = _apply_performance_optimizations(df, rec, data_size)
            optimized_rec.update(perf_optimizations)
            
            # Apply memory optimizations
            memory_optimizations = _apply_memory_optimizations(df, rec)
            optimized_rec.update(memory_optimizations)
            
            # Calculate performance score
            perf_score = _calculate_performance_score(df, rec, data_size)
            optimized_rec['performance_score'] = perf_score
            
            optimized_recommendations.append(optimized_rec)
        
        # Sort by performance score
        optimized_recommendations.sort(key=lambda x: x.get('performance_score', 0), reverse=True)
        
        return {
            'status': 'success',
            'optimized_recommendations': optimized_recommendations,
            'performance_summary': _generate_performance_summary(df, optimized_recommendations)
        }
        
    except Exception as e:
        logger.error(f"Error in optimize_pivot_performance: {str(e)}")
        return {
            'status': 'error',
            'message': f"Failed to optimize pivot performance: {str(e)}"
        }


def enhance_pivot_usability(data: Dict[str, Any], recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Enhance pivot table recommendations for better user experience and readability.
    
    Args:
        data: Dictionary containing the dataset information
        recommendations: List of pivot table recommendations to enhance
        
    Returns:
        Dictionary with enhanced recommendations and usability improvements
    """
    try:
        rows = data.get('rows', [])
        if not rows:
            return {'status': 'error', 'message': 'No data rows provided'}
        
        df = pd.DataFrame(rows)
        
        enhanced_recommendations = []
        
        for rec in recommendations:
            enhanced_rec = rec.copy()
            
            # Apply usability enhancements
            usability_features = _apply_usability_enhancements(df, rec)
            enhanced_rec.update(usability_features)
            
            # Add formatting recommendations
            formatting = _generate_formatting_recommendations(df, rec)
            enhanced_rec['formatting'] = formatting
            
            # Calculate usability score
            usability_score = _calculate_usability_score(df, rec)
            enhanced_rec['usability_score'] = usability_score
            
            enhanced_recommendations.append(enhanced_rec)
        
        # Sort by usability score
        enhanced_recommendations.sort(key=lambda x: x.get('usability_score', 0), reverse=True)
        
        return {
            'status': 'success',
            'enhanced_recommendations': enhanced_recommendations,
            'usability_summary': _generate_usability_summary(enhanced_recommendations)
        }
        
    except Exception as e:
        logger.error(f"Error in enhance_pivot_usability: {str(e)}")
        return {
            'status': 'error',
            'message': f"Failed to enhance pivot usability: {str(e)}"
        }


def _apply_performance_optimizations(df: pd.DataFrame, recommendation: Dict[str, Any], data_size: int) -> Dict[str, Any]:
    """Apply performance optimizations based on data size and complexity."""
    optimizations = {'performance_optimizations': []}
    
    # Large dataset sampling
    if data_size > 100000:
        sample_size = min(50000, data_size // 2)
        optimizations['performance_optimizations'].append(f'Large dataset detected: Recommend sampling to {sample_size} rows')
        optimizations['recommended_sample_size'] = sample_size
    
    # Aggregation function optimization
    values = recommendation.get('values', [])
    aggfunc = recommendation.get('aggfunc', 'sum')
    
    if aggfunc == 'mean' and data_size > 10000:
        optimizations['performance_optimizations'].append('Consider using "sum" aggregation for better performance on large datasets')
        optimizations['optimized_aggfunc'] = 'sum'
    
    # Index optimization
    index_cols = recommendation.get('index', [])
    if len(index_cols) > 2 and data_size > 50000:
        optimizations['performance_optimizations'].append('Consider reducing index columns for better performance')
        optimizations['optimized_index'] = index_cols[:2]
    
    # Memory usage estimation
    estimated_memory = _estimate_pivot_memory_usage(df, recommendation)
    optimizations['estimated_memory_mb'] = estimated_memory
    
    if estimated_memory > 500:  # More than 500MB
        optimizations['performance_optimizations'].append('High memory usage expected: Consider data reduction strategies')
    
    return optimizations


def _apply_memory_optimizations(df: pd.DataFrame, recommendation: Dict[str, Any]) -> Dict[str, Any]:
    """Apply memory optimization strategies."""
    optimizations = {'memory_optimizations': []}
    
    # Categorical optimization
    index_cols = recommendation.get('index', []) + recommendation.get('columns', [])
    categorical_candidates = []
    
    for col in index_cols:
        if col in df.columns and df[col].dtype == 'object':
            unique_ratio = df[col].nunique() / len(df)
            if unique_ratio < 0.5:  # Less than 50% unique values
                categorical_candidates.append(col)
    
    if categorical_candidates:
        optimizations['memory_optimizations'].append(f'Convert to categorical: {categorical_candidates}')
        optimizations['categorical_columns'] = categorical_candidates
    
    # Column selection optimization
    all_cols = set(recommendation.get('index', []) + recommendation.get('columns', []) + recommendation.get('values', []))
    unused_cols = set(df.columns) - all_cols
    
    if len(unused_cols) > len(all_cols):
        optimizations['memory_optimizations'].append(f'Remove {len(unused_cols)} unused columns before pivot')
        optimizations['columns_to_remove'] = list(unused_cols)
    
    return optimizations


def _apply_usability_enhancements(df: pd.DataFrame, recommendation: Dict[str, Any]) -> Dict[str, Any]:
    """Apply usability enhancements for better user experience."""
    enhancements = {'usability_enhancements': []}
    
    # Smart column ordering
    columns = recommendation.get('columns', [])
    if len(columns) > 1:
        ordered_columns = _optimize_column_order(df, columns)
        enhancements['optimized_column_order'] = ordered_columns
        enhancements['usability_enhancements'].append('Optimized column ordering for readability')
    
    # Value column recommendations
    values = recommendation.get('values', [])
    for val_col in values:
        if val_col in df.columns and pd.api.types.is_numeric_dtype(df[val_col]):
            # Check for decimal values
            if df[val_col].dtype == 'float64':
                decimal_places = _suggest_decimal_places(df[val_col])
                enhancements['usability_enhancements'].append(f'Round {val_col} to {decimal_places} decimal places')
    
    # Empty cell handling
    null_percentage = df.isnull().sum().sum() / (len(df) * len(df.columns)) * 100
    if null_percentage > 5:
        enhancements['usability_enhancements'].append('Consider fill strategy for empty cells in pivot table')
        enhancements['recommended_fill_value'] = 0 if recommendation.get('aggfunc') in ['sum', 'count'] else 'N/A'
    
    # Hierarchical display recommendations
    index_cols = recommendation.get('index', [])
    if len(index_cols) > 1:
        enhancements['usability_enhancements'].append('Use hierarchical display with collapsible sections')
        enhancements['hierarchy_levels'] = len(index_cols)
    
    return enhancements


def _generate_formatting_recommendations(df: pd.DataFrame, recommendation: Dict[str, Any]) -> Dict[str, Any]:
    """Generate formatting recommendations for better presentation."""
    formatting = {}
    
    values = recommendation.get('values', [])
    for val_col in values:
        if val_col in df.columns:
            col_data = df[val_col].dropna()
            if pd.api.types.is_numeric_dtype(col_data):
                # Determine appropriate formatting
                if 'revenue' in val_col.lower() or 'sales' in val_col.lower() or 'amount' in val_col.lower():
                    formatting[val_col] = {'type': 'currency', 'symbol': '$', 'decimals': 2}
                elif 'percentage' in val_col.lower() or 'rate' in val_col.lower():
                    formatting[val_col] = {'type': 'percentage', 'decimals': 1}
                elif col_data.dtype == 'int64':
                    formatting[val_col] = {'type': 'integer', 'thousands_separator': True}
                else:
                    formatting[val_col] = {'type': 'decimal', 'decimals': 2}
    
    return formatting


def _calculate_performance_score(df: pd.DataFrame, recommendation: Dict[str, Any], data_size: int) -> float:
    """Calculate performance score for a pivot table recommendation."""
    score = 1.0
    
    # Size penalty
    if data_size > 100000:
        score *= 0.7
    elif data_size > 50000:
        score *= 0.85
    
    # Complexity penalty
    total_dimensions = len(recommendation.get('index', [])) + len(recommendation.get('columns', []))
    if total_dimensions > 3:
        score *= 0.8
    elif total_dimensions > 2:
        score *= 0.9
    
    # Aggregation function efficiency
    aggfunc = recommendation.get('aggfunc', 'sum')
    if aggfunc in ['sum', 'count']:
        score *= 1.0  # No penalty for efficient functions
    elif aggfunc in ['mean', 'std']:
        score *= 0.9  # Slight penalty for more complex functions
    
    return min(score, 1.0)


def _calculate_usability_score(df: pd.DataFrame, recommendation: Dict[str, Any]) -> float:
    """Calculate usability score for a pivot table recommendation."""
    score = 0.5  # Base score
    
    # Readability factors
    index_cols = recommendation.get('index', [])
    column_cols = recommendation.get('columns', [])
    
    # Prefer simpler structures
    if len(index_cols) <= 2 and len(column_cols) <= 1:
        score += 0.3
    elif len(index_cols) <= 1 and len(column_cols) <= 2:
        score += 0.2
    
    # Business relevance boost
    business_score = recommendation.get('business_score', 0)
    score += business_score * 0.3
    
    # Data quality factor
    quality_score = recommendation.get('data_quality_score', 1.0)
    score *= quality_score
    
    return min(score, 1.0)


def _estimate_pivot_memory_usage(df: pd.DataFrame, recommendation: Dict[str, Any]) -> float:
    """Estimate memory usage of pivot table in MB."""
    # Basic estimation based on data size and pivot complexity
    base_memory = df.memory_usage(deep=True).sum() / (1024 * 1024)  # Convert to MB
    
    index_cols = recommendation.get('index', [])
    column_cols = recommendation.get('columns', [])
    
    # Estimate pivot table size
    index_cardinality = 1
    for col in index_cols:
        if col in df.columns:
            index_cardinality *= df[col].nunique()
    
    column_cardinality = 1
    for col in column_cols:
        if col in df.columns:
            column_cardinality *= df[col].nunique()
    
    # Rough estimation: base memory * cardinality factor
    estimated_memory = base_memory * (index_cardinality * column_cardinality) / len(df)
    
    return max(estimated_memory, base_memory * 0.1)  # Minimum 10% of original size


def _optimize_column_order(df: pd.DataFrame, columns: List[str]) -> List[str]:
    """Optimize column order for better readability."""
    column_stats = []
    
    for col in columns:
        if col in df.columns:
            unique_count = df[col].nunique()
            column_stats.append((col, unique_count))
    
    # Sort by cardinality (fewer unique values first for better readability)
    column_stats.sort(key=lambda x: x[1])
    
    return [col for col, _ in column_stats]


def _suggest_decimal_places(series: pd.Series) -> int:
    """Suggest appropriate number of decimal places for a numeric series."""
    # Check the range of values
    max_val = series.max()
    min_val = series.min()
    
    if max_val > 1000000:
        return 0  # Large numbers, no decimals needed
    elif max_val > 1000:
        return 1  # Thousands, 1 decimal
    elif max_val > 10:
        return 2  # Tens/hundreds, 2 decimals
    else:
        return 3  # Small numbers, 3 decimals


def _generate_performance_summary(df: pd.DataFrame, recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate performance optimization summary."""
    summary = {
        'dataset_size': len(df),
        'avg_performance_score': np.mean([r.get('performance_score', 0) for r in recommendations]),
        'memory_efficient_recommendations': len([r for r in recommendations if r.get('estimated_memory_mb', 0) < 100]),
        'optimization_techniques_applied': set()
    }
    
    for rec in recommendations:
        optimizations = rec.get('performance_optimizations', [])
        for opt in optimizations:
            summary['optimization_techniques_applied'].add(opt.split(':')[0])  # Get technique name
    
    summary['optimization_techniques_applied'] = list(summary['optimization_techniques_applied'])
    
    return summary


def _generate_usability_summary(recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate usability enhancement summary."""
    summary = {
        'total_recommendations': len(recommendations),
        'avg_usability_score': np.mean([r.get('usability_score', 0) for r in recommendations]),
        'enhancements_applied': set(),
        'formatting_coverage': 0
    }
    
    formatting_count = 0
    for rec in recommendations:
        enhancements = rec.get('usability_enhancements', [])
        summary['enhancements_applied'].update(enhancements)
        
        if rec.get('formatting'):
            formatting_count += 1
    
    summary['enhancements_applied'] = list(summary['enhancements_applied'])
    summary['formatting_coverage'] = formatting_count / len(recommendations) if recommendations else 0
    
    return summary


def generate_chart_recommendations(data: Dict[str, Any], pivot_recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate chart recommendations based on pivot table configurations.
    
    Args:
        data: Dictionary containing the dataset information
        pivot_recommendations: List of pivot table recommendations to convert to charts
        
    Returns:
        Dictionary with chart recommendations and visualization configurations
    """
    try:
        rows = data.get('rows', [])
        if not rows:
            return {'status': 'error', 'message': 'No data rows provided'}
        
        df = pd.DataFrame(rows)
        chart_recommendations = []
        
        for i, pivot_rec in enumerate(pivot_recommendations):
            chart_configs = _generate_chart_configs_for_pivot(df, pivot_rec, i+1)
            chart_recommendations.extend(chart_configs)
        
        # Sort by visualization score
        chart_recommendations.sort(key=lambda x: x.get('visualization_score', 0), reverse=True)
        
        return {
            'status': 'success',
            'chart_recommendations': chart_recommendations,
            'visualization_summary': _generate_visualization_summary(chart_recommendations)
        }
        
    except Exception as e:
        logger.error(f"Error in generate_chart_recommendations: {str(e)}")
        return {
            'status': 'error',
            'message': f"Failed to generate chart recommendations: {str(e)}"
        }


def _generate_chart_configs_for_pivot(df: pd.DataFrame, pivot_rec: Dict[str, Any], pivot_id: int) -> List[Dict[str, Any]]:
    """Generate multiple chart configuration options for a single pivot table."""
    configs = []
    
    index_cols = pivot_rec.get('index', [])
    column_cols = pivot_rec.get('columns', [])
    value_cols = pivot_rec.get('values', [])
    
    # Chart 1: Primary chart type based on pivot structure
    primary_chart = _determine_primary_chart_type(df, pivot_rec)
    if primary_chart:
        config = _create_chart_config(df, pivot_rec, primary_chart, pivot_id, 1)
        configs.append(config)
    
    # Chart 2: Alternative chart type if applicable
    alternative_chart = _determine_alternative_chart_type(df, pivot_rec, primary_chart)
    if alternative_chart:
        config = _create_chart_config(df, pivot_rec, alternative_chart, pivot_id, 2)
        configs.append(config)
    
    # Chart 3: Time-series specific chart if temporal data exists
    if _has_temporal_dimension(df, pivot_rec):
        temporal_chart = _create_temporal_chart_config(df, pivot_rec, pivot_id, 3)
        configs.append(temporal_chart)
    
    return configs


def _determine_primary_chart_type(df: pd.DataFrame, pivot_rec: Dict[str, Any]) -> Optional[str]:
    """Determine the most appropriate primary chart type for a pivot configuration."""
    index_cols = pivot_rec.get('index', [])
    column_cols = pivot_rec.get('columns', [])
    value_cols = pivot_rec.get('values', [])
    
    # Single categorical dimension
    if len(index_cols) == 1 and not column_cols:
        cardinality = df[index_cols[0]].nunique() if index_cols[0] in df.columns else 0
        if cardinality <= 6:
            return 'pie'  # Good for small categories
        else:
            return 'bar'  # Better for many categories
    
    # Two categorical dimensions
    elif len(index_cols) == 1 and len(column_cols) == 1:
        return 'heatmap'
    
    # Multiple categorical dimensions (hierarchical)
    elif len(index_cols) > 1:
        return 'stacked_bar'
    
    # Time-series detection
    elif _has_temporal_dimension(df, pivot_rec):
        return 'line'
    
    # Multiple values
    elif len(value_cols) > 1:
        return 'grouped_bar'
    
    # Default fallback
    return 'bar'


def _determine_alternative_chart_type(df: pd.DataFrame, pivot_rec: Dict[str, Any], primary_type: str) -> Optional[str]:
    """Determine an alternative chart type that could also work well."""
    index_cols = pivot_rec.get('index', [])
    column_cols = pivot_rec.get('columns', [])
    value_cols = pivot_rec.get('values', [])
    
    # Don't suggest alternative if primary is already optimal
    if primary_type in ['heatmap', 'line']:
        return None
    
    # Alternative for bar charts
    if primary_type == 'bar':
        if len(value_cols) > 1:
            return 'grouped_bar'
        elif len(index_cols) == 1 and df[index_cols[0]].nunique() <= 10:
            return 'horizontal_bar'
    
    # Alternative for pie charts
    elif primary_type == 'pie':
        return 'doughnut'
    
    # Alternative for stacked bar
    elif primary_type == 'stacked_bar':
        return 'stacked_area'
    
    return None


def _has_temporal_dimension(df: pd.DataFrame, pivot_rec: Dict[str, Any]) -> bool:
    """Check if the pivot table has temporal dimensions."""
    all_cols = pivot_rec.get('index', []) + pivot_rec.get('columns', [])
    
    for col in all_cols:
        if col in df.columns:
            # Check column name patterns
            if any(word in str(col).lower() for word in ['date', 'time', 'year', 'month', 'day']):
                return True
            
            # Try to parse as datetime
            try:
                pd.to_datetime(df[col].dropna().head(5))
                return True
            except:
                continue
    
    return False


def _create_chart_config(df: pd.DataFrame, pivot_rec: Dict[str, Any], chart_type: str, pivot_id: int, chart_id: int) -> Dict[str, Any]:
    """Create a complete chart configuration for a given chart type."""
    config = {
        'id': f'chart_{pivot_id}_{chart_id}',
        'pivot_source_id': pivot_id,
        'chart_type': chart_type,
        'title': _generate_chart_title(pivot_rec, chart_type),
        'description': _generate_chart_description(pivot_rec, chart_type),
        'visualization_score': _calculate_visualization_score(df, pivot_rec, chart_type),
        'config': _generate_chart_library_config(df, pivot_rec, chart_type),
        'accessibility': _generate_accessibility_config(pivot_rec, chart_type),
        'responsive': _generate_responsive_config(chart_type)
    }
    
    return config


def _create_temporal_chart_config(df: pd.DataFrame, pivot_rec: Dict[str, Any], pivot_id: int, chart_id: int) -> Dict[str, Any]:
    """Create a time-series specific chart configuration."""
    return {
        'id': f'chart_{pivot_id}_{chart_id}',
        'pivot_source_id': pivot_id,
        'chart_type': 'line',
        'title': f"Time Series: {pivot_rec.get('title', 'Trend Analysis')}",
        'description': 'Time-based trend visualization showing changes over time',
        'visualization_score': 0.9,  # High score for temporal data
        'config': _generate_chart_library_config(df, pivot_rec, 'line'),
        'temporal_features': {
            'time_aggregation': 'auto',
            'trend_analysis': True,
            'seasonal_detection': True
        },
        'accessibility': _generate_accessibility_config(pivot_rec, 'line'),
        'responsive': _generate_responsive_config('line')
    }


def _generate_chart_title(pivot_rec: Dict[str, Any], chart_type: str) -> str:
    """Generate an appropriate title for the chart."""
    base_title = pivot_rec.get('title', 'Data Analysis')
    chart_labels = {
        'bar': 'Bar Chart',
        'line': 'Line Chart',
        'pie': 'Pie Chart',
        'heatmap': 'Heatmap',
        'stacked_bar': 'Stacked Bar Chart',
        'grouped_bar': 'Grouped Bar Chart',
        'horizontal_bar': 'Horizontal Bar Chart',
        'doughnut': 'Doughnut Chart',
        'stacked_area': 'Stacked Area Chart'
    }
    
    chart_label = chart_labels.get(chart_type, 'Chart')
    return f"{base_title} - {chart_label}"


def _generate_chart_description(pivot_rec: Dict[str, Any], chart_type: str) -> str:
    """Generate a description explaining the chart's purpose."""
    descriptions = {
        'bar': 'Compare values across categories using vertical bars',
        'line': 'Show trends and changes over time with connected data points',
        'pie': 'Display proportional relationships as slices of a circle',
        'heatmap': 'Visualize data intensity using color gradients across two dimensions',
        'stacked_bar': 'Show total values and component breakdown in stacked segments',
        'grouped_bar': 'Compare multiple metrics side-by-side across categories',
        'horizontal_bar': 'Compare values across categories using horizontal bars',
        'doughnut': 'Display proportional relationships with a modern ring design',
        'stacked_area': 'Show cumulative totals and component changes over time'
    }
    
    return descriptions.get(chart_type, 'Visualize data relationships and patterns')


def _calculate_visualization_score(df: pd.DataFrame, pivot_rec: Dict[str, Any], chart_type: str) -> float:
    """Calculate how well-suited a chart type is for the given pivot configuration."""
    score = 0.5  # Base score
    
    index_cols = pivot_rec.get('index', [])
    column_cols = pivot_rec.get('columns', [])
    value_cols = pivot_rec.get('values', [])
    
    # Chart type suitability scoring
    if chart_type == 'bar':
        if len(index_cols) == 1 and not column_cols:
            score += 0.4
        if len(value_cols) == 1:
            score += 0.1
    
    elif chart_type == 'line':
        if _has_temporal_dimension(df, pivot_rec):
            score += 0.5
        if len(value_cols) <= 3:  # Not too many lines
            score += 0.1
    
    elif chart_type == 'pie':
        if len(index_cols) == 1 and not column_cols:
            cardinality = df[index_cols[0]].nunique() if index_cols[0] in df.columns else 10
            if cardinality <= 6:
                score += 0.4
            else:
                score -= 0.2  # Penalty for too many slices
    
    elif chart_type == 'heatmap':
        if len(index_cols) == 1 and len(column_cols) == 1:
            score += 0.5
    
    elif chart_type in ['stacked_bar', 'grouped_bar']:
        if len(value_cols) > 1 or len(index_cols) > 1:
            score += 0.3
    
    # Business relevance boost
    business_score = pivot_rec.get('business_score', 0)
    score += business_score * 0.2
    
    return min(score, 1.0)


def _generate_chart_library_config(df: pd.DataFrame, pivot_rec: Dict[str, Any], chart_type: str) -> Dict[str, Any]:
    """Generate configuration for popular chart libraries (Chart.js, Plotly, etc.)."""
    index_cols = pivot_rec.get('index', [])
    value_cols = pivot_rec.get('values', [])
    
    base_config = {
        'data': {
            'labels': index_cols,
            'datasets': []
        },
        'options': {
            'responsive': True,
            'plugins': {
                'title': {
                    'display': True,
                    'text': _generate_chart_title(pivot_rec, chart_type)
                },
                'legend': {
                    'display': len(value_cols) > 1
                }
            }
        }
    }
    
    # Chart-specific configurations
    if chart_type in ['bar', 'horizontal_bar']:
        base_config['type'] = 'bar'
        base_config['options']['indexAxis'] = 'y' if chart_type == 'horizontal_bar' else 'x'
        
    elif chart_type == 'line':
        base_config['type'] = 'line'
        base_config['options']['scales'] = {
            'x': {'type': 'time' if _has_temporal_dimension(df, pivot_rec) else 'category'},
            'y': {'beginAtZero': True}
        }
        
    elif chart_type in ['pie', 'doughnut']:
        base_config['type'] = chart_type
        base_config['options']['cutout'] = '50%' if chart_type == 'doughnut' else '0%'
        
    elif chart_type == 'stacked_bar':
        base_config['type'] = 'bar'
        base_config['options']['scales'] = {
            'x': {'stacked': True},
            'y': {'stacked': True}
        }
    
    # Add dataset configurations
    for i, value_col in enumerate(value_cols):
        dataset_config = {
            'label': value_col,
            'backgroundColor': _generate_color_palette(i, len(value_cols)),
            'borderColor': _generate_color_palette(i, len(value_cols), border=True),
            'borderWidth': 1
        }
        base_config['data']['datasets'].append(dataset_config)
    
    return base_config


def _generate_accessibility_config(pivot_rec: Dict[str, Any], chart_type: str) -> Dict[str, Any]:
    """Generate accessibility configuration for charts."""
    return {
        'alt_text': f"Chart showing {pivot_rec.get('description', 'data visualization')}",
        'aria_label': _generate_chart_title(pivot_rec, chart_type),
        'keyboard_navigation': True,
        'high_contrast_mode': True,
        'screen_reader_table': True,  # Provide data table alternative
        'color_blind_friendly': True
    }


def _generate_responsive_config(chart_type: str) -> Dict[str, Any]:
    """Generate responsive design configuration."""
    return {
        'mobile_optimized': True,
        'breakpoints': {
            'mobile': {'width': 320, 'height': 240},
            'tablet': {'width': 768, 'height': 400},
            'desktop': {'width': 1024, 'height': 500}
        },
        'aspect_ratio': 'auto' if chart_type in ['pie', 'doughnut'] else '16:9',
        'legend_position': 'bottom' if chart_type in ['pie', 'doughnut'] else 'top'
    }


def _generate_color_palette(index: int, total: int, border: bool = False) -> str:
    """Generate color palette for chart elements."""
    # Professional color palette
    colors = [
        '#3B82F6',  # Blue
        '#10B981',  # Green
        '#F59E0B',  # Yellow
        '#EF4444',  # Red
        '#8B5CF6',  # Purple
        '#06B6D4',  # Cyan
        '#F97316',  # Orange
        '#84CC16'   # Lime
    ]
    
    base_color = colors[index % len(colors)]
    
    if border:
        return base_color
    else:
        # Add transparency for fill colors
        if base_color.startswith('#'):
            return base_color + '80'  # 50% opacity
        return base_color


def _generate_visualization_summary(chart_recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate summary of visualization recommendations."""
    summary = {
        'total_charts': len(chart_recommendations),
        'chart_types': {},
        'avg_visualization_score': 0,
        'accessibility_coverage': 0,
        'responsive_charts': 0
    }
    
    if not chart_recommendations:
        return summary
    
    # Count chart types
    for chart in chart_recommendations:
        chart_type = chart.get('chart_type', 'unknown')
        summary['chart_types'][chart_type] = summary['chart_types'].get(chart_type, 0) + 1
    
    # Calculate averages
    total_score = sum(chart.get('visualization_score', 0) for chart in chart_recommendations)
    summary['avg_visualization_score'] = total_score / len(chart_recommendations)
    
    # Count accessibility and responsive features
    accessibility_count = sum(1 for chart in chart_recommendations if chart.get('accessibility'))
    responsive_count = sum(1 for chart in chart_recommendations if chart.get('responsive'))
    
    summary['accessibility_coverage'] = accessibility_count / len(chart_recommendations)
    summary['responsive_charts'] = responsive_count
    
    return summary


class PivotTableAnalysisAgent:
    """
    Enhanced Pivot Table Analysis Agent using Google ADK.
    
    Generates intelligent pivot table recommendations for cleaner dashboard 
    visualizations and better data insights.
    """
    
    def __init__(self, model: str = "gemini-2.0-flash-exp"):
        """
        Initialize the Pivot Table Analysis Agent.
        
        Args:
            model: The LLM model to use for the agent
        """
        self.model = model
        logger.info("Pivot Table Analysis Agent initialized")
    
    def get_agent(self) -> Agent:
        """Return the configured ADK agent with pivot table analysis tools."""
        try:
            # Define the function tools
            tools = [
                FunctionTool(
                    name="analyze_data_structure",
                    description="Analyze data structure to understand column types and relationships for pivot table creation",
                    function=analyze_data_structure
                ),
                FunctionTool(
                    name="generate_pivot_recommendations",
                    description="Generate 3-5 intelligent pivot table recommendations based on data characteristics",
                    function=generate_pivot_recommendations
                ),
                FunctionTool(
                    name="apply_business_intelligence_heuristics",
                    description="Apply advanced business intelligence heuristics to enhance pivot table insights with KPI alignment, temporal analysis, outlier detection, and business pattern recognition",
                    function=apply_business_intelligence_heuristics
                ),
                FunctionTool(
                    name="optimize_pivot_performance",
                    description="Optimize pivot table recommendations for better performance and memory usage with data sampling, categorical optimization, and aggregation function tuning",
                    function=optimize_pivot_performance
                ),
                FunctionTool(
                    name="enhance_pivot_usability",
                    description="Enhance pivot table recommendations for better user experience with smart formatting, column ordering, and readability improvements",
                    function=enhance_pivot_usability
                )
            ]
            
            # Create the agent with tools
            agent = Agent(
                model=self.model,
                tools=tools,
                system="You are an expert data analyst specializing in pivot table analysis, advanced business intelligence, performance optimization, and data visualization. "
                      "Your role is to analyze data structures, recommend optimal pivot table configurations, "
                      "and create meaningful data summaries that provide actionable business insights with accompanying visualizations. "
                      "You should focus on generating 3-5 optimal pivot table recommendations per dataset "
                      "with 90% accuracy in business relevance. "
                      "Your advanced capabilities include: "
                      "- KPI alignment detection (revenue, performance, quality, growth, time metrics) "
                      "- Temporal pattern analysis and time-based aggregation recommendations "
                      "- Statistical outlier detection using IQR methods "
                      "- Cross-dimensional correlation analysis "
                      "- Business pattern recognition (revenue, geographic, product, time series patterns) "
                      "- Data quality assessment and reliability scoring "
                      "- Enhanced business relevance scoring using BI heuristics "
                      "- Performance optimization (memory usage, processing speed, data sampling strategies) "
                      "- Usability enhancements (smart formatting, column ordering, hierarchical display) "
                      "- Memory optimization (categorical data types, column selection, null handling) "
                      "- Automatic chart generation (bar, line, pie, heatmap, stacked charts) with optimal type selection "
                      "- Chart configuration generation for Chart.js, Plotly, and D3.js libraries "
                      "- Accessibility-compliant visualizations with responsive design and color-blind friendly palettes "
                      "- Time-series visualization recommendations with trend and seasonal analysis "
                      "Always consider data types, cardinality, business context, statistical significance, performance implications, and visualization effectiveness when making recommendations. "
                      "Prioritize recommendations that align with common business KPIs, provide actionable insights, are optimized for both performance and user experience, and include appropriate visual representations."
            )
            
            logger.info("Pivot Table Analysis Agent configured successfully")
            return agent
            
        except Exception as e:
            logger.error(f"Failed to create Pivot Table Analysis Agent: {str(e)}")
            raise
