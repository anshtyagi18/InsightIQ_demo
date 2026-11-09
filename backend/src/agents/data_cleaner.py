"""
Data Cleaner & Preprocessor Agent

This agent ensures data quality and prepares data for analysis using Google ADK.
As specified in the PRD, it handles missing values, duplicates, data type validation,
and provides data quality assessment.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from google.adk.agents import Agent
from google.adk.tools import FunctionTool
import logging

logger = logging.getLogger(__name__)


def detect_missing_values(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Detect and analyze missing values in the dataset.
    
    Args:
        data: Dictionary containing the dataset information
        
    Returns:
        Dictionary with missing value analysis
    """
    try:
        rows = data.get('rows', [])
        columns = data.get('columns', [])
        
        if not rows or not columns:
            return {
                'status': 'error',
                'message': 'Invalid data format - missing rows or columns'
            }
        
        missing_analysis = {}
        total_rows = len(rows)
        
        for column in columns:
            missing_count = 0
            for row in rows:
                if row.get(column) is None or row.get(column) == '' or str(row.get(column)).strip() == '':
                    missing_count += 1
            
            missing_percentage = (missing_count / total_rows) * 100 if total_rows > 0 else 0
            missing_analysis[column] = {
                'count': missing_count,
                'percentage': missing_percentage,
                'recommendations': _get_missing_value_recommendations({'missing_value_summary': {column: {'percentage': missing_percentage}}})
            }
        
        return {
            'status': 'success',
            'missing_value_summary': missing_analysis,
            'total_rows': total_rows,
            'recommendations': _get_missing_value_recommendations({'missing_value_summary': missing_analysis})
        }
        
    except Exception as e:
        logger.error(f"Error in detect_missing_values: {str(e)}")
        return {
            'status': 'error',
            'message': f"Failed to analyze missing values: {str(e)}"
        }


