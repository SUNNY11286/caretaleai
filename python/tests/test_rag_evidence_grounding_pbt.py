"""
Property-Based Tests for RAG System - Evidence-Based Information Grounding

Feature: caretale-ai
Property 7: Evidence-Based Information Grounding

For any medical information request, the RAG System should ground all responses
in approved clinical guidelines with proper source attribution, prioritizing
patient-specific instructions over general guidelines when conflicts arise.

**Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5**
"""

import pytest
from hypothesis import given, strategies as st, assume, settings
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
    RetrievalConfig,
    KnowledgeBaseCategory
)


# Custom strategies for generating test data
@st.composite
def medical_domain_strategy(draw):
    """Generate random medical domains"""
    return draw(st.sampled_from(list(MedicalDomain)))


@st.composite
def authority_source_strategy(draw):
    """Generate valid authority sources"""
    org_types = ["government", "professional_association", "academic", "healthcare_system"]
    org_names = [
        "American Heart Association",
        "FDA",
        "CDC",
        "WHO",
        "Mayo Clinic",
        "Johns Hopkins Medicine",
        "American Medical Association",
        "National Institutes of Health"
    ]
    
    return AuthoritySource(
        organization_name=draw(st.sampled_from(org_names)),
        organization_type=draw(st.sampled_from(org_types)),
        url=f"https://www.{draw(st.text(alphabet=st.characters(whitelist_categories=('Ll',)), min_size=3, max_size=10))}.org",
        credibility_score=draw(st.floats(min_value=0.7, max_value=1.0))
    )


@st.composite
def document_metadata_strategy(draw):
    """Generate valid document metadata"""
    doc_types = ["guideline", "protocol", "educational", "research", "reference"]
    
    return DocumentMetadata(
        title=draw(st.text(min_size=10, max_size=100)),
        authors=[draw(st.text(min_size=5, max_size=30)) for _ in range(draw(st.integers(min_value=1, max_value=3)))],
        publication_date=datetime(
            year=draw(st.integers(min_value=2020, max_value=2024)),
            month=draw(st.integers(min_value=1, max_value=12)),
            day=draw(st.integers(min_value=1, max_value=28)),
            tzinfo=timezone.utc
        ),
        version=f"{draw(st.integers(min_value=1, max_value=5))}.{draw(st.integers(min_value=0, max_value=9))}",
        keywords=draw(st.lists(st.text(min_size=3, max_size=20), min_size=1, max_size=5)),
        abstract=draw(st.text(min_size=50, max_size=200)),
        language="en",
        document_type=draw(st.sampled_from(doc_types))
    )


@st.composite
def citation_info_strategy(draw):
    """Generate valid citation information"""
    styles = ["APA", "MLA", "Chicago", "Vancouver"]
    
    return CitationInfo(
        citation_text=draw(st.text(min_size=20, max_size=150)),
        citation_style=draw(st.sampled_from(styles)),
        doi=f"10.{draw(st.integers(min_value=1000, max_value=9999))}/example",
        url=f"https://www.example.org/{draw(st.text(alphabet=st.characters(whitelist_categories=('Ll',)), min_size=5, max_size=15))}"
    )


@st.composite
def knowledge_document_strategy(draw, is_patient_specific=False):
    """Generate valid knowledge documents"""
    doc_id_prefix = "patient-specific" if is_patient_specific else "general"
    
    # Generate content that indicates whether it's patient-specific or general
    if is_patient_specific:
        content_prefix = "Patient-specific discharge instructions: "
        content_body = draw(st.text(min_size=100, max_size=500))
    else:
        content_prefix = "General clinical guideline: "
        content_body = draw(st.text(min_size=100, max_size=500))
    
    return KnowledgeDocument(
        document_id=f"{doc_id_prefix}-{draw(st.integers(min_value=1, max_value=10000))}",
        source=draw(authority_source_strategy()),
        domain=draw(medical_domain_strategy()),
        content=content_prefix + content_body,
        metadata=draw(document_metadata_strategy()),
        last_updated=datetime.now(timezone.utc),
        validation_status=ValidationStatus.VALIDATED,
        citation_format=draw(citation_info_strategy())
    )


