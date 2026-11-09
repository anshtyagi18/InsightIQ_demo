#!/usr/bin/env python3
"""
Question-Driven Chart Engine for InsightIQ.

Performs core calculations and chart data preparation using Python and pandas:
- Parses user questions against dataset schema.
- Identifies required metrics, dimensions, filters, and sub-questions.
- Computes aggregations, rankings, peak/trough analyses, trends, and growth rates.
- Automatically selects the best chart type (bar, line, area, pie, etc.).
- Prepares complete chart configurations with clear titles, axis labels, legends, and data labels.
- Provides factual calculated metrics for downstream AI interpretation.
"""

import sys
import json
import argparse
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np

def convert_to_json_serializable(obj):
    """Recursively convert numpy/pandas types to standard JSON-serializable types."""
    if obj is None:
        return None
    if isinstance(obj, (bool, np.bool_)):
        return bool(obj)
    if isinstance(obj, (int, np.integer)):
        return int(obj)
    if isinstance(obj, (float, np.floating)):
        if np.isnan(obj) or np.isinf(obj):
            return None
        return round(float(obj), 4)
    if isinstance(obj, (pd.Timestamp, datetime, np.datetime64)):
        try:
            return pd.Timestamp(obj).strftime('%Y-%m-%d')
        except Exception:
            return str(obj)
    if isinstance(obj, pd.Series):
        return [convert_to_json_serializable(v) for v in obj.tolist()]
    if isinstance(obj, pd.DataFrame):
        return [convert_to_json_serializable(r) for r in obj.to_dict('records')]
    if isinstance(obj, (list, tuple)):
        return [convert_to_json_serializable(v) for v in obj]
    if isinstance(obj, dict):
        return {str(k): convert_to_json_serializable(v) for k, v in obj.items()}
    return str(obj)


