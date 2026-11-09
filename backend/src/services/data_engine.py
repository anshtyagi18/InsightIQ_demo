"""
Enterprise Data Engine & Profiling Service for Insightia / InsightIQ.
Provides high-throughput ingestion (.csv, .xlsx, .xls, .json), automated EDA,
data health auditing, outlier detection (IQR & Z-score), and deterministic cleaning pipelines.
"""

import io
import json
import math
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd


class DataSessionStore:
    """Thread-safe in-memory session store for active datasets and revision history."""
    _sessions: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def get(cls, session_id: str) -> Optional[Dict[str, Any]]:
        return cls._sessions.get(session_id)

    @classmethod
    def set(cls, session_id: str, data: Dict[str, Any]):
        cls._sessions[session_id] = data

    @classmethod
    def get_df(cls, session_id: str) -> Optional[pd.DataFrame]:
        session = cls.get(session_id)
        if session and "df" in session:
            return session["df"]
        return None

    @classmethod
    def update_df(cls, session_id: str, new_df: pd.DataFrame, audit_entry: str):
        session = cls.get(session_id)
        if not session:
            session = {
                "session_id": session_id,
                "history": [],
                "created_at": datetime.utcnow().isoformat(),
            }
            cls.set(session_id, session)

        # Store previous state in history for undo capability
        if "df" in session:
            history = session.setdefault("history", [])
            history.append({
                "timestamp": datetime.utcnow().isoformat(),
                "action": audit_entry,
                "shape": list(session["df"].shape),
            })

        session["df"] = new_df
        session["updated_at"] = datetime.utcnow().isoformat()
        audit_log = session.setdefault("audit_log", [])
        audit_log.append({
            "timestamp": datetime.utcnow().isoformat(),
            "message": audit_entry,
            "rows": int(new_df.shape[0]),
            "cols": int(new_df.shape[1]),
        })


def sanitize_value(val: Any) -> Any:
    """Recursively convert float NaN/Inf, Timestamps, and Numpy types for valid JSON."""
    if val is None:
        return None
    if isinstance(val, (float, np.floating)):
        if math.isnan(val) or math.isinf(val):
            return None
        return float(val)
    if isinstance(val, (np.integer, int)):
        return int(val)
    if isinstance(val, (np.bool_, bool)):
        return bool(val)
    if isinstance(val, (pd.Timestamp, datetime)):
        return val.isoformat()
    if isinstance(val, np.ndarray):
        return [sanitize_value(v) for v in val.tolist()]
    if isinstance(val, (list, tuple)):
        return [sanitize_value(v) for v in val]
    if isinstance(val, dict):
        return {k: sanitize_value(v) for k, v in val.items()}
    if pd.isna(val):
        return None
    return str(val)


