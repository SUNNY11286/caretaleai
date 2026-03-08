/**
 * Citation Generator Component
 * Implements transparent source attribution for all medical information.
 */

import { KnowledgeDocument } from '../shared/types/knowledge-document';
import { Citation, GroundedResponse, ValidationResult } from './types';

export class CitationGenerator {
  generateCitations(
    responseText: string,
    sourceDocuments: KnowledgeDocument[],
    citationStyle: string = 'APA'
  ): Citation[] {
    return sourceDocuments.map((doc) => this.createCitation(doc, responseText, citationStyle));
  }

  createGroundedResponse(
    responseText: string,
    sourceDocuments: KnowledgeDocument[],
    includeInlineCitations: boolean = true
  ): GroundedResponse {
    const citations = this.generateCitations(responseText, sourceDocuments);

    let finalText = responseText;
    if (includeInlineCitations) {
      finalText = this.addInlineCitations(responseText, citations);
    }

    return {
      responseText: finalText,
      citations,
      sourceDocuments,
    };
  }

  private createCitation(
    document: KnowledgeDocument,
    responseText: string,
    citationStyle: string
  ): Citation {
    let citationText: string;

    if (citationStyle === 'APA') {
      citationText = this.formatAPA(document);
    } else if (citationStyle === 'Vancouver') {
      citationText = this.formatVancouver(document);
    } else {
      citationText = this.formatSimple(document);
    }

    const snippet = this.extractSnippet(document.content, responseText);

    return {
      citationText,
      documentId: document.documentId,
      sourceName: document.source.organizationName,
      url: document.citationFormat.url || document.source.url,
      snippet,
    };
  }

  private formatAPA(document: KnowledgeDocument): string {
    const year = document.metadata.publicationDate.getFullYear();

    const title = document.metadata.title;
    const org = document.source.organizationName;
    const url = document.citationFormat.url || document.source.url || '';

    let citation = `${org}. (${year}). ${title}.`;
    if (url) {
      citation += ` Retrieved from ${url}`;
    }

    return citation;
  }

  private formatVancouver(document: KnowledgeDocument): string {
    const org = document.source.organizationName;
    const title = document.metadata.title;
    const year = document.metadata.publicationDate.getFullYear();

    return `${org}. ${title}. ${year}.`;
  }

  private formatSimple(document: KnowledgeDocument): string {
    return `${document.metadata.title} - ${document.source.organizationName}`;
  }

  private extractSnippet(documentContent: string, responseText: string, maxLength: number = 200): string {
    let snippet = documentContent.substring(0, maxLength);
    if (documentContent.length > maxLength) {
      snippet += '...';
    }
    return snippet;
  }

  private addInlineCitations(responseText: string, citations: Citation[]): string {
    if (citations.length === 0) {
      return responseText;
    }

    let citationSection = '\n\nSources:\n';
    citations.forEach((citation, i) => {
      citationSection += `[${i + 1}] ${citation.citationText}\n`;
    });

    return responseText + citationSection;
  }

  validateCitations(groundedResponse: GroundedResponse): ValidationResult {
    const hasCitations = groundedResponse.citations.length > 0;
    const allDocumentsCited =
      groundedResponse.citations.length === groundedResponse.sourceDocuments.length;
    const allCitationsHaveSources = groundedResponse.citations.every(
      (citation) => citation.sourceName && citation.citationText
    );

    const sourceDocIds = new Set(groundedResponse.sourceDocuments.map((doc) => doc.documentId));
    const allCitationsTraceable = groundedResponse.citations.every((citation) =>
      sourceDocIds.has(citation.documentId)
    );

    const valid =
      hasCitations && allDocumentsCited && allCitationsHaveSources && allCitationsTraceable;

    return {
      hasCitations,
      allDocumentsCited,
      allCitationsHaveSources,
      allCitationsTraceable,
      valid,
    };
  }
}
