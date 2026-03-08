"""
Unit tests for core data models
Tests basic instantiation and validation of data models
"""

from datetime import datetime
import pytest
from pydantic import ValidationError

from src.models import (
    PatientProfile,
    Demographics,
    AccessibilitySettings,
    LanguageSettings,
    CommunicationPreferences,
    NotificationPreferences,
    HealthLiteracyLevel,
    CareContext,
    CareInstruction,
    Medication,
    Appointment,
    CareTeamMember,
    Contact,
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
    KnowledgeDocument,
    AuthoritySource,
    DocumentMetadata,
    CitationInfo,
    MedicalDomain,
    ValidationStatus,
)


class TestPatientProfile:
    """Tests for PatientProfile model"""

    def test_create_valid_patient_profile(self):
        """Test creating a valid patient profile"""
        profile = PatientProfile(
            patient_id="P12345",
            demographics=Demographics(
                age=65,
                gender="female",
                preferred_name="Jane"
            ),
            accessibility_needs=AccessibilitySettings(
                screen_reader_enabled=True,
                high_contrast_mode=False,
                font_size="large",
                voice_output_enabled=True,
                keyboard_navigation_only=False
            ),
            language_preferences=LanguageSettings(
                primary_language="en",
                secondary_languages=["es"],
                translation_enabled=True
            ),
            health_literacy_level=HealthLiteracyLevel.INTERMEDIATE,
            communication_preferences=CommunicationPreferences(
                preferred_input_mode="voice",
                preferred_output_mode="audio",
                notification_preferences=NotificationPreferences(
                    email=True,
                    sms=True,
                    push=False
                ),
                reminder_frequency="medium"
            )
        )

        assert profile.patient_id == "P12345"
        assert profile.demographics.age == 65
        assert profile.health_literacy_level == HealthLiteracyLevel.INTERMEDIATE

    def test_invalid_age(self):
        """Test that invalid age raises validation error"""
        with pytest.raises(ValidationError):
            Demographics(age=200)  # Age > 150


class TestCareContext:
    """Tests for CareContext model"""

    def test_create_valid_care_context(self):
        """Test creating a valid care context"""
        care_context = CareContext(
            discharge_date=datetime(2024, 1, 15),
            discharge_diagnosis=["Pneumonia", "Dehydration"],
            care_instructions=[
                CareInstruction(
                    instruction_id="I001",
                    category="medication",
                    description="Take antibiotics as prescribed",
                    priority="high",
                    frequency="twice daily",
                    duration="10 days"
                )
            ],
            medications=[
                Medication(
                    medication_id="M001",
                    name="Amoxicillin",
                    dosage="500mg",
                    frequency="twice daily",
                    route="oral",
                    purpose="Treat bacterial infection",
                    start_date=datetime(2024, 1, 15),
                    instructions="Take with food",
                    side_effects=["nausea", "diarrhea"]
                )
            ],
            follow_up_appointments=[
                Appointment(
                    appointment_id="A001",
                    provider="Dr. Smith",
                    specialty="Primary Care",
                    date=datetime(2024, 1, 22),
                    location="Main Clinic",
                    purpose="Follow-up check"
                )
            ],
            care_team=[
                CareTeamMember(
                    member_id="CT001",
                    name="Dr. Smith",
                    role="Primary Care Physician",
                    contact_info=Contact(
                        name="Dr. Smith",
                        phone="555-0100",
                        email="dr.smith@clinic.com",
                        preferred_contact_method="email"
                    )
                )
            ],
            emergency_contacts=[
                Contact(
                    name="John Doe",
                    relationship="spouse",
                    phone="555-0200",
                    preferred_contact_method="phone"
                )
            ]
        )

        assert len(care_context.discharge_diagnosis) == 2
        assert care_context.medications[0].name == "Amoxicillin"
        assert care_context.care_team[0].role == "Primary Care Physician"


