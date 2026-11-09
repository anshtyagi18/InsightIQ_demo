"""
Intelligent Data Filtering Agent

This agent eliminates irrelevant data from dashboard calculations using AI-powered 
column classification to improve data accuracy. It implements pattern recognition 
for serial numbers, phone numbers, IDs, and other non-analytical data while providing 
business context analysis for accurate classification.
"""

import pandas as pd
import numpy as np
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from google.adk.agents import Agent
from google.adk.tools import FunctionTool
import logging
import json

# LiteLLM imports for OpenRouter integration
try:
    from litellm import completion
    LITELLM_AVAILABLE = True
except ImportError:
    LITELLM_AVAILABLE = False
    logging.warning("LiteLLM not available. Install with: pip install litellm")

logger = logging.getLogger(__name__)


@dataclass
class ColumnClassification:
    """Result of column classification analysis."""
    column_name: str
    classification: str  # 'relevant', 'irrelevant', 'metadata'
    data_type: str
    confidence: float
    reasoning: str
    sample_values: List[str]
    pattern_matches: List[str]


@dataclass
class DataFilteringResult:
    """Complete result of intelligent data filtering."""
    relevant_columns: List[str]
    irrelevant_columns: List[str]
    metadata_columns: List[str]
    column_classifications: List[ColumnClassification]
    confidence_score: float
    filtering_summary: str
    total_columns_analyzed: int
    columns_filtered: int
    data_retention_percentage: float


def detect_serial_number_patterns(values: List[Any], column_name: str = "") -> Dict[str, Any]:
    """
    Detect if column contains serial numbers or sequential IDs.
    
    Args:
        values: List of column values to analyze
        column_name: Name of the column (optional, improves detection accuracy)
        
    Returns:
        Dictionary with detection results
    """
    try:
        # Convert to strings and filter out nulls
        str_values = [str(v).strip() for v in values if v is not None and str(v).strip() != '']
        
        if len(str_values) < 2:
            return {
                'is_serial': False,
                'confidence': 0.0,
                'pattern_type': 'insufficient_data',
                'reasoning': 'Insufficient data for pattern detection'
            }
        
        # Check column name for serial number indicators first
        column_confidence = 0.0
        name_reasoning_parts = []
        is_business_data = False
        
        if column_name:
            column_lower = column_name.lower().replace(' ', '').replace('.', '').replace('_', '').replace('-', '')
            
            # Strong business data indicators (should NOT be serial numbers)
            business_indicators = [
                'sales', 'revenue', 'amount', 'price', 'cost', 'value', 'total', 'sum',
                'quantity', 'count', 'volume', 'weight', 'height', 'width', 'length',
                'rate', 'percent', 'percentage', 'ratio', 'score', 'rating', 'points',
                'profit', 'loss', 'margin', 'commission', 'fee', 'tax', 'discount',
                'balance', 'payment', 'invoice', 'order', 'product', 'item', 'service'
            ]
            
            # Check for business indicators first
            for indicator in business_indicators:
                if indicator in column_lower:
                    is_business_data = True
                    name_reasoning_parts.append(f"Column name '{column_name}' contains business indicator '{indicator}'")
                    break
            
            # Only check for serial patterns if it's not clearly business data
            if not is_business_data:
                serial_name_patterns = [
                    's.no', 'sno', 'sr.no', 'srno', 'serial', 'serialno', 'serialnumber',
                    'index', 'row', 'seq', 'sequence', 'no.', 'num', '#', 'slno'
                ]
                
                # Check for exact matches or patterns in column name
                for pattern in serial_name_patterns:
                    pattern_clean = pattern.replace('.', '').replace(' ', '')
                    if pattern_clean in column_lower or column_lower == pattern_clean:
                        column_confidence = 0.9  # Very high confidence for name-based detection
                        name_reasoning_parts.append(f"Column name '{column_name}' matches serial pattern '{pattern}'")
                        break
                
                # Check for partial matches with lower confidence
                if column_confidence == 0.0:
                    partial_patterns = ['serial', 'index', 'seq', 'row']  # Removed 'num' as it's too generic
                    for pattern in partial_patterns:
                        if pattern in column_lower:
                            column_confidence = 0.7
                            name_reasoning_parts.append(f"Column name '{column_name}' contains serial indicator '{pattern}'")
                            break
        
        # If it's clearly business data, return early with low serial confidence
        if is_business_data:
            return {
                'is_serial': False,
                'confidence': 0.1,  # Very low confidence that it's a serial number
                'pattern_type': 'business_data',
                'pattern_matches': {},
                'is_sequential': False,
                'unique_ratio': len(set(str_values)) / len(str_values),
                'column_name_confidence': 0.0,
                'reasoning': '; '.join(name_reasoning_parts)
            }
        
        # Common serial number patterns in data values
        patterns = {
            'sequential_numeric': r'^\d+$',
            'prefixed_numeric': r'^[A-Z]{1,4}\d+$',
            'hyphenated_code': r'^[A-Z0-9]+-[A-Z0-9]+(-[A-Z0-9]+)*$',
            'barcode_like': r'^\d{8,}$',
            'product_code': r'^[A-Z]{2,4}-?\d{4,}$',
            'uuid_like': r'^[A-F0-9]{8}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{12}$'
        }
        
        matches = {}
        for pattern_name, pattern in patterns.items():
            pattern_matches = sum(1 for v in str_values if re.match(pattern, v.upper()))
            match_percentage = pattern_matches / len(str_values)
            matches[pattern_name] = {
                'matches': pattern_matches,
                'percentage': match_percentage
            }
        
        # Find best matching pattern
        best_pattern = max(matches.items(), key=lambda x: x[1]['percentage'])
        best_percentage = best_pattern[1]['percentage']
        
        # Check for sequential nature (numeric values)
        try:
            numeric_values = []
            for v in str_values[:50]:  # Sample first 50 values
                try:
                    # Extract numeric part
                    numeric_part = re.findall(r'\d+', v)
                    if numeric_part:
                        numeric_values.append(int(numeric_part[-1]))  # Use last number found
                except:
                    continue
            
            is_sequential = False
            if len(numeric_values) >= 3:
                # Check if values are mostly sequential or in order
                sorted_values = sorted(numeric_values)
                differences = [sorted_values[i+1] - sorted_values[i] for i in range(len(sorted_values)-1)]
                avg_diff = np.mean(differences) if differences else 0
                
                # For sequential detection, be more strict:
                # 1. Small, consistent differences (typical of serial numbers: 1,2,3 or 100,101,102)
                # 2. Values should start from 1 or similar low number (typical serial pattern)
                min_val = min(numeric_values) if numeric_values else 0
                is_sequential = (avg_diff <= 2 and len(set(differences)) <= 2 and min_val <= 10)
                
        except Exception:
            is_sequential = False
        
        # Determine if this is likely a serial number
        confidence = column_confidence  # Start with column name confidence
        reasoning_parts = name_reasoning_parts.copy()
        
        # Add data pattern confidence, but be more conservative
        if best_percentage >= 0.8:
            # If column name already suggests serial, add full data confidence
            # If no column name evidence, be more conservative
            data_confidence_multiplier = 1.0 if column_confidence > 0.5 else 0.3
            confidence += 0.6 * (1 - column_confidence) * data_confidence_multiplier
            reasoning_parts.append(f"High pattern match ({best_pattern[0]}: {best_percentage:.1%})")
        elif best_percentage >= 0.5:
            data_confidence_multiplier = 1.0 if column_confidence > 0.5 else 0.2
            confidence += 0.3 * (1 - column_confidence) * data_confidence_multiplier
            reasoning_parts.append(f"Moderate pattern match ({best_pattern[0]}: {best_percentage:.1%})")
        
        if is_sequential:
            # Sequential pattern is strong evidence, but only if column name also suggests it
            sequential_confidence_multiplier = 1.0 if column_confidence > 0.5 else 0.4
            confidence += 0.3 * (1 - column_confidence) * sequential_confidence_multiplier
            reasoning_parts.append("Sequential numeric pattern detected")
        
        # Check for unique values (typical of serial numbers)
        unique_ratio = len(set(str_values)) / len(str_values)
        if unique_ratio >= 0.95:
            # High uniqueness alone is not enough evidence without other indicators
            uniqueness_confidence_multiplier = 1.0 if column_confidence > 0.5 else 0.1
            confidence += 0.1 * (1 - column_confidence) * uniqueness_confidence_multiplier
            reasoning_parts.append("High uniqueness ratio")
        
        # Ensure confidence doesn't exceed 1.0
        confidence = min(confidence, 1.0)
        
        # Adjust thresholds: be more demanding for serial number detection
        if column_confidence > 0.5:
            # If column name suggests serial number, use lower threshold
            detection_threshold = 0.3
        else:
            # If no column name evidence, require very high confidence from data patterns
            detection_threshold = 0.7
        
        is_serial = confidence >= detection_threshold
        
        return {
            'is_serial': is_serial,
            'confidence': confidence,
            'pattern_type': best_pattern[0] if is_serial else 'none',
            'pattern_matches': matches,
            'is_sequential': is_sequential,
            'unique_ratio': unique_ratio,
            'column_name_confidence': column_confidence,
            'reasoning': '; '.join(reasoning_parts) if reasoning_parts else 'No clear serial pattern detected'
        }
        
    except Exception as e:
        logger.error(f"Error in detect_serial_number_patterns: {str(e)}")
        return {
            'is_serial': False,
            'confidence': 0.0,
            'pattern_type': 'error',
            'reasoning': f"Error during analysis: {str(e)}"
        }


