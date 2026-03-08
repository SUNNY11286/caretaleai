/**
 * Interaction Record Data Model
 * Represents a complete record of a patient interaction including
 * input, processing, routing, responses, and safety checks.
 */

export enum InputType {
  TEXT = 'text',
  VOICE = 'voice',
  IMAGE = 'image',
}

export enum OutputFormat {
  TEXT = 'text',
  AUDIO = 'audio',
  VISUAL = 'visual',
  MIXED = 'mixed',
}

export interface NormalizedRequest {
  requestId: string;
  patientId: string;
  originalInput: string;
  inputType: InputType;
  intent: string;
  entities: Record<string, any>;
  context: Record<string, any>;
  timestamp: Date;
}

export interface PipelineRoute {
  pipelineId: string;
  pipelineName: string;
  routingReason: string;
  priority: number;
  timestamp: Date;
}

export interface PipelineResponse {
  pipelineId: string;
  pipelineName: string;
  responseContent: string;
  confidence: number;
  sources?: string[];
  processingTime: number;
  timestamp: Date;
}

export interface FormattedResponse {
  responseId: string;
  content: string;
  format: OutputFormat;
  accessibilityFeatures: string[];
  citations?: string[];
  timestamp: Date;
}

export enum SafetyCheckType {
  SCOPE_BOUNDARY = 'scope_boundary',
  HALLUCINATION = 'hallucination',
  EMERGENCY_DETECTION = 'emergency_detection',
  CONTENT_VALIDATION = 'content_validation',
}

export enum SafetyCheckStatus {
  PASSED = 'passed',
  FLAGGED = 'flagged',
  BLOCKED = 'blocked',
}

export interface SafetyCheckResult {
  checkType: SafetyCheckType;
  status: SafetyCheckStatus;
  details: string;
  riskScore?: number;
  timestamp: Date;
}

export interface QualityMetrics {
  responseTime: number;
  confidenceScore: number;
  userSatisfaction?: number;
  clarificationNeeded: boolean;
  escalatedToCareTeam: boolean;
}

export interface InteractionRecord {
  interactionId: string;
  patientId: string;
  timestamp: Date;
  inputType: InputType;
  inputContent: string;
  processedRequest: NormalizedRequest;
  pipelineRouting: PipelineRoute[];
  responses: PipelineResponse[];
  finalOutput: FormattedResponse;
  safetyChecks: SafetyCheckResult[];
  qualityMetrics: QualityMetrics;
}
