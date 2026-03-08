"""
Unit tests for RAG System components
"""

import pytest
from datetime import datetime, timezone
from src.models.knowledge_document import (
    KnowledgeDocument,
    MedicalDomain,
    ValidationStatus,
    AuthoritySource,
    DocumentMetadata,
    CitationInfo
)
from src.rag_system import (
    RAGSystem,
    DocumentRetriever,
    RetrievalConfig,
    Reranker,
    RerankingConfig,
    CitationGenerator,
    KnowledgeBaseManager,
    KnowledgeBaseCategory
)


@pytest.fixture
def sample_document():
    """Create a sample knowledge document for testing"""
    return KnowledgeDocument(
        document_id="doc-001",
        source=AuthoritySource(
            organization_name="American Heart Association",
            organization_type="professional_association",
            url="https://www.heart.org",
            credibility_score=0.95
        ),
        domain=MedicalDomain.CARDIOLOGY,
        content="Post-discharge care for heart failure patients includes daily weight monitoring, medication adherence, and dietary sodium restriction.",
        metadata=DocumentMetadata(
            title="Heart Failure Post-Discharge Guidelines",
            authors=["Dr. Smith", "Dr. Jones"],
            publication_date=datetime(2023, 1, 15, tzinfo=timezone.utc),
            version="2.0",
            keywords=["heart failure", "post-discharge", "care management"],
            abstract="Guidelines for managing heart failure patients after hospital discharge.",
            language="en",
            document_type="guideline"
        ),
        last_updated=datetime(2023, 6, 1, tzinfo=timezone.utc),
        validation_status=ValidationStatus.VALIDATED,
        citation_format=CitationInfo(
            citation_text="American Heart Association. (2023). Heart Failure Post-Discharge Guidelines.",
            citation_style="APA",
            doi="10.1000/example",
            url="https://www.heart.org/guidelines"
        )
    )


@pytest.fixture
def sample_documents():
    """Create multiple sample documents for testing"""
    docs = []
    for i in range(5):
        doc = KnowledgeDocument(
            document_id=f"doc-{i:03d}",
            source=AuthoritySource(
                organization_name=f"Medical Organization {i}",
                organization_type="professional_association",
                credibility_score=0.8 + i * 0.04
            ),
            domain=MedicalDomain.CARDIOLOGY if i < 3 else MedicalDomain.GENERAL_MEDICINE,
            content=f"Medical content for document {i}. This contains important clinical information.",
            metadata=DocumentMetadata(
                title=f"Clinical Guideline {i}",
                publication_date=datetime(2023, i + 1, 1, tzinfo=timezone.utc),
                keywords=["clinical", "guideline"],
                language="en",
                document_type="guideline"
            ),
            last_updated=datetime(2023, i + 1, 15, tzinfo=timezone.utc),
            validation_status=ValidationStatus.VALIDATED,
            citation_format=CitationInfo(
                citation_text=f"Citation {i}",
                citation_style="APA"
            )
        )
        docs.append(doc)
    return docs



class TestDocumentRetriever:
    """Test DocumentRetriever component"""

    def test_add_documents(self, sample_documents):
        """Test adding documents to retriever"""
        retriever = DocumentRetriever()
        retriever.add_documents(sample_documents)
        
        assert len(retriever.documents) == 5
        assert retriever.embeddings is not None
        assert retriever.embeddings.shape[0] == 5

    def test_retrieve_with_no_documents(self):
        """Test retrieval with empty document set"""
        retriever = DocumentRetriever()
        results = retriever.retrieve("heart failure care")
        
        assert results == []

    def test_retrieve_with_domain_filter(self, sample_documents):
        """Test retrieval with domain filtering"""
        retriever = DocumentRetriever()
        retriever.add_documents(sample_documents)
        
        config = RetrievalConfig(
            top_k=10,
            similarity_threshold=0.0,  # Low threshold to get results
            domain_filter=MedicalDomain.CARDIOLOGY
        )
        
        results = retriever.retrieve("medical information", config)
        
        # Should only return cardiology documents (first 3)
        assert all(doc.domain == MedicalDomain.CARDIOLOGY for doc in results)

    def test_clear(self, sample_documents):
        """Test clearing retriever"""
        retriever = DocumentRetriever()
        retriever.add_documents(sample_documents)
        retriever.clear()
        
        assert len(retriever.documents) == 0
        assert retriever.embeddings is None


