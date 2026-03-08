/**
 * Simple validation script to test TypeScript data models
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
} from './index';

function testPatientProfile(): boolean {
  const profile: PatientProfile = {
    patientId: 'P12345',
    demographics: {
      age: 65,
      gender: 'female',
    },
    accessibilityNeeds: {
      screenReaderEnabled: false,
      highContrastMode: false,
      fontSize: 'medium',
      voiceOutputEnabled: false,
      keyboardNavigationOnly: false,
    },
    languagePreferences: {
      primaryLanguage: 'en',
      translationEnabled: false,
    },
    healthLiteracyLevel: HealthLiteracyLevel.INTERMEDIATE,
    communicationPreferences: {
      preferredInputMode: 'text',
      preferredOutputMode: 'text',
      notificationPreferences: {
        email: false,
        sms: false,
        push: false,
      },
      reminderFrequency: 'medium',
    },
    careContext: {
      dischargeDate: new Date('2024-01-15'),
      dischargeDiagnosis: ['Pneumonia'],
      careInstructions: [],
      medications: [],
      followUpAppointments: [],
      careTeam: [],
      emergencyContacts: [],
    },
  };
  console.log(`✓ PatientProfile created: ${profile.patientId}`);
  return true;
}

function testCareContext(): boolean {
  const careContext: CareContext = {
    dischargeDate: new Date('2024-01-15'),
    dischargeDiagnosis: ['Pneumonia'],
    careInstructions: [],
    medications: [],
    followUpAppointments: [],
    careTeam: [],
    emergencyContacts: [],
  };
  console.log(`✓ CareContext created with ${careContext.dischargeDiagnosis.length} diagnoses`);
  return true;
}

function testInteractionRecord(): boolean {
  const record: InteractionRecord = {
    interactionId: 'INT001',
    patientId: 'P12345',
    timestamp: new Date(),
    inputType: InputType.TEXT,
    inputContent: 'Test input',
    processedRequest: {
      requestId: 'REQ001',
      patientId: 'P12345',
      originalInput: 'Test input',
      inputType: InputType.TEXT,
      intent: 'test',
      entities: {},
      context: {},
      timestamp: new Date(),
    },
    pipelineRouting: [],
    responses: [],
    finalOutput: {
      responseId: 'RESP001',
      content: 'Test response',
      format: OutputFormat.TEXT,
      accessibilityFeatures: [],
      timestamp: new Date(),
    },
    safetyChecks: [],
    qualityMetrics: {
      responseTime: 1.0,
      confidenceScore: 0.9,
      clarificationNeeded: false,
      escalatedToCareTeam: false,
    },
  };
  console.log(`✓ InteractionRecord created: ${record.interactionId}`);
  return true;
}

function testKnowledgeDocument(): boolean {
  const document: KnowledgeDocument = {
    documentId: 'DOC001',
    source: {
      organizationName: 'Test Org',
      organizationType: 'government',
      credibilityScore: 0.95,
    },
    domain: MedicalDomain.GENERAL_MEDICINE,
    content: 'Test content',
    metadata: {
      title: 'Test Document',
      publicationDate: new Date('2023-01-01'),
      keywords: ['test'],
      language: 'en',
      documentType: 'guideline',
    },
    lastUpdated: new Date(),
    validationStatus: ValidationStatus.VALIDATED,
    citationFormat: {
      citationText: 'Test citation',
      citationStyle: 'APA',
    },
  };
  console.log(`✓ KnowledgeDocument created: ${document.documentId}`);
  return true;
}

function main() {
  console.log('Validating TypeScript data models...\n');

  const tests = [
    testPatientProfile,
    testCareContext,
    testInteractionRecord,
    testKnowledgeDocument,
  ];

  let passed = 0;
  let failed = 0;

  for (const test of tests) {
    try {
      if (test()) {
        passed++;
      }
    } catch (error) {
      console.log(`✗ ${test.name} failed:`, error);
      failed++;
    }
  }

  console.log('\n' + '='.repeat(50));
  console.log(`Results: ${passed} passed, ${failed} failed`);
  console.log('='.repeat(50));

  if (failed === 0) {
    console.log('\n✓ All TypeScript data models validated successfully!');
    process.exit(0);
  } else {
    console.log(`\n✗ ${failed} test(s) failed`);
    process.exit(1);
  }
}

main();