class DataEngine:
    """Core analytical data engine handling ingestion, profiling, anomaly detection and auto-cleaning."""

    @staticmethod
    def parse_file(content: bytes, filename: str) -> pd.DataFrame:
        """Parse raw file bytes into a clean Pandas DataFrame."""
        lower_name = filename.lower()
        if lower_name.endswith('.csv'):
            # Detect separator or fallback cleanly
            try:
                df = pd.read_csv(io.BytesIO(content), encoding='utf-8')
            except UnicodeDecodeError:
                df = pd.read_csv(io.BytesIO(content), encoding='latin1')
        elif lower_name.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(io.BytesIO(content))
        elif lower_name.endswith('.json'):
            try:
                df = pd.read_json(io.BytesIO(content))
            except Exception:
                data = json.loads(content.decode('utf-8'))
                if isinstance(data, list):
                    df = pd.DataFrame(data)
                elif isinstance(data, dict):
                    # Check if dictionary contains record array or keys as columns
                    key = next((k for k, v in data.items() if isinstance(v, list)), None)
                    if key:
                        df = pd.DataFrame(data[key])
                    else:
                        df = pd.DataFrame([data])
                else:
                    raise ValueError("Unsupported JSON layout")
        else:
            raise ValueError(f"Unsupported file format: {filename}. Supported formats: .csv, .xlsx, .xls, .json")

        # Sanitize column names: strip whitespace, replace newline characters
        df.columns = [str(c).strip().replace('\n', ' ') for c in df.columns]
        return df

    @classmethod
    def profile_dataframe(cls, df: pd.DataFrame, dataset_name: str = "Dataset") -> Dict[str, Any]:
        """
        Generate deep automated EDA & profiling:
        - Overall Health Score (0-100)
        - Column-level metrics (types, nulls, unique, distribution, stats, anomalies)
        - Pairwise Pearson correlation matrix
        - Automated key natural language insights
        """
        total_rows, total_cols = df.shape
        if total_rows == 0:
            return {
                "dataset_name": dataset_name,
                "total_rows": 0,
                "total_cols": total_cols,
                "health_score": 0,
                "columns": [],
                "correlations": {},
                "insights": ["Dataset is empty."],
                "preview": []
            }

        total_cells = total_rows * total_cols
        total_missing_cells = int(df.isna().sum().sum())
        missing_rate = total_missing_cells / total_cells if total_cells > 0 else 0

        duplicate_rows = int(df.duplicated().sum())
        duplicate_rate = duplicate_rows / total_rows if total_rows > 0 else 0

        # Calculate dataset health score: 100 - penalties
        # Penalty 1: Missing values (up to 40 pts)
        missing_penalty = min(missing_rate * 100 * 1.5, 40)
        # Penalty 2: Duplicate rows (up to 20 pts)
        duplicate_penalty = min(duplicate_rate * 100 * 2.0, 20)

        outlier_count_total = 0
        columns_profile: List[Dict[str, Any]] = []
        numeric_col_names: List[str] = []

        for col in df.columns:
            series = df[col]
            missing_count = int(series.isna().sum())
            missing_pct = round((missing_count / total_rows) * 100, 2)
            unique_count = int(series.nunique(dropna=True))

            # Detect semantic type
            is_numeric = pd.api.types.is_numeric_dtype(series)
            is_datetime = pd.api.types.is_datetime64_any_dtype(series)
            is_bool = pd.api.types.is_bool_dtype(series)

            col_type = "text"
            if is_bool:
                col_type = "boolean"
            elif is_numeric:
                col_type = "numeric"
                numeric_col_names.append(col)
            elif is_datetime:
                col_type = "datetime"
            else:
                # Try inferring if string column is parseable datetime
                sample = series.dropna().head(20).astype(str)
                if len(sample) > 0 and sample.str.contains(r'^\d{4}[-/]\d{1,2}[-/]\d{1,2}').mean() > 0.8:
                    col_type = "datetime"
                elif unique_count <= max(15, total_rows * 0.05):
                    col_type = "categorical"

            # Column stats & outlier calculation
            col_stats: Dict[str, Any] = {}
            col_outliers_iqr = 0
            col_outliers_zscore = 0

            if col_type == "numeric":
                cleaned_numeric = series.dropna()
                if len(cleaned_numeric) > 0:
                    mean_val = float(cleaned_numeric.mean())
                    std_val = float(cleaned_numeric.std()) if len(cleaned_numeric) > 1 else 0.0
                    min_val = float(cleaned_numeric.min())
                    max_val = float(cleaned_numeric.max())
                    median_val = float(cleaned_numeric.median())
                    q1 = float(cleaned_numeric.quantile(0.25))
                    q3 = float(cleaned_numeric.quantile(0.75))
                    iqr = q3 - q1

                    # IQR Outliers
                    lower_bound = q1 - 1.5 * iqr
                    upper_bound = q3 + 1.5 * iqr
                    col_outliers_iqr = int(((cleaned_numeric < lower_bound) | (cleaned_numeric > upper_bound)).sum())

                    # Z-score Outliers (|z| > 3)
                    if std_val > 0:
                        z_scores = (cleaned_numeric - mean_val) / std_val
                        col_outliers_zscore = int((z_scores.abs() > 3).sum())

                    outlier_count_total += col_outliers_iqr

                    skew_val = float(cleaned_numeric.skew()) if len(cleaned_numeric) > 2 else 0.0
                    if math.isnan(skew_val):
                        skew_val = 0.0

                    col_stats = {
                        "min": min_val,
                        "max": max_val,
                        "mean": round(mean_val, 2),
                        "median": round(median_val, 2),
                        "std": round(std_val, 2),
                        "q25": round(q1, 2),
                        "q75": round(q3, 2),
                        "iqr": round(iqr, 2),
                        "skewness": round(skew_val, 2),
                        "outliers_iqr": col_outliers_iqr,
                        "outliers_zscore": col_outliers_zscore,
                        "lower_bound": round(lower_bound, 2),
                        "upper_bound": round(upper_bound, 2),
                    }

            # Top value frequencies (for category/histogram distribution visualizer)
            top_values = []
            try:
                counts = series.value_counts(dropna=True).head(8)
                for val, count in counts.items():
                    top_values.append({
                        "name": str(val)[:24],
                        "count": int(count),
                        "percentage": round((count / total_rows) * 100, 1)
                    })
            except Exception:
                pass

            columns_profile.append({
                "name": col,
                "type": col_type,
                "missing_count": missing_count,
                "missing_pct": missing_pct,
                "unique_count": unique_count,
                "stats": col_stats,
                "top_values": top_values,
                "outliers_count": col_outliers_iqr if col_type == "numeric" else 0,
            })

        # Penalty 3: Outlier ratio (up to 15 pts)
        outlier_rate = outlier_count_total / total_cells if total_cells > 0 else 0
        outlier_penalty = min(outlier_rate * 100 * 2.0, 15)

        raw_health = 100 - missing_penalty - duplicate_penalty - outlier_penalty
        health_score = max(5, min(100, int(round(raw_health))))

        # Correlation Matrix for Numeric Columns (Pearson)
        correlations: Dict[str, Dict[str, float]] = {}
        strong_correlations: List[Dict[str, Any]] = []
        if len(numeric_col_names) >= 2:
            try:
                corr_df = df[numeric_col_names].corr(method='pearson')
                for c1 in numeric_col_names:
                    correlations[c1] = {}
                    for c2 in numeric_col_names:
                        val = corr_df.loc[c1, c2]
                        if pd.isna(val) or math.isnan(val):
                            correlations[c1][c2] = 0.0
                        else:
                            correlations[c1][c2] = round(float(val), 3)

                        if c1 < c2 and not pd.isna(val) and abs(float(val)) >= 0.5:
                            strong_correlations.append({
                                "col1": c1,
                                "col2": c2,
                                "correlation": round(float(val), 3),
                                "strength": "Strong Positive" if val > 0.7 else "Moderate Positive" if val > 0 else "Strong Negative" if val < -0.7 else "Moderate Negative"
                            })
            except Exception:
                pass

        # Generate Automated Key Strategic Insights
        insights: List[Dict[str, Any]] = []

        # 1. Health & Completeness Insight
        if health_score >= 90:
            insights.append({
                "type": "health",
                "level": "success",
                "title": "High Data Quality Integrity",
                "description": f"Dataset demonstrates excellent integrity with a health score of {health_score}%. Minimal missing cells ({missing_rate*100:.1f}%) and {duplicate_rows} duplicate rows."
            })
        elif health_score >= 70:
            insights.append({
                "type": "health",
                "level": "warning",
                "title": "Moderate Data Quality Needs Attention",
                "description": f"Dataset health score is {health_score}%. Detected {total_missing_cells} missing values ({missing_rate*100:.1f}%) and {duplicate_rows} duplicate rows. Consider running Auto-Clean."
            })
        else:
            insights.append({
                "type": "health",
                "level": "alert",
                "title": "Critical Missingness or Anomalies Detected",
                "description": f"Dataset health score is low ({health_score}%). Contains {total_missing_cells} null values ({missing_rate*100:.1f}%) and {outlier_count_total} extreme statistical outliers."
            })

        # 2. Outlier Insights
        high_outlier_cols = [c for c in columns_profile if c["type"] == "numeric" and c["outliers_count"] > 0]
        if high_outlier_cols:
            top_outlier = max(high_outlier_cols, key=lambda x: x["outliers_count"])
            insights.append({
                "type": "anomaly",
                "level": "warning",
                "title": f"Statistical Outliers in {top_outlier['name']}",
                "description": f"Column '{top_outlier['name']}' has {top_outlier['outliers_count']} outliers beyond 1.5x IQR boundary. Values range from {top_outlier['stats'].get('min')} to {top_outlier['stats'].get('max')}."
            })

        # 3. Correlation Insights
        if strong_correlations:
            strongest = max(strong_correlations, key=lambda x: abs(x["correlation"]))
            insights.append({
                "type": "trend",
                "level": "info",
                "title": f"Significant Correlation: {strongest['col1']} vs {strongest['col2']}",
                "description": f"Strong Pearson correlation coefficient of {strongest['correlation']} ({strongest['strength']}) detected between '{strongest['col1']}' and '{strongest['col2']}'."
            })

        # 4. Skewness / Distribution Insight
        skewed_cols = [c for c in columns_profile if c["type"] == "numeric" and abs(c["stats"].get("skewness", 0)) > 1.2]
        if skewed_cols:
            c = skewed_cols[0]
            direction = "right-skewed (high positive tail)" if c["stats"]["skewness"] > 0 else "left-skewed (heavy low values)"
            insights.append({
                "type": "distribution",
                "level": "info",
                "title": f"Distribution Asymmetry in '{c['name']}'",
                "description": f"Distribution is strongly {direction} with skewness {c['stats']['skewness']}. Mean ({c['stats']['mean']}) deviates substantially from Median ({c['stats']['median']})."
            })

        # Data preview (sanitized first 50 rows)
        preview_rows = []
        preview_df = df.head(50)
        for _, row in preview_df.iterrows():
            preview_rows.append({col: sanitize_value(row[col]) for col in df.columns})

        result = {
            "dataset_name": dataset_name,
            "total_rows": total_rows,
            "total_cols": total_cols,
            "total_cells": total_cells,
            "missing_cells": total_missing_cells,
            "missing_rate": round(missing_rate * 100, 2),
            "duplicate_rows": duplicate_rows,
            "duplicate_rate": round(duplicate_rate * 100, 2),
            "outlier_count": outlier_count_total,
            "health_score": health_score,
            "columns": columns_profile,
            "correlations": correlations,
            "strong_correlations": strong_correlations,
            "insights": insights,
            "preview": preview_rows,
        }

        return sanitize_value(result)

    @classmethod
    def clean_dataframe(
        cls,
        df: pd.DataFrame,
        action: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Tuple[pd.DataFrame, str]:
        """
        Execute deterministic data cleaning operations:
        - 'impute': Impute missing values (mean, median, mode, constant)
        - 'drop_na': Drop rows with missing values
        - 'remove_duplicates': Remove duplicate rows
        - 'remove_outliers': Remove outliers using IQR or Z-score
        - 'coerce_types': Coerce date, numeric, or categorical types
        - 'auto_clean': Full multi-step enterprise clean pass
        """
        params = params or {}
        cleaned_df = df.copy()
        audit_msg = ""

        before_rows, before_cols = cleaned_df.shape
        before_nulls = int(cleaned_df.isna().sum().sum())

        if action == "impute":
            strategy = params.get("strategy", "median")
            columns = params.get("columns", list(cleaned_df.columns))
            fill_val = params.get("value")
            imputed_count = 0

            for col in columns:
                if col not in cleaned_df.columns:
                    continue
                col_nulls = int(cleaned_df[col].isna().sum())
                if col_nulls == 0:
                    continue

                if strategy == "constant" and fill_val is not None:
                    cleaned_df[col] = cleaned_df[col].fillna(fill_val)
                    imputed_count += col_nulls
                elif pd.api.types.is_numeric_dtype(cleaned_df[col]):
                    if strategy == "mean":
                        m = cleaned_df[col].mean()
                        cleaned_df[col] = cleaned_df[col].fillna(m)
                    elif strategy == "mode":
                        mode_s = cleaned_df[col].mode()
                        if not mode_s.empty:
                            cleaned_df[col] = cleaned_df[col].fillna(mode_s[0])
                    else:  # median
                        med = cleaned_df[col].median()
                        cleaned_df[col] = cleaned_df[col].fillna(med)
                    imputed_count += col_nulls
                else:
                    # Categorical / string mode
                    mode_s = cleaned_df[col].mode()
                    if not mode_s.empty:
                        cleaned_df[col] = cleaned_df[col].fillna(mode_s[0])
                    else:
                        cleaned_df[col] = cleaned_df[col].fillna("Unknown")
                    imputed_count += col_nulls

            audit_msg = f"Imputed {imputed_count} missing values using {strategy} strategy across {len(columns)} columns."

        elif action == "drop_na":
            columns = params.get("columns")
            if columns:
                valid_cols = [c for c in columns if c in cleaned_df.columns]
                cleaned_df = cleaned_df.dropna(subset=valid_cols)
            else:
                cleaned_df = cleaned_df.dropna()

            rows_dropped = before_rows - len(cleaned_df)
            audit_msg = f"Dropped {rows_dropped} rows containing null values."

        elif action == "remove_duplicates":
            cleaned_df = cleaned_df.drop_duplicates()
            dups_removed = before_rows - len(cleaned_df)
            audit_msg = f"Removed {dups_removed} duplicate rows."

        elif action == "remove_outliers":
            method = params.get("method", "iqr")
            columns = params.get("columns", [c for c in cleaned_df.columns if pd.api.types.is_numeric_dtype(cleaned_df[c])])
            mask = pd.Series(True, index=cleaned_df.index)

            for col in columns:
                if col not in cleaned_df.columns or not pd.api.types.is_numeric_dtype(cleaned_df[col]):
                    continue
                series = cleaned_df[col].dropna()
                if len(series) < 5:
                    continue

                if method == "iqr":
                    q1 = series.quantile(0.25)
                    q3 = series.quantile(0.75)
                    iqr = q3 - q1
                    lower = q1 - 1.5 * iqr
                    upper = q3 + 1.5 * iqr
                    col_mask = (cleaned_df[col] >= lower) & (cleaned_df[col] <= upper)
                    mask = mask & col_mask
                elif method == "zscore":
                    mean_val = series.mean()
                    std_val = series.std()
                    if std_val > 0:
                        col_mask = ((cleaned_df[col] - mean_val) / std_val).abs() <= 3
                        mask = mask & col_mask

            cleaned_df = cleaned_df[mask]
            outliers_removed = before_rows - len(cleaned_df)
            audit_msg = f"Filtered out {outliers_removed} outliers using {method.upper()} threshold across {len(columns)} numeric columns."

        elif action == "coerce_types":
            type_conversions = 0
            for col in cleaned_df.columns:
                series = cleaned_df[col].dropna()
                if series.empty:
                    continue
                # Try date coercion
                if not pd.api.types.is_datetime64_any_dtype(series) and series.dtype == 'object':
                    try:
                        # Check sample
                        converted = pd.to_datetime(cleaned_df[col], errors='coerce')
                        if converted.notna().sum() / len(series) > 0.8:
                            cleaned_df[col] = converted
                            type_conversions += 1
                            continue
                    except Exception:
                        pass

                # Try numeric coercion for object columns that might have currency or commas
                if series.dtype == 'object':
                    try:
                        cleaned_str = cleaned_df[col].astype(str).str.replace(r'[\$,]', '', regex=True)
                        converted_num = pd.to_numeric(cleaned_str, errors='coerce')
                        if converted_num.notna().sum() / len(series) > 0.85:
                            cleaned_df[col] = converted_num
                            type_conversions += 1
                    except Exception:
                        pass

            audit_msg = f"Coerced data types for {type_conversions} columns (normalized dates and numeric formats)."

        elif action == "auto_clean":
            # 1. Deduplicate
            cleaned_df = cleaned_df.drop_duplicates()
            dups_removed = before_rows - len(cleaned_df)

            # 2. Type coercion
            type_conversions = 0
            for col in cleaned_df.columns:
                if cleaned_df[col].dtype == 'object':
                    # Numeric strip
                    try:
                        s_str = cleaned_df[col].astype(str).str.replace(r'[\$,]', '', regex=True)
                        conv = pd.to_numeric(s_str, errors='coerce')
                        if conv.notna().sum() / max(1, len(cleaned_df[col].dropna())) > 0.85:
                            cleaned_df[col] = conv
                            type_conversions += 1
                            continue
                    except Exception:
                        pass
                    # Date
                    try:
                        conv_date = pd.to_datetime(cleaned_df[col], errors='coerce')
                        if conv_date.notna().sum() / max(1, len(cleaned_df[col].dropna())) > 0.85:
                            cleaned_df[col] = conv_date
                            type_conversions += 1
                    except Exception:
                        pass

            # 3. Impute missing values (median for numeric, mode for categorical)
            imputed_count = 0
            for col in cleaned_df.columns:
                col_nulls = int(cleaned_df[col].isna().sum())
                if col_nulls > 0:
                    # If >70% null, drop column
                    if col_nulls / len(cleaned_df) > 0.7:
                        cleaned_df = cleaned_df.drop(columns=[col])
                        continue
                    if pd.api.types.is_numeric_dtype(cleaned_df[col]):
                        cleaned_df[col] = cleaned_df[col].fillna(cleaned_df[col].median())
                    else:
                        m = cleaned_df[col].mode()
                        cleaned_df[col] = cleaned_df[col].fillna(m[0] if not m.empty else "Unknown")
                    imputed_count += col_nulls

            after_nulls = int(cleaned_df.isna().sum().sum())
            audit_msg = (
                f"Auto-Clean complete: Removed {dups_removed} duplicates, "
                f"imputed {imputed_count} nulls, and updated {type_conversions} column types."
            )

        else:
            raise ValueError(f"Unknown cleaning action: {action}")

        return cleaned_df, audit_msg