def detect_phone_number_patterns(values: List[Any]) -> Dict[str, Any]:
    """
    Detect if column contains phone numbers.
    
    Args:
        values: List of column values to analyze
        
    Returns:
        Dictionary with detection results
    """
    try:
        # Convert to strings and filter out nulls
        str_values = [str(v).strip() for v in values if v is not None and str(v).strip() != '']
        
        if len(str_values) < 2:
            return {
                'is_phone': False,
                'confidence': 0.0,
                'phone_format': 'insufficient_data',
                'reasoning': 'Insufficient data for phone number detection'
            }
        
        # Phone number patterns
        phone_patterns = {
            'us_standard': r'^\+?1?[-.\s]?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})$',
            'international': r'^\+[1-9]\d{1,14}$',
            'digits_only': r'^\d{10,15}$',
            'formatted': r'^[\+]?[1-9][\d\s\-\(\)\.]{8,20}$',
            'us_with_ext': r'^\+?1?[-.\s]?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})[\s]?[x|ext\.?]?[\s]?\d{1,5}$'
        }
        
        matches = {}
        total_matches = 0
        
        for pattern_name, pattern in phone_patterns.items():
            pattern_matches = sum(1 for v in str_values if re.match(pattern, v.replace(' ', '')))
            match_percentage = pattern_matches / len(str_values)
            matches[pattern_name] = {
                'matches': pattern_matches,
                'percentage': match_percentage
            }
            total_matches += pattern_matches
        
        # Overall phone number confidence
        overall_match_percentage = min(total_matches / len(str_values), 1.0)
        
        # Additional validation checks
        avg_length = np.mean([len(re.sub(r'[^\d]', '', v)) for v in str_values])
        length_consistency = np.std([len(re.sub(r'[^\d]', '', v)) for v in str_values])
        
        confidence = 0.0
        reasoning_parts = []
        
        if overall_match_percentage >= 0.8:
            confidence += 0.7
            reasoning_parts.append(f"High phone pattern match ({overall_match_percentage:.1%})")
        elif overall_match_percentage >= 0.5:
            confidence += 0.4
            reasoning_parts.append(f"Moderate phone pattern match ({overall_match_percentage:.1%})")
        
        # Check average length (typical phone numbers are 10-15 digits)
        if 10 <= avg_length <= 15:
            confidence += 0.2
            reasoning_parts.append(f"Appropriate digit length (avg: {avg_length:.1f})")
        
        # Check consistency in length
        if length_consistency <= 2:
            confidence += 0.1
            reasoning_parts.append("Consistent digit length")
        
        best_format = max(matches.items(), key=lambda x: x[1]['percentage'])[0]
        is_phone = confidence >= 0.5
        
        return {
            'is_phone': is_phone,
            'confidence': min(confidence, 1.0),
            'phone_format': best_format if is_phone else 'none',
            'pattern_matches': matches,
            'average_length': avg_length,
            'length_consistency': length_consistency,
            'reasoning': '; '.join(reasoning_parts) if reasoning_parts else 'No clear phone number pattern detected'
        }
        
    except Exception as e:
        logger.error(f"Error in detect_phone_number_patterns: {str(e)}")
        return {
            'is_phone': False,
            'confidence': 0.0,
            'phone_format': 'error',
            'reasoning': f"Error during analysis: {str(e)}"
        }


