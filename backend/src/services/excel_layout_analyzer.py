"""
Intelligent Excel Layout Detection & Normalization

This module analyzes Excel files to detect various layout patterns and normalizes them
into a standard tabular format. Handles transposed data, pivot tables, cross-tabs,
hierarchical headers, merged cells, and other complex Excel structures.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple, Set
from dataclasses import dataclass, asdict
import logging
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter, column_index_from_string
import re
from collections import Counter, defaultdict

logger = logging.getLogger(__name__)


@dataclass
class LayoutDetectionResult:
    """Result of layout detection analysis."""
    layout_type: str  # 'standard', 'transposed', 'pivot', 'crosstab', 'hierarchical', 'mixed'
    confidence: float  # 0-100
    header_rows: List[int]  # Row indices containing headers
    header_cols: List[int]  # Column indices containing headers
    data_start_row: int
    data_start_col: int
    data_end_row: int
    data_end_col: int
    merged_cells: List[Tuple[int, int, int, int]]  # (start_row, start_col, end_row, end_col)
    hierarchy_levels: int  # Number of header hierarchy levels
    transformation_needed: bool
    metadata: Dict[str, Any]
    reasoning: str  # Explanation of detection


@dataclass
class NormalizedData:
    """Normalized DataFrame with metadata."""
    dataframe: pd.DataFrame
    original_layout: str
    transformations_applied: List[str]
    confidence: float
    metadata: Dict[str, Any]


class ExcelLayoutAnalyzer:
    """
    Analyzes Excel file layouts and normalizes them to standard tabular format.
    Uses a combination of rule-based and heuristic approaches.
    """
    
    def __init__(self):
        """Initialize the layout analyzer."""
        self.layout_patterns = {
            'standard': self._detect_standard_layout,
            'transposed': self._detect_transposed_layout,
            'pivot': self._detect_pivot_layout,
            'crosstab': self._detect_crosstab_layout,
            'hierarchical': self._detect_hierarchical_layout,
            'mixed': self._detect_mixed_layout
        }
        
    def analyze_and_normalize(
        self, 
        file_path: str, 
        sheet_name: Optional[str] = None
    ) -> NormalizedData:
        """
        Main entry point: analyze Excel layout and return normalized data.
        
        Args:
            file_path: Path to Excel file
            sheet_name: Specific sheet name (None = first sheet)
            
        Returns:
            NormalizedData object with normalized DataFrame
        """
        try:
            # Load workbook with openpyxl for advanced analysis
            wb = load_workbook(file_path, data_only=True)
            sheet = wb[sheet_name] if sheet_name else wb.active
            
            # Log sheet info
            logger.info(f"Analyzing sheet: {sheet.title} ({sheet.max_row} rows x {sheet.max_column} cols)")
            logger.info(f"Merged cells: {len(list(sheet.merged_cells.ranges))} ranges")
            
            # Detect layout pattern
            detection_result = self.detect_layout(sheet)
            logger.info(f"✓ Detected layout: {detection_result.layout_type} "
                       f"(confidence: {detection_result.confidence:.1f}%)")
            logger.info(f"  Reasoning: {detection_result.reasoning}")
            logger.info(f"  Header rows: {detection_result.header_rows}")
            logger.info(f"  Data starts at row: {detection_result.data_start_row}")
            
            # Normalize based on detected layout
            normalized = self._normalize_layout(sheet, detection_result)
            
            logger.info(f"✓ Normalized to {len(normalized.dataframe)} rows x {len(normalized.dataframe.columns)} columns")
            logger.info(f"  Transformations: {normalized.transformations_applied}")
            
            wb.close()
            return normalized
            
        except Exception as e:
            logger.error(f"✗ Error analyzing Excel layout: {str(e)}", exc_info=True)
            # Fallback to standard pandas read
            try:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                logger.warning(f"Using fallback pandas read: {len(df)} rows x {len(df.columns)} columns")
                return NormalizedData(
                    dataframe=df,
                    original_layout='standard',
                    transformations_applied=[],
                    confidence=50.0,
                    metadata={'error': str(e), 'fallback': True}
                )
            except Exception as fallback_error:
                logger.error(f"✗ Fallback also failed: {str(fallback_error)}")
                raise
    
    def detect_layout(self, sheet) -> LayoutDetectionResult:
        """
        Detect the layout pattern of an Excel sheet.
        
        Args:
            sheet: openpyxl worksheet object
            
        Returns:
            LayoutDetectionResult with detected pattern
        """
        # Extract basic sheet information
        max_row = sheet.max_row
        max_col = sheet.max_column
        
        # Analyze cell patterns
        cell_analysis = self._analyze_cell_patterns(sheet, max_row, max_col)
        
        # Try each layout detector and score them
        detection_scores = {}
        detection_results = {}
        
        for layout_type, detector_func in self.layout_patterns.items():
            try:
                result = detector_func(sheet, cell_analysis, max_row, max_col)
                detection_scores[layout_type] = result.confidence
                detection_results[layout_type] = result
            except Exception as e:
                logger.warning(f"Error detecting {layout_type} layout: {e}")
                detection_scores[layout_type] = 0.0
        
        # Select highest confidence detection
        best_layout = max(detection_scores, key=detection_scores.get)
        best_result = detection_results[best_layout]
        
        logger.info(f"Layout detection scores: {detection_scores}")
        
        return best_result
    
    def _analyze_cell_patterns(
        self, 
        sheet, 
        max_row: int, 
        max_col: int
    ) -> Dict[str, Any]:
        """
        Analyze cell patterns to inform layout detection.
        
        Returns:
            Dictionary with cell pattern statistics
        """
        # Sample cells for analysis (don't read entire sheet for large files)
        sample_rows = min(max_row, 50)
        sample_cols = min(max_col, 30)
        
        # Cell type counters
        row_text_counts = [0] * sample_rows
        col_text_counts = [0] * sample_cols
        row_numeric_counts = [0] * sample_rows
        col_numeric_counts = [0] * sample_cols
        
        # Formatting analysis
        bold_cells = []
        merged_cells_list = []
        
        # Analyze merged cells
        for merged_range in sheet.merged_cells.ranges:
            min_row, min_col = merged_range.min_row, merged_range.min_col
            max_row_m, max_col_m = merged_range.max_row, merged_range.max_col
            merged_cells_list.append((min_row - 1, min_col - 1, max_row_m - 1, max_col_m - 1))
        
        # Sample cells
        for row_idx in range(1, sample_rows + 1):
            for col_idx in range(1, sample_cols + 1):
                cell = sheet.cell(row=row_idx, column=col_idx)
                value = cell.value
                
                if value is not None and value != '':
                    # Count text vs numeric
                    if isinstance(value, (int, float)):
                        row_numeric_counts[row_idx - 1] += 1
                        col_numeric_counts[col_idx - 1] += 1
                    else:
                        row_text_counts[row_idx - 1] += 1
                        col_text_counts[col_idx - 1] += 1
                    
                    # Check if bold (header indicator)
                    if cell.font and cell.font.bold:
                        bold_cells.append((row_idx - 1, col_idx - 1))
        
        # Calculate statistics
        total_cells_sampled = sample_rows * sample_cols
        non_empty_cells = sum(row_text_counts) + sum(row_numeric_counts)
        
        return {
            'max_row': max_row,
            'max_col': max_col,
            'sample_rows': sample_rows,
            'sample_cols': sample_cols,
            'row_text_counts': row_text_counts,
            'col_text_counts': col_text_counts,
            'row_numeric_counts': row_numeric_counts,
            'col_numeric_counts': col_numeric_counts,
            'bold_cells': bold_cells,
            'merged_cells': merged_cells_list,
            'density': non_empty_cells / total_cells_sampled if total_cells_sampled > 0 else 0,
            'text_ratio': sum(row_text_counts) / non_empty_cells if non_empty_cells > 0 else 0
        }
    
    def _detect_standard_layout(
        self, 
        sheet, 
        cell_analysis: Dict, 
        max_row: int, 
        max_col: int
    ) -> LayoutDetectionResult:
        """
        Detect standard tabular layout: headers in row 1, data below.
        """
        confidence = 0.0
        reasoning_parts = []
        
        # PENALTY: Merged cells in top rows suggest hierarchical, not standard
        top_merged = [m for m in cell_analysis['merged_cells'] if m[0] < 3]
        if len(top_merged) >= 2:
            confidence -= 30
            reasoning_parts.append(f"Multiple merged cells detected ({len(top_merged)} ranges) - likely hierarchical")
        elif len(top_merged) == 1:
            confidence -= 15
            reasoning_parts.append("Merged cells detected - possibly hierarchical")
        
        # Check if first row has mostly text (headers)
        first_row_text = cell_analysis['row_text_counts'][0]
        first_row_total = first_row_text + cell_analysis['row_numeric_counts'][0]
        
        if first_row_total > 0:
            first_row_text_ratio = first_row_text / first_row_total
            if first_row_text_ratio > 0.7:
                confidence += 30
                reasoning_parts.append(f"First row is {first_row_text_ratio:.0%} text (likely headers)")
        
        # Check if subsequent rows have more numeric data
        if len(cell_analysis['row_numeric_counts']) > 3:
            data_rows_numeric = cell_analysis['row_numeric_counts'][1:5]
            avg_numeric = np.mean(data_rows_numeric)
            avg_text = np.mean(cell_analysis['row_text_counts'][1:5])
            
            if avg_numeric > avg_text:
                confidence += 25
                reasoning_parts.append("Data rows contain mostly numeric values")
        
        # Check for bold first row (header formatting)
        bold_in_first_row = sum(1 for r, c in cell_analysis['bold_cells'] if r == 0)
        if bold_in_first_row > max_col * 0.5:
            confidence += 20
            reasoning_parts.append("First row has bold formatting")
        
        # Check column consistency (headers in all columns)
        if first_row_total >= max_col * 0.7:
            confidence += 15
            reasoning_parts.append("Headers present in most columns")
        
        # Penalty for unusual characteristics
        if max_row > max_col * 3:  # Very tall and narrow
            confidence -= 10
        
        # Cap minimum at 0
        confidence = max(confidence, 0.0)
        
        reasoning = "; ".join(reasoning_parts) if reasoning_parts else "Default standard layout"
        
        return LayoutDetectionResult(
            layout_type='standard',
            confidence=min(confidence, 95.0),
            header_rows=[0],
            header_cols=[],
            data_start_row=1,
            data_start_col=0,
            data_end_row=max_row - 1,
            data_end_col=max_col - 1,
            merged_cells=cell_analysis['merged_cells'],
            hierarchy_levels=1,
            transformation_needed=False,
            metadata={'first_row_text_ratio': first_row_text / first_row_total if first_row_total > 0 else 0},
            reasoning=reasoning
        )
    
    def _detect_transposed_layout(
        self, 
        sheet, 
        cell_analysis: Dict, 
        max_row: int, 
        max_col: int
    ) -> LayoutDetectionResult:
        """
        Detect transposed layout: headers in column A, data in rows to the right.
        """
        confidence = 0.0
        reasoning_parts = []
        
        # PENALTY: Merged cells in top rows strongly suggest hierarchical, NOT transposed
        top_merged = [m for m in cell_analysis['merged_cells'] if m[0] < 3]
        if len(top_merged) >= 2:
            confidence -= 40  # Heavy penalty
            reasoning_parts.append(f"Multiple merged cells in header area ({len(top_merged)} ranges) - likely hierarchical, not transposed")
        elif len(top_merged) == 1:
            confidence -= 20  # Light penalty
            reasoning_parts.append("Merged cells detected - possibly hierarchical")
        
        # Check if first column has mostly text
        first_col_text = cell_analysis['col_text_counts'][0]
        first_col_total = first_col_text + cell_analysis['col_numeric_counts'][0]
        
        if first_col_total > 0:
            first_col_text_ratio = first_col_text / first_col_total
            if first_col_text_ratio > 0.8:
                confidence += 35
                reasoning_parts.append(f"First column is {first_col_text_ratio:.0%} text (likely headers)")
        
        # Check if data columns have more numeric content
        if len(cell_analysis['col_numeric_counts']) > 2:
            data_cols_numeric = cell_analysis['col_numeric_counts'][1:5]
            avg_numeric = np.mean(data_cols_numeric)
            avg_text = np.mean(cell_analysis['col_text_counts'][1:5])
            
            if avg_numeric > avg_text * 1.5:
                confidence += 30
                reasoning_parts.append("Data columns contain mostly numeric values")
        
        # Check aspect ratio (wider than tall suggests transposition)
        if max_col > max_row * 1.5:
            confidence += 20
            reasoning_parts.append(f"Sheet is wider ({max_col} cols) than tall ({max_row} rows)")
        
        # Check for bold first column
        bold_in_first_col = sum(1 for r, c in cell_analysis['bold_cells'] if c == 0)
        if bold_in_first_col > max_row * 0.4:
            confidence += 15
            reasoning_parts.append("First column has bold formatting")
        
        # Cap minimum at 0
        confidence = max(confidence, 0.0)
        
        reasoning = "; ".join(reasoning_parts) if reasoning_parts else "Appears to be transposed"
        
        return LayoutDetectionResult(
            layout_type='transposed',
            confidence=min(confidence, 95.0),
            header_rows=[],
            header_cols=[0],
            data_start_row=0,
            data_start_col=1,
            data_end_row=max_row - 1,
            data_end_col=max_col - 1,
            merged_cells=cell_analysis['merged_cells'],
            hierarchy_levels=1,
            transformation_needed=True,
            metadata={'first_col_text_ratio': first_col_text / first_col_total if first_col_total > 0 else 0},
            reasoning=reasoning
        )
    
    def _detect_pivot_layout(
        self, 
        sheet, 
        cell_analysis: Dict, 
        max_row: int, 
        max_col: int
    ) -> LayoutDetectionResult:
        """
        Detect pivot table layout: row headers + column headers + data matrix.
        """
        confidence = 0.0
        reasoning_parts = []
        
        # Look for text in both first row and first column
        first_row_text = cell_analysis['row_text_counts'][0]
        first_col_text = cell_analysis['col_text_counts'][0]
        
        if first_row_text > 2 and first_col_text > 2:
            confidence += 30
            reasoning_parts.append("Both first row and first column contain text headers")
        
        # Check for numeric data in the interior (not first row/col)
        interior_numeric = 0
        interior_total = 0
        for row_idx in range(1, min(10, len(cell_analysis['row_numeric_counts']))):
            for col_idx in range(1, min(10, len(cell_analysis['col_numeric_counts']))):
                if row_idx < len(cell_analysis['row_numeric_counts']):
                    interior_numeric += cell_analysis['col_numeric_counts'][col_idx]
                    interior_total += (cell_analysis['col_numeric_counts'][col_idx] + 
                                     cell_analysis['col_text_counts'][col_idx])
        
        if interior_total > 0 and interior_numeric / interior_total > 0.7:
            confidence += 35
            reasoning_parts.append("Interior cells are mostly numeric (data matrix)")
        
        # Check for approximately equal dimensions (square-ish pivot table)
        aspect_ratio = max_col / max_row if max_row > 0 else 0
        if 0.5 <= aspect_ratio <= 2.0:
            confidence += 20
            reasoning_parts.append("Dimensions suggest pivot table structure")
        
        reasoning = "; ".join(reasoning_parts) if reasoning_parts else "Appears to be pivot table"
        
        return LayoutDetectionResult(
            layout_type='pivot',
            confidence=min(confidence, 95.0),
            header_rows=[0],
            header_cols=[0],
            data_start_row=1,
            data_start_col=1,
            data_end_row=max_row - 1,
            data_end_col=max_col - 1,
            merged_cells=cell_analysis['merged_cells'],
            hierarchy_levels=1,
            transformation_needed=True,
            metadata={'aspect_ratio': aspect_ratio},
            reasoning=reasoning
        )
    
    def _detect_crosstab_layout(
        self, 
        sheet, 
        cell_analysis: Dict, 
        max_row: int, 
        max_col: int
    ) -> LayoutDetectionResult:
        """
        Detect cross-tabulated layout with both row and column headers.
        Similar to pivot but with different transformation needs.
        """
        # Cross-tab is very similar to pivot, use similar logic
        pivot_result = self._detect_pivot_layout(sheet, cell_analysis, max_row, max_col)
        
        # Adjust for cross-tab specific characteristics
        confidence = pivot_result.confidence * 0.9  # Slightly lower base confidence
        
        return LayoutDetectionResult(
            layout_type='crosstab',
            confidence=confidence,
            header_rows=pivot_result.header_rows,
            header_cols=pivot_result.header_cols,
            data_start_row=pivot_result.data_start_row,
            data_start_col=pivot_result.data_start_col,
            data_end_row=pivot_result.data_end_row,
            data_end_col=pivot_result.data_end_col,
            merged_cells=pivot_result.merged_cells,
            hierarchy_levels=1,
            transformation_needed=True,
            metadata=pivot_result.metadata,
            reasoning=pivot_result.reasoning.replace("pivot", "cross-tab")
        )
    
    def _detect_hierarchical_layout(
        self, 
        sheet, 
        cell_analysis: Dict, 
        max_row: int, 
        max_col: int
    ) -> LayoutDetectionResult:
        """
        Detect hierarchical headers (multi-level column headers).
        Enhanced to better handle merged cells and multi-level structures.
        """
        confidence = 0.0
        reasoning_parts = []
        header_rows_detected = []
        
        # Analyze merged cells more thoroughly
        merged_by_row = {}
        for m in cell_analysis['merged_cells']:
            start_row = m[0]
            if start_row < 5:  # Focus on top 5 rows
                if start_row not in merged_by_row:
                    merged_by_row[start_row] = []
                merged_by_row[start_row].append(m)
        
        # Look for multiple rows with merged cells
        rows_with_merges = len(merged_by_row)
        if rows_with_merges >= 2:
            confidence += 60  # Increased from 45 to ensure hierarchical wins
            reasoning_parts.append(f"Found merged cells in {rows_with_merges} header rows")
        
        # Check for spanning merged cells (hierarchical indicator)
        vertical_spans = [m for m in cell_analysis['merged_cells'] 
                         if m[0] < 3 and (m[2] - m[0]) >= 1]  # Spans at least 2 rows
        if vertical_spans:
            confidence += 25
            reasoning_parts.append(f"Found {len(vertical_spans)} vertically spanning merged cells")
        
        # Detect header rows by analyzing content
        for row_idx in range(min(5, len(cell_analysis['row_text_counts']))):
            row_text = cell_analysis['row_text_counts'][row_idx]
            row_numeric = cell_analysis['row_numeric_counts'][row_idx]
            row_total = row_text + row_numeric
            
            if row_total > 0:
                text_ratio = row_text / row_total
                # Header row indicators:
                # - High text ratio (>60%)
                # - Has merged cells
                # - Low cell count (merged cells reduce count)
                # - First 2 rows default to headers if they have any text
                is_header = (text_ratio > 0.6 or 
                           row_idx in merged_by_row or
                           row_total < max_col * 0.5 or  # Sparse (due to merging)
                           (row_idx < 2 and text_ratio > 0.3))  # First 2 rows with any text
                
                if is_header:
                    header_rows_detected.append(row_idx)
        
        # Ensure we have at least 2 header rows for hierarchical
        if len(header_rows_detected) >= 2:
            confidence += 30
            reasoning_parts.append(f"Detected {len(header_rows_detected)} header rows")
        elif len(header_rows_detected) == 1 and rows_with_merges >= 2:
            # Add second row if we have merges but only detected 1 header
            header_rows_detected.append(header_rows_detected[0] + 1)
            confidence += 20
            reasoning_parts.append("Inferred second header row from merge patterns")
        
        hierarchy_levels = len(header_rows_detected) if header_rows_detected else 2
        data_start_row = max(header_rows_detected) + 1 if header_rows_detected else 2
        
        reasoning = "; ".join(reasoning_parts) if reasoning_parts else "Appears to have hierarchical headers"
        
        return LayoutDetectionResult(
            layout_type='hierarchical',
            confidence=min(confidence, 95.0),
            header_rows=header_rows_detected if header_rows_detected else [0, 1],
            header_cols=[],
            data_start_row=data_start_row,
            data_start_col=0,
            data_end_row=max_row - 1,
            data_end_col=max_col - 1,
            merged_cells=cell_analysis['merged_cells'],
            hierarchy_levels=hierarchy_levels,
            transformation_needed=True,
            metadata={
                'merged_cells_in_headers': len([m for m in cell_analysis['merged_cells'] if m[0] < data_start_row]),
                'vertical_spans': len(vertical_spans),
                'rows_with_merges': rows_with_merges
            },
            reasoning=reasoning
        )
    
    def _detect_mixed_layout(
        self, 
        sheet, 
        cell_analysis: Dict, 
        max_row: int, 
        max_col: int
    ) -> LayoutDetectionResult:
        """
        Detect mixed layout (multiple tables or unusual structure).
        This is a fallback for complex layouts.
        """
        confidence = 30.0  # Low default confidence
        reasoning = "Layout doesn't clearly match standard patterns - may contain multiple tables or complex structure"
        
        # Check for multiple distinct data regions
        # (simplified detection - could be enhanced)
        
        return LayoutDetectionResult(
            layout_type='mixed',
            confidence=confidence,
            header_rows=[0],
            header_cols=[],
            data_start_row=1,
            data_start_col=0,
            data_end_row=max_row - 1,
            data_end_col=max_col - 1,
            merged_cells=cell_analysis['merged_cells'],
            hierarchy_levels=1,
            transformation_needed=True,
            metadata={'requires_manual_review': True},
            reasoning=reasoning
        )
    
    def _normalize_layout(
        self, 
        sheet, 
        detection: LayoutDetectionResult
    ) -> NormalizedData:
        """
        Normalize detected layout to standard tabular format.
        """
        transformations = []
        
        if detection.layout_type == 'standard':
            df = self._extract_standard_data(sheet, detection)
            
        elif detection.layout_type == 'transposed':
            df = self._extract_transposed_data(sheet, detection)
            transformations.append('transposed')
            
        elif detection.layout_type == 'pivot':
            df = self._extract_pivot_data(sheet, detection)
            transformations.append('unpivoted')
            
        elif detection.layout_type == 'crosstab':
            df = self._extract_crosstab_data(sheet, detection)
            transformations.append('denormalized_crosstab')
            
        elif detection.layout_type == 'hierarchical':
            df = self._extract_hierarchical_data(sheet, detection)
            transformations.append('flattened_hierarchy')
            
        else:  # mixed or unknown
            df = self._extract_standard_data(sheet, detection)
            transformations.append('best_effort_extraction')
        
        # Clean the dataframe
        df = self._clean_dataframe(df)
        transformations.append('cleaned')
        
        return NormalizedData(
            dataframe=df,
            original_layout=detection.layout_type,
            transformations_applied=transformations,
            confidence=detection.confidence,
            metadata=asdict(detection)
        )
    
    def _extract_standard_data(self, sheet, detection: LayoutDetectionResult) -> pd.DataFrame:
        """
        Extract data from standard layout.
        Handles merged cells properly.
        """
        # Build merged cell value map
        merged_cell_values = self._build_merged_cell_map(sheet, detection.merged_cells)
        
        # Read data starting from detected data region
        data = []
        headers = []
        
        # Get headers
        header_row = detection.header_rows[0] if detection.header_rows else 0
        for col_idx in range(detection.data_start_col, min(detection.data_end_col + 1, sheet.max_column)):
            if (header_row, col_idx) in merged_cell_values:
                header_value = merged_cell_values[(header_row, col_idx)]
            else:
                cell = sheet.cell(row=header_row + 1, column=col_idx + 1)
                header_value = cell.value
            
            header_str = str(header_value).strip() if header_value is not None else f"Column_{col_idx}"
            headers.append(header_str if header_str else f"Column_{col_idx}")
        
        # Get data rows
        start_row = detection.data_start_row if detection.data_start_row > 0 else 1
        for row_idx in range(start_row, min(detection.data_end_row + 1, sheet.max_row)):
            row_data = []
            for col_idx in range(detection.data_start_col, min(detection.data_end_col + 1, sheet.max_column)):
                if (row_idx, col_idx) in merged_cell_values:
                    cell_value = merged_cell_values[(row_idx, col_idx)]
                else:
                    cell = sheet.cell(row=row_idx + 1, column=col_idx + 1)
                    cell_value = cell.value
                row_data.append(cell_value)
            
            # Only add non-empty rows
            if any(val is not None for val in row_data):
                data.append(row_data)
        
        if not data:
            return pd.DataFrame(columns=headers)
        
        df = pd.DataFrame(data, columns=headers)
        return df
    
    def _build_merged_cell_map(self, sheet, merged_cells: List[Tuple[int, int, int, int]]) -> Dict[Tuple[int, int], Any]:
        """
        Build a map of all cells in merged ranges to their values.
        
        Args:
            sheet: openpyxl worksheet
            merged_cells: List of (start_row, start_col, end_row, end_col) tuples
            
        Returns:
            Dict mapping (row_idx, col_idx) to cell value
        """
        merged_map = {}
        for merged_range in merged_cells:
            start_row, start_col, end_row, end_col = merged_range
            # Get value from top-left cell
            cell_value = sheet.cell(row=start_row + 1, column=start_col + 1).value
            # Map all cells in range to this value
            for r in range(start_row, end_row + 1):
                for c in range(start_col, end_col + 1):
                    merged_map[(r, c)] = cell_value
        return merged_map
    
    def _extract_transposed_data(self, sheet, detection: LayoutDetectionResult) -> pd.DataFrame:
        """Extract and transpose data from transposed layout."""
        # Read transposed data
        data = {}
        
        # Get row headers (will become column names)
        for row_idx in range(detection.data_start_row, detection.data_end_row + 1):
            cell = sheet.cell(row=row_idx + 1, column=detection.header_cols[0] + 1)
            header_name = str(cell.value) if cell.value is not None else f"Row_{row_idx}"
            
            # Get data for this row (will become a column)
            row_data = []
            for col_idx in range(detection.data_start_col + 1, detection.data_end_col + 2):
                cell = sheet.cell(row=row_idx + 1, column=col_idx)
                row_data.append(cell.value)
            
            data[header_name] = row_data
        
        df = pd.DataFrame(data)
        return df
    
    def _extract_pivot_data(self, sheet, detection: LayoutDetectionResult) -> pd.DataFrame:
        """Extract and unpivot data from pivot table layout."""
        # Get column headers
        col_headers = []
        for col_idx in range(detection.data_start_col + 1, detection.data_end_col + 2):
            cell = sheet.cell(row=detection.header_rows[0] + 1, column=col_idx)
            col_headers.append(str(cell.value) if cell.value is not None else f"Col_{col_idx}")
        
        # Get row headers and data
        unpivoted_data = []
        
        for row_idx in range(detection.data_start_row + 1, detection.data_end_row + 2):
            # Get row header
            row_header_cell = sheet.cell(row=row_idx, column=detection.header_cols[0] + 1)
            row_header = str(row_header_cell.value) if row_header_cell.value is not None else f"Row_{row_idx}"
            
            # Get values for each column
            for col_idx, col_header in enumerate(col_headers):
                cell = sheet.cell(row=row_idx, column=detection.data_start_col + 1 + col_idx)
                value = cell.value
                
                unpivoted_data.append({
                    'Category': row_header,
                    'Measure': col_header,
                    'Value': value
                })
        
        df = pd.DataFrame(unpivoted_data)
        return df
    
    def _extract_crosstab_data(self, sheet, detection: LayoutDetectionResult) -> pd.DataFrame:
        """Extract and denormalize cross-tabulated data."""
        # Similar to pivot but with different naming
        return self._extract_pivot_data(sheet, detection)
    
    def _extract_hierarchical_data(self, sheet, detection: LayoutDetectionResult) -> pd.DataFrame:
        """
        Extract data with hierarchical headers and flatten them.
        Properly handles merged cells in headers.
        """
        # Build merged cell value map
        merged_cell_values = self._build_merged_cell_map(sheet, detection.merged_cells)
        
        # Build hierarchical column names
        hierarchical_headers = []
        
        for col_idx in range(detection.data_start_col, detection.data_end_col + 1):
            header_parts = []
            last_value = None
            
            for header_row in detection.header_rows:
                # Check if this cell is part of a merged range
                if (header_row, col_idx) in merged_cell_values:
                    cell_value = merged_cell_values[(header_row, col_idx)]
                else:
                    cell = sheet.cell(row=header_row + 1, column=col_idx + 1)
                    cell_value = cell.value
                
                # Clean and add value
                if cell_value is not None and str(cell_value).strip():
                    clean_value = str(cell_value).strip()
                    # Avoid repeating same value from merged cells spanning rows
                    if clean_value != last_value:
                        header_parts.append(clean_value)
                        last_value = clean_value
            
            # Combine hierarchical parts
            if header_parts:
                # Join with underscore and clean
                combined_header = '_'.join(header_parts)
                # Remove multiple underscores
                combined_header = '_'.join(part for part in combined_header.split('_') if part)
                hierarchical_headers.append(combined_header)
            else:
                hierarchical_headers.append(f"Column_{col_idx}")
        
        # Get data rows
        data = []
        for row_idx in range(detection.data_start_row, min(detection.data_end_row + 1, sheet.max_row)):
            row_data = []
            for col_idx in range(detection.data_start_col, detection.data_end_col + 1):
                # Check if this data cell is merged
                cell_value = None
                if (row_idx, col_idx) in merged_cell_values:
                    cell_value = merged_cell_values[(row_idx, col_idx)]
                else:
                    cell = sheet.cell(row=row_idx + 1, column=col_idx + 1)
                    cell_value = cell.value
                row_data.append(cell_value)
            
            # Only add non-empty rows
            if any(val is not None and str(val).strip() for val in row_data):
                data.append(row_data)
        
        if not data:
            # If no data rows found, return empty DataFrame with headers
            return pd.DataFrame(columns=hierarchical_headers)
        
        df = pd.DataFrame(data, columns=hierarchical_headers)
        return df
    
    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and standardize the extracted dataframe."""
        # Remove completely empty rows and columns
        df = df.dropna(how='all', axis=0)
        df = df.dropna(how='all', axis=1)
        
        # Reset index
        df = df.reset_index(drop=True)
        
        # Clean column names
        df.columns = [self._clean_column_name(str(col)) for col in df.columns]
        
        # Ensure unique column names
        df.columns = self._make_unique_columns(df.columns.tolist())
        
        return df
    
    def _clean_column_name(self, name: str) -> str:
        """Clean a column name."""
        # Remove extra whitespace
        name = ' '.join(name.split())
        
        # Remove special characters that might cause issues
        name = re.sub(r'[^\w\s-]', '', name)
        
        # Replace spaces with underscores
        name = name.replace(' ', '_')
        
        # Ensure it starts with a letter or underscore
        if name and not name[0].isalpha() and name[0] != '_':
            name = 'Col_' + name
        
        return name or 'Unknown_Column'
    
    def _make_unique_columns(self, columns: List[str]) -> List[str]:
        """Ensure all column names are unique by appending numbers if needed."""
        seen = {}
        unique_columns = []
        
        for col in columns:
            if col in seen:
                seen[col] += 1
                unique_columns.append(f"{col}_{seen[col]}")
            else:
                seen[col] = 0
                unique_columns.append(col)
        
        return unique_columns

