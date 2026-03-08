"""
Interaction Record Data Model
Represents a complete record of a patient interaction including
input, processing, routing, responses, and safety checks.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class InputType(str, Enum):
    """Type of input from patient"""
    TEXT = "text"
    VOICE = "voice"
    IMAGE = "image"


class OutputFormat(str, Enum):
    """Format of output to patient"""
    TEXT = "text"
    AUDIO = "audio"
    VISUAL = "visual"
    MIXED = "mixed"


class NormalizedRequest(BaseModel):
    """Normalized and processed patient request"""
    request_id: str
    patient_id: str
    original_input: str
    input_type: InputType
    intent: str
    entities: Dict[str, Any]
    context: Dict[str, Any]
    timestamp: datetime


class PipelineRoute(BaseModel):
    """Record of pipeline routing decision"""
    pipeline_id: str
    pipeline_name: str
    routing_reason: str
    priority: int
    timestamp: datetime


class PipelineResponse(BaseModel):
    """Response from an AI pipeline"""
    pipeline_id: str
    pipeline_name: str
    response_content: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    sources: Optional[List[str]] = None
    processing_time: float = Field(..., ge=0.0)
    timestamp: datetime


class FormattedResponse(BaseModel):
    """Final formatted response to patient"""
    response_id: str
    content: str
    format: OutputFormat
    accessibility_features: List[str]
    citations: Optional[List[str]] = None
    timestamp: datetime


class SafetyCheckType(str, Enum):
    """Type of safety check performed"""
    SCOPE_BOUNDARY = "scope_boundary"
    HALLUCINATION = "hallucination"
    EMERGENCY_DETECTION = "emergency_detection"
    CONTENT_VALIDATION = "content_validation"


class SafetyCheckStatus(str, Enum):
    """Result status of safety check"""
    PASSED = "passed"
    FLAGGED = "flagged"
    BLOCKED = "blocked"


class SafetyCheckResult(BaseModel):
    """Result of a safety check"""
    check_type: SafetyCheckType
    status: SafetyCheckStatus
    details: str
    risk_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    timestamp: datetime


class QualityMetrics(BaseModel):
    """Quality metrics for the interaction"""
    response_time: float = Field(..., ge=0.0)
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    user_satisfaction: Optional[float] = Field(None, ge=0.0, le=5.0)
    clarification_needed: bool
    escalated_to_care_team: bool


class InteractionRecord(BaseModel):
    """Complete record of a patient interaction"""
    interaction_id: str
    patient_id: str
    timestamp: datetime
    input_type: InputType
    input_content: str
    processed_request: NormalizedRequest
    pipeline_routing: List[PipelineRoute]
    responses: List[PipelineResponse]
    final_output: FormattedResponse
    safety_checks: List[SafetyCheckResult]
    quality_metrics: QualityMetrics
