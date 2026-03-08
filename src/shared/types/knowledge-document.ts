/**
 * Knowledge Document Data Model
 * Represents a document in the knowledge base with metadata,
 * source information, and validation status.
 */

export enum MedicalDomain {
  CARDIOLOGY = 'cardiology',
  NEUROLOGY = 'neurology',
  ORTHOPEDICS = 'orthopedics',
  GENERAL_MEDICINE = 'general_medicine',
  SURGERY = 'surgery',
  PEDIATRICS = 'pediatrics',
  GERIATRICS = 'geriatrics',
  PHARMACY = 'pharmacy',
  NURSING = 'nursing',
  REHABILITATION = 'rehabilitation',
  MENTAL_HEALTH = 'mental_health',
  OTHER = 'other',
}

export enum ValidationStatus {
  VALIDATED = 'validated',
  PENDING_REVIEW = 'pending_review',
  OUTDATED = 'outdated',
  DEPRECATED = 'deprecated',
}

export interface AuthoritySource {
  organizationName: string;
  organizationType: 'government' | 'professional_association' | 'academic' | 'healthcare_system';
  url?: string;
  credibilityScore: number;
}

export interface DocumentMetadata {
  title: string;
  authors?: string[];
  publicationDate: Date;
  version?: string;
  keywords: string[];
  abstract?: string;
  language: string;
  documentType: 'guideline' | 'protocol' | 'educational' | 'research' | 'reference';
}

export interface CitationInfo {
  citationText: string;
  citationStyle: 'APA' | 'MLA' | 'Chicago' | 'Vancouver';
  doi?: string;
  url?: string;
}

export interface KnowledgeDocument {
  documentId: string;
  source: AuthoritySource;
  domain: MedicalDomain;
  content: string;
  metadata: DocumentMetadata;
  lastUpdated: Date;
  validationStatus: ValidationStatus;
  citationFormat: CitationInfo;
}
