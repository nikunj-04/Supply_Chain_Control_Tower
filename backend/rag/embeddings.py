"""
Embedding Service - Converts text to vector embeddings using sentence-transformers.
Model: all-MiniLM-L6-v2 (384 dimensions, fast, local, free)
"""

import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Union
import logging

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Handles text embedding generation using sentence-transformers.
    Singleton pattern to avoid loading model multiple times.
    """
    
    _instance = None
    _model = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EmbeddingService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._model is None:
            self._load_model()
    
    def _load_model(self):
        """Load the sentence-transformers model."""
        try:
            logger.info("Loading embedding model: all-MiniLM-L6-v2")
            self._model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info(f"✅ Model loaded successfully (384 dimensions)")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
    
    def encode(self, text: Union[str, List[str]], show_progress: bool = False) -> np.ndarray:
        """
        Generate embeddings for text.
        
        Args:
            text: Single text string or list of strings
            show_progress: Show progress bar for batch encoding
            
        Returns:
            numpy array of shape (384,) for single text or (n, 384) for list
        """
        if isinstance(text, str):
            return self._model.encode(text, convert_to_numpy=True)
        else:
            return self._model.encode(
                text,
                convert_to_numpy=True,
                show_progress_bar=show_progress,
                batch_size=32
            )
    
    def get_dimension(self) -> int:
        """Get embedding dimension (384 for all-MiniLM-L6-v2)."""
        return self._model.get_sentence_embedding_dimension()
    
    @property
    def model_name(self) -> str:
        """Get the model name."""
        return "all-MiniLM-L6-v2"
