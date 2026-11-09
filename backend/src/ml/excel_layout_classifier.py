"""
ML-based Excel Layout Classifier

Trains and uses machine learning models to classify Excel layout types.
Features are extracted from cell patterns, formatting, and structure.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
import logging
import pickle
import os
from pathlib import Path

try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logging.warning("scikit-learn not available, ML classification disabled")

logger = logging.getLogger(__name__)


@dataclass
class LayoutFeatures:
    """Features extracted from Excel sheet for ML classification."""
    # Dimension features
    n_rows: int
    n_cols: int
    aspect_ratio: float
    
    # Content features
    text_density: float
    numeric_density: float
    empty_cell_ratio: float
    
    # Pattern features
    first_row_text_ratio: float
    first_col_text_ratio: float
    interior_numeric_ratio: float
    
    # Formatting features
    bold_cell_ratio: float
    merged_cell_count: int
    merged_in_top_rows: int
    
    # Statistical features
    col_variance: float
    row_variance: float
    
    def to_array(self) -> np.ndarray:
        """Convert features to numpy array for ML model."""
        return np.array([
            self.n_rows,
            self.n_cols,
            self.aspect_ratio,
            self.text_density,
            self.numeric_density,
            self.empty_cell_ratio,
            self.first_row_text_ratio,
            self.first_col_text_ratio,
            self.interior_numeric_ratio,
            self.bold_cell_ratio,
            self.merged_cell_count,
            self.merged_in_top_rows,
            self.col_variance,
            self.row_variance
        ])


class ExcelLayoutClassifier:
    """
    ML-based classifier for Excel layout types.
    Uses Random Forest to classify layouts based on extracted features.
    """
    
    # Layout type mapping
    LAYOUT_TYPES = {
        0: 'standard',
        1: 'transposed',
        2: 'pivot',
        3: 'crosstab',
        4: 'hierarchical',
        5: 'mixed'
    }
    
    LAYOUT_TO_INT = {v: k for k, v in LAYOUT_TYPES.items()}
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize the classifier.
        
        Args:
            model_path: Path to saved model file (None = train new model)
        """
        self.model = None
        self.scaler = None
        self.model_path = model_path or os.path.join(
            os.path.dirname(__file__), 
            '../../.models/excel_layout_classifier.pkl'
        )
        
        if SKLEARN_AVAILABLE:
            if os.path.exists(self.model_path):
                self.load_model()
            else:
                logger.info("No trained model found, will use heuristic classification")
        else:
            logger.warning("scikit-learn not available, ML classification disabled")
    
    def extract_features(self, sheet) -> LayoutFeatures:
        """
        Extract features from an Excel sheet for classification.
        
        Args:
            sheet: openpyxl worksheet object
            
        Returns:
            LayoutFeatures object
        """
        max_row = sheet.max_row
        max_col = sheet.max_column
        
        # Sample cells (limit to first 50 rows and 30 cols for efficiency)
        sample_rows = min(max_row, 50)
        sample_cols = min(max_col, 30)
        
        # Count cell types
        text_count = 0
        numeric_count = 0
        empty_count = 0
        bold_count = 0
        
        first_row_text = 0
        first_row_total = 0
        first_col_text = 0
        first_col_total = 0
        
        interior_numeric = 0
        interior_total = 0
        
        # Cell value variance by row and column
        row_type_variance = []
        col_type_variance = []
        
        for row_idx in range(1, sample_rows + 1):
            row_numeric = 0
            row_total = 0
            
            for col_idx in range(1, sample_cols + 1):
                cell = sheet.cell(row=row_idx, column=col_idx)
                value = cell.value
                
                # Count by type
                if value is None or value == '':
                    empty_count += 1
                elif isinstance(value, (int, float)):
                    numeric_count += 1
                    row_numeric += 1
                    row_total += 1
                    
                    # First row/col stats
                    if row_idx == 1:
                        first_row_total += 1
                    if col_idx == 1:
                        first_col_total += 1
                    
                    # Interior stats (not first row/col)
                    if row_idx > 1 and col_idx > 1:
                        interior_numeric += 1
                        interior_total += 1
                else:
                    text_count += 1
                    row_total += 1
                    
                    if row_idx == 1:
                        first_row_text += 1
                        first_row_total += 1
                    if col_idx == 1:
                        first_col_text += 1
                        first_col_total += 1
                    
                    if row_idx > 1 and col_idx > 1:
                        interior_total += 1
                
                # Check formatting
                if cell.font and cell.font.bold:
                    bold_count += 1
            
            # Row variance
            row_type_variance.append(row_numeric / row_total if row_total > 0 else 0)
        
        # Column variance
        for col_idx in range(1, sample_cols + 1):
            col_numeric = 0
            col_total = 0
            for row_idx in range(1, sample_rows + 1):
                cell = sheet.cell(row=row_idx, column=col_idx)
                value = cell.value
                if value is not None and value != '':
                    col_total += 1
                    if isinstance(value, (int, float)):
                        col_numeric += 1
            col_type_variance.append(col_numeric / col_total if col_total > 0 else 0)
        
        # Count merged cells
        merged_count = len(list(sheet.merged_cells.ranges))
        merged_in_top = sum(1 for m in sheet.merged_cells.ranges if m.min_row <= 3)
        
        # Calculate features
        total_cells = sample_rows * sample_cols
        
        return LayoutFeatures(
            n_rows=max_row,
            n_cols=max_col,
            aspect_ratio=max_col / max_row if max_row > 0 else 0,
            text_density=text_count / total_cells if total_cells > 0 else 0,
            numeric_density=numeric_count / total_cells if total_cells > 0 else 0,
            empty_cell_ratio=empty_count / total_cells if total_cells > 0 else 0,
            first_row_text_ratio=first_row_text / first_row_total if first_row_total > 0 else 0,
            first_col_text_ratio=first_col_text / first_col_total if first_col_total > 0 else 0,
            interior_numeric_ratio=interior_numeric / interior_total if interior_total > 0 else 0,
            bold_cell_ratio=bold_count / total_cells if total_cells > 0 else 0,
            merged_cell_count=merged_count,
            merged_in_top_rows=merged_in_top,
            col_variance=np.var(col_type_variance) if col_type_variance else 0,
            row_variance=np.var(row_type_variance) if row_type_variance else 0
        )
    
    def predict(self, features: LayoutFeatures) -> Tuple[str, float]:
        """
        Predict layout type from features.
        
        Args:
            features: Extracted features
            
        Returns:
            Tuple of (layout_type, confidence)
        """
        if not SKLEARN_AVAILABLE or self.model is None:
            # Fallback to heuristic classification
            return self._heuristic_classify(features)
        
        try:
            # Convert features to array and scale
            X = features.to_array().reshape(1, -1)
            X_scaled = self.scaler.transform(X)
            
            # Predict
            prediction = self.model.predict(X_scaled)[0]
            probabilities = self.model.predict_proba(X_scaled)[0]
            confidence = float(probabilities[prediction]) * 100
            
            layout_type = self.LAYOUT_TYPES[prediction]
            
            return layout_type, confidence
            
        except Exception as e:
            logger.error(f"ML prediction failed: {str(e)}, using heuristic")
            return self._heuristic_classify(features)
    
    def _heuristic_classify(self, features: LayoutFeatures) -> Tuple[str, float]:
        """
        Heuristic classification when ML model is not available.
        
        Args:
            features: Extracted features
            
        Returns:
            Tuple of (layout_type, confidence)
        """
        scores = {
            'standard': 0.0,
            'transposed': 0.0,
            'pivot': 0.0,
            'hierarchical': 0.0
        }
        
        # Standard layout indicators
        if features.first_row_text_ratio > 0.7:
            scores['standard'] += 30
        if features.interior_numeric_ratio > 0.6:
            scores['standard'] += 25
        if features.aspect_ratio < 0.5:  # Taller than wide
            scores['standard'] += 20
        
        # Transposed layout indicators
        if features.first_col_text_ratio > 0.7:
            scores['transposed'] += 30
        if features.aspect_ratio > 2.0:  # Wider than tall
            scores['transposed'] += 25
        
        # Pivot/crosstab indicators
        if features.first_row_text_ratio > 0.5 and features.first_col_text_ratio > 0.5:
            scores['pivot'] += 40
        if features.interior_numeric_ratio > 0.7:
            scores['pivot'] += 20
        if 0.5 <= features.aspect_ratio <= 2.0:  # Approximately square
            scores['pivot'] += 15
        
        # Hierarchical indicators
        if features.merged_in_top_rows >= 2:
            scores['hierarchical'] += 40
        if features.merged_cell_count >= 3:
            scores['hierarchical'] += 20
        
        # Get best classification
        best_type = max(scores, key=scores.get)
        confidence = min(scores[best_type], 85.0)  # Cap at 85% for heuristic
        
        return best_type, confidence
    
    def train(
        self,
        training_data: List[Tuple[LayoutFeatures, str]],
        save_path: Optional[str] = None
    ):
        """
        Train the classifier on labeled data.
        
        Args:
            training_data: List of (features, label) tuples
            save_path: Path to save trained model
        """
        if not SKLEARN_AVAILABLE:
            logger.error("Cannot train: scikit-learn not available")
            return
        
        # Prepare data
        X = np.array([f.to_array() for f, _ in training_data])
        y = np.array([self.LAYOUT_TO_INT[label] for _, label in training_data])
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Scale features
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train model
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        self.model.fit(X_train_scaled, y_train)
        
        # Evaluate
        train_score = self.model.score(X_train_scaled, y_train)
        test_score = self.model.score(X_test_scaled, y_test)
        
        logger.info(f"Model trained: train_acc={train_score:.3f}, test_acc={test_score:.3f}")
        
        # Save model
        save_path = save_path or self.model_path
        self.save_model(save_path)
    
    def save_model(self, path: Optional[str] = None):
        """Save trained model to file."""
        if self.model is None or self.scaler is None:
            logger.warning("No model to save")
            return
        
        path = path or self.model_path
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        with open(path, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'scaler': self.scaler
            }, f)
        
        logger.info(f"Model saved to {path}")
    
    def load_model(self, path: Optional[str] = None):
        """Load trained model from file."""
        path = path or self.model_path
        
        if not os.path.exists(path):
            logger.warning(f"Model file not found: {path}")
            return
        
        try:
            with open(path, 'rb') as f:
                data = pickle.load(f)
                self.model = data['model']
                self.scaler = data['scaler']
            
            logger.info(f"Model loaded from {path}")
        except Exception as e:
            logger.error(f"Failed to load model: {str(e)}")