def detect_duplicates(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Detect duplicate rows in the dataset.
    
    Args:
        data: Dictionary containing the dataset information
        
    Returns:
        Dictionary with duplicate analysis
    """
    try:
        rows = data.get('rows', [])
        
        if not rows:
            return {
                'status': 'error',
                'message': 'No data rows provided'
            }
        
        # Convert to list of tuples for duplicate detection
        row_tuples = []
        for row in rows:
            # Sort items to ensure consistent ordering
            sorted_items = sorted(row.items())
            row_tuples.append(tuple(sorted_items))
        
        unique_rows = set(row_tuples)
        duplicate_count = len(rows) - len(unique_rows)
        duplicate_percentage = (duplicate_count / len(rows)) * 100 if len(rows) > 0 else 0
        
        recommendations = _get_duplicate_recommendations({'duplicate_percentage': duplicate_percentage})
        
        return {
            'status': 'success',
            'total_rows': len(rows),
            'unique_rows': len(unique_rows),
            'duplicate_count': duplicate_count,
            'duplicate_percentage': duplicate_percentage,
            'recommendations': recommendations
        }
        
    except Exception as e:
        logger.error(f"Error in detect_duplicates: {str(e)}")
        return {
            'status': 'error',
            'message': f"Failed to analyze duplicates: {str(e)}"
        }


def validate_data_types(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and recommend optimal data types for each column.
    
    Args:
        data: Dictionary containing the dataset information
        
    Returns:
        Dictionary with data type analysis
    """
    try:
        rows = data.get('rows', [])
        columns = data.get('columns', [])
        
        if not rows or not columns:
            return {
                'status': 'error',
                'message': 'Invalid data format - missing rows or columns'
            }
        
        type_analysis = {}
        
        for column in columns:
            column_values = [row.get(column) for row in rows if row.get(column) is not None]
            
            if not column_values:
                type_analysis[column] = {
                    'current_type': 'null',
                    'recommended_type': 'string',
                    'confidence': 0.0,
                    'sample_values': []
                }
                continue
            
            recommended_type = _recommend_data_type(column_values)
            sample_values = column_values[:5]  # First 5 non-null values
            
            type_analysis[column] = {
                'current_type': type(column_values[0]).__name__,
                'recommended_type': recommended_type,
                'confidence': 0.9,  # Simplified confidence calculation
                'sample_values': sample_values
            }
        
        return {
            'status': 'success',
            'type_analysis': type_analysis,
            'recommendations': 'Consider converting columns to recommended types for better performance'
        }
        
    except Exception as e:
        logger.error(f"Error in validate_data_types: {str(e)}")
        return {
            'status': 'error',
            'message': f"Failed to validate data types: {str(e)}"
        }


def _get_missing_value_recommendations(analysis: Dict[str, Any]) -> List[str]:
    """Generate recommendations for handling missing values."""
    recommendations = []
    
    missing_summary = analysis.get('missing_value_summary', {})
    
    for column, info in missing_summary.items():
        percentage = info.get('percentage', 0)
        
        if percentage > 50:
            recommendations.append(f"Consider dropping column '{column}' (>{percentage:.1f}% missing)")
        elif percentage > 20:
            recommendations.append(f"Use imputation for column '{column}' ({percentage:.1f}% missing)")
        elif percentage > 5:
            recommendations.append(f"Fill missing values in column '{column}' ({percentage:.1f}% missing)")
        elif percentage > 0:
            recommendations.append(f"Handle few missing values in column '{column}' ({percentage:.1f}% missing)")
    
    return recommendations


def _get_duplicate_recommendations(analysis: Dict[str, Any]) -> List[str]:
    """Generate recommendations for handling duplicates."""
    recommendations = []
    percentage = analysis.get('duplicate_percentage', 0)
    
    if percentage > 10:
        recommendations.append("High duplicate rate detected - consider thorough deduplication")
    elif percentage > 5:
        recommendations.append("Moderate duplicates found - review and remove duplicates")
    elif percentage > 0:
        recommendations.append("Few duplicates detected - standard deduplication recommended")
    else:
        recommendations.append("No duplicates found - data is clean")
    
    return recommendations


def _recommend_data_type(values: List[Any]) -> str:
    """Recommend the most appropriate data type for a list of values."""
    if not values:
        return 'string'
    
    # Check for numeric types
    numeric_count = 0
    for value in values:
        try:
            float(str(value))
            numeric_count += 1
        except (ValueError, TypeError):
            pass
    
    if numeric_count == len(values):
        # Check if all are integers
        int_count = 0
        for value in values:
            try:
                if float(str(value)).is_integer():
                    int_count += 1
            except (ValueError, TypeError):
                pass
        
        if int_count == len(values):
            return 'integer'
        else:
            return 'float'
    
    # Check for boolean
    bool_values = {'true', 'false', '1', '0', 'yes', 'no'}
    if all(str(value).lower() in bool_values for value in values):
        return 'boolean'
    
    # Check for datetime (simplified)
    datetime_patterns = ['-', '/', ':', 'T', 'Z']
    if any(any(pattern in str(value) for pattern in datetime_patterns) for value in values):
        return 'datetime'
    
    return 'string'


def impute_missing_values(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Impute missing values in the dataset using various strategies.
    
    Args:
        data: Dictionary containing:
            - rows: List of row dictionaries
            - columns: List of column names
            - imputation_config: Optional dict with column-specific strategies
                Format: {"column_name": {"strategy": "mean|median|mode|ffill|bfill|drop", "value": custom_value}}
                
    Returns:
        Dictionary with imputation results and cleaned data
    """
    try:
        rows = data.get('rows', [])
        columns = data.get('columns', [])
        imputation_config = data.get('imputation_config', {})
        
        if not rows or not columns:
            return {
                'status': 'error',
                'message': 'Invalid data format - missing rows or columns'
            }
        
        # Convert to pandas DataFrame for easier manipulation
        df = pd.DataFrame(rows)
        original_row_count = len(df)
        imputation_report = {}
        
        for column in columns:
            if column not in df.columns:
                continue
                
            missing_count = df[column].isnull().sum()
            if missing_count == 0:
                imputation_report[column] = {
                    'strategy': 'none',
                    'missing_before': 0,
                    'missing_after': 0,
                    'values_imputed': 0
                }
                continue
            
            # Get strategy for this column
            column_config = imputation_config.get(column, {})
            strategy = column_config.get('strategy', 'auto')
            custom_value = column_config.get('value', None)
            
            # Auto-determine strategy based on data type
            if strategy == 'auto':
                strategy = _determine_imputation_strategy(df[column])
            
            # Apply imputation strategy
            original_missing = df[column].isnull().sum()
            
            if strategy == 'mean' and pd.api.types.is_numeric_dtype(df[column]):
                fill_value = df[column].mean()
                df[column] = df[column].fillna(fill_value)
            elif strategy == 'median' and pd.api.types.is_numeric_dtype(df[column]):
                fill_value = df[column].median()
                df[column] = df[column].fillna(fill_value)
            elif strategy == 'mode':
                mode_values = df[column].mode()
                if len(mode_values) > 0:
                    fill_value = mode_values[0]
                    df[column] = df[column].fillna(fill_value)
            elif strategy == 'ffill':
                df[column] = df[column].fillna(method='ffill')
            elif strategy == 'bfill':
                df[column] = df[column].fillna(method='bfill')
            elif strategy == 'custom' and custom_value is not None:
                df[column] = df[column].fillna(custom_value)
            elif strategy == 'drop':
                df = df.dropna(subset=[column])
            else:
                # Default to mode for categorical, mean for numeric
                if pd.api.types.is_numeric_dtype(df[column]):
                    fill_value = df[column].mean()
                    df[column] = df[column].fillna(fill_value)
                else:
                    mode_values = df[column].mode()
                    if len(mode_values) > 0:
                        fill_value = mode_values[0]
                        df[column] = df[column].fillna(fill_value)
            
            final_missing = df[column].isnull().sum()
            imputation_report[column] = {
                'strategy': strategy,
                'missing_before': int(original_missing),
                'missing_after': int(final_missing),
                'values_imputed': int(original_missing - final_missing)
            }
        
        # Convert back to dictionary format
        cleaned_rows = df.to_dict('records')
        final_row_count = len(cleaned_rows)
        
        return {
            'status': 'success',
            'original_row_count': original_row_count,
            'final_row_count': final_row_count,
            'rows_removed': original_row_count - final_row_count,
            'cleaned_data': {
                'rows': cleaned_rows,
                'columns': columns
            },
            'imputation_report': imputation_report,
            'summary': f"Successfully imputed missing values in {len([col for col, report in imputation_report.items() if report['values_imputed'] > 0])} columns"
        }
        
    except Exception as e:
        logger.error(f"Error in impute_missing_values: {str(e)}")
        return {
            'status': 'error',
            'message': f"Failed to impute missing values: {str(e)}"
        }


def _determine_imputation_strategy(series: pd.Series) -> str:
    """
    Automatically determine the best imputation strategy for a column.
    
    Args:
        series: Pandas series to analyze
        
    Returns:
        Recommended imputation strategy
    """
    # Get non-null values for analysis
    non_null_values = series.dropna()
    
    if len(non_null_values) == 0:
        return 'drop'
    
    # For numeric columns
    if pd.api.types.is_numeric_dtype(series):
        # Check distribution skewness
        try:
            skewness = non_null_values.skew()
            if abs(skewness) < 0.5:  # Roughly normal distribution
                return 'mean'
            else:  # Skewed distribution
                return 'median'
        except:
            return 'median'
    
    # For categorical/text columns
    else:
        # Use mode for categorical data
        return 'mode'


def _handle_missing_values(data: Dict[str, Any], strategy: str = 'auto') -> Dict[str, Any]:
    """
    Handle missing values based on the specified strategy.
    
    Args:
        data: Dictionary containing the dataset information
        strategy: Overall strategy to apply ('auto', 'mean', 'median', 'mode', 'drop')
        
    Returns:
        Dictionary with cleaned data and imputation results
    """
    try:
        # Create imputation config based on strategy
        imputation_config = {}
        columns = data.get('columns', [])
        
        if strategy != 'auto':
            # Apply same strategy to all columns
            for column in columns:
                imputation_config[column] = {'strategy': strategy}
        
        # Add imputation config to data
        data_with_config = data.copy()
        data_with_config['imputation_config'] = imputation_config
        
        # Use the comprehensive imputation function
        return impute_missing_values(data_with_config)
        
    except Exception as e:
        logger.error(f"Error in _handle_missing_values: {str(e)}")
        return {
            'status': 'error',
            'message': f"Failed to handle missing values: {str(e)}"
        }


def _convert_data_types(data: Dict[str, Any], type_mapping: Dict[str, str]) -> Dict[str, Any]:
    """Convert data types based on the provided mapping."""
    # Implementation for converting data types
    # This is a placeholder for the actual implementation
    return {
        'status': 'success',
        'message': 'Data types converted successfully',
        'conversions_applied': type_mapping
    }


def remove_duplicates(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Remove duplicate rows from the dataset with various strategies.
    
    Args:
        data: Dictionary containing:
            - rows: List of row dictionaries
            - columns: List of column names
            - duplicate_config: Optional dict with removal configuration
                Format: {
                    "strategy": "first|last|all",  # which duplicates to keep
                    "subset": ["col1", "col2"],    # columns to consider for duplicates
                    "keep_index": True/False       # whether to preserve original index info
                }
                
    Returns:
        Dictionary with duplicate removal results and cleaned data
    """
    try:
        rows = data.get('rows', [])
        columns = data.get('columns', [])
        duplicate_config = data.get('duplicate_config', {})
        
        if not rows or not columns:
            return {
                'status': 'error',
                'message': 'Invalid data format - missing rows or columns'
            }
        
        # Convert to pandas DataFrame for easier manipulation
        df = pd.DataFrame(rows)
        original_row_count = len(df)
        
        # Get configuration
        strategy = duplicate_config.get('strategy', 'first')  # keep first occurrence by default
        subset_columns = duplicate_config.get('subset', None)  # consider all columns by default
        keep_index = duplicate_config.get('keep_index', False)
        
        # Add original index if requested
        if keep_index:
            df['_original_index'] = df.index
        
        # Validate subset columns
        if subset_columns:
            invalid_columns = [col for col in subset_columns if col not in df.columns]
            if invalid_columns:
                return {
                    'status': 'error',
                    'message': f'Invalid subset columns: {invalid_columns}'
                }
        
        # Detect duplicates before removal
        duplicate_mask = df.duplicated(subset=subset_columns, keep=False)
        duplicates_found = df[duplicate_mask].copy()
        duplicate_count = duplicate_mask.sum()
        
        # Remove duplicates based on strategy
        if strategy == 'first':
            # Keep first occurrence, remove subsequent duplicates
            df_cleaned = df.drop_duplicates(subset=subset_columns, keep='first')
        elif strategy == 'last':
            # Keep last occurrence, remove previous duplicates
            df_cleaned = df.drop_duplicates(subset=subset_columns, keep='last')
        elif strategy == 'all':
            # Remove all duplicates (keep none)
            df_cleaned = df[~duplicate_mask]
        else:
            return {
                'status': 'error',
                'message': f'Invalid strategy: {strategy}. Use "first", "last", or "all"'
            }
        
        # Calculate results
        final_row_count = len(df_cleaned)
        rows_removed = original_row_count - final_row_count
        
        # Remove the original index column if it was added temporarily
        if keep_index and '_original_index' in df_cleaned.columns and not keep_index:
            df_cleaned = df_cleaned.drop(columns=['_original_index'])
        
        # Convert back to dictionary format
        cleaned_rows = df_cleaned.to_dict('records')
        
        # Create detailed duplicate report
        duplicate_groups = []
        if duplicate_count > 0:
            # Group duplicates for reporting
            duplicate_info = duplicates_found.groupby(
                duplicates_found.columns.tolist() if subset_columns is None else subset_columns
            ).size().reset_index(name='count')
            
            # Convert to list for reporting (limit to avoid huge reports)
            duplicate_groups = duplicate_info.head(10).to_dict('records')
        
        return {
            'status': 'success',
            'original_row_count': original_row_count,
            'final_row_count': final_row_count,
            'duplicate_count': duplicate_count,
            'rows_removed': rows_removed,
            'duplicate_percentage': (duplicate_count / original_row_count) * 100 if original_row_count > 0 else 0,
            'removal_strategy': strategy,
            'subset_columns': subset_columns or 'all columns',
            'cleaned_data': {
                'rows': cleaned_rows,
                'columns': columns
            },
            'duplicate_groups': duplicate_groups,
            'summary': f"Removed {rows_removed} duplicate rows using '{strategy}' strategy"
        }
        
    except Exception as e:
        logger.error(f"Error in remove_duplicates: {str(e)}")
        return {
            'status': 'error',
            'message': f"Failed to remove duplicates: {str(e)}"
        }


def analyze_duplicate_patterns(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze duplicate patterns to help choose the best removal strategy.
    
    Args:
        data: Dictionary containing the dataset information
        
    Returns:
        Dictionary with detailed duplicate pattern analysis
    """
    try:
        rows = data.get('rows', [])
        columns = data.get('columns', [])
        
        if not rows or not columns:
            return {
                'status': 'error',
                'message': 'Invalid data format - missing rows or columns'
            }
        
        df = pd.DataFrame(rows)
        
        # Overall duplicate analysis
        total_duplicates = df.duplicated().sum()
        total_unique = len(df) - total_duplicates
        
        # Column-wise duplicate analysis
        column_analysis = {}
        for column in columns:
            if column in df.columns:
                col_duplicates = df[column].duplicated().sum()
                col_unique = df[column].nunique()
                column_analysis[column] = {
                    'unique_values': int(col_unique),
                    'duplicate_values': int(col_duplicates),
                    'uniqueness_ratio': col_unique / len(df) if len(df) > 0 else 0
                }
        
        # Find most common duplicate patterns
        duplicate_patterns = []
        if total_duplicates > 0:
            duplicate_rows = df[df.duplicated(keep=False)]
            if len(duplicate_rows) > 0:
                # Group by all columns to find exact duplicate patterns
                pattern_counts = duplicate_rows.groupby(
                    duplicate_rows.columns.tolist()
                ).size().sort_values(ascending=False)
                
                # Convert top patterns to readable format
                for i, (pattern, count) in enumerate(pattern_counts.head(5).items()):
                    if isinstance(pattern, tuple):
                        pattern_dict = dict(zip(columns, pattern))
                    else:
                        pattern_dict = {'value': pattern}
                    
                    duplicate_patterns.append({
                        'pattern': pattern_dict,
                        'occurrences': int(count),
                        'rank': i + 1
                    })
        
        # Recommendations based on analysis
        recommendations = []
        if total_duplicates == 0:
            recommendations.append("No duplicates found - no action needed")
        elif total_duplicates < len(df) * 0.05:  # Less than 5%
            recommendations.append("Low duplicate rate - standard removal with 'first' strategy recommended")
        elif total_duplicates < len(df) * 0.20:  # Less than 20%
            recommendations.append("Moderate duplicates - review patterns and use 'first' or 'last' strategy")
        else:
            recommendations.append("High duplicate rate - investigate data source and consider 'all' strategy for complete removal")
        
        return {
            'status': 'success',
            'total_rows': len(df),
            'total_duplicates': int(total_duplicates),
            'total_unique': int(total_unique),
            'duplicate_percentage': (total_duplicates / len(df)) * 100 if len(df) > 0 else 0,
            'column_analysis': column_analysis,
            'duplicate_patterns': duplicate_patterns,
            'recommendations': recommendations
        }
        
    except Exception as e:
        logger.error(f"Error in analyze_duplicate_patterns: {str(e)}")
        return {
            'status': 'error',
            'message': f"Failed to analyze duplicate patterns: {str(e)}"
        }


def detect_outliers(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Detect outliers in numeric columns using multiple statistical methods.
    
    Args:
        data: Dictionary containing:
            - rows: List of row dictionaries
            - columns: List of column names
            - outlier_config: Optional dict with detection configuration
                Format: {
                    "method": "zscore|iqr|modified_zscore|isolation_forest",
                    "threshold": 3.0,  # for z-score methods
                    "columns": ["col1", "col2"]  # specific columns to analyze
                }
                
    Returns:
        Dictionary with outlier detection results
    """
    try:
        rows = data.get('rows', [])
        columns = data.get('columns', [])
        outlier_config = data.get('outlier_config', {})
        
        if not rows or not columns:
            return {
                'status': 'error',
                'message': 'Invalid data format - missing rows or columns'
            }
        
        # Convert to pandas DataFrame
        df = pd.DataFrame(rows)
        
        # Get configuration
        method = outlier_config.get('method', 'zscore')
        threshold = outlier_config.get('threshold', 3.0)
        target_columns = outlier_config.get('columns', None)
        
        # Filter to numeric columns only
        if target_columns:
            numeric_columns = [col for col in target_columns if col in df.columns and pd.api.types.is_numeric_dtype(df[col])]
        else:
            numeric_columns = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]
        
        if not numeric_columns:
            return {
                'status': 'warning',
                'message': 'No numeric columns found for outlier detection',
                'numeric_columns': [],
                'outlier_analysis': {}
            }
        
        outlier_analysis = {}
        total_outliers = 0
        
        for column in numeric_columns:
            column_data = df[column].dropna()
            
            if len(column_data) < 3:  # Need at least 3 points for meaningful outlier detection
                outlier_analysis[column] = {
                    'method': method,
                    'outlier_count': 0,
                    'outlier_percentage': 0.0,
                    'outlier_indices': [],
                    'outlier_values': [],
                    'statistics': {
                        'mean': float(column_data.mean()) if len(column_data) > 0 else None,
                        'std': float(column_data.std()) if len(column_data) > 0 else None,
                        'q1': None,
                        'q3': None,
                        'iqr': None
                    },
                    'message': 'Insufficient data for outlier detection'
                }
                continue
            
            # Apply selected method
            if method == 'zscore':
                outlier_mask, stats = _detect_outliers_zscore(column_data, threshold)
            elif method == 'modified_zscore':
                outlier_mask, stats = _detect_outliers_modified_zscore(column_data, threshold)
            elif method == 'iqr':
                outlier_mask, stats = _detect_outliers_iqr(column_data)
            else:
                return {
                    'status': 'error',
                    'message': f'Invalid method: {method}. Use "zscore", "modified_zscore", or "iqr"'
                }
            
            # Get outlier information
            outlier_indices = df[df[column].isin(column_data[outlier_mask])].index.tolist()
            outlier_values = column_data[outlier_mask].tolist()
            outlier_count = len(outlier_values)
            total_outliers += outlier_count
            
            outlier_analysis[column] = {
                'method': method,
                'threshold': threshold if method in ['zscore', 'modified_zscore'] else None,
                'outlier_count': outlier_count,
                'outlier_percentage': (outlier_count / len(column_data)) * 100,
                'outlier_indices': outlier_indices,
                'outlier_values': outlier_values,
                'statistics': stats
            }
        
        # Generate recommendations
        recommendations = _get_outlier_recommendations(outlier_analysis, total_outliers, len(df))
        
        return {
            'status': 'success',
            'total_rows': len(df),
            'numeric_columns': numeric_columns,
            'method': method,
            'total_outliers': total_outliers,
            'outlier_percentage': (total_outliers / len(df)) * 100 if len(df) > 0 else 0,
            'outlier_analysis': outlier_analysis,
            'recommendations': recommendations
        }
        
    except Exception as e:
        logger.error(f"Error in detect_outliers: {str(e)}")
        return {
            'status': 'error',
            'message': f"Failed to detect outliers: {str(e)}"
        }


def _detect_outliers_zscore(data: pd.Series, threshold: float = 3.0) -> Tuple[pd.Series, Dict]:
    """Detect outliers using Z-score method."""
    mean_val = data.mean()
    std_val = data.std()
    
    if std_val == 0:
        # No variation in data, no outliers
        return pd.Series([False] * len(data), index=data.index), {
            'mean': float(mean_val),
            'std': float(std_val),
            'threshold': threshold
        }
    
    z_scores = np.abs((data - mean_val) / std_val)
    outlier_mask = z_scores > threshold
    
    return outlier_mask, {
        'mean': float(mean_val),
        'std': float(std_val),
        'threshold': threshold,
        'max_zscore': float(z_scores.max()),
        'min_zscore': float(z_scores.min())
    }


def _detect_outliers_modified_zscore(data: pd.Series, threshold: float = 3.5) -> Tuple[pd.Series, Dict]:
    """Detect outliers using Modified Z-score method (using median)."""
    median_val = data.median()
    mad = np.median(np.abs(data - median_val))  # Median Absolute Deviation
    
    if mad == 0:
        # Use standard deviation if MAD is 0
        mad = data.std()
        if mad == 0:
            return pd.Series([False] * len(data), index=data.index), {
                'median': float(median_val),
                'mad': float(mad),
                'threshold': threshold
            }
    
    # Modified Z-score = 0.6745 * (x - median) / MAD
    modified_z_scores = np.abs(0.6745 * (data - median_val) / mad)
    outlier_mask = modified_z_scores > threshold
    
    return outlier_mask, {
        'median': float(median_val),
        'mad': float(mad),
        'threshold': threshold,
        'max_modified_zscore': float(modified_z_scores.max()),
        'min_modified_zscore': float(modified_z_scores.min())
    }


def _detect_outliers_iqr(data: pd.Series) -> Tuple[pd.Series, Dict]:
    """Detect outliers using Interquartile Range (IQR) method."""
    q1 = data.quantile(0.25)
    q3 = data.quantile(0.75)
    iqr = q3 - q1
    
    # Define outliers as values outside 1.5 * IQR from Q1 and Q3
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    
    outlier_mask = (data < lower_bound) | (data > upper_bound)
    
    return outlier_mask, {
        'q1': float(q1),
        'q3': float(q3),
        'iqr': float(iqr),
        'lower_bound': float(lower_bound),
        'upper_bound': float(upper_bound),
        'mean': float(data.mean()),
        'std': float(data.std())
    }


def _get_outlier_recommendations(analysis: Dict[str, Any], total_outliers: int, total_rows: int) -> List[str]:
    """Generate recommendations for handling outliers."""
    recommendations = []
    outlier_percentage = (total_outliers / total_rows) * 100 if total_rows > 0 else 0
    
    if total_outliers == 0:
        recommendations.append("No outliers detected - data appears clean")
    elif outlier_percentage < 1:
        recommendations.append("Very few outliers detected (<1%) - consider investigating individual cases")
    elif outlier_percentage < 5:
        recommendations.append("Low outlier rate (1-5%) - review outliers for data entry errors or genuine extreme values")
    elif outlier_percentage < 10:
        recommendations.append("Moderate outlier rate (5-10%) - consider domain expertise to determine treatment")
    else:
        recommendations.append("High outlier rate (>10%) - investigate data collection process and consider robust statistical methods")
    
    # Column-specific recommendations
    high_outlier_columns = []
    for column, info in analysis.items():
        if isinstance(info, dict) and info.get('outlier_percentage', 0) > 10:
            high_outlier_columns.append(column)
    
    if high_outlier_columns:
        recommendations.append(f"Columns with high outlier rates: {', '.join(high_outlier_columns)}")
    
    return recommendations


def remove_outliers(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Remove or cap outliers in the dataset.
    
    Args:
        data: Dictionary containing:
            - rows: List of row dictionaries
            - columns: List of column names
            - outlier_config: Dict with removal configuration
                Format: {
                    "method": "zscore|iqr|modified_zscore",
                    "threshold": 3.0,
                    "action": "remove|cap",  # remove rows or cap values
                    "columns": ["col1", "col2"]
                }
                
    Returns:
        Dictionary with outlier removal results and cleaned data
    """
    try:
        rows = data.get('rows', [])
        columns = data.get('columns', [])
        outlier_config = data.get('outlier_config', {})
        
        if not rows or not columns:
            return {
                'status': 'error',
                'message': 'Invalid data format - missing rows or columns'
            }
        
        # First detect outliers
        detection_result = detect_outliers(data)
        if detection_result['status'] != 'success':
            return detection_result
        
        # Convert to pandas DataFrame
        df = pd.DataFrame(rows)
        original_row_count = len(df)
        
        # Get configuration
        action = outlier_config.get('action', 'remove')
        
        outlier_removal_report = {}
        total_outliers_removed = 0
        total_values_capped = 0
        
        # Process each numeric column
        for column, outlier_info in detection_result['outlier_analysis'].items():
            if outlier_info['outlier_count'] == 0:
                outlier_removal_report[column] = {
                    'action': 'none',
                    'outliers_before': 0,
                    'outliers_after': 0,
                    'values_changed': 0
                }
                continue
            
            outlier_indices = outlier_info['outlier_indices']
            
            if action == 'remove':
                # Remove rows containing outliers
                df = df.drop(index=outlier_indices)
                values_changed = len(outlier_indices)
                total_outliers_removed += values_changed
                
            elif action == 'cap':
                # Cap outliers to boundary values
                if outlier_info['method'] == 'iqr':
                    stats = outlier_info['statistics']
                    lower_bound = stats['lower_bound']
                    upper_bound = stats['upper_bound']
                    
                    # Cap values
                    df.loc[df[column] < lower_bound, column] = lower_bound
                    df.loc[df[column] > upper_bound, column] = upper_bound
                    values_changed = outlier_info['outlier_count']
                    total_values_capped += values_changed
                    
                else:  # z-score methods
                    # Cap to mean ± (threshold * std)
                    stats = outlier_info['statistics']
                    if 'mean' in stats and 'std' in stats:
                        threshold = outlier_info.get('threshold', 3.0)
                        lower_bound = stats['mean'] - threshold * stats['std']
                        upper_bound = stats['mean'] + threshold * stats['std']
                        
                        df.loc[df[column] < lower_bound, column] = lower_bound
                        df.loc[df[column] > upper_bound, column] = upper_bound
                        values_changed = outlier_info['outlier_count']
                        total_values_capped += values_changed
                    else:
                        values_changed = 0
            else:
                return {
                    'status': 'error',
                    'message': f'Invalid action: {action}. Use "remove" or "cap"'
                }
            
            outlier_removal_report[column] = {
                'action': action,
                'outliers_before': outlier_info['outlier_count'],
                'outliers_after': 0 if action == 'remove' else outlier_info['outlier_count'],
                'values_changed': values_changed
            }
        
        # Convert back to dictionary format
        cleaned_rows = df.to_dict('records')
        final_row_count = len(cleaned_rows)
        
        return {
            'status': 'success',
            'original_row_count': original_row_count,
            'final_row_count': final_row_count,
            'rows_removed': original_row_count - final_row_count,
            'action_performed': action,
            'total_outliers_removed': total_outliers_removed,
            'total_values_capped': total_values_capped,
            'cleaned_data': {
                'rows': cleaned_rows,
                'columns': columns
            },
            'outlier_removal_report': outlier_removal_report,
            'summary': f"Processed outliers using '{action}' action: {total_outliers_removed + total_values_capped} changes made"
        }
        
    except Exception as e:
        logger.error(f"Error in remove_outliers: {str(e)}")
        return {
            'status': 'error',
            'message': f"Failed to remove outliers: {str(e)}"
        }


def generate_data_quality_report(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a comprehensive data quality report combining all analysis tools.
    
    Args:
        data: Dictionary containing the dataset information and optional configuration
        
    Returns:
        Dictionary with comprehensive data quality report
    """
    try:
        rows = data.get('rows', [])
        columns = data.get('columns', [])
        report_config = data.get('report_config', {})
        
        if not rows or not columns:
            return {
                'status': 'error',
                'message': 'Invalid data format - missing rows or columns'
            }
        
        # Initialize report structure
        quality_report = {
            'status': 'success',
            'dataset_overview': {
                'total_rows': len(rows),
                'total_columns': len(columns),
                'column_names': columns
            },
            'quality_analysis': {},
            'recommendations': [],
            'overall_score': 0.0,
            'summary': {}
        }
        
        # 1. Missing Values Analysis
        missing_analysis = detect_missing_values(data)
        if missing_analysis['status'] == 'success':
            total_missing = sum(info['count'] for info in missing_analysis['missing_value_summary'].values())
            total_cells = len(rows) * len(columns)
            missing_percentage = (total_missing / total_cells) * 100 if total_cells > 0 else 0
            
            quality_report['quality_analysis']['missing_values'] = {
                'total_missing_cells': total_missing,
                'missing_percentage': missing_percentage,
                'columns_with_missing': len([col for col, info in missing_analysis['missing_value_summary'].items() if info['count'] > 0]),
                'detailed_analysis': missing_analysis['missing_value_summary'],
                'recommendations': missing_analysis.get('recommendations', [])
            }
            quality_report['recommendations'].extend(missing_analysis.get('recommendations', []))
        
        # 2. Duplicate Analysis
        duplicate_analysis = detect_duplicates(data)
        if duplicate_analysis['status'] == 'success':
            quality_report['quality_analysis']['duplicates'] = {
                'total_duplicates': duplicate_analysis['duplicate_count'],
                'duplicate_percentage': duplicate_analysis['duplicate_percentage'],
                'unique_rows': duplicate_analysis['unique_rows'],
                'recommendations': duplicate_analysis.get('recommendations', [])
            }
            quality_report['recommendations'].extend(duplicate_analysis.get('recommendations', []))
        
        # 3. Outlier Analysis (for numeric columns only)
        numeric_columns = []
        for column in columns:
            column_values = [row.get(column) for row in rows if row.get(column) is not None]
            if column_values and all(isinstance(v, (int, float)) or (isinstance(v, str) and v.replace('.', '', 1).isdigit()) for v in column_values):
                numeric_columns.append(column)
        
        if numeric_columns:
            outlier_analysis = detect_outliers(data)
            if outlier_analysis['status'] == 'success':
                total_outliers = sum(info['outlier_count'] for info in outlier_analysis['outlier_analysis'].values())
                total_numeric_values = sum(len([row.get(col) for row in rows if row.get(col) is not None]) for col in numeric_columns)
                outlier_percentage = (total_outliers / total_numeric_values) * 100 if total_numeric_values > 0 else 0
                
                quality_report['quality_analysis']['outliers'] = {
                    'total_outliers': total_outliers,
                    'outlier_percentage': outlier_percentage,
                    'numeric_columns_analyzed': len(numeric_columns),
                    'columns_with_outliers': len([col for col, info in outlier_analysis['outlier_analysis'].items() if info['outlier_count'] > 0]),
                    'detailed_analysis': outlier_analysis['outlier_analysis'],
                    'recommendations': outlier_analysis.get('recommendations', [])
                }
                quality_report['recommendations'].extend(outlier_analysis.get('recommendations', []))
        
        # 4. Data Type Analysis
        type_analysis = validate_data_types(data)
        if type_analysis['status'] == 'success':
            type_mismatches = 0
            for col, info in type_analysis['type_analysis'].items():
                if info['current_type'] != info['recommended_type']:
                    type_mismatches += 1
            
            quality_report['quality_analysis']['data_types'] = {
                'columns_analyzed': len(columns),
                'type_mismatches': type_mismatches,
                'optimization_potential': (type_mismatches / len(columns)) * 100 if len(columns) > 0 else 0,
                'detailed_analysis': type_analysis['type_analysis'],
                'recommendations': [type_analysis.get('recommendations', '')]
            }
            if type_analysis.get('recommendations'):
                quality_report['recommendations'].append(type_analysis['recommendations'])
        
        # 5. Calculate Overall Quality Score
        score_components = []
        
        # Missing values score (0-25 points)
        if 'missing_values' in quality_report['quality_analysis']:
            missing_pct = quality_report['quality_analysis']['missing_values']['missing_percentage']
            missing_score = max(0, 25 - (missing_pct / 2))  # Lose 0.5 points per 1% missing
            score_components.append(missing_score)
        
        # Duplicates score (0-25 points)
        if 'duplicates' in quality_report['quality_analysis']:
            duplicate_pct = quality_report['quality_analysis']['duplicates']['duplicate_percentage']
            duplicate_score = max(0, 25 - duplicate_pct)  # Lose 1 point per 1% duplicates
            score_components.append(duplicate_score)
        
        # Outliers score (0-25 points)
        if 'outliers' in quality_report['quality_analysis']:
            outlier_pct = quality_report['quality_analysis']['outliers']['outlier_percentage']
            outlier_score = max(0, 25 - (outlier_pct / 2))  # Lose 0.5 points per 1% outliers
            score_components.append(outlier_score)
        
        # Data types score (0-25 points)
        if 'data_types' in quality_report['quality_analysis']:
            type_optimization_pct = quality_report['quality_analysis']['data_types']['optimization_potential']
            type_score = max(0, 25 - (type_optimization_pct / 4))  # Lose 0.25 points per 1% type mismatch
            score_components.append(type_score)
        
        quality_report['overall_score'] = sum(score_components) if score_components else 0.0
        
        # 6. Generate Summary
        quality_level = "Excellent" if quality_report['overall_score'] >= 90 else \
                       "Good" if quality_report['overall_score'] >= 75 else \
                       "Fair" if quality_report['overall_score'] >= 60 else \
                       "Poor"
        
        quality_report['summary'] = {
            'quality_level': quality_level,
            'score': quality_report['overall_score'],
            'total_issues': len(quality_report['recommendations']),
            'priority_actions': quality_report['recommendations'][:3] if quality_report['recommendations'] else [],
            'dataset_health': f"Dataset has {quality_level.lower()} quality with {len(quality_report['recommendations'])} recommended actions"
        }
        
        # 7. Optional detailed formatting
        include_detailed = report_config.get('include_detailed', True)
        if not include_detailed:
            # Remove detailed analysis for summary report
            for analysis_type in quality_report['quality_analysis'].values():
                if 'detailed_analysis' in analysis_type:
                    del analysis_type['detailed_analysis']
        
        return quality_report
        
    except Exception as e:
        logger.error(f"Error in generate_data_quality_report: {str(e)}")
        return {
            'status': 'error',
            'message': f"Failed to generate data quality report: {str(e)}"
        }


def generate_cleaning_comparison_report(original_data: Dict[str, Any], cleaned_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a before/after comparison report for data cleaning operations.
    
    Args:
        original_data: Dictionary containing the original dataset
        cleaned_data: Dictionary containing the cleaned dataset
        
    Returns:
        Dictionary with before/after comparison report
    """
    try:
        # Generate reports for both datasets
        original_report = generate_data_quality_report(original_data)
        cleaned_report = generate_data_quality_report(cleaned_data)
        
        if original_report['status'] != 'success' or cleaned_report['status'] != 'success':
            return {
                'status': 'error',
                'message': 'Failed to generate comparison reports'
            }
        
        # Calculate improvements
        comparison_report = {
            'status': 'success',
            'comparison_summary': {
                'original_score': original_report['overall_score'],
                'cleaned_score': cleaned_report['overall_score'],
                'improvement': cleaned_report['overall_score'] - original_report['overall_score'],
                'improvement_percentage': ((cleaned_report['overall_score'] - original_report['overall_score']) / original_report['overall_score'] * 100) if original_report['overall_score'] > 0 else 0
            },
            'detailed_improvements': {},
            'cleaning_impact': {}
        }
        
        # Compare specific metrics
        metrics_to_compare = ['missing_values', 'duplicates', 'outliers', 'data_types']
        
        for metric in metrics_to_compare:
            if metric in original_report['quality_analysis'] and metric in cleaned_report['quality_analysis']:
                original_metric = original_report['quality_analysis'][metric]
                cleaned_metric = cleaned_report['quality_analysis'][metric]
                
                comparison_report['detailed_improvements'][metric] = {
                    'before': original_metric,
                    'after': cleaned_metric
                }
                
                # Calculate specific improvements
                if metric == 'missing_values':
                    missing_reduction = original_metric['total_missing_cells'] - cleaned_metric['total_missing_cells']
                    comparison_report['cleaning_impact'][metric] = {
                        'cells_fixed': missing_reduction,
                        'percentage_improvement': ((original_metric['missing_percentage'] - cleaned_metric['missing_percentage']) / original_metric['missing_percentage'] * 100) if original_metric['missing_percentage'] > 0 else 0
                    }
                
                elif metric == 'duplicates':
                    duplicates_removed = original_metric['total_duplicates'] - cleaned_metric['total_duplicates']
                    comparison_report['cleaning_impact'][metric] = {
                        'duplicates_removed': duplicates_removed,
                        'percentage_improvement': ((original_metric['duplicate_percentage'] - cleaned_metric['duplicate_percentage']) / original_metric['duplicate_percentage'] * 100) if original_metric['duplicate_percentage'] > 0 else 0
                    }
                
                elif metric == 'outliers':
                    outliers_handled = original_metric['total_outliers'] - cleaned_metric['total_outliers']
                    comparison_report['cleaning_impact'][metric] = {
                        'outliers_handled': outliers_handled,
                        'percentage_improvement': ((original_metric['outlier_percentage'] - cleaned_metric['outlier_percentage']) / original_metric['outlier_percentage'] * 100) if original_metric['outlier_percentage'] > 0 else 0
                    }
        
        # Dataset size comparison
        original_rows = original_report['dataset_overview']['total_rows']
        cleaned_rows = cleaned_report['dataset_overview']['total_rows']
        
        comparison_report['dataset_changes'] = {
            'rows_before': original_rows,
            'rows_after': cleaned_rows,
            'rows_removed': original_rows - cleaned_rows,
            'retention_rate': (cleaned_rows / original_rows * 100) if original_rows > 0 else 0
        }
        
        return comparison_report
        
    except Exception as e:
        logger.error(f"Error in generate_cleaning_comparison_report: {str(e)}")
        return {
            'status': 'error',
            'message': f"Failed to generate cleaning comparison report: {str(e)}"
        }


class DataCleanerAgent:
    """
    Data Cleaner Agent using Google ADK.
    
    This agent handles data quality assessment and preprocessing using Google ADK
    architecture with function tools for missing values, duplicates, and data validation.
    """
    
    def __init__(self, model: str = "gemini-2.0-flash-exp"):
        """
        Initialize the Data Cleaner Agent.
        
        Args:
            model: The LLM model to use for the agent
        """
        # Create function tools
        self.missing_values_tool = FunctionTool(func=detect_missing_values)
        self.imputation_tool = FunctionTool(func=impute_missing_values)
        self.duplicates_tool = FunctionTool(func=detect_duplicates)
        self.remove_duplicates_tool = FunctionTool(func=remove_duplicates)
        self.duplicate_analysis_tool = FunctionTool(func=analyze_duplicate_patterns)
        self.outlier_detection_tool = FunctionTool(func=detect_outliers)
        self.outlier_removal_tool = FunctionTool(func=remove_outliers)
        self.data_types_tool = FunctionTool(func=validate_data_types)
        self.quality_report_tool = FunctionTool(func=generate_data_quality_report)
        self.comparison_report_tool = FunctionTool(func=generate_cleaning_comparison_report)
        
        self.agent = Agent(
            model=model,
            name="data_cleaner_agent",
            description="Specialized agent for data quality assessment and preprocessing. Analyzes datasets for missing values, duplicates, outliers, and data type optimization.",
            instruction="""You are the Data Cleaner Agent, responsible for ensuring data quality and preparing datasets for analysis.

Your capabilities include:
1. Missing Value Analysis: Detect and analyze missing values, providing recommendations for handling them
2. Missing Value Imputation: Clean datasets by imputing missing values using various strategies (mean, median, mode, forward/backward fill, custom values)
3. Duplicate Detection: Identify duplicate rows and recommend deduplication strategies
4. Duplicate Removal: Remove duplicate rows using configurable strategies (first, last, all)
5. Duplicate Pattern Analysis: Analyze duplicate patterns to recommend optimal removal strategies
6. Outlier Detection: Identify outliers using statistical methods (Z-score, Modified Z-score, IQR)
7. Outlier Removal: Remove or cap outliers using configurable strategies
8. Data Type Validation: Analyze column data types and recommend optimizations
9. Data Quality Reporting: Generate comprehensive data quality reports and before/after cleaning comparisons

Always provide detailed analysis with actionable recommendations. When processing data:
- Use detect_missing_values to analyze missing data patterns
- Use impute_missing_values to clean data by filling missing values with appropriate strategies
- Use detect_duplicates to identify duplicate rows
- Use analyze_duplicate_patterns for detailed duplicate pattern analysis
- Use remove_duplicates to clean data by removing duplicate rows
- Use detect_outliers to identify outliers in numeric columns
- Use remove_outliers to clean data by removing or capping outlier values
- Use validate_data_types to recommend optimal data types
- Use generate_data_quality_report to create comprehensive quality assessments
- Use generate_cleaning_comparison_report to compare datasets before and after cleaning
- Provide clear, actionable recommendations for data cleaning

For missing value imputation:
- 'auto' strategy automatically selects the best method per column
- 'mean' for numeric columns with normal distribution
- 'median' for numeric columns with skewed distribution  
- 'mode' for categorical columns
- 'ffill'/'bfill' for time series data
- 'custom' with specific values when needed
- 'drop' to remove rows with missing values

For duplicate removal:
- 'first' strategy keeps the first occurrence of duplicates (default)
- 'last' strategy keeps the last occurrence of duplicates
- 'all' strategy removes all duplicate occurrences (keeps none)
- 'subset' parameter allows considering only specific columns for duplicates
- Use analyze_duplicate_patterns first to understand patterns and choose strategy

For outlier detection and removal:
- 'zscore' method uses standard Z-score (default threshold: 3.0)
- 'modified_zscore' method uses median-based Modified Z-score (default threshold: 3.5)
- 'iqr' method uses Interquartile Range (1.5 * IQR rule)
- 'remove' action removes entire rows containing outliers
- 'cap' action caps outlier values to boundary limits
- Focus on numeric columns only for outlier analysis

For data quality reporting:
- Use generate_data_quality_report for comprehensive quality analysis with overall scores
- Reports include missing values, duplicates, outliers, and data type analysis
- Overall quality score (0-100) based on weighted scoring across all dimensions
- Quality levels: Excellent (90+), Good (75-89), Fair (60-74), Poor (<60)
- Use generate_cleaning_comparison_report to compare datasets before and after cleaning
- Comparison reports show improvement metrics and cleaning impact

Be thorough in your analysis and explain the implications of data quality issues.""",
            tools=[
                self.missing_values_tool,
                self.imputation_tool,
                self.duplicates_tool,
                self.remove_duplicates_tool,
                self.duplicate_analysis_tool,
                self.outlier_detection_tool,
                self.outlier_removal_tool,
                self.data_types_tool,
                self.quality_report_tool,
                self.comparison_report_tool
            ]
        )
        
        logger.info("Data Cleaner Agent initialized successfully")
    
    def get_agent(self) -> Agent:
        """Return the ADK agent instance."""
        return self.agent 