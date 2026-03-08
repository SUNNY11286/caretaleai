/**
 * Re-ranker Component
 * Implements relevance scoring and context selection for optimal response grounding.
 */

import { KnowledgeDocument } from '../shared/types/knowledge-document';
import { RankedDocument, RerankingConfig } from './types';

export class Reranker {
  private config: RerankingConfig;

  constructor(config?: Partial<RerankingConfig>) {
    this.config = {
      maxContextDocs: config?.maxContextDocs ?? 5,
      diversityWeight: config?.diversityWeight ?? 0.3,
      recencyWeight: config?.recencyWeight ?? 0.2,
      authorityWeight: config?.authorityWeight ?? 0.5,
    };
  }

  rerank(
    query: string,
    documents: KnowledgeDocument[],
    initialScores?: number[]
  ): RankedDocument[] {
    if (documents.length === 0) {
      return [];
    }

    const scores = initialScores ?? documents.map(() => 1.0);
    const authorityScores = this.computeAuthorityScores(documents);
    const recencyScores = this.computeRecencyScores(documents);
    const diversityScores = this.computeDiversityScores(documents);

    const finalScores = this.combineScores(scores, authorityScores, recencyScores, diversityScores);

    // Sort by score and create ranked documents
    const indexed = documents.map((doc, idx) => ({ doc, score: finalScores[idx], idx }));
    indexed.sort((a, b) => b.score - a.score);

    return indexed.slice(0, this.config.maxContextDocs).map((item, rank) => ({
      document: item.doc,
      relevanceScore: item.score,
      rank: rank + 1,
    }));
  }

  private computeAuthorityScores(documents: KnowledgeDocument[]): number[] {
    return documents.map((doc) => doc.source.credibilityScore);
  }

  private computeRecencyScores(documents: KnowledgeDocument[]): number[] {
    const now = new Date();
    return documents.map((doc) => {
      const ageDays = (now.getTime() - doc.lastUpdated.getTime()) / (1000 * 60 * 60 * 24);
      return Math.exp(-ageDays / 365.0);
    });
  }

  private computeDiversityScores(documents: KnowledgeDocument[]): number[] {
    const domainCounts = new Map<string, number>();

    documents.forEach((doc) => {
      const count = domainCounts.get(doc.domain) ?? 0;
      domainCounts.set(doc.domain, count + 1);
    });

    const scores = documents.map((doc) => 1.0 / (domainCounts.get(doc.domain) ?? 1));
    const maxScore = Math.max(...scores);
    return scores.map((s) => s / maxScore);
  }

  private combineScores(
    initialScores: number[],
    authorityScores: number[],
    recencyScores: number[],
    diversityScores: number[]
  ): number[] {
    const maxInitial = Math.max(...initialScores);
    const normalizedInitial = initialScores.map((s) => s / maxInitial);

    const semanticWeight =
      1.0 - (this.config.authorityWeight + this.config.recencyWeight + this.config.diversityWeight);

    return normalizedInitial.map((_, i) => {
      return (
        semanticWeight * normalizedInitial[i] +
        this.config.authorityWeight * authorityScores[i] +
        this.config.recencyWeight * recencyScores[i] +
        this.config.diversityWeight * diversityScores[i]
      );
    });
  }

  selectContext(rankedDocuments: RankedDocument[], maxTokens: number = 2000): RankedDocument[] {
    const selected: RankedDocument[] = [];
    let totalTokens = 0;

    for (const doc of rankedDocuments) {
      const docTokens = Math.floor(doc.document.content.length / 4);

      if (totalTokens + docTokens <= maxTokens) {
        selected.push(doc);
        totalTokens += docTokens;
      } else {
        break;
      }
    }

    return selected;
  }
}
