/**
 * Unit tests for AI Orchestrator component
 */

import {
  AIOrchestrator,
  PipelineType,
  Pipeline,
  RequestAnalysis,
} from '../ai-orchestrator';
import {
  NormalizedRequest,
  InputType,
  PipelineResponse,
} from '../../shared/types/interaction-record';

// Mock pipeline implementation
class MockPipeline implements Pipeline {
  id: string;
  name: string;
  type: PipelineType;
  isAvailable: boolean = true;
  averageResponseTime: number = 100;
  successRate: number = 0.95;
  private shouldFail: boolean = false;

  constructor(type: PipelineType, id?: string) {
    this.type = type;
    this.id = id || `${type}_pipeline`;
    this.name = `${type} Pipeline`;
  }

  setShouldFail(fail: boolean): void {
    this.shouldFail = fail;
  }

  async process(request: NormalizedRequest): Promise<PipelineResponse> {
    if (this.shouldFail) {
      throw new Error('Pipeline processing failed');
    }

    return {
      pipelineId: this.id,
      pipelineName: this.name,
      responseContent: `Response from ${this.name} for: ${request.originalInput}`,
      confidence: 0.9,
      sources: ['test-source-1'],
      processingTime: this.averageResponseTime,
      timestamp: new Date(),
    };
  }
}

