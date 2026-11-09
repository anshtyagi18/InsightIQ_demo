"""
AI-Powered Comparison Engine

This module provides intelligent comparison analysis using AI/LLM capabilities
instead of traditional rule-based logic. It can adapt to various data types,
formats, and business contexts automatically.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, cast
import logging
import json
from dataclasses import dataclass
from datetime import datetime

from src.services.litellm_service import LiteLLMService

logger = logging.getLogger(__name__)

@dataclass
class AIAnalysisResult:
    """Result from AI-powered analysis."""
    analysis_type: str
    confidence_score: float
    insights: List[Dict[str, Any]]
    metrics: Dict[str, Any]
    recommendations: List[str]
    data_quality_assessment: Dict[str, Any]

class AIComparisonEngine:
    """
    AI-powered comparison engine that uses LLM for intelligent analysis.
    Adapts to various data types and business contexts automatically.
    """
    
    def __init__(self):
        self.llm_service = LiteLLMService()
        self.analysis_cache = {}
        
    async def analyze_data_context(self, estimated_df: pd.DataFrame, actual_df: pd.DataFrame) -> Dict[str, Any]:
        """Use AI to understand the business context and data characteristics."""
        try:
            # Prepare data summary for AI analysis
            data_summary = self._prepare_data_summary(estimated_df, actual_df)
            
            prompt = f"""
Analyze this dataset comparison context and provide intelligent insights:

Dataset Summary:
{json.dumps(data_summary, indent=2)}

Please analyze and provide:
1. Business domain/context (finance, sales, marketing, operations, etc.)
2. Data characteristics and quality assessment
3. Key metrics that should be prioritized for analysis
4. Potential data issues or anomalies to watch for
5. Recommended analysis approach based on the data structure
6. Expected variance thresholds for this type of data

Respond with structured JSON containing your analysis.
"""

            response_format = {
                "business_domain": "string",
                "data_quality_score": "number (0-100)",
                "key_metrics": ["list of important metrics"],
                "analysis_approach": "string",
                "variance_thresholds": {
                    "critical": "number",
                    "significant": "number", 
                    "acceptable": "number"
                },
                "potential_issues": ["list of potential data issues"],
                "confidence": "number (0-100)"
            }
            
            if not self.llm_service.is_available():
                return self._fallback_context_analysis(estimated_df, actual_df)
            
            ai_response = await self.llm_service.generate_structured_response(
                prompt=prompt,
                response_format=response_format
            )
            
            if ai_response.error:
                logger.warning(f"AI context analysis failed: {ai_response.error}")
                return self._fallback_context_analysis(estimated_df, actual_df)
            
            try:
                context = json.loads(ai_response.content)
                logger.info(f"[AI_ENGINE] Identified business domain: {context.get('business_domain', 'unknown')}")
                return context
            except json.JSONDecodeError:
                logger.warning("Failed to parse AI context analysis response")
                return self._fallback_context_analysis(estimated_df, actual_df)
                
        except Exception as e:
            logger.error(f"Error in AI context analysis: {str(e)}")
            return self._fallback_context_analysis(estimated_df, actual_df)
    
    async def intelligent_column_mapping(self, estimated_df: pd.DataFrame, actual_df: pd.DataFrame) -> Dict[str, str]:
        """Use AI to intelligently map columns between datasets."""
        try:
            est_columns = list(estimated_df.columns)
            act_columns = list(actual_df.columns)
            
            # Sample data for context
            est_sample = estimated_df.head(3).to_dict('records')
            act_sample = actual_df.head(3).to_dict('records')
            
            prompt = f"""
Intelligently map columns between estimated and actual datasets:

Estimated Dataset Columns: {est_columns}
Estimated Sample Data: {json.dumps(est_sample, default=str)}

Actual Dataset Columns: {act_columns}  
Actual Sample Data: {json.dumps(act_sample, default=str)}

Create intelligent column mappings considering:
1. Semantic similarity (e.g., "Sales_Forecast" -> "Actual_Sales")
2. Business logic (e.g., "Revenue_Est" -> "Revenue_Actual")
3. Data type compatibility
4. Column content patterns

