"""
Knowledge Base Manager Component
Maintains curated library of approved clinical sources.
"""

from typing import List, Optional, Dict
from datetime import datetime, timezone
from enum import Enum

from ..models.knowledge_document import (
    KnowledgeDocument,
    MedicalDomain,
    ValidationStatus
)


class KnowledgeBaseCategory(str, Enum):
    """Categories of knowledge in the knowledge base"""
    CLINICAL_GUIDELINES = "clinical_guidelines"
    EDUCATIONAL_CONTENT = "educational_content"
    DRUG_INFORMATION = "drug_information"
    CARE_PROTOCOLS = "care_protocols"


class KnowledgeBaseManager:
    """
    Manages the curated knowledge base of approved clinical sources.
    Handles document storage, retrieval, validation, and updates.
    """

    def __init__(self):
        """Initialize the knowledge base manager."""
        self.documents: Dict[str, KnowledgeDocument] = {}
        self.categories: Dict[KnowledgeBaseCategory, List[str]] = {
            category: [] for category in KnowledgeBaseCategory
        }

    def add_document(
        self,
        document: KnowledgeDocument,
        category: KnowledgeBaseCategory
    ) -> bool:
        """
        Add a document to the knowledge base.
        
        Args:
            document: Knowledge document to add
            category: Category to add the document to
            
        Returns:
            True if document was added successfully
        """
        # Check if document already exists
        if document.document_id in self.documents:
            return False

        # Add document
        self.documents[document.document_id] = document
        self.categories[category].append(document.document_id)
        
        return True

    def get_document(self, document_id: str) -> Optional[KnowledgeDocument]:
        """
        Retrieve a document by ID.
        
        Args:
            document_id: Document identifier
            
        Returns:
            Knowledge document or None if not found
        """
        return self.documents.get(document_id)

    def get_documents_by_category(
        self,
        category: KnowledgeBaseCategory
    ) -> List[KnowledgeDocument]:
        """
        Get all documents in a category.
        
        Args:
            category: Knowledge base category
            
        Returns:
            List of documents in the category
        """
        doc_ids = self.categories.get(category, [])
        return [self.documents[doc_id] for doc_id in doc_ids if doc_id in self.documents]

    def get_documents_by_domain(
        self,
        domain: MedicalDomain
    ) -> List[KnowledgeDocument]:
        """
        Get all documents for a medical domain.
        
        Args:
            domain: Medical domain
            
        Returns:
            List of documents in the domain
        """
        return [
            doc for doc in self.documents.values()
            if doc.domain == domain
        ]

    def get_validated_documents(self) -> List[KnowledgeDocument]:
        """
        Get all validated documents.
        
        Returns:
            List of validated documents
        """
        return [
            doc for doc in self.documents.values()
            if doc.validation_status == ValidationStatus.VALIDATED
        ]

    def update_document_status(
        self,
        document_id: str,
        new_status: ValidationStatus
    ) -> bool:
        """
        Update the validation status of a document.
        
        Args:
            document_id: Document identifier
            new_status: New validation status
            
        Returns:
            True if update was successful
        """
        if document_id not in self.documents:
            return False
        
        self.documents[document_id].validation_status = new_status
        return True

    def remove_document(self, document_id: str) -> bool:
        """
        Remove a document from the knowledge base.
        
        Args:
            document_id: Document identifier
            
        Returns:
            True if document was removed
        """
        if document_id not in self.documents:
            return False
        
        # Remove from categories
        for category_docs in self.categories.values():
            if document_id in category_docs:
                category_docs.remove(document_id)
        
        # Remove document
        del self.documents[document_id]
        return True

    def get_outdated_documents(self, days_threshold: int = 365) -> List[KnowledgeDocument]:
        """
        Get documents that haven't been updated recently.
        
        Args:
            days_threshold: Number of days to consider a document outdated
            
        Returns:
            List of outdated documents
        """
        now = datetime.now(timezone.utc)
        outdated = []
        
        for doc in self.documents.values():
            last_updated = doc.last_updated
            if last_updated.tzinfo is None:
                last_updated = last_updated.replace(tzinfo=timezone.utc)
            
            age_days = (now - last_updated).days
            if age_days > days_threshold:
                outdated.append(doc)
        
        return outdated

    def get_all_documents(self) -> List[KnowledgeDocument]:
        """
        Get all documents in the knowledge base.
        
        Returns:
            List of all documents
        """
        return list(self.documents.values())

    def get_statistics(self) -> Dict[str, int]:
        """
        Get statistics about the knowledge base.
        
        Returns:
            Dictionary with statistics
        """
        stats = {
            "total_documents": len(self.documents),
            "validated": sum(
                1 for doc in self.documents.values()
                if doc.validation_status == ValidationStatus.VALIDATED
            ),
            "pending_review": sum(
                1 for doc in self.documents.values()
                if doc.validation_status == ValidationStatus.PENDING_REVIEW
            ),
            "outdated": sum(
                1 for doc in self.documents.values()
                if doc.validation_status == ValidationStatus.OUTDATED
            ),
        }
        
        # Add category counts
        for category in KnowledgeBaseCategory:
            stats[f"category_{category.value}"] = len(self.categories[category])
        
        return stats
