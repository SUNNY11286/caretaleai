"""
Core Data Models and Interfaces
Central export point for all CARETALE AI data models
"""

# Patient Profile exports
from .patient_profile import (
    PatientProfile,
    Demographics,
    AccessibilitySettings,
    LanguageSettings,
    CommunicationPreferences,
    NotificationPreferences,
    HealthLiteracyLevel,
)

# Care Context exports
from .care_context import (
    CareContext,
    CareInstruction,
    Medication,
    Appointment,
    CareTeamMember,
    Contact,
)

# Interaction Record exports
from .interaction_record import (
    InteractionRecord,
    NormalizedRequest,
    PipelineRoute,
    PipelineResponse,
    FormattedResponse,
    SafetyCheckResult,
    QualityMetrics,
    InputType,
    OutputFormat,
    SafetyCheckType,
    SafetyCheckStatus,
)

# Knowledge Document exports
from .knowledge_document import (
    KnowledgeDocument,
    AuthoritySource,
    DocumentMetadata,
    CitationInfo,
    MedicalDomain,
    ValidationStatus,
)

__all__ = [
    # Patient Profile
    "PatientProfile",
    "Demographics",
    "AccessibilitySettings",
    "LanguageSettings",
    "CommunicationPreferences",
    "NotificationPreferences",
    "HealthLiteracyLevel",
    # Care Context
    "CareContext",
    "CareInstruction",
    "Medication",
    "Appointment",
    "CareTeamMember",
    "Contact",
    # Interaction Record
    "InteractionRecord",
    "NormalizedRequest",
    "PipelineRoute",
    "PipelineResponse",
    "FormattedResponse",
    "SafetyCheckResult",
    "QualityMetrics",
    "InputType",
    "OutputFormat",
    "SafetyCheckType",
    "SafetyCheckStatus",
    # Knowledge Document
    "KnowledgeDocument",
    "AuthoritySource",
    "DocumentMetadata",
    "CitationInfo",
    "MedicalDomain",
    "ValidationStatus",
]