class QuestionChartEngine:
    """Analyzes questions, computes exact aggregations, and builds targeted chart configs."""

    def __init__(self, data: List[Dict[str, Any]], dataset_name: str = "Dataset"):
        self.raw_data = data
        self.dataset_name = dataset_name
        self.df = pd.DataFrame(data)
        self._normalize_dataset()

    def _normalize_dataset(self):
        """Clean and type-infer the dataframe for analytical grouping and date operations."""
        if self.df.empty:
            return

        # Strip whitespace from string columns
        for col in self.df.columns:
            if self.df[col].dtype == 'object':
                self.df[col] = self.df[col].apply(lambda x: x.strip() if isinstance(x, str) else x)

        # Detect and convert numeric columns
        self.numeric_cols = []
        self.date_cols = []
        self.categorical_cols = []

        for col in self.df.columns:
            # Check if numeric
            converted_numeric = pd.to_numeric(self.df[col], errors='coerce')
            non_null_original = self.df[col].dropna()
            non_null_numeric = converted_numeric.dropna()

            if len(non_null_original) > 0 and len(non_null_numeric) / len(non_null_original) > 0.7:
                self.df[col] = converted_numeric
                self.numeric_cols.append(col)
                continue

            # Check if date
            is_date_col = False
            col_lower = str(col).lower()
            if any(k in col_lower for k in ['date', 'time', 'created', 'order', 'day', 'month', 'year', 'period']):
                try:
                    converted_date = pd.to_datetime(self.df[col], errors='coerce')
                    if converted_date.dropna().count() / max(1, len(non_null_original)) > 0.6:
                        self.df[f"_dt_{col}"] = converted_date
                        self.date_cols.append(col)
                        is_date_col = True
                except Exception:
                    pass

            if not is_date_col:
                self.categorical_cols.append(col)

        # Add calendar helper columns if date column found
        if self.date_cols:
            primary_dt_col = f"_dt_{self.date_cols[0]}"
            self.df['_year'] = self.df[primary_dt_col].dt.year
            self.df['_month_name'] = self.df[primary_dt_col].dt.month_name()
            self.df['_month_num'] = self.df[primary_dt_col].dt.month
            self.df['_year_month'] = self.df[primary_dt_col].dt.strftime('%b %Y')
            self.df['_quarter'] = 'Q' + self.df[primary_dt_col].dt.quarter.astype(str) + ' ' + self.df['_year'].astype(str)

    def _match_column(self, term: str, candidates: List[str]) -> Optional[str]:
        """Fuzzy/token match a term from query to candidate columns."""
        term_clean = re.sub(r'[^a-zA-Z0-9]', '', term.lower())
        if not term_clean:
            return None

        # Exact match
        for c in candidates:
            c_clean = re.sub(r'[^a-zA-Z0-9]', '', c.lower())
            if term_clean == c_clean:
                return c

        # Substring match
        for c in candidates:
            c_clean = re.sub(r'[^a-zA-Z0-9]', '', c.lower())
            if term_clean in c_clean or c_clean in term_clean:
                return c

        # Common business synonyms
        synonyms = {
            'sales': ['revenue', 'amount', 'order_amount', 'sales', 'turnover', 'gross_sales', 'total'],
            'revenue': ['sales', 'amount', 'order_amount', 'revenue', 'turnover', 'total'],
            'profit': ['margin', 'net_income', 'profit', 'earnings', 'net_profit'],
            'units': ['quantity', 'volume', 'count', 'items', 'units'],
            'cost': ['expense', 'spending', 'fee', 'cost', 'shipping_fee'],
            'region': ['territory', 'location', 'area', 'country', 'state', 'region'],
            'category': ['product_group', 'department', 'type', 'segment', 'category'],
            'customer': ['client', 'account', 'customer_segment', 'buyer', 'user'],
            'rep': ['sales_rep', 'agent', 'employee', 'owner', 'representative']
        }

        for syn_key, syn_list in synonyms.items():
            if term_clean == syn_key or term_clean in syn_list:
                for c in candidates:
                    c_clean = re.sub(r'[^a-zA-Z0-9]', '', c.lower())
                    if any(s in c_clean for s in syn_list):
                        return c

        return None

    def analyze_question(self, question: str) -> Dict[str, Any]:
        """Core analytical pipeline: parse question, compute stats, and generate targeted charts."""
        q_lower = question.lower().strip()

        # 1. Identify Target Metric
        target_metric = None
        for word in ['sales', 'revenue', 'profit', 'margin', 'discount', 'cost', 'amount', 'quantity', 'units', 'fee', 'order_amount', 'price']:
            if word in q_lower:
                matched = self._match_column(word, self.numeric_cols)
                if matched:
                    target_metric = matched
                    break

        if not target_metric and self.numeric_cols:
            # Default to first prominent numeric column (e.g. Revenue, Sales, or Order_Amount)
            pref = ['revenue', 'sales', 'amount', 'profit', 'total']
            for p in pref:
                matched = self._match_column(p, self.numeric_cols)
                if matched:
                    target_metric = matched
                    break
            if not target_metric:
                target_metric = self.numeric_cols[0]

        # 2. Identify Temporal Dimensions
        has_year = any(w in q_lower for w in ['year', 'annual', 'yearly', 'annually', 'yoy'])
        has_month = any(w in q_lower for w in ['month', 'monthly', 'highest month', 'which month', 'best month'])
        has_quarter = any(w in q_lower for w in ['quarter', 'quarterly', 'q1', 'q2', 'q3', 'q4'])
        has_date = any(w in q_lower for w in ['date', 'day', 'daily', 'over time', 'trend'])

        # 3. Identify Categorical Dimensions
        target_dimension = None
        for col in self.categorical_cols:
            col_words = re.sub(r'[^a-zA-Z0-9 ]', ' ', col.lower()).split()
            if any(w in q_lower for w in col_words if len(w) > 2):
                target_dimension = col
                break

        if not target_dimension:
            # Check for general business dimension keywords
            for kw in ['category', 'region', 'product', 'channel', 'segment', 'customer', 'country', 'rep', 'status', 'brand']:
                if kw in q_lower:
                    matched = self._match_column(kw, self.categorical_cols)
                    if matched:
                        target_dimension = matched
                        break

        # 4. Detect Specific Sub-questions & Questions Intent
        is_highest_query = any(w in q_lower for w in ['highest', 'best', 'top', 'maximum', 'max', 'peak'])
        is_lowest_query = any(w in q_lower for w in ['lowest', 'worst', 'minimum', 'min', 'trough'])
        is_comparison = any(w in q_lower for w in ['compare', 'vs', 'versus', 'across', 'breakdown', 'by'])

        charts: List[Dict[str, Any]] = []
        key_metrics: List[Dict[str, Any]] = []
        direct_answer_sentences: List[str] = []

        metric_name_clean = target_metric.replace('_', ' ') if target_metric else "Metric"

        # CASE A: User asks about Year + Month (e.g. "Show sales by year and which month had the highest sales")
        if (has_year or has_month) and self.date_cols:
            primary_dt = f"_dt_{self.date_cols[0]}"
            
            # --- Annual Aggregation ---
            if has_year or (not target_dimension):
                df_year = self.df.dropna(subset=['_year', target_metric]).copy()
                if not df_year.empty:
                    year_summary = df_year.groupby('_year')[target_metric].agg(['sum', 'count', 'mean']).reset_index()
                    year_summary['_year'] = year_summary['_year'].astype(int).astype(str)
                    year_summary = year_summary.sort_values('_year')
                    
                    chart_annual_data = []
                    for _, row in year_summary.iterrows():
                        chart_annual_data.append({
                            "year": str(row['_year']),
                            metric_name_clean: round(float(row['sum']), 2),
                            "Transactions": int(row['count']),
                            "Average": round(float(row['mean']), 2)
                        })

                    # Annual chart type: bar or area
                    annual_chart_type = 'bar' if len(chart_annual_data) <= 8 else 'area'
                    charts.append({
                        "id": "chart_annual_overview",
                        "chart_type": annual_chart_type,
                        "title": f"Annual {metric_name_clean} Performance",
                        "subtitle": f"Total {metric_name_clean} aggregated chronologically by year",
                        "x_key": "year",
                        "y_keys": [metric_name_clean],
                        "x_label": "Year",
                        "y_label": f"Total {metric_name_clean}",
                        "legend": [metric_name_clean],
                        "data": chart_annual_data,
                        "recharts_config": {
                            "xAxisKey": "year",
                            "dataKey": metric_name_clean,
                            "xaxis_title": "Year",
                            "yaxis_title": f"Total {metric_name_clean} ($)" if 'revenue' in target_metric.lower() or 'sales' in target_metric.lower() or 'profit' in target_metric.lower() else f"Total {metric_name_clean}"
                        },
                        "data_columns": ["year", metric_name_clean]
                    })

                    total_all_years = df_year[target_metric].sum()
                    key_metrics.append({
                        "label": f"Total {metric_name_clean}",
                        "value": f"${total_all_years:,.2f}" if 'revenue' in target_metric.lower() or 'sales' in target_metric.lower() else f"{total_all_years:,.0f}",
                        "numeric": float(total_all_years),
                        "badge": "Cumulative Total"
                    })

            # --- Monthly Aggregation & Peak Month Calculation ---
            if has_month or is_highest_query or True:
                df_month = self.df.dropna(subset=['_year_month', target_metric]).copy()
                if not df_month.empty:
                    # Sort chronologically by year and month_num
                    month_summary = df_month.groupby(['_year', '_month_num', '_month_name', '_year_month'])[target_metric].agg(['sum', 'count', 'mean']).reset_index()
                    month_summary = month_summary.sort_values(['_year', '_month_num'])

                    chart_month_data = []
                    for _, row in month_summary.iterrows():
                        chart_month_data.append({
                            "period": str(row['_year_month']),
                            "month": str(row['_month_name']),
                            metric_name_clean: round(float(row['sum']), 2),
                            "Transactions": int(row['count'])
                        })

                    # Calculate Peak / Highest Month
                    max_row = month_summary.loc[month_summary['sum'].idxmax()]
                    peak_month_label = str(max_row['_year_month'])
                    peak_month_name = str(max_row['_month_name'])
                    peak_val = float(max_row['sum'])
                    avg_monthly = float(month_summary['sum'].mean())
                    outperformance_pct = ((peak_val - avg_monthly) / max(1, avg_monthly)) * 100

                    # Calculate Lowest Month
                    min_row = month_summary.loc[month_summary['sum'].idxmin()]
                    low_month_label = str(min_row['_year_month'])
                    low_val = float(min_row['sum'])

                    formatted_peak_val = f"${peak_val:,.2f}" if 'revenue' in target_metric.lower() or 'sales' in target_metric.lower() else f"{peak_val:,.0f}"

                    key_metrics.append({
                        "label": "Highest Month",
                        "value": f"{peak_month_label}",
                        "formatted": formatted_peak_val,
                        "numeric": peak_val,
                        "badge": f"+{outperformance_pct:.1f}% vs Avg",
                        "is_primary": True
                    })

                    key_metrics.append({
                        "label": "Monthly Average",
                        "value": f"${avg_monthly:,.2f}" if 'revenue' in target_metric.lower() or 'sales' in target_metric.lower() else f"{avg_monthly:,.0f}",
                        "numeric": avg_monthly
                    })

                    direct_answer_sentences.append(
                        f"{peak_month_label} recorded the highest {metric_name_clean.lower()} at {formatted_peak_val}, outperforming the monthly average by {outperformance_pct:.1f}%."
                    )

                    # Monthly Chart
                    charts.append({
                        "id": "chart_monthly_trend",
                        "chart_type": "line",
                        "title": f"Monthly {metric_name_clean} Trend & Peak Month",
                        "subtitle": f"Timeline highlighting {peak_month_label} as the highest volume period",
                        "x_key": "period",
                        "y_keys": [metric_name_clean],
                        "x_label": "Month",
                        "y_label": f"Monthly {metric_name_clean}",
                        "legend": [f"Monthly {metric_name_clean}"],
                        "highlight_item": {
                            "key": "period",
                            "value": peak_month_label,
                            "label": f"Highest: {formatted_peak_val}"
                        },
                        "data": chart_month_data,
                        "recharts_config": {
                            "xAxisKey": "period",
                            "dataKey": metric_name_clean,
                            "xaxis_title": "Month",
                            "yaxis_title": f"Monthly {metric_name_clean} ($)" if 'revenue' in target_metric.lower() or 'sales' in target_metric.lower() else f"Monthly {metric_name_clean}"
                        },
                        "data_columns": ["period", metric_name_clean]
                    })

        # CASE B: Categorical Breakdown (e.g. "by Region", "by Category", "top products")
        elif target_dimension and target_metric:
            df_cat = self.df.dropna(subset=[target_dimension, target_metric]).copy()
            cat_summary = df_cat.groupby(target_dimension)[target_metric].agg(['sum', 'count', 'mean']).reset_index()
            cat_summary = cat_summary.sort_values('sum', ascending=False)

            dim_clean = target_dimension.replace('_', ' ')
            top_row = cat_summary.iloc[0]
            top_dim_val = str(top_row[target_dimension])
            top_val = float(top_row['sum'])
            total_sum = float(cat_summary['sum'].sum())
            top_share_pct = (top_val / max(1, total_sum)) * 100

            formatted_top_val = f"${top_val:,.2f}" if 'revenue' in target_metric.lower() or 'sales' in target_metric.lower() else f"{top_val:,.0f}"

            key_metrics.append({
                "label": f"Top {dim_clean}",
                "value": top_dim_val,
                "formatted": formatted_top_val,
                "numeric": top_val,
                "badge": f"{top_share_pct:.1f}% Share",
                "is_primary": True
            })

            key_metrics.append({
                "label": f"Total {metric_name_clean}",
                "value": f"${total_sum:,.2f}" if 'revenue' in target_metric.lower() or 'sales' in target_metric.lower() else f"{total_sum:,.0f}",
                "numeric": total_sum
            })

            direct_answer_sentences.append(
                f"{top_dim_val} is the leading {dim_clean.lower()} with {formatted_top_val} in {metric_name_clean.lower()}, accounting for {top_share_pct:.1f}% of the total."
            )

            # Limit to top 10 categories for chart clarity
            chart_cat_data = []
            for _, row in cat_summary.head(10).iterrows():
                chart_cat_data.append({
                    "category": str(row[target_dimension]),
                    metric_name_clean: round(float(row['sum']), 2),
                    "Average": round(float(row['mean']), 2),
                    "Count": int(row['count'])
                })

            chart_type = 'pie' if len(chart_cat_data) <= 5 and not is_comparison else 'bar'
            charts.append({
                "id": f"chart_{target_dimension.lower()}_distribution",
                "chart_type": chart_type,
                "title": f"{metric_name_clean} by {dim_clean}",
                "subtitle": f"Comparative breakdown sorted by total {metric_name_clean.lower()}",
                "x_key": "category",
                "y_keys": [metric_name_clean],
                "x_label": dim_clean,
                "y_label": f"Total {metric_name_clean}",
                "legend": [metric_name_clean],
                "data": chart_cat_data,
                "recharts_config": {
                    "xAxisKey": "category",
                    "dataKey": metric_name_clean,
                    "xaxis_title": dim_clean,
                    "yaxis_title": f"Total {metric_name_clean} ($)" if 'revenue' in target_metric.lower() or 'sales' in target_metric.lower() else f"Total {metric_name_clean}"
                },
                "data_columns": ["category", metric_name_clean]
            })

        # CASE C: Fallback / General overview if query was ambiguous
        if not charts and target_metric:
            # Fallback to the primary dimension available or index
            dim = self.categorical_cols[0] if self.categorical_cols else "Index"
            df_grp = self.df.groupby(dim)[target_metric].sum().reset_index().sort_values(target_metric, ascending=False).head(10)
            chart_data = []
            for _, row in df_grp.iterrows():
                chart_data.append({
                    "category": str(row[dim]),
                    metric_name_clean: round(float(row[target_metric]), 2)
                })

            charts.append({
                "id": "chart_general_metric",
                "chart_type": "bar",
                "title": f"{metric_name_clean} Distribution",
                "subtitle": f"Top segments by {metric_name_clean.lower()}",
                "x_key": "category",
                "y_keys": [metric_name_clean],
                "x_label": dim.replace('_', ' '),
                "y_label": metric_name_clean,
                "legend": [metric_name_clean],
                "data": chart_data,
                "recharts_config": {
                    "xAxisKey": "category",
                    "dataKey": metric_name_clean,
                    "xaxis_title": dim.replace('_', ' '),
                    "yaxis_title": metric_name_clean
                },
                "data_columns": ["category", metric_name_clean]
            })

        # Construct final direct answer
        if not direct_answer_sentences:
            direct_answer_sentences.append(f"Analyzed {metric_name_clean} across {len(self.df)} records.")

        direct_answer = " ".join(direct_answer_sentences)

        # Build response payload
        response = {
            "status": "success",
            "question": question,
            "intent": {
                "metric": target_metric,
                "dimension": target_dimension,
                "has_temporal": has_year or has_month or has_date,
                "has_year": has_year,
                "has_month": has_month,
                "sub_questions": ["peak_month"] if (has_month or is_highest_query) else []
            },
            "direct_answer": direct_answer,
            "key_metrics": key_metrics,
            "charts": charts,
            "calculations_summary": {
                "total_rows_analyzed": len(self.df),
                "metric_used": target_metric,
                "columns_available": list(self.df.columns),
                "timestamp": datetime.now().isoformat()
            }
        }

        return convert_to_json_serializable(response)


