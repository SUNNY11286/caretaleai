/**
 * Care Context Data Model
 * Represents the complete care context for a patient including
 * discharge information, medications, appointments, and care team.
 */

export interface CareInstruction {
  instructionId: string;
  category: 'medication' | 'activity' | 'diet' | 'wound-care' | 'monitoring' | 'other';
  description: string;
  priority: 'urgent' | 'high' | 'medium' | 'low';
  frequency?: string;
  duration?: string;
  startDate?: Date;
  endDate?: Date;
}

export interface Medication {
  medicationId: string;
  name: string;
  dosage: string;
  frequency: string;
  route: string;
  purpose: string;
  startDate: Date;
  endDate?: Date;
  instructions: string;
  sideEffects?: string[];
  interactions?: string[];
}

export interface Appointment {
  appointmentId: string;
  provider: string;
  specialty: string;
  date: Date;
  location: string;
  purpose: string;
  preparationInstructions?: string[];
}

export interface CareTeamMember {
  memberId: string;
  name: string;
  role: string;
  specialty?: string;
  contactInfo: Contact;
}

export interface Contact {
  name: string;
  relationship?: string;
  phone: string;
  email?: string;
  preferredContactMethod: 'phone' | 'email' | 'sms';
}

export interface CareContext {
  dischargeDate: Date;
  dischargeDiagnosis: string[];
  careInstructions: CareInstruction[];
  medications: Medication[];
  followUpAppointments: Appointment[];
  careTeam: CareTeamMember[];
  emergencyContacts: Contact[];
}