describe('AIOrchestrator', () => {
  let orchestrator: AIOrchestrator;

  beforeEach(() => {
    orchestrator = new AIOrchestrator();
  });

  describe('Pipeline Registration', () => {
    it('should register a pipeline successfully', () => {
      const pipeline = new MockPipeline(PipelineType.CARE_STORY);
      orchestrator.registerPipeline(pipeline);

      const metrics = orchestrator.getPerformanceMetrics();
      expect(metrics[PipelineType.CARE_STORY]).toBeDefined();
      expect(metrics[PipelineType.CARE_STORY].isAvailable).toBe(true);
    });

    it('should initialize circuit breaker for registered pipeline', () => {
      const pipeline = new MockPipeline(PipelineType.MEDICATION_CLARIFICATION);
      orchestrator.registerPipeline(pipeline);

      const metrics = orchestrator.getPerformanceMetrics();
      expect(metrics[PipelineType.MEDICATION_CLARIFICATION].circuitBreakerOpen).toBe(false);
      expect(metrics[PipelineType.MEDICATION_CLARIFICATION].failureCount).toBe(0);
    });
  });

  describe('Request Analysis', () => {
    it('should identify care story intent', () => {
      const request: NormalizedRequest = {
        requestId: 'req-1',
        patientId: 'patient-1',
        originalInput: 'Show me my discharge instructions',
        inputType: InputType.TEXT,
        intent: 'care story',
        entities: {},
        context: {},
        timestamp: new Date(),
      };

      const analysis = orchestrator.analyzeRequest(request);

      expect(analysis.primaryIntent).toBe('care_story_generation');
      expect(analysis.suggestedPipelines).toContain(PipelineType.CARE_STORY);
      expect(analysis.complexity).toBe('simple');
      expect(analysis.requiresMultiplePipelines).toBe(false);
    });

    it('should identify medication clarification intent', () => {
      const request: NormalizedRequest = {
        requestId: 'req-2',
        patientId: 'patient-1',
        originalInput: 'What is this medication for?',
        inputType: InputType.TEXT,
        intent: 'medication question',
        entities: {},
        context: {},
        timestamp: new Date(),
      };

      const analysis = orchestrator.analyzeRequest(request);

      expect(analysis.primaryIntent).toBe('medication_clarification');
      expect(analysis.suggestedPipelines).toContain(PipelineType.MEDICATION_CLARIFICATION);
    });

    it('should identify understanding verification intent', () => {
      const request: NormalizedRequest = {
        requestId: 'req-3',
        patientId: 'patient-1',
        originalInput: 'I am confused about what to do',
        inputType: InputType.TEXT,
        intent: 'confused about instructions',
        entities: {},
        context: {},
        timestamp: new Date(),
      };

      const analysis = orchestrator.analyzeRequest(request);

      expect(analysis.primaryIntent).toBe('understanding_verification');
      expect(analysis.suggestedPipelines).toContain(PipelineType.UNDERSTANDING_VERIFICATION);
    });

    it('should identify follow-up intent', () => {
      const request: NormalizedRequest = {
        requestId: 'req-4',
        patientId: 'patient-1',
        originalInput: 'When is my next appointment?',
        inputType: InputType.TEXT,
        intent: 'appointment reminder',
        entities: {},
        context: {},
        timestamp: new Date(),
      };

      const analysis = orchestrator.analyzeRequest(request);

      expect(analysis.primaryIntent).toBe('follow_up');
      expect(analysis.suggestedPipelines).toContain(PipelineType.FOLLOW_UP);
    });

    it('should detect multi-pipeline needs', () => {
      const request: NormalizedRequest = {
        requestId: 'req-5',
        patientId: 'patient-1',
        originalInput: 'Show me my care plan and medication schedule',
        inputType: InputType.TEXT,
        intent: 'care story with medication',
        entities: {},
        context: {},
        timestamp: new Date(),
      };

      const analysis = orchestrator.analyzeRequest(request);

      expect(analysis.requiresMultiplePipelines).toBe(true);
      expect(analysis.suggestedPipelines.length).toBeGreaterThan(1);
      expect(analysis.complexity).toBe('moderate');
    });

    it('should default to understanding verification for unclear intent', () => {
      const request: NormalizedRequest = {
        requestId: 'req-6',
        patientId: 'patient-1',
        originalInput: 'Hello',
        inputType: InputType.TEXT,
        intent: 'greeting',
        entities: {},
        context: {},
        timestamp: new Date(),
      };

      const analysis = orchestrator.analyzeRequest(request);

      expect(analysis.primaryIntent).toBe('general_query');
      expect(analysis.suggestedPipelines).toContain(PipelineType.UNDERSTANDING_VERIFICATION);
      expect(analysis.confidence).toBeLessThan(0.8);
    });
  });

  describe('Pipeline Routing', () => {
    beforeEach(() => {
      // Register all pipeline types
      orchestrator.registerPipeline(new MockPipeline(PipelineType.CARE_STORY));
      orchestrator.registerPipeline(new MockPipeline(PipelineType.MEDICATION_CLARIFICATION));
      orchestrator.registerPipeline(new MockPipeline(PipelineType.UNDERSTANDING_VERIFICATION));
      orchestrator.registerPipeline(new MockPipeline(PipelineType.FOLLOW_UP));
    });

    it('should route to single pipeline for simple request', async () => {
      const request: NormalizedRequest = {
        requestId: 'req-7',
        patientId: 'patient-1',
        originalInput: 'Show me my medications',
        inputType: InputType.TEXT,
        intent: 'medication list',
        entities: {},
        context: {},
        timestamp: new Date(),
      };

      const analysis = orchestrator.analyzeRequest(request);
      const routes = await orchestrator.routeToPipeline(analysis, request);

      expect(routes.length).toBe(1);
      expect(routes[0].routingReason).toBe('primary_intent');
      expect(routes[0].priority).toBe(1);
    });

    it('should route to multiple pipelines for complex request', async () => {
      const request: NormalizedRequest = {
        requestId: 'req-8',
        patientId: 'patient-1',
        originalInput: 'Show me my care plan with medication reminders',
        inputType: InputType.TEXT,
        intent: 'care story with medication and reminder',
        entities: {},
        context: {},
        timestamp: new Date(),
      };

      const analysis = orchestrator.analyzeRequest(request);
      const routes = await orchestrator.routeToPipeline(analysis, request);

      expect(routes.length).toBeGreaterThan(1);
      expect(routes[0].routingReason).toBe('primary_intent');
      expect(routes[1].routingReason).toBe('secondary_intent');
    });
  });

  describe('Multi-Pipeline Coordination', () => {
    it('should coordinate multiple pipelines successfully', async () => {
      const pipelines = [
        new MockPipeline(PipelineType.CARE_STORY),
        new MockPipeline(PipelineType.MEDICATION_CLARIFICATION),
      ];

      const request: NormalizedRequest = {
        requestId: 'req-9',
        patientId: 'patient-1',
        originalInput: 'Tell me about my care plan and medications',
        inputType: InputType.TEXT,
        intent: 'care story with medication',
        entities: {},
        context: {},
        timestamp: new Date(),
      };

      const result = await orchestrator.coordinateMultiPipeline(pipelines, request);

      expect(result.responses.length).toBe(2);
      expect(result.integratedContent).toContain('Response from');
      expect(result.confidence).toBeGreaterThan(0);
      expect(result.sources.length).toBeGreaterThan(0);
      expect(result.processingTime).toBeGreaterThanOrEqual(0);
    });

    it('should handle partial pipeline failures gracefully', async () => {
      const pipeline1 = new MockPipeline(PipelineType.CARE_STORY);
      const pipeline2 = new MockPipeline(PipelineType.MEDICATION_CLARIFICATION);
      pipeline2.setShouldFail(true);

      const pipelines = [pipeline1, pipeline2];

      const request: NormalizedRequest = {
        requestId: 'req-10',
        patientId: 'patient-1',
        originalInput: 'Tell me about my care',
        inputType: InputType.TEXT,
        intent: 'care story',
        entities: {},
        context: {},
        timestamp: new Date(),
      };

      const result = await orchestrator.coordinateMultiPipeline(pipelines, request);

      // Should still have response from successful pipeline
      expect(result.responses.length).toBeGreaterThan(0);
      expect(result.integratedContent).toBeTruthy();
    });

    it('should integrate responses from multiple pipelines', async () => {
      const pipelines = [
        new MockPipeline(PipelineType.CARE_STORY),
        new MockPipeline(PipelineType.FOLLOW_UP),
      ];

      const request: NormalizedRequest = {
        requestId: 'req-11',
        patientId: 'patient-1',
        originalInput: 'What should I do and when?',
        inputType: InputType.TEXT,
        intent: 'care story with follow-up',
        entities: {},
        context: {},
        timestamp: new Date(),
      };

      const result = await orchestrator.coordinateMultiPipeline(pipelines, request);

      expect(result.integratedContent).toContain('care_story');
      expect(result.integratedContent).toContain('follow_up');
    });
  });

  describe('Circuit Breaker and Failover', () => {
    it('should handle pipeline failover', async () => {
      const failedPipeline = new MockPipeline(PipelineType.CARE_STORY);
      failedPipeline.setShouldFail(true);

      const request: NormalizedRequest = {
        requestId: 'req-12',
        patientId: 'patient-1',
        originalInput: 'Show me my care plan',
        inputType: InputType.TEXT,
        intent: 'care story',
        entities: {},
        context: {},
        timestamp: new Date(),
      };

      const fallbackResponse = await orchestrator.handleFailover(failedPipeline, request);

      expect(fallbackResponse.pipelineId).toBe('fallback');
      expect(fallbackResponse.responseContent).toContain('trouble processing');
      expect(fallbackResponse.confidence).toBeLessThan(0.5);
    });

    it('should open circuit breaker after multiple failures', async () => {
      const pipeline = new MockPipeline(PipelineType.MEDICATION_CLARIFICATION);
      pipeline.setShouldFail(true);
      orchestrator.registerPipeline(pipeline);

      const request: NormalizedRequest = {
        requestId: 'req-13',
        patientId: 'patient-1',
        originalInput: 'What is this medication?',
        inputType: InputType.TEXT,
        intent: 'medication question',
        entities: {},
        context: {},
        timestamp: new Date(),
      };

      // Trigger multiple failures
      for (let i = 0; i < 3; i++) {
        await orchestrator.handleFailover(pipeline, request);
      }

      const metrics = orchestrator.getPerformanceMetrics();
      expect(metrics[PipelineType.MEDICATION_CLARIFICATION].circuitBreakerOpen).toBe(true);
      expect(metrics[PipelineType.MEDICATION_CLARIFICATION].failureCount).toBeGreaterThanOrEqual(3);
    });
  });

  describe('Performance Monitoring', () => {
    it('should provide performance metrics for all pipelines', () => {
      orchestrator.registerPipeline(new MockPipeline(PipelineType.CARE_STORY));
      orchestrator.registerPipeline(new MockPipeline(PipelineType.MEDICATION_CLARIFICATION));

      const metrics = orchestrator.getPerformanceMetrics();

      expect(metrics[PipelineType.CARE_STORY]).toBeDefined();
      expect(metrics[PipelineType.MEDICATION_CLARIFICATION]).toBeDefined();
      expect(metrics[PipelineType.CARE_STORY].isAvailable).toBe(true);
      expect(metrics[PipelineType.CARE_STORY].averageResponseTime).toBeGreaterThan(0);
      expect(metrics[PipelineType.CARE_STORY].successRate).toBeGreaterThan(0);
    });

    it('should track circuit breaker status in metrics', () => {
      const pipeline = new MockPipeline(PipelineType.UNDERSTANDING_VERIFICATION);
      orchestrator.registerPipeline(pipeline);

      const metrics = orchestrator.getPerformanceMetrics();

      expect(metrics[PipelineType.UNDERSTANDING_VERIFICATION].circuitBreakerOpen).toBe(false);
      expect(metrics[PipelineType.UNDERSTANDING_VERIFICATION].failureCount).toBe(0);
    });
  });
});
