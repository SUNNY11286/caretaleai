/**
 * AI Orchestrator Component
 * Central routing and coordination hub for all AI pipeline interactions.
 * 
 * Responsibilities:
 * - Analyze incoming patient requests to determine intent and routing
 * - Route requests to appropriate specialized pipelines
 * - Coordinate multi-pipeline requests for complex queries
 * - Monitor pipeline performance and implement circuit breakers
 * - Handle failover to backup systems when needed
 */

import {
  NormalizedRequest,
  PipelineRoute,
  PipelineResponse,
} from '../shared/types/interaction-record';

export enum PipelineType {
  CARE_STORY = 'care_story',
  UNDERSTANDING_VERIFICATION = 'understanding_verification',
  MEDICATION_CLARIFICATION = 'medication_clarification',
  FOLLOW_UP = 'follow_up',
}

export interface RequestAnalysis {
  primaryIntent: string;
  secondaryIntents: string[];
  complexity: 'simple' | 'moderate' | 'complex';
  requiresMultiplePipelines: boolean;
  suggestedPipelines: PipelineType[];
  confidence: number;
  entities: Record<string, any>;
}

export interface Pipeline {
  id: string;
  name: string;
  type: PipelineType;
  isAvailable: boolean;
  averageResponseTime: number;
  successRate: number;
  process(request: NormalizedRequest): Promise<PipelineResponse>;
}

export interface CoordinatedResponse {
  responses: PipelineResponse[];
  integratedContent: string;
  confidence: number;
  sources: string[];
  processingTime: number;
}

export interface CircuitBreakerState {
  pipelineId: string;
  isOpen: boolean;
  failureCount: number;
  lastFailureTime?: Date;
  nextRetryTime?: Date;
}

/**
 * AI Orchestrator - Routes and coordinates AI pipeline requests
 */
export class AIOrchestrator {
  private pipelines: Map<PipelineType, Pipeline>;
  private circuitBreakers: Map<string, CircuitBreakerState>;
  private readonly failureThreshold: number = 3;
  private readonly circuitBreakerTimeout: number = 60000; // 60 seconds

  constructor() {
    this.pipelines = new Map();
    this.circuitBreakers = new Map();
  }

  /**
   * Register a pipeline with the orchestrator
   */
  registerPipeline(pipeline: Pipeline): void {
    this.pipelines.set(pipeline.type, pipeline);
    this.circuitBreakers.set(pipeline.id, {
      pipelineId: pipeline.id,
      isOpen: false,
      failureCount: 0,
    });
  }

  /**
   * Analyze incoming request to determine routing strategy
   * Implements Requirement 7.1: Request analysis and routing
   */
  analyzeRequest(request: NormalizedRequest): RequestAnalysis {
    const intent = request.intent.toLowerCase();
    const entities = request.entities;
    
    // Determine primary intent and suggested pipelines
    let primaryIntent = intent;
    let suggestedPipelines: PipelineType[] = [];
    let complexity: 'simple' | 'moderate' | 'complex' = 'simple';
    let confidence = 0.8;

    // Care story generation requests
    if (this.matchesIntent(intent, ['care story', 'discharge', 'instructions', 'care plan'])) {
      primaryIntent = 'care_story_generation';
      suggestedPipelines.push(PipelineType.CARE_STORY);
    }
    
    // Understanding verification requests
    else if (this.matchesIntent(intent, ['confused', 'clarify', 'explain', 'understand', 'what does', 'help me understand'])) {
      primaryIntent = 'understanding_verification';
      suggestedPipelines.push(PipelineType.UNDERSTANDING_VERIFICATION);
    }
    
    // Medication-related requests
    else if (this.matchesIntent(intent, ['medication', 'medicine', 'drug', 'pill', 'prescription', 'dose'])) {
      primaryIntent = 'medication_clarification';
      suggestedPipelines.push(PipelineType.MEDICATION_CLARIFICATION);
    }
    
    // Follow-up and reminder requests
    else if (this.matchesIntent(intent, ['reminder', 'appointment', 'follow-up', 'schedule', 'when should'])) {
      primaryIntent = 'follow_up';
      suggestedPipelines.push(PipelineType.FOLLOW_UP);
    }
    
    // Default to understanding verification for unclear intents
    else {
      primaryIntent = 'general_query';
      suggestedPipelines.push(PipelineType.UNDERSTANDING_VERIFICATION);
      confidence = 0.5;
    }

    // Check for multi-pipeline needs
    const secondaryIntents: string[] = [];
    
    // If medication mentioned in care story context
    if (suggestedPipelines.includes(PipelineType.CARE_STORY) && 
        this.matchesIntent(intent, ['medication', 'medicine'])) {
      secondaryIntents.push('medication_clarification');
      suggestedPipelines.push(PipelineType.MEDICATION_CLARIFICATION);
      complexity = 'moderate';
    }
    
    // If follow-up mentioned with other intents
    if (this.matchesIntent(intent, ['reminder', 'appointment']) && 
        suggestedPipelines.length > 0 && 
        !suggestedPipelines.includes(PipelineType.FOLLOW_UP)) {
      secondaryIntents.push('follow_up');
      suggestedPipelines.push(PipelineType.FOLLOW_UP);
      complexity = 'moderate';
    }

    // Complex queries require multiple pipelines
    if (suggestedPipelines.length > 2) {
      complexity = 'complex';
    }

    return {
      primaryIntent,
      secondaryIntents,
      complexity,
      requiresMultiplePipelines: suggestedPipelines.length > 1,
      suggestedPipelines,
      confidence,
      entities,
    };
  }