Provide mappings as JSON object where keys are estimated columns and values are actual columns.
Only map columns that have clear semantic relationships.
"""

            response_format = {
                "column_mappings": {"estimated_column": "actual_column"},
                "confidence_scores": {"estimated_column": "number (0-100)"},
                "unmapped_estimated": ["list of unmapped estimated columns"],
                "unmapped_actual": ["list of unmapped actual columns"]
            }
            
            if not self.llm_service.is_available():
                return self._fallback_column_mapping(estimated_df, actual_df)
            
            ai_response = await self.llm_service.generate_structured_response(
                prompt=prompt,
                response_format=response_format
            )
            
            if ai_response.error:
                logger.warning(f"AI column mapping failed: {ai_response.error}")
                return self._fallback_column_mapping(estimated_df, actual_df)
            
            try:
                mapping_result = json.loads(ai_response.content)
                column_mappings = mapping_result.get('column_mappings', {})
                logger.info(f"[AI_ENGINE] Mapped {len(column_mappings)} column pairs using AI")
                return column_mappings
            except json.JSONDecodeError:
                logger.warning("Failed to parse AI column mapping response")
                return self._fallback_column_mapping(estimated_df, actual_df)
                
        except Exception as e:
            logger.error(f"Error in AI column mapping: {str(e)}")
            return self._fallback_column_mapping(estimated_df, actual_df)
    
    async def ai_variance_analysis(self, estimated_df: pd.DataFrame, actual_df: pd.DataFrame, 
                                 column_mapping: Dict[str, str], context: Dict[str, Any]) -> AIAnalysisResult:
        """AI-powered variance analysis with business context understanding."""
        try:
            # Calculate basic statistics
            variance_stats = self._calculate_variance_statistics(estimated_df, actual_df, column_mapping)
            
            prompt = f"""
Perform intelligent variance analysis with business context:

Business Context: {context.get('business_domain', 'general')}
Variance Statistics: {json.dumps(variance_stats, default=str)}
Expected Thresholds: {context.get('variance_thresholds', {})}

Analyze the variance patterns and provide:
1. Business impact assessment for each variance
2. Root cause hypotheses based on the data patterns
3. Severity classification considering business context
4. Actionable insights and recommendations
5. Trend analysis and predictions

Focus on business value rather than just statistical measures.
"""

            response_format = {
                "overall_assessment": "string",
                "critical_variances": [{"metric": "string", "variance": "number", "impact": "string", "severity": "string"}],
                "business_insights": ["list of business insights"],
                "root_causes": ["list of potential root causes"],
                "recommendations": ["list of actionable recommendations"],
                "confidence": "number (0-100)"
            }
            
            if not self.llm_service.is_available():
                return self._fallback_variance_analysis(variance_stats)
            
            ai_response = await self.llm_service.generate_structured_response(
                prompt=prompt,
                response_format=response_format
            )
            
            if ai_response.error:
                logger.warning(f"AI variance analysis failed: {ai_response.error}")
                return self._fallback_variance_analysis(variance_stats)
            
            try:
                analysis = json.loads(ai_response.content)
                return AIAnalysisResult(
                    analysis_type="variance",
                    confidence_score=analysis.get('confidence', 75) / 100,
                    insights=[{"title": "AI Variance Analysis", "description": analysis.get('overall_assessment', '')}],
                    metrics=variance_stats,
                    recommendations=analysis.get('recommendations', []),
                    data_quality_assessment={"variance_quality": "good"}
                )
            except json.JSONDecodeError:
                logger.warning("Failed to parse AI variance analysis response")
                return self._fallback_variance_analysis(variance_stats)
                
        except Exception as e:
            logger.error(f"Error in AI variance analysis: {str(e)}")
            return self._fallback_variance_analysis({})
    
    async def ai_trend_analysis(self, estimated_df: pd.DataFrame, actual_df: pd.DataFrame,
                              column_mapping: Dict[str, str], context: Dict[str, Any]) -> AIAnalysisResult:
        """AI-powered trend analysis with pattern recognition."""
        try:
            # Calculate trend statistics
            trend_stats = self._calculate_trend_statistics(estimated_df, actual_df, column_mapping)
            
            prompt = f"""
Perform intelligent trend analysis with pattern recognition:

Business Context: {context.get('business_domain', 'general')}
Trend Statistics: {json.dumps(trend_stats, default=str)}

