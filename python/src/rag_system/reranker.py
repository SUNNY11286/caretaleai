"""
Re-ranker Component
Implements relevance scoring and context selection for optimal response grounding.
"""

from typing import List, Optional
from dataclasses import dataclass
import numpy as np

from ..models.knowledge_document import KnowledgeDocument


@dataclass
class RankedDocument:
    """A document with its relevance score"""
    document: KnowledgeDocument
    relevance_score: float
    rank: int


@dataclass
class RerankingConfig:
    """Configuration for re-ranking"""
    max_context_docs: int = 5
    diversity_weight: float = 0.3
    recency_weight: float = 0.2
    authority_weight: float = 0.5


class Reranker:
    """
    Re-ranks retrieved documents based on multiple relevance signals.
    Combines semantic similarity with authority, recency, and diversity.
    """

    def __init__(self, config: Optional[RerankingConfig] = None):
        """
        Initialize the re-ranker.
        
        Args:
            config: Re-ranking configuration (optional)
        """
        self.config = config or RerankingConfig()

    def rerank(
        self,
        query: str,
        documents: List[KnowledgeDocument],
        initial_scores: Optional[List[float]] = None
    ) -> List[RankedDocument]:
        """
        Re-rank documents based on multiple relevance signals.
        
        Args:
            query: The original query
            documents: List of documents to re-rank
            initial_scores: Initial similarity scores (optional)
            
        Returns:
            List of ranked documents with scores
        """
        if not documents:
            return []

        # Use initial scores or compute new ones
        if initial_scores is None:
            initial_scores = [1.0] * len(documents)

        # Compute additional relevance signals
        authority_scores = self._compute_authority_scores(documents)
        recency_scores = self._compute_recency_scores(documents)
        diversity_scores = self._compute_diversity_scores(documents, query)

        # Combine scores with weights
        final_scores = self._combine_scores(
            initial_scores,
            authority_scores,
            recency_scores,
            diversity_scores
        )

        # Sort by final score and create ranked documents
        sorted_indices = np.argsort(final_scores)[::-1]
        
        ranked_docs = []
        for rank, idx in enumerate(sorted_indices[:self.config.max_context_docs], start=1):
            ranked_docs.append(RankedDocument(
                document=documents[idx],
                relevance_score=final_scores[idx],
                rank=rank
            ))

        return ranked_docs

    def _compute_authority_scores(self, documents: List[KnowledgeDocument]) -> List[float]:
        """
        Compute authority scores based on source credibility.
        
        Args:
            documents: List of documents
            
        Returns:
            List of authority scores (0-1)
        """
        return [doc.source.credibility_score for doc in documents]

    def _compute_recency_scores(self, documents: List[KnowledgeDocument]) -> List[float]:
        """
        Compute recency scores based on last update date.
        More recent documents get higher scores.
        
        Args:
            documents: List of documents
            
        Returns:
            List of recency scores (0-1)
        """
        from datetime import datetime, timezone
        
        now = datetime.now(timezone.utc)
        scores = []
        
        for doc in documents:
            # Ensure last_updated is timezone-aware
            last_updated = doc.last_updated
            if last_updated.tzinfo is None:
                last_updated = last_updated.replace(tzinfo=timezone.utc)
            
            # Calculate age in days
            age_days = (now - last_updated).days
            
            # Exponential decay: score = exp(-age_days / 365)
            # Documents older than ~3 years get very low scores
            score = np.exp(-age_days / 365.0)
            scores.append(score)
        
        return scores

    def _compute_diversity_scores(
        self, 
        documents: List[KnowledgeDocument],
        query: str
    ) -> List[float]:
        """
        Compute diversity scores to avoid redundant information.
        Documents covering different aspects get higher scores.
        
        Args:
            documents: List of documents
            query: Original query
            
        Returns:
            List of diversity scores (0-1)
        """
        # Simplified diversity: penalize documents from the same domain
        domain_counts = {}
        for doc in documents:
            domain_counts[doc.domain] = domain_counts.get(doc.domain, 0) + 1
        
        scores = []
        for doc in documents:
            # Higher diversity score for less common domains
            diversity = 1.0 / domain_counts[doc.domain]
            scores.append(diversity)
        
        # Normalize to 0-1 range
        max_score = max(scores) if scores else 1.0
        return [s / max_score for s in scores]

    def _combine_scores(
        self,
        initial_scores: List[float],
        authority_scores: List[float],
        recency_scores: List[float],
        diversity_scores: List[float]
    ) -> List[float]:
        """
        Combine multiple score signals with configured weights.
        
        Args:
            initial_scores: Initial similarity scores
            authority_scores: Authority/credibility scores
            recency_scores: Recency scores
            diversity_scores: Diversity scores
            
        Returns:
            Combined final scores
        """
        # Normalize initial scores to 0-1 range
        max_initial = max(initial_scores) if initial_scores else 1.0
        normalized_initial = [s / max_initial for s in initial_scores]

        # Compute semantic similarity weight (remaining weight after other factors)
        semantic_weight = 1.0 - (
            self.config.authority_weight + 
            self.config.recency_weight + 
            self.config.diversity_weight
        )

        # Combine with weights
        final_scores = []
        for i in range(len(initial_scores)):
            score = (
                semantic_weight * normalized_initial[i] +
                self.config.authority_weight * authority_scores[i] +
                self.config.recency_weight * recency_scores[i] +
                self.config.diversity_weight * diversity_scores[i]
            )
            final_scores.append(score)

        return final_scores

    def select_context(
        self,
        ranked_documents: List[RankedDocument],
        max_tokens: int = 2000
    ) -> List[RankedDocument]:
        """
        Select optimal context documents within token budget.
        
        Args:
            ranked_documents: List of ranked documents
            max_tokens: Maximum total tokens for context
            
        Returns:
            Selected documents that fit within token budget
        """
        selected = []
        total_tokens = 0

        for doc in ranked_documents:
            # Rough estimate: 1 token ≈ 4 characters
            doc_tokens = len(doc.document.content) // 4
            
            if total_tokens + doc_tokens <= max_tokens:
                selected.append(doc)
                total_tokens += doc_tokens
            else:
                break

        return selected