  /**
   * Route request to appropriate pipeline(s)
   * Implements Requirement 7.2: Pipeline selection and routing
   */
  async routeToPipeline(
    analysis: RequestAnalysis,
    request: NormalizedRequest
  ): Promise<PipelineRoute[]> {
    const routes: PipelineRoute[] = [];
    
    // Sort pipelines by priority (primary intent first)
    const sortedPipelines = this.prioritizePipelines(analysis.suggestedPipelines);
    
    for (let i = 0; i < sortedPipelines.length; i++) {
      const pipelineType = sortedPipelines[i];
      const pipeline = this.pipelines.get(pipelineType);
      
      if (!pipeline) {
        continue;
      }

      // Check circuit breaker
      const circuitBreaker = this.circuitBreakers.get(pipeline.id);
      if (circuitBreaker && this.isCircuitBreakerOpen(circuitBreaker)) {
        // Try to find backup pipeline
        continue;
      }

      routes.push({
        pipelineId: pipeline.id,
        pipelineName: pipeline.name,
        routingReason: i === 0 ? 'primary_intent' : 'secondary_intent',
        priority: i + 1,
        timestamp: new Date(),
      });
    }

    return routes;
  }

  /**
   * Coordinate multiple pipelines for complex requests
   * Implements Requirement 7.3: Multi-pipeline coordination
   */
  async coordinateMultiPipeline(
    pipelines: Pipeline[],
    request: NormalizedRequest
  ): Promise<CoordinatedResponse> {
    const startTime = Date.now();
    const responses: PipelineResponse[] = [];
    const sources: Set<string> = new Set();

    // Execute pipelines in parallel for efficiency
    const pipelinePromises = pipelines.map(async (pipeline) => {
      try {
        const response = await this.executePipelineWithCircuitBreaker(pipeline, request);
        responses.push(response);
        
        // Collect sources
        if (response.sources) {
          response.sources.forEach(source => sources.add(source));
        }
        
        return response;
      } catch (error) {
        // Log error but continue with other pipelines
        console.error(`Pipeline ${pipeline.name} failed:`, error);
        return null;
      }
    });

    await Promise.all(pipelinePromises);

    // Filter out failed responses
    const successfulResponses = responses.filter(r => r !== null);

    // Integrate responses
    const integratedContent = this.integrateResponses(successfulResponses);
    const averageConfidence = successfulResponses.length > 0
      ? successfulResponses.reduce((sum, r) => sum + r.confidence, 0) / successfulResponses.length
      : 0;

    const processingTime = Date.now() - startTime;

    return {
      responses: successfulResponses,
      integratedContent,
      confidence: averageConfidence,
      sources: Array.from(sources),
      processingTime,
    };
  }

  /**
   * Handle pipeline failover to backup systems
   * Implements Requirement 7.5: Failover and backup routing
   */
  async handleFailover(
    failedPipeline: Pipeline,
    request: NormalizedRequest
  ): Promise<PipelineResponse> {
    // Mark circuit breaker
    this.recordFailure(failedPipeline.id);

    // Try to find alternative pipeline of same type
    const alternativePipeline = this.findAlternativePipeline(failedPipeline.type);
    
    if (alternativePipeline) {
      try {
        return await alternativePipeline.process(request);
      } catch (error) {
        // Alternative also failed
        this.recordFailure(alternativePipeline.id);
      }
    }

    // Return fallback response
    return {
      pipelineId: 'fallback',
      pipelineName: 'Fallback Handler',
      responseContent: 'I apologize, but I\'m having trouble processing your request right now. Please try again in a moment, or contact your care team for immediate assistance.',
      confidence: 0.3,
      processingTime: 0,
      timestamp: new Date(),
    };
  }

