/**
 * Unit tests for core data models
 * Tests basic instantiation and validation of data models
 */

import {
  PatientProfile,
  CareContext,
  InteractionRecord,
  KnowledgeDocument,
  HealthLiteracyLevel,
  InputType,
  OutputFormat,
  SafetyCheckType,
  SafetyCheckStatus,
  MedicalDomain,
  ValidationStatus,
} from '../index';

describe('Data Models', () => {
  describe('PatientProfile', () => {
    it('should create a valid patient profile', () => {
      const profile: PatientProfile = {
        patientId: 'P12345',
        demographics: {
          age: 65,
          gender: 'female',
          preferredName: 'Jane',
        },
        accessibilityNeeds: {
          screenReaderEnabled: true,
          highContrastMode: false,
          fontSize: 'large',
          voiceOutputEnabled: true,
          keyboardNavigationOnly: false,
        },
        languagePreferences: {
          primaryLanguage: 'en',
          secondaryLanguages: ['es'],
          translationEnabled: true,
        },
        healthLiteracyLevel: HealthLiteracyLevel.INTERMEDIATE,
        communicationPreferences: {
          preferredInputMode: 'voice',
          preferredOutputMode: 'audio',
          notificationPreferences: {
            email: true,
            sms: true,
            push: false,
          },
          reminderFrequency: 'medium',
        },
        careContext: {
          dischargeDate: new Date('2024-01-15'),
          dischargeDiagnosis: ['Heart Failure'],
          careInstructions: [],
          medications: [],
          followUpAppointments: [],
          careTeam: [],
          emergencyContacts: [],
        },
      };

      expect(profile.patientId).toBe('P12345');
      expect(profile.demographics.age).toBe(65);
      expect(profile.healthLiteracyLevel).toBe(HealthLiteracyLevel.INTERMEDIATE);
    });
  });

  describe('CareContext', () => {
    it('should create a valid care context', () => {
      const careContext: CareContext = {
        dischargeDate: new Date('2024-01-15'),
        dischargeDiagnosis: ['Pneumonia', 'Dehydration'],
        careInstructions: [
          {
            instructionId: 'I001',
            category: 'medication',
            description: 'Take antibiotics as prescribed',
            priority: 'high',
            frequency: 'twice daily',
            duration: '10 days',
          },
        ],
        medications: [
          {
            medicationId: 'M001',
            name: 'Amoxicillin',
            dosage: '500mg',
            frequency: 'twice daily',
            route: 'oral',
            purpose: 'Treat bacterial infection',
            startDate: new Date('2024-01-15'),
            instructions: 'Take with food',
            sideEffects: ['nausea', 'diarrhea'],
          },
        ],
        followUpAppointments: [
          {
            appointmentId: 'A001',
            provider: 'Dr. Smith',
            specialty: 'Primary Care',
            date: new Date('2024-01-22'),
            location: 'Main Clinic',
            purpose: 'Follow-up check',
          },
        ],
        careTeam: [
          {
            memberId: 'CT001',
            name: 'Dr. Smith',
            role: 'Primary Care Physician',
            contactInfo: {
              name: 'Dr. Smith',
              phone: '555-0100',
              email: 'dr.smith@clinic.com',
              preferredContactMethod: 'email',
            },
          },
        ],
        emergencyContacts: [
          {
            name: 'John Doe',
            relationship: 'spouse',
            phone: '555-0200',
            preferredContactMethod: 'phone',
          },
        ],
      };

      expect(careContext.dischargeDiagnosis).toHaveLength(2);
      expect(careContext.medications[0].name).toBe('Amoxicillin');
      expect(careContext.careTeam[0].role).toBe('Primary Care Physician');
    });
  });

  describe('InteractionRecord', () => {
    it('should create a valid interaction record', () => {
      const record: InteractionRecord = {
        interactionId: 'INT001',
        patientId: 'P12345',
        timestamp: new Date('2024-01-16T10:30:00'),
        inputType: InputType.TEXT,
        inputContent: 'When should I take my medication?',
        processedRequest: {
          requestId: 'REQ001',
          patientId: 'P12345',
          originalInput: 'When should I take my medication?',
          inputType: InputType.TEXT,
          intent: 'medication_timing',
          entities: { medication: 'Amoxicillin' },
          context: {},
          timestamp: new Date('2024-01-16T10:30:00'),
        },
        pipelineRouting: [
          {
            pipelineId: 'MCP001',
            pipelineName: 'Medication Clarification Pipeline',
            routingReason: 'Medication-related query detected',
            priority: 1,
            timestamp: new Date('2024-01-16T10:30:01'),
          },
        ],
        responses: [
          {
            pipelineId: 'MCP001',
            pipelineName: 'Medication Clarification Pipeline',
            responseContent: 'Take Amoxicillin twice daily with food',
            confidence: 0.95,
            sources: ['Discharge Instructions'],
            processingTime: 0.5,
            timestamp: new Date('2024-01-16T10:30:02'),
          },
        ],
        finalOutput: {
          responseId: 'RESP001',
          content: 'Take Amoxicillin twice daily with food',
          format: OutputFormat.TEXT,
          accessibilityFeatures: ['screen-reader-compatible'],
          timestamp: new Date('2024-01-16T10:30:03'),
        },
        safetyChecks: [
          {
            checkType: SafetyCheckType.SCOPE_BOUNDARY,
            status: SafetyCheckStatus.PASSED,
            details: 'Response within medical scope',
            riskScore: 0.1,
            timestamp: new Date('2024-01-16T10:30:02'),
          },
        ],
        qualityMetrics: {
          responseTime: 3.0,
          confidenceScore: 0.95,
          clarificationNeeded: false,
          escalatedToCareTeam: false,
        },
      };

      expect(record.interactionId).toBe('INT001');
      expect(record.inputType).toBe(InputType.TEXT);
      expect(record.responses).toHaveLength(1);
      expect(record.safetyChecks[0].status).toBe(SafetyCheckStatus.PASSED);
    });
  });

  describe('KnowledgeDocument', () => {
    it('should create a valid knowledge document', () => {
      const document: KnowledgeDocument = {
        documentId: 'DOC001',
        source: {
          organizationName: 'American Heart Association',
          organizationType: 'professional_association',
          url: 'https://www.heart.org',
          credibilityScore: 0.95,
        },
        domain: MedicalDomain.CARDIOLOGY,
        content: 'Heart failure management guidelines...',
        metadata: {
          title: 'Heart Failure Management Guidelines',
          authors: ['Dr. Johnson', 'Dr. Williams'],
          publicationDate: new Date('2023-01-01'),
          version: '2.0',
          keywords: ['heart failure', 'management', 'guidelines'],
          abstract: 'Comprehensive guidelines for heart failure management',
          language: 'en',
          documentType: 'guideline',
        },
        lastUpdated: new Date('2023-06-01'),
        validationStatus: ValidationStatus.VALIDATED,
        citationFormat: {
          citationText: 'American Heart Association. (2023). Heart Failure Management Guidelines.',
          citationStyle: 'APA',
          url: 'https://www.heart.org/guidelines',
        },
      };

      expect(document.documentId).toBe('DOC001');
      expect(document.domain).toBe(MedicalDomain.CARDIOLOGY);
      expect(document.validationStatus).toBe(ValidationStatus.VALIDATED);
      expect(document.metadata.authors).toHaveLength(2);
    });
  });
});
