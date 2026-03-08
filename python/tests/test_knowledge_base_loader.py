"""
Tests for Knowledge Base Loader
"""

import pytest
from pathlib import Path

from src.rag_system.knowledge_base_loader import KnowledgeBaseLoader, create_and_load_knowledge_base
from src.rag_system.knowledge_base_manager import KnowledgeBaseManager, KnowledgeBaseCategory
from src.models.knowledge_document import ValidationStatus


class TestKnowledgeBaseLoader:
    """Test suite for Knowledge Base Loader"""

    def test_load_all_documents(self):
        """Test loading all documents from the knowledge base"""
        manager = KnowledgeBaseManager()
        data_path = str(Path(__file__).parent.parent.parent / "data" / "knowledge-base")
        loader = KnowledgeBaseLoader(manager, data_path)
        
        results = loader.load_all()
        
        # Should have loaded documents successfully
        assert results["loaded"] > 0, "Should load at least one document"
        assert results["loaded"] == 12, f"Should load 12 documents, loaded {results['loaded']}"
        assert results["failed"] == 0, f"Should have no failures, but had {results['failed']}"
        
        # Check that documents are in the manager
        all_docs = manager.get_all_documents()
        assert len(all_docs) == 12, f"Manager should have 12 documents, has {len(all_docs)}"

    def test_load_clinical_guidelines(self):
        """Test loading clinical guidelines category"""
        manager = KnowledgeBaseManager()
        data_path = str(Path(__file__).parent.parent.parent / "data" / "knowledge-base")
        loader = KnowledgeBaseLoader(manager, data_path)
        
        results = loader.load_category(KnowledgeBaseCategory.CLINICAL_GUIDELINES)
        
        assert results["loaded"] == 3, "Should load 3 clinical guidelines"
        assert results["failed"] == 0, "Should have no failures"
        
        # Verify documents are in the correct category
        guidelines = manager.get_documents_by_category(KnowledgeBaseCategory.CLINICAL_GUIDELINES)
        assert len(guidelines) == 3, "Should have 3 guidelines in the category"

    def test_load_educational_content(self):
        """Test loading educational content category"""
        manager = KnowledgeBaseManager()
        data_path = str(Path(__file__).parent.parent.parent / "data" / "knowledge-base")
        loader = KnowledgeBaseLoader(manager, data_path)
        
        results = loader.load_category(KnowledgeBaseCategory.EDUCATIONAL_CONTENT)
        
        assert results["loaded"] == 3, "Should load 3 educational content documents"
        assert results["failed"] == 0, "Should have no failures"

    def test_load_drug_information(self):
        """Test loading drug information category"""
        manager = KnowledgeBaseManager()
        data_path = str(Path(__file__).parent.parent.parent / "data" / "knowledge-base")
        loader = KnowledgeBaseLoader(manager, data_path)
        
        results = loader.load_category(KnowledgeBaseCategory.DRUG_INFORMATION)
        
        assert results["loaded"] == 3, "Should load 3 drug information documents"
        assert results["failed"] == 0, "Should have no failures"

    def test_load_care_protocols(self):
        """Test loading care protocols category"""
        manager = KnowledgeBaseManager()
        data_path = str(Path(__file__).parent.parent.parent / "data" / "knowledge-base")
        loader = KnowledgeBaseLoader(manager, data_path)
        
        results = loader.load_category(KnowledgeBaseCategory.CARE_PROTOCOLS)
        
        assert results["loaded"] == 3, "Should load 3 care protocol documents"
        assert results["failed"] == 0, "Should have no failures"

    def test_document_validation_status(self):
        """Test that loaded documents have correct validation status"""
        manager = KnowledgeBaseManager()
        data_path = str(Path(__file__).parent.parent.parent / "data" / "knowledge-base")
        loader = KnowledgeBaseLoader(manager, data_path)
        
        loader.load_all()
        
        # All sample documents should be validated
        validated_docs = manager.get_validated_documents()
        assert len(validated_docs) == 12, "All 12 documents should be validated"

    def test_document_metadata(self):
        """Test that document metadata is loaded correctly"""
        manager = KnowledgeBaseManager()
        data_path = str(Path(__file__).parent.parent.parent / "data" / "knowledge-base")
        loader = KnowledgeBaseLoader(manager, data_path)
        
        loader.load_all()
        
        # Check a specific document
        doc = manager.get_document("cg-001-heart-failure")
        assert doc is not None, "Should find heart failure document"
        assert doc.metadata.title == "Heart Failure Management Guidelines"
        assert doc.source.organization_name == "American Heart Association"
        assert doc.source.organization_type == "professional_association"
        assert "heart failure" in doc.metadata.keywords
        assert doc.validation_status == ValidationStatus.VALIDATED

    def test_create_and_load_convenience_function(self):
        """Test the convenience function for creating and loading knowledge base"""
        data_path = str(Path(__file__).parent.parent.parent / "data" / "knowledge-base")
        manager = create_and_load_knowledge_base(data_path)
        
        # Should have loaded all documents
        stats = manager.get_statistics()
        assert stats["total_documents"] == 12, "Should have 12 total documents"
        assert stats["validated"] == 12, "All documents should be validated"
        assert stats["category_clinical_guidelines"] == 3
        assert stats["category_educational_content"] == 3
        assert stats["category_drug_information"] == 3
        assert stats["category_care_protocols"] == 3

    def test_load_nonexistent_directory(self):
        """Test loading from a nonexistent directory"""
        manager = KnowledgeBaseManager()
        loader = KnowledgeBaseLoader(manager, "nonexistent/path")
        
        results = loader.load_all()
        
        # Should have errors but not crash
        assert results["loaded"] == 0
        assert len(results["errors"]) > 0
