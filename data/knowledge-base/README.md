# CARETALE AI Knowledge Base

This directory contains the curated knowledge base for the CARETALE AI system. All documents are stored in JSON format and organized by category.

## Directory Structure

```
data/knowledge-base/
├── clinical-guidelines/     # Evidence-based clinical protocols and guidelines
├── educational-content/     # Patient education materials
├── drug-information/        # Medication information and safety guidelines
├── care-protocols/          # Standardized care pathways for post-discharge scenarios
└── README.md               # This file
```

## Categories

### Clinical Guidelines
Evidence-based medical recommendations and protocols from authoritative medical organizations. These provide the foundation for clinical decision support and care recommendations.

**Current documents:**
- Heart Failure Management Guidelines (AHA)
- Diabetes Post-Discharge Management (ADA)
- Post-Surgical Wound Care Guidelines (WHS)

### Educational Content
Patient-friendly explanations of medical concepts, procedures, and self-care practices. Written at appropriate health literacy levels (5th-6th grade reading level).

**Current documents:**
- Understanding Your Blood Pressure (NHLBI)
- Taking Your Medications Safely (AHRQ)
- Recognizing Medical Warning Signs (CDC)

### Drug Information
Comprehensive medication information including usage instructions, side effects, interactions, and safety warnings. Based on authoritative sources like MedlinePlus.

**Current documents:**
- Metoprolol (Beta-Blocker)
- Lisinopril (ACE Inhibitor)
- Warfarin (Anticoagulant)

### Care Protocols
Standardized care pathways for common post-discharge scenarios, providing structured guidance for recovery timelines, activities, and follow-up care.

**Current documents:**
- Post-Cardiac Surgery Care Protocol (STS)
- COPD Exacerbation Post-Discharge Protocol (GOLD)
- Total Hip Replacement Recovery Protocol (AAOS)

## Document Schema

Each knowledge document follows this JSON schema:

```json
{
  "documentId": "unique-identifier",
  "source": {
    "name": "Source Organization",
    "url": "https://source-url.org",
    "authority": "ACRONYM",
    "publicationDate": "YYYY-MM-DD"
  },
  "domain": "medical-domain",
  "title": "Document Title",
  "content": "Full text content...",
  "metadata": {
    "version": "version-number",
    "keywords": ["keyword1", "keyword2"],
    "targetAudience": "patients|providers",
    ...additional metadata
  },
  "lastUpdated": "ISO-8601-timestamp",
  "validationStatus": "validated|pending_review|outdated",
  "citationFormat": {
    "apa": "APA citation format",
    "shortForm": "Short citation"
  }
}
```

## Validation Status

Documents can have one of three validation statuses:
- **validated**: Reviewed and approved for use in the system
- **pending_review**: Awaiting clinical review and validation
- **outdated**: Requires update due to age or new guidelines

## Adding New Documents

When adding new documents to the knowledge base:

1. Follow the JSON schema structure
2. Use authoritative medical sources only
3. Include complete citation information
4. Set appropriate validation status
5. Use clear, descriptive document IDs
6. Add relevant keywords for searchability
7. Specify the target audience
8. Include the medical domain

## Medical Domains

Supported medical domains include:
- cardiology
- endocrinology
- pulmonology
- orthopedics
- surgery
- hematology
- general (cross-cutting topics)

## Source Authority

All documents must come from recognized authoritative sources such as:
- Government health agencies (CDC, NIH, FDA)
- Professional medical societies (AHA, ADA, AAOS)
- Evidence-based guideline organizations
- Peer-reviewed medical literature

## Maintenance

The knowledge base should be regularly reviewed and updated:
- Documents older than 365 days should be reviewed for currency
- New clinical guidelines should be incorporated promptly
- Outdated information should be flagged and updated
- The KnowledgeBaseManager provides methods to identify outdated documents

## Usage in RAG System

These documents are used by the RAG (Retrieval-Augmented Generation) system to:
1. Retrieve relevant medical context for patient queries
2. Ground AI-generated responses in evidence-based sources
3. Provide citations and source attribution
4. Ensure medical accuracy and safety

The RAG system's Document Retriever uses semantic search to find relevant documents, the Re-ranker scores them by relevance, and the Citation Generator ensures proper attribution in responses.
