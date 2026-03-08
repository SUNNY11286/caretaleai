/**
 * Types and interfaces for the RAG System
 */

import { KnowledgeDocument, MedicalDomain } from '../shared/types/knowledge-document';

export interface RetrievalConfig {
  topK: number;
  similarityThreshold: number;
  domainFilter?: MedicalDomain;
}

export interface RerankingConfig {
  maxContextDocs: number;
  diversityWeight: number;
  recencyWeight: number;
  authorityWeight: number;
}

export interface RankedDocument {
  document: KnowledgeDocument;
  relevanceScore: number;
  rank: number;
}

export interface Citation {
  citationText: string;
  documentId: string;
  sourceName: string;
  url?: string;
  snippet: string;
}

export interface GroundedResponse {
  responseText: string;
  citations: Citation[];
  sourceDocuments: KnowledgeDocument[];
}

export enum KnowledgeBaseCategory {
  CLINICAL_GUIDELINES = 'clinical_guidelines',
  EDUCATIONAL_CONTENT = 'educational_content',
  DRUG_INFORMATION = 'drug_information',
  CARE_PROTOCOLS = 'care_protocols',
}

export interface ValidationResult {
  hasCitations: boolean;
  allDocumentsCited: boolean;
  allCitationsHaveSources: boolean;
  allCitationsTraceable: boolean;
  valid: boolean;
}
