"""
Patient Profile Data Model
Represents comprehensive patient information including demographics,
accessibility needs, and care context.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field


class HealthLiteracyLevel(str, Enum):
    """Health literacy level of the patient"""
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class Demographics(BaseModel):
    """Patient demographic information"""
    age: int = Field(..., ge=0, le=150)
    gender: Optional[str] = None
    preferred_name: Optional[str] = None


class AccessibilitySettings(BaseModel):
    """Accessibility preferences and requirements"""
    screen_reader_enabled: bool = False
    high_contrast_mode: bool = False
    font_size: str = Field(default="medium", pattern="^(small|medium|large|extra-large)$")
    voice_output_enabled: bool = False
    keyboard_navigation_only: bool = False


class LanguageSettings(BaseModel):
    """Language preferences for patient communication"""
    primary_language: str
    secondary_languages: Optional[List[str]] = None
    translation_enabled: bool = False


class NotificationPreferences(BaseModel):
    """Notification channel preferences"""
    email: bool = False
    sms: bool = False
    push: bool = False


class CommunicationPreferences(BaseModel):
    """Patient communication preferences"""
    preferred_input_mode: str = Field(default="text", pattern="^(text|voice|mixed)$")
    preferred_output_mode: str = Field(default="text", pattern="^(text|audio|visual|mixed)$")
    notification_preferences: NotificationPreferences
    reminder_frequency: str = Field(default="medium", pattern="^(low|medium|high)$")


class PatientProfile(BaseModel):
    """Complete patient profile with all relevant information"""
    patient_id: str
    demographics: Demographics
    accessibility_needs: AccessibilitySettings
    language_preferences: LanguageSettings
    health_literacy_level: HealthLiteracyLevel
    communication_preferences: CommunicationPreferences
    # care_context is defined in care_context.py to avoid circular imports
