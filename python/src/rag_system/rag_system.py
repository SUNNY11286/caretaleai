"""
RAG System - Main Interface
Integrates all RAG components for evidence-based medical context retrieval.
"""

from typing import List, Optional

from ..models.knowledge_document import KnowledgeDocument, MedicalDomain
from .document_retriever import DocumentRetriever, RetrievalConfig
from .reranker import Reranker, RankedDocument, RerankingConfig
from .citation_generator import CitationGenerator, GroundedResponse
from .knowledge_base_manager import KnowledgeBaseManager, KnowledgeBaseCategory


class RAGSystem:
    """
    Main RAG System interface implementing the complete retrieval-augmented
    generation pipeline for evidence-based medical responses.
    """

    def __init__(
        self,
        retrieval_config: Optional[RetrievalConfig] = None,
        reranking_config: Optional[RerankingConfig] = None
    ):
        """
        Initialize the RAG System with all components.
        
        Args:
            retrieval_config: Configuration for document retrieval
            reranking_config: Configuration for re-ranking
        """
        self.knowledge_base = KnowledgeBaseManager()
        self.retriever = DocumentRetriever()
        self.reranker = Reranker(reranking_config)
        self.citation_generator = CitationGenerator()
        self.retrieval_config = retrieval_config or RetrievalConfig()

    def retrieve_relevant_docs(
        self,
        query: str,
        domain: Optional[MedicalDomain] = None
    ) -> List[KnowledgeDocument]:
        """
        Retrieve relevant documents for a query.
        
        Args:
            query: Search query
            domain: Optional medical domain filter
            
        Returns:
            List of relevant knowledge documents
        """
        # Update retrieval config with domain filter
        config = RetrievalConfig(
            top_k=self.retrieval_config.top_k,
            similarity_threshold=self.retrieval_config.similarity_threshold,
            domain_filter=domain
        )
        
        # Retrieve documents
        return self.retriever.retrieve(query, config)

    def rerank_by_relevance(
        self,
        query: str,
        documents: List[KnowledgeDocument]
    ) -> List[RankedDocument]:
        """
        Re-rank documents by relevance using multiple signals.
        
        Args:
            query: Original query
            documents: Documents to re-rank
            
        Returns:
            List of ranked documents with scores
        """
        return self.reranker.rerank(query, documents)

    def generate_grounded_response(
        self,
        query: str,
        context: List[RankedDocument]
    ) -> GroundedResponse:
        """
        Generate a grounded response with citations.
        
        Args:
            query: User query
            context: Ranked context documents
            
        Returns:
            Grounded response with citations
        """
        # Extract documents from ranked context
        source_documents = [ranked.document for ranked in context]
        
        # Generate response text (placeholder - in production, use LLM)
        response_text = self._generate_response_text(query, context)
        
        # Create grounded response with citations
        return self.citation_generator.create_grounded_response(
            response_text,
            source_documents,
            include_inline_citations=True
        )

    def validate_citations(self, response: GroundedResponse) -> dict:
        """
        Validate citations in a grounded response.
        
        Args:
            response: Grounded response to validate
            
        Returns:
            Validation results
        """
        return self.citation_generator.validate_citations(response)

    def add_knowledge(
        self,
        document: KnowledgeDocument,
        category: KnowledgeBaseCategory
    ) -> bool:
        """
        Add a document to the knowledge base and retriever.
        
        Args:
            document: Knowledge document to add
            category: Category for the document
            
        Returns:
            True if document was added successfully
        """
        # Add to knowledge base
        success = self.knowledge_base.add_document(document, category)
        
        if success:
            # Add to retriever for semantic search
            self.retriever.add_documents([document])
        
        return success

    def initialize_knowledge_base(
        self,
        documents: List[tuple[KnowledgeDocument, KnowledgeBaseCategory]]
    ) -> int:
        """
        Initialize the knowledge base with multiple documents.
        
        Args:
            documents: List of (document, category) tuples
            
        Returns:
            Number of documents successfully added
        """
        count = 0
        for document, category in documents:
            if self.add_knowledge(document, category):
                count += 1
        
        return count

    def _generate_response_text(
        self,
        query: str,
        context: List[RankedDocument]
    ) -> str:
        """
        Generate response text from query and context.
        This is a placeholder - in production, use an LLM.
        
        Args:
            query: User query
            context: Ranked context documents
            
        Returns:
            Generated response text
        """
        # Placeholder implementation
        if not context:
            return "I don't have enough information to answer that question."
        
        # Simple response based on top document
        top_doc = context[0].document
        response = f"Based on {top_doc.source.organization_name} guidelines: "
        response += top_doc.content[:200] + "..."
        
        return response

    def get_knowledge_base_stats(self) -> dict:
        """
        Get statistics about the knowledge base.
        
        Returns:
            Dictionary with statistics
        """
        return self.knowledge_base.get_statistics()
