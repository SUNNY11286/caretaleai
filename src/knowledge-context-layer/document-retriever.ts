/**
 * Document Retriever Component
 * Implements semantic search across clinical guidelines using dense vector embeddings.
 */

import { KnowledgeDocument, MedicalDomain } from '../shared/types/knowledge-document';
import { RetrievalConfig } from './types';

export class DocumentRetriever {
  private documents: KnowledgeDocument[] = [];
  private embeddings: number[][] | null = null;
  private embeddingDim: number;

  constructor(embeddingDim: number = 768) {
    this.embeddingDim = embeddingDim;
  }

  addDocuments(documents: KnowledgeDocument[]): void {
    this.documents.push(...documents);
    const newEmbeddings = this.computeEmbeddings(documents.map((doc) => doc.content));

    if (this.embeddings === null) {
      this.embeddings = newEmbeddings;
    } else {
      this.embeddings.push(...newEmbeddings);
    }
  }

  retrieve(query: string, config?: RetrievalConfig): KnowledgeDocument[] {
    const defaultConfig: RetrievalConfig = {
      topK: 10,
      similarityThreshold: 0.7,
      domainFilter: config?.domainFilter,
    };
    const finalConfig = { ...defaultConfig, ...config };

    if (this.documents.length === 0 || this.embeddings === null) {
      return [];
    }

    const queryEmbedding = this.computeQueryEmbedding(query);
    const candidateIndices = this.filterByDomain(finalConfig.domainFilter);
    const similarities = this.computeSimilarities(queryEmbedding, candidateIndices);
    const relevantIndices = this.filterAndRank(
      similarities,
      candidateIndices,
      finalConfig.similarityThreshold,
      finalConfig.topK
    );

    return relevantIndices.map((idx) => this.documents[idx]);
  }

  private computeEmbeddings(texts: string[]): number[][] {
    // Placeholder: random embeddings for minimal implementation
    return texts.map(() =>
      Array.from({ length: this.embeddingDim }, () => Math.random() - 0.5)
    );
  }

  private computeQueryEmbedding(query: string): number[] {
    // Placeholder: random embedding
    return Array.from({ length: this.embeddingDim }, () => Math.random() - 0.5);
  }

  private filterByDomain(domainFilter?: MedicalDomain): number[] {
    if (!domainFilter) {
      return Array.from({ length: this.documents.length }, (_, i) => i);
    }

    return this.documents
      .map((doc, idx) => (doc.domain === domainFilter ? idx : -1))
      .filter((idx) => idx !== -1);
  }

  private computeSimilarities(queryEmbedding: number[], candidateIndices: number[]): number[] {
    if (candidateIndices.length === 0 || !this.embeddings) {
      return [];
    }

    const queryNorm = this.norm(queryEmbedding);
    const similarities: number[] = [];

    for (const idx of candidateIndices) {
      const docEmbedding = this.embeddings[idx];
      const docNorm = this.norm(docEmbedding);
      const dotProduct = this.dotProduct(queryEmbedding, docEmbedding);
      const similarity = dotProduct / (queryNorm * docNorm + 1e-8);
      similarities.push(similarity);
    }

    return similarities;
  }

  private filterAndRank(
    similarities: number[],
    candidateIndices: number[],
    threshold: number,
    topK: number
  ): number[] {
    if (similarities.length === 0) {
      return [];
    }

    // Filter by threshold
    const filtered: Array<{ idx: number; score: number }> = [];
    for (let i = 0; i < similarities.length; i++) {
      if (similarities[i] >= threshold) {
        filtered.push({ idx: candidateIndices[i], score: similarities[i] });
      }
    }

    // Sort by score (descending) and take top-k
    filtered.sort((a, b) => b.score - a.score);
    return filtered.slice(0, topK).map((item) => item.idx);
  }

  private norm(vector: number[]): number {
    return Math.sqrt(vector.reduce((sum, val) => sum + val * val, 0));
  }

  private dotProduct(a: number[], b: number[]): number {
    return a.reduce((sum, val, i) => sum + val * b[i], 0);
  }

  clear(): void {
    this.documents = [];
    this.embeddings = null;
  }
}
