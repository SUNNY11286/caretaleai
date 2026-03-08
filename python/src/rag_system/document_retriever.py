"""
Document Retriever Component
Implements semantic search across clinical guidelines using dense vector embeddings.
"""

from typing import List, Optional
import numpy as np
from dataclasses import dataclass

from ..models.knowledge_document import KnowledgeDocument, MedicalDomain


@dataclass
class RetrievalConfig:
    """Configuration for document retrieval"""
    top_k: int = 10
    similarity_threshold: float = 0.7
    domain_filter: Optional[MedicalDomain] = None


class DocumentRetriever:
    """
    Retrieves relevant documents from the knowledge base using semantic search.
    Uses dense vector embeddings for similarity matching.
    """

    def __init__(self, embedding_dim: int = 768):
        """
        Initialize the document retriever.
        
        Args:
            embedding_dim: Dimension of the embedding vectors (default: 768 for BERT-like models)
        """
        self.embedding_dim = embedding_dim
        self.documents: List[KnowledgeDocument] = []
        self.embeddings: Optional[np.ndarray] = None

    def add_documents(self, documents: List[KnowledgeDocument]) -> None:
        """
        Add documents to the retriever's index.
        
        Args:
            documents: List of knowledge documents to add
        """
        self.documents.extend(documents)
        # In a real implementation, this would compute embeddings
        # For now, we'll use placeholder embeddings
        new_embeddings = self._compute_embeddings([doc.content for doc in documents])
        
        if self.embeddings is None:
            self.embeddings = new_embeddings
        else:
            self.embeddings = np.vstack([self.embeddings, new_embeddings])

    def retrieve(
        self, 
        query: str, 
        config: Optional[RetrievalConfig] = None
    ) -> List[KnowledgeDocument]:
        """
        Retrieve relevant documents for a given query using semantic search.
        
        Args:
            query: The search query
            config: Retrieval configuration (optional)
            
        Returns:
            List of relevant knowledge documents, sorted by relevance
        """
        if config is None:
            config = RetrievalConfig()

        if not self.documents or self.embeddings is None:
            return []

        # Compute query embedding
        query_embedding = self._compute_query_embedding(query)

        # Filter by domain if specified
        candidate_indices = self._filter_by_domain(config.domain_filter)

        # Compute similarity scores
        similarities = self._compute_similarities(query_embedding, candidate_indices)

        # Filter by threshold and get top-k
        relevant_indices = self._filter_and_rank(
            similarities, 
            candidate_indices,
            config.similarity_threshold,
            config.top_k
        )

        return [self.documents[idx] for idx in relevant_indices]

    def _compute_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Compute embeddings for a list of texts.
        In a real implementation, this would use a pre-trained model.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            Array of embeddings with shape (len(texts), embedding_dim)
        """
        # Placeholder: random embeddings for minimal implementation
        # In production, use a model like sentence-transformers
        return np.random.randn(len(texts), self.embedding_dim)

    def _compute_query_embedding(self, query: str) -> np.ndarray:
        """
        Compute embedding for a query string.
        
        Args:
            query: Query string
            
        Returns:
            Query embedding vector
        """
        # Placeholder: random embedding
        # In production, use the same model as _compute_embeddings
        return np.random.randn(self.embedding_dim)

    def _filter_by_domain(
        self, 
        domain_filter: Optional[MedicalDomain]
    ) -> List[int]:
        """
        Filter document indices by medical domain.
        
        Args:
            domain_filter: Medical domain to filter by (None for no filtering)
            
        Returns:
            List of document indices matching the domain filter
        """
        if domain_filter is None:
            return list(range(len(self.documents)))
        
        return [
            idx for idx, doc in enumerate(self.documents)
            if doc.domain == domain_filter
        ]

    def _compute_similarities(
        self, 
        query_embedding: np.ndarray,
        candidate_indices: List[int]
    ) -> np.ndarray:
        """
        Compute cosine similarity between query and candidate documents.
        
        Args:
            query_embedding: Query embedding vector
            candidate_indices: Indices of candidate documents
            
        Returns:
            Array of similarity scores
        """
        if not candidate_indices:
            return np.array([])

        candidate_embeddings = self.embeddings[candidate_indices]
        
        # Cosine similarity
        query_norm = np.linalg.norm(query_embedding)
        doc_norms = np.linalg.norm(candidate_embeddings, axis=1)
        
        similarities = np.dot(candidate_embeddings, query_embedding) / (doc_norms * query_norm + 1e-8)
        
        return similarities

    def _filter_and_rank(
        self,
        similarities: np.ndarray,
        candidate_indices: List[int],
        threshold: float,
        top_k: int
    ) -> List[int]:
        """
        Filter by similarity threshold and return top-k results.
        
        Args:
            similarities: Similarity scores
            candidate_indices: Candidate document indices
            threshold: Minimum similarity threshold
            top_k: Maximum number of results to return
            
        Returns:
            List of document indices, sorted by relevance
        """
        if len(similarities) == 0:
            return []

        # Filter by threshold
        above_threshold = similarities >= threshold
        filtered_indices = [
            candidate_indices[i] 
            for i, above in enumerate(above_threshold) 
            if above
        ]
        filtered_scores = similarities[above_threshold]

        # Sort by score (descending) and take top-k
        sorted_order = np.argsort(filtered_scores)[::-1][:top_k]
        
        return [filtered_indices[i] for i in sorted_order]

    def clear(self) -> None:
        """Clear all documents and embeddings from the retriever."""
        self.documents = []
        self.embeddings = None