Analyze the trend patterns and provide:
1. Trend alignment assessment between estimated and actual
2. Seasonal or cyclical pattern detection
3. Anomaly identification and explanation
4. Forecasting accuracy evaluation
5. Business implications of trend deviations

Focus on actionable business insights from trend patterns.
"""

            response_format = {
                "trend_alignment": "string (strong/moderate/weak/poor)",
                "pattern_insights": ["list of pattern insights"],
                "anomalies": [{"period": "string", "description": "string", "impact": "string"}],
                "forecasting_assessment": "string",
                "business_implications": ["list of business implications"],
                "confidence": "number (0-100)"
            }
            
            if not self.llm_service.is_available():
                return self._fallback_trend_analysis(trend_stats)
            
            ai_response = await self.llm_service.generate_structured_response(
                prompt=prompt,
                response_format=response_format
            )
            
            if ai_response.error:
                logger.warning(f"AI trend analysis failed: {ai_response.error}")
                return self._fallback_trend_analysis(trend_stats)
            
            try:
                analysis = json.loads(ai_response.content)
                return AIAnalysisResult(
                    analysis_type="trend",
                    confidence_score=analysis.get('confidence', 75) / 100,
                    insights=analysis.get('pattern_insights', []),
                    metrics=trend_stats,
                    recommendations=analysis.get('business_implications', []),
                    data_quality_assessment={"trend_quality": analysis.get('trend_alignment', 'moderate')}
                )
            except json.JSONDecodeError:
                logger.warning("Failed to parse AI trend analysis response")
                return self._fallback_trend_analysis(trend_stats)
                
        except Exception as e:
            logger.error(f"Error in AI trend analysis: {str(e)}")
            return self._fallback_trend_analysis({})
    
    def _prepare_data_summary(self, estimated_df: pd.DataFrame, actual_df: pd.DataFrame) -> Dict[str, Any]:
        """Prepare a comprehensive data summary for AI analysis."""
        return {
            "estimated_shape": estimated_df.shape,
            "actual_shape": actual_df.shape,
            "estimated_columns": list(estimated_df.columns),
            "actual_columns": list(actual_df.columns),
            "estimated_dtypes": estimated_df.dtypes.to_dict(),
            "actual_dtypes": actual_df.dtypes.to_dict(),
            "estimated_sample": estimated_df.head(2).to_dict('records'),
            "actual_sample": actual_df.head(2).to_dict('records'),
            "numeric_columns_est": len(estimated_df.select_dtypes(include=[np.number]).columns),
            "numeric_columns_act": len(actual_df.select_dtypes(include=[np.number]).columns),
            "data_density_est": estimated_df.count().sum() / (estimated_df.shape[0] * estimated_df.shape[1]),
            "data_density_act": actual_df.count().sum() / (actual_df.shape[0] * actual_df.shape[1])
        }
    
    def _calculate_variance_statistics(self, estimated_df: pd.DataFrame, actual_df: pd.DataFrame, 
                                     column_mapping: Dict[str, str]) -> Dict[str, Any]:
        """Calculate comprehensive variance statistics."""
        stats = {"metrics": [], "overall_variance": 0, "total_analyzed": 0}
        
        total_variance = 0
        analyzed_count = 0
        
        for est_col, act_col in column_mapping.items():
            if est_col in estimated_df.columns and act_col in actual_df.columns:
                try:
                    est_values = cast(pd.Series, pd.to_numeric(estimated_df[est_col], errors='coerce'))
                    act_values = cast(pd.Series, pd.to_numeric(actual_df[act_col], errors='coerce'))
                    
                    if est_values.notna().sum() > 0 and act_values.notna().sum() > 0:
                        est_sum = est_values.sum()
                        act_sum = act_values.sum()
                        
                        if abs(est_sum) > 0.001:
                            variance = ((act_sum - est_sum) / est_sum) * 100
                            total_variance += abs(variance)
                            analyzed_count += 1
                            
                            stats["metrics"].append({
                                "metric": f"{est_col} vs {act_col}",
                                "estimated_total": float(est_sum),
                                "actual_total": float(act_sum),
                                "variance_percentage": float(variance),
                                "data_points": int(est_values.notna().sum())
                            })
                except Exception as e:
                    logger.warning(f"Error calculating variance for {est_col}: {str(e)}")
        
        stats["overall_variance"] = total_variance / analyzed_count if analyzed_count > 0 else 0
        stats["total_analyzed"] = analyzed_count
        return stats
    
    def _calculate_trend_statistics(self, estimated_df: pd.DataFrame, actual_df: pd.DataFrame,
                                  column_mapping: Dict[str, str]) -> Dict[str, Any]:
        """Calculate comprehensive trend statistics."""
        stats = {"correlations": [], "trend_strength": 0, "total_analyzed": 0}
        
        correlations = []
        
        for est_col, act_col in column_mapping.items():
            if est_col in estimated_df.columns and act_col in actual_df.columns:
                try:
                    est_values = cast(pd.Series, pd.to_numeric(estimated_df[est_col], errors='coerce')).dropna()
                    act_values = cast(pd.Series, pd.to_numeric(actual_df[act_col], errors='coerce')).dropna()
                    
                    if len(est_values) >= 3 and len(act_values) >= 3:
                        min_len = min(len(est_values), len(act_values))
                        correlation = np.corrcoef(est_values[:min_len], act_values[:min_len])[0, 1]
                        
                        if not np.isnan(correlation):
                            correlations.append(correlation)
                            stats["correlations"].append({
                                "metric": f"{est_col} vs {act_col}",
                                "correlation": float(correlation),
                                "data_points": min_len
                            })
                except Exception as e:
                    logger.warning(f"Error calculating trend for {est_col}: {str(e)}")
        
        stats["trend_strength"] = np.mean(correlations) if correlations else 0
        stats["total_analyzed"] = len(correlations)
        return stats
    
    def _fallback_context_analysis(self, estimated_df: pd.DataFrame, actual_df: pd.DataFrame) -> Dict[str, Any]:
        """Fallback context analysis when AI is not available."""
        return {
            "business_domain": "general",
            "data_quality_score": 75,
            "key_metrics": list(estimated_df.select_dtypes(include=[np.number]).columns)[:5],
            "analysis_approach": "standard statistical analysis",
            "variance_thresholds": {"critical": 25, "significant": 15, "acceptable": 5},
            "potential_issues": ["Data quality should be verified"],
            "confidence": 60
        }
    
    def _fallback_column_mapping(self, estimated_df: pd.DataFrame, actual_df: pd.DataFrame) -> Dict[str, str]:
        """Fallback column mapping using simple string similarity."""
        mapping = {}
        est_cols = list(estimated_df.columns)
        act_cols = list(actual_df.columns)
        
        for est_col in est_cols:
            best_match = None
            best_score = 0
            
            for act_col in act_cols:
                # Simple similarity based on common words
                est_words = set(est_col.lower().replace('_', ' ').split())
                act_words = set(act_col.lower().replace('_', ' ').split())
                
                if est_words & act_words:  # If there are common words
                    score = len(est_words & act_words) / len(est_words | act_words)
                    if score > best_score and score > 0.3:
                        best_score = score
                        best_match = act_col
            
            if best_match:
                mapping[est_col] = best_match
        
        return mapping
    
    def _fallback_variance_analysis(self, variance_stats: Dict[str, Any]) -> AIAnalysisResult:
        """Fallback variance analysis when AI is not available."""
        return AIAnalysisResult(
            analysis_type="variance",
            confidence_score=0.6,
            insights=[{"title": "Basic Variance Analysis", "description": "Statistical variance analysis completed"}],
            metrics=variance_stats,
            recommendations=["Review high variance metrics", "Investigate data quality"],
            data_quality_assessment={"variance_quality": "moderate"}
        )
    
    def _fallback_trend_analysis(self, trend_stats: Dict[str, Any]) -> AIAnalysisResult:
        """Fallback trend analysis when AI is not available."""
        return AIAnalysisResult(
            analysis_type="trend",
            confidence_score=0.6,
            insights=[{"title": "Basic Trend Analysis", "description": "Basic trend correlation analysis completed"}],
            metrics=trend_stats,
            recommendations=["Monitor trend patterns", "Improve forecasting accuracy"],
            data_quality_assessment={"trend_quality": "moderate"}
        ) 