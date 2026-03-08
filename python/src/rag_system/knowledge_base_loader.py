"""
Knowledge Base Loader Utility
Loads knowledge documents from JSON files into the Knowledge Base Manager
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

from .knowledge_base_manager import KnowledgeBaseManager, KnowledgeBaseCategory
from ..models.knowledge_document import (
    KnowledgeDocument,
    AuthoritySource,
    DocumentMetadata,
    CitationInfo,
    ValidationStatus,
    MedicalDomain
)


class KnowledgeBaseLoader:
    """Loads knowledge documents from JSON files into the Knowledge Base Manager"""

    def __init__(self, manager: KnowledgeBaseManager, data_path: str = "data/knowledge-base"):
        """
        Initialize the loader.
        
        Args:
            manager: Knowledge base manager instance
            data_path: Path to the knowledge base data directory
        """
        self.manager = manager
        self.data_path = Path(data_path)

    def load_all(self) -> Dict[str, Any]:
        """
        Load all documents from the knowledge base directory.
        
        Returns:
            Dictionary with loading results including counts and errors
        """
        results = {
            "loaded": 0,
            "failed": 0,
            "errors": []
        }

        categories = [
            ("clinical-guidelines", KnowledgeBaseCategory.CLINICAL_GUIDELINES),
            ("educational-content", KnowledgeBaseCategory.EDUCATIONAL_CONTENT),
            ("drug-information", KnowledgeBaseCategory.DRUG_INFORMATION),
            ("care-protocols", KnowledgeBaseCategory.CARE_PROTOCOLS),
        ]

        for dir_name, category in categories:
            category_path = self.data_path / dir_name

            if not category_path.exists():
                results["errors"].append(f"Directory not found: {category_path}")
                continue

            json_files = list(category_path.glob("*.json"))

            for file_path in json_files:
                try:
                    result = self.load_document(str(file_path), category)
                    if result["success"]:
                        results["loaded"] += 1
                    else:
                        results["failed"] += 1
                        results["errors"].append(f"{file_path.name}: {result.get('error', 'Unknown error')}")
                except Exception as e:
                    results["failed"] += 1
                    results["errors"].append(f"{file_path.name}: {str(e)}")

        return results

    def load_document(
        self,
        file_path: str,
        category: KnowledgeBaseCategory
    ) -> Dict[str, Any]:
        """
        Load a single document from a JSON file.
        
        Args:
            file_path: Path to the JSON file
            category: Knowledge base category
            
        Returns:
            Dictionary with success status and optional error message
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                json_doc = json.load(f)

            # Convert JSON document to KnowledgeDocument
            document = KnowledgeDocument(
                document_id=json_doc["documentId"],
                source=AuthoritySource(
                    organization_name=json_doc["source"]["organizationName"],
                    organization_type=json_doc["source"]["organizationType"],
                    url=json_doc["source"].get("url"),
                    credibility_score=json_doc["source"]["credibilityScore"]
                ),
                domain=MedicalDomain(json_doc["domain"]),
                content=json_doc["content"],
                metadata=DocumentMetadata(
                    title=json_doc["metadata"]["title"],
                    publication_date=datetime.fromisoformat(
                        json_doc["metadata"]["publicationDate"].replace('Z', '+00:00')
                    ),
                    version=json_doc["metadata"].get("version"),
                    keywords=json_doc["metadata"]["keywords"],
                    language=json_doc["metadata"]["language"],
                    document_type=json_doc["metadata"]["documentType"]
                ),
                last_updated=datetime.fromisoformat(
                    json_doc["lastUpdated"].replace('Z', '+00:00')
                ),
                validation_status=self._parse_validation_status(json_doc["validationStatus"]),
                citation_format=CitationInfo(
                    citation_text=json_doc["citationFormat"]["citationText"],
                    citation_style=json_doc["citationFormat"]["citationStyle"],
                    url=json_doc["citationFormat"].get("url")
                )
            )

            added = self.manager.add_document(document, category)

            if not added:
                return {
                    "success": False,
                    "error": "Document already exists or could not be added"
                }

            return {"success": True}

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def load_category(self, category: KnowledgeBaseCategory) -> Dict[str, Any]:
        """
        Load documents from a specific category.
        
        Args:
            category: Knowledge base category to load
            
        Returns:
            Dictionary with loading results
        """
        results = {
            "loaded": 0,
            "failed": 0,
            "errors": []
        }

        category_dirs = {
            KnowledgeBaseCategory.CLINICAL_GUIDELINES: "clinical-guidelines",
            KnowledgeBaseCategory.EDUCATIONAL_CONTENT: "educational-content",
            KnowledgeBaseCategory.DRUG_INFORMATION: "drug-information",
            KnowledgeBaseCategory.CARE_PROTOCOLS: "care-protocols",
        }

        category_path = self.data_path / category_dirs[category]

        if not category_path.exists():
            results["errors"].append(f"Directory not found: {category_path}")
            return results

        json_files = list(category_path.glob("*.json"))

        for file_path in json_files:
            try:
                result = self.load_document(str(file_path), category)
                if result["success"]:
                    results["loaded"] += 1
                else:
                    results["failed"] += 1
                    results["errors"].append(f"{file_path.name}: {result.get('error', 'Unknown error')}")
            except Exception as e:
                results["failed"] += 1
                results["errors"].append(f"{file_path.name}: {str(e)}")

        return results

    def _parse_validation_status(self, status: str) -> ValidationStatus:
        """Parse validation status string to enum"""
        status_lower = status.lower()
        if status_lower == "validated":
            return ValidationStatus.VALIDATED
        elif status_lower == "pending_review":
            return ValidationStatus.PENDING_REVIEW
        elif status_lower == "outdated":
            return ValidationStatus.OUTDATED
        else:
            return ValidationStatus.PENDING_REVIEW


def create_and_load_knowledge_base(data_path: str = None) -> KnowledgeBaseManager:
    """
    Convenience function to create and load a knowledge base.
    
    Args:
        data_path: Optional path to knowledge base data directory
        
    Returns:
        Loaded knowledge base manager
    """
    manager = KnowledgeBaseManager()
    loader = KnowledgeBaseLoader(
        manager,
        data_path if data_path else "data/knowledge-base"
    )
    results = loader.load_all()

    print(f"Knowledge Base loaded: {results['loaded']} documents loaded, {results['failed']} failed")

    if results["errors"]:
        print("Errors during loading:")
        for error in results["errors"]:
            print(f"  - {error}")

    return manager
