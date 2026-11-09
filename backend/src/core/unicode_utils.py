"""
Unicode Utilities for Analytics Hub
Provides safe Unicode handling for Windows systems and general cross-platform compatibility.
"""

import sys
import logging
import json
from typing import Any, Dict, List, Union, Optional

logger = logging.getLogger(__name__)

# Common Unicode replacements for logging and display
UNICODE_REPLACEMENTS = {
    # Currency symbols
    '₹': 'INR', '€': 'EUR', '£': 'GBP', '¥': 'JPY', '₩': 'KRW',
    '$': 'USD', '¢': 'cents', '₽': 'RUB', '₨': 'Rs',
    
    # Emoji symbols commonly used in logging
    '✅': '[OK]', '❌': '[FAIL]', '⚠️': '[WARN]', '❗': '[ALERT]',
    '🎯': '[TARGET]', '🔍': '[SEARCH]', '📊': '[CHART]', '📈': '[TREND]',
    '🔬': '[ANALYSIS]', '🔗': '[LINK]', '📌': '[PIN]', '🤖': '[AI]',
    '⏱️': '[PENDING]', '🚀': '[START]', '✨': '[NEW]', '🛠️': '[TOOL]',
    '💡': '[IDEA]', '🔧': '[FIX]', '📝': '[NOTE]', '🎉': '[SUCCESS]',
    '🔄': '[PROCESS]', '🛑': '[STOP]', '💾': '[SAVE]', '🔐': '[SECURE]',
    '🌟': '[STAR]', '⭐': '[RATING]', '🏆': '[WINNER]', '📋': '[LIST]',
    
    # Mathematical and special symbols
    '≈': '~=', '≠': '!=', '≤': '<=', '≥': '>=', '±': '+/-',
    '×': 'x', '÷': '/', '°': 'deg', '²': '^2', '³': '^3',
    '½': '1/2', '¼': '1/4', '¾': '3/4', '→': '->', '←': '<-',
    
    # Quotation marks
    '"': '"', '"': '"', ''': "'", ''': "'", '«': '<<', '»': '>>',
    
    # Dashes and spaces
    '—': '--', '–': '-', ' ': ' ',  # Non-breaking space to regular space
    
    # Other common symbols
    '…': '...', '™': '(TM)', '®': '(R)', '©': '(C)', '§': 'Section',
    '¶': 'Para', '•': '*', '·': '.', '‚': ',', '„': '"',
}

def safe_str(obj: Any, fallback: str = "[UNREPRESENTABLE]") -> str:
    """
    Convert any object to a safe ASCII string representation.
    
    Args:
        obj: The object to convert
        fallback: String to use if conversion fails
        
    Returns:
        Safe ASCII string representation
    """
    try:
        if obj is None:
            return "None"
        
        # Convert to string
        if hasattr(obj, '__str__'):
            text = str(obj)
        else:
            text = repr(obj)
        
        # Replace Unicode characters
        for unicode_char, replacement in UNICODE_REPLACEMENTS.items():
            text = text.replace(unicode_char, replacement)
        
        # Encode to ASCII with replacement characters
        return text.encode('ascii', errors='replace').decode('ascii')
        
    except Exception as e:
        logger.warning(f"Failed to convert object to safe string: {e}")
        return fallback

def safe_log_message(message: str) -> str:
    """
    Convert a log message to ASCII-safe format for logging on Windows.
    
    Args:
        message: The log message to make safe
        
    Returns:
        ASCII-safe version of the message
    """
    try:
        # Replace problematic Unicode characters
        safe_message = message
        for unicode_char, replacement in UNICODE_REPLACEMENTS.items():
            safe_message = safe_message.replace(unicode_char, replacement)
        
        # Encode to ASCII, replacing any remaining problematic characters
        safe_message = safe_message.encode('ascii', errors='replace').decode('ascii')
        return safe_message
    except Exception:
        # Fallback: remove all non-ASCII characters
        return ''.join(char for char in message if ord(char) < 128)

def safe_dict_for_json(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert a dictionary to be JSON-safe by handling Unicode and non-serializable objects.
    
    Args:
        data: Dictionary to make JSON-safe
        
    Returns:
        JSON-safe dictionary
    """
    def convert_value(value):
        if value is None:
            return None
        elif isinstance(value, (str, int, float, bool)):
            return safe_str(value) if isinstance(value, str) else value
        elif isinstance(value, dict):
            return {safe_str(k): convert_value(v) for k, v in value.items()}
        elif isinstance(value, (list, tuple)):
            return [convert_value(item) for item in value]
        else:
            return safe_str(value)
    
    try:
        return {safe_str(k): convert_value(v) for k, v in data.items()}
    except Exception as e:
        logger.warning(f"Failed to convert dictionary for JSON: {e}")
        return {"error": "Failed to convert data"}

def safe_json_dumps(data: Any, **kwargs) -> str:
    """
    JSON dumps with safe Unicode handling.
    
    Args:
        data: Data to serialize
        **kwargs: Additional arguments for json.dumps
        
    Returns:
        JSON string with safe Unicode handling
    """
    try:
        # Set default ensure_ascii to True for safety
        kwargs.setdefault('ensure_ascii', True)
        kwargs.setdefault('errors', 'replace')
        
        if isinstance(data, dict):
            safe_data = safe_dict_for_json(data)
        elif isinstance(data, (list, tuple)):
            safe_data = [safe_dict_for_json(item) if isinstance(item, dict) else safe_str(item) 
                        for item in data]
        else:
            safe_data = safe_str(data)
        
        return json.dumps(safe_data, **kwargs)
    except Exception as e:
        logger.warning(f"Failed to serialize to JSON: {e}")
        return json.dumps({"error": f"Serialization failed: {safe_str(e)}"}, ensure_ascii=True)

def configure_safe_stdout():
    """
    Configure stdout and stderr for safe Unicode handling on Windows.
    """
    try:
        if sys.platform.startswith('win') and hasattr(sys.stdout, 'reconfigure'):
            try:
                sys.stdout.reconfigure(encoding='utf-8', errors='replace')
                sys.stderr.reconfigure(encoding='utf-8', errors='replace')
                logger.info("[OK] Console encoding configured for UTF-8")
                return True
            except Exception as e:
                logger.warning(f"[WARN] Could not configure console encoding: {e}")
                return False
    except Exception as e:
        logger.warning(f"[WARN] Error in stdout configuration: {e}")
        return False

def is_ascii_safe(text: str) -> bool:
    """
    Check if a string is ASCII-safe.
    
    Args:
        text: String to check
        
    Returns:
        True if the string is ASCII-safe
    """
    try:
        text.encode('ascii')
        return True
    except UnicodeEncodeError:
        return False

def get_safe_filename(filename: str) -> str:
    """
    Convert a filename to be safe for filesystem operations.
    
    Args:
        filename: Original filename
        
    Returns:
        Filesystem-safe filename
    """
    try:
        # Replace problematic characters for filenames
        unsafe_chars = '<>:"/\\|?*'
        safe_filename = filename
        
        for char in unsafe_chars:
            safe_filename = safe_filename.replace(char, '_')
        
        # Handle Unicode characters
        safe_filename = safe_str(safe_filename)
        
        # Remove leading/trailing spaces and dots
        safe_filename = safe_filename.strip('. ')
        
        # Ensure we have a filename
        if not safe_filename:
            safe_filename = "unnamed_file"
        
        return safe_filename
    except Exception:
        return "safe_filename"

# Auto-configure on import
configure_safe_stdout() 