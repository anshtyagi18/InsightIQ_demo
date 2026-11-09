"""
Dataset Interpretation Service for InsightIQ

Architecture:
1. Python/Pandas/SQL performs all data cleaning, calculations, and analytical profiling.
2. Only processed and structured statistical summaries are sent to Gemini.
3. Gemini generates the main dashboard Summary, Key Insights, Executive Business Insights,
   and recommends specific charts (with rationale on why each chart is useful).
4. Gemini does NOT create charts or perform calculations.
5. Python/Pandas takes Gemini's chart recommendations and calculates the exact data,
   labels, titles, legends, and Recharts formatting.
6. The Gemini API key is securely kept in backend environment variables.
"""

import os
import json
import logging
import re
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class DatasetInterpreterService:
    """Intelligent dataset interpretation service combining Pandas calculations with Gemini reasoning."""

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.model_name = "gemini-3.8-flash"

    def clean_and_calculate_statistics(self, df: pd.DataFrame, dataset_name: str = "Dataset") -> Dict[str, Any]:
        """
        Step 1: Python/Pandas cleans the dataset and computes all analytical statistics.
        Raw rows will NOT be sent to Gemini - only this compact calculated summary.
        """
        if df.empty:
            return {"error": "Dataset is empty"}

        # 1. Clean columns
        df_clean = df.copy()
        df_clean.columns = [str(c).strip() for c in df_clean.columns]

        total_rows = len(df_clean)
        total_cols = len(df_clean.columns)

        numeric_cols = []
        date_cols = []
        categorical_cols = []

        # Classify and clean data types
        for col in df_clean.columns:
            # Check if column looks like a date
            col_lower = str(col).lower()
            if any(k in col_lower for k in ['date', 'time', 'year', 'month', 'day', 'timestamp', 'period']):
                try:
                    df_clean[col] = pd.to_datetime(df_clean[col], errors='coerce')
                    if df_clean[col].notna().sum() > 0.3 * total_rows:
                        date_cols.append(col)
                        continue
                except Exception:
                    pass

            # Check if column is numeric or can be converted to numeric
            if pd.api.types.is_numeric_dtype(df_clean[col]):
                numeric_cols.append(col)
            else:
                # Try cleaning currency / percentage / thousand commas
                cleaned_series = (
                    df_clean[col]
                    .astype(str)
                    .str.replace(r'[\$,€,£,¥,%]', '', regex=True)
                    .str.replace(',', '')
                    .str.strip()
                )
                converted = pd.to_numeric(cleaned_series, errors='coerce')
                if converted.notna().sum() > 0.5 * total_rows and converted.nunique() > 2:
                    df_clean[col] = converted
                    numeric_cols.append(col)
                else:
                    categorical_cols.append(col)

        # Compute column-by-column descriptive statistics
        columns_profile = []
        numeric_summaries = {}
        for col in numeric_cols:
            series = df_clean[col].dropna()
            if len(series) == 0:
                continue
            col_sum = float(series.sum())
            col_mean = float(series.mean())
            col_median = float(series.median())
            col_min = float(series.min())
            col_max = float(series.max())
            col_std = float(series.std()) if len(series) > 1 else 0.0

            numeric_summaries[col] = {
                "sum": round(col_sum, 2),
                "mean": round(col_mean, 2),
                "median": round(col_median, 2),
                "min": round(col_min, 2),
                "max": round(col_max, 2),
                "std": round(col_std, 2),
                "non_null_count": int(len(series)),
                "null_count": int(total_rows - len(series)),
            }
            columns_profile.append({
                "column": col,
                "type": "numeric",
                **numeric_summaries[col]
            })

        categorical_summaries = {}
        for col in categorical_cols:
            series = df_clean[col].dropna().astype(str)
            if len(series) == 0:
                continue
            val_counts = series.value_counts()
            top_values = [
                {"value": str(val), "count": int(count), "percentage": round(float(count / total_rows * 100), 1)}
                for val, count in val_counts.head(5).items()
            ]
            categorical_summaries[col] = {
                "unique_count": int(series.nunique()),
                "top_values": top_values,
                "dominant_value": str(val_counts.index[0]) if len(val_counts) > 0 else "N/A",
                "dominant_percentage": round(float(val_counts.iloc[0] / total_rows * 100), 1) if len(val_counts) > 0 else 0,
            }
            columns_profile.append({
                "column": col,
                "type": "categorical",
                "unique_count": int(series.nunique()),
                "dominant_value": categorical_summaries[col]["dominant_value"],
            })

        # Calculate Bivariate aggregations: top numeric col by top categorical col
        aggregations = []
        if numeric_cols and categorical_cols:
            primary_num = numeric_cols[0]
            primary_cat = categorical_cols[0]
            grouped = df_clean.groupby(primary_cat)[primary_num].agg(['sum', 'mean', 'count']).reset_index()
            grouped = grouped.sort_values(by='sum', ascending=False).head(8)
            aggregations.append({
                "metric": primary_num,
                "dimension": primary_cat,
                "breakdown": [
                    {
                        "category": str(row[primary_cat]),
                        "sum": round(float(row['sum']), 2),
                        "mean": round(float(row['mean']), 2),
                        "count": int(row['count'])
                    }
                    for _, row in grouped.iterrows()
                ]
            })

        # Calculate Temporal Trends if date column exists
        temporal_trends = []
        if date_cols and numeric_cols:
            primary_date = date_cols[0]
            primary_num = numeric_cols[0]
            valid_dates = df_clean[[primary_date, primary_num]].dropna()
            if not valid_dates.empty:
                try:
                    valid_dates['period'] = valid_dates[primary_date].dt.to_period('M').astype(str)
                    time_agg = valid_dates.groupby('period')[primary_num].sum().reset_index()
                    time_agg = time_agg.sort_values('period').head(12)
                    temporal_trends = [
                        {"period": str(row['period']), "value": round(float(row[primary_num]), 2)}
                        for _, row in time_agg.iterrows()
                    ]
                except Exception as e:
                    logger.debug(f"Temporal aggregation error: {e}")

        # Calculate Correlations between numeric columns
        correlations = []
        if len(numeric_cols) >= 2:
            num_df = df_clean[numeric_cols].dropna()
            if len(num_df) > 3:
                corr_matrix = num_df.corr()
                for i in range(len(numeric_cols)):
                    for j in range(i + 1, len(numeric_cols)):
                        c1, c2 = numeric_cols[i], numeric_cols[j]
                        val = corr_matrix.loc[c1, c2]
                        if not np.isnan(val):
                            correlations.append({
                                "column_a": c1,
                                "column_b": c2,
                                "pearson_r": round(float(val), 3),
                                "strength": "strong" if abs(val) >= 0.7 else "moderate" if abs(val) >= 0.4 else "weak"
                            })

        return {
            "dataset_name": dataset_name,
            "total_rows": total_rows,
            "total_columns": total_cols,
            "numeric_columns": numeric_cols,
            "categorical_columns": categorical_cols,
            "date_columns": date_cols,
            "numeric_summaries": numeric_summaries,
            "categorical_summaries": categorical_summaries,
            "aggregations": aggregations,
            "temporal_trends": temporal_trends,
            "correlations": correlations,
            "calculated_at": datetime.utcnow().isoformat()
        }

    async def interpret_with_gemini(self, stats: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 2: Send ONLY the processed, structured statistical results to Gemini.
        Gemini generates:
          - Executive Summary (grounded in numbers)
          - Key Insights (factual observations)
          - Executive Business Insights (strategic themes & recommendations)
          - Structured Chart Recommendations (with 'why_useful')
        Gemini must NOT calculate numbers or create charts.
        """
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            logger.warning("GEMINI_API_KEY not configured, using deterministic fallback interpreter")
            return self._generate_rule_based_interpretation(stats)

        prompt = f"""
You are the Chief Data Scientist & Executive Business Advisor for InsightIQ.
You have been provided with PRE-CALCULATED, verified statistical results from a Python/Pandas analytics engine.

CRITICAL RULES:
1. All calculations, numbers, sums, averages, and groupings have ALREADY been accurately computed by Python/Pandas.
2. DO NOT perform any math or calculations yourself.
3. DO NOT output chart SVG, HTML, or raw chart code.
4. GROUND ALL INSIGHTS STRICTLY in the provided statistics. Never invent numbers.
5. Identify which specific charts are most valuable for this dataset and explain WHY each chart is useful.
6. Return ONLY a valid JSON object with the exact keys specified below.

PRE-CALCULATED DATASET STATISTICS:
{json.dumps(stats, indent=2)}

OUTPUT JSON SCHEMA:
{{
  "executive_summary": "2-3 crisp sentences providing the executive narrative of the dataset, quoting total rows ({stats.get('total_rows')}) and primary metric totals/averages.",
  "key_insights": [
    {{
      "title": "Short title",
      "observation": "Factual observation citing actual calculated figures from the data",
      "metric_reference": "Column or metric name",
      "impact": "positive | neutral | negative"
    }}
  ],
  "executive_business_insights": [
    {{
      "strategic_theme": "e.g., Resource Allocation, Category Concentration, or Growth Dynamics",
      "finding": "Business finding directly supported by the calculated statistics",
      "actionable_recommendation": "Concrete operational recommendation based on the numbers",
      "priority": "high | medium | low"
    }}
  ],
  "recommended_charts": [
    {{
      "id": "chart_1",
      "chart_type": "bar | line | area | pie | scatter",
      "title": "Clear business chart title",
      "description": "What this chart visualizes",
      "metric_column": "Exact numeric column name from numeric_columns list",
      "dimension_column": "Exact categorical or date column from columns list",
      "aggregation": "sum | mean | count",
      "why_useful": "Specific rationale explaining why this visualization uncovers a key business pattern in this dataset"
    }}
  ]
}}
"""
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(
                self.model_name,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.2,
                    max_output_tokens=2048,
                    response_mime_type="application/json"
                )
            )
            response = model.generate_content(prompt)
            text = response.text if response and hasattr(response, 'text') else ""
            
            clean_text = text.strip()
            if clean_text.startswith("```json"):
                clean_text = clean_text[7:]
            if clean_text.endswith("```"):
                clean_text = clean_text[:-3]
            clean_text = clean_text.strip()
            
            result = json.loads(clean_text)
            result["model_used"] = self.model_name
            result["source"] = "gemini-ai"
            return result
        except Exception as e:
            logger.error(f"Gemini interpretation failed: {e}. Falling back to rule-based engine.")
            fallback = self._generate_rule_based_interpretation(stats)
            fallback["gemini_error"] = str(e)
            return fallback

    def generate_recommended_charts(self, df: pd.DataFrame, recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Step 3: Python/Pandas takes Gemini's chart recommendations and calculates the exact
        chart datasets, formatted values, titles, legends, and Recharts configuration.
        """
        generated_charts = []
        if df.empty or not recommendations:
            return generated_charts

        # Clean column names
        df_clean = df.copy()
        df_clean.columns = [str(c).strip() for c in df_clean.columns]

        color_palette = ["#3b82f6", "#10b981", "#8b5cf6", "#f59e0b", "#06b6d4", "#ec4899", "#6366f1"]

        for idx, rec in enumerate(recommendations):
            try:
                chart_id = rec.get("id") or f"chart_{idx + 1}"
                chart_type = rec.get("chart_type", "bar").lower()
                metric_col = rec.get("metric_column")
                dim_col = rec.get("dimension_column")
                agg_func = rec.get("aggregation", "sum").lower()
                why_useful = rec.get("why_useful", "Provides essential business visibility.")
                title = rec.get("title", f"{metric_col} by {dim_col}")
                description = rec.get("description", f"Distribution of {metric_col} across {dim_col}")

                # Ensure columns exist in dataset
                if not metric_col or metric_col not in df_clean.columns:
                    # Fallback to first numeric column
                    numeric_cols = df_clean.select_dtypes(include=[np.number]).columns.tolist()
                    if not numeric_cols:
                        continue
                    metric_col = numeric_cols[0]

                if not dim_col or dim_col not in df_clean.columns:
                    cat_cols = df_clean.select_dtypes(exclude=[np.number]).columns.tolist()
                    if not cat_cols:
                        continue
                    dim_col = cat_cols[0]

                # Convert numeric column
                df_clean[metric_col] = pd.to_numeric(df_clean[metric_col], errors='coerce').fillna(0)

                # Aggregate with Pandas
                if agg_func == 'mean':
                    grouped = df_clean.groupby(dim_col)[metric_col].mean()
                elif agg_func == 'count':
                    grouped = df_clean.groupby(dim_col)[metric_col].count()
                else:
                    grouped = df_clean.groupby(dim_col)[metric_col].sum()

                # Sort and take top items
                if chart_type in ['line', 'area'] and any(k in str(dim_col).lower() for k in ['date', 'time', 'period', 'month']):
                    # Chronological sort for dates
                    grouped = grouped.sort_index().head(15)
                else:
                    grouped = grouped.sort_values(ascending=False).head(10)

                chart_data = [
                    {
                        dim_col: str(category),
                        metric_col: round(float(val), 2),
                        "name": str(category),
                        "value": round(float(val), 2),
                        "formatted_value": f"${round(float(val), 2):,}" if any(k in metric_col.lower() for k in ['revenue', 'sales', 'cost', 'price', 'profit', 'amount']) else f"{round(float(val), 2):,}"
                    }
                    for category, val in grouped.items()
                ]

                primary_color = color_palette[idx % len(color_palette)]

                generated_charts.append({
                    "id": chart_id,
                    "title": title,
                    "description": description,
                    "why_useful": why_useful,
                    "chart_type": chart_type,
                    "metric_column": metric_col,
                    "dimension_column": dim_col,
                    "aggregation": agg_func,
                    "data": chart_data,
                    "data_columns": [dim_col, metric_col],
                    "color": primary_color,
                    "recharts_config": {
                        "type": chart_type.capitalize() + "Chart",
                        "dataKey": metric_col,
                        "xAxisKey": dim_col,
                        "fill": primary_color,
                        "stroke": primary_color,
                        "strokeWidth": 2,
                        "height": 320
                    }
                })
            except Exception as e:
                logger.error(f"Error generating recommended chart {rec}: {e}")

        return generated_charts

    async def process_dataset(self, df: pd.DataFrame, dataset_name: str = "Dataset") -> Dict[str, Any]:
        """
        Complete end-to-end pipeline:
        1. Python/Pandas calculates statistics and summaries.
        2. Sends pre-computed statistics to Gemini for intelligent interpretation and chart recommendations.
        3. Python/Pandas builds the exact recommended charts.
        """
        # Step 1: Calculations in Pandas
        stats = self.clean_and_calculate_statistics(df, dataset_name)
        if "error" in stats:
            return {"status": "error", "message": stats["error"]}

        # Step 2: Gemini generates summary, insights, and recommendations
        interpretation = await self.interpret_with_gemini(stats)

        # Step 3: Python/Pandas generates the recommended charts
        recommendations = interpretation.get("recommended_charts", [])
        charts = self.generate_recommended_charts(df, recommendations)

        return {
            "status": "success",
            "dataset_name": dataset_name,
            "dataset_summary": {
                "total_rows": stats["total_rows"],
                "total_columns": stats["total_columns"],
                "numeric_columns": stats["numeric_columns"],
                "categorical_columns": stats["categorical_columns"],
                "date_columns": stats["date_columns"],
                "primary_metric": stats["numeric_columns"][0] if stats["numeric_columns"] else None,
                "primary_dimension": stats["categorical_columns"][0] if stats["categorical_columns"] else None,
            },
            "calculated_metrics": stats["numeric_summaries"],
            "aggregations": stats["aggregations"],
            "temporal_trends": stats["temporal_trends"],
            "correlations": stats["correlations"],
            "ai_interpretation": {
                "executive_summary": interpretation.get("executive_summary"),
                "key_insights": interpretation.get("key_insights", []),
                "executive_business_insights": interpretation.get("executive_business_insights", []),
                "model_used": interpretation.get("model_used", self.model_name),
                "source": interpretation.get("source", "gemini-ai")
            },
            "charts": charts
        }

    def _generate_rule_based_interpretation(self, stats: Dict[str, Any]) -> Dict[str, Any]:
        """Deterministic factual interpretation generator when Gemini is not connected."""
        total_rows = stats.get("total_rows", 0)
        num_cols = stats.get("numeric_columns", [])
        cat_cols = stats.get("categorical_columns", [])
        date_cols = stats.get("date_columns", [])
        num_sums = stats.get("numeric_summaries", {})
        cat_sums = stats.get("categorical_summaries", {})

        primary_metric = num_cols[0] if num_cols else "Value"
        primary_metric_data = num_sums.get(primary_metric, {})
        primary_sum = primary_metric_data.get("sum", 0)
        primary_mean = primary_metric_data.get("mean", 0)

        primary_dim = cat_cols[0] if cat_cols else "Category"
        dominant_cat = cat_sums.get(primary_dim, {}).get("dominant_value", "Top Segment")
        dominant_pct = cat_sums.get(primary_dim, {}).get("dominant_percentage", 0)

        summary = (
            f"The dataset comprises {total_rows:,} records across {stats.get('total_columns', 0)} attributes. "
            f"Primary quantitative tracking in {primary_metric} totals ${primary_sum:,.2f} with an average of "
            f"${primary_mean:,.2f} per observation. Volume concentration is led by {primary_dim} ({dominant_cat} at {dominant_pct}%)."
        )

        key_insights = [
            {
                "title": f"Primary Metric Volume ({primary_metric})",
                "observation": f"Aggregate {primary_metric} reached ${primary_sum:,.2f} across {total_rows:,} entries.",
                "metric_reference": primary_metric,
                "impact": "positive"
            },
            {
                "title": f"Category Distribution in {primary_dim}",
                "observation": f"{dominant_cat} represents the highest activity share with {dominant_pct}% of total records.",
                "metric_reference": primary_dim,
                "impact": "neutral"
            },
            {
                "title": "Baseline Performance Benchmark",
                "observation": f"The statistical mean of {primary_metric} is ${primary_mean:,.2f} with a median of ${primary_metric_data.get('median', 0):,.2f}.",
                "metric_reference": primary_metric,
                "impact": "neutral"
            }
        ]

        executive_business_insights = [
            {
                "strategic_theme": "Concentration & Market Share",
                "finding": f"Significant throughput is concentrated within {dominant_cat} ({dominant_pct}% volume).",
                "actionable_recommendation": f"Optimize supply and inventory planning around top-performing {primary_dim} segments while diversifying lower-volume categories.",
                "priority": "high"
            },
            {
                "strategic_theme": "Variance & Yield Optimization",
                "finding": f"Mean {primary_metric} (${primary_mean:,.2f}) reflects solid baseline stability.",
                "actionable_recommendation": "Establish automated threshold alerts for transactions deviating beyond standard standard-deviation boundaries.",
                "priority": "medium"
            }
        ]

        recommended_charts = []
        if num_cols and cat_cols:
            recommended_charts.append({
                "id": "chart_1",
                "chart_type": "bar",
                "title": f"{primary_metric} by {primary_dim}",
                "description": f"Compares aggregate {primary_metric} across key {primary_dim} categories",
                "metric_column": primary_metric,
                "dimension_column": primary_dim,
                "aggregation": "sum",
                "why_useful": f"Identifies primary operational contributors and volume skew across {primary_dim} segments."
            })

        if len(num_cols) >= 2 and cat_cols:
            second_metric = num_cols[1]
            recommended_charts.append({
                "id": "chart_2",
                "chart_type": "bar",
                "title": f"Average {second_metric} by {primary_dim}",
                "description": f"Analyzes unit performance of {second_metric}",
                "metric_column": second_metric,
                "dimension_column": primary_dim,
                "aggregation": "mean",
                "why_useful": f"Evaluates categorical efficiency to ensure top volume drivers are also high-yield."
            })

        if date_cols and num_cols:
            recommended_charts.append({
                "id": "chart_3",
                "chart_type": "area",
                "title": f"{primary_metric} Over Time",
                "description": f"Chronological trend of {primary_metric}",
                "metric_column": primary_metric,
                "dimension_column": date_cols[0],
                "aggregation": "sum",
                "why_useful": "Reveals seasonality, operational momentum, and cyclical peak/trough periods."
            })

        return {
            "executive_summary": summary,
            "key_insights": key_insights,
            "executive_business_insights": executive_business_insights,
            "recommended_charts": recommended_charts,
            "model_used": "insightiq-statistical-engine",
            "source": "rules-engine"
        }

dataset_interpreter = DatasetInterpreterService()
