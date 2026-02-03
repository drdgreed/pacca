"""
RAG (Retrieval-Augmented Generation) module for PACCA.

Provides semantic search over clinical guidelines for
evidence-based decision support.
"""

from pacca.rag.pipeline import GuidelineVectorStore, RAGPipeline
from pacca.rag.sample_guidelines import SAMPLE_GUIDELINES

__all__ = [
    "GuidelineVectorStore",
    "RAGPipeline",
    "SAMPLE_GUIDELINES",
]
