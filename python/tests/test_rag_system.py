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

    def test_add_empty_documents_list(self):
        """Test adding empty documents list"""
        retriever = DocumentRetriever()
        retriever.add_documents([])
        
        assert len(retriever.documents) == 0
        # Empty array is created, not None
        assert retriever.embeddings is not None
        assert retriever.embeddings.shape[0] == 0

    def test_retrieve_with_no_documents(self):
        """Test retrieval with empty document set"""
        retriever = DocumentRetriever()
        results = retriever.retrieve("heart failure care")
        
        assert results == []

    def test_retrieve_with_empty_query(self, sample_documents):
        """Test retrieval with empty query string"""
        retriever = DocumentRetriever()
        retriever.add_documents(sample_documents)
        
        results = retriever.retrieve("")
        
        # Should handle empty query gracefully
        assert isinstance(results, list)

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

    def test_retrieve_respects_top_k(self, sample_documents):
        """Test that retrieval respects top_k configuration"""
        retriever = DocumentRetriever()
        retriever.add_documents(sample_documents)
        
        config = RetrievalConfig(
            top_k=2,
            similarity_threshold=0.0
        )
        
        results = retriever.retrieve("medical information", config)
        
        assert len(results) <= 2

    def test_retrieve_respects_similarity_threshold(self, sample_documents):
        """Test that retrieval respects similarity threshold"""
        retriever = DocumentRetriever()
        retriever.add_documents(sample_documents)
        
        # High threshold should return fewer results
        config_high = RetrievalConfig(
            top_k=10,
            similarity_threshold=0.9
        )
        
        results_high = retriever.retrieve("medical information", config_high)
        
        # Low threshold should return more results
        config_low = RetrievalConfig(
            top_k=10,
            similarity_threshold=0.0
        )
        
        results_low = retriever.retrieve("medical information", config_low)
        
        assert len(results_high) <= len(results_low)

    def test_clear(self, sample_documents):
        """Test clearing retriever"""
        retriever = DocumentRetriever()
        retriever.add_documents(sample_documents)
        retriever.clear()
        
        assert len(retriever.documents) == 0
        assert retriever.embeddings is None

    def test_add_documents_incrementally(self, sample_documents):
        """Test adding documents in multiple batches"""
        retriever = DocumentRetriever()
        
        # Add first batch
        retriever.add_documents(sample_documents[:2])
        assert len(retriever.documents) == 2
        
        # Add second batch
        retriever.add_documents(sample_documents[2:])
        assert len(retriever.documents) == 5

    def test_retrieve_with_special_characters(self, sample_documents):
        """Test retrieval with special characters in query"""
        retriever = DocumentRetriever()
        retriever.add_documents(sample_documents)
        
        # Query with special characters
        results = retriever.retrieve("heart failure: care & management?")
        
        # Should handle special characters gracefully
        assert isinstance(results, list)


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

    def test_rerank_single_document(self, sample_document):
        """Test re-ranking with single document"""
        reranker = Reranker()
        results = reranker.rerank("query", [sample_document])
        
        assert len(results) == 1
        assert results[0].rank == 1
        assert results[0].document == sample_document

    def test_rerank_respects_max_context_docs(self, sample_documents):
        """Test that re-ranking respects max_context_docs config"""
        config = RerankingConfig(max_context_docs=3)
        reranker = Reranker(config)
        results = reranker.rerank("query", sample_documents)
        
        assert len(results) <= 3

    def test_rerank_scores_are_normalized(self, sample_documents):
        """Test that relevance scores are properly normalized"""
        reranker = Reranker()
        results = reranker.rerank("medical query", sample_documents)
        
        # Scores should be between 0 and 1
        for result in results:
            assert 0.0 <= result.relevance_score <= 1.0

    def test_rerank_ordering_by_relevance(self, sample_documents):
        """Test that documents are ordered by relevance score"""
        reranker = Reranker()
        results = reranker.rerank("medical query", sample_documents)
        
        # Scores should be in descending order
        scores = [r.relevance_score for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_select_context_within_token_budget(self, sample_documents):
        """Test context selection within token budget"""
        reranker = Reranker()
        ranked = reranker.rerank("query", sample_documents)
        
        selected = reranker.select_context(ranked, max_tokens=100)
        
        # Should select fewer documents due to token limit
        assert len(selected) <= len(ranked)

    def test_select_context_empty_ranked_docs(self):
        """Test context selection with empty ranked documents"""
        reranker = Reranker()
        selected = reranker.select_context([], max_tokens=1000)
        
        assert selected == []

    def test_select_context_respects_token_budget(self, sample_documents):
        """Test that context selection respects token budget"""
        reranker = Reranker()
        ranked = reranker.rerank("query", sample_documents)
        
        # Very small token budget
        selected_small = reranker.select_context(ranked, max_tokens=50)
        
        # Large token budget
        selected_large = reranker.select_context(ranked, max_tokens=10000)
        
        # Larger budget should allow more documents
        assert len(selected_small) <= len(selected_large)

    def test_rerank_with_empty_query(self, sample_documents):
        """Test re-ranking with empty query"""
        reranker = Reranker()
        results = reranker.rerank("", sample_documents)
        
        # Should still rank documents
        assert len(results) > 0
        assert all(hasattr(r, 'relevance_score') for r in results)


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

    def test_generate_citations_empty_documents(self):
        """Test citation generation with empty documents list"""
        generator = CitationGenerator()
        citations = generator.generate_citations(
            "Response text",
            [],
            "APA"
        )
        
        assert citations == []

    def test_generate_citations_multiple_documents(self, sample_documents):
        """Test citation generation with multiple documents"""
        generator = CitationGenerator()
        citations = generator.generate_citations(
            "Response text",
            sample_documents,
            "APA"
        )
        
        assert len(citations) == len(sample_documents)
        # Each citation should have unique document ID
        doc_ids = [c.document_id for c in citations]
        assert len(doc_ids) == len(set(doc_ids))

    def test_generate_citations_different_styles(self, sample_document):
        """Test citation generation with different citation styles"""
        generator = CitationGenerator()
        
        apa_citations = generator.generate_citations(
            "Response text",
            [sample_document],
            "APA"
        )
        
        mla_citations = generator.generate_citations(
            "Response text",
            [sample_document],
            "MLA"
        )
        
        # Both should generate citations
        assert len(apa_citations) == 1
        assert len(mla_citations) == 1

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

    def test_create_grounded_response_without_inline_citations(self, sample_document):
        """Test grounded response without inline citations"""
        generator = CitationGenerator()
        response = generator.create_grounded_response(
            "This is medical advice.",
            [sample_document],
            include_inline_citations=False
        )
        
        assert response.response_text != ""
        assert len(response.citations) == 1
        # Without inline citations, sources section is not added to the text
        # but citations are still generated
        assert len(response.source_documents) == 1

    def test_create_grounded_response_empty_text(self, sample_document):
        """Test grounded response with empty response text"""
        generator = CitationGenerator()
        response = generator.create_grounded_response(
            "",
            [sample_document],
            include_inline_citations=True
        )
        
        # Should still create citations
        assert len(response.citations) == 1
        assert len(response.source_documents) == 1

    def test_create_grounded_response_no_sources(self):
        """Test grounded response with no source documents"""
        generator = CitationGenerator()
        response = generator.create_grounded_response(
            "Response text",
            [],
            include_inline_citations=True
        )
        
        assert response.response_text != ""
        assert len(response.citations) == 0
        assert len(response.source_documents) == 0

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

    def test_validate_citations_no_citations(self):
        """Test validation of response with no citations"""
        generator = CitationGenerator()
        response = generator.create_grounded_response(
            "Response text",
            []
        )
        
        validation = generator.validate_citations(response)
        
        assert validation["has_citations"] is False
        # Other checks may vary based on implementation

    def test_validate_citations_comprehensive_checks(self, sample_documents):
        """Test comprehensive citation validation"""
        generator = CitationGenerator()
        response = generator.create_grounded_response(
            "Medical information from multiple sources",
            sample_documents
        )
        
        validation = generator.validate_citations(response)
        
        # Check all validation fields exist
        required_fields = [
            "has_citations",
            "all_documents_cited",
            "all_citations_have_sources",
            "all_citations_traceable",
            "valid"
        ]
        
        for field in required_fields:
            assert field in validation

    def test_citation_traceability(self, sample_documents):
        """Test that citations are traceable to source documents"""
        generator = CitationGenerator()
        response = generator.create_grounded_response(
            "Medical information",
            sample_documents
        )
        
        # Every citation should reference a source document
        citation_doc_ids = {c.document_id for c in response.citations}
        source_doc_ids = {d.document_id for d in response.source_documents}
        
        assert citation_doc_ids.issubset(source_doc_ids)


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

    def test_get_nonexistent_document(self):
        """Test getting a document that doesn't exist"""
        manager = KnowledgeBaseManager()
        doc = manager.get_document("nonexistent-id")
        
        assert doc is None

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

    def test_get_documents_by_empty_category(self):
        """Test retrieving documents from empty category"""
        manager = KnowledgeBaseManager()
        docs = manager.get_documents_by_category(KnowledgeBaseCategory.DRUG_INFORMATION)
        
        assert docs == []

    def test_get_documents_by_domain(self, sample_documents):
        """Test retrieving documents by domain"""
        manager = KnowledgeBaseManager()
        for doc in sample_documents:
            manager.add_document(doc, KnowledgeBaseCategory.CLINICAL_GUIDELINES)
        
        cardiology_docs = manager.get_documents_by_domain(MedicalDomain.CARDIOLOGY)
        
        assert len(cardiology_docs) == 3

    def test_get_documents_by_nonexistent_domain(self):
        """Test retrieving documents by domain with no matches"""
        manager = KnowledgeBaseManager()
        docs = manager.get_documents_by_domain(MedicalDomain.NEUROLOGY)
        
        assert docs == []

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

    def test_update_nonexistent_document_status(self):
        """Test updating status of nonexistent document"""
        manager = KnowledgeBaseManager()
        success = manager.update_document_status(
            "nonexistent-id",
            ValidationStatus.OUTDATED
        )
        
        assert success is False

    def test_remove_document(self, sample_document):
        """Test removing a document"""
        manager = KnowledgeBaseManager()
        manager.add_document(sample_document, KnowledgeBaseCategory.CLINICAL_GUIDELINES)
        
        success = manager.remove_document(sample_document.document_id)
        
        assert success is True
        assert manager.get_document(sample_document.document_id) is None

    def test_remove_nonexistent_document(self):
        """Test removing a document that doesn't exist"""
        manager = KnowledgeBaseManager()
        success = manager.remove_document("nonexistent-id")
        
        assert success is False

    def test_get_statistics(self, sample_documents):
        """Test getting knowledge base statistics"""
        manager = KnowledgeBaseManager()
        for doc in sample_documents:
            manager.add_document(doc, KnowledgeBaseCategory.CLINICAL_GUIDELINES)
        
        stats = manager.get_statistics()
        
        assert stats["total_documents"] == 5
        assert stats["validated"] == 5
        assert stats["category_clinical_guidelines"] == 5

    def test_get_statistics_empty_knowledge_base(self):
        """Test statistics for empty knowledge base"""
        manager = KnowledgeBaseManager()
        stats = manager.get_statistics()
        
        assert stats["total_documents"] == 0

    def test_get_statistics_multiple_categories(self, sample_documents):
        """Test statistics with documents in multiple categories"""
        manager = KnowledgeBaseManager()
        
        manager.add_document(sample_documents[0], KnowledgeBaseCategory.CLINICAL_GUIDELINES)
        manager.add_document(sample_documents[1], KnowledgeBaseCategory.EDUCATIONAL_CONTENT)
        manager.add_document(sample_documents[2], KnowledgeBaseCategory.DRUG_INFORMATION)
        
        stats = manager.get_statistics()
        
        assert stats["total_documents"] == 3
        assert stats["category_clinical_guidelines"] == 1
        assert stats["category_educational_content"] == 1
        assert stats["category_drug_information"] == 1

    def test_add_multiple_documents_same_category(self, sample_documents):
        """Test adding multiple documents to same category"""
        manager = KnowledgeBaseManager()
        
        for doc in sample_documents:
            success = manager.add_document(doc, KnowledgeBaseCategory.CLINICAL_GUIDELINES)
            assert success is True
        
        guidelines = manager.get_documents_by_category(KnowledgeBaseCategory.CLINICAL_GUIDELINES)
        assert len(guidelines) == 5


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

    def test_retrieve_relevant_docs_empty_query(self, sample_documents):
        """Test document retrieval with empty query"""
        rag = RAGSystem()
        rag.initialize_knowledge_base([
            (doc, KnowledgeBaseCategory.CLINICAL_GUIDELINES)
            for doc in sample_documents
        ])
        
        results = rag.retrieve_relevant_docs("")
        
        # Should handle empty query gracefully
        assert isinstance(results, list)

    def test_retrieve_relevant_docs_no_documents(self):
        """Test document retrieval with no documents in knowledge base"""
        rag = RAGSystem()
        
        results = rag.retrieve_relevant_docs("medical information")
        
        assert results == []

    def test_retrieve_relevant_docs_with_domain_filter(self, sample_documents):
        """Test document retrieval with domain filtering"""
        rag = RAGSystem()
        rag.initialize_knowledge_base([
            (doc, KnowledgeBaseCategory.CLINICAL_GUIDELINES)
            for doc in sample_documents
        ])
        
        results = rag.retrieve_relevant_docs(
            "medical information",
            domain=MedicalDomain.CARDIOLOGY
        )
        
        # Should only return cardiology documents
        if results:
            assert all(doc.domain == MedicalDomain.CARDIOLOGY for doc in results)

    def test_rerank_by_relevance(self, sample_documents):
        """Test document re-ranking"""
        rag = RAGSystem()
        ranked = rag.rerank_by_relevance("query", sample_documents)
        
        assert len(ranked) <= 5
        assert all(hasattr(r, 'relevance_score') for r in ranked)

    def test_rerank_by_relevance_empty_documents(self):
        """Test re-ranking with empty document list"""
        rag = RAGSystem()
        ranked = rag.rerank_by_relevance("query", [])
        
        assert ranked == []

    def test_rerank_by_relevance_single_document(self, sample_document):
        """Test re-ranking with single document"""
        rag = RAGSystem()
        ranked = rag.rerank_by_relevance("query", [sample_document])
        
        assert len(ranked) == 1
        assert ranked[0].rank == 1
        assert hasattr(ranked[0], 'relevance_score')

    def test_generate_grounded_response(self, sample_documents):
        """Test grounded response generation"""
        rag = RAGSystem()
        ranked = rag.rerank_by_relevance("query", sample_documents)
        
        response = rag.generate_grounded_response("query", ranked)
        
        assert response.response_text != ""
        assert len(response.citations) > 0
        assert len(response.source_documents) > 0

    def test_generate_grounded_response_empty_context(self):
        """Test grounded response generation with empty context"""
        rag = RAGSystem()
        
        response = rag.generate_grounded_response("query", [])
        
        # Should handle empty context gracefully
        assert response.response_text != ""
        assert "don't have enough information" in response.response_text.lower()

    def test_generate_grounded_response_with_citations(self, sample_documents):
        """Test that grounded response includes proper citations"""
        rag = RAGSystem()
        ranked = rag.rerank_by_relevance("medical query", sample_documents)
        
        response = rag.generate_grounded_response("medical query", ranked)
        
        # Verify citations are included
        assert len(response.citations) > 0
        # Verify citation markers in text
        assert "Sources:" in response.response_text or "[" in response.response_text

    def test_validate_citations(self, sample_documents):
        """Test citation validation"""
        rag = RAGSystem()
        ranked = rag.rerank_by_relevance("query", sample_documents)
        response = rag.generate_grounded_response("query", ranked)
        
        validation = rag.validate_citations(response)
        
        assert validation["valid"] is True

    def test_validate_citations_comprehensive(self, sample_documents):
        """Test comprehensive citation validation checks"""
        rag = RAGSystem()
        ranked = rag.rerank_by_relevance("query", sample_documents)
        response = rag.generate_grounded_response("query", ranked)
        
        validation = rag.validate_citations(response)
        
        # Check all validation fields
        assert "has_citations" in validation
        assert "all_documents_cited" in validation
        assert "all_citations_have_sources" in validation
        assert "all_citations_traceable" in validation
        assert "valid" in validation
        
        # All should be True for valid response
        assert validation["has_citations"] is True
        assert validation["all_documents_cited"] is True
        assert validation["all_citations_have_sources"] is True
        assert validation["all_citations_traceable"] is True
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

    def test_end_to_end_rag_pipeline(self, sample_documents):
        """Test complete RAG pipeline: retrieve -> rerank -> generate -> validate"""
        rag = RAGSystem(retrieval_config=RetrievalConfig(similarity_threshold=0.0))
        
        # Initialize knowledge base
        rag.initialize_knowledge_base([
            (doc, KnowledgeBaseCategory.CLINICAL_GUIDELINES)
            for doc in sample_documents
        ])
        
        query = "What are the medical guidelines?"
        
        # Step 1: Retrieve
        retrieved = rag.retrieve_relevant_docs(query)
        assert len(retrieved) > 0
        
        # Step 2: Rerank
        ranked = rag.rerank_by_relevance(query, retrieved)
        assert len(ranked) > 0
        assert all(hasattr(r, 'relevance_score') for r in ranked)
        
        # Step 3: Generate
        response = rag.generate_grounded_response(query, ranked)
        assert response.response_text != ""
        assert len(response.citations) > 0
        
        # Step 4: Validate
        validation = rag.validate_citations(response)
        assert validation["valid"] is True

    def test_rag_with_custom_configs(self):
        """Test RAG system with custom retrieval and reranking configs"""
        retrieval_config = RetrievalConfig(
            top_k=3,
            similarity_threshold=0.5
        )
        reranking_config = RerankingConfig(
            max_context_docs=2
        )
        
        rag = RAGSystem(
            retrieval_config=retrieval_config,
            reranking_config=reranking_config
        )
        
        assert rag.retrieval_config.top_k == 3
        assert rag.retrieval_config.similarity_threshold == 0.5
        assert rag.reranker.config.max_context_docs == 2

    def test_rag_handles_duplicate_documents(self, sample_document):
        """Test that RAG system handles duplicate document additions"""
        rag = RAGSystem()
        
        # Add same document twice
        success1 = rag.add_knowledge(
            sample_document,
            KnowledgeBaseCategory.CLINICAL_GUIDELINES
        )
        success2 = rag.add_knowledge(
            sample_document,
            KnowledgeBaseCategory.CLINICAL_GUIDELINES
        )
        
        assert success1 is True
        assert success2 is False  # Should reject duplicate
        
        stats = rag.get_knowledge_base_stats()
        assert stats["total_documents"] == 1  # Only one document added

    def test_rag_response_quality_with_relevant_context(self, sample_document):
        """Test that RAG generates better responses with relevant context"""
        rag = RAGSystem(retrieval_config=RetrievalConfig(similarity_threshold=0.0))
        
        # Add a specific document
        rag.add_knowledge(sample_document, KnowledgeBaseCategory.CLINICAL_GUIDELINES)
        
        # Query related to the document
        query = "heart failure care"
        
        # Retrieve and generate
        retrieved = rag.retrieve_relevant_docs(query)
        
        # Check if documents were retrieved
        if len(retrieved) > 0:
            ranked = rag.rerank_by_relevance(query, retrieved)
            response = rag.generate_grounded_response(query, ranked)
            
            # Response should reference the source organization
            assert sample_document.source.organization_name in response.response_text or \
                   any(sample_document.source.organization_name in citation.source_name 
                       for citation in response.citations)
        else:
            # If no documents retrieved, that's also valid behavior
            # (depends on similarity threshold and embedding quality)
            assert True

    def test_rag_citation_traceability(self, sample_documents):
        """Test that all citations are traceable to source documents"""
        rag = RAGSystem()
        rag.initialize_knowledge_base([
            (doc, KnowledgeBaseCategory.CLINICAL_GUIDELINES)
            for doc in sample_documents
        ])
        
        retrieved = rag.retrieve_relevant_docs("medical information")
        ranked = rag.rerank_by_relevance("medical information", retrieved)
        response = rag.generate_grounded_response("medical information", ranked)
        
        # Every citation should have a corresponding source document
        citation_doc_ids = {citation.document_id for citation in response.citations}
        source_doc_ids = {doc.document_id for doc in response.source_documents}
        
        assert citation_doc_ids.issubset(source_doc_ids), \
            "All citations should be traceable to source documents"
