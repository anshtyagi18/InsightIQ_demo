"""
Enhanced Intelligent Comparison Agent

This agent specializes in comparing estimated/forecasted datasets with actual performance data.
It provides AI-powered alignment, variance analysis, trend comparison, and natural language explanations.
"""

from typing import Dict, List, Any, Optional, Tuple, Union
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass, asdict
import asyncio
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MinMaxScaler
import json
import re
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)

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

@dataclass
class DataAlignment:
    """Result of data alignment between estimated and actual datasets."""
    column_mapping: Dict[str, str]
    temporal_alignment: Dict[str, Any]
    common_dimensions: List[str]
    alignment_confidence: float
    missing_mappings: List[str]

class IntelligentComparisonAgent:
    """
    ENHANCED AI-powered agent for comparing estimated vs actual datasets.
    
    Capabilities:
    - Enhanced intelligent column matching using semantic similarity
    - Temporal data alignment
    - Deep individual metric analysis
    - Comprehensive variance analysis with statistical significance
    - Trend pattern detection and deviation analysis
    - Granular insights by regions/categories
    - Missing metrics detection
    - Business impact prioritization
    - Natural language insights generation
    - Actionable recommendations
    """
    
    def __init__(self):
        self.business_synonyms = {
            'revenue': ['sales', 'income', 'earnings', 'turnover'],
            'cost': ['expense', 'expenditure', 'spend', 'outlay'],
            'profit': ['margin', 'net income', 'earnings', 'surplus'],
            'quantity': ['volume', 'amount', 'count', 'units'],
            'date': ['time', 'period', 'month', 'week', 'day'],
            'category': ['type', 'class', 'segment', 'group'],
            'performance': ['kpi', 'metric', 'measure', 'indicator'],
            'target': ['goal', 'forecast', 'plan', 'projection', 'estimated'],
            'actual': ['real', 'achieved', 'realized', 'delivered'],
            'energy': ['power', 'electricity', 'delivered', 'consumption', 'kwh', 'mwh'],
            'units': ['count', 'number', 'quantity', 'volume', 'pieces'],
            'rating': ['grade', 'score', 'class', 'level', 'tier'],
            'region': ['area', 'zone', 'location', 'territory', 'district'],
            'product': ['item', 'service', 'category', 'type', 'variant']
        }
        
        self.variance_thresholds = {
            'critical': 0.25,  # 25% variance
            'significant': 0.15,  # 15% variance
            'moderate': 0.10,  # 10% variance
            'minor': 0.05   # 5% variance
        }

    async def compare_datasets(
        self, 
        estimated_df: pd.DataFrame, 
        actual_df: pd.DataFrame,
        comparison_config: Optional[Dict[str, Any]] = None
    ) -> ComparisonResult:
        """
        ENHANCED Main method to perform deep comparison between estimated vs actual datasets.
        
        Args:
            estimated_df: DataFrame containing estimated/forecasted data
            actual_df: DataFrame containing actual performance data
            comparison_config: Optional configuration for comparison parameters
            
        Returns:
            ComparisonResult with comprehensive deep analysis
        """
        logger.info("[COMPARISON] Starting ENHANCED intelligent dataset comparison")
        
        try:
            # Step 1: Enhanced dataset alignment with case-insensitive matching
            alignment = await self._align_datasets_enhanced(estimated_df, actual_df, comparison_config or {})
            logger.info(f"[COMPARISON] Enhanced data alignment completed with confidence: {alignment.alignment_confidence}")
            
            # Step 2: Deep individual metric analysis - NEW
            individual_metrics_analysis = await self._analyze_individual_metrics(
                estimated_df, actual_df, alignment, comparison_config or {}
            )
            logger.info(f"[COMPARISON] Individual metrics analysis completed for {len(individual_metrics_analysis.get('metrics', []))} metrics")
            
            # Step 3: Enhanced variance analysis with granular insights
            variance_analysis = await self._analyze_variance_enhanced(
                estimated_df, actual_df, alignment, comparison_config or {}
            )
            logger.info(f"[COMPARISON] Enhanced variance analysis completed")
            
            # Step 4: Deep trend deviation analysis - NEW 
            trend_deviation_analysis = await self._analyze_trend_deviations(
                estimated_df, actual_df, alignment, comparison_config or {}
            )
            logger.info(f"[COMPARISON] Trend deviation analysis completed")
            
            # Step 5: Granular insight extraction by categories/regions - NEW
            granular_insights = await self._extract_granular_insights(
                estimated_df, actual_df, alignment, individual_metrics_analysis, variance_analysis
            )
            logger.info(f"[COMPARISON] Granular insights extraction completed")
            
            # Step 6: Missing metrics detection - NEW
            missing_metrics = await self._detect_missing_metrics(estimated_df, actual_df, alignment)
            logger.info(f"[COMPARISON] Missing metrics detection completed")
            
            # Step 7: Business impact prioritization - NEW
            prioritized_insights = await self._prioritize_insights_by_business_impact(
                individual_metrics_analysis, variance_analysis, trend_deviation_analysis, granular_insights
            )
            logger.info(f"[COMPARISON] Business impact prioritization completed")
            
            # Step 8: Enhanced visualization generation
            enhanced_charts = await self._create_enhanced_comparison_charts(
                estimated_df, actual_df, alignment, individual_metrics_analysis, 
                variance_analysis, trend_deviation_analysis, granular_insights
            )
            logger.info(f"[COMPARISON] Created {len(enhanced_charts)} enhanced charts")
            
            # Step 9: Comprehensive KPI generation
            comprehensive_kpis = await self._generate_comprehensive_kpis(
                individual_metrics_analysis, variance_analysis, trend_deviation_analysis, 
                alignment, missing_metrics
            )
            logger.info(f"[COMPARISON] Generated {len(comprehensive_kpis)} comprehensive KPIs")
            
            # Step 10: Generate enhanced recommendations with specific actions
            enhanced_recommendations = await self._generate_enhanced_recommendations(
                prioritized_insights, missing_metrics, variance_analysis, trend_deviation_analysis
            )
            logger.info(f"[COMPARISON] Generated {len(enhanced_recommendations)} enhanced recommendations")
            
            # Compile comprehensive result with all new components
            result = ComparisonResult(
                overall_variance=variance_analysis.get('overall_variance', 0.0),
                trend_alignment=trend_deviation_analysis.get('overall_alignment_status', 'unknown'),
                critical_deviations=prioritized_insights.get('high_impact_deviations', []),
                performance_summary={
                    **variance_analysis.get('summary', {}),
                    'individual_metrics_summary': individual_metrics_analysis.get('summary', {}),
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
            
            logger.info("[COMPARISON] ENHANCED dataset comparison completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"[COMPARISON] Error in enhanced dataset comparison: {str(e)}")
            raise

    async def _align_datasets_enhanced(
        self, 
        estimated_df: pd.DataFrame, 
        actual_df: pd.DataFrame, 
        config: Dict[str, Any]
    ) -> DataAlignment:
        """Enhanced dataset alignment with improved case-insensitive matching."""
        logger.info("[ALIGNMENT] Starting enhanced dataset alignment")
        
        try:
            # Create case-insensitive column mappings
            column_mapping = {}
            estimated_cols = list(estimated_df.columns)
            actual_cols = list(actual_df.columns)
            
            logger.info(f"[ALIGNMENT] Estimated columns: {estimated_cols}")
            logger.info(f"[ALIGNMENT] Actual columns: {actual_cols}")
            
            # Enhanced column matching
            for est_col in estimated_cols:
                best_match = await self._find_best_column_match_enhanced(est_col, actual_cols)
                if best_match:
                    column_mapping[est_col] = best_match
                    logger.info(f"[ALIGNMENT] Mapped '{est_col}' -> '{best_match}'")
            
            # Find temporal alignment
            temporal_alignment = await self._find_temporal_alignment_enhanced(
                estimated_df, actual_df, column_mapping
            )
            
            # Find common dimensions for grouping
            common_dimensions = await self._find_common_dimensions_enhanced(
                estimated_df, actual_df, column_mapping
            )
            
            # Calculate alignment confidence
            alignment_confidence = self._calculate_alignment_confidence_enhanced(
                column_mapping, temporal_alignment, common_dimensions, estimated_df, actual_df
            )
            
            # Find missing mappings
            missing_mappings = self._find_missing_mappings_enhanced(
                estimated_df, actual_df, column_mapping
            )
            
            alignment = DataAlignment(
                column_mapping=column_mapping,
                temporal_alignment=temporal_alignment,
                common_dimensions=common_dimensions,
                alignment_confidence=alignment_confidence,
                missing_mappings=missing_mappings
            )
            
            logger.info(f"[ALIGNMENT] Enhanced alignment completed with {len(column_mapping)} mappings")
            return alignment
            
        except Exception as e:
            logger.error(f"[ALIGNMENT] Error in enhanced dataset alignment: {str(e)}")
            raise

    async def _find_best_column_match_enhanced(
        self, 
        target_col: str, 
        candidate_cols: List[str]
    ) -> Optional[str]:
        """Enhanced column matching with improved case-insensitive logic."""
        target_lower = target_col.lower().strip()
        best_score = 0.0
        best_match = None
        
        for candidate in candidate_cols:
            candidate_lower = candidate.lower().strip()
            score = 0.0
            
            # Exact match (case-insensitive)
            if target_lower == candidate_lower:
                return candidate
            
            # Substring match
            if target_lower in candidate_lower or candidate_lower in target_lower:
                score += 0.8
            
            # Enhanced semantic similarity
            score += self._calculate_semantic_similarity_enhanced(target_lower, candidate_lower)
            
            # String similarity with fuzzy matching
            score += SequenceMatcher(None, target_lower, candidate_lower).ratio() * 0.6
            
            # Word overlap analysis
            target_words = set(re.findall(r'\w+', target_lower))
            candidate_words = set(re.findall(r'\w+', candidate_lower))
            if target_words and candidate_words:
                overlap = len(target_words & candidate_words) / len(target_words | candidate_words)
                score += overlap * 0.7
                
            # Business context matching
            score += self._calculate_business_context_similarity(target_lower, candidate_lower)
            
            if score > best_score and score > 0.4:  # Lower threshold for better matching
                best_score = score
                best_match = candidate
                
        return best_match

    def _calculate_semantic_similarity_enhanced(self, col1: str, col2: str) -> float:
        """Enhanced semantic similarity with extended business vocabulary."""
        similarity = 0.0
        
        # Extended business synonyms
        extended_synonyms = {
            **self.business_synonyms,
            'energy': ['power', 'electricity', 'delivered', 'consumption', 'kwh', 'mwh'],
            'units': ['count', 'number', 'quantity', 'volume', 'pieces'],
            'rating': ['grade', 'score', 'class', 'level', 'tier'],
            'region': ['area', 'zone', 'location', 'territory', 'district'],
            'product': ['item', 'service', 'category', 'type', 'variant'],
            'time': ['date', 'period', 'month', 'quarter', 'year', 'week'],
            'performance': ['achievement', 'result', 'outcome', 'output']
        }
        
        for concept, synonyms in extended_synonyms.items():
            if concept in col1 or any(syn in col1 for syn in synonyms):
                if concept in col2 or any(syn in col2 for syn in synonyms):
                    similarity += 0.9
                    break
                    
        return min(similarity, 1.0)

    def _calculate_business_context_similarity(self, col1: str, col2: str) -> float:
        """Calculate similarity based on business context patterns."""
        patterns = {
            'financial': ['revenue', 'cost', 'profit', 'price', 'amount', 'value', 'money'],
            'operational': ['units', 'quantity', 'volume', 'count', 'production'],
            'temporal': ['date', 'time', 'period', 'month', 'year', 'quarter'],
            'categorical': ['type', 'category', 'class', 'group', 'segment'],
            'performance': ['rating', 'score', 'grade', 'performance', 'efficiency']
        }
        
        for pattern_type, keywords in patterns.items():
            col1_match = any(keyword in col1 for keyword in keywords)
            col2_match = any(keyword in col2 for keyword in keywords)
            
            if col1_match and col2_match:
                return 0.3
                
        return 0.0

    async def _analyze_individual_metrics(
        self, 
        estimated_df: pd.DataFrame, 
        actual_df: pd.DataFrame, 
        alignment: DataAlignment, 
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """NEW: Deep analysis of each individual metric with comprehensive comparisons."""
        logger.info("[INDIVIDUAL_METRICS] Starting individual metrics analysis")
        
        try:
            metrics_analysis = {
                'metrics': [],
                'summary': {
                    'total_metrics_analyzed': 0,
                    'metrics_with_high_variance': 0,
                    'metrics_with_trend_misalignment': 0,
                    'best_performing_metric': None,
                    'worst_performing_metric': None
                }
            }
            
            metric_performances = []
            
            for est_col, act_col in alignment.column_mapping.items():
                if (est_col in estimated_df.columns and act_col in actual_df.columns):
                    # Only analyze numeric columns
                    if (pd.api.types.is_numeric_dtype(estimated_df[est_col]) and 
                        pd.api.types.is_numeric_dtype(actual_df[act_col])):
                        
                        metric_analysis = await self._analyze_single_metric(
                            estimated_df[est_col], actual_df[act_col], est_col, act_col, 
                            estimated_df, actual_df, alignment
                        )
                        
                        if metric_analysis:
                            metrics_analysis['metrics'].append(metric_analysis)
                            metric_performances.append({
                                'metric': est_col,
                                'accuracy_score': metric_analysis.get('accuracy_score', 0)
                            })
                            
            # Calculate summary statistics
            metrics_analysis['summary']['total_metrics_analyzed'] = len(metrics_analysis['metrics'])
            
            high_variance_count = sum(1 for m in metrics_analysis['metrics'] 
                                    if abs(m.get('variance_percentage', 0)) > 15)
            metrics_analysis['summary']['metrics_with_high_variance'] = high_variance_count
            
            trend_misalignment_count = sum(1 for m in metrics_analysis['metrics'] 
                                         if m.get('trend_correlation', 1) < 0.6)
            metrics_analysis['summary']['metrics_with_trend_misalignment'] = trend_misalignment_count
            
            # Find best and worst performing metrics
            if metric_performances:
                best_metric = max(metric_performances, key=lambda x: x['accuracy_score'])
                worst_metric = min(metric_performances, key=lambda x: x['accuracy_score'])
                metrics_analysis['summary']['best_performing_metric'] = best_metric['metric']
                metrics_analysis['summary']['worst_performing_metric'] = worst_metric['metric']
            
            logger.info(f"[INDIVIDUAL_METRICS] Analyzed {len(metrics_analysis['metrics'])} individual metrics")
            return metrics_analysis
            
        except Exception as e:
            logger.error(f"[INDIVIDUAL_METRICS] Error in individual metrics analysis: {str(e)}")
            raise

    async def _analyze_single_metric(
        self, 
        estimated_series: pd.Series, 
        actual_series: pd.Series, 
        est_col_name: str, 
        act_col_name: str,
        estimated_df: pd.DataFrame,
        actual_df: pd.DataFrame,
        alignment: DataAlignment
    ) -> Optional[Dict[str, Any]]:
        """Analyze a single metric with comprehensive statistics."""
        try:
            # Clean data
            est_clean = pd.to_numeric(estimated_series, errors='coerce').dropna()
            act_clean = pd.to_numeric(actual_series, errors='coerce').dropna()
            
            if len(est_clean) == 0 or len(act_clean) == 0:
                return None
            
            # Basic statistics
            est_sum = est_clean.sum()
            act_sum = act_clean.sum()
            est_mean = est_clean.mean()
            act_mean = act_clean.mean()
            est_std = est_clean.std()
            act_std = act_clean.std()
            
            # Variance calculations
            if est_sum != 0:
                variance_percentage = ((act_sum - est_sum) / est_sum) * 100
            else:
                variance_percentage = 0 if act_sum == 0 else float('inf')
            
            # MAPE calculation
            mape = self._calculate_mape(est_clean, act_clean)
            
            # Correlation analysis
            if len(est_clean) > 1 and len(act_clean) > 1:
                # Align series for correlation
                min_len = min(len(est_clean), len(act_clean))
                correlation = np.corrcoef(est_clean[:min_len], act_clean[:min_len])[0, 1]
                if np.isnan(correlation):
                    correlation = 0.0
            else:
                correlation = 0.0
            
            # Calculate accuracy score (inverse of MAPE)
            accuracy_score = max(0, 100 - mape) if not np.isnan(mape) and mape != float('inf') else 0
            
            # Trend analysis
            trend_analysis = self._analyze_metric_trend(est_clean, act_clean)
            
            # Seasonal pattern detection
            seasonal_patterns = self._detect_seasonal_patterns(est_clean, act_clean)
            
            # Outlier detection
            outliers = self._detect_outliers_in_metric(est_clean, act_clean)
            
            return {
                'metric_name': est_col_name,
                'matched_column': act_col_name,
                'estimated_total': float(est_sum),
                'actual_total': float(act_sum),
                'estimated_mean': float(est_mean),
                'actual_mean': float(act_mean),
                'estimated_std': float(est_std),
                'actual_std': float(act_std),
                'variance_percentage': float(variance_percentage),
                'mape': float(mape) if not np.isnan(mape) else 0.0,
                'trend_correlation': float(correlation),
                'accuracy_score': float(accuracy_score),
                'trend_analysis': trend_analysis,
                'seasonal_patterns': seasonal_patterns,
                'outliers_detected': outliers,
                'deviation_severity': self._categorize_variance_severity(variance_percentage),
                'data_points_compared': min(len(est_clean), len(act_clean))
            }
            
        except Exception as e:
            logger.error(f"[SINGLE_METRIC] Error analyzing metric {est_col_name}: {str(e)}")
            return None

    def _analyze_metric_trend(self, est_series: pd.Series, act_series: pd.Series) -> Dict[str, Any]:
        """Analyze trend patterns in a metric."""
        try:
            trend_analysis = {
                'estimated_trend': 'stable',
                'actual_trend': 'stable',
                'trend_alignment': 'unknown',
                'trend_strength': 0.0
            }
            
            if len(est_series) > 2:
                # Calculate linear trend
                x = np.arange(len(est_series))
                est_slope = np.polyfit(x, est_series, 1)[0]
                
                if est_slope > 0.1:
                    trend_analysis['estimated_trend'] = 'increasing'
                elif est_slope < -0.1:
                    trend_analysis['estimated_trend'] = 'decreasing'
                else:
                    trend_analysis['estimated_trend'] = 'stable'
            
            if len(act_series) > 2:
                x = np.arange(len(act_series))
                act_slope = np.polyfit(x, act_series, 1)[0]
                
                if act_slope > 0.1:
                    trend_analysis['actual_trend'] = 'increasing'
                elif act_slope < -0.1:
                    trend_analysis['actual_trend'] = 'decreasing'
                else:
                    trend_analysis['actual_trend'] = 'stable'
            
            # Determine alignment
            if trend_analysis['estimated_trend'] == trend_analysis['actual_trend']:
                trend_analysis['trend_alignment'] = 'aligned'
                trend_analysis['trend_strength'] = 1.0
            else:
                trend_analysis['trend_alignment'] = 'misaligned'
                trend_analysis['trend_strength'] = 0.0
            
            return trend_analysis
            
        except Exception as e:
            logger.error(f"Error in trend analysis: {str(e)}")
            return {'estimated_trend': 'unknown', 'actual_trend': 'unknown', 'trend_alignment': 'unknown', 'trend_strength': 0.0}

    def _detect_seasonal_patterns(self, est_series: pd.Series, act_series: pd.Series) -> Dict[str, Any]:
        """Detect seasonal patterns in the data."""
        try:
            seasonal_info = {
                'estimated_seasonality': False,
                'actual_seasonality': False,
                'seasonal_alignment': False,
                'seasonal_strength': 0.0
            }
            
            # Simple seasonality detection based on variance patterns
            if len(est_series) >= 12:  # Need at least 12 data points
                est_var = est_series.rolling(window=3).var().dropna()
                if len(est_var) > 0 and est_var.std() > est_var.mean() * 0.5:
                    seasonal_info['estimated_seasonality'] = True
            
            if len(act_series) >= 12:
                act_var = act_series.rolling(window=3).var().dropna()
                if len(act_var) > 0 and act_var.std() > act_var.mean() * 0.5:
                    seasonal_info['actual_seasonality'] = True
            
            # Check if both show seasonality
            if seasonal_info['estimated_seasonality'] and seasonal_info['actual_seasonality']:
                seasonal_info['seasonal_alignment'] = True
                seasonal_info['seasonal_strength'] = 0.8
            
            return seasonal_info
            
        except Exception as e:
            logger.error(f"Error in seasonal pattern detection: {str(e)}")
            return {'estimated_seasonality': False, 'actual_seasonality': False, 'seasonal_alignment': False, 'seasonal_strength': 0.0}

    def _detect_outliers_in_metric(self, est_series: pd.Series, act_series: pd.Series) -> Dict[str, Any]:
        """Detect outliers in estimated vs actual data."""
        try:
            outliers_info = {
                'estimated_outliers_count': 0,
                'actual_outliers_count': 0,
                'outlier_impact': 'low'
            }
            
            # Use IQR method for outlier detection
            def detect_outliers_iqr(series):
                if len(series) < 4:
                    return []
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
            logger.error(f"Error in outlier detection: {str(e)}")
            return {'estimated_outliers_count': 0, 'actual_outliers_count': 0, 'outlier_impact': 'unknown'}

    def _calculate_mape(self, est_series: pd.Series, act_series: pd.Series) -> float:
        """Calculate Mean Absolute Percentage Error."""
        try:
            if len(est_series) == 0 or len(act_series) == 0:
                return float('inf')
            
            # Align series
            min_len = min(len(est_series), len(act_series))
            est_aligned = est_series[:min_len]
            act_aligned = act_series[:min_len]
            
            # Remove zero values from denominator to avoid division by zero
            non_zero_mask = est_aligned != 0
            if not non_zero_mask.any():
                return float('inf')
            
            est_filtered = est_aligned[non_zero_mask]
            act_filtered = act_aligned[non_zero_mask]
            
            mape = np.mean(np.abs((act_filtered - est_filtered) / est_filtered)) * 100
            return float(mape)
            
        except Exception as e:
            logger.error(f"Error calculating MAPE: {str(e)}")
            return float('inf')

    def _categorize_variance_severity(self, variance_percentage: float) -> str:
        """Categorize the severity of variance."""
        try:
            abs_variance = abs(variance_percentage)
            
            if abs_variance > self.variance_thresholds['critical'] * 100:
                return 'critical'
            elif abs_variance > self.variance_thresholds['significant'] * 100:
                return 'significant'
            elif abs_variance > self.variance_thresholds['moderate'] * 100:
                return 'moderate'
            elif abs_variance > self.variance_thresholds['minor'] * 100:
                return 'minor'
            else:
                return 'minimal'
                
        except Exception:
            return 'unknown'

    # Placeholder methods for missing functionality - to be implemented
    async def _find_temporal_alignment_enhanced(self, estimated_df, actual_df, column_mapping):
        """Enhanced temporal alignment."""
        return {'temporal_columns': [], 'date_mapping': {}}

    async def _find_common_dimensions_enhanced(self, estimated_df, actual_df, column_mapping):
        """Enhanced common dimensions finding."""
        return []

    def _calculate_alignment_confidence_enhanced(self, column_mapping, temporal_alignment, common_dimensions, estimated_df, actual_df):
        """Enhanced alignment confidence calculation."""
        if not column_mapping:
            return 0.0
        return len(column_mapping) / max(len(estimated_df.columns), len(actual_df.columns))

    def _find_missing_mappings_enhanced(self, estimated_df, actual_df, column_mapping):
        """Enhanced missing mappings detection."""
        mapped_est = set(column_mapping.keys())
        mapped_act = set(column_mapping.values())
        return list((set(estimated_df.columns) - mapped_est) | (set(actual_df.columns) - mapped_act))

    async def _analyze_variance_enhanced(self, estimated_df, actual_df, alignment, config):
        """Enhanced variance analysis - placeholder."""
        return {
            'overall_variance': 0.0,
            'column_variances': {},
            'critical_deviations': [],
            'summary': {}
        }

    async def _analyze_trend_deviations(self, estimated_df, actual_df, alignment, config):
        """Trend deviation analysis - placeholder."""
        return {
            'overall_alignment_status': 'unknown',
            'metric_trend_correlations': {},
            'divergence_periods': [],
            'summary': {}
        }

    async def _extract_granular_insights(self, estimated_df, actual_df, alignment, individual_metrics, variance_analysis):
        """Granular insights extraction - placeholder."""
        return {
            'insights_by_category': {},
            'summary': {}
        }

    async def _detect_missing_metrics(self, estimated_df, actual_df, alignment):
        """Missing metrics detection - placeholder."""
        return {
            'missing_in_estimated': [],
            'missing_in_actual': [],
            'total_missing': 0
        }

    async def _prioritize_insights_by_business_impact(self, individual_metrics, variance_analysis, trend_deviation, granular_insights):
        """Business impact prioritization - placeholder."""
        return {
            'high_impact_deviations': [],
            'insights': [],
            'summary': {}
        }

    async def _create_enhanced_comparison_charts(self, estimated_df, actual_df, alignment, individual_metrics, variance_analysis, trend_deviation, granular_insights):
        """Enhanced charts creation - placeholder."""
        return []

    async def _generate_comprehensive_kpis(self, individual_metrics, variance_analysis, trend_deviation, alignment, missing_metrics):
        """Comprehensive KPIs generation - placeholder."""
        return []

    async def _generate_enhanced_recommendations(self, prioritized_insights, missing_metrics, variance_analysis, trend_deviation):
        """Enhanced recommendations generation - placeholder."""
        return []