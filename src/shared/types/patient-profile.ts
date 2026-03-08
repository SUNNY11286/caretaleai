/**
 * Patient Profile Data Model
 * Represents comprehensive patient information including demographics,
 * accessibility needs, and care context.
 */

export enum HealthLiteracyLevel {
  BASIC = 'basic',
  INTERMEDIATE = 'intermediate',
  ADVANCED = 'advanced',
}

export interface Demographics {
  age: number;
  gender?: string;
  preferredName?: string;
}

export interface AccessibilitySettings {
  screenReaderEnabled: boolean;
  highContrastMode: boolean;
  fontSize: 'small' | 'medium' | 'large' | 'extra-large';
  voiceOutputEnabled: boolean;
  keyboardNavigationOnly: boolean;
}

export interface LanguageSettings {
  primaryLanguage: string;
  secondaryLanguages?: string[];
  translationEnabled: boolean;
}

export interface CommunicationPreferences {
  preferredInputMode: 'text' | 'voice' | 'mixed';
  preferredOutputMode: 'text' | 'audio' | 'visual' | 'mixed';
  notificationPreferences: {
    email: boolean;
    sms: boolean;
    push: boolean;
  };
  reminderFrequency: 'low' | 'medium' | 'high';
}

export interface PatientProfile {
  patientId: string;
  demographics: Demographics;
  accessibilityNeeds: AccessibilitySettings;
  languagePreferences: LanguageSettings;
  healthLiteracyLevel: HealthLiteracyLevel;
  communicationPreferences: CommunicationPreferences;
  careContext: CareContext;
}

// Forward declaration - CareContext is defined in care-context.ts
export interface CareContext {
  dischargeDate: Date;
  dischargeDiagnosis: string[];
  careInstructions: CareInstruction[];
  medications: Medication[];
  followUpAppointments: Appointment[];
  careTeam: CareTeamMember[];
  emergencyContacts: Contact[];
}

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
