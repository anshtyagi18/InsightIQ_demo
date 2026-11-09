"""
Trend Detector Agent

This agent identifies patterns, trends, and anomalies in time-series data.
Implements time-series decomposition, sliding window analysis, and anomaly detection
using Google ADK architecture.
"""

from typing import Dict, List, Any, Optional, Tuple, Union
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.ensemble import IsolationForest
from sklearn.svm import OneClassSVM
try:
    from statsmodels.tsa.seasonal import seasonal_decompose
except ImportError:
    seasonal_decompose = None
try:
    import matplotlib.pyplot as plt
    import seaborn as sns
except ImportError:
    plt = None
    sns = None
import logging
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Google ADK imports
from google.adk.agents import Agent
from google.adk.tools import FunctionTool
# from ..core.adk_config import adk_config  # Temporarily commented out

logger = logging.getLogger(__name__)


# Tool Functions for Google ADK Integration
def preprocess_timeseries_data_tool(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tool function: Preprocess time-series data including handling missing values and normalization.
    
    Args:
        data: Dictionary containing:
            - dataset: DataFrame-like structure with rows and datetime info
            - datetime_col: Name of the datetime column
            - value_cols: List of column names containing the values to analyze
            - config: Optional configuration dict with handle_missing and normalize settings
    
    Returns:
        Dictionary with preprocessing results
    """
    try:
        # Extract parameters
        dataset = data.get('dataset', {})
        datetime_col = data.get('datetime_col', 'date')
        value_cols = data.get('value_cols', [])
        config = data.get('config', {})
        
        handle_missing = config.get('handle_missing', 'interpolate')
        normalize = config.get('normalize', True)
        
        # Convert to DataFrame if needed
        if 'rows' in dataset and 'columns' in dataset:
            df = pd.DataFrame(dataset['rows'])
        else:
            return {'status': 'error', 'message': 'Invalid dataset format'}
        
        # Create TrendDetectorAgent instance for processing
        agent = TrendDetectorCore()
        processed_data = agent.preprocess_timeseries_data(
            df, datetime_col, value_cols, handle_missing, normalize
        )
        
        return {
            'status': 'success',
            'processed_data': {
                'rows': processed_data.reset_index().to_dict('records'),
                'columns': processed_data.columns.tolist(),
                'shape': processed_data.shape,
                'date_range': [str(processed_data.index.min()), str(processed_data.index.max())]
            },
            'preprocessing_info': {
                'missing_values_handled': True,
                'normalization_applied': normalize,
                'method_used': handle_missing
            }
        }
        
    except Exception as e:
        logger.error(f"Error in preprocess_timeseries_data_tool: {str(e)}")
        return {'status': 'error', 'message': f"Preprocessing failed: {str(e)}"}


def decompose_timeseries_tool(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tool function: Decompose time-series data into trend, seasonal, and residual components.
    
    Args:
        data: Dictionary containing:
            - series_data: Time series data with datetime index
            - model: Type of decomposition ('additive' or 'multiplicative')
            - period: Optional period for seasonal decomposition
    
    Returns:
        Dictionary with decomposition results
    """
    try:
        series_data = data.get('series_data', [])
        model = data.get('model', 'additive')
        period = data.get('period')
        
        # Convert to pandas Series
        if isinstance(series_data, list):
            df = pd.DataFrame(series_data)
            if 'date' in df.columns and 'value' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
                series = df['value']
            else:
                return {'status': 'error', 'message': 'Series data must have date and value columns'}
        else:
            return {'status': 'error', 'message': 'Invalid series data format'}
        
        # Create TrendDetectorAgent instance for processing
        agent = TrendDetectorCore()
        decomp_result = agent.decompose_timeseries(series, model, period)
        
        # Convert results to serializable format
        serializable_result = {}
        for component, series_data in decomp_result.items():
            serializable_result[component] = {
                'values': series_data.values.tolist(),
                'index': series_data.index.strftime('%Y-%m-%d').tolist(),
                'length': len(series_data)
            }
        
        return {
            'status': 'success',
            'decomposition': serializable_result,
            'model_used': model,
            'period_used': period
        }
        
    except Exception as e:
        logger.error(f"Error in decompose_timeseries_tool: {str(e)}")
        return {'status': 'error', 'message': f"Decomposition failed: {str(e)}"}


def detect_anomalies_tool(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tool function: Detect anomalies in time-series data using various methods.
    
    Args:
        data: Dictionary containing:
            - dataset: Time series data
            - method: Anomaly detection method
            - contamination: Expected proportion of outliers
            - use_residuals: Whether to use decomposition residuals
    
    Returns:
        Dictionary with anomaly detection results
    """
    try:
        dataset = data.get('dataset', {})
        method = data.get('method', 'isolation_forest')
        contamination = data.get('contamination', 0.1)
        use_residuals = data.get('use_residuals', False)
        
        # Convert to DataFrame
        if 'rows' in dataset:
            df = pd.DataFrame(dataset['rows'])
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
        else:
            return {'status': 'error', 'message': 'Invalid dataset format'}
        
        # Create TrendDetectorAgent instance for processing
        agent = TrendDetectorCore()
        anomaly_labels, anomaly_info = agent.detect_anomalies(
            df, method, contamination, use_residuals
        )
        
        return {
            'status': 'success',
            'anomaly_labels': anomaly_labels.tolist() if hasattr(anomaly_labels, 'tolist') else list(anomaly_labels),
            'anomaly_info': anomaly_info,
            'anomaly_summary': {
                'total_anomalies': anomaly_info.get('n_anomalies', 0),
                'anomaly_rate': anomaly_info.get('anomaly_rate', 0),
                'method_used': method,
                'contamination_used': contamination
            }
        }
        
    except Exception as e:
        logger.error(f"Error in detect_anomalies_tool: {str(e)}")
        return {'status': 'error', 'message': f"Anomaly detection failed: {str(e)}"}


def analyze_trends_tool(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tool function: Generate comprehensive trend analysis and correlation matrices.
    
    Args:
        data: Dictionary containing:
            - dataset: Preprocessed time-series data
            - value_cols: List of value columns to analyze
    
    Returns:
        Dictionary with trend analysis results
    """
    try:
        dataset = data.get('dataset', {})
        value_cols = data.get('value_cols', [])
        
        # Convert to DataFrame
        if 'rows' in dataset:
            df = pd.DataFrame(dataset['rows'])
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
        else:
            return {'status': 'error', 'message': 'Invalid dataset format'}
        
        # Create TrendDetectorAgent instance for processing
        agent = TrendDetectorCore()
        trend_results = agent.generate_trend_analysis(df, value_cols)
        
        return {
            'status': 'success',
            'trend_analysis': trend_results,
            'analysis_summary': {
                'columns_analyzed': value_cols,
                'correlations_computed': len(value_cols) > 1,
                'seasonality_assessed': 'seasonality_strength' in trend_results
            }
        }
        
    except Exception as e:
        logger.error(f"Error in analyze_trends_tool: {str(e)}")
        return {'status': 'error', 'message': f"Trend analysis failed: {str(e)}"}


def complete_timeseries_analysis_tool(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tool function: Perform complete end-to-end time-series analysis.
    
    Args:
        data: Dictionary containing:
            - dataset: Input dataset
            - datetime_col: Name of datetime column
            - value_cols: List of value columns to analyze
            - config: Optional configuration dictionary
    
    Returns:
        Dictionary with complete analysis results
    """
    try:
        dataset = data.get('dataset', {})
        datetime_col = data.get('datetime_col', 'date')
        value_cols = data.get('value_cols', [])
        config = data.get('config', {})
        
        # Convert to DataFrame
        if 'rows' in dataset:
            df = pd.DataFrame(dataset['rows'])
        else:
            return {'status': 'error', 'message': 'Invalid dataset format'}
        
        # Create TrendDetectorAgent instance for processing
        agent = TrendDetectorCore()
        results = agent.analyze_complete_timeseries(df, datetime_col, value_cols, config)
        
        return {
            'status': 'success',
            'complete_analysis': results,
            'analysis_metadata': {
                'datetime_column': datetime_col,
                'value_columns': value_cols,
                'config_used': config,
                'timestamp': datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error in complete_timeseries_analysis_tool: {str(e)}")
        return {'status': 'error', 'message': f"Complete analysis failed: {str(e)}"}


def analyze_trends_comprehensive(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Comprehensive trend analysis function for LangGraph orchestrator integration.
    
    This function provides a unified interface for the orchestrator to perform
    complete time-series analysis including preprocessing, decomposition,
    trend detection, and anomaly detection.
    
    Args:
        data: Dictionary containing:
            - rows: List of data rows
            - columns: List of column names
            - analysis_config: Configuration for analysis parameters
    
    Returns:
        Dictionary with comprehensive analysis results compatible with orchestrator
    """
    try:
        logger.info("Starting comprehensive trend analysis for orchestrator")
        
        # Extract data and configuration
        rows = data.get('rows', [])
        columns = data.get('columns', [])
        analysis_config = data.get('analysis_config', {})
        
        if not rows or not columns:
            return {
                'status': 'error',
                'message': 'Invalid data format - missing rows or columns'
            }
        
        # Convert to DataFrame
        df = pd.DataFrame(rows)
        
        # Auto-detect datetime and value columns
        datetime_col = None
        value_cols = []
        
        # Look for datetime column
        time_indicators = ['date', 'time', 'timestamp', 'datetime', 'period']
        for col in columns:
            if any(indicator in col.lower() for indicator in time_indicators):
                datetime_col = col
                break
        
        # Look for numeric value columns
        for col in columns:
            if col != datetime_col and col not in ['id', 'index']:
                # Check if column contains numeric data
                try:
                    sample_values = [row.get(col) for row in rows[:5] if row.get(col) is not None]
                    if sample_values and all(isinstance(v, (int, float)) or str(v).replace('.', '').isdigit() 
                                           for v in sample_values):
                        value_cols.append(col)
                except:
                    continue
        
        if not datetime_col:
            # If no datetime column found, create an index-based analysis
            logger.info("No datetime column detected, using row index for time-series analysis")
            df['_index_date'] = pd.date_range(start='2024-01-01', periods=len(df), freq='D')
            datetime_col = '_index_date'
        
        if not value_cols:
            return {
                'status': 'error',
                'message': 'No numeric value columns detected for trend analysis'
            }
        
        logger.info(f"Using datetime column: {datetime_col}, value columns: {value_cols}")
        
        # Create TrendDetectorCore instance
        trend_core = TrendDetectorCore()
        
        # Perform comprehensive analysis
        config = {
            'window_size': analysis_config.get('window_size', 7),
            'decomposition_model': analysis_config.get('decomposition_model', 'additive'),
            'anomaly_threshold': analysis_config.get('anomaly_threshold', 2.0),
            'handle_missing': 'interpolate',
            'normalize': True
        }
        
        complete_results = trend_core.analyze_complete_timeseries(
            df, datetime_col, value_cols, config
        )
        
        # Format results for orchestrator compatibility
        formatted_results = {
            'status': 'success',
            'analysis_summary': {
                'confidence_score': complete_results.get('trend_analysis', {}).get('overall_confidence', 0.7),
                'trends_detected': complete_results.get('trend_analysis', {}).get('detected_trends', []),
                'anomaly_count': complete_results.get('anomaly_analysis', {}).get('total_anomalies', 0),
                'data_quality': complete_results.get('preprocessing_info', {}).get('data_quality', 'good')
            },
            'time_series_analysis': {
                'has_temporal_patterns': len(value_cols) > 0 and datetime_col is not None,
                'trend_component': complete_results.get('decomposition', {}).get('trend_summary', {}),
                'seasonal_component': complete_results.get('decomposition', {}).get('seasonal_summary', {}),
                'residual_analysis': complete_results.get('decomposition', {}).get('residual_summary', {})
            },
            'trend_patterns': complete_results.get('trend_analysis', {}),
            'anomaly_detection': complete_results.get('anomaly_analysis', {}),
            'rolling_statistics': complete_results.get('rolling_analysis', {}),
            'preprocessing_info': complete_results.get('preprocessing_info', {}),
            'raw_analysis': complete_results
        }
        
        logger.info("Comprehensive trend analysis completed successfully")
        return formatted_results
        
    except Exception as e:
        logger.error(f"Error in analyze_trends_comprehensive: {str(e)}")
        return {
            'status': 'error',
            'message': f"Comprehensive trend analysis failed: {str(e)}",
            'analysis_summary': {
                'confidence_score': 0.0,
                'trends_detected': [],
                'anomaly_count': 0,
                'data_quality': 'error'
            }
        }


class TrendDetectorCore:
    """
    Core trend detection functionality - this contains all the original implementation
    without the ADK wrapper, so it can be used by the tool functions.
    """
    
    def __init__(self):
        """Initialize the core trend detector."""
        self.scaler = MinMaxScaler()
        self.decomposition_result = None
        self.anomaly_detector = None
        self.rolling_stats = {}
    
    def preprocess_timeseries_data(
        self, 
        data: pd.DataFrame, 
        datetime_col: str, 
        value_cols: List[str],
        handle_missing: str = 'interpolate',
        normalize: bool = True
    ) -> pd.DataFrame:
        """
        Preprocess time-series data including handling missing values and normalization.
        
        Args:
            data: Input DataFrame containing time-series data
            datetime_col: Name of the datetime column
            value_cols: List of column names containing the values to analyze
            handle_missing: Method to handle missing values ('interpolate', 'drop', 'forward_fill', 'backward_fill')
            normalize: Whether to normalize the data using MinMaxScaler
        
        Returns:
            Preprocessed DataFrame
        """
        logger.info("Starting time-series data preprocessing")
        
        # Create a copy to avoid modifying original data
        df = data.copy()
        
        # Ensure datetime column is properly formatted
        if datetime_col in df.columns:
            df[datetime_col] = pd.to_datetime(df[datetime_col])
            df = df.set_index(datetime_col)
        else:
            raise ValueError(f"Datetime column '{datetime_col}' not found in data")
        
        # Sort by datetime index
        df = df.sort_index()
        
        # Handle missing values
        initial_missing = df[value_cols].isnull().sum().sum()
        logger.info(f"Found {initial_missing} missing values")
        
        for col in value_cols:
            if handle_missing == 'interpolate':
                df[col] = df[col].interpolate(method='time')
            elif handle_missing == 'drop':
                df = df.dropna(subset=[col])
            elif handle_missing == 'forward_fill':
                df[col] = df[col].fillna(method='ffill')
            elif handle_missing == 'backward_fill':
                df[col] = df[col].fillna(method='bfill')
            else:
                raise ValueError(f"Unknown missing value handling method: {handle_missing}")
        
        # Remove any remaining NaN values
        df = df.dropna(subset=value_cols)
        
        final_missing = df[value_cols].isnull().sum().sum()
        logger.info(f"After preprocessing: {final_missing} missing values remain")
        
        # Normalize data if requested
        if normalize:
            logger.info("Normalizing data using MinMaxScaler")
            for col in value_cols:
                df[f'{col}_normalized'] = self.scaler.fit_transform(df[[col]])
        
        logger.info(f"Preprocessing complete. Data shape: {df.shape}")
        return df
    
    def decompose_timeseries(
        self, 
        data: pd.Series, 
        model: str = 'additive',
        period: Optional[int] = None
    ) -> Dict[str, pd.Series]:
        """
        Decompose time-series data into trend, seasonal, and residual components.
        
        Args:
            data: Time-series data as pandas Series
            model: Type of decomposition ('additive' or 'multiplicative')
            period: Period for seasonal decomposition (auto-detected if None)
        
        Returns:
            Dictionary containing trend, seasonal, and residual components
        """
        logger.info("Starting time-series decomposition")
        
        # Auto-detect period if not provided
        if period is None:
            # Try to infer frequency
            freq = pd.infer_freq(data.index)
            if freq:
                if 'D' in freq:  # Daily data
                    period = 365 if len(data) > 730 else 7
                elif 'H' in freq:  # Hourly data
                    period = 24
                elif 'M' in freq:  # Monthly data
                    period = 12
                else:
                    period = min(52, len(data) // 2)  # Default fallback
            else:
                period = min(52, len(data) // 2)  # Default fallback
        
        logger.info(f"Using period: {period} for decomposition")
        
        # Perform decomposition
        try:
            decomposition = seasonal_decompose(
                data, 
                model=model, 
                period=period,
                extrapolate_trend='freq'
            )
            
            self.decomposition_result = {
                'trend': decomposition.trend,
                'seasonal': decomposition.seasonal,
                'residual': decomposition.resid,
                'observed': decomposition.observed
            }
            
            logger.info("Time-series decomposition completed successfully")
            return self.decomposition_result
            
        except Exception as e:
            logger.error(f"Decomposition failed: {str(e)}")
            raise
    
    def sliding_window_analysis(
        self, 
        data: pd.Series, 
        window_sizes: List[int] = None,
        statistics: List[str] = None
    ) -> Dict[str, pd.DataFrame]:
        """
        Implement sliding window analysis to compute rolling statistics.
        
        Args:
            data: Time-series data as pandas Series
            window_sizes: List of window sizes to compute rolling statistics
            statistics: List of statistics to compute ('mean', 'std', 'var', 'min', 'max')
        
        Returns:
            Dictionary containing rolling statistics for each window size
        """
        logger.info("Starting sliding window analysis")
        
        if window_sizes is None:
            # Auto-determine window sizes based on data frequency and length
            data_length = len(data)
            if data_length > 1000:
                window_sizes = [7, 30, 90, 365]  # Daily data windows
            elif data_length > 100:
                window_sizes = [5, 10, 20, 50]
            else:
                window_sizes = [3, 5, 10]
        
        if statistics is None:
            statistics = ['mean', 'std', 'var', 'min', 'max']
        
        rolling_results = {}
        
        for window_size in window_sizes:
            if window_size >= len(data):
                logger.warning(f"Window size {window_size} is larger than data length {len(data)}, skipping")
                continue
                
            logger.info(f"Computing rolling statistics for window size: {window_size}")
            
            rolling_data = {}
            rolling_obj = data.rolling(window=window_size, min_periods=1)
            
            for stat in statistics:
                if hasattr(rolling_obj, stat):
                    rolling_data[f'{stat}'] = getattr(rolling_obj, stat)()
                else:
                    logger.warning(f"Statistic '{stat}' not available for rolling computation")
            
            rolling_results[f'window_{window_size}'] = pd.DataFrame(rolling_data)
        
        self.rolling_stats = rolling_results
        logger.info(f"Sliding window analysis completed for {len(rolling_results)} window sizes")
        return rolling_results
    
    def detect_anomalies(
        self, 
        data: Union[pd.Series, pd.DataFrame],
        method: str = 'isolation_forest',
        contamination: float = 0.1,
        use_residuals: bool = True
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Detect anomalies in time-series data using statistical methods or machine learning.
        
        Args:
            data: Time-series data
            method: Anomaly detection method ('isolation_forest', 'one_class_svm', 'statistical')
            contamination: Expected proportion of outliers
            use_residuals: Whether to use residuals from decomposition for anomaly detection
        
        Returns:
            Tuple of (anomaly_labels, anomaly_info)
        """
        logger.info(f"Starting anomaly detection using method: {method}")
        
        # Prepare data for anomaly detection
        if use_residuals and self.decomposition_result is not None:
            logger.info("Using residuals from decomposition for anomaly detection")
            analysis_data = self.decomposition_result['residual'].dropna()
        else:
            analysis_data = data
        
        # Convert to DataFrame if Series
        if isinstance(analysis_data, pd.Series):
            analysis_data = analysis_data.to_frame()
        
        # Remove any remaining NaN values
        analysis_data = analysis_data.dropna()
        
        if len(analysis_data) == 0:
            logger.error("No data available for anomaly detection")
            return np.array([]), {}
        
        anomaly_info = {
            'method': method,
            'contamination': contamination,
            'data_points': len(analysis_data)
        }
        
        try:
            if method == 'isolation_forest':
                detector = IsolationForest(
                    contamination=contamination,
                    random_state=42,
                    n_estimators=100
                )
                anomaly_labels = detector.fit_predict(analysis_data)
                anomaly_info['anomaly_score'] = detector.decision_function(analysis_data)
                
            elif method == 'one_class_svm':
                detector = OneClassSVM(
                    nu=contamination,
                    kernel='rbf',
                    gamma='scale'
                )
                anomaly_labels = detector.fit_predict(analysis_data)
                anomaly_info['anomaly_score'] = detector.decision_function(analysis_data)
                
            elif method == 'statistical':
                # Statistical anomaly detection using z-score
                z_scores = np.abs((analysis_data - analysis_data.mean()) / analysis_data.std())
                threshold = 3  # 3-sigma rule
                anomaly_labels = np.where(z_scores.max(axis=1) > threshold, -1, 1)
                anomaly_info['z_scores'] = z_scores
                anomaly_info['threshold'] = threshold
                
            else:
                raise ValueError(f"Unknown anomaly detection method: {method}")
            
            self.anomaly_detector = detector if method != 'statistical' else None
            
            # Convert -1 (anomaly) and 1 (normal) to boolean array
            anomalies = anomaly_labels == -1
            n_anomalies = np.sum(anomalies)
            
            anomaly_info['n_anomalies'] = n_anomalies
            anomaly_info['anomaly_rate'] = n_anomalies / len(anomaly_labels)
            
            logger.info(f"Anomaly detection completed. Found {n_anomalies} anomalies ({anomaly_info['anomaly_rate']:.2%})")
            
            return anomaly_labels, anomaly_info
            
        except Exception as e:
            logger.error(f"Anomaly detection failed: {str(e)}")
            raise
    
    def generate_trend_analysis(
        self, 
        data: pd.DataFrame,
        value_cols: List[str]
    ) -> Dict[str, Any]:
        """
        Generate comprehensive trend analysis and correlation matrices.
        
        Args:
            data: Preprocessed time-series data
            value_cols: List of value columns to analyze
        
        Returns:
            Dictionary containing trend analysis results
        """
        logger.info("Generating trend analysis and correlation matrices")
        
        analysis_results = {
            'correlation_matrix': {},
            'trend_summary': {},
            'seasonality_strength': {},
            'volatility_analysis': {}
        }
        
        # Correlation analysis
        if len(value_cols) > 1:
            correlation_matrix = data[value_cols].corr()
            analysis_results['correlation_matrix'] = correlation_matrix.to_dict()
            logger.info("Correlation matrix computed")
        
        # Individual trend analysis for each column
        for col in value_cols:
            if col in data.columns:
                series_data = data[col].dropna()
                
                # Basic trend statistics
                trend_stats = {
                    'mean': float(series_data.mean()),
                    'std': float(series_data.std()),
                    'min': float(series_data.min()),
                    'max': float(series_data.max()),
                    'trend_direction': 'increasing' if series_data.iloc[-1] > series_data.iloc[0] else 'decreasing',
                    'total_change': float(series_data.iloc[-1] - series_data.iloc[0]),
                    'percent_change': float((series_data.iloc[-1] - series_data.iloc[0]) / series_data.iloc[0] * 100)
                }
                
                analysis_results['trend_summary'][col] = trend_stats
                
                # Volatility analysis
                volatility = {
                    'daily_volatility': float(series_data.pct_change().std()),
                    'coefficient_of_variation': float(series_data.std() / series_data.mean()) if series_data.mean() != 0 else 0
                }
                analysis_results['volatility_analysis'][col] = volatility
        
        # Seasonality strength analysis (if decomposition was performed)
        if self.decomposition_result is not None:
            seasonal_component = self.decomposition_result['seasonal']
            residual_component = self.decomposition_result['residual']
            
            if seasonal_component is not None and residual_component is not None:
                seasonal_var = seasonal_component.var()
                residual_var = residual_component.var()
                seasonality_strength = seasonal_var / (seasonal_var + residual_var)
                
                analysis_results['seasonality_strength'] = {
                    'strength': float(seasonality_strength),
                    'interpretation': 'strong' if seasonality_strength > 0.6 else 'moderate' if seasonality_strength > 0.3 else 'weak'
                }
        
        logger.info("Trend analysis completed")
        return analysis_results
    
    def create_visualizations(
        self, 
        data: pd.DataFrame,
        value_cols: List[str],
        save_path: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Create visualizations for trend analysis.
        
        Args:
            data: Time-series data
            value_cols: List of value columns to visualize
            save_path: Path to save plots (optional)
        
        Returns:
            Dictionary with plot information
        """
        logger.info("Creating trend analysis visualizations")
        
        plots_created = {}
        
        try:
            # Set up the plotting style
            plt.style.use('seaborn-v0_8')
            fig_size = (15, 12)
            
            # 1. Original time series plot
            plt.figure(figsize=fig_size)
            for col in value_cols:
                if col in data.columns:
                    plt.plot(data.index, data[col], label=col, alpha=0.8)
            plt.title('Time Series Data')
            plt.xlabel('Time')
            plt.ylabel('Values')
            plt.legend()
            plt.grid(True, alpha=0.3)
            if save_path:
                plt.savefig(f"{save_path}_timeseries.png", dpi=300, bbox_inches='tight')
            plots_created['timeseries'] = 'Time series plot created'
            plt.close()
            
            # 2. Decomposition plot (if available)
            if self.decomposition_result is not None:
                fig, axes = plt.subplots(4, 1, figsize=(15, 12))
                
                components = ['observed', 'trend', 'seasonal', 'residual']
                titles = ['Original', 'Trend', 'Seasonal', 'Residual']
                
                for i, (comp, title) in enumerate(zip(components, titles)):
                    if comp in self.decomposition_result:
                        axes[i].plot(self.decomposition_result[comp].index, 
                                   self.decomposition_result[comp].values)
                        axes[i].set_title(f'{title} Component')
                        axes[i].grid(True, alpha=0.3)
                
                plt.tight_layout()
                if save_path:
                    plt.savefig(f"{save_path}_decomposition.png", dpi=300, bbox_inches='tight')
                plots_created['decomposition'] = 'Decomposition plot created'
                plt.close()
            
            # 3. Correlation matrix heatmap
            if len(value_cols) > 1:
                plt.figure(figsize=(10, 8))
                correlation_matrix = data[value_cols].corr()
                sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', center=0, 
                           square=True, fmt='.2f', cbar_kws={'shrink': 0.8})
                plt.title('Correlation Matrix')
                if save_path:
                    plt.savefig(f"{save_path}_correlation.png", dpi=300, bbox_inches='tight')
                plots_created['correlation'] = 'Correlation heatmap created'
                plt.close()
            
            # 4. Rolling statistics plot (if available)
            if self.rolling_stats:
                for window_name, rolling_data in self.rolling_stats.items():
                    plt.figure(figsize=fig_size)
                    for stat in ['mean', 'std']:
                        if stat in rolling_data.columns:
                            plt.plot(rolling_data.index, rolling_data[stat], 
                                   label=f'{stat.capitalize()}', alpha=0.8)
                    plt.title(f'Rolling Statistics - {window_name}')
                    plt.xlabel('Time')
                    plt.ylabel('Values')
                    plt.legend()
                    plt.grid(True, alpha=0.3)
                    if save_path:
                        plt.savefig(f"{save_path}_rolling_{window_name}.png", dpi=300, bbox_inches='tight')
                    plots_created[f'rolling_{window_name}'] = f'Rolling statistics plot for {window_name} created'
                    plt.close()
            
            logger.info(f"Created {len(plots_created)} visualization plots")
            
        except Exception as e:
            logger.error(f"Error creating visualizations: {str(e)}")
            
        return plots_created
    
    def analyze_complete_timeseries(
        self, 
        data: pd.DataFrame,
        datetime_col: str,
        value_cols: List[str],
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Complete end-to-end time-series analysis.
        
        Args:
            data: Input DataFrame
            datetime_col: Name of datetime column
            value_cols: List of value columns to analyze
            config: Optional configuration dictionary
        
        Returns:
            Complete analysis results
        """
        logger.info("Starting complete time-series analysis")
        
        # Default configuration
        default_config = {
            'handle_missing': 'interpolate',
            'normalize': True,
            'decomposition_model': 'additive',
            'anomaly_method': 'isolation_forest',
            'contamination': 0.1,
            'create_visualizations': True,
            'save_plots': False
        }
        
        if config:
            default_config.update(config)
        config = default_config
        
        results = {
            'preprocessing': {},
            'decomposition': {},
            'rolling_analysis': {},
            'anomaly_detection': {},
            'trend_analysis': {},
            'visualizations': {},
            'metadata': {
                'analysis_timestamp': datetime.now().isoformat(),
                'config_used': config
            }
        }
        
        try:
            # 1. Preprocess data
            logger.info("Step 1: Preprocessing data")
            processed_data = self.preprocess_timeseries_data(
                data, datetime_col, value_cols,
                handle_missing=config['handle_missing'],
                normalize=config['normalize']
            )
            results['preprocessing'] = {
                'status': 'completed',
                'shape': processed_data.shape,
                'date_range': [str(processed_data.index.min()), str(processed_data.index.max())]
            }
            
            # 2. Time-series decomposition (use first value column)
            logger.info("Step 2: Time-series decomposition")
            main_col = value_cols[0]
            if main_col in processed_data.columns:
                decomp_result = self.decompose_timeseries(
                    processed_data[main_col],
                    model=config['decomposition_model']
                )
                results['decomposition'] = {
                    'status': 'completed',
                    'components': list(decomp_result.keys())
                }
            
            # 3. Sliding window analysis
            logger.info("Step 3: Sliding window analysis")
            rolling_result = self.sliding_window_analysis(processed_data[main_col])
            results['rolling_analysis'] = {
                'status': 'completed',
                'window_sizes': list(rolling_result.keys())
            }
            
            # 4. Anomaly detection
            logger.info("Step 4: Anomaly detection")
            anomaly_labels, anomaly_info = self.detect_anomalies(
                processed_data[value_cols],
                method=config['anomaly_method'],
                contamination=config['contamination']
            )
            results['anomaly_detection'] = {
                'status': 'completed',
                'anomaly_info': anomaly_info
            }
            
            # 5. Trend analysis
            logger.info("Step 5: Trend analysis")
            trend_results = self.generate_trend_analysis(processed_data, value_cols)
            results['trend_analysis'] = {
                'status': 'completed',
                'results': trend_results
            }
            
            # 6. Create visualizations
            if config['create_visualizations']:
                logger.info("Step 6: Creating visualizations")
                viz_results = self.create_visualizations(
                    processed_data, value_cols,
                    save_path='trend_analysis' if config['save_plots'] else None
                )
                results['visualizations'] = {
                    'status': 'completed',
                    'plots_created': viz_results
                }
            
            logger.info("Complete time-series analysis finished successfully")
            results['status'] = 'success'
            
        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}")
            results['status'] = 'failed'
            results['error'] = str(e)
        
        return results


class TrendDetectorAgent:
    """
    Trend Detector Agent using Google ADK with OpenRouter/DeepSeek integration.
    
    This agent handles time-series analysis including preprocessing, decomposition,
    sliding window analysis, anomaly detection, and trend analysis using Google ADK
    architecture with function tools.
    """
    
    def __init__(self, model: str = None):
        """
        Initialize the Trend Detector Agent.
        
        Args:
            model: The LLM model to use for the agent (defaults to configured model)
        """
        # Use configured model if none provided
        if model is None:
            model = adk_config.default_model
        
        # Create function tools
        self.preprocess_tool = FunctionTool(func=preprocess_timeseries_data_tool)
        self.decomposition_tool = FunctionTool(func=decompose_timeseries_tool)
        self.anomaly_detection_tool = FunctionTool(func=detect_anomalies_tool)
        self.trend_analysis_tool = FunctionTool(func=analyze_trends_tool)
        self.complete_analysis_tool = FunctionTool(func=complete_timeseries_analysis_tool)
        
        # Get model configuration
        model_config = adk_config.get_model_config()
        
        self.agent = Agent(
            model=model,
            name="trend_detector_agent",
            description="Specialized agent for time-series analysis and trend detection. Analyzes temporal data for patterns, anomalies, seasonality, and correlations using advanced statistical methods.",
            instruction=f"""You are the Trend Detector Agent, powered by {model_config.get('provider', 'Google')} AI, specialized in comprehensive time-series analysis and pattern detection.

Your capabilities include:

1. **Time-series Data Preprocessing**: Clean and prepare temporal data for analysis
   - Handle missing values using interpolation, forward/backward fill, or dropping strategies
   - Normalize data using MinMaxScaler for consistent analysis
   - Validate datetime columns and ensure proper temporal ordering
   - Support multiple value columns for multivariate analysis

2. **Time-series Decomposition**: Break down temporal data into fundamental components
   - Decompose series into trend, seasonal, and residual components
   - Auto-detect seasonal periods (daily, weekly, monthly, yearly patterns)
   - Support both additive and multiplicative decomposition models
   - Provide insights into underlying data structure and patterns

3. **Sliding Window Analysis**: Compute rolling statistics for trend detection
   - Calculate rolling statistics (mean, std, variance, min, max) across multiple window sizes
   - Adapt window sizes based on data characteristics and frequency
   - Identify short-term and long-term trend patterns
   - Support configurable window parameters for specific analysis needs

4. **Anomaly Detection**: Identify unusual patterns and outliers in temporal data
   - Multiple detection methods: IsolationForest, OneClassSVM, Statistical (Z-score)
   - Configurable contamination parameters for sensitivity tuning
   - Option to use decomposition residuals for more accurate detection
   - Comprehensive anomaly scoring and rate calculation

5. **Comprehensive Trend Analysis**: Generate detailed insights and correlations
   - Multi-variate correlation analysis and matrices
   - Detailed trend statistics (direction, magnitude, volatility)
   - Seasonality strength assessment and interpretation
   - Risk metrics and coefficient of variation calculations

6. **Complete End-to-End Analysis**: Full workflow from raw data to actionable insights
   - Configurable analysis pipelines with customizable parameters
   - JSON-serializable results for API integration
   - Comprehensive metadata and execution tracking
   - Support for both summary and detailed analysis modes

**Usage Guidelines:**
- Use `preprocess_timeseries_data_tool` to clean and prepare temporal data
- Use `decompose_timeseries_tool` to analyze underlying patterns and seasonality  
- Use `detect_anomalies_tool` to identify outliers and unusual patterns
- Use `analyze_trends_tool` for correlation analysis and trend insights
- Use `complete_timeseries_analysis_tool` for full end-to-end analysis workflows

**Input Format Expectations:**
- Datasets should contain 'rows' (list of records) and 'columns' (list of column names)
- Datetime columns should be properly formatted or convertible to datetime
- Value columns should be numeric for statistical analysis
- Configuration parameters are optional but enable fine-tuning of analysis

**Analysis Configuration Options:**
- Missing value handling: 'interpolate', 'drop', 'forward_fill', 'backward_fill'
- Decomposition models: 'additive', 'multiplicative'
- Anomaly detection methods: 'isolation_forest', 'one_class_svm', 'statistical'
- Contamination levels: 0.05-0.2 (5%-20% expected outlier rate)
- Normalization: Enable for consistent multi-series analysis

Always provide detailed analysis with actionable insights. Explain temporal patterns, highlight significant trends, and suggest follow-up analysis when appropriate. Use statistical evidence to support findings and recommend optimal parameters based on data characteristics.

Current model configuration: {model_config}""",
            tools=[
                self.preprocess_tool,
                self.decomposition_tool,
                self.anomaly_detection_tool,
                self.trend_analysis_tool,
                self.complete_analysis_tool
            ]
        )
        
        logger.info(f"Trend Detector Agent initialized successfully with {model_config.get('provider', 'Google')} model: {model}")
    
    def get_agent(self) -> Agent:
        """Return the ADK agent instance."""
        return self.agent


class TrendDetector:
    """
    Wrapper class for TrendDetectorCore to provide the expected interface for dashboard integration.
    This class maintains backward compatibility with existing code that expects a TrendDetector class
    with an analyze_data method.
    """
    
    def __init__(self):
        """Initialize the TrendDetector wrapper."""
        self.core = TrendDetectorCore()
        logger.info("TrendDetector wrapper initialized successfully")
    
    async def analyze_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze data using the core trend detection functionality.
        
        Args:
            data: Dictionary containing dataset information with 'rows' and 'columns'
            
        Returns:
            Dictionary with trend analysis results
        """
        try:
            # Convert data to DataFrame if needed
            if 'rows' in data and 'columns' in data:
                df = pd.DataFrame(data['rows'])
            elif isinstance(data, dict) and 'data' in data:
                df = pd.DataFrame(data['data'])
            else:
                # Try to convert the data directly
                df = pd.DataFrame(data)
            
            # Auto-detect datetime and value columns
            datetime_col = None
            value_cols = []
            
            # Find datetime column
            for col in df.columns:
                if any(keyword in col.lower() for keyword in ['date', 'time', 'timestamp']):
                    try:
                        pd.to_datetime(df[col])
                        datetime_col = col
                        break
                    except:
                        continue
            
            # Find numeric columns for analysis
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            value_cols = numeric_cols[:3]  # Limit to first 3 numeric columns
            
            # If no datetime column found, create a simple index-based one
            if datetime_col is None and len(df) > 1:
                df['auto_index'] = pd.date_range(start='2023-01-01', periods=len(df), freq='D')
                datetime_col = 'auto_index'
            
            # If no value columns found, try to find any numeric-like columns
            if not value_cols:
                for col in df.columns:
                    if col != datetime_col:
                        try:
                            df[col] = pd.to_numeric(df[col], errors='coerce')
                            if not df[col].isna().all():
                                value_cols.append(col)
                        except:
                            continue
                value_cols = value_cols[:3]  # Limit to 3 columns
            
            # If we still don't have the required columns, return basic analysis
            if not datetime_col or not value_cols:
                return {
                    'status': 'success',
                    'trends': [],
                    'summary': {
                        'total_trends': 0,
                        'data_quality': 'insufficient_temporal_data',
                        'message': 'No suitable datetime or numeric columns found for trend analysis'
                    },
                    'metadata': {
                        'columns_analyzed': len(df.columns),
                        'rows_analyzed': len(df),
                        'analysis_type': 'basic'
                    }
                }
            
            # Perform the complete time-series analysis
            analysis_result = self.core.analyze_complete_timeseries(
                df, datetime_col, value_cols
            )
            
            # Transform the results to match expected dashboard format
            trends = []
            if analysis_result.get('status') == 'success':
                trend_analysis = analysis_result.get('trend_analysis', {}).get('results', {})
                
                for col in value_cols:
                    if col in trend_analysis.get('correlation_matrix', {}):
                        trends.append({
                            'column': col,
                            'trend_direction': self._determine_trend_direction(df[col]),
                            'correlation_strength': trend_analysis.get('correlation_matrix', {}).get(col, {}).get(col, 1.0),
                            'volatility': trend_analysis.get('volatility', {}).get(col, 0.0),
                            'anomaly_count': analysis_result.get('anomaly_detection', {}).get('anomaly_info', {}).get('n_anomalies', 0)
                        })
            
            return {
                'status': 'success',
                'trends': trends,
                'summary': {
                    'total_trends': len(trends),
                    'data_quality': 'good' if analysis_result.get('status') == 'success' else 'fair',
                    'datetime_column': datetime_col,
                    'value_columns': value_cols,
                    'analysis_components': list(analysis_result.keys())
                },
                'detailed_analysis': analysis_result,
                'metadata': {
                    'analysis_timestamp': datetime.now().isoformat(),
                    'method_used': 'complete_timeseries_analysis'
                }
            }
            
        except Exception as e:
            logger.error(f"Error in analyze_data: {str(e)}")
            return {
                'status': 'error',
                'trends': [],
                'summary': {
                    'total_trends': 0,
                    'data_quality': 'error',
                    'error_message': str(e)
                },
                'metadata': {
                    'analysis_timestamp': datetime.now().isoformat(),
                    'error': str(e)
                }
            }
    
    def _determine_trend_direction(self, series: pd.Series) -> str:
        """
        Determine the overall trend direction of a time series.
        
        Args:
            series: Pandas series to analyze
            
        Returns:
            'increasing', 'decreasing', or 'stable'
        """
        try:
            # Calculate linear trend using simple slope
            x = np.arange(len(series))
            y = series.values
            
            # Remove NaN values
            mask = ~np.isnan(y)
            if mask.sum() < 2:
                return 'stable'
                
            x_clean = x[mask]
            y_clean = y[mask]
            
            # Calculate slope using least squares
            slope = np.polyfit(x_clean, y_clean, 1)[0]
            
            # Determine direction based on slope
            if slope > 0.01:  # Threshold for positive trend
                return 'increasing'
            elif slope < -0.01:  # Threshold for negative trend
                return 'decreasing'
            else:
                return 'stable'
                
        except Exception:
            return 'stable'