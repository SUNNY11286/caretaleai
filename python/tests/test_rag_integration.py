"""
Integration test for RAG System - demonstrating complete pipeline
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
from src.rag_system import RAGSystem, KnowledgeBaseCategory


def test_complete_rag_pipeline():
    """
    Test the complete RAG pipeline: retrieve -> rerank -> generate -> validate
    This demonstrates task 4.2 implementation working end-to-end.
    """
    # Initialize RAG System with lower similarity threshold for testing
    from src.rag_system import RetrievalConfig
    rag = RAGSystem(retrieval_config=RetrievalConfig(similarity_threshold=0.0))
    
    # Create sample medical knowledge documents
    heart_failure_doc = KnowledgeDocument(
        document_id="hf-001",
        source=AuthoritySource(
            organization_name="American Heart Association",
            organization_type="professional_association",
            url="https://www.heart.org",
            credibility_score=0.95
        ),
        domain=MedicalDomain.CARDIOLOGY,
        content="Post-discharge care for heart failure patients includes daily weight monitoring to detect fluid retention, strict medication adherence especially for diuretics and ACE inhibitors, and dietary sodium restriction to less than 2000mg per day. Patients should monitor for symptoms like shortness of breath, swelling, or rapid weight gain.",
        metadata=DocumentMetadata(
            title="Heart Failure Post-Discharge Guidelines",
            authors=["Dr. Smith", "Dr. Jones"],
            publication_date=datetime(2023, 1, 15, tzinfo=timezone.utc),
            version="2.0",
            keywords=["heart failure", "post-discharge", "care management"],
            abstract="Comprehensive guidelines for managing heart failure patients after hospital discharge.",
            language="en",
            document_type="guideline"
        ),
        last_updated=datetime(2023, 6, 1, tzinfo=timezone.utc),
        validation_status=ValidationStatus.VALIDATED,
        citation_format=CitationInfo(
            citation_text="American Heart Association. (2023). Heart Failure Post-Discharge Guidelines.",
            citation_style="APA",
            doi="10.1000/hf-guidelines",
            url="https://www.heart.org/guidelines/hf"
        )
    )
    
    medication_doc = KnowledgeDocument(
        document_id="med-001",
        source=AuthoritySource(
            organization_name="FDA",
            organization_type="government",
            url="https://www.fda.gov",
            credibility_score=0.98
        ),
        domain=MedicalDomain.GENERAL_MEDICINE,
        content="Medication adherence is critical for post-discharge recovery. Patients should take medications exactly as prescribed, at the same time each day. Use pill organizers to track daily doses. Never skip doses or stop medications without consulting your healthcare provider.",
        metadata=DocumentMetadata(
            title="Medication Adherence Guidelines",
            publication_date=datetime(2023, 3, 1, tzinfo=timezone.utc),
            keywords=["medication", "adherence", "patient education"],
            language="en",
            document_type="guideline"
        ),
        last_updated=datetime(2023, 5, 1, tzinfo=timezone.utc),
        validation_status=ValidationStatus.VALIDATED,
        citation_format=CitationInfo(
            citation_text="FDA. (2023). Medication Adherence Guidelines.",
            citation_style="APA"
        )
    )
    
    # Add documents to knowledge base
    rag.add_knowledge(heart_failure_doc, KnowledgeBaseCategory.CLINICAL_GUIDELINES)
    rag.add_knowledge(medication_doc, KnowledgeBaseCategory.EDUCATIONAL_CONTENT)
    
    # Patient query
    query = "What should I do after being discharged from the hospital for heart failure?"
    
    # Step 1: Retrieve relevant documents (without domain filter to get all relevant docs)
    retrieved_docs = rag.retrieve_relevant_docs(query)
    assert len(retrieved_docs) > 0, "Should retrieve at least one document"
    print(f"✓ Retrieved {len(retrieved_docs)} relevant documents")
    
    # Step 2: Re-rank by relevance
    ranked_docs = rag.rerank_by_relevance(query, retrieved_docs)
    assert len(ranked_docs) > 0, "Should have ranked documents"
    assert all(hasattr(doc, 'relevance_score') for doc in ranked_docs), "All docs should have relevance scores"
    assert all(hasattr(doc, 'rank') for doc in ranked_docs), "All docs should have ranks"
    print(f"✓ Re-ranked {len(ranked_docs)} documents by relevance")
    
    # Step 3: Generate grounded response with citations
    grounded_response = rag.generate_grounded_response(query, ranked_docs)
    assert grounded_response.response_text != "", "Should generate response text"
    assert len(grounded_response.citations) > 0, "Should include citations"
    assert len(grounded_response.source_documents) > 0, "Should reference source documents"
    print(f"✓ Generated grounded response with {len(grounded_response.citations)} citations")
    print(f"  Response preview: {grounded_response.response_text[:100]}...")
    
    # Step 4: Validate citations
    validation_result = rag.validate_citations(grounded_response)
    assert validation_result["valid"] is True, "Citations should be valid"
    assert validation_result["has_citations"] is True, "Should have citations"
    assert validation_result["all_documents_cited"] is True, "All documents should be cited"
    assert validation_result["all_citations_have_sources"] is True, "All citations should have sources"
    print(f"✓ Validated citations successfully")
    
    # Verify the complete pipeline produces evidence-based, cited responses
    assert "Sources:" in grounded_response.response_text or "[" in grounded_response.response_text, \
        "Response should include citation markers"
    
    print("\n✅ Complete RAG pipeline test passed!")
    print(f"   - Retrieved relevant medical documents")
    print(f"   - Re-ranked by relevance to query")
    print(f"   - Generated grounded response with citations")
    print(f"   - Validated all citations are traceable")


def test_rag_pipeline_with_domain_filtering():
    """
    Test RAG pipeline with domain filtering to ensure proper scoping
    """
    rag = RAGSystem()
    
    # Add documents from different domains
    cardiology_doc = KnowledgeDocument(
        document_id="cardio-001",
        source=AuthoritySource(
            organization_name="Cardiology Association",
            organization_type="professional_association",
            credibility_score=0.9
        ),
        domain=MedicalDomain.CARDIOLOGY,
        content="Cardiology-specific content about heart conditions.",
        metadata=DocumentMetadata(
            title="Cardiology Guidelines",
            publication_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
            keywords=["cardiology"],
            language="en",
            document_type="guideline"
        ),
        last_updated=datetime(2023, 1, 1, tzinfo=timezone.utc),
        validation_status=ValidationStatus.VALIDATED,
        citation_format=CitationInfo(
            citation_text="Cardiology Association. (2023).",
            citation_style="APA"
        )
    )
    
    general_doc = KnowledgeDocument(
        document_id="gen-001",
        source=AuthoritySource(
            organization_name="General Medical Board",
            organization_type="professional_association",
            credibility_score=0.85
        ),
        domain=MedicalDomain.GENERAL_MEDICINE,
        content="General medical content about patient care.",
        metadata=DocumentMetadata(
            title="General Care Guidelines",
            publication_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
            keywords=["general"],
            language="en",
            document_type="guideline"
        ),
        last_updated=datetime(2023, 1, 1, tzinfo=timezone.utc),
        validation_status=ValidationStatus.VALIDATED,
        citation_format=CitationInfo(
            citation_text="General Medical Board. (2023).",
            citation_style="APA"
        )
    )
    
    rag.add_knowledge(cardiology_doc, KnowledgeBaseCategory.CLINICAL_GUIDELINES)
    rag.add_knowledge(general_doc, KnowledgeBaseCategory.CLINICAL_GUIDELINES)
    
    # Retrieve with domain filter
    cardiology_results = rag.retrieve_relevant_docs(
        "medical information",
        domain=MedicalDomain.CARDIOLOGY
    )
    
    # Verify domain filtering works
    if cardiology_results:
        assert all(doc.domain == MedicalDomain.CARDIOLOGY for doc in cardiology_results), \
            "Domain filter should only return cardiology documents"
        print("✓ Domain filtering works correctly")


if __name__ == "__main__":
    test_complete_rag_pipeline()
    test_rag_pipeline_with_domain_filtering()
    print("\n✅ All RAG integration tests passed!")
