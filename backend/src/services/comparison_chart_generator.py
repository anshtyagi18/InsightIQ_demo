"""
Comparison Chart Generator

Generates intelligent, context-aware charts for comparison analysis including:
- Adaptive chart selection based on data characteristics
- Business-focused visualizations
- Interactive chart configurations
- AI-suggested chart types and insights
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, cast
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class ComparisonChartGenerator:
    """
    Intelligent chart generator for comparison analysis.
    Creates context-aware visualizations optimized for business insights.
    """
    
    def __init__(self):
        self.chart_templates = {
            'variance_overview': self._create_variance_overview_chart,
            'side_by_side': self._create_side_by_side_chart,
            'trend_correlation': self._create_trend_correlation_chart,
            'deviation_heatmap': self._create_deviation_heatmap_chart,
            'performance_dashboard': self._create_performance_dashboard_chart,
            'metric_breakdown': self._create_metric_breakdown_chart,
            'accuracy_gauge': self._create_accuracy_gauge_chart,
            'waterfall': self._create_waterfall_chart
        }
    
    async def generate_intelligent_charts(self, estimated_df: pd.DataFrame, actual_df: pd.DataFrame,
                                        column_mapping: Dict[str, str], analysis_result: Dict[str, Any],
                                        context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate intelligent charts based on data characteristics and analysis results.
        
        Args:
            estimated_df: Estimated data DataFrame
            actual_df: Actual data DataFrame  
            column_mapping: Column mapping between datasets
            analysis_result: Results from comparison analysis
            context: Business context and data characteristics
            
        Returns:
            List of chart configurations optimized for the data
        """
        try:
            logger.info("[CHART_GEN] Generating intelligent charts for comparison analysis")
            
            charts = []
            
            # Determine optimal chart types based on data characteristics
            chart_strategy = await self._determine_chart_strategy(
                estimated_df, actual_df, column_mapping, analysis_result, context
            )
            
            logger.info(f"[CHART_GEN] Chart strategy: {chart_strategy['approach']}")
            
            # Generate charts based on strategy
            for chart_type in chart_strategy['recommended_charts']:
                try:
                    if chart_type in self.chart_templates:
                        chart = await self.chart_templates[chart_type](
                            estimated_df, actual_df, column_mapping, analysis_result, context
                        )
                        if chart:
                            charts.append(chart)
                            logger.info(f"[CHART_GEN] Generated {chart_type} chart")
                except Exception as e:
                    logger.warning(f"[CHART_GEN] Failed to generate {chart_type} chart: {str(e)}")
            
            # Limit charts based on analysis level
            max_charts = self._get_max_charts(context.get('analysis_level', 'standard'))
            charts = charts[:max_charts]
            
            logger.info(f"[CHART_GEN] Generated {len(charts)} charts")
            return charts
            
        except Exception as e:
            logger.error(f"[CHART_GEN] Error generating charts: {str(e)}")
            return self._generate_fallback_charts(estimated_df, actual_df, column_mapping)
    
    async def _determine_chart_strategy(self, estimated_df: pd.DataFrame, actual_df: pd.DataFrame,
                                      column_mapping: Dict[str, str], analysis_result: Dict[str, Any],
                                      context: Dict[str, Any]) -> Dict[str, Any]:
        """Determine the optimal chart strategy based on data characteristics."""
        try:
            strategy = {
                'approach': 'adaptive',
                'recommended_charts': [],
                'priority_metrics': [],
                'visualization_focus': 'variance'
            }
            
            # Analyze data characteristics
            num_metrics = len(column_mapping)
            data_size = min(len(estimated_df), len(actual_df))
            business_domain = context.get('business_domain', 'general')
            
            # Always include variance overview
            strategy['recommended_charts'].append('variance_overview')
            
            # Add charts based on number of metrics
            if num_metrics >= 2:
                strategy['recommended_charts'].append('side_by_side')
                
            if num_metrics >= 3:
                strategy['recommended_charts'].append('deviation_heatmap')
            
            # Add trend analysis if we have time-series data
            if data_size >= 5:
                strategy['recommended_charts'].append('trend_correlation')
            
            # Add performance dashboard for comprehensive analysis
            if context.get('analysis_level') == 'comprehensive':
                strategy['recommended_charts'].extend(['performance_dashboard', 'metric_breakdown'])
            
            # Business domain specific charts
            if business_domain in ['finance', 'sales']:
                strategy['recommended_charts'].append('waterfall')
                strategy['visualization_focus'] = 'financial_impact'
            elif business_domain in ['operations', 'manufacturing']:
                strategy['recommended_charts'].append('accuracy_gauge')
                strategy['visualization_focus'] = 'operational_efficiency'
            
            # Prioritize metrics with highest variance
            variance_analysis = analysis_result.get('variance_analysis', {})
            if 'metrics' in variance_analysis:
                sorted_metrics = sorted(
                    variance_analysis['metrics'],
                    key=lambda x: abs(x.get('variance_percentage', 0)),
                    reverse=True
                )
                strategy['priority_metrics'] = [m['metric'] for m in sorted_metrics[:3]]
            
            return strategy
            
        except Exception as e:
            logger.error(f"Error determining chart strategy: {str(e)}")
            return {
                'approach': 'basic',
                'recommended_charts': ['variance_overview', 'side_by_side'],
                'priority_metrics': [],
                'visualization_focus': 'variance'
            }
    
    async def _create_variance_overview_chart(self, estimated_df: pd.DataFrame, actual_df: pd.DataFrame,
                                            column_mapping: Dict[str, str], analysis_result: Dict[str, Any],
                                            context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a variance overview chart showing all metrics."""
        try:
            variance_data = []
            
            for est_col, act_col in column_mapping.items():
                if est_col in estimated_df.columns and act_col in actual_df.columns:
                    est_values = cast(pd.Series, pd.to_numeric(estimated_df[est_col], errors='coerce'))
                    act_values = cast(pd.Series, pd.to_numeric(actual_df[act_col], errors='coerce'))
                    
                    if est_values.notna().sum() > 0 and act_values.notna().sum() > 0:
                        est_sum = est_values.sum()
                        act_sum = act_values.sum()
                        
                        if abs(est_sum) > 0.001:
                            variance = ((act_sum - est_sum) / est_sum) * 100
                            
                            variance_data.append({
                                'metric': est_col.replace('_', ' '),
                                'variance': round(variance, 2),
                                'estimated': round(est_sum, 2),
                                'actual': round(act_sum, 2),
                                'absolute_variance': round(abs(variance), 2)
                            })
            
            if not variance_data:
                return None
            
            # Sort by absolute variance for better visualization
            variance_data.sort(key=lambda x: x['absolute_variance'], reverse=True)
            
            return {
                'type': 'bar',
                'title': 'Variance Overview - All Metrics',
                'subtitle': 'Percentage variance between estimated and actual values',
                'data': variance_data,
                'config': {
                    'xAxisKey': 'metric',
                    'bars': [
                        {
                            'dataKey': 'variance',
                            'name': 'Variance %',
                            'fill': '#8884d8'
                        }
                    ],
                    'tooltip': {
                        'formatter': 'variance_tooltip'
                    },
                    'yAxisLabel': 'Variance (%)',
                    'colorScale': 'variance_severity'
                },
                'insights': [
                    f"Highest variance: {variance_data[0]['metric']} ({variance_data[0]['variance']:.1f}%)",
                    f"Analyzed {len(variance_data)} metrics total"
                ]
            }
            
        except Exception as e:
            logger.error(f"Error creating variance overview chart: {str(e)}")
            return None
    
    async def _create_side_by_side_chart(self, estimated_df: pd.DataFrame, actual_df: pd.DataFrame,
                                       column_mapping: Dict[str, str], analysis_result: Dict[str, Any],
                                       context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a side-by-side comparison chart."""
        try:
            comparison_data = []
            
            for est_col, act_col in list(column_mapping.items())[:5]:  # Limit to 5 metrics
                if est_col in estimated_df.columns and act_col in actual_df.columns:
                    est_values = cast(pd.Series, pd.to_numeric(estimated_df[est_col], errors='coerce'))
                    act_values = cast(pd.Series, pd.to_numeric(actual_df[act_col], errors='coerce'))
                    
                    if est_values.notna().sum() > 0 and act_values.notna().sum() > 0:
                        comparison_data.append({
                            'metric': est_col.replace('_', ' '),
                            'estimated': round(est_values.sum(), 2),
                            'actual': round(act_values.sum(), 2)
                        })
            
            if not comparison_data:
                return None
            
            return {
                'type': 'grouped_bar',
                'title': 'Estimated vs Actual Comparison',
                'subtitle': 'Side-by-side comparison of key metrics',
                'data': comparison_data,
                'config': {
                    'xAxisKey': 'metric',
                    'bars': [
                        {
                            'dataKey': 'estimated',
                            'name': 'Estimated',
                            'fill': '#8884d8'
                        },
                        {
                            'dataKey': 'actual',
                            'name': 'Actual',
                            'fill': '#82ca9d'
                        }
                    ],
                    'yAxisLabel': 'Value',
                    'legend': True
                },
                'insights': [
                    f"Comparing {len(comparison_data)} key metrics",
                    "Blue bars show estimated values, green bars show actual values"
                ]
            }
            
        except Exception as e:
            logger.error(f"Error creating side-by-side chart: {str(e)}")
            return None
    
    async def _create_trend_correlation_chart(self, estimated_df: pd.DataFrame, actual_df: pd.DataFrame,
                                            column_mapping: Dict[str, str], analysis_result: Dict[str, Any],
                                            context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a trend correlation chart."""
        try:
            # Use the first numeric column pair for trend analysis
            for est_col, act_col in column_mapping.items():
                if est_col in estimated_df.columns and act_col in actual_df.columns:
                    est_values = cast(pd.Series, pd.to_numeric(estimated_df[est_col], errors='coerce')).dropna()
                    act_values = cast(pd.Series, pd.to_numeric(actual_df[act_col], errors='coerce')).dropna()
                    
                    if len(est_values) >= 3 and len(act_values) >= 3:
                        min_len = min(len(est_values), len(act_values))
                        
                        trend_data = []
                        for i in range(min_len):
                            trend_data.append({
                                'period': f'Period {i+1}',
                                'estimated': round(float(est_values.iloc[i]), 2),
                                'actual': round(float(act_values.iloc[i]), 2)
                            })
                        
                        # Calculate correlation
                        correlation = np.corrcoef(est_values[:min_len], act_values[:min_len])[0, 1]
                        
                        return {
                            'type': 'line',
                            'title': f'Trend Analysis - {est_col.replace("_", " ")}',
                            'subtitle': f'Correlation: {correlation:.3f}',
                            'data': trend_data,
                            'config': {
                                'xAxisKey': 'period',
                                'lines': [
                                    {
                                        'dataKey': 'estimated',
                                        'name': 'Estimated',
                                        'stroke': '#8884d8',
                                        'strokeWidth': 2
                                    },
                                    {
                                        'dataKey': 'actual',
                                        'name': 'Actual',
                                        'stroke': '#82ca9d',
                                        'strokeWidth': 2
                                    }
                                ],
                                'yAxisLabel': 'Value',
                                'legend': True
                            },
                            'insights': [
                                f"Correlation coefficient: {correlation:.3f}",
                                f"Trend alignment: {'Strong' if abs(correlation) > 0.7 else 'Moderate' if abs(correlation) > 0.4 else 'Weak'}"
                            ]
                        }
            
            return None
            
        except Exception as e:
            logger.error(f"Error creating trend correlation chart: {str(e)}")
            return None
    
    async def _create_deviation_heatmap_chart(self, estimated_df: pd.DataFrame, actual_df: pd.DataFrame,
                                            column_mapping: Dict[str, str], analysis_result: Dict[str, Any],
                                            context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a deviation heatmap chart."""
        try:
            heatmap_data = []
            
            for est_col, act_col in column_mapping.items():
                if est_col in estimated_df.columns and act_col in actual_df.columns:
                    est_values = cast(pd.Series, pd.to_numeric(estimated_df[est_col], errors='coerce'))
                    act_values = cast(pd.Series, pd.to_numeric(actual_df[act_col], errors='coerce'))
                    
                    if est_values.notna().sum() > 0 and act_values.notna().sum() > 0:
                        # Calculate variance for each data point
                        for i in range(min(len(est_values), len(act_values))):
                            if pd.notna(est_values.iloc[i]) and pd.notna(act_values.iloc[i]):
                                est_val = est_values.iloc[i]
                                act_val = act_values.iloc[i]
                                
                                if abs(est_val) > 0.001:
                                    variance = ((act_val - est_val) / est_val) * 100
                                    
                                    heatmap_data.append({
                                        'metric': est_col.replace('_', ' '),
                                        'period': f'P{i+1}',
                                        'variance': round(variance, 1),
                                        'severity': self._categorize_variance_severity(variance)
                                    })
            
            if not heatmap_data:
                return None
            
            return {
                'type': 'heatmap',
                'title': 'Deviation Heatmap',
                'subtitle': 'Variance patterns across metrics and periods',
                'data': heatmap_data,
                'config': {
                    'xAxisKey': 'period',
                    'yAxisKey': 'metric',
                    'valueKey': 'variance',
                    'colorScale': 'variance_heatmap'
                },
                'insights': [
                    f"Analyzed {len(set(d['metric'] for d in heatmap_data))} metrics",
                    f"Across {len(set(d['period'] for d in heatmap_data))} periods"
                ]
            }
            
        except Exception as e:
            logger.error(f"Error creating deviation heatmap chart: {str(e)}")
            return None
    
    async def _create_performance_dashboard_chart(self, estimated_df: pd.DataFrame, actual_df: pd.DataFrame,
                                                column_mapping: Dict[str, str], analysis_result: Dict[str, Any],
                                                context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a performance dashboard chart."""
        try:
            # This would be a complex multi-panel dashboard
            # For now, return a summary performance chart
            
            performance_metrics = []
            
            # Calculate overall accuracy
            total_variance = 0
            metric_count = 0
            
            for est_col, act_col in column_mapping.items():
                if est_col in estimated_df.columns and act_col in actual_df.columns:
                    est_values = cast(pd.Series, pd.to_numeric(estimated_df[est_col], errors='coerce'))
                    act_values = cast(pd.Series, pd.to_numeric(actual_df[act_col], errors='coerce'))
                    
                    if est_values.notna().sum() > 0 and act_values.notna().sum() > 0:
                        est_sum = est_values.sum()
                        act_sum = act_values.sum()
                        
                        if abs(est_sum) > 0.001:
                            variance = abs(((act_sum - est_sum) / est_sum) * 100)
                            total_variance += variance
                            metric_count += 1
            
            if metric_count > 0:
                avg_variance = total_variance / metric_count
                accuracy = max(0, 100 - avg_variance)
                
                performance_metrics.append({
                    'category': 'Overall Accuracy',
                    'score': round(accuracy, 1),
                    'target': 85,
                    'status': 'good' if accuracy >= 85 else 'warning' if accuracy >= 70 else 'poor'
                })
            
            return {
                'type': 'gauge',
                'title': 'Performance Dashboard',
                'subtitle': 'Overall forecasting performance',
                'data': performance_metrics,
                'config': {
                    'valueKey': 'score',
                    'maxValue': 100,
                    'colorScale': 'performance'
                },
                'insights': [
                    f"Overall accuracy: {performance_metrics[0]['score']:.1f}%" if performance_metrics else "No data available"
                ]
            }
            
        except Exception as e:
            logger.error(f"Error creating performance dashboard chart: {str(e)}")
            return None
    
    async def _create_metric_breakdown_chart(self, estimated_df: pd.DataFrame, actual_df: pd.DataFrame,
                                           column_mapping: Dict[str, str], analysis_result: Dict[str, Any],
                                           context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a detailed metric breakdown chart."""
        # Implementation similar to variance overview but with more detail
        return await self._create_variance_overview_chart(estimated_df, actual_df, column_mapping, analysis_result, context)
    
    async def _create_accuracy_gauge_chart(self, estimated_df: pd.DataFrame, actual_df: pd.DataFrame,
                                         column_mapping: Dict[str, str], analysis_result: Dict[str, Any],
                                         context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create an accuracy gauge chart."""
        # Implementation similar to performance dashboard
        return await self._create_performance_dashboard_chart(estimated_df, actual_df, column_mapping, analysis_result, context)
    
    async def _create_waterfall_chart(self, estimated_df: pd.DataFrame, actual_df: pd.DataFrame,
                                    column_mapping: Dict[str, str], analysis_result: Dict[str, Any],
                                    context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a waterfall chart showing cumulative variance impact."""
        try:
            waterfall_data = []
            cumulative = 0
            
            # Start with estimated total
            est_total = 0
            for est_col in column_mapping.keys():
                if est_col in estimated_df.columns:
                    est_values = cast(pd.Series, pd.to_numeric(estimated_df[est_col], errors='coerce'))
                    if est_values.notna().sum() > 0:
                        est_total += est_values.sum()
            
            waterfall_data.append({
                'category': 'Estimated Total',
                'value': round(est_total, 2),
                'cumulative': round(est_total, 2),
                'type': 'start'
            })
            
            cumulative = est_total
            
            # Add variance for each metric
            for est_col, act_col in column_mapping.items():
                if est_col in estimated_df.columns and act_col in actual_df.columns:
                    est_values = cast(pd.Series, pd.to_numeric(estimated_df[est_col], errors='coerce'))
                    act_values = cast(pd.Series, pd.to_numeric(actual_df[act_col], errors='coerce'))
                    
                    if est_values.notna().sum() > 0 and act_values.notna().sum() > 0:
                        est_sum = est_values.sum()
                        act_sum = act_values.sum()
                        variance_amount = act_sum - est_sum
                        cumulative += variance_amount
                        
                        waterfall_data.append({
                            'category': f"{est_col.replace('_', ' ')} Variance",
                            'value': round(variance_amount, 2),
                            'cumulative': round(cumulative, 2),
                            'type': 'positive' if variance_amount > 0 else 'negative'
                        })
            
            # Add actual total
            waterfall_data.append({
                'category': 'Actual Total',
                'value': round(cumulative, 2),
                'cumulative': round(cumulative, 2),
                'type': 'end'
            })
            
            return {
                'type': 'waterfall',
                'title': 'Variance Waterfall Analysis',
                'subtitle': 'Cumulative impact of variances',
                'data': waterfall_data,
                'config': {
                    'xAxisKey': 'category',
                    'valueKey': 'value',
                    'cumulativeKey': 'cumulative',
                    'colorScale': 'waterfall'
                },
                'insights': [
                    f"Total variance: {cumulative - est_total:.2f}",
                    f"Variance percentage: {((cumulative - est_total) / est_total * 100):.1f}%" if est_total != 0 else "N/A"
                ]
            }
            
        except Exception as e:
            logger.error(f"Error creating waterfall chart: {str(e)}")
            return None
    
    def _categorize_variance_severity(self, variance: float) -> str:
        """Categorize variance severity for color coding."""
        abs_variance = abs(variance)
        if abs_variance <= 5:
            return 'low'
        elif abs_variance <= 15:
            return 'medium'
        elif abs_variance <= 25:
            return 'high'
        else:
            return 'critical'
    
    def _get_max_charts(self, analysis_level: str) -> int:
        """Get maximum number of charts based on analysis level."""
        if analysis_level == 'basic':
            return 3
        elif analysis_level == 'standard':
            return 6
        else:  # comprehensive
            return 10
    
    def _generate_fallback_charts(self, estimated_df: pd.DataFrame, actual_df: pd.DataFrame,
                                column_mapping: Dict[str, str]) -> List[Dict[str, Any]]:
        """Generate basic fallback charts when main generation fails."""
        try:
            charts = []
            
            # Simple variance chart
            variance_data = []
            for est_col, act_col in list(column_mapping.items())[:3]:
                if est_col in estimated_df.columns and act_col in actual_df.columns:
                    est_values = cast(pd.Series, pd.to_numeric(estimated_df[est_col], errors='coerce'))
                    act_values = cast(pd.Series, pd.to_numeric(actual_df[act_col], errors='coerce'))
                    
                    if est_values.notna().sum() > 0 and act_values.notna().sum() > 0:
                        est_sum = est_values.sum()
                        act_sum = act_values.sum()
                        
                        if abs(est_sum) > 0.001:
                            variance = ((act_sum - est_sum) / est_sum) * 100
                            variance_data.append({
                                'metric': est_col.replace('_', ' '),
                                'variance': round(variance, 2)
                            })
            
            if variance_data:
                charts.append({
                    'type': 'bar',
                    'title': 'Basic Variance Analysis',
                    'data': variance_data,
                    'config': {
                        'xAxisKey': 'metric',
                        'bars': [{'dataKey': 'variance', 'name': 'Variance %', 'fill': '#8884d8'}]
                    }
                })
            
            return charts
            
        except Exception as e:
            logger.error(f"Error generating fallback charts: {str(e)}")
            return [] 