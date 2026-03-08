/**
 * Unit tests for RAG System components
 */

import {
  RAGSystem,
  DocumentRetriever,
  Reranker,
  CitationGenerator,
  KnowledgeBaseManager,
  KnowledgeBaseCategory,
} from '../index';
import {
  KnowledgeDocument,
  MedicalDomain,
  ValidationStatus,
} from '../../shared/types/knowledge-document';

describe('RAG System', () => {
  const createSampleDocument = (id: string = 'doc-001'): KnowledgeDocument => ({
    documentId: id,
    source: {
      organizationName: 'American Heart Association',
      organizationType: 'professional_association',
      url: 'https://www.heart.org',
      credibilityScore: 0.95,
    },
    domain: MedicalDomain.CARDIOLOGY,
    content:
      'Post-discharge care for heart failure patients includes daily weight monitoring, medication adherence, and dietary sodium restriction.',
    metadata: {
      title: 'Heart Failure Post-Discharge Guidelines',
      authors: ['Dr. Smith', 'Dr. Jones'],
      publicationDate: new Date('2023-01-15'),
      version: '2.0',
      keywords: ['heart failure', 'post-discharge', 'care management'],
      abstract: 'Guidelines for managing heart failure patients after hospital discharge.',
      language: 'en',
      documentType: 'guideline',
    },
    lastUpdated: new Date('2023-06-01'),
    validationStatus: ValidationStatus.VALIDATED,
    citationFormat: {
      citationText: 'American Heart Association. (2023). Heart Failure Post-Discharge Guidelines.',
      citationStyle: 'APA',
      doi: '10.1000/example',
      url: 'https://www.heart.org/guidelines',
    },
  });

  describe('DocumentRetriever', () => {
    it('should add documents', () => {
      const retriever = new DocumentRetriever();
      const docs = [createSampleDocument()];
      retriever.addDocuments(docs);

      const results = retriever.retrieve('heart failure');
      expect(results).toBeDefined();
    });

    it('should return empty array when no documents', () => {
      const retriever = new DocumentRetriever();
      const results = retriever.retrieve('query');
      expect(results).toEqual([]);
    });

    it('should clear documents', () => {
      const retriever = new DocumentRetriever();
      retriever.addDocuments([createSampleDocument()]);
      retriever.clear();

      const results = retriever.retrieve('query');
      expect(results).toEqual([]);
    });
  });

  describe('Reranker', () => {
    it('should rerank documents', () => {
      const reranker = new Reranker();
      const docs = [createSampleDocument('doc-1'), createSampleDocument('doc-2')];

      const ranked = reranker.rerank('query', docs);

      expect(ranked.length).toBeLessThanOrEqual(5);
      ranked.forEach((r, i) => {
        expect(r.rank).toBe(i + 1);
        expect(r.relevanceScore).toBeGreaterThanOrEqual(0);
      });
    });

    it('should return empty array for empty input', () => {
      const reranker = new Reranker();
      const ranked = reranker.rerank('query', []);
      expect(ranked).toEqual([]);
    });
  });

  describe('CitationGenerator', () => {
    it('should generate citations', () => {
      const generator = new CitationGenerator();
      const doc = createSampleDocument();

      const citations = generator.generateCitations('Response text', [doc]);

      expect(citations).toHaveLength(1);
      expect(citations[0].documentId).toBe(doc.documentId);
      expect(citations[0].sourceName).toBe(doc.source.organizationName);
    });

    it('should create grounded response', () => {
      const generator = new CitationGenerator();
      const doc = createSampleDocument();

      const response = generator.createGroundedResponse('Medical advice', [doc], true);

      expect(response.responseText).toContain('Sources:');
      expect(response.citations).toHaveLength(1);
      expect(response.sourceDocuments).toHaveLength(1);
    });

    it('should validate citations', () => {
      const generator = new CitationGenerator();
      const doc = createSampleDocument();
      const response = generator.createGroundedResponse('Medical advice', [doc]);

      const validation = generator.validateCitations(response);

      expect(validation.valid).toBe(true);
      expect(validation.hasCitations).toBe(true);
    });
  });

  describe('KnowledgeBaseManager', () => {
    it('should add document', () => {
      const manager = new KnowledgeBaseManager();
      const doc = createSampleDocument();

      const success = manager.addDocument(doc, KnowledgeBaseCategory.CLINICAL_GUIDELINES);

      expect(success).toBe(true);
      expect(manager.getDocument(doc.documentId)).toEqual(doc);
    });

    it('should not add duplicate document', () => {
      const manager = new KnowledgeBaseManager();
      const doc = createSampleDocument();

      manager.addDocument(doc, KnowledgeBaseCategory.CLINICAL_GUIDELINES);
      const success = manager.addDocument(doc, KnowledgeBaseCategory.CLINICAL_GUIDELINES);

      expect(success).toBe(false);
    });

    it('should get documents by category', () => {
      const manager = new KnowledgeBaseManager();
      const doc1 = createSampleDocument('doc-1');
      const doc2 = createSampleDocument('doc-2');

      manager.addDocument(doc1, KnowledgeBaseCategory.CLINICAL_GUIDELINES);
      manager.addDocument(doc2, KnowledgeBaseCategory.EDUCATIONAL_CONTENT);

      const guidelines = manager.getDocumentsByCategory(KnowledgeBaseCategory.CLINICAL_GUIDELINES);
      expect(guidelines).toHaveLength(1);
    });

    it('should get statistics', () => {
      const manager = new KnowledgeBaseManager();
      manager.addDocument(createSampleDocument(), KnowledgeBaseCategory.CLINICAL_GUIDELINES);

      const stats = manager.getStatistics();

      expect(stats.total_documents).toBe(1);
      expect(stats.validated).toBe(1);
    });
  });

  describe('RAGSystem Integration', () => {
    it('should initialize', () => {
      const rag = new RAGSystem();
      expect(rag).toBeDefined();
    });

    it('should add knowledge', () => {
      const rag = new RAGSystem();
      const doc = createSampleDocument();

      const success = rag.addKnowledge(doc, KnowledgeBaseCategory.CLINICAL_GUIDELINES);

      expect(success).toBe(true);
    });

    it('should initialize knowledge base', () => {
      const rag = new RAGSystem();
      const docs: Array<[KnowledgeDocument, KnowledgeBaseCategory]> = [
        [createSampleDocument('doc-1'), KnowledgeBaseCategory.CLINICAL_GUIDELINES],
        [createSampleDocument('doc-2'), KnowledgeBaseCategory.CLINICAL_GUIDELINES],
      ];

      const count = rag.initializeKnowledgeBase(docs);

      expect(count).toBe(2);
    });

    it('should retrieve and rerank documents', () => {
      const rag = new RAGSystem();
      const docs: Array<[KnowledgeDocument, KnowledgeBaseCategory]> = [
        [createSampleDocument('doc-1'), KnowledgeBaseCategory.CLINICAL_GUIDELINES],
        [createSampleDocument('doc-2'), KnowledgeBaseCategory.CLINICAL_GUIDELINES],
      ];

      rag.initializeKnowledgeBase(docs);
      const retrieved = rag.retrieveRelevantDocs('heart failure');
      const ranked = rag.rerankByRelevance('heart failure', retrieved);

      expect(ranked.length).toBeGreaterThan(0);
    });

    it('should generate grounded response', () => {
      const rag = new RAGSystem();
      const doc = createSampleDocument();
      rag.addKnowledge(doc, KnowledgeBaseCategory.CLINICAL_GUIDELINES);

      const retrieved = rag.retrieveRelevantDocs('heart failure');
      const ranked = rag.rerankByRelevance('heart failure', retrieved);
      const response = rag.generateGroundedResponse('heart failure care', ranked);

      expect(response.responseText).toBeDefined();
      expect(response.citations.length).toBeGreaterThan(0);
    });

    it('should get knowledge base stats', () => {
      const rag = new RAGSystem();
      rag.addKnowledge(createSampleDocument(), KnowledgeBaseCategory.CLINICAL_GUIDELINES);

      const stats = rag.getKnowledgeBaseStats();

      expect(stats.total_documents).toBe(1);
    });
  });
});
