#!/usr/bin/env python3
"""
Unified Chart Calculation Engine for InsightIQ.

Responsibilities:
1. Python/Pandas performs ALL calculations:
   - Data cleaning, type inference, handling currencies/dates.
   - Descriptive statistics (sum, mean, median, min, max, std).
   - Dimension-metric aggregations (sum, mean, count) with rankings.
   - Chronological temporal trend aggregations.
   - Bivariate distributions and metric correlations.
   - Exact formatted series data generation for Recharts.
2. Serves as the mathematical backbone for the unified chart pipeline.
"""

import sys
import os
import json
import argparse
import re
import math
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Any, Optional, Union

# Optional pandas/numpy support, graceful fallback to standard library
try:
    import pandas as pd
    import numpy as np
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False


def convert_to_json_serializable(obj: Any) -> Any:
    """Recursively convert types to standard JSON-serializable types."""
    if obj is None:
        return None
    if isinstance(obj, bool):
        return bool(obj)
    if isinstance(obj, int):
        return int(obj)
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return round(float(obj), 2)
    if isinstance(obj, datetime):
        return obj.strftime('%Y-%m-%d')
    if HAS_PANDAS:
        if isinstance(obj, (np.bool_,)):
            return bool(obj)
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            if np.isnan(obj) or np.isinf(obj):
                return None
            return round(float(obj), 2)
        if isinstance(obj, (pd.Timestamp, np.datetime64)):
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