def detect_id_patterns(values: List[Any], column_name: str = "") -> Dict[str, Any]:
    """
    Detect if column contains various types of ID fields.
    
    Args:
        values: List of column values to analyze
        column_name: Name of the column (optional, improves detection accuracy)
        
    Returns:
        Dictionary with detection results
    """
    try:
        # Convert to strings and filter out nulls
        str_values = [str(v).strip() for v in values if v is not None and str(v).strip() != '']
        
        if len(str_values) < 2:
            return {
                'is_id': False,
                'confidence': 0.0,
                'id_type': 'insufficient_data',
                'reasoning': 'Insufficient data for ID detection'
            }
        
        # Check for business indicators first (should NOT be IDs)
        if column_name:
            column_lower = column_name.lower().replace(' ', '').replace('.', '').replace('_', '').replace('-', '')
            business_indicators = [
                'sales', 'revenue', 'amount', 'price', 'cost', 'value', 'total', 'sum',
                'quantity', 'count', 'volume', 'weight', 'height', 'width', 'length',
                'rate', 'percent', 'percentage', 'ratio', 'score', 'rating', 'points',
                'profit', 'loss', 'margin', 'commission', 'fee', 'tax', 'discount',
                'balance', 'payment', 'invoice', 'product', 'item', 'service'
            ]
            
            for indicator in business_indicators:
                if indicator in column_lower:
                    return {
                        'is_id': False,
                        'confidence': 0.1,
                        'id_type': 'business_data',
                        'reasoning': f"Column name '{column_name}' contains business indicator '{indicator}'"
                    }
        
        # ID patterns
        id_patterns = {
            'simple_numeric': r'^\d+$',
            'guid_uuid': r'^[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}$',
            'email_like': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
            'username_like': r'^[a-zA-Z0-9_.-]{3,}$',
            'alphanumeric_id': r'^[A-Z0-9]{4,}$',
            'prefixed_id': r'^[A-Z]{2,4}[0-9]{3,}$',
            'social_security': r'^\d{3}-\d{2}-\d{4}$'
        }
        
        matches = {}
        for pattern_name, pattern in id_patterns.items():
            pattern_matches = sum(1 for v in str_values if re.match(pattern, v.upper()))
            match_percentage = pattern_matches / len(str_values)
            matches[pattern_name] = {
                'matches': pattern_matches,
                'percentage': match_percentage
            }
        
        # Check uniqueness (IDs should be mostly unique)
        unique_ratio = len(set(str_values)) / len(str_values)
        
        # Check for typical ID characteristics
        avg_length = np.mean([len(v) for v in str_values])
        length_std = np.std([len(v) for v in str_values])
        
        confidence = 0.0
        reasoning_parts = []
        
        # Find best matching pattern
        best_pattern = max(matches.items(), key=lambda x: x[1]['percentage'])
        best_percentage = best_pattern[1]['percentage']
        
        if best_percentage >= 0.9:
            confidence += 0.6
            reasoning_parts.append(f"Strong pattern match ({best_pattern[0]}: {best_percentage:.1%})")
        elif best_percentage >= 0.7:
            confidence += 0.4
            reasoning_parts.append(f"Good pattern match ({best_pattern[0]}: {best_percentage:.1%})")
        
        # High uniqueness is typical of IDs
        if unique_ratio >= 0.95:
            confidence += 0.3
            reasoning_parts.append(f"High uniqueness ({unique_ratio:.1%})")
        elif unique_ratio >= 0.8:
            confidence += 0.1
            reasoning_parts.append(f"Good uniqueness ({unique_ratio:.1%})")
        
        # Consistent length is typical of IDs
        if length_std <= 2:
            confidence += 0.1
            reasoning_parts.append("Consistent length")
        
        is_id = confidence >= 0.4
        
        return {
            'is_id': is_id,
            'confidence': min(confidence, 1.0),
            'id_type': best_pattern[0] if is_id else 'none',
            'pattern_matches': matches,
            'unique_ratio': unique_ratio,
            'average_length': avg_length,
            'length_consistency': length_std,
            'reasoning': '; '.join(reasoning_parts) if reasoning_parts else 'No clear ID pattern detected'
        }
        
    except Exception as e:
        logger.error(f"Error in detect_id_patterns: {str(e)}")
        return {
            'is_id': False,
            'confidence': 0.0,
            'id_type': 'error',
            'reasoning': f"Error during analysis: {str(e)}"
        }


def detect_metadata_patterns(column_name: str, values: List[Any]) -> Dict[str, Any]:
    """
    Detect if column contains metadata (timestamps, status, etc.).
    
    Args:
        column_name: Name of the column
        values: List of column values to analyze
        
    Returns:
        Dictionary with detection results
    """
    try:
        # Convert to strings and filter out nulls
        str_values = [str(v).strip() for v in values if v is not None and str(v).strip() != '']
        
        if len(str_values) < 2:
            return {
                'is_metadata': False,
                'confidence': 0.0,
                'metadata_type': 'insufficient_data',
                'reasoning': 'Insufficient data for metadata detection'
            }
        
        # Metadata indicators by column name
        name_indicators = {
            'timestamp': ['timestamp', 'created', 'updated', 'modified', 'date', 'time'],
            'status': ['status', 'state', 'condition', 'flag'],
            'system': ['id', 'uid', 'guid', 'key', 'ref', 'reference'],
            'audit': ['created_by', 'updated_by', 'author', 'modifier'],
            'version': ['version', 'revision', 'build', 'release']
        }
        
        column_lower = column_name.lower()
        name_match_type = None
        name_confidence = 0.0
        
        for metadata_type, keywords in name_indicators.items():
            if any(keyword in column_lower for keyword in keywords):
                name_match_type = metadata_type
                name_confidence = 0.7  # High confidence for name-based detection
                break
        
        # Value pattern analysis
        value_patterns = {
            'timestamp': [
                r'\d{4}-\d{2}-\d{2}',  # Date
                r'\d{2}/\d{2}/\d{4}',  # US Date
                r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}',  # ISO timestamp
                r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}'   # SQL timestamp
            ],
            'status': [
                r'^(active|inactive|pending|approved|rejected|draft|published)$',
                r'^(true|false)$',
                r'^(yes|no)$',
                r'^(0|1)$'
            ],
            'boolean': [
                r'^(true|false)$',
                r'^(True|False)$',
                r'^(TRUE|FALSE)$',
                r'^(1|0)$'
            ]
        }
        
        pattern_matches = {}
        for pattern_type, patterns in value_patterns.items():
            total_matches = 0
            for pattern in patterns:
                matches = sum(1 for v in str_values if re.match(pattern, str(v), re.IGNORECASE))
                total_matches += matches
            
            match_percentage = min(total_matches / len(str_values), 1.0)
            pattern_matches[pattern_type] = match_percentage
        
        # Check for limited unique values (typical of categorical metadata)
        unique_values = set(str_values)
        unique_ratio = len(unique_values) / len(str_values)
        is_categorical = unique_ratio <= 0.1 and len(unique_values) <= 20
        
        # Calculate overall confidence
        confidence = name_confidence
        reasoning_parts = []
        
        if name_match_type:
            reasoning_parts.append(f"Column name indicates {name_match_type}")
        
        # Add pattern-based confidence
        best_pattern_match = max(pattern_matches.items(), key=lambda x: x[1])
        if best_pattern_match[1] >= 0.8:
            confidence += 0.2
            reasoning_parts.append(f"Strong {best_pattern_match[0]} pattern match")
        elif best_pattern_match[1] >= 0.5:
            confidence += 0.1
            reasoning_parts.append(f"Moderate {best_pattern_match[0]} pattern match")
        
        if is_categorical:
            confidence += 0.1
            reasoning_parts.append(f"Limited unique values ({len(unique_values)})")
        
        metadata_type = name_match_type or (best_pattern_match[0] if best_pattern_match[1] >= 0.5 else 'unknown')
        is_metadata = confidence >= 0.3
        
        return {
            'is_metadata': is_metadata,
            'confidence': min(confidence, 1.0),
            'metadata_type': metadata_type if is_metadata else 'none',
            'name_match': name_match_type,
            'pattern_matches': pattern_matches,
            'is_categorical': is_categorical,
            'unique_values_count': len(unique_values),
            'unique_ratio': unique_ratio,
            'reasoning': '; '.join(reasoning_parts) if reasoning_parts else 'No clear metadata pattern detected'
        }
        
    except Exception as e:
        logger.error(f"Error in detect_metadata_patterns: {str(e)}")
        return {
            'is_metadata': False,
            'confidence': 0.0,
            'metadata_type': 'error',
            'reasoning': f"Error during analysis: {str(e)}"
        }


