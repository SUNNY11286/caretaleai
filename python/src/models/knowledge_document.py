"""
Knowledge Document Data Model
Represents a document in the knowledge base with metadata,
source information, and validation status.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field


class MedicalDomain(str, Enum):
    """Medical domain classification"""
    CARDIOLOGY = "cardiology"
    NEUROLOGY = "neurology"
    ORTHOPEDICS = "orthopedics"
    GENERAL_MEDICINE = "general_medicine"
    SURGERY = "surgery"
    PEDIATRICS = "pediatrics"
    GERIATRICS = "geriatrics"
    PHARMACY = "pharmacy"
    NURSING = "nursing"
    REHABILITATION = "rehabilitation"
    MENTAL_HEALTH = "mental_health"
    OTHER = "other"


class ValidationStatus(str, Enum):
    """Validation status of the document"""
    VALIDATED = "validated"
    PENDING_REVIEW = "pending_review"
    OUTDATED = "outdated"
    DEPRECATED = "deprecated"


class AuthoritySource(BaseModel):
    """Source authority information"""
    organization_name: str
    organization_type: str = Field(
        ..., 
        pattern="^(government|professional_association|academic|healthcare_system)$"
    )
    url: Optional[str] = None
    credibility_score: float = Field(..., ge=0.0, le=1.0)


class DocumentMetadata(BaseModel):
    """Document metadata"""
    title: str
    authors: Optional[List[str]] = None
    publication_date: datetime
    version: Optional[str] = None
    keywords: List[str]
    abstract: Optional[str] = None
    language: str
    document_type: str = Field(
        ..., 
        pattern="^(guideline|protocol|educational|research|reference)$"
    )


class CitationInfo(BaseModel):
    """Citation information for the document"""
    citation_text: str
    citation_style: str = Field(..., pattern="^(APA|MLA|Chicago|Vancouver)$")
    doi: Optional[str] = None
    url: Optional[str] = None


class KnowledgeDocument(BaseModel):
    """Complete knowledge document with all metadata"""
    document_id: str
    source: AuthoritySource
    domain: MedicalDomain
    content: str
    metadata: DocumentMetadata
    last_updated: datetime
    validation_status: ValidationStatus
    citation_format: CitationInfo
