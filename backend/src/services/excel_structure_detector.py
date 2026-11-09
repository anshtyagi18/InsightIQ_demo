"""
AI-Powered Excel Structure Detection

Uses vision models (GPT-4V, Claude 3.5 Sonnet) to analyze Excel layouts
when rule-based detection is insufficient or confidence is low.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import logging
import json
import base64
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from openpyxl import load_workbook
from openpyxl.styles import PatternFill
import asyncio

from src.services.litellm_service import LiteLLMService

logger = logging.getLogger(__name__)


@dataclass
class AIStructureAnalysis:
    """AI-detected structure analysis result."""
    layout_type: str
    confidence: float
    transformation_instructions: List[str]
    header_locations: Dict[str, List[int]]
    data_region: Dict[str, int]
    reasoning: str
    alternative_interpretations: List[Dict[str, Any]]


class ExcelStructureDetector:
    """
    AI-powered Excel structure detector using vision models.
    Fallback for complex layouts that rule-based detection can't handle.
    """
    
    def __init__(self):
        """Initialize the AI structure detector."""
        self.llm_service = LiteLLMService()
        self.vision_models = [
            'gpt-4-vision-preview',
            'claude-3-5-sonnet-20241022',
            'gemini-pro-vision'
        ]
        
    async def analyze_structure_with_ai(
        self,
        file_path: str,
        sheet_name: Optional[str] = None,
        use_vision: bool = True
    ) -> AIStructureAnalysis:
        """
        Analyze Excel structure using AI.
        
        Args:
            file_path: Path to Excel file
            sheet_name: Specific sheet name
            use_vision: If True, use vision models; otherwise use text-based analysis
            
        Returns:
            AIStructureAnalysis with detected structure
        """
        try:
            wb = load_workbook(file_path, data_only=True)
            sheet = wb[sheet_name] if sheet_name else wb.active
            
            if use_vision and self.llm_service.is_available():
                # Generate visual representation
                image = self._sheet_to_image(sheet)
                result = await self._analyze_with_vision(image, sheet)
            else:
                # Use text-based analysis
                result = await self._analyze_with_text(sheet)
            
            wb.close()
            return result
            
        except Exception as e:
            logger.error(f"Error in AI structure analysis: {str(e)}")
            return AIStructureAnalysis(
                layout_type='standard',
                confidence=30.0,
                transformation_instructions=['use_standard_read'],
                header_locations={'rows': [0]},
                data_region={'start_row': 1, 'start_col': 0},
                reasoning=f"AI analysis failed: {str(e)}",
                alternative_interpretations=[]
            )
    
    def _sheet_to_image(
        self,
        sheet,
        max_rows: int = 30,
        max_cols: int = 20
    ) -> Image.Image:
        """
        Convert Excel sheet to an image for vision model analysis.
        
        Args:
            sheet: openpyxl worksheet
            max_rows: Maximum rows to visualize
            max_cols: Maximum columns to visualize
            
        Returns:
            PIL Image of the sheet
        """
        # Cell dimensions
        cell_width = 100
        cell_height = 30
        
        # Calculate image size
        n_rows = min(max_rows, sheet.max_row)
        n_cols = min(max_cols, sheet.max_column)
        img_width = n_cols * cell_width
        img_height = n_rows * cell_height
        
        # Create image
        img = Image.new('RGB', (img_width, img_height), color='white')
        draw = ImageDraw.Draw(img)
        
        # Try to use a font (fallback to default if not available)
        try:
            font = ImageFont.truetype("arial.ttf", 12)
            bold_font = ImageFont.truetype("arialbd.ttf", 12)
        except:
            font = ImageFont.load_default()
            bold_font = font
        
        # Draw cells
        for row_idx in range(n_rows):
            for col_idx in range(n_cols):
                x = col_idx * cell_width
                y = row_idx * cell_height
                
                # Get cell
                cell = sheet.cell(row=row_idx + 1, column=col_idx + 1)
                value = str(cell.value) if cell.value is not None else ""
                
                # Cell background
                if cell.fill and cell.fill.patternType:
                    # Simplified: just detect if cell has fill
                    bg_color = (220, 220, 220)  # Light gray for filled cells
                else:
                    bg_color = (255, 255, 255)  # White
                
                draw.rectangle([x, y, x + cell_width, y + cell_height], fill=bg_color, outline='black')
                
                # Cell text
                text_font = bold_font if (cell.font and cell.font.bold) else font
                text_color = (0, 0, 0)
                
                # Truncate long text
                if len(value) > 12:
                    value = value[:12] + "..."
                
                # Draw text
                text_bbox = draw.textbbox((0, 0), value, font=text_font)
                text_width = text_bbox[2] - text_bbox[0]
                text_height = text_bbox[3] - text_bbox[1]
                text_x = x + 5
                text_y = y + (cell_height - text_height) // 2
                
                draw.text((text_x, text_y), value, fill=text_color, font=text_font)
        
        return img
    
    async def _analyze_with_vision(
        self,
        image: Image.Image,
        sheet
    ) -> AIStructureAnalysis:
        """
        Analyze Excel structure using vision model.
        
        Args:
            image: PIL Image of the sheet
            sheet: openpyxl worksheet
            
        Returns:
            AIStructureAnalysis result
        """
        # Convert image to base64
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode()
        
        # Prepare prompt
        prompt = f"""Analyze this Excel spreadsheet image and determine its structure.

