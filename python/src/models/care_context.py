"""
Care Context Data Model
Represents the complete care context for a patient including
discharge information, medications, appointments, and care team.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class CareInstruction(BaseModel):
    """Individual care instruction for the patient"""
    instruction_id: str
    category: str = Field(..., pattern="^(medication|activity|diet|wound-care|monitoring|other)$")
    description: str
    priority: str = Field(..., pattern="^(urgent|high|medium|low)$")
    frequency: Optional[str] = None
    duration: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class Medication(BaseModel):
    """Medication information"""
    medication_id: str
    name: str
    dosage: str
    frequency: str
    route: str
    purpose: str
    start_date: datetime
    end_date: Optional[datetime] = None
    instructions: str
    side_effects: Optional[List[str]] = None
    interactions: Optional[List[str]] = None


class Appointment(BaseModel):
    """Follow-up appointment information"""
    appointment_id: str
    provider: str
    specialty: str
    date: datetime
    location: str
    purpose: str
    preparation_instructions: Optional[List[str]] = None


class Contact(BaseModel):
    """Contact information"""
    name: str
    relationship: Optional[str] = None
    phone: str
    email: Optional[str] = None
    preferred_contact_method: str = Field(..., pattern="^(phone|email|sms)$")


class CareTeamMember(BaseModel):
    """Care team member information"""
    member_id: str
    name: str
    role: str
    specialty: Optional[str] = None
    contact_info: Contact


class CareContext(BaseModel):
    """Complete care context for a patient"""
    discharge_date: datetime
    discharge_diagnosis: List[str]
    care_instructions: List[CareInstruction]
    medications: List[Medication]
    follow_up_appointments: List[Appointment]
    care_team: List[CareTeamMember]
    emergency_contacts: List[Contact]
