/**
 * RAG System - Main Interface
 * Integrates all RAG components for evidence-based medical context retrieval.
 */

import { KnowledgeDocument, MedicalDomain } from '../shared/types/knowledge-document';
import { DocumentRetriever } from './document-retriever';
import { Reranker } from './reranker';
import { CitationGenerator } from './citation-generator';
import { KnowledgeBaseManager } from './knowledge-base-manager';
import {
  RetrievalConfig,
  RerankingConfig,
  RankedDocument,
  GroundedResponse,
  KnowledgeBaseCategory,
  ValidationResult,
} from './types';

export class RAGSystem {
  private knowledgeBase: KnowledgeBaseManager;
  private retriever: DocumentRetriever;
  private reranker: Reranker;
  private citationGenerator: CitationGenerator;
  private retrievalConfig: RetrievalConfig;

  constructor(retrievalConfig?: Partial<RetrievalConfig>, rerankingConfig?: Partial<RerankingConfig>) {
    this.knowledgeBase = new KnowledgeBaseManager();
    this.retriever = new DocumentRetriever();
    this.reranker = new Reranker(rerankingConfig);
    this.citationGenerator = new CitationGenerator();
    this.retrievalConfig = {
      topK: retrievalConfig?.topK ?? 10,
      similarityThreshold: retrievalConfig?.similarityThreshold ?? 0.7,
      domainFilter: retrievalConfig?.domainFilter,
    };
  }

  retrieveRelevantDocs(query: string, domain?: MedicalDomain): KnowledgeDocument[] {
    const config: RetrievalConfig = {
      ...this.retrievalConfig,
      domainFilter: domain,
    };

    return this.retriever.retrieve(query, config);
  }

  rerankByRelevance(query: string, documents: KnowledgeDocument[]): RankedDocument[] {
    return this.reranker.rerank(query, documents);
  }

  generateGroundedResponse(query: string, context: RankedDocument[]): GroundedResponse {
    const sourceDocuments = context.map((ranked) => ranked.document);
    const responseText = this.generateResponseText(query, context);

    return this.citationGenerator.createGroundedResponse(responseText, sourceDocuments, true);
  }

  validateCitations(response: GroundedResponse): ValidationResult {
    return this.citationGenerator.validateCitations(response);
  }

  addKnowledge(document: KnowledgeDocument, category: KnowledgeBaseCategory): boolean {
    const success = this.knowledgeBase.addDocument(document, category);

    if (success) {
      this.retriever.addDocuments([document]);
    }

    return success;
  }

  initializeKnowledgeBase(documents: Array<[KnowledgeDocument, KnowledgeBaseCategory]>): number {
    let count = 0;
    for (const [document, category] of documents) {
      if (this.addKnowledge(document, category)) {
        count++;
      }
    }
    return count;
  }

  private generateResponseText(query: string, context: RankedDocument[]): string {
    // Placeholder implementation
    if (context.length === 0) {
      return "I don't have enough information to answer that question.";
    }

    const topDoc = context[0].document;
    const response = `Based on ${topDoc.source.organizationName} guidelines: `;
    return response + topDoc.content.substring(0, 200) + '...';
  }

  getKnowledgeBaseStats(): Record<string, number> {
    return this.knowledgeBase.getStatistics();
  }
}