class UnifiedChartEngine:
    """Core computational engine for dataset profiling, aggregations, and chart series calculation."""

    def __init__(self, data: List[Dict[str, Any]], dataset_name: str = "Dataset"):
        self.dataset_name = dataset_name
        self.raw_data = data or []
        self.numeric_cols: List[str] = []
        self.categorical_cols: List[str] = []
        self.date_cols: List[str] = []
        self.cleaned_rows: List[Dict[str, Any]] = []
        self._normalize_dataset()

    def _normalize_dataset(self):
        """Clean columns, infer types, handle currency and dates."""
        if not self.raw_data:
            return

        # Discover all unique column names
        all_cols = []
        for r in self.raw_data:
            if isinstance(r, dict):
                for k in r.keys():
                    if k not in all_cols:
                        all_cols.append(k)

        total_rows = len(self.raw_data)
        col_types = {}

        for col in all_cols:
            col_lower = str(col).lower()
            is_date_col = any(k in col_lower for k in ['date', 'time', 'year', 'month', 'day', 'timestamp', 'period', 'created'])
            
            num_success = 0
            date_success = 0
            val_count = 0

            for r in self.raw_data:
                if not isinstance(r, dict):
                    continue
                val = r.get(col)
                if val is None or val == "":
                    continue
                val_count += 1

                # Check date
                if is_date_col:
                    try:
                        str_val = str(val).strip()
                        if len(str_val) >= 4 and any(sep in str_val for sep in ['-', '/', ' ']):
                            date_success += 1
                    except Exception:
                        pass

                # Check numeric
                try:
                    cleaned_val = str(val).replace('$', '').replace('€', '').replace('£', '').replace('¥', '').replace('%', '').replace(',', '').strip()
                    float(cleaned_val)
                    num_success += 1
                except (ValueError, TypeError):
                    pass

            if is_date_col and val_count > 0 and (date_success / val_count) > 0.4:
                self.date_cols.append(col)
                col_types[col] = 'date'
            elif val_count > 0 and (num_success / val_count) > 0.5:
                self.numeric_cols.append(col)
                col_types[col] = 'numeric'
            else:
                self.categorical_cols.append(col)
                col_types[col] = 'categorical'

        # Store cleaned rows
        self.cleaned_rows = []
        for r in self.raw_data:
            if not isinstance(r, dict):
                continue
            cleaned_row = {}
            for col, ctype in col_types.items():
                val = r.get(col)
                if val is None or val == "":
                    cleaned_row[col] = None
                elif ctype == 'numeric':
                    try:
                        c_str = str(val).replace('$', '').replace('€', '').replace('£', '').replace('¥', '').replace('%', '').replace(',', '').strip()
                        cleaned_row[col] = float(c_str)
                    except Exception:
                        cleaned_row[col] = 0.0
                elif ctype == 'date':
                    cleaned_row[col] = str(val).strip()
                else:
                    cleaned_row[col] = str(val).strip()
            self.cleaned_rows.append(cleaned_row)

    def calculate_statistics(self) -> Dict[str, Any]:
        """Compute comprehensive statistical profile and pre-aggregated breakdowns."""
        if not self.cleaned_rows:
            return {"error": "Dataset is empty"}

        total_rows = len(self.cleaned_rows)
        total_cols = len(self.numeric_cols) + len(self.categorical_cols) + len(self.date_cols)

        # Numeric summaries
        numeric_summaries = {}
        for col in self.numeric_cols:
            vals = [r[col] for r in self.cleaned_rows if r.get(col) is not None]
            if not vals:
                continue
            vals.sort()
            n = len(vals)
            s = sum(vals)
            m = s / n
            med = vals[n // 2] if n % 2 != 0 else (vals[n // 2 - 1] + vals[n // 2]) / 2
            variance = sum((x - m) ** 2 for x in vals) / (n - 1) if n > 1 else 0.0
            std = math.sqrt(variance)

            numeric_summaries[col] = {
                "sum": round(s, 2),
                "mean": round(m, 2),
                "median": round(med, 2),
                "min": round(vals[0], 2),
                "max": round(vals[-1], 2),
                "std": round(std, 2),
                "count": n
            }

        # Categorical summaries
        categorical_summaries = {}
        for col in self.categorical_cols:
            counts = defaultdict(int)
            for r in self.cleaned_rows:
                v = r.get(col)
                if v is not None:
                    counts[str(v)] += 1
            if not counts:
                continue
            sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)
            top_vals = [
                {"value": k, "count": v, "pct": round((v / total_rows) * 100, 1)}
                for k, v in sorted_counts[:5]
            ]
            dominant_k, dominant_v = sorted_counts[0]
            categorical_summaries[col] = {
                "unique_count": len(counts),
                "dominant_value": dominant_k,
                "dominant_percentage": round((dominant_v / total_rows) * 100, 1),
                "top_values": top_vals
            }

        # Bivariate pre-calculated aggregations
        bivariate_aggregations = []
        for cat in self.categorical_cols[:3]:
            for num in self.numeric_cols[:2]:
                cat_data = defaultdict(lambda: {"sum": 0.0, "count": 0})
                for r in self.cleaned_rows:
                    c_val = str(r.get(cat) or 'Unknown').strip()
                    n_val = r.get(num)
                    if n_val is not None:
                        cat_data[c_val]["sum"] += n_val
                        cat_data[c_val]["count"] += 1
                
                sorted_items = sorted(cat_data.items(), key=lambda x: x[1]["sum"], reverse=True)[:10]
                bivariate_aggregations.append({
                    "dimension": cat,
                    "metric": num,
                    "items": [
                        {
                            "category": k,
                            "sum": round(v["sum"], 2),
                            "mean": round(v["sum"] / v["count"], 2) if v["count"] > 0 else 0.0,
                            "count": v["count"]
                        }
                        for k, v in sorted_items
                    ]
                })

        # Temporal aggregations
        temporal_aggregations = []
        if self.date_cols and self.numeric_cols:
            dt_col = self.date_cols[0]
            num_col = self.numeric_cols[0]
            time_data = defaultdict(lambda: {"sum": 0.0, "count": 0})
            for r in self.cleaned_rows:
                d_val = str(r.get(dt_col) or '').strip()
                n_val = r.get(num_col)
                if d_val and n_val is not None:
                    period_key = d_val[:7] if len(d_val) >= 7 else d_val
                    time_data[period_key]["sum"] += n_val
                    time_data[period_key]["count"] += 1

            sorted_timeline = sorted(time_data.items(), key=lambda x: x[0])[:18]
            temporal_aggregations.append({
                "date_column": dt_col,
                "metric": num_col,
                "timeline": [
                    {
                        "period": k,
                        "sum": round(v["sum"], 2),
                        "mean": round(v["sum"] / v["count"], 2) if v["count"] > 0 else 0.0,
                        "count": v["count"]
                    }
                    for k, v in sorted_timeline
                ]
            })

        # Correlations between numeric columns
        correlations = []
        if len(self.numeric_cols) >= 2:
            for i in range(len(self.numeric_cols)):
                for j in range(i + 1, len(self.numeric_cols)):
                    c1 = self.numeric_cols[i]
                    c2 = self.numeric_cols[j]
                    pairs = [(r[c1], r[c2]) for r in self.cleaned_rows if r.get(c1) is not None and r.get(c2) is not None]
                    if len(pairs) > 3:
                        n = len(pairs)
                        sum_x = sum(p[0] for p in pairs)
                        sum_y = sum(p[1] for p in pairs)
                        sum_x2 = sum(p[0] ** 2 for p in pairs)
                        sum_y2 = sum(p[1] ** 2 for p in pairs)
                        sum_xy = sum(p[0] * p[1] for p in pairs)
                        denom = math.sqrt((n * sum_x2 - sum_x ** 2) * (n * sum_y2 - sum_y ** 2))
                        if denom != 0:
                            r_val = (n * sum_xy - sum_x * sum_y) / denom
                            correlations.append({
                                "col_a": c1,
                                "col_b": c2,
                                "pearson_r": round(float(r_val), 3),
                                "strength": "strong" if abs(r_val) >= 0.7 else "moderate" if abs(r_val) >= 0.4 else "weak"
                            })

        return {
            "dataset_name": self.dataset_name,
            "total_rows": total_rows,
            "total_columns": total_cols,
            "numeric_columns": self.numeric_cols,
            "categorical_columns": self.categorical_cols,
            "date_columns": self.date_cols,
            "numeric_summaries": numeric_summaries,
            "categorical_summaries": categorical_summaries,
            "bivariate_aggregations": bivariate_aggregations,
            "temporal_aggregations": temporal_aggregations,
            "correlations": correlations
        }

    def compute_chart_series(self, chart_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Calculates exact series data for a single chart constructed by Gemini."""
        if not self.cleaned_rows:
            return {"data": []}

        metric = chart_spec.get("metric_column") or (self.numeric_cols[0] if self.numeric_cols else None)
        dimension = chart_spec.get("dimension_column") or (self.categorical_cols[0] if self.categorical_cols else None)
        aggregation = chart_spec.get("aggregation", "sum").lower()
        limit = chart_spec.get("limit", 10)

        if not metric or not dimension:
            return {"data": []}

        is_temporal = (dimension in self.date_cols) or any(k in str(dimension).lower() for k in ['date', 'time', 'period', 'year', 'month'])
        grouped = defaultdict(lambda: {"sum": 0.0, "count": 0})

        for r in self.cleaned_rows:
            dim_val = r.get(dimension)
            met_val = r.get(metric, 0.0) or 0.0
            if dim_val is None:
                continue
            dim_str = str(dim_val).strip()
            if is_temporal and len(dim_str) >= 7:
                dim_str = dim_str[:7]
            grouped[dim_str]["sum"] += float(met_val)
            grouped[dim_str]["count"] += 1

        if aggregation == 'mean':
            items = [(k, v["sum"] / v["count"] if v["count"] > 0 else 0.0) for k, v in grouped.items()]
        elif aggregation == 'count':
            items = [(k, float(v["count"])) for k, v in grouped.items()]
        else:
            items = [(k, v["sum"]) for k, v in grouped.items()]

        if is_temporal:
            sorted_items = sorted(items, key=lambda x: x[0])[:18]
        else:
            sorted_items = sorted(items, key=lambda x: x[1], reverse=True)[:limit]

        is_money = bool(re.search(r'revenue|sales|cost|price|profit|amount|spend|budget', metric, re.IGNORECASE))
        is_pct = bool(re.search(r'rate|percent|percentage|margin|ratio', metric, re.IGNORECASE))

        series_data = []
        for cat, val in sorted_items:
            num_val = round(float(val), 2)
            if is_money:
                formatted = f"${num_val:,.2f}" if num_val < 1000000 else f"${num_val/1e6:,.2f}M"
            elif is_pct:
                formatted = f"{num_val:.1f}%"
            else:
                formatted = f"{num_val:,.2f}" if isinstance(num_val, float) and not num_val.is_integer() else f"{int(num_val):,}"

            series_data.append({
                dimension: str(cat),
                metric: num_val,
                "name": str(cat),
                "value": num_val,
                "formatted_value": formatted
            })

        return {
            "dimension": dimension,
            "metric": metric,
            "aggregation": aggregation,
            "data": series_data
        }


def main():
    parser = argparse.ArgumentParser(description="Unified Chart Engine for InsightIQ")
    parser.add_argument("--analyze", action="store_true", help="Calculate statistical profile from JSON on stdin")
    parser.add_argument("--compute-series", action="store_true", help="Calculate series data from JSON spec on stdin")
    args = parser.parse_args()

    try:
        input_data = json.load(sys.stdin)
    except Exception as e:
        sys.stderr.write(f"Error reading JSON from stdin: {e}\n")
        sys.exit(1)

    if args.analyze:
        rows = input_data.get("rows", input_data if isinstance(input_data, list) else [])
        dataset_name = input_data.get("dataset_name", "Dataset") if isinstance(input_data, dict) else "Dataset"
        engine = UnifiedChartEngine(rows, dataset_name=dataset_name)
        stats = engine.calculate_statistics()
        print(json.dumps(convert_to_json_serializable(stats)))
    elif args.compute_series:
        rows = input_data.get("rows", [])
        chart_specs = input_data.get("chart_specs", [])
        engine = UnifiedChartEngine(rows)
        results = []
        for spec in chart_specs:
            res = engine.compute_chart_series(spec)
            results.append({**spec, **res})
        print(json.dumps(convert_to_json_serializable(results)))
    else:
        # Default: analyze
        rows = input_data.get("rows", input_data if isinstance(input_data, list) else [])
        engine = UnifiedChartEngine(rows)
        stats = engine.calculate_statistics()
        print(json.dumps(convert_to_json_serializable(stats)))


if __name__ == "__main__":
    main()
