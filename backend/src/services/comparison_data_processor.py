"""
Comparison Data Processor

Handles intelligent data processing for comparison analysis including:
- Multi-format file support (Excel, CSV, JSON)
- Intelligent sheet detection and selection
- Data cleaning and normalization
- Type inference and conversion
- Missing data handling
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union, cast
import logging
import io
import json
from datetime import datetime
import re

logger = logging.getLogger(__name__)

class ComparisonDataProcessor:
    """
    Intelligent data processor for comparison analysis.
    Handles various data formats and automatically optimizes data for analysis.
    """
    
    def __init__(self):
        self.supported_formats = ['.xlsx', '.xls', '.csv', '.json', '.tsv']
        self.date_patterns = [
            r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
            r'\d{2}/\d{2}/\d{4}',  # MM/DD/YYYY
            r'\d{2}-\d{2}-\d{4}',  # MM-DD-YYYY
            r'\d{4}/\d{2}/\d{2}',  # YYYY/MM/DD
        ]
    
    async def process_file(self, contents: bytes, filename: str, 
                          sheet_name: Optional[str] = None) -> pd.DataFrame:
        """
        Process uploaded file into a clean DataFrame ready for analysis.
        
        Args:
            contents: File contents as bytes
            filename: Original filename
            sheet_name: Specific sheet name for Excel files
            
        Returns:
            Cleaned and processed DataFrame
        """
        try:
            logger.info(f"[DATA_PROCESSOR] Processing file: {filename}")
            
            # Determine file type and read accordingly
            df = await self._read_file_by_type(contents, filename, sheet_name)
            
            if df is None or df.empty:
                raise ValueError(f"Could not read data from {filename}")
            
            logger.info(f"[DATA_PROCESSOR] Initial shape: {df.shape}")
            
            # Clean and optimize the data
            df_cleaned = await self._clean_and_optimize_data(df, filename)
            
            logger.info(f"[DATA_PROCESSOR] Final shape: {df_cleaned.shape}")
            return df_cleaned
            
        except Exception as e:
            logger.error(f"[DATA_PROCESSOR] Error processing {filename}: {str(e)}")
            raise
    
    async def detect_excel_sheets(self, contents: bytes, filename: str) -> List[Dict[str, Any]]:
        """
        Detect and analyze all sheets in an Excel file.
        
        Returns:
            List of sheet information with metadata
        """
        try:
            if not filename.lower().endswith(('.xlsx', '.xls')):
                return []
            
            # Read Excel file to get sheet names
            excel_file = pd.ExcelFile(io.BytesIO(contents))
            sheet_info = []
            
            for sheet_name in excel_file.sheet_names:
                try:
                    # Read first few rows to analyze content
                    df_sample = pd.read_excel(io.BytesIO(contents), sheet_name=sheet_name, nrows=10)
                    
                    # Analyze sheet characteristics
                    analysis = await self._analyze_sheet_content(df_sample, sheet_name)
                    sheet_info.append({
                        'name': sheet_name,
                        'rows': len(df_sample),
                        'columns': len(df_sample.columns),
                        'numeric_columns': len(df_sample.select_dtypes(include=[np.number]).columns),
                        'data_density': df_sample.count().sum() / (len(df_sample) * len(df_sample.columns)),
                        'likely_type': analysis['likely_type'],
                        'confidence': analysis['confidence'],
                        'sample_columns': list(df_sample.columns)[:5]
                    })
                except Exception as e:
                    logger.warning(f"Could not analyze sheet {sheet_name}: {str(e)}")
                    sheet_info.append({
                        'name': sheet_name,
                        'error': str(e),
                        'likely_type': 'unknown',
                        'confidence': 0
                    })
            
            return sheet_info
            
        except Exception as e:
            logger.error(f"Error detecting Excel sheets: {str(e)}")
            return []
    
    async def find_best_sheet_match(self, sheet_info: List[Dict[str, Any]], 
                                  target_type: str) -> Optional[str]:
        """
        Find the best sheet match for estimated or actual data.
        
        Args:
            sheet_info: List of sheet information from detect_excel_sheets
            target_type: 'estimated' or 'actual'
            
        Returns:
            Best matching sheet name or None
        """
        try:
            # Keywords for different data types
            estimated_keywords = ['forecast', 'estimate', 'predicted', 'planned', 'budget', 'target', 'proj']
            actual_keywords = ['actual', 'real', 'result', 'outcome', 'performance', 'achieved']
            
            target_keywords = estimated_keywords if target_type == 'estimated' else actual_keywords
            
            best_match = None
            best_score = 0
            
            for sheet in sheet_info:
                if 'error' in sheet:
                    continue
                
                score = 0
                sheet_name_lower = sheet['name'].lower()
                
                # Check for keyword matches
                for keyword in target_keywords:
                    if keyword in sheet_name_lower:
                        score += 10
                
                # Prefer sheets with more numeric data
                score += sheet.get('numeric_columns', 0) * 2
                
                # Prefer sheets with higher data density
                score += sheet.get('data_density', 0) * 5
                
                # Prefer sheets with reasonable size
                rows = sheet.get('rows', 0)
                if 5 <= rows <= 1000:
                    score += 3
                
                if score > best_score:
                    best_score = score
                    best_match = sheet['name']
            
            logger.info(f"[DATA_PROCESSOR] Best {target_type} sheet match: {best_match} (score: {best_score})")
            return best_match
            
        except Exception as e:
            logger.error(f"Error finding best sheet match: {str(e)}")
            return None
    
    async def _read_file_by_type(self, contents: bytes, filename: str, 
                               sheet_name: Optional[str] = None) -> pd.DataFrame:
        """Read file based on its type and extension."""
        filename_lower = filename.lower()
        
        try:
            if filename_lower.endswith('.csv'):
                # Try different encodings and separators
                for encoding in ['utf-8', 'latin-1', 'cp1252']:
                    try:
                        content_str = contents.decode(encoding)
                        # Detect separator
                        separator = self._detect_csv_separator(content_str)
                        df = pd.read_csv(io.StringIO(content_str), sep=separator)
                        if not df.empty:
                            return df
                    except Exception:
                        continue
                raise ValueError("Could not read CSV file with any encoding")
                
            elif filename_lower.endswith(('.xlsx', '.xls')):
                if sheet_name:
                    return pd.read_excel(io.BytesIO(contents), sheet_name=sheet_name)
                else:
                    # Read first sheet by default
                    return pd.read_excel(io.BytesIO(contents))
                    
            elif filename_lower.endswith('.json'):
                content_str = contents.decode('utf-8')
                data = json.loads(content_str)
                return pd.DataFrame(data)
                
            elif filename_lower.endswith('.tsv'):
                content_str = contents.decode('utf-8')
                return pd.read_csv(io.StringIO(content_str), sep='\t')
                
            else:
                # Try to auto-detect format
                try:
                    # Try Excel first
                    return pd.read_excel(io.BytesIO(contents))
                except:
                    # Try CSV
                    content_str = contents.decode('utf-8')
                    separator = self._detect_csv_separator(content_str)
                    return pd.read_csv(io.StringIO(content_str), sep=separator)
                    
        except Exception as e:
            logger.error(f"Error reading file {filename}: {str(e)}")
            raise
    
    async def _clean_and_optimize_data(self, df: pd.DataFrame, filename: str) -> pd.DataFrame:
        """Clean and optimize DataFrame for comparison analysis."""
        try:
            df_clean = df.copy()
            
            # Remove completely empty rows and columns
            df_clean = df_clean.dropna(how='all').dropna(axis=1, how='all')
            
            # Clean column names
            df_clean.columns = [self._clean_column_name(col) for col in df_clean.columns]
            
            # Handle duplicate column names
            df_clean = self._handle_duplicate_columns(df_clean)
            
            # Intelligent type conversion
            df_clean = await self._intelligent_type_conversion(df_clean)
            
            # Handle missing values intelligently
            df_clean = await self._handle_missing_values(df_clean)
            
            # Remove rows that are likely headers or footers
            df_clean = self._remove_header_footer_rows(df_clean)
            
            return df_clean
            
        except Exception as e:
            logger.error(f"Error cleaning data: {str(e)}")
            return df
    
    def _clean_column_name(self, col_name: str) -> str:
        """Clean and standardize column names."""
        if pd.isna(col_name):
            return "Unnamed_Column"
        
        # Convert to string and clean
        clean_name = str(col_name).strip()
        
        # Remove special characters but keep underscores and spaces
        clean_name = re.sub(r'[^\w\s]', '', clean_name)
        
        # Replace multiple spaces with single space
        clean_name = re.sub(r'\s+', ' ', clean_name)
        
        # Replace spaces with underscores for consistency
        clean_name = clean_name.replace(' ', '_')
        
        return clean_name if clean_name else "Unnamed_Column"
    
    def _handle_duplicate_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Handle duplicate column names by adding suffixes."""
        columns = list(df.columns)
        seen = {}
        new_columns = []
        
        for col in columns:
            if col in seen:
                seen[col] += 1
                new_columns.append(f"{col}_{seen[col]}")
            else:
                seen[col] = 0
                new_columns.append(col)
        
        df.columns = new_columns
        return df
    
    async def _intelligent_type_conversion(self, df: pd.DataFrame) -> pd.DataFrame:
        """Intelligently convert column types based on content."""
        df_converted = df.copy()
        
        for col in df_converted.columns:
            try:
                # Skip if already numeric
                if pd.api.types.is_numeric_dtype(df_converted[col]):
                    continue
                
                # Try to convert to numeric
                numeric_series = cast(pd.Series, pd.to_numeric(df_converted[col], errors='coerce'))
                
                # If more than 70% of values can be converted to numeric, convert the column
                valid_numeric_ratio = numeric_series.notna().sum() / len(df_converted[col])
                if valid_numeric_ratio > 0.7:
                    df_converted[col] = numeric_series
                    logger.info(f"[DATA_PROCESSOR] Converted {col} to numeric ({valid_numeric_ratio:.1%} valid)")
                    continue
                
                # Try to convert to datetime
                if self._looks_like_date(cast(pd.Series, df_converted[col])):
                    try:
                        df_converted[col] = pd.to_datetime(df_converted[col], errors='coerce')
                        logger.info(f"[DATA_PROCESSOR] Converted {col} to datetime")
                        continue
                    except:
                        pass
                
                # Keep as string/object type
                df_converted[col] = df_converted[col].astype(str)
                
            except Exception as e:
                logger.warning(f"Error converting column {col}: {str(e)}")
                continue
        
        return df_converted
    
    async def _handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Handle missing values intelligently based on column type."""
        df_filled = df.copy()
        
        for col in df_filled.columns:
            try:
                if pd.api.types.is_numeric_dtype(df_filled[col]):
                    # For numeric columns, fill with median if less than 30% missing
                    missing_ratio = df_filled[col].isna().sum() / len(df_filled[col])
                    if 0 < missing_ratio < 0.3:
                        median_val = df_filled[col].median()
                        df_filled[col] = df_filled[col].fillna(median_val)
                        logger.info(f"[DATA_PROCESSOR] Filled {col} missing values with median: {median_val}")
                
                elif pd.api.types.is_datetime64_any_dtype(df_filled[col]):
                    # For datetime columns, forward fill
                    df_filled[col] = df_filled[col].fillna(method='ffill')
                
                # For string columns, keep NaN as is for now
                
            except Exception as e:
                logger.warning(f"Error handling missing values for {col}: {str(e)}")
                continue
        
        return df_filled
    
    def _remove_header_footer_rows(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove rows that look like headers or footers."""
        if len(df) <= 3:
            return df
        
        df_clean = df.copy()
        
        # Remove rows where all values are strings and look like headers
        for idx in df_clean.index:
            row = df_clean.loc[idx]
            
            # Check if row looks like a header (all strings, no numbers)
            if all(isinstance(val, str) and not self._is_numeric_string(val) for val in row if pd.notna(val)):
                # Check if this row has column-like names
                if any(keyword in str(val).lower() for val in row if pd.notna(val) 
                      for keyword in ['total', 'sum', 'average', 'mean', 'count']):
                    df_clean = df_clean.drop(idx)
                    logger.info(f"[DATA_PROCESSOR] Removed likely footer row at index {idx}")
        
        return df_clean
    
    def _detect_csv_separator(self, content: str) -> str:
        """Detect the most likely separator for CSV content."""
        separators = [',', ';', '\t', '|']
        separator_counts = {}
        
        # Check first few lines
        lines = content.split('\n')[:5]
        
        for sep in separators:
            count = sum(line.count(sep) for line in lines)
            separator_counts[sep] = count
        
        # Return separator with highest count
        best_sep = max(separator_counts.items(), key=lambda x: x[1])[0]
        return best_sep if separator_counts[best_sep] > 0 else ','
    
    def _looks_like_date(self, series: pd.Series) -> bool:
        """Check if a series looks like it contains dates."""
        if len(series) == 0:
            return False
        
        # Sample a few non-null values
        sample_values = series.dropna().head(5)
        
        date_like_count = 0
        for val in sample_values:
            val_str = str(val)
            for pattern in self.date_patterns:
                if re.search(pattern, val_str):
                    date_like_count += 1
                    break
        
        return date_like_count >= len(sample_values) * 0.6
    
    def _is_numeric_string(self, val: str) -> bool:
        """Check if a string represents a number."""
        try:
            float(val.replace(',', '').replace('$', '').replace('%', ''))
            return True
        except:
            return False
    
    async def _analyze_sheet_content(self, df: pd.DataFrame, sheet_name: str) -> Dict[str, Any]:
        """Analyze sheet content to determine its likely purpose."""
        try:
            sheet_name_lower = sheet_name.lower()
            
            # Keywords that suggest data type
            estimated_keywords = ['forecast', 'estimate', 'predicted', 'planned', 'budget', 'target']
            actual_keywords = ['actual', 'real', 'result', 'outcome', 'performance']
            
            confidence = 50  # Base confidence
            likely_type = 'data'
            
            # Check sheet name for keywords
            for keyword in estimated_keywords:
                if keyword in sheet_name_lower:
                    likely_type = 'estimated'
                    confidence += 30
                    break
            
            for keyword in actual_keywords:
                if keyword in sheet_name_lower:
                    likely_type = 'actual'
                    confidence += 30
                    break
            
            # Check column names for additional clues
            column_names = ' '.join(str(col).lower() for col in df.columns)
            
            if any(keyword in column_names for keyword in estimated_keywords):
                if likely_type == 'data':
                    likely_type = 'estimated'
                confidence += 20
            
            if any(keyword in column_names for keyword in actual_keywords):
                if likely_type == 'data':
                    likely_type = 'actual'
                confidence += 20
            
            # Boost confidence if sheet has good data characteristics
            numeric_ratio = len(df.select_dtypes(include=[np.number]).columns) / len(df.columns)
            if numeric_ratio > 0.3:
                confidence += 10
            
            return {
                'likely_type': likely_type,
                'confidence': min(confidence, 100)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing sheet content: {str(e)}")
            return {'likely_type': 'unknown', 'confidence': 0} 