def analyze_business_context(data: Dict[str, Any], industry: str = "", use_case: str = "", requirements: List[str] = None) -> str:
    """
    Generate comprehensive business context for AI-powered column classification.
    
    Args:
        data: Dictionary containing the dataset information  
        industry: Industry context (e.g., "e-commerce", "healthcare", "finance")
        use_case: Specific use case (e.g., "sales analysis", "customer segmentation")
        requirements: List of specific business requirements
        
    Returns:
        Formatted business context string for AI classification
    """
    try:
        context_parts = []
        
        # Basic data analysis
        rows = data.get('rows', [])
        columns = data.get('columns', [])
        
        if rows and columns:
            context_parts.append(f"Dataset: {len(rows)} records, {len(columns)} columns")
            
            # Analyze column characteristics for context
            numeric_indicators = []
            date_indicators = []
            text_indicators = []
            id_indicators = []
            
            for column in columns[:10]:  # Sample first 10 columns
                column_lower = column.lower()
                
                # Check for common patterns in column names
                if any(keyword in column_lower for keyword in ['amount', 'price', 'cost', 'revenue', 'quantity', 'count', 'number', 'rate', 'percent']):
                    numeric_indicators.append(column)
                elif any(keyword in column_lower for keyword in ['date', 'time', 'created', 'updated', 'modified']):
                    date_indicators.append(column)
                elif any(keyword in column_lower for keyword in ['id', 'uid', 'key', 'reference', 'code', 'serial']):
                    id_indicators.append(column)
                elif any(keyword in column_lower for keyword in ['name', 'description', 'title', 'category', 'status', 'type']):
                    text_indicators.append(column)
            
            if numeric_indicators:
                context_parts.append(f"Likely business metrics: {', '.join(numeric_indicators[:3])}")
            if id_indicators:
                context_parts.append(f"Likely identifiers (exclude): {', '.join(id_indicators[:3])}")
            if date_indicators:
                context_parts.append(f"Date/time fields: {', '.join(date_indicators[:3])}")
        
        # Industry-specific guidance
        industry_contexts = {
            "e-commerce": "Focus: sales amounts, quantities, order metrics, customer behavior. Exclude: order IDs, customer IDs, tracking codes",
            "healthcare": "Focus: patient outcomes, treatment metrics, costs. Exclude: patient IDs, SSNs, phone numbers (PHI compliance)",
            "finance": "Focus: financial metrics, returns, risk indicators. Exclude: account numbers, SSNs, transaction IDs",
            "manufacturing": "Focus: production volumes, costs, quality metrics. Exclude: serial numbers, part IDs, batch codes",
            "retail": "Focus: sales data, inventory levels, store performance. Exclude: product codes, customer IDs, store IDs",
            "saas": "Focus: usage metrics, subscription values, user engagement. Exclude: user IDs, session IDs, API keys",
            "marketing": "Focus: campaign performance, conversion rates, ROI. Exclude: customer IDs, email addresses, tracking IDs"
        }
        
        if industry and industry.lower() in industry_contexts:
            context_parts.append(f"Industry guidance ({industry}): {industry_contexts[industry.lower()]}")
        
        # Use case specific guidance
        use_case_contexts = {
            "sales analysis": "Prioritize: revenue, quantity, pricing metrics, sales periods. Key for forecasting and performance tracking",
            "customer segmentation": "Focus: behavioral metrics, purchase patterns, demographics. Avoid: individual identifiers",
            "financial reporting": "Emphasize: financial KPIs, costs, revenues, margins. Critical for executive dashboards",
            "operational dashboard": "Focus: efficiency metrics, volumes, cycle times. Real-time operational monitoring",
            "executive dashboard": "High-level: strategic KPIs, growth metrics, key performance indicators only",
            "inventory management": "Focus: stock levels, turnover rates, reorder points. Operational inventory insights",
            "quality control": "Emphasize: defect rates, quality scores, compliance metrics. Production quality tracking"
        }
        
        if use_case and use_case.lower() in use_case_contexts:
            context_parts.append(f"Use case focus ({use_case}): {use_case_contexts[use_case.lower()]}")
        
        # Specific requirements
        if requirements:
            context_parts.append(f"Special requirements: {'; '.join(requirements)}")
        
        # General classification rules
        context_parts.append("INCLUDE: numerical business data, quantities, amounts, rates, percentages, analytical dates")
        context_parts.append("EXCLUDE: IDs, serial numbers, phone numbers, emails, addresses, system timestamps, audit fields")
        
        return " | ".join(context_parts)
        
    except Exception as e:
        logger.error(f"Error in analyze_business_context: {str(e)}")
        return "General business data analysis for dashboard creation"

def ai_classify_columns(data: Dict[str, Any], business_context: str = "", model: str = "openrouter/anthropic/claude-3-haiku") -> Dict[str, Any]:
    """
    Use AI to directly classify columns for dashboard relevance.
    
    Args:
        data: Dictionary containing the dataset information
        business_context: Additional business context for better classification
        model: AI model to use for classification
        
    Returns:
        Dictionary with AI classification results
    """
    try:
        if not LITELLM_AVAILABLE:
            logger.warning("LiteLLM not available. Using enhanced fallback classification.")
            return fallback_column_classification(data)
        
        rows = data.get('rows', [])
        columns = data.get('columns', [])
        
        if not rows or not columns:
            return {
                'status': 'error',
                'message': 'Invalid data format - missing rows or columns'
            }
        
        # Prepare sample data for AI analysis
        sample_data = {}
        for column in columns:
            column_values = [row.get(column) for row in rows[:10]]  # Sample first 10 rows
            non_null_values = [str(v) for v in column_values if v is not None and str(v).strip() != '']
            sample_data[column] = {
                'sample_values': non_null_values[:5],  # Top 5 sample values
                'total_rows': len(rows),
                'non_null_count': len(non_null_values),
                'unique_count': len(set(non_null_values)) if non_null_values else 0
            }
        
        # Enhance business context if not provided or basic
        if not business_context or business_context == "General business data analysis for dashboard creation":
            business_context = analyze_business_context(data)
        
        # Create AI prompt for classification
        prompt = f"""You are analyzing Excel column data to determine which columns should be INCLUDED in dashboard calculations and which should be EXCLUDED.

Business Context: {business_context}

CLASSIFICATION RULES:
- INCLUDE: Columns with numerical data, business metrics, measurements, amounts, quantities, rates, percentages, dates for analysis
- EXCLUDE: Serial numbers, IDs, phone numbers, emails, addresses, system timestamps, status flags, reference codes

Column Data Analysis:
{json.dumps(sample_data, indent=2)}

For each column, classify as:
- INCLUDE: This column should be included in dashboard calculations
- EXCLUDE: This column should be excluded from dashboard calculations

Return ONLY a JSON object in this exact format:
{{
    "classifications": {{
        "column_name": {{
            "decision": "INCLUDE" or "EXCLUDE",
            "confidence": 0.0-1.0,
            "reasoning": "brief explanation"
        }}
    }},
    "summary": "overall analysis summary"
}}"""

        try:
            # Make AI call
            response = completion(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=1500
            )
            
            ai_content = response.choices[0].message.content.strip()
            
            # Extract JSON from response
            json_start = ai_content.find('{')
            json_end = ai_content.rfind('}') + 1
            
            if json_start == -1 or json_end == -1:
                raise ValueError("No JSON found in AI response")
            
            ai_result = json.loads(ai_content[json_start:json_end])
            
            # Process AI results into our format
            classifications = []
            relevant_columns = []
            irrelevant_columns = []
            
            for column in columns:
                ai_class = ai_result.get('classifications', {}).get(column, {})
                
                if ai_class:
                    decision = ai_class.get('decision', 'INCLUDE').upper()
                    confidence = ai_class.get('confidence', 0.5)
                    reasoning = ai_class.get('reasoning', 'AI classification')
                    
                    if decision == 'INCLUDE':
                        classification = 'relevant'
                        relevant_columns.append(column)
                    else:
                        classification = 'irrelevant'
                        irrelevant_columns.append(column)
                    
                    # Determine data type from sample
                    sample_values = sample_data[column]['sample_values']
                    data_type = 'unknown'
                    
                    if sample_values:
                        # Simple data type detection
                        try:
                            numeric_count = sum(1 for v in sample_values if str(v).replace('.', '').replace('-', '').isdigit())
                            if numeric_count >= len(sample_values) * 0.7:
                                data_type = 'numeric'
                            else:
                                unique_ratio = sample_data[column]['unique_count'] / max(sample_data[column]['non_null_count'], 1)
                                data_type = 'categorical' if unique_ratio <= 0.5 else 'text'
                        except:
                            data_type = 'mixed'
                    
                    classifications.append(ColumnClassification(
                        column_name=column,
                        classification=classification,
                        data_type=data_type,
                        confidence=confidence,
                        reasoning=reasoning,
                        sample_values=sample_values,
                        pattern_matches=['ai_classified']
                    ))
                else:
                    # Default to relevant if AI didn't classify
                    relevant_columns.append(column)
                    classifications.append(ColumnClassification(
                        column_name=column,
                        classification='relevant',
                        data_type='unknown',
                        confidence=0.5,
                        reasoning='Default classification - not analyzed by AI',
                        sample_values=sample_data[column]['sample_values'],
                        pattern_matches=['default']
                    ))
            
            overall_confidence = np.mean([c.confidence for c in classifications])
            
            result = DataFilteringResult(
                relevant_columns=relevant_columns,
                irrelevant_columns=irrelevant_columns,
                metadata_columns=[],  # AI classifies as include/exclude only
                column_classifications=classifications,
                confidence_score=overall_confidence,
                filtering_summary=ai_result.get('summary', 'AI-powered column classification completed'),
                total_columns_analyzed=len(columns),
                columns_filtered=len(irrelevant_columns),
                data_retention_percentage=(len(relevant_columns) / len(columns)) * 100
            )
            
            return {
                'status': 'success',
                'filtering_result': asdict(result),
                'detailed_classifications': [asdict(c) for c in classifications],
                'ai_summary': ai_result.get('summary', 'AI classification completed')
            }
            
        except Exception as ai_error:
            logger.error(f"AI classification failed: {ai_error}. Using enhanced fallback.")
            fallback_result = fallback_column_classification(data)
            fallback_result['ai_fallback_reason'] = f"AI failed: {str(ai_error)}"
            return fallback_result
            
    except Exception as e:
        logger.error(f"Error in ai_classify_columns: {str(e)}. Using enhanced fallback.")
        fallback_result = fallback_column_classification(data)
        fallback_result['main_error'] = f"Main function failed: {str(e)}"
        return fallback_result


