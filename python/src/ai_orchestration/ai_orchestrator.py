"""
AI Orchestrator Component
Central routing and coordination hub for all AI pipeline interactions.

Responsibilities:
- Analyze incoming patient requests to determine intent and routing
- Route requests to appropriate specialized pipelines
- Coordinate multi-pipeline requests for complex queries
- Monitor pipeline performance and implement circuit breakers
- Handle failover to backup systems when needed
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import List, Dict, Any, Optional, Protocol
from pydantic import BaseModel, Field

from ..models.interaction_record import NormalizedRequest, PipelineRoute, PipelineResponse


class PipelineType(str, Enum):
    """Types of AI pipelines available"""
    CARE_STORY = "care_story"
    UNDERSTANDING_VERIFICATION = "understanding_verification"
    MEDICATION_CLARIFICATION = "medication_clarification"
    FOLLOW_UP = "follow_up"


class RequestAnalysis(BaseModel):
    """Analysis of a patient request for routing"""
    primary_intent: str
    secondary_intents: List[str]
    complexity: str = Field(..., pattern="^(simple|moderate|complex)$")
    requires_multiple_pipelines: bool
    suggested_pipelines: List[PipelineType]
    confidence: float = Field(..., ge=0.0, le=1.0)
    entities: Dict[str, Any]


class Pipeline(Protocol):
    """Protocol for AI pipeline implementations"""
    id: str
    name: str
    type: PipelineType
    is_available: bool
    average_response_time: float
    success_rate: float

    async def process(self, request: NormalizedRequest) -> PipelineResponse:
        """Process a request and return a response"""
        ...


class CoordinatedResponse(BaseModel):
    """Response from coordinated multi-pipeline execution"""
    responses: List[PipelineResponse]
    integrated_content: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    sources: List[str]
    processing_time: float


class CircuitBreakerState(BaseModel):
    """State of a circuit breaker for a pipeline"""
    pipeline_id: str
    is_open: bool
    failure_count: int
    last_failure_time: Optional[datetime] = None
    next_retry_time: Optional[datetime] = None


class AIOrchestrator:
    """
    AI Orchestrator - Routes and coordinates AI pipeline requests
    """

    def __init__(
        self,
        failure_threshold: int = 3,
        circuit_breaker_timeout: int = 60,
    ):
        """
        Initialize the AI Orchestrator
        
        Args:
            failure_threshold: Number of failures before opening circuit breaker
            circuit_breaker_timeout: Timeout in seconds before retrying failed pipeline
        """
        self.pipelines: Dict[PipelineType, Pipeline] = {}
        self.circuit_breakers: Dict[str, CircuitBreakerState] = {}
        self.failure_threshold = failure_threshold
        self.circuit_breaker_timeout = circuit_breaker_timeout

    def register_pipeline(self, pipeline: Pipeline) -> None:
        """Register a pipeline with the orchestrator"""
        self.pipelines[pipeline.type] = pipeline
        self.circuit_breakers[pipeline.id] = CircuitBreakerState(
            pipeline_id=pipeline.id,
            is_open=False,
            failure_count=0,
        )

    def analyze_request(self, request: NormalizedRequest) -> RequestAnalysis:
        """
        Analyze incoming request to determine routing strategy
        Implements Requirement 7.1: Request analysis and routing
        """
        intent = request.intent.lower()
        entities = request.entities

        # Determine primary intent and suggested pipelines
        primary_intent = intent
        suggested_pipelines: List[PipelineType] = []
        complexity = "simple"
        confidence = 0.8

        # Care story generation requests
        if self._matches_intent(intent, ['care story', 'discharge', 'instructions', 'care plan']):
            primary_intent = 'care_story_generation'
            suggested_pipelines.append(PipelineType.CARE_STORY)

        # Understanding verification requests
        elif self._matches_intent(intent, ['confused', 'clarify', 'explain', 'understand', 'what does', 'help me understand']):
            primary_intent = 'understanding_verification'
            suggested_pipelines.append(PipelineType.UNDERSTANDING_VERIFICATION)

        # Medication-related requests
        elif self._matches_intent(intent, ['medication', 'medicine', 'drug', 'pill', 'prescription', 'dose']):
            primary_intent = 'medication_clarification'
            suggested_pipelines.append(PipelineType.MEDICATION_CLARIFICATION)

        # Follow-up and reminder requests
        elif self._matches_intent(intent, ['reminder', 'appointment', 'follow-up', 'schedule', 'when should']):
            primary_intent = 'follow_up'
            suggested_pipelines.append(PipelineType.FOLLOW_UP)

        # Default to understanding verification for unclear intents
        else:
            primary_intent = 'general_query'
            suggested_pipelines.append(PipelineType.UNDERSTANDING_VERIFICATION)
            confidence = 0.5

        # Check for multi-pipeline needs
        secondary_intents: List[str] = []

        # If medication mentioned in care story context
        if (PipelineType.CARE_STORY in suggested_pipelines and
                self._matches_intent(intent, ['medication', 'medicine'])):
            secondary_intents.append('medication_clarification')
            suggested_pipelines.append(PipelineType.MEDICATION_CLARIFICATION)
            complexity = 'moderate'

        # If follow-up mentioned with other intents
        if (self._matches_intent(intent, ['reminder', 'appointment']) and
                len(suggested_pipelines) > 0 and
                PipelineType.FOLLOW_UP not in suggested_pipelines):
            secondary_intents.append('follow_up')
            suggested_pipelines.append(PipelineType.FOLLOW_UP)
            complexity = 'moderate'

        # Complex queries require multiple pipelines
        if len(suggested_pipelines) > 2:
            complexity = 'complex'

        return RequestAnalysis(
            primary_intent=primary_intent,
            secondary_intents=secondary_intents,
            complexity=complexity,
            requires_multiple_pipelines=len(suggested_pipelines) > 1,
            suggested_pipelines=suggested_pipelines,
            confidence=confidence,
            entities=entities,
        )

    async def route_to_pipeline(
        self,
        analysis: RequestAnalysis,
        request: NormalizedRequest,
    ) -> List[PipelineRoute]:
        """
        Route request to appropriate pipeline(s)
        Implements Requirement 7.2: Pipeline selection and routing
        """
        routes: List[PipelineRoute] = []

        # Sort pipelines by priority (primary intent first)
        sorted_pipelines = self._prioritize_pipelines(analysis.suggested_pipelines)

        for i, pipeline_type in enumerate(sorted_pipelines):
            pipeline = self.pipelines.get(pipeline_type)

            if not pipeline:
                continue

            # Check circuit breaker
            circuit_breaker = self.circuit_breakers.get(pipeline.id)
            if circuit_breaker and self._is_circuit_breaker_open(circuit_breaker):
                # Try to find backup pipeline
                continue

            routes.append(PipelineRoute(
                pipeline_id=pipeline.id,
                pipeline_name=pipeline.name,
                routing_reason='primary_intent' if i == 0 else 'secondary_intent',
                priority=i + 1,
                timestamp=datetime.now(),
            ))

        return routes

    async def coordinate_multi_pipeline(
        self,
        pipelines: List[Pipeline],
        request: NormalizedRequest,
    ) -> CoordinatedResponse:
        """
        Coordinate multiple pipelines for complex requests
        Implements Requirement 7.3: Multi-pipeline coordination
        """
        import asyncio
        import time

        start_time = time.time()
        responses: List[PipelineResponse] = []
        sources: set = set()

        # Execute pipelines in parallel for efficiency
        async def execute_pipeline(pipeline: Pipeline) -> Optional[PipelineResponse]:
            try:
                response = await self._execute_pipeline_with_circuit_breaker(pipeline, request)
                responses.append(response)

                # Collect sources
                if response.sources:
                    for source in response.sources:
                        sources.add(source)

                return response
            except Exception as e:
                # Log error but continue with other pipelines
                print(f"Pipeline {pipeline.name} failed: {e}")
                return None

        # Execute all pipelines concurrently
        await asyncio.gather(*[execute_pipeline(p) for p in pipelines])

        # Filter out failed responses
        successful_responses = [r for r in responses if r is not None]

        # Integrate responses
        integrated_content = self._integrate_responses(successful_responses)
        average_confidence = (
            sum(r.confidence for r in successful_responses) / len(successful_responses)
            if successful_responses else 0.0
        )

        processing_time = time.time() - start_time

        return CoordinatedResponse(
            responses=successful_responses,
            integrated_content=integrated_content,
            confidence=average_confidence,
            sources=list(sources),
            processing_time=processing_time,
        )

    async def handle_failover(
        self,
        failed_pipeline: Pipeline,
        request: NormalizedRequest,
    ) -> PipelineResponse:
        """
        Handle pipeline failover to backup systems
        Implements Requirement 7.5: Failover and backup routing
        """
        # Mark circuit breaker
        self._record_failure(failed_pipeline.id)

        # Try to find alternative pipeline of same type
        alternative_pipeline = self._find_alternative_pipeline(failed_pipeline.type)

        if alternative_pipeline:
            try:
                return await alternative_pipeline.process(request)
            except Exception:
                # Alternative also failed
                self._record_failure(alternative_pipeline.id)

        # Return fallback response
        return PipelineResponse(
            pipeline_id='fallback',
            pipeline_name='Fallback Handler',
            response_content=(
                "I apologize, but I'm having trouble processing your request right now. "
                "Please try again in a moment, or contact your care team for immediate assistance."
            ),
            confidence=0.3,
            processing_time=0.0,
            timestamp=datetime.now(),
        )

    async def _execute_pipeline_with_circuit_breaker(
        self,
        pipeline: Pipeline,
        request: NormalizedRequest,
    ) -> PipelineResponse:
        """Execute pipeline with circuit breaker protection"""
        circuit_breaker = self.circuit_breakers.get(pipeline.id)

        if circuit_breaker and self._is_circuit_breaker_open(circuit_breaker):
            raise Exception(f"Circuit breaker open for pipeline {pipeline.id}")

        try:
            response = await pipeline.process(request)
            self._record_success(pipeline.id)
            return response
        except Exception as e:
            self._record_failure(pipeline.id)
            raise e

    def _is_circuit_breaker_open(self, circuit_breaker: CircuitBreakerState) -> bool:
        """Check if circuit breaker is open"""
        if not circuit_breaker.is_open:
            return False

        # Check if timeout has passed
        if circuit_breaker.next_retry_time and datetime.now() >= circuit_breaker.next_retry_time:
            # Reset circuit breaker
            circuit_breaker.is_open = False
            circuit_breaker.failure_count = 0
            return False

        return True

    def _record_success(self, pipeline_id: str) -> None:
        """Record pipeline success"""
        circuit_breaker = self.circuit_breakers.get(pipeline_id)
        if circuit_breaker:
            circuit_breaker.failure_count = 0
            circuit_breaker.is_open = False

    def _record_failure(self, pipeline_id: str) -> None:
        """Record pipeline failure and potentially open circuit breaker"""
        circuit_breaker = self.circuit_breakers.get(pipeline_id)
        if not circuit_breaker:
            return

        circuit_breaker.failure_count += 1
        circuit_breaker.last_failure_time = datetime.now()

        if circuit_breaker.failure_count >= self.failure_threshold:
            circuit_breaker.is_open = True
            circuit_breaker.next_retry_time = datetime.now() + timedelta(
                seconds=self.circuit_breaker_timeout
            )

    def _find_alternative_pipeline(self, pipeline_type: PipelineType) -> Optional[Pipeline]:
        """Find alternative pipeline of the same type"""
        # In a real implementation, this would check for backup pipelines
        # For now, return None as we don't have backup pipelines configured
        return None

    def _integrate_responses(self, responses: List[PipelineResponse]) -> str:
        """Integrate multiple pipeline responses into coherent output"""
        if not responses:
            return ''

        if len(responses) == 1:
            return responses[0].response_content

        # For multiple responses, combine them with clear sections
        sections = [response.response_content for response in responses]
        return '\n\n'.join(sections)

    def _prioritize_pipelines(self, pipelines: List[PipelineType]) -> List[PipelineType]:
        """Prioritize pipelines based on analysis"""
        # Primary intent pipeline should be first
        # For now, just return as-is since they're already ordered by priority
        return list(pipelines)

    def _matches_intent(self, intent: str, keywords: List[str]) -> bool:
        """Check if intent matches any of the keywords"""
        lower_intent = intent.lower()
        return any(keyword.lower() in lower_intent for keyword in keywords)

    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics for monitoring
        Implements Requirement 7.5: Performance monitoring
        """
        metrics: Dict[str, Any] = {}

        for pipeline_type, pipeline in self.pipelines.items():
            circuit_breaker = self.circuit_breakers.get(pipeline.id)
            metrics[pipeline_type.value] = {
                'is_available': pipeline.is_available,
                'average_response_time': pipeline.average_response_time,
                'success_rate': pipeline.success_rate,
                'circuit_breaker_open': circuit_breaker.is_open if circuit_breaker else False,
                'failure_count': circuit_breaker.failure_count if circuit_breaker else 0,
            }

        return metrics
