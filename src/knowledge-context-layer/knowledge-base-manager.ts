/**
 * Knowledge Base Manager Component
 * Maintains curated library of approved clinical sources.
 */

import { KnowledgeDocument, MedicalDomain, ValidationStatus } from '../shared/types/knowledge-document';
import { KnowledgeBaseCategory } from './types';

export class KnowledgeBaseManager {
  private documents: Map<string, KnowledgeDocument> = new Map();
  private categories: Map<KnowledgeBaseCategory, string[]> = new Map([
    [KnowledgeBaseCategory.CLINICAL_GUIDELINES, []],
    [KnowledgeBaseCategory.EDUCATIONAL_CONTENT, []],
    [KnowledgeBaseCategory.DRUG_INFORMATION, []],
    [KnowledgeBaseCategory.CARE_PROTOCOLS, []],
  ]);

  addDocument(document: KnowledgeDocument, category: KnowledgeBaseCategory): boolean {
    if (this.documents.has(document.documentId)) {
      return false;
    }

    this.documents.set(document.documentId, document);
    const categoryDocs = this.categories.get(category) ?? [];
    categoryDocs.push(document.documentId);
    this.categories.set(category, categoryDocs);

    return true;
  }

  getDocument(documentId: string): KnowledgeDocument | undefined {
    return this.documents.get(documentId);
  }

  getDocumentsByCategory(category: KnowledgeBaseCategory): KnowledgeDocument[] {
    const docIds = this.categories.get(category) ?? [];
    return docIds.map((id) => this.documents.get(id)).filter((doc): doc is KnowledgeDocument => doc !== undefined);
  }

  getDocumentsByDomain(domain: MedicalDomain): KnowledgeDocument[] {
    return Array.from(this.documents.values()).filter((doc) => doc.domain === domain);
  }

  getValidatedDocuments(): KnowledgeDocument[] {
    return Array.from(this.documents.values()).filter(
      (doc) => doc.validationStatus === ValidationStatus.VALIDATED
    );
  }

  updateDocumentStatus(documentId: string, newStatus: ValidationStatus): boolean {
    const document = this.documents.get(documentId);

    if (!document) {
      return false;
    }

    document.validationStatus = newStatus;
    return true;
  }

  removeDocument(documentId: string): boolean {
    if (!this.documents.has(documentId)) {
      return false;
    }

    // Remove from categories
    for (const [, docIds] of this.categories) {
      const index = docIds.indexOf(documentId);
      if (index !== -1) {
        docIds.splice(index, 1);
      }
    }

    this.documents.delete(documentId);
    return true;
  }

  getOutdatedDocuments(daysThreshold: number = 365): KnowledgeDocument[] {
    const now = new Date();
    const outdated: KnowledgeDocument[] = [];

    for (const doc of this.documents.values()) {
      const ageDays = (now.getTime() - doc.lastUpdated.getTime()) / (1000 * 60 * 60 * 24);
      if (ageDays > daysThreshold) {
        outdated.push(doc);
      }
    }

    return outdated;
  }

  getAllDocuments(): KnowledgeDocument[] {
    return Array.from(this.documents.values());
  }

  getStatistics(): Record<string, number> {
    const stats: Record<string, number> = {
      total_documents: this.documents.size,
      validated: 0,
      pending_review: 0,
      outdated: 0,
    };

    for (const doc of this.documents.values()) {
      if (doc.validationStatus === ValidationStatus.VALIDATED) {
        stats.validated++;
      } else if (doc.validationStatus === ValidationStatus.PENDING_REVIEW) {
        stats.pending_review++;
      } else if (doc.validationStatus === ValidationStatus.OUTDATED) {
        stats.outdated++;
      }
    }

    // Add category counts
    for (const [category, docIds] of this.categories) {
      stats[`category_${category}`] = docIds.length;
    }

    return stats;
  }
}