def ai_enhanced_classification(data: Dict[str, Any], business_context: str = "") -> Dict[str, Any]:
    """
    Use AI to enhance column classification with business context analysis.
    
    Args:
        data: Dictionary containing the dataset information
        business_context: Additional business context for better classification
        
    Returns:
        Dictionary with AI-enhanced classification results
    """
    try:
        if not LITELLM_AVAILABLE:
            logger.warning("LiteLLM not available. Falling back to pattern-based classification.")
            return classify_column_patterns(data)
        
        rows = data.get('rows', [])
        columns = data.get('columns', [])
        
        if not rows or not columns:
            return {
                'status': 'error',
                'message': 'Invalid data format - missing rows or columns'
            }
        
        # Get initial pattern-based classification
        pattern_result = classify_column_patterns(data)
        
        if pattern_result['status'] != 'success':
            return pattern_result
        
        # Prepare data for AI analysis
        sample_data = {}
        for column in columns[:10]:  # Limit to first 10 columns for AI analysis
            column_values = [row.get(column) for row in rows[:20]]  # Sample first 20 rows
            non_null_values = [str(v) for v in column_values if v is not None and str(v).strip() != '']
            sample_data[column] = non_null_values[:5]  # Top 5 sample values
        
        # Create AI prompt for enhanced classification
        prompt = f"""Analyze the following Excel column data and classify each column as either:
1. RELEVANT - Data suitable for dashboard calculations and analytics
2. IRRELEVANT - Data that should be excluded from calculations (IDs, phone numbers, serial numbers, etc.)
3. METADATA - Descriptive information that provides context but isn't for calculation

Business Context: {business_context if business_context else "General business data analysis"}

Column Data:
{json.dumps(sample_data, indent=2)}

For each column, provide:
- Classification (RELEVANT/IRRELEVANT/METADATA)
- Confidence (0.0-1.0)
- Reasoning

Return the result as JSON in this format:
{{
    "classifications": {{
        "column_name": {{
            "classification": "RELEVANT|IRRELEVANT|METADATA",
            "confidence": 0.0-1.0,
            "reasoning": "explanation"
        }}
    }},
    "overall_confidence": 0.0-1.0,
    "summary": "brief summary of analysis"
}}"""

        try:
            # Make AI call with OpenRouter
            response = completion(
                model="openrouter/anthropic/claude-3-haiku",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=2000
            )
            
            ai_content = response.choices[0].message.content
            
            # Try to parse JSON from AI response
            try:
                # Extract JSON from response
                json_start = ai_content.find('{')
                json_end = ai_content.rfind('}') + 1
                if json_start != -1 and json_end != -1:
                    ai_result = json.loads(ai_content[json_start:json_end])
                else:
                    raise ValueError("No JSON found in AI response")
            except Exception as json_error:
                logger.warning(f"Failed to parse AI JSON response: {json_error}")
                return pattern_result  # Fall back to pattern-based result
            
            # Enhance pattern-based results with AI insights
            enhanced_classifications = []
            pattern_classifications = pattern_result['detailed_classifications']
            
            for pattern_class in pattern_classifications:
                column_name = pattern_class['column_name']
                
                # Get AI classification if available
                ai_class = ai_result.get('classifications', {}).get(column_name, {})
                
                if ai_class:
                    # Combine pattern and AI confidence
                    pattern_confidence = pattern_class['confidence']
                    ai_confidence = ai_class.get('confidence', 0.0)
                    combined_confidence = (pattern_confidence + ai_confidence) / 2
                    
                    # Use AI classification if confidence is high
                    if ai_confidence >= 0.7:
                        classification = ai_class['classification'].lower()
                        reasoning = f"AI-enhanced: {ai_class.get('reasoning', '')}; Pattern: {pattern_class['reasoning']}"
                    else:
                        classification = pattern_class['classification']
                        reasoning = f"Pattern-based: {pattern_class['reasoning']}; AI input: {ai_class.get('reasoning', 'low confidence')}"
                    
                    enhanced_classifications.append(ColumnClassification(
                        column_name=column_name,
                        classification=classification,
                        data_type=pattern_class['data_type'],
                        confidence=combined_confidence,
                        reasoning=reasoning,
                        sample_values=pattern_class['sample_values'],
                        pattern_matches=pattern_class['pattern_matches'] + ['ai_enhanced']
                    ))
                else:
                    # Keep original pattern-based classification
                    enhanced_classifications.append(ColumnClassification(**pattern_class))
            
            # Update result with enhanced classifications
            relevant_columns = [c.column_name for c in enhanced_classifications if c.classification == 'relevant']
            irrelevant_columns = [c.column_name for c in enhanced_classifications if c.classification == 'irrelevant']
            metadata_columns = [c.column_name for c in enhanced_classifications if c.classification == 'metadata']
            
            overall_confidence = np.mean([c.confidence for c in enhanced_classifications])
            
            enhanced_result = DataFilteringResult(
                relevant_columns=relevant_columns,
                irrelevant_columns=irrelevant_columns,
                metadata_columns=metadata_columns,
                column_classifications=enhanced_classifications,
                confidence_score=overall_confidence,
                filtering_summary=f"AI-enhanced analysis: {ai_result.get('summary', 'Enhanced with AI insights')}",
                total_columns_analyzed=len(columns),
                columns_filtered=len(irrelevant_columns),
                data_retention_percentage=(len(relevant_columns) / len(columns)) * 100
            )
            
            return {
                'status': 'success',
                'filtering_result': asdict(enhanced_result),
                'detailed_classifications': [asdict(c) for c in enhanced_classifications],
                'ai_enhanced': True,
                'ai_summary': ai_result.get('summary', 'AI enhancement applied')
            }
            
        except Exception as ai_error:
            logger.warning(f"AI enhancement failed: {ai_error}. Using pattern-based classification.")
            return pattern_result
            
    except Exception as e:
        logger.error(f"Error in ai_enhanced_classification: {str(e)}")
        return {
            'status': 'error',
            'message': f"Failed to perform AI-enhanced classification: {str(e)}"
        }