class TestReranker:
    """Test Reranker component"""

    def test_rerank_empty_documents(self):
        """Test re-ranking with empty document list"""
        reranker = Reranker()
        results = reranker.rerank("query", [])
        
        assert results == []

    def test_rerank_with_documents(self, sample_documents):
        """Test re-ranking with documents"""
        reranker = Reranker()
        results = reranker.rerank("medical query", sample_documents)
        
        assert len(results) <= 5  # max_context_docs default
        assert all(hasattr(r, 'document') for r in results)
        assert all(hasattr(r, 'relevance_score') for r in results)
        assert all(hasattr(r, 'rank') for r in results)
        
        # Check ranks are sequential
        for i, result in enumerate(results, start=1):
            assert result.rank == i

    def test_rerank_respects_max_context_docs(self, sample_documents):
        """Test that re-ranking respects max_context_docs config"""
        config = RerankingConfig(max_context_docs=3)
        reranker = Reranker(config)
        results = reranker.rerank("query", sample_documents)
        
        assert len(results) <= 3

    def test_select_context_within_token_budget(self, sample_documents):
        """Test context selection within token budget"""
        reranker = Reranker()
        ranked = reranker.rerank("query", sample_documents)
        
        selected = reranker.select_context(ranked, max_tokens=100)
        
        # Should select fewer documents due to token limit
        assert len(selected) <= len(ranked)


class TestCitationGenerator:
    """Test CitationGenerator component"""

    def test_generate_citations(self, sample_document):
        """Test citation generation"""
        generator = CitationGenerator()
        citations = generator.generate_citations(
            "Response text",
            [sample_document],
            "APA"
        )
        
        assert len(citations) == 1
        assert citations[0].document_id == sample_document.document_id
        assert citations[0].source_name == sample_document.source.organization_name
        assert citations[0].citation_text != ""

    def test_create_grounded_response(self, sample_document):
        """Test grounded response creation"""
        generator = CitationGenerator()
        response = generator.create_grounded_response(
            "This is medical advice.",
            [sample_document],
            include_inline_citations=True
        )
        
        assert response.response_text != ""
        assert len(response.citations) == 1
        assert len(response.source_documents) == 1
        assert "Sources:" in response.response_text

    def test_validate_citations(self, sample_document):
        """Test citation validation"""
        generator = CitationGenerator()
        response = generator.create_grounded_response(
            "Medical advice",
            [sample_document]
        )
        
        validation = generator.validate_citations(response)
        
        assert validation["has_citations"] is True
        assert validation["all_documents_cited"] is True
        assert validation["all_citations_have_sources"] is True
        assert validation["all_citations_traceable"] is True
        assert validation["valid"] is True


class TestKnowledgeBaseManager:
    """Test KnowledgeBaseManager component"""

    def test_add_document(self, sample_document):
        """Test adding a document"""
        manager = KnowledgeBaseManager()
        success = manager.add_document(
            sample_document,
            KnowledgeBaseCategory.CLINICAL_GUIDELINES
        )
        
        assert success is True
        assert manager.get_document(sample_document.document_id) == sample_document

    def test_add_duplicate_document(self, sample_document):
        """Test adding duplicate document fails"""
        manager = KnowledgeBaseManager()
        manager.add_document(sample_document, KnowledgeBaseCategory.CLINICAL_GUIDELINES)
        success = manager.add_document(sample_document, KnowledgeBaseCategory.CLINICAL_GUIDELINES)
        
        assert success is False

    def test_get_documents_by_category(self, sample_documents):
        """Test retrieving documents by category"""
        manager = KnowledgeBaseManager()
        for doc in sample_documents[:3]:
            manager.add_document(doc, KnowledgeBaseCategory.CLINICAL_GUIDELINES)
        for doc in sample_documents[3:]:
            manager.add_document(doc, KnowledgeBaseCategory.EDUCATIONAL_CONTENT)
        
        guidelines = manager.get_documents_by_category(KnowledgeBaseCategory.CLINICAL_GUIDELINES)
        educational = manager.get_documents_by_category(KnowledgeBaseCategory.EDUCATIONAL_CONTENT)
        
        assert len(guidelines) == 3
        assert len(educational) == 2

    def test_get_documents_by_domain(self, sample_documents):
        """Test retrieving documents by domain"""
        manager = KnowledgeBaseManager()
        for doc in sample_documents:
            manager.add_document(doc, KnowledgeBaseCategory.CLINICAL_GUIDELINES)
        
        cardiology_docs = manager.get_documents_by_domain(MedicalDomain.CARDIOLOGY)
        
        assert len(cardiology_docs) == 3

    def test_update_document_status(self, sample_document):
        """Test updating document validation status"""
        manager = KnowledgeBaseManager()
        manager.add_document(sample_document, KnowledgeBaseCategory.CLINICAL_GUIDELINES)
        
        success = manager.update_document_status(
            sample_document.document_id,
            ValidationStatus.OUTDATED
        )
        
        assert success is True
        doc = manager.get_document(sample_document.document_id)
        assert doc.validation_status == ValidationStatus.OUTDATED

    def test_remove_document(self, sample_document):
        """Test removing a document"""
        manager = KnowledgeBaseManager()
        manager.add_document(sample_document, KnowledgeBaseCategory.CLINICAL_GUIDELINES)
        
        success = manager.remove_document(sample_document.document_id)
        
        assert success is True
        assert manager.get_document(sample_document.document_id) is None

    def test_get_statistics(self, sample_documents):
        """Test getting knowledge base statistics"""
        manager = KnowledgeBaseManager()
        for doc in sample_documents:
            manager.add_document(doc, KnowledgeBaseCategory.CLINICAL_GUIDELINES)
        
        stats = manager.get_statistics()
        
        assert stats["total_documents"] == 5
        assert stats["validated"] == 5
        assert stats["category_clinical_guidelines"] == 5


