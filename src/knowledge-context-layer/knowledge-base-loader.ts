/**
 * Knowledge Base Loader Utility
 * Loads knowledge documents from JSON files into the Knowledge Base Manager
 */

import * as fs from 'fs';
import * as path from 'path';
import { KnowledgeBaseManager } from './knowledge-base-manager';
import { KnowledgeDocument, ValidationStatus, MedicalDomain } from '../shared/types/knowledge-document';
import { KnowledgeBaseCategory } from './types';

interface DocumentSource {
  name: string;
  url: string;
  authority: string;
  publicationDate: string;
}

interface DocumentMetadata {
  version: string;
  keywords: string[];
  targetAudience: string;
  [key: string]: any;
}

interface CitationFormat {
  apa: string;
  shortForm: string;
}

interface JsonDocument {
  documentId: string;
  source: DocumentSource;
  domain: string;
  title: string;
  content: string;
  metadata: DocumentMetadata;
  lastUpdated: string;
  validationStatus: string;
  citationFormat: CitationFormat;
}

export class KnowledgeBaseLoader {
  private manager: KnowledgeBaseManager;
  private dataPath: string;

  constructor(manager: KnowledgeBaseManager, dataPath: string = 'data/knowledge-base') {
    this.manager = manager;
    this.dataPath = dataPath;
  }

  /**
   * Load all documents from the knowledge base directory
   */
  loadAll(): { loaded: number; failed: number; errors: string[] } {
    const results = {
      loaded: 0,
      failed: 0,
      errors: [] as string[],
    };

    const categories = [
      { dir: 'clinical-guidelines', category: KnowledgeBaseCategory.CLINICAL_GUIDELINES },
      { dir: 'educational-content', category: KnowledgeBaseCategory.EDUCATIONAL_CONTENT },
      { dir: 'drug-information', category: KnowledgeBaseCategory.DRUG_INFORMATION },
      { dir: 'care-protocols', category: KnowledgeBaseCategory.CARE_PROTOCOLS },
    ];

    for (const { dir, category } of categories) {
      const categoryPath = path.join(this.dataPath, dir);
      
      if (!fs.existsSync(categoryPath)) {
        results.errors.push(`Directory not found: ${categoryPath}`);
        continue;
      }

      const files = fs.readdirSync(categoryPath).filter((f) => f.endsWith('.json'));

      for (const file of files) {
        const filePath = path.join(categoryPath, file);
        try {
          const result = this.loadDocument(filePath, category);
          if (result.success) {
            results.loaded++;
          } else {
            results.failed++;
            results.errors.push(`${file}: ${result.error}`);
          }
        } catch (error) {
          results.failed++;
          results.errors.push(`${file}: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
      }
    }

    return results;
  }

  /**
   * Load a single document from a JSON file
   */
  loadDocument(
    filePath: string,
    category: KnowledgeBaseCategory
  ): { success: boolean; error?: string } {
    try {
      const fileContent = fs.readFileSync(filePath, 'utf-8');
      const jsonDoc: JsonDocument = JSON.parse(fileContent);

      // Convert JSON document to KnowledgeDocument
      const document: KnowledgeDocument = {
        documentId: jsonDoc.documentId,
        source: {
          name: jsonDoc.source.name,
          url: jsonDoc.source.url,
          authority: jsonDoc.source.authority,
          publicationDate: new Date(jsonDoc.source.publicationDate),
        },
        domain: jsonDoc.domain as MedicalDomain,
        content: jsonDoc.content,
        metadata: {
          title: jsonDoc.title,
          version: jsonDoc.metadata.version,
          keywords: jsonDoc.metadata.keywords,
          ...jsonDoc.metadata,
        },
        lastUpdated: new Date(jsonDoc.lastUpdated),
        validationStatus: this.parseValidationStatus(jsonDoc.validationStatus),
        citationFormat: jsonDoc.citationFormat,
      };

      const added = this.manager.addDocument(document, category);

      if (!added) {
        return { success: false, error: 'Document already exists or could not be added' };
      }

      return { success: true };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }

  /**
   * Load documents from a specific category
   */
  loadCategory(category: KnowledgeBaseCategory): { loaded: number; failed: number; errors: string[] } {
    const results = {
      loaded: 0,
      failed: 0,
      errors: [] as string[],
    };

    const categoryDirs: Record<KnowledgeBaseCategory, string> = {
      [KnowledgeBaseCategory.CLINICAL_GUIDELINES]: 'clinical-guidelines',
      [KnowledgeBaseCategory.EDUCATIONAL_CONTENT]: 'educational-content',
      [KnowledgeBaseCategory.DRUG_INFORMATION]: 'drug-information',
      [KnowledgeBaseCategory.CARE_PROTOCOLS]: 'care-protocols',
    };

    const categoryPath = path.join(this.dataPath, categoryDirs[category]);

    if (!fs.existsSync(categoryPath)) {
      results.errors.push(`Directory not found: ${categoryPath}`);
      return results;
    }

    const files = fs.readdirSync(categoryPath).filter((f) => f.endsWith('.json'));

    for (const file of files) {
      const filePath = path.join(categoryPath, file);
      try {
        const result = this.loadDocument(filePath, category);
        if (result.success) {
          results.loaded++;
        } else {
          results.failed++;
          results.errors.push(`${file}: ${result.error}`);
        }
      } catch (error) {
        results.failed++;
        results.errors.push(`${file}: ${error instanceof Error ? error.message : 'Unknown error'}`);
      }
    }

    return results;
  }

  private parseValidationStatus(status: string): ValidationStatus {
    switch (status.toLowerCase()) {
      case 'validated':
        return ValidationStatus.VALIDATED;
      case 'pending_review':
        return ValidationStatus.PENDING_REVIEW;
      case 'outdated':
        return ValidationStatus.OUTDATED;
      default:
        return ValidationStatus.PENDING_REVIEW;
    }
  }
}

/**
 * Convenience function to create and load a knowledge base
 */
export function createAndLoadKnowledgeBase(dataPath?: string): KnowledgeBaseManager {
  const manager = new KnowledgeBaseManager();
  const loader = new KnowledgeBaseLoader(manager, dataPath);
  const results = loader.loadAll();

  console.log(`Knowledge Base loaded: ${results.loaded} documents loaded, ${results.failed} failed`);
  
  if (results.errors.length > 0) {
    console.error('Errors during loading:');
    results.errors.forEach((error) => console.error(`  - ${error}`));
  }

  return manager;
}