def fallback_column_classification(data: Dict[str, Any], confidence_threshold: float = 0.6) -> Dict[str, Any]:
    """
    Enhanced rule-based fallback system for column classification.
    Provides conservative, reliable classification when AI services are unavailable.
    
    Args:
        data: Dictionary containing the dataset information
        confidence_threshold: Minimum confidence required for classification (default: 0.6)
        
    Returns:
        Dictionary with classification results and safety guarantees
    """
    try:
        rows = data.get('rows', [])
        columns = data.get('columns', [])
        
        if not rows or not columns:
            return {
                'status': 'error',
                'message': 'Invalid data format - missing rows or columns'
            }
        
        classifications = []
        safety_warnings = []
        
        for column in columns:
            # Extract column values
            column_values = [row.get(column) for row in rows]
            
            # Safely handle datetime objects and other special types when filtering non-null values
            non_null_values = []
            for v in column_values:
                if v is not None:
                    try:
                        # Convert to string safely (handles datetime objects)
                        str_v = str(v).strip()
                        if str_v != '':
                            non_null_values.append(v)  # Keep original value, not string version
                    except Exception:
                        # If str() fails, skip this value
                        continue
            
            if len(non_null_values) < 2:
                classifications.append(ColumnClassification(
                    column_name=column,
                    classification='irrelevant',
                    data_type='insufficient_data',
                    confidence=0.8,
                    reasoning='Insufficient non-null data',
                    sample_values=[str(v) for v in non_null_values[:5]],
                    pattern_matches=[]
                ))
                safety_warnings.append(f"Column '{column}' has insufficient data - included for safety")
                continue
            
            # Conservative classification logic
            classification_result = _apply_conservative_rules(column, non_null_values, confidence_threshold)
            
            classifications.append(ColumnClassification(
                column_name=column,
                classification=classification_result['classification'],
                data_type=classification_result['data_type'],
                confidence=classification_result['confidence'],
                reasoning=classification_result['reasoning'],
                sample_values=classification_result['sample_values'],
                pattern_matches=classification_result['pattern_matches']
            ))
            
            # Add safety warnings for borderline cases
            if classification_result['confidence'] < confidence_threshold and classification_result['classification'] == 'irrelevant':
                safety_warnings.append(f"Column '{column}' classified as irrelevant with low confidence - verify manually")
        
        # Separate columns by classification
        relevant_columns = [c.column_name for c in classifications if c.classification == 'relevant']
        irrelevant_columns = [c.column_name for c in classifications if c.classification == 'irrelevant']
        metadata_columns = [c.column_name for c in classifications if c.classification == 'metadata']
        
        # Safety checks
        if len(relevant_columns) < len(columns) * 0.3:  # Less than 30% relevant is suspicious
            safety_warnings.append("Warning: Very few columns classified as relevant - review classifications")
        
        overall_confidence = np.mean([c.confidence for c in classifications])
        
        result = DataFilteringResult(
            relevant_columns=relevant_columns,
            irrelevant_columns=irrelevant_columns,
            metadata_columns=metadata_columns,
            column_classifications=classifications,
            confidence_score=overall_confidence,
            filtering_summary=f"Rule-based fallback classification completed. {len(safety_warnings)} safety warnings.",
            total_columns_analyzed=len(columns),
            columns_filtered=len(irrelevant_columns),
            data_retention_percentage=(len(relevant_columns) / len(columns)) * 100
        )
        
        return {
            'status': 'success',
            'filtering_result': asdict(result),
            'detailed_classifications': [asdict(c) for c in classifications],
            'safety_warnings': safety_warnings,
            'fallback_used': True,
            'confidence_threshold': confidence_threshold
        }
        
    except Exception as e:
        logger.error(f"Error in fallback_column_classification: {str(e)}")
        # Emergency fallback - include all columns for safety
        emergency_result = _emergency_safe_classification(data)
        return emergency_result

def _apply_conservative_rules(column_name: str, values: List[Any], confidence_threshold: float) -> Dict[str, Any]:
    """
    Apply conservative classification rules with safety-first approach.
    
    Args:
        column_name: Name of the column
        values: List of non-null values
        confidence_threshold: Minimum confidence for classification
        
    Returns:
        Classification result with conservative bias toward inclusion
    """
    sample_values = [str(v) for v in values[:5]]
    column_lower = column_name.lower()
    
    # High-confidence exclusion patterns (only exclude if very certain)
    high_confidence_exclusions = {
        'id_patterns': ['id', 'uid', 'guid', 'key', '_id', 'ref', 'reference'],
        'contact_patterns': ['phone', 'email', 'address', 'postal', 'zip'],
        'system_patterns': ['created_at', 'updated_at', 'timestamp', 'modified', 'audit'],
        'serial_patterns': ['serial', 'barcode', 'sku', 'code', 'tracking']
    }
    
    # Check for clear exclusion patterns
    for pattern_type, patterns in high_confidence_exclusions.items():
        if any(pattern in column_lower for pattern in patterns):
            # Verify with data patterns for high confidence
            verification_result = _verify_exclusion_pattern(values, pattern_type)
            
            if verification_result['confidence'] >= 0.8:
                return {
                    'classification': 'irrelevant',
                    'data_type': verification_result['data_type'],
                    'confidence': verification_result['confidence'],
                    'reasoning': f"High-confidence {pattern_type} exclusion: {verification_result['reasoning']}",
                    'sample_values': sample_values,
                    'pattern_matches': ['fallback_exclusion', pattern_type]
                }
    
    # Check for clear inclusion patterns
    business_patterns = ['amount', 'price', 'cost', 'revenue', 'quantity', 'count', 'rate', 'percent', 'total', 'value']
    if any(pattern in column_lower for pattern in business_patterns):
        # Try to verify it's actually numeric/business data
        numeric_verification = _verify_business_metric(values)
        if numeric_verification['confidence'] >= 0.7:
            return {
                'classification': 'relevant',
                'data_type': 'numeric',
                'confidence': numeric_verification['confidence'],
                'reasoning': f"High-confidence business metric: {numeric_verification['reasoning']}",
                'sample_values': sample_values,
                'pattern_matches': ['fallback_inclusion', 'business_metric']
            }
    
    # Default conservative classification - favor inclusion for safety
    data_type_result = _determine_data_type(values)
    
    # Conservative logic: only exclude if very confident it's not business data
    if data_type_result['type'] in ['text', 'mixed'] and len(set(str(v) for v in values)) == len(values):
        # High uniqueness text data might be identifiers
        return {
            'classification': 'metadata',  # Safer than irrelevant
            'data_type': data_type_result['type'],
            'confidence': 0.6,
            'reasoning': 'Conservative: unique text data classified as metadata for safety',
            'sample_values': sample_values,
            'pattern_matches': ['fallback_conservative', 'metadata_safe']
        }
    
    # Default to relevant for safety
    return {
        'classification': 'relevant',
        'data_type': data_type_result['type'],
        'confidence': 0.5,
        'reasoning': 'Conservative fallback: defaulting to relevant for safety',
        'sample_values': sample_values,
        'pattern_matches': ['fallback_safe', 'default_relevant']
    }

