"""
Vector Store - FAISS-based vector storage and similarity search.
Provides fast semantic search over embedded documents.
"""

import faiss
import numpy as np
import json
import os
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class VectorStore:
    """
    FAISS-based vector store for semantic search.
    Stores embeddings and metadata separately.
    """
    
    def __init__(self, dimension: int = 384, index_path: str = "data/vector_index"):
        """
        Initialize vector store.
        
        Args:
            dimension: Embedding dimension (384 for all-MiniLM-L6-v2)
            index_path: Path to store/load index files
        """
        self.dimension = dimension
        self.index_path = Path(index_path)
        self.index_path.mkdir(parents=True, exist_ok=True)
        
        # Create FAISS index (using IndexFlatL2 for exact search)
        self.index = faiss.IndexFlatL2(dimension)
        
        # Metadata storage (parallel to vectors)
        self.metadata: List[Dict[str, Any]] = []
        
        logger.info(f"✅ Vector store initialized (dimension={dimension})")
    
    def add(self, embeddings: np.ndarray, metadata: List[Dict[str, Any]]):
        """
        Add vectors and metadata to the store.
        
        Args:
            embeddings: numpy array of shape (n, dimension)
            metadata: list of metadata dicts (one per embedding)
        """
        if len(embeddings) != len(metadata):
            raise ValueError("Number of embeddings must match metadata entries")
        
        # Ensure embeddings are float32 (FAISS requirement)
        if embeddings.dtype != np.float32:
            embeddings = embeddings.astype(np.float32)
        
        # Add to FAISS index
        self.index.add(embeddings)
        
        # Store metadata
        self.metadata.extend(metadata)
        
        logger.info(f"Added {len(embeddings)} vectors to store (total: {len(self.metadata)})")
    
    def search(self, query_embedding: np.ndarray, k: int = 10) -> List[Dict[str, Any]]:
        """
        Search for most similar vectors.
        
        Args:
            query_embedding: Query vector (shape: (dimension,) or (1, dimension))
            k: Number of results to return
            
        Returns:
            List of dicts with 'metadata' and 'score' keys
        """
        # Ensure 2D array
        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)
        
        # Ensure float32
        if query_embedding.dtype != np.float32:
            query_embedding = query_embedding.astype(np.float32)
        
        # Search
        distances, indices = self.index.search(query_embedding, min(k, len(self.metadata)))
        
        # Build results (convert L2 distance to similarity score)
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < len(self.metadata):
                # Convert L2 distance to similarity (0-1 range)
                # Smaller distance = higher similarity
                similarity = 1 / (1 + dist)
                
                results.append({
                    'metadata': self.metadata[idx],
                    'score': float(similarity),
                    'distance': float(dist)
                })
        
        return results
    
    def save(self, name: str = "default"):
        """
        Save index and metadata to disk.
        
        Args:
            name: Name for the index files
        """
        try:
            # Save FAISS index
            index_file = self.index_path / f"{name}.index"
            faiss.write_index(self.index, str(index_file))
            
            # Save metadata
            metadata_file = self.index_path / f"{name}.metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump(self.metadata, f)
            
            logger.info(f"✅ Saved vector store: {name} ({len(self.metadata)} vectors)")
        except Exception as e:
            logger.error(f"Failed to save vector store: {e}")
            raise
    
    def load(self, name: str = "default") -> bool:
        """
        Load index and metadata from disk.
        
        Args:
            name: Name of the index files
            
        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            index_file = self.index_path / f"{name}.index"
            metadata_file = self.index_path / f"{name}.metadata.json"
            
            if not index_file.exists() or not metadata_file.exists():
                logger.warning(f"Index files not found: {name}")
                return False
            
            # Load FAISS index
            self.index = faiss.read_index(str(index_file))
            
            # Load metadata
            with open(metadata_file, 'r') as f:
                self.metadata = json.load(f)
            
            logger.info(f"✅ Loaded vector store: {name} ({len(self.metadata)} vectors)")
            return True
        except Exception as e:
            logger.error(f"Failed to load vector store: {e}")
            return False
    
    def clear(self):
        """Clear all vectors and metadata."""
        self.index = faiss.IndexFlatL2(self.dimension)
        self.metadata = []
        logger.info("Vector store cleared")
    
    def __len__(self) -> int:
        """Get number of vectors in store."""
        return len(self.metadata)
