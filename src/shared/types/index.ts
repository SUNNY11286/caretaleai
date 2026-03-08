/**
 * Core Data Models and Interfaces
 * Central export point for all CARETALE AI data models
 */

// Patient Profile exports
export {
  PatientProfile,
  Demographics,
  AccessibilitySettings,
  LanguageSettings,
  CommunicationPreferences,
  HealthLiteracyLevel,
} from './patient-profile';

// Care Context exports
export {
  CareContext,
  CareInstruction,
  Medication,
  Appointment,
  CareTeamMember,
  Contact,
} from './care-context';

// Interaction Record exports
export {
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
} from './interaction-record';

// Knowledge Document exports
export {
  KnowledgeDocument,
  AuthoritySource,
  DocumentMetadata,
  CitationInfo,
  MedicalDomain,
  ValidationStatus,
} from './knowledge-document';
