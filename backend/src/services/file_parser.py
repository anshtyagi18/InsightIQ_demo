"""
File parser service for generating previews of uploaded files.
Supports CSV, Excel (xlsx, xls), and JSON files.
"""

import json
import pandas as pd
import numpy as np
import io
from typing import Dict, Any, List, Optional
from fastapi import HTTPException

class SmartJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles pandas/numpy special values."""
    
    def encode(self, obj):
        """Convert numpy/pandas special values to JSON-safe equivalents."""
        if isinstance(obj, dict):
            # Convert keys to strings if they're datetime objects
            new_obj = {}
            for k, v in obj.items():
                if hasattr(k, 'isoformat'):  # datetime key
                    new_key = k.isoformat()
                elif hasattr(k, 'strftime'):  # other datetime-like key
                    try:
                        new_key = k.isoformat()
                    except:
                        new_key = str(k)
                else:
                    new_key = k
                new_obj[new_key] = self._convert_value(v)
            obj = new_obj
        elif isinstance(obj, list):
            obj = [self._convert_value(item) for item in obj]
        else:
            obj = self._convert_value(obj)
        return super().encode(obj)
    
    def _convert_value(self, value):
        """Convert individual values to JSON-safe format."""
        # Handle datetime objects first
        if hasattr(value, 'isoformat'):  # datetime, date, time objects
            return value.isoformat()
        elif hasattr(value, 'strftime'):  # other datetime-like objects
            try:
                return value.isoformat()
            except:
                return str(value)
        
        # Handle numpy arrays and pandas Series
        if isinstance(value, (np.ndarray, pd.Series)):
            return [self._convert_value(item) for item in value]
        elif hasattr(value, '__len__') and hasattr(value, '__getitem__') and not isinstance(value, (str, dict)):
            # Handle other array-like objects (but not strings or dicts)
            try:
                return [self._convert_value(item) for item in value]
            except (TypeError, AttributeError):
                pass
        
        # Handle scalar values
        try:
            if pd.isna(value):
                return None
        except (TypeError, ValueError):
            # pd.isna can fail on certain types, so we'll check other conditions
            pass
            
        if isinstance(value, float) and (np.isnan(value) or np.isinf(value)):
            return None
        elif hasattr(value, 'item'):  # numpy scalar
            return value.item()
        elif isinstance(value, (np.integer, np.floating)):
            return float(value) if np.isfinite(value) else None
        elif isinstance(value, np.bool_):
            return bool(value)
        elif isinstance(value, dict):
            # Handle nested dictionaries with potential datetime keys
            new_dict = {}
            for k, v in value.items():
                if hasattr(k, 'isoformat'):  # datetime key
                    new_key = k.isoformat()
                elif hasattr(k, 'strftime'):  # other datetime-like key
                    try:
                        new_key = k.isoformat()
                    except:
                        new_key = str(k)
                else:
                    new_key = k
                new_dict[new_key] = self._convert_value(v)
            return new_dict
        elif isinstance(value, list):
            return [self._convert_value(item) for item in value]
        return value

class FileParserService:
    """Service for parsing files and generating previews."""
    
    @staticmethod
    def get_file_preview(content: bytes, filename: str, content_type: str, preview_rows: int = 5) -> Dict[str, Any]:
        """
        Generate a preview of the uploaded file.
        
        Args:
            content: File content as bytes
            filename: Original filename
            content_type: MIME type of the file
            preview_rows: Number of rows to include in preview (default: 5)
            
        Returns:
            Dictionary containing file preview and metadata
        """
        
        try:
            file_extension = filename.lower().split('.')[-1]
            
            if content_type == 'text/csv' or file_extension == 'csv':
                return FileParserService._parse_csv(content, preview_rows)
            
            elif content_type == 'application/json' or file_extension == 'json':
                return FileParserService._parse_json(content, preview_rows)
            
            elif file_extension in ['xlsx', 'xls'] or 'excel' in content_type or 'spreadsheet' in content_type:
                return FileParserService._parse_excel(content, preview_rows)
            
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported file type for preview: {file_extension}"
                )
                
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=422,
                detail=f"Error parsing file: {str(e)}"
            )
    
    @staticmethod
    def _clean_dataframe_for_json(df: pd.DataFrame) -> pd.DataFrame:
        """Clean DataFrame to ensure JSON serialization compatibility."""
        # Create a copy to avoid modifying the original
        df = df.copy()
        
        # Replace inf values with NaN first, then handle NaN
        df = df.replace([np.inf, -np.inf], np.nan)
        
        # Convert all numeric columns to ensure proper handling
        for col in df.select_dtypes(include=[np.number]).columns:
            # Replace NaN with None for JSON serialization
            df[col] = df[col].where(pd.notna(df[col]), None)
        
        # Convert any remaining problematic dtypes
        for col in df.columns:
            if df[col].dtype == 'object':
                # Check for mixed types that might cause issues
                try:
                    # Try to convert object columns with potential numpy values
                    df[col] = df[col].apply(lambda x: None if pd.isna(x) else x)
                except (TypeError, ValueError):
                    # If conversion fails, convert to string
                    df[col] = df[col].astype(str)
                    
        return df
    
    @staticmethod
    def _parse_csv(content: bytes, preview_rows: int) -> Dict[str, Any]:
        """Parse CSV file and return preview with intelligent cleaning."""
        try:
            # Convert bytes to string
            csv_string = content.decode('utf-8')
            encoding = "utf-8"
        except UnicodeDecodeError:
            csv_string = content.decode('latin-1')
            encoding = "latin-1"

        # Read CSV using pandas
        df = pd.read_csv(io.StringIO(csv_string))
        df_clean = FileParserService._clean_dataframe_for_json(df)

        # Run intelligent cleaning pipeline
        cleaning_result = None
        try:
            from backend.src.services.excel_cleaning_pipeline import ExcelCleaningPipeline
            pipeline = ExcelCleaningPipeline()
            cleaning_result = pipeline.process_file(content, filename="dataset.csv")
        except Exception as e:
            pass

        res = {
            "file_type": "CSV",
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "columns": df.columns.tolist(),
            "column_types": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "preview_rows": min(preview_rows, len(df)),
            "preview_data": df_clean.head(preview_rows).to_dict('records'),
            "has_header": True,
            "encoding": encoding,
            "data_quality": {
                "null_counts": df.isnull().sum().to_dict(),
                "infinity_counts": {col: np.isinf(df[col]).sum() if df[col].dtype in ['float64', 'float32'] else 0 
                                  for col in df.columns}
            }
        }

        if cleaning_result and cleaning_result.get("status") == "success":
            res["cleaning_report"] = {
                "cleanliness_score_before": cleaning_result["cleanliness_score_before"],
                "cleanliness_score_after": cleaning_result["cleanliness_score_after"],
                "summary": cleaning_result["summary"],
                "actions_taken": cleaning_result["actions_taken"],
                "issues_detected": cleaning_result["issues_detected"],
                "rows_before": cleaning_result["rows_before"],
                "rows_after": cleaning_result["rows_after"],
                "cols_before": cleaning_result["cols_before"],
                "cols_after": cleaning_result["cols_after"],
            }
            res["cleaned_preview"] = cleaning_result["preview_after"][:preview_rows]
            res["columns_profile"] = cleaning_result["columns"]
            res["is_analytics_ready"] = True

        return res

    @staticmethod
    def _parse_excel(content: bytes, preview_rows: int) -> Dict[str, Any]:
        """Parse Excel file and return preview with intelligent cleaning and layout detection."""
        import tempfile
        import os
        
        # Save to temporary file for analysis
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp_file:
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        layout_info = {
            'original_layout': 'standard',
            'transformations_applied': [],
            'detection_confidence': 50.0,
            'layout_normalized': False
        }

        try:
            # 1. First run intelligent cleaning pipeline on the Excel file
            cleaning_result = None
            try:
                from backend.src.services.excel_cleaning_pipeline import ExcelCleaningPipeline
                pipeline = ExcelCleaningPipeline()
                cleaning_result = pipeline.process_file(tmp_path, filename="uploaded.xlsx")
            except Exception as e:
                pass

            # 2. Also run layout analyzer if available
            try:
                from src.services.excel_layout_analyzer import ExcelLayoutAnalyzer
                analyzer = ExcelLayoutAnalyzer()
                normalized_result = analyzer.analyze_and_normalize(tmp_path)
                df = normalized_result.dataframe
                layout_info = {
                    'original_layout': normalized_result.original_layout,
                    'transformations_applied': normalized_result.transformations_applied,
                    'detection_confidence': normalized_result.confidence,
                    'layout_normalized': True
                }
            except Exception:
                # Fallback to standard pandas read if layout analyzer not available
                excel_file = pd.ExcelFile(io.BytesIO(content))
                first_sheet = excel_file.sheet_names[0] if excel_file.sheet_names else 'Sheet1'
                df = pd.read_excel(io.BytesIO(content), sheet_name=first_sheet)

        finally:
            # Clean up temporary file - original uploaded file remains intact
            try:
                os.unlink(tmp_path)
            except:
                pass
        
        # Get sheet info for response
        try:
            excel_file = pd.ExcelFile(io.BytesIO(content))
            sheet_names = excel_file.sheet_names
            first_sheet = sheet_names[0] if sheet_names else 'Sheet1'
        except Exception:
            sheet_names = ["Sheet1"]
            first_sheet = "Sheet1"
        
        # Clean the dataframe for JSON serialization
        df_clean = FileParserService._clean_dataframe_for_json(df)
        
        response_obj = {
            "file_type": "Excel",
            "sheet_names": sheet_names,
            "active_sheet": first_sheet,
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "columns": df.columns.tolist(),
            "column_types": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "preview_rows": min(preview_rows, len(df)),
            "preview_data": df_clean.head(preview_rows).to_dict('records'),
            "has_header": True,
            "data_quality": {
                "null_counts": df.isnull().sum().to_dict(),
                "infinity_counts": {col: np.isinf(df[col]).sum() if df[col].dtype in ['float64', 'float32'] else 0 
                                  for col in df.columns}
            },
            "layout_info": layout_info
        }

        # Attach intelligent cleaning report and analytics-ready dataset
        if cleaning_result and cleaning_result.get("status") == "success":
            response_obj["cleaning_report"] = {
                "cleanliness_score_before": cleaning_result["cleanliness_score_before"],
                "cleanliness_score_after": cleaning_result["cleanliness_score_after"],
                "summary": cleaning_result["summary"],
                "actions_taken": cleaning_result["actions_taken"],
                "issues_detected": cleaning_result["issues_detected"],
                "rows_before": cleaning_result["rows_before"],
                "rows_after": cleaning_result["rows_after"],
                "cols_before": cleaning_result["cols_before"],
                "cols_after": cleaning_result["cols_after"],
            }
            response_obj["cleaned_preview"] = cleaning_result["preview_after"][:preview_rows]
            response_obj["columns_profile"] = cleaning_result["columns"]
            response_obj["cleaned_data"] = cleaning_result["cleaned_data"]
            response_obj["is_analytics_ready"] = True

        return response_obj
    
    @staticmethod
    def _parse_json(content: bytes, preview_rows: int) -> Dict[str, Any]:
        """Parse JSON file and return preview."""
        # Parse JSON content
        json_string = content.decode('utf-8')
        data = json.loads(json_string)
        
        # Handle different JSON structures
        if isinstance(data, list):
            # Array of objects
            total_items = len(data)
            preview_data = data[:preview_rows]
            
            # If items are objects, analyze structure
            if data and isinstance(data[0], dict):
                # Get all unique keys from the first few items
                all_keys = set()
                for item in data[:min(10, len(data))]:
                    if isinstance(item, dict):
                        all_keys.update(item.keys())
                
                return {
                    "file_type": "JSON",
                    "structure_type": "array_of_objects",
                    "total_items": total_items,
                    "preview_items": min(preview_rows, total_items),
                    "preview_data": preview_data,
                    "detected_fields": list(all_keys)
                }
            else:
                # Array of primitives
                return {
                    "file_type": "JSON",
                    "structure_type": "array_of_primitives",
                    "total_items": total_items,
                    "preview_items": min(preview_rows, total_items),
                    "preview_data": preview_data
                }
        
        elif isinstance(data, dict):
            # Single object or nested structure
            return {
                "file_type": "JSON",
                "structure_type": "object",
                "keys": list(data.keys()),
                "preview_data": {k: v for i, (k, v) in enumerate(data.items()) if i < preview_rows}
            }
        
        else:
            # Primitive value
            return {
                "file_type": "JSON",
                "structure_type": "primitive",
                "data_type": type(data).__name__,
                "value": data
            } 


class FileParser:
    """
    Wrapper class for FileParserService to provide the expected interface for dashboard integration.
    """
    
    def __init__(self):
        """Initialize the FileParser wrapper."""
        self.service = FileParserService()
    
    async def parse_file(self, file) -> Dict[str, Any]:
        """
        Parse an uploaded file and return structured data.
        
        Args:
            file: FastAPI UploadFile object
            
        Returns:
            Dictionary with parsed data and metadata
        """
        try:
            # Read file content
            content = await file.read()
            
            # Get file preview/parsing results
            file_info = self.service.get_file_preview(
                content=content,
                filename=file.filename,
                content_type=file.content_type
            )
            
            # Convert to expected format for dashboard
            if file_info.get('file_type') in ['CSV', 'Excel']:
                # For structured data (CSV/Excel), return rows and columns format
                return {
                    'status': 'success',
                    'data': {
                        'rows': file_info.get('preview_data', []),
                        'columns': file_info.get('columns', []),
                        'total_rows': file_info.get('total_rows', 0),
                        'total_columns': file_info.get('total_columns', 0),
                        'file_type': file_info.get('file_type'),
                        'column_types': file_info.get('column_types', {})
                    },
                    'metadata': {
                        'filename': file.filename,
                        'content_type': file.content_type,
                        'file_size': len(content),
                        'encoding': file_info.get('encoding', 'utf-8'),
                        'has_header': file_info.get('has_header', True)
                    }
                }
            
            elif file_info.get('file_type') == 'JSON':
                # For JSON data, try to convert to rows/columns format
                preview_data = file_info.get('preview_data', [])
                
                if file_info.get('structure_type') == 'array_of_objects' and preview_data:
                    # Extract columns from first object
                    columns = list(preview_data[0].keys()) if preview_data else []
                    
                    return {
                        'status': 'success',
                        'data': {
                            'rows': preview_data,
                            'columns': columns,
                            'total_rows': file_info.get('total_items', len(preview_data)),
                            'total_columns': len(columns),
                            'file_type': 'JSON',
                            'structure_type': file_info.get('structure_type')
                        },
                        'metadata': {
                            'filename': file.filename,
                            'content_type': file.content_type,
                            'file_size': len(content),
                            'detected_fields': file_info.get('detected_fields', columns)
                        }
                    }
                else:
                    # Return as-is for non-tabular JSON
                    return {
                        'status': 'success',
                        'data': {
                            'raw_data': preview_data,
                            'structure_type': file_info.get('structure_type'),
                            'file_type': 'JSON'
                        },
                        'metadata': {
                            'filename': file.filename,
                            'content_type': file.content_type,
                            'file_size': len(content)
                        }
                    }
            
            else:
                # Unsupported file type
                return {
                    'status': 'error',
                    'message': f"Unsupported file type: {file_info.get('file_type', 'unknown')}"
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': f"Failed to parse file: {str(e)}"
            }
    
    async def parse_file_from_path(self, file_path: str) -> Dict[str, Any]:
        """
        Parse a file from its file path and return structured data.
        
        Args:
            file_path: Path to the file to parse
            
        Returns:
            Dictionary with parsed data and metadata
        """
        try:
            import os
            import mimetypes
            
            # Check if file exists
            if not os.path.exists(file_path):
                return {
                    'status': 'error',
                    'message': f"File not found: {file_path}"
                }
            
            # Read file content
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # Get filename and content type
            filename = os.path.basename(file_path)
            content_type, _ = mimetypes.guess_type(file_path)
            
            # Default content type based on extension if not detected
            if not content_type:
                ext = os.path.splitext(filename)[1].lower()
                if ext == '.csv':
                    content_type = 'text/csv'
                elif ext in ['.xlsx', '.xls']:
                    content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                elif ext == '.json':
                    content_type = 'application/json'
                else:
                    content_type = 'application/octet-stream'
            
            # Get file preview/parsing results
            file_info = self.service.get_file_preview(
                content=content,
                filename=filename,
                content_type=content_type
            )
            
            # Convert to expected format for dashboard
            if file_info.get('file_type') in ['CSV', 'Excel']:
                # For structured data (CSV/Excel), return rows and columns format
                return {
                    'status': 'success',
                    'data': {
                        'rows': file_info.get('preview_data', []),
                        'columns': file_info.get('columns', []),
                        'total_rows': file_info.get('total_rows', 0),
                        'total_columns': file_info.get('total_columns', 0),
                        'file_type': file_info.get('file_type'),
                        'column_types': file_info.get('column_types', {}),
                        'sheet_names': file_info.get('sheet_names', [])  # For Excel files
                    },
                    'metadata': {
                        'filename': filename,
                        'file_path': file_path,
                        'content_type': content_type,
                        'file_size': len(content),
                        'encoding': file_info.get('encoding', 'utf-8'),
                        'has_header': file_info.get('has_header', True)
                    }
                }
            
            elif file_info.get('file_type') == 'JSON':
                # For JSON data, try to convert to rows/columns format
                preview_data = file_info.get('preview_data', [])
                
                if file_info.get('structure_type') == 'array_of_objects' and preview_data:
                    # Extract columns from first object
                    columns = list(preview_data[0].keys()) if preview_data else []
                    
                    return {
                        'status': 'success',
                        'data': {
                            'rows': preview_data,
                            'columns': columns,
                            'total_rows': file_info.get('total_items', len(preview_data)),
                            'total_columns': len(columns),
                            'file_type': 'JSON',
                            'structure_type': file_info.get('structure_type')
                        },
                        'metadata': {
                            'filename': filename,
                            'file_path': file_path,
                            'content_type': content_type,
                            'file_size': len(content),
                            'detected_fields': file_info.get('detected_fields', columns)
                        }
                    }
                else:
                    # Return as-is for non-tabular JSON
                    return {
                        'status': 'success',
                        'data': {
                            'raw_data': preview_data,
                            'structure_type': file_info.get('structure_type'),
                            'file_type': 'JSON'
                        },
                        'metadata': {
                            'filename': filename,
                            'file_path': file_path,
                            'content_type': content_type,
                            'file_size': len(content)
                        }
                    }
            
            else:
                # Unsupported file type
                return {
                    'status': 'error',
                    'message': f"Unsupported file type: {file_info.get('file_type', 'unknown')}"
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': f"Failed to parse file from path {file_path}: {str(e)}"
            } 