The spreadsheet has {sheet.max_row} rows and {sheet.max_column} columns total (showing first 30 rows and 20 columns in the image).

Please identify:
1. Layout type: standard (headers top, data below), transposed (headers left, data right), 
   pivot (row and column headers), crosstab, hierarchical (multi-level headers), or mixed
2. Where are the headers located (which rows and/or columns)?
3. Where does the actual data region start and end?
4. Are there merged cells that indicate hierarchical headers?
5. What transformations would be needed to normalize this to a standard tabular format?

Provide your analysis in JSON format:
{{
    "layout_type": "standard|transposed|pivot|crosstab|hierarchical|mixed",
    "confidence": 0-100,
    "header_rows": [list of row indices, 0-based],
    "header_cols": [list of column indices, 0-based],
    "data_start_row": <integer>,
    "data_start_col": <integer>,
    "data_end_row": <integer>,
    "data_end_col": <integer>,
    "transformation_steps": ["step 1", "step 2", ...],
    "reasoning": "explanation of your analysis",
    "alternative_interpretation": "if there's another possible interpretation"
}}"""

        try:
            # Call vision model
            response = await self.llm_service.generate_vision_response(
                prompt=prompt,
                image_base64=img_base64,
                model=self.vision_models[0]  # Try primary vision model
            )
            
            if response.error:
                logger.warning(f"Vision model failed: {response.error}, falling back to text analysis")
                return await self._analyze_with_text(sheet)
            
            # Parse response
            analysis_dict = json.loads(response.content)
            
            return AIStructureAnalysis(
                layout_type=analysis_dict.get('layout_type', 'standard'),
                confidence=float(analysis_dict.get('confidence', 70.0)),
                transformation_instructions=analysis_dict.get('transformation_steps', []),
                header_locations={
                    'rows': analysis_dict.get('header_rows', [0]),
                    'cols': analysis_dict.get('header_cols', [])
                },
                data_region={
                    'start_row': analysis_dict.get('data_start_row', 1),
                    'start_col': analysis_dict.get('data_start_col', 0),
                    'end_row': analysis_dict.get('data_end_row', sheet.max_row - 1),
                    'end_col': analysis_dict.get('data_end_col', sheet.max_column - 1)
                },
                reasoning=analysis_dict.get('reasoning', 'AI vision analysis'),
                alternative_interpretations=[{
                    'interpretation': analysis_dict.get('alternative_interpretation', '')
                }] if analysis_dict.get('alternative_interpretation') else []
            )
            
        except json.JSONDecodeError:
            logger.error("Failed to parse AI vision response as JSON")
            return await self._analyze_with_text(sheet)
        except Exception as e:
            logger.error(f"Vision analysis error: {str(e)}")
            return await self._analyze_with_text(sheet)
    
    async def _analyze_with_text(self, sheet) -> AIStructureAnalysis:
        """
        Analyze Excel structure using text-based AI analysis.
        
        Args:
            sheet: openpyxl worksheet
            
        Returns:
            AIStructureAnalysis result
        """
        # Extract sample data from sheet
        sample_data = self._extract_sample_text(sheet, max_rows=20, max_cols=15)
        
        prompt = f"""Analyze this Excel spreadsheet data and determine its structure.

Spreadsheet size: {sheet.max_row} rows × {sheet.max_column} columns
Sample data (first 20 rows, 15 columns):

{sample_data}

Please identify:
1. Layout type: standard, transposed, pivot, crosstab, hierarchical, or mixed
2. Header locations (rows and/or columns)
3. Data region boundaries
4. Transformation steps needed to normalize to standard tabular format

Respond in JSON format:
{{
    "layout_type": "standard|transposed|pivot|crosstab|hierarchical|mixed",
    "confidence": 0-100,
    "header_rows": [0],
    "header_cols": [],
    "data_start_row": 1,
    "data_start_col": 0,
    "transformation_steps": ["description of each transformation"],
    "reasoning": "your analysis"
}}"""

        try:
            if not self.llm_service.is_available():
                # Return conservative default
                return AIStructureAnalysis(
                    layout_type='standard',
                    confidence=50.0,
                    transformation_instructions=['use_standard_pandas_read'],
                    header_locations={'rows': [0], 'cols': []},
                    data_region={'start_row': 1, 'start_col': 0, 
                               'end_row': sheet.max_row - 1, 'end_col': sheet.max_column - 1},
                    reasoning='AI service not available, using default standard layout',
                    alternative_interpretations=[]
                )
            
            response = await self.llm_service.generate_structured_response(
                prompt=prompt,
                response_format={
                    "layout_type": "string",
                    "confidence": "number",
                    "header_rows": ["array of integers"],
                    "header_cols": ["array of integers"],
                    "data_start_row": "integer",
                    "data_start_col": "integer",
                    "transformation_steps": ["array of strings"],
                    "reasoning": "string"
                }
            )
            
            if response.error:
                logger.warning(f"Text-based AI analysis failed: {response.error}")
                return self._get_fallback_analysis(sheet)
            
            analysis_dict = json.loads(response.content)
            
            return AIStructureAnalysis(
                layout_type=analysis_dict.get('layout_type', 'standard'),
                confidence=float(analysis_dict.get('confidence', 65.0)),
                transformation_instructions=analysis_dict.get('transformation_steps', []),
                header_locations={
                    'rows': analysis_dict.get('header_rows', [0]),
                    'cols': analysis_dict.get('header_cols', [])
                },
                data_region={
                    'start_row': analysis_dict.get('data_start_row', 1),
                    'start_col': analysis_dict.get('data_start_col', 0),
                    'end_row': sheet.max_row - 1,
                    'end_col': sheet.max_column - 1
                },
                reasoning=analysis_dict.get('reasoning', 'AI text analysis'),
                alternative_interpretations=[]
            )
            
        except Exception as e:
            logger.error(f"Text-based analysis error: {str(e)}")
            return self._get_fallback_analysis(sheet)
    
    def _extract_sample_text(
        self,
        sheet,
        max_rows: int = 20,
        max_cols: int = 15
    ) -> str:
        """
        Extract sample text representation of sheet for AI analysis.
        
        Args:
            sheet: openpyxl worksheet
            max_rows: Maximum rows to extract
            max_cols: Maximum columns to extract
            
        Returns:
            Formatted text representation
        """
        lines = []
        
        for row_idx in range(min(max_rows, sheet.max_row)):
            row_values = []
            for col_idx in range(min(max_cols, sheet.max_column)):
                cell = sheet.cell(row=row_idx + 1, column=col_idx + 1)
                value = str(cell.value) if cell.value is not None else ""
                
                # Add formatting indicators
                if cell.font and cell.font.bold:
                    value = f"**{value}**"
                
                # Truncate long values
                if len(value) > 20:
                    value = value[:20] + "..."
                
                row_values.append(value)
            
            lines.append(" | ".join(row_values))
        
        return "\n".join(lines)
    
    def _get_fallback_analysis(self, sheet) -> AIStructureAnalysis:
        """
        Get fallback analysis when AI analysis fails.
        
        Args:
            sheet: openpyxl worksheet
            
        Returns:
            Conservative fallback analysis
        """
        return AIStructureAnalysis(
            layout_type='standard',
            confidence=40.0,
            transformation_instructions=['read_as_standard_table'],
            header_locations={'rows': [0], 'cols': []},
            data_region={
                'start_row': 1,
                'start_col': 0,
                'end_row': sheet.max_row - 1,
                'end_col': sheet.max_column - 1
            },
            reasoning='Fallback to standard layout due to analysis errors',
            alternative_interpretations=[]
        )
    
    def combine_rule_and_ai_analysis(
        self,
        rule_based_confidence: float,
        ai_analysis: AIStructureAnalysis,
        threshold: float = 75.0
    ) -> str:
        """
        Combine rule-based and AI analysis results.
        
        Args:
            rule_based_confidence: Confidence from rule-based detection
            ai_analysis: AI analysis result
            threshold: Confidence threshold for preferring rule-based
            
        Returns:
            Recommended layout type to use
        """
        # If rule-based has high confidence, trust it
        if rule_based_confidence >= threshold:
            logger.info(f"Using rule-based detection (confidence: {rule_based_confidence:.1f}%)")
            return 'rule_based'
        
        # If AI has much higher confidence, use AI
        if ai_analysis.confidence > rule_based_confidence + 20:
            logger.info(f"Using AI detection (confidence: {ai_analysis.confidence:.1f}% vs {rule_based_confidence:.1f}%)")
            return 'ai_based'
        
        # If both are low confidence, prefer rule-based as safer
        if rule_based_confidence < 60 and ai_analysis.confidence < 60:
            logger.warning(f"Both analyses have low confidence, using rule-based as fallback")
            return 'rule_based'
        
        # Otherwise use the higher confidence one
        if ai_analysis.confidence > rule_based_confidence:
            return 'ai_based'
        else:
            return 'rule_based'