class TestInteractionRecord:
    """Tests for InteractionRecord model"""

    def test_create_valid_interaction_record(self):
        """Test creating a valid interaction record"""
        record = InteractionRecord(
            interaction_id="INT001",
            patient_id="P12345",
            timestamp=datetime(2024, 1, 16, 10, 30, 0),
            input_type=InputType.TEXT,
            input_content="When should I take my medication?",
            processed_request=NormalizedRequest(
                request_id="REQ001",
                patient_id="P12345",
                original_input="When should I take my medication?",
                input_type=InputType.TEXT,
                intent="medication_timing",
                entities={"medication": "Amoxicillin"},
                context={},
                timestamp=datetime(2024, 1, 16, 10, 30, 0)
            ),
            pipeline_routing=[
                PipelineRoute(
                    pipeline_id="MCP001",
                    pipeline_name="Medication Clarification Pipeline",
                    routing_reason="Medication-related query detected",
                    priority=1,
                    timestamp=datetime(2024, 1, 16, 10, 30, 1)
                )
            ],
            responses=[
                PipelineResponse(
                    pipeline_id="MCP001",
                    pipeline_name="Medication Clarification Pipeline",
                    response_content="Take Amoxicillin twice daily with food",
                    confidence=0.95,
                    sources=["Discharge Instructions"],
                    processing_time=0.5,
                    timestamp=datetime(2024, 1, 16, 10, 30, 2)
                )
            ],
            final_output=FormattedResponse(
                response_id="RESP001",
                content="Take Amoxicillin twice daily with food",
                format=OutputFormat.TEXT,
                accessibility_features=["screen-reader-compatible"],
                timestamp=datetime(2024, 1, 16, 10, 30, 3)
            ),
            safety_checks=[
                SafetyCheckResult(
                    check_type=SafetyCheckType.SCOPE_BOUNDARY,
                    status=SafetyCheckStatus.PASSED,
                    details="Response within medical scope",
                    risk_score=0.1,
                    timestamp=datetime(2024, 1, 16, 10, 30, 2)
                )
            ],
            quality_metrics=QualityMetrics(
                response_time=3.0,
                confidence_score=0.95,
                clarification_needed=False,
                escalated_to_care_team=False
            )
        )

        assert record.interaction_id == "INT001"
        assert record.input_type == InputType.TEXT
        assert len(record.responses) == 1
        assert record.safety_checks[0].status == SafetyCheckStatus.PASSED

    def test_invalid_confidence_score(self):
        """Test that invalid confidence score raises validation error"""
        with pytest.raises(ValidationError):
            PipelineResponse(
                pipeline_id="MCP001",
                pipeline_name="Test Pipeline",
                response_content="Test content",
                confidence=1.5,  # Invalid: > 1.0
                processing_time=0.5,
                timestamp=datetime.now()
            )


class TestKnowledgeDocument:
    """Tests for KnowledgeDocument model"""

    def test_create_valid_knowledge_document(self):
        """Test creating a valid knowledge document"""
        document = KnowledgeDocument(
            document_id="DOC001",
            source=AuthoritySource(
                organization_name="American Heart Association",
                organization_type="professional_association",
                url="https://www.heart.org",
                credibility_score=0.95
            ),
            domain=MedicalDomain.CARDIOLOGY,
            content="Heart failure management guidelines...",
            metadata=DocumentMetadata(
                title="Heart Failure Management Guidelines",
                authors=["Dr. Johnson", "Dr. Williams"],
                publication_date=datetime(2023, 1, 1),
                version="2.0",
                keywords=["heart failure", "management", "guidelines"],
                abstract="Comprehensive guidelines for heart failure management",
                language="en",
                document_type="guideline"
            ),
            last_updated=datetime(2023, 6, 1),
            validation_status=ValidationStatus.VALIDATED,
            citation_format=CitationInfo(
                citation_text="American Heart Association. (2023). Heart Failure Management Guidelines.",
                citation_style="APA",
                url="https://www.heart.org/guidelines"
            )
        )

        assert document.document_id == "DOC001"
        assert document.domain == MedicalDomain.CARDIOLOGY
        assert document.validation_status == ValidationStatus.VALIDATED
        assert len(document.metadata.authors) == 2

    def test_invalid_credibility_score(self):
        """Test that invalid credibility score raises validation error"""
        with pytest.raises(ValidationError):
            AuthoritySource(
                organization_name="Test Org",
                organization_type="government",
                credibility_score=1.5  # Invalid: > 1.0
            )