class TestRAGSystem:
    """Test RAGSystem integration"""

    def test_initialization(self):
        """Test RAG system initialization"""
        rag = RAGSystem()
        
        assert rag.knowledge_base is not None
        assert rag.retriever is not None
        assert rag.reranker is not None
        assert rag.citation_generator is not None

    def test_add_knowledge(self, sample_document):
        """Test adding knowledge to RAG system"""
        rag = RAGSystem()
        success = rag.add_knowledge(
            sample_document,
            KnowledgeBaseCategory.CLINICAL_GUIDELINES
        )
        
        assert success is True

    def test_initialize_knowledge_base(self, sample_documents):
        """Test initializing knowledge base with multiple documents"""
        rag = RAGSystem()
        docs_with_categories = [
            (doc, KnowledgeBaseCategory.CLINICAL_GUIDELINES)
            for doc in sample_documents
        ]
        
        count = rag.initialize_knowledge_base(docs_with_categories)
        
        assert count == 5

    def test_retrieve_relevant_docs(self, sample_documents):
        """Test document retrieval"""
        rag = RAGSystem()
        rag.initialize_knowledge_base([
            (doc, KnowledgeBaseCategory.CLINICAL_GUIDELINES)
            for doc in sample_documents
        ])
        
        results = rag.retrieve_relevant_docs("medical information")
        
        assert isinstance(results, list)

    def test_rerank_by_relevance(self, sample_documents):
        """Test document re-ranking"""
        rag = RAGSystem()
        ranked = rag.rerank_by_relevance("query", sample_documents)
        
        assert len(ranked) <= 5
        assert all(hasattr(r, 'relevance_score') for r in ranked)

    def test_generate_grounded_response(self, sample_documents):
        """Test grounded response generation"""
        rag = RAGSystem()
        ranked = rag.rerank_by_relevance("query", sample_documents)
        
        response = rag.generate_grounded_response("query", ranked)
        
        assert response.response_text != ""
        assert len(response.citations) > 0
        assert len(response.source_documents) > 0

    def test_validate_citations(self, sample_documents):
        """Test citation validation"""
        rag = RAGSystem()
        ranked = rag.rerank_by_relevance("query", sample_documents)
        response = rag.generate_grounded_response("query", ranked)
        
        validation = rag.validate_citations(response)
        
        assert validation["valid"] is True

    def test_get_knowledge_base_stats(self, sample_documents):
        """Test getting knowledge base statistics"""
        rag = RAGSystem()
        rag.initialize_knowledge_base([
            (doc, KnowledgeBaseCategory.CLINICAL_GUIDELINES)
            for doc in sample_documents
        ])
        
        stats = rag.get_knowledge_base_stats()
        
        assert stats["total_documents"] == 5