def main():
    parser = argparse.ArgumentParser(description="InsightIQ Question-Driven Chart Engine")
    parser.add_argument("--input", type=str, help="Path to input JSON or CSV file containing dataset records")
    parser.add_argument("--question", type=str, required=True, help="User's analytical question")
    parser.add_argument("--name", type=str, default="Dataset", help="Dataset name")
    args = parser.parse_args()

    # Read data from file or stdin
    try:
        if args.input:
            if args.input.endswith('.csv'):
                df = pd.read_csv(args.input)
                records = df.to_dict('records')
            else:
                with open(args.input, 'r', encoding='utf-8') as f:
                    records = json.load(f)
        else:
            input_text = sys.stdin.read().strip()
            if not input_text:
                print(json.dumps({"status": "error", "message": "No input data provided"}))
                sys.exit(1)
            records = json.loads(input_text)

        engine = QuestionChartEngine(records, dataset_name=args.name)
        result = engine.analyze_question(args.question)
        print(json.dumps(result, ensure_ascii=False))

    except Exception as e:
        import traceback
        err_msg = str(e)
        stack = traceback.format_exc()
        print(json.dumps({
            "status": "error",
            "message": f"Engine execution failed: {err_msg}",
            "traceback": stack
        }))
        sys.exit(1)


if __name__ == "__main__":
    main()
