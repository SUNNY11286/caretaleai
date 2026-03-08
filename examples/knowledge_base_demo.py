"""
Knowledge Base Demo
Demonstrates loading and using the CARETALE AI knowledge base
"""

import sys
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "python" / "src"))

from rag_system.knowledge_base_loader import create_and_load_knowledge_base
from rag_system.knowledge_base_manager import KnowledgeBaseCategory
from models.knowledge_document import MedicalDomain


def main():
    print("=== CARETALE AI Knowledge Base Demo ===\n")

    # Load the knowledge base (adjust path to be relative to workspace root)
    print("Loading knowledge base...")
    data_path = str(Path(__file__).parent.parent / "data" / "knowledge-base")
    knowledge_base = create_and_load_knowledge_base(data_path)
    print()

    # Display statistics
    print("Knowledge Base Statistics:")
    stats = knowledge_base.get_statistics()
    print(f"  Total documents: {stats['total_documents']}")
    print(f"  Validated: {stats['validated']}")
    print(f"  Pending review: {stats['pending_review']}")
    print(f"  Outdated: {stats['outdated']}")
    print()

    print("Documents by Category:")
    print(f"  Clinical Guidelines: {stats['category_clinical_guidelines']}")
    print(f"  Educational Content: {stats['category_educational_content']}")
    print(f"  Drug Information: {stats['category_drug_information']}")
    print(f"  Care Protocols: {stats['category_care_protocols']}")
    print()

    # Get clinical guidelines
    print("=== Clinical Guidelines ===")
    guidelines = knowledge_base.get_documents_by_category(
        KnowledgeBaseCategory.CLINICAL_GUIDELINES
    )
    for doc in guidelines:
        print(f"\n{doc.metadata.title}")
        print(f"  Source: {doc.source.name}")
        print(f"  Domain: {doc.domain.value}")
        print(f"  Last Updated: {doc.last_updated.date()}")
        print(f"  Citation: {doc.citation_format.short_form}")
    print()

    # Get drug information
    print("=== Drug Information ===")
    drugs = knowledge_base.get_documents_by_category(
        KnowledgeBaseCategory.DRUG_INFORMATION
    )
    for doc in drugs:
        print(f"\n{doc.metadata.title}")
        print(f"  Source: {doc.source.name}")
        print(f"  Keywords: {', '.join(doc.metadata.keywords)}")
    print()

    # Get documents by domain
    print("=== Cardiology Documents ===")
    cardiology_docs = knowledge_base.get_documents_by_domain(MedicalDomain.CARDIOLOGY)
    print(f"Found {len(cardiology_docs)} cardiology documents:")
    for doc in cardiology_docs:
        print(f"  - {doc.metadata.title} ({doc.source.authority})")
    print()

    # Get a specific document
    print("=== Specific Document Example ===")
    heart_failure_doc = knowledge_base.get_document("cg-001-heart-failure")
    if heart_failure_doc:
        print(f"Title: {heart_failure_doc.metadata.title}")
        print(f"Source: {heart_failure_doc.source.name}")
        print("\nContent Preview (first 200 chars):")
        print(heart_failure_doc.content[:200] + "...")
        print("\nFull Citation:")
        print(heart_failure_doc.citation_format.apa)
    print()

    # Check for outdated documents
    print("=== Document Maintenance ===")
    outdated = knowledge_base.get_outdated_documents(365)
    if outdated:
        print(f"Found {len(outdated)} documents older than 365 days:")
        for doc in outdated:
            from datetime import datetime, timezone
            age = (datetime.now(timezone.utc) - doc.last_updated).days
            print(f"  - {doc.metadata.title} ({age} days old)")
    else:
        print("All documents are up to date (less than 365 days old)")
    print()

    print("=== Demo Complete ===")


if __name__ == "__main__":
    main()