  /**
   * Execute pipeline with circuit breaker protection
   */
  private async executePipelineWithCircuitBreaker(
    pipeline: Pipeline,
    request: NormalizedRequest
  ): Promise<PipelineResponse> {
    const circuitBreaker = this.circuitBreakers.get(pipeline.id);
    
    if (circuitBreaker && this.isCircuitBreakerOpen(circuitBreaker)) {
      throw new Error(`Circuit breaker open for pipeline ${pipeline.id}`);
    }

    try {
      const response = await pipeline.process(request);
      this.recordSuccess(pipeline.id);
      return response;
    } catch (error) {
      this.recordFailure(pipeline.id);
      throw error;
    }
  }

  /**
   * Check if circuit breaker is open
   */
  private isCircuitBreakerOpen(circuitBreaker: CircuitBreakerState): boolean {
    if (!circuitBreaker.isOpen) {
      return false;
    }

    // Check if timeout has passed
    if (circuitBreaker.nextRetryTime && new Date() >= circuitBreaker.nextRetryTime) {
      // Reset circuit breaker
      circuitBreaker.isOpen = false;
      circuitBreaker.failureCount = 0;
      return false;
    }

    return true;
  }

  /**
   * Record pipeline success
   */
  private recordSuccess(pipelineId: string): void {
    const circuitBreaker = this.circuitBreakers.get(pipelineId);
    if (circuitBreaker) {
      circuitBreaker.failureCount = 0;
      circuitBreaker.isOpen = false;
    }
  }

  /**
   * Record pipeline failure and potentially open circuit breaker
   */
  private recordFailure(pipelineId: string): void {
    const circuitBreaker = this.circuitBreakers.get(pipelineId);
    if (!circuitBreaker) {
      return;
    }

    circuitBreaker.failureCount++;
    circuitBreaker.lastFailureTime = new Date();

    if (circuitBreaker.failureCount >= this.failureThreshold) {
      circuitBreaker.isOpen = true;
      circuitBreaker.nextRetryTime = new Date(Date.now() + this.circuitBreakerTimeout);
    }
  }

  /**
   * Find alternative pipeline of the same type
   */
  private findAlternativePipeline(type: PipelineType): Pipeline | null {
    // In a real implementation, this would check for backup pipelines
    // For now, return null as we don't have backup pipelines configured
    return null;
  }

  /**
   * Integrate multiple pipeline responses into coherent output
   */
  private integrateResponses(responses: PipelineResponse[]): string {
    if (responses.length === 0) {
      return '';
    }

    if (responses.length === 1) {
      return responses[0].responseContent;
    }

    // For multiple responses, combine them with clear sections
    const sections = responses.map((response, index) => {
      return response.responseContent;
    });

    return sections.join('\n\n');
  }

  /**
   * Prioritize pipelines based on analysis
   */
  private prioritizePipelines(pipelines: PipelineType[]): PipelineType[] {
    // Primary intent pipeline should be first
    // For now, just return as-is since they're already ordered by priority
    return [...pipelines];
  }

  /**
   * Check if intent matches any of the keywords
   */
  private matchesIntent(intent: string, keywords: string[]): boolean {
    const lowerIntent = intent.toLowerCase();
    return keywords.some(keyword => lowerIntent.includes(keyword.toLowerCase()));
  }

  /**
   * Get performance metrics for monitoring
   * Implements Requirement 7.5: Performance monitoring
   */
  getPerformanceMetrics(): Record<string, any> {
    const metrics: Record<string, any> = {};

    this.pipelines.forEach((pipeline, type) => {
      const circuitBreaker = this.circuitBreakers.get(pipeline.id);
      metrics[type] = {
        isAvailable: pipeline.isAvailable,
        averageResponseTime: pipeline.averageResponseTime,
        successRate: pipeline.successRate,
        circuitBreakerOpen: circuitBreaker?.isOpen || false,
        failureCount: circuitBreaker?.failureCount || 0,
      };
    });

    return metrics;
  }
}