@st.composite
def medical_query_strategy(draw):
    """Generate medical information queries"""
    query_templates = [
        "What should I do about {}?",
        "How do I manage {}?",
        "What are the guidelines for {}?",
        "Can you explain {} to me?",
        "What is the recommended treatment for {}?",
        "How should I care for {}?",
        "What precautions should I take for {}?"
    ]
    
    medical_topics = [
        "heart failure",
        "diabetes management",
        "wound care",
        "medication adherence",
        "post-surgical recovery",
        "blood pressure monitoring",
        "pain management",
        "infection prevention"
    ]
    
    template = draw(st.sampled_from(query_templates))
    topic = draw(st.sampled_from(medical_topics))
    
    return template.format(topic)


class TestEvidenceBasedInformationGrounding:
    """
    Property 7: Evidence-Based Information Grounding
    
    For any medical information request, the RAG System should ground all responses
    in approved clinical guidelines with proper source attribution, prioritizing
    patient-specific instructions over general guidelines when conflicts arise.
    
    **Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5**
    """

    @given(
        query=medical_query_strategy(),
        general_docs=st.lists(knowledge_document_strategy(is_patient_specific=False), min_size=1, max_size=5)
    )
    @settings(max_examples=100, deadline=None)
    def test_property_responses_grounded_in_clinical_guidelines(self, query, general_docs):
        """
        Property 7.1: Responses Grounded in Clinical Guidelines
        
        **Validates: Requirements 6.1, 6.2**
        
        WHEN providing medical information, THE RAG_System SHALL retrieve context
        from approved clinical guidelines and ground all medical advice in
        evidence-based sources.
        """
        # Initialize RAG system with low similarity threshold for testing
        rag = RAGSystem(retrieval_config=RetrievalConfig(similarity_threshold=0.0))
        
        # Add general clinical guidelines to knowledge base
        for doc in general_docs:
            rag.add_knowledge(doc, KnowledgeBaseCategory.CLINICAL_GUIDELINES)
        
        # Retrieve relevant documents
        retrieved_docs = rag.retrieve_relevant_docs(query)
        
        # Verify documents are retrieved from approved sources
        assert len(retrieved_docs) > 0, \
            "RAG system should retrieve at least one document for medical queries"
        
        # Verify all retrieved documents are validated (Requirement 6.1)
        for doc in retrieved_docs:
            assert doc.validation_status == ValidationStatus.VALIDATED, \
                "All retrieved documents should be validated clinical guidelines"
        
        # Re-rank and generate response
        ranked_docs = rag.rerank_by_relevance(query, retrieved_docs)
        response = rag.generate_grounded_response(query, ranked_docs)
        
        # Verify response is grounded in evidence-based sources (Requirement 6.2)
        assert response.response_text, \
            "Response should contain text grounded in clinical guidelines"
        assert len(response.source_documents) > 0, \
            "Response should reference source documents"
        
        # Verify all source documents are from approved clinical guidelines
        for source_doc in response.source_documents:
            assert source_doc.validation_status == ValidationStatus.VALIDATED, \
                "All source documents should be validated"
            assert source_doc.source.credibility_score >= 0.7, \
                "All sources should have high credibility scores"

    @given(
        query=medical_query_strategy(),
        docs=st.lists(knowledge_document_strategy(is_patient_specific=False), min_size=1, max_size=5)
    )
    @settings(max_examples=100, deadline=None)
    def test_property_proper_source_attribution(self, query, docs):
        """
        Property 7.2: Proper Source Attribution
        
        **Validates: Requirements 6.3, 6.5**
        
        THE RAG_System SHALL maintain a curated knowledge base of public clinical
        guidelines and track information sources for transparency and verification.
        """
        # Initialize RAG system
        rag = RAGSystem(retrieval_config=RetrievalConfig(similarity_threshold=0.0))
        
        # Add documents to knowledge base
        for doc in docs:
            rag.add_knowledge(doc, KnowledgeBaseCategory.CLINICAL_GUIDELINES)
        
        # Retrieve and generate response
        retrieved_docs = rag.retrieve_relevant_docs(query)
        
        if len(retrieved_docs) > 0:
            ranked_docs = rag.rerank_by_relevance(query, retrieved_docs)
            response = rag.generate_grounded_response(query, ranked_docs)
            
            # Verify proper source attribution (Requirement 6.5)
            assert len(response.citations) > 0, \
                "Response should include citations for source attribution"
            
            # Verify all citations have required information
            for citation in response.citations:
                assert citation.citation_text, \
                    "Each citation should have formatted citation text"
                assert citation.source_name, \
                    "Each citation should identify the source organization"
                assert citation.document_id, \
                    "Each citation should be traceable to a document ID"
            
            # Validate citations are traceable (Requirement 6.5)
            validation = rag.validate_citations(response)
            assert validation["has_citations"], \
                "Response should have citations"
            assert validation["all_citations_have_sources"], \
                "All citations should have source information"
            assert validation["all_citations_traceable"], \
                "All citations should be traceable to source documents"
            assert validation["valid"], \
                "Citation validation should pass for properly attributed responses"

    @given(
        query=medical_query_strategy(),
        patient_specific_doc=knowledge_document_strategy(is_patient_specific=True),
        general_docs=st.lists(knowledge_document_strategy(is_patient_specific=False), min_size=1, max_size=3)
    )
    @settings(max_examples=100, deadline=None)
    def test_property_patient_specific_instructions_prioritized(self, query, patient_specific_doc, general_docs):
        """
        Property 7.3: Patient-Specific Instructions Prioritized
        
        **Validates: Requirement 6.4**
        
        WHEN information conflicts arise, THE RAG_System SHALL prioritize
        patient-specific discharge instructions over general guidelines.
        """
        # Initialize RAG system
        rag = RAGSystem(retrieval_config=RetrievalConfig(similarity_threshold=0.0))
        
        # Add patient-specific document with higher priority
        rag.add_knowledge(patient_specific_doc, KnowledgeBaseCategory.CARE_PROTOCOLS)
        
        # Add general clinical guidelines
        for doc in general_docs:
            rag.add_knowledge(doc, KnowledgeBaseCategory.CLINICAL_GUIDELINES)
        
        # Retrieve all documents
        retrieved_docs = rag.retrieve_relevant_docs(query)
        
        # Check if patient-specific document was retrieved
        patient_specific_retrieved = any(
            doc.document_id == patient_specific_doc.document_id
            for doc in retrieved_docs
        )
        
        if patient_specific_retrieved and len(retrieved_docs) > 1:
            # Re-rank documents
            ranked_docs = rag.rerank_by_relevance(query, retrieved_docs)
            
            # Generate response
            response = rag.generate_grounded_response(query, ranked_docs)
            
            # Verify patient-specific document is included in sources (Requirement 6.4)
            source_doc_ids = [doc.document_id for doc in response.source_documents]
            
            # If patient-specific document was retrieved, it should be prioritized
            # This means it should appear in the source documents used for the response
            assert patient_specific_doc.document_id in source_doc_ids, \
                "Patient-specific instructions should be included when available"
            
            # Verify the response references patient-specific content
            # (indicated by the "Patient-specific discharge instructions:" prefix)
            patient_specific_content_used = any(
                "Patient-specific" in doc.content
                for doc in response.source_documents
            )
            
            assert patient_specific_content_used, \
                "Response should prioritize patient-specific discharge instructions"

    @given(
        query=medical_query_strategy(),
        docs=st.lists(knowledge_document_strategy(is_patient_specific=False), min_size=2, max_size=5)
    )
    @settings(max_examples=100, deadline=None)
    def test_property_knowledge_base_maintains_approved_sources(self, query, docs):
        """
        Property 7.4: Knowledge Base Maintains Approved Sources
        
        **Validates: Requirement 6.3**
        
        THE RAG_System SHALL maintain a curated knowledge base of public clinical
        guidelines and educational content.
        """
        # Initialize RAG system
        rag = RAGSystem()
        
        # Add documents to different categories
        for i, doc in enumerate(docs):
            if i % 2 == 0:
                category = KnowledgeBaseCategory.CLINICAL_GUIDELINES
            else:
                category = KnowledgeBaseCategory.EDUCATIONAL_CONTENT
            
            success = rag.add_knowledge(doc, category)
            assert success, "Should successfully add approved documents to knowledge base"
        
        # Verify knowledge base statistics
        stats = rag.get_knowledge_base_stats()
        assert stats["total_documents"] == len(docs), \
            "Knowledge base should track all added documents"
        assert stats["validated"] == len(docs), \
            "All documents in knowledge base should be validated"
        
        # Verify documents can be retrieved
        retrieved_docs = rag.retrieve_relevant_docs(query)
        
        # All retrieved documents should be from the curated knowledge base
        for doc in retrieved_docs:
            assert doc.validation_status == ValidationStatus.VALIDATED, \
                "Knowledge base should only contain validated documents"
            assert doc.source.credibility_score >= 0.7, \
                "Knowledge base should only contain credible sources"

    @given(
        query=medical_query_strategy(),
        docs=st.lists(knowledge_document_strategy(is_patient_specific=False), min_size=1, max_size=5)
    )
    @settings(max_examples=100, deadline=None)
    def test_property_complete_evidence_based_pipeline(self, query, docs):
        """
        Property 7.5: Complete Evidence-Based Information Pipeline
        
        **Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5**
        
        For any medical information request, the complete RAG pipeline should:
        1. Retrieve from approved clinical guidelines (6.1)
        2. Ground responses in evidence-based sources (6.2)
        3. Use curated knowledge base (6.3)
        4. Track sources for transparency (6.5)
        """
        # Initialize RAG system
        rag = RAGSystem(retrieval_config=RetrievalConfig(similarity_threshold=0.0))
        
        # Build curated knowledge base (Requirement 6.3)
        for doc in docs:
            rag.add_knowledge(doc, KnowledgeBaseCategory.CLINICAL_GUIDELINES)
        
        # Execute complete pipeline
        # Step 1: Retrieve from approved guidelines (Requirement 6.1)
        retrieved_docs = rag.retrieve_relevant_docs(query)
        assert len(retrieved_docs) > 0, \
            "Should retrieve documents from approved clinical guidelines"
        
        # Verify all retrieved documents are validated
        for doc in retrieved_docs:
            assert doc.validation_status == ValidationStatus.VALIDATED
        
        # Step 2: Re-rank by relevance
        ranked_docs = rag.rerank_by_relevance(query, retrieved_docs)
        assert len(ranked_docs) > 0, "Should have ranked documents"
        
        # Step 3: Generate grounded response (Requirement 6.2)
        response = rag.generate_grounded_response(query, ranked_docs)
        assert response.response_text, \
            "Should generate response grounded in evidence-based sources"
        assert len(response.source_documents) > 0, \
            "Response should be grounded in source documents"
        
        # Step 4: Verify source tracking and transparency (Requirement 6.5)
        assert len(response.citations) > 0, \
            "Should track information sources with citations"
        
        validation = rag.validate_citations(response)
        assert validation["valid"], \
            "Citations should be valid and traceable"
        assert validation["all_citations_traceable"], \
            "All citations should be traceable to source documents"
        
        # Verify complete evidence-based pipeline
        # All source documents should be from approved, validated sources
        for source_doc in response.source_documents:
            assert source_doc.validation_status == ValidationStatus.VALIDATED
            assert source_doc.source.credibility_score >= 0.7
        
        # All citations should reference these validated sources
        citation_doc_ids = {c.document_id for c in response.citations}
        source_doc_ids = {d.document_id for d in response.source_documents}
        assert citation_doc_ids.issubset(source_doc_ids), \
            "All citations should reference validated source documents"