def _verify_exclusion_pattern(values: List[Any], pattern_type: str) -> Dict[str, Any]:
    """Verify that data matches exclusion patterns before excluding."""
    str_values = [str(v).strip() for v in values if v is not None]
    
    if pattern_type == 'id_patterns':
        # Check for ID characteristics
        unique_ratio = len(set(str_values)) / len(str_values)
        avg_length = np.mean([len(v) for v in str_values])
        
        if unique_ratio > 0.95 and (avg_length < 3 or avg_length > 50):
            return {'confidence': 0.9, 'data_type': 'identifier', 'reasoning': 'High uniqueness + typical ID length'}
        elif unique_ratio > 0.9:
            return {'confidence': 0.7, 'data_type': 'identifier', 'reasoning': 'High uniqueness suggests ID'}
        
    elif pattern_type == 'contact_patterns':
        # Simple pattern checks for contact info
        email_like = sum(1 for v in str_values if '@' in v and '.' in v)
        phone_like = sum(1 for v in str_values if any(c.isdigit() for c in v) and len(v) >= 10)
        
        if email_like >= len(str_values) * 0.8:
            return {'confidence': 0.95, 'data_type': 'contact', 'reasoning': 'Email pattern detected'}
        elif phone_like >= len(str_values) * 0.7:
            return {'confidence': 0.85, 'data_type': 'contact', 'reasoning': 'Phone pattern detected'}
    
    return {'confidence': 0.3, 'data_type': 'unknown', 'reasoning': 'Pattern not verified'}

def _verify_business_metric(values: List[Any]) -> Dict[str, Any]:
    """Verify that data appears to be business metrics."""
    try:
        numeric_values = []
        for v in values:
            try:
                numeric_values.append(float(str(v).replace(',', '').replace('$', '')))
            except:
                continue
        
        if len(numeric_values) >= len(values) * 0.8:
            # Check for reasonable business metric characteristics
            if len(numeric_values) > 1:
                std_dev = np.std(numeric_values)
                mean_val = np.mean(numeric_values)
                
                # Business metrics usually have some variation
                if std_dev > 0 and mean_val > 0:
                    return {'confidence': 0.9, 'reasoning': 'Numeric data with business-like variation'}
            
            return {'confidence': 0.7, 'reasoning': 'High numeric content'}
        
        return {'confidence': 0.3, 'reasoning': 'Low numeric content'}
        
    except Exception:
        return {'confidence': 0.2, 'reasoning': 'Error in numeric verification'}

def _determine_data_type(values: List[Any]) -> Dict[str, str]:
    """Determine the primary data type of the column."""
    str_values = [str(v) for v in values]
    
    # Count different types
    numeric_count = 0
    date_count = 0
    
    for v in str_values:
        # Simple numeric check
        try:
            float(v.replace(',', '').replace('$', '').replace('%', ''))
            numeric_count += 1
            continue
        except:
            pass
        
        # Simple date check
        if any(pattern in v for pattern in ['-', '/', '2024', '2023', '2022', '2021', '2020']):
            date_count += 1
    
    total = len(str_values)
    if numeric_count >= total * 0.7:
        return {'type': 'numeric'}
    elif date_count >= total * 0.5:
        return {'type': 'date'}
    elif len(set(str_values)) <= total * 0.5:
        return {'type': 'categorical'}
    else:
        return {'type': 'text'}

def _emergency_safe_classification(data: Dict[str, Any]) -> Dict[str, Any]:
    """Emergency fallback - include all columns for safety."""
    columns = data.get('columns', [])
    
    classifications = []
    for column in columns:
        classifications.append(ColumnClassification(
            column_name=column,
            classification='relevant',
            data_type='unknown',
            confidence=0.1,
            reasoning='Emergency fallback - all columns included for safety',
            sample_values=[],
            pattern_matches=['emergency_safe']
        ))
    
    result = DataFilteringResult(
        relevant_columns=columns,
        irrelevant_columns=[],
        metadata_columns=[],
        column_classifications=classifications,
        confidence_score=0.1,
        filtering_summary="Emergency fallback activated - all columns included for safety",
        total_columns_analyzed=len(columns),
        columns_filtered=0,
        data_retention_percentage=100.0
    )
    
    return {
        'status': 'success',
        'filtering_result': asdict(result),
        'detailed_classifications': [asdict(c) for c in classifications],
        'safety_warnings': ['Emergency fallback used - manual review recommended'],
        'emergency_fallback': True
    }

def classify_column_patterns(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze all columns in the dataset and classify them using pattern recognition.
    
    Args:
        data: Dictionary containing the dataset information
        
    Returns:
        Dictionary with classification results for all columns
    """
    try:
        rows = data.get('rows', [])
        columns = data.get('columns', [])
        
        if not rows or not columns:
            return {
                'status': 'error',
                'message': 'Invalid data format - missing rows or columns'
            }
        
        classifications = []
        
        for column in columns:
            # Extract column values
            column_values = [row.get(column) for row in rows]
            
            # Safely handle datetime objects and other special types when filtering non-null values
            non_null_values = []
            for v in column_values:
                if v is not None:
                    try:
                        # Convert to string safely (handles datetime objects)
                        str_v = str(v).strip()
                        if str_v != '':
                            non_null_values.append(v)  # Keep original value, not string version
                    except Exception:
                        # If str() fails, skip this value
                        continue
            
            if len(non_null_values) < 2:
                classifications.append(ColumnClassification(
                    column_name=column,
                    classification='irrelevant',
                    data_type='insufficient_data',
                    confidence=0.8,
                    reasoning='Insufficient non-null data',
                    sample_values=[str(v) for v in non_null_values[:5]],
                    pattern_matches=[]
                ))
                continue
            
            # Run all pattern detection functions
            serial_result = detect_serial_number_patterns(non_null_values, column)
            phone_result = detect_phone_number_patterns(non_null_values)
            id_result = detect_id_patterns(non_null_values, column)
            metadata_result = detect_metadata_patterns(column, non_null_values)
            
            # Determine classification based on pattern matches
            classification = 'relevant'  # Default
            confidence = 0.0
            reasoning_parts = []
            pattern_matches = []
            data_type = 'unknown'
            
            # Check for irrelevant patterns (highest priority)
            if serial_result['is_serial'] and serial_result['confidence'] >= 0.6:
                classification = 'irrelevant'
                confidence = serial_result['confidence']
                data_type = 'serial_number'
                reasoning_parts.append('Serial number pattern detected')
                pattern_matches.append('serial_number')
                
            elif phone_result['is_phone'] and phone_result['confidence'] >= 0.7:
                classification = 'irrelevant'
                confidence = phone_result['confidence']
                data_type = 'phone_number'
                reasoning_parts.append('Phone number pattern detected')
                pattern_matches.append('phone_number')
                
            elif id_result['is_id'] and id_result['confidence'] >= 0.6:
                classification = 'irrelevant'
                confidence = id_result['confidence']
                data_type = 'identifier'
                reasoning_parts.append('ID pattern detected')
                pattern_matches.append('identifier')
            
            # Check for metadata patterns
            elif metadata_result['is_metadata'] and metadata_result['confidence'] >= 0.5:
                classification = 'metadata'
                confidence = metadata_result['confidence']
                data_type = metadata_result['metadata_type']
                reasoning_parts.append(f"Metadata pattern detected ({metadata_result['metadata_type']})")
                pattern_matches.append('metadata')
            
            # If no clear pattern, assume relevant but check for some indicators
            else:
                # Check for potentially relevant numerical data
                try:
                    numeric_values = []
                    for v in non_null_values[:50]:  # Sample
                        try:
                            if isinstance(v, (int, float)):
                                numeric_values.append(float(v))
                            else:
                                # Try to parse as number
                                clean_v = re.sub(r'[^\d.-]', '', str(v))
                                if clean_v:
                                    numeric_values.append(float(clean_v))
                        except:
                            continue
                    
                    if len(numeric_values) >= len(non_null_values) * 0.7:
                        # Mostly numeric, likely relevant for analysis
                        data_type = 'numeric'
                        confidence = 0.8
                        reasoning_parts.append('Numeric data suitable for analysis')
                    else:
                        # Text data, might be categorical
                        unique_ratio = len(set(non_null_values)) / len(non_null_values)
                        if unique_ratio <= 0.5:
                            data_type = 'categorical'
                            confidence = 0.7
                            reasoning_parts.append('Categorical data suitable for analysis')
                        else:
                            data_type = 'text'
                            confidence = 0.6
                            reasoning_parts.append('Text data, relevance uncertain')
                
                except Exception:
                    data_type = 'mixed'
                    confidence = 0.5
                    reasoning_parts.append('Mixed data type')
            
            reasoning = '; '.join(reasoning_parts) if reasoning_parts else 'No specific patterns detected'
            
            classifications.append(ColumnClassification(
                column_name=column,
                classification=classification,
                data_type=data_type,
                confidence=confidence,
                reasoning=reasoning,
                sample_values=[str(v) for v in non_null_values[:5]],
                pattern_matches=pattern_matches
            ))
        
        # Summarize results
        relevant_columns = [c.column_name for c in classifications if c.classification == 'relevant']
        irrelevant_columns = [c.column_name for c in classifications if c.classification == 'irrelevant']
        metadata_columns = [c.column_name for c in classifications if c.classification == 'metadata']
        
        overall_confidence = np.mean([c.confidence for c in classifications])
        columns_filtered = len(irrelevant_columns)
        data_retention_percentage = (len(relevant_columns) / len(columns)) * 100
        
        summary_parts = [
            f"Analyzed {len(columns)} columns",
            f"Identified {len(relevant_columns)} relevant columns",
            f"Filtered out {len(irrelevant_columns)} irrelevant columns",
            f"Found {len(metadata_columns)} metadata columns"
        ]
        
        result = DataFilteringResult(
            relevant_columns=relevant_columns,
            irrelevant_columns=irrelevant_columns,
            metadata_columns=metadata_columns,
            column_classifications=classifications,
            confidence_score=overall_confidence,
            filtering_summary='; '.join(summary_parts),
            total_columns_analyzed=len(columns),
            columns_filtered=columns_filtered,
            data_retention_percentage=data_retention_percentage
        )
        
        return {
            'status': 'success',
            'filtering_result': asdict(result),
            'detailed_classifications': [asdict(c) for c in classifications]
        }
        
    except Exception as e:
        logger.error(f"Error in classify_column_patterns: {str(e)}")
        return {
            'status': 'error',
            'message': f"Failed to classify columns: {str(e)}"
        }


class IntelligentDataFilterAgent:
    """
    Intelligent Data Filter Agent using Google ADK.
    
    This agent handles intelligent data filtering to eliminate irrelevant columns
    from dashboard calculations using AI-powered pattern recognition.
    """
    
    def __init__(self, model: str = "gemini-2.0-flash-exp"):
        """
        Initialize the Intelligent Data Filter Agent.
        
        Args:
            model: The LLM model to use for the agent
        """
        # Create function tools
        self.ai_classification_tool = FunctionTool(func=ai_classify_columns)
        self.business_context_tool = FunctionTool(func=analyze_business_context)
        self.enhanced_classification_tool = FunctionTool(func=ai_enhanced_classification)
        self.fallback_classification_tool = FunctionTool(func=fallback_column_classification)
        self.pattern_classification_tool = FunctionTool(func=classify_column_patterns)
        
        self.agent = Agent(
            model=model,
            name="intelligent_data_filter_agent",
            description="Specialized agent for intelligent data filtering. Identifies and eliminates irrelevant columns from dashboard calculations using AI-powered pattern recognition.",
            instruction="""You are the Intelligent Data Filter Agent, responsible for determining which columns should be INCLUDED or EXCLUDED from dashboard calculations using AI-powered analysis.

Your primary capability:
- AI-Powered Column Classification: Use AI models to intelligently determine column relevance for dashboard analytics

Core Functions:
1. ai_classify_columns: Primary function that uses AI to classify columns as INCLUDE/EXCLUDE for dashboard calculations
2. analyze_business_context: Generate comprehensive business context from industry, use case, and data characteristics
3. ai_enhanced_classification: Enhanced version combining AI analysis with pattern recognition
4. fallback_column_classification: Enhanced rule-based fallback system with safety guarantees and conservative classification
5. classify_column_patterns: Basic pattern-based classification for reference

Decision Criteria:
- INCLUDE: Numerical data, business metrics, measurements, amounts, quantities, rates, percentages, analytical dates
- EXCLUDE: Serial numbers, IDs, phone numbers, emails, addresses, system timestamps, status flags, reference codes

When analyzing data:
- Use ai_classify_columns as the primary method for column classification
- Use analyze_business_context to generate industry/use-case specific guidance when business context is needed
- Provide comprehensive business context (industry, use case, requirements) to improve AI decision accuracy
- Use ai_enhanced_classification for combining AI analysis with pattern recognition when maximum accuracy is needed
- Use fallback_column_classification when AI services are unavailable - provides safety-first conservative classification
- The fallback system includes safety warnings, confidence thresholds, and emergency protocols
- Always explain the reasoning behind each classification decision
- Maintain high accuracy to avoid excluding important business data
- Prioritize data inclusion over exclusion when in doubt (safety-first approach)

The AI model will analyze column names, sample data, and business context to make intelligent inclusion/exclusion decisions that optimize dashboard relevance and analytical value.""",
            tools=[
                self.ai_classification_tool,
                self.business_context_tool,
                self.enhanced_classification_tool,
                self.fallback_classification_tool,
                self.pattern_classification_tool
            ]
        )
        
        logger.info("Intelligent Data Filter Agent initialized successfully")
    
    def get_agent(self) -> Agent:
        """Return the ADK agent instance."""
        return self.agent 