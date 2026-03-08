"""
Unit tests for AI Orchestrator component
"""

import pytest
from datetime import datetime
from typing import Optional

from src.ai_orchestration.ai_orchestrator import (
    AIOrchestrator,
    PipelineType,
    RequestAnalysis,
    CoordinatedResponse,
)
from src.models.interaction_record import (
    NormalizedRequest,
    InputType,
    PipelineResponse,
)


class MockPipeline:
    """Mock pipeline implementation for testing"""

    def __init__(self, pipeline_type: PipelineType, pipeline_id: Optional[str] = None):
        self.type = pipeline_type
        self.id = pipeline_id or f"{pipeline_type.value}_pipeline"
        self.name = f"{pipeline_type.value} Pipeline"
        self.is_available = True
        self.average_response_time = 100.0
        self.success_rate = 0.95
        self._should_fail = False

    def set_should_fail(self, fail: bool) -> None:
        """Set whether this pipeline should fail"""
        self._should_fail = fail

    async def process(self, request: NormalizedRequest) -> PipelineResponse:
        """Process a request and return a response"""
        if self._should_fail:
            raise Exception("Pipeline processing failed")

        return PipelineResponse(
            pipeline_id=self.id,
            pipeline_name=self.name,
            response_content=f"Response from {self.name} for: {request.original_input}",
            confidence=0.9,
            sources=["test-source-1"],
            processing_time=self.average_response_time,
            timestamp=datetime.now(),
        )


class TestAIOrchestrator:
    """Test suite for AI Orchestrator"""

    def setup_method(self):
        """Set up test fixtures"""
        self.orchestrator = AIOrchestrator()

    def test_register_pipeline(self):
        """Test pipeline registration"""
        pipeline = MockPipeline(PipelineType.CARE_STORY)
        self.orchestrator.register_pipeline(pipeline)

        metrics = self.orchestrator.get_performance_metrics()
        assert PipelineType.CARE_STORY.value in metrics
        assert metrics[PipelineType.CARE_STORY.value]["is_available"] is True

    def test_initialize_circuit_breaker(self):
        """Test circuit breaker initialization for registered pipeline"""
        pipeline = MockPipeline(PipelineType.MEDICATION_CLARIFICATION)
        self.orchestrator.register_pipeline(pipeline)

        metrics = self.orchestrator.get_performance_metrics()
        assert metrics[PipelineType.MEDICATION_CLARIFICATION.value]["circuit_breaker_open"] is False
        assert metrics[PipelineType.MEDICATION_CLARIFICATION.value]["failure_count"] == 0

    def test_analyze_care_story_intent(self):
        """Test identification of care story intent"""
        request = NormalizedRequest(
            request_id="req-1",
            patient_id="patient-1",
            original_input="Show me my discharge instructions",
            input_type=InputType.TEXT,
            intent="care story",
            entities={},
            context={},
            timestamp=datetime.now(),
        )

        analysis = self.orchestrator.analyze_request(request)

        assert analysis.primary_intent == "care_story_generation"
        assert PipelineType.CARE_STORY in analysis.suggested_pipelines
        assert analysis.complexity == "simple"
        assert analysis.requires_multiple_pipelines is False

    def test_analyze_medication_intent(self):
        """Test identification of medication clarification intent"""
        request = NormalizedRequest(
            request_id="req-2",
            patient_id="patient-1",
            original_input="What is this medication for?",
            input_type=InputType.TEXT,
            intent="medication question",
            entities={},
            context={},
            timestamp=datetime.now(),
        )

        analysis = self.orchestrator.analyze_request(request)

        assert analysis.primary_intent == "medication_clarification"
        assert PipelineType.MEDICATION_CLARIFICATION in analysis.suggested_pipelines

    def test_analyze_understanding_verification_intent(self):
        """Test identification of understanding verification intent"""
        request = NormalizedRequest(
            request_id="req-3",
            patient_id="patient-1",
            original_input="I am confused about what to do",
            input_type=InputType.TEXT,
            intent="confused about instructions",
            entities={},
            context={},
            timestamp=datetime.now(),
        )

        analysis = self.orchestrator.analyze_request(request)

        assert analysis.primary_intent == "understanding_verification"
        assert PipelineType.UNDERSTANDING_VERIFICATION in analysis.suggested_pipelines

    def test_analyze_follow_up_intent(self):
        """Test identification of follow-up intent"""
        request = NormalizedRequest(
            request_id="req-4",
            patient_id="patient-1",
            original_input="When is my next appointment?",
            input_type=InputType.TEXT,
            intent="appointment reminder",
            entities={},
            context={},
            timestamp=datetime.now(),
        )

        analysis = self.orchestrator.analyze_request(request)

        assert analysis.primary_intent == "follow_up"
        assert PipelineType.FOLLOW_UP in analysis.suggested_pipelines

    def test_detect_multi_pipeline_needs(self):
        """Test detection of multi-pipeline requirements"""
        request = NormalizedRequest(
            request_id="req-5",
            patient_id="patient-1",
            original_input="Show me my care plan and medication schedule",
            input_type=InputType.TEXT,
            intent="care story with medication",
            entities={},
            context={},
            timestamp=datetime.now(),
        )

        analysis = self.orchestrator.analyze_request(request)

        assert analysis.requires_multiple_pipelines is True
        assert len(analysis.suggested_pipelines) > 1
        assert analysis.complexity == "moderate"

    def test_default_to_understanding_verification(self):
        """Test default routing to understanding verification for unclear intent"""
        request = NormalizedRequest(
            request_id="req-6",
            patient_id="patient-1",
            original_input="Hello",
            input_type=InputType.TEXT,
            intent="greeting",
            entities={},
            context={},
            timestamp=datetime.now(),
        )

        analysis = self.orchestrator.analyze_request(request)

        assert analysis.primary_intent == "general_query"
        assert PipelineType.UNDERSTANDING_VERIFICATION in analysis.suggested_pipelines
        assert analysis.confidence < 0.8

    @pytest.mark.asyncio
    async def test_route_to_single_pipeline(self):
        """Test routing to single pipeline for simple request"""
        # Register all pipeline types
        self.orchestrator.register_pipeline(MockPipeline(PipelineType.CARE_STORY))
        self.orchestrator.register_pipeline(MockPipeline(PipelineType.MEDICATION_CLARIFICATION))
        self.orchestrator.register_pipeline(MockPipeline(PipelineType.UNDERSTANDING_VERIFICATION))
        self.orchestrator.register_pipeline(MockPipeline(PipelineType.FOLLOW_UP))

        request = NormalizedRequest(
            request_id="req-7",
            patient_id="patient-1",
            original_input="Show me my medications",
            input_type=InputType.TEXT,
            intent="medication list",
            entities={},
            context={},
            timestamp=datetime.now(),
        )

        analysis = self.orchestrator.analyze_request(request)
        routes = await self.orchestrator.route_to_pipeline(analysis, request)

        assert len(routes) == 1
        assert routes[0].routing_reason == "primary_intent"
        assert routes[0].priority == 1

    @pytest.mark.asyncio
    async def test_route_to_multiple_pipelines(self):
        """Test routing to multiple pipelines for complex request"""
        # Register all pipeline types
        self.orchestrator.register_pipeline(MockPipeline(PipelineType.CARE_STORY))
        self.orchestrator.register_pipeline(MockPipeline(PipelineType.MEDICATION_CLARIFICATION))
        self.orchestrator.register_pipeline(MockPipeline(PipelineType.UNDERSTANDING_VERIFICATION))
        self.orchestrator.register_pipeline(MockPipeline(PipelineType.FOLLOW_UP))

        request = NormalizedRequest(
            request_id="req-8",
            patient_id="patient-1",
            original_input="Show me my care plan with medication reminders",
            input_type=InputType.TEXT,
            intent="care story with medication and reminder",
            entities={},
            context={},
            timestamp=datetime.now(),
        )

        analysis = self.orchestrator.analyze_request(request)
        routes = await self.orchestrator.route_to_pipeline(analysis, request)

        assert len(routes) > 1
        assert routes[0].routing_reason == "primary_intent"
        assert routes[1].routing_reason == "secondary_intent"

    @pytest.mark.asyncio
    async def test_coordinate_multiple_pipelines(self):
        """Test coordination of multiple pipelines"""
        pipelines = [
            MockPipeline(PipelineType.CARE_STORY),
            MockPipeline(PipelineType.MEDICATION_CLARIFICATION),
        ]

        request = NormalizedRequest(
            request_id="req-9",
            patient_id="patient-1",
            original_input="Tell me about my care plan and medications",
            input_type=InputType.TEXT,
            intent="care story with medication",
            entities={},
            context={},
            timestamp=datetime.now(),
        )

        result = await self.orchestrator.coordinate_multi_pipeline(pipelines, request)

        assert len(result.responses) == 2
        assert "Response from" in result.integrated_content
        assert result.confidence > 0
        assert len(result.sources) > 0
        assert result.processing_time >= 0

    @pytest.mark.asyncio
    async def test_handle_partial_pipeline_failures(self):
        """Test graceful handling of partial pipeline failures"""
        pipeline1 = MockPipeline(PipelineType.CARE_STORY)
        pipeline2 = MockPipeline(PipelineType.MEDICATION_CLARIFICATION)
        pipeline2.set_should_fail(True)

        pipelines = [pipeline1, pipeline2]

        request = NormalizedRequest(
            request_id="req-10",
            patient_id="patient-1",
            original_input="Tell me about my care",
            input_type=InputType.TEXT,
            intent="care story",
            entities={},
            context={},
            timestamp=datetime.now(),
        )

        result = await self.orchestrator.coordinate_multi_pipeline(pipelines, request)

        # Should still have response from successful pipeline
        assert len(result.responses) > 0
        assert result.integrated_content

    @pytest.mark.asyncio
    async def test_integrate_multiple_responses(self):
        """Test integration of responses from multiple pipelines"""
        pipelines = [
            MockPipeline(PipelineType.CARE_STORY),
            MockPipeline(PipelineType.FOLLOW_UP),
        ]

        request = NormalizedRequest(
            request_id="req-11",
            patient_id="patient-1",
            original_input="What should I do and when?",
            input_type=InputType.TEXT,
            intent="care story with follow-up",
            entities={},
            context={},
            timestamp=datetime.now(),
        )

        result = await self.orchestrator.coordinate_multi_pipeline(pipelines, request)

        assert "care_story" in result.integrated_content
        assert "follow_up" in result.integrated_content

    @pytest.mark.asyncio
    async def test_handle_failover(self):
        """Test pipeline failover handling"""
        failed_pipeline = MockPipeline(PipelineType.CARE_STORY)
        failed_pipeline.set_should_fail(True)

        request = NormalizedRequest(
            request_id="req-12",
            patient_id="patient-1",
            original_input="Show me my care plan",
            input_type=InputType.TEXT,
            intent="care story",
            entities={},
            context={},
            timestamp=datetime.now(),
        )

        fallback_response = await self.orchestrator.handle_failover(failed_pipeline, request)

        assert fallback_response.pipeline_id == "fallback"
        assert "trouble processing" in fallback_response.response_content
        assert fallback_response.confidence < 0.5

    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_after_failures(self):
        """Test circuit breaker opens after multiple failures"""
        pipeline = MockPipeline(PipelineType.MEDICATION_CLARIFICATION)
        pipeline.set_should_fail(True)
        self.orchestrator.register_pipeline(pipeline)

        request = NormalizedRequest(
            request_id="req-13",
            patient_id="patient-1",
            original_input="What is this medication?",
            input_type=InputType.TEXT,
            intent="medication question",
            entities={},
            context={},
            timestamp=datetime.now(),
        )

        # Trigger multiple failures
        for _ in range(3):
            await self.orchestrator.handle_failover(pipeline, request)

        metrics = self.orchestrator.get_performance_metrics()
        assert metrics[PipelineType.MEDICATION_CLARIFICATION.value]["circuit_breaker_open"] is True
        assert metrics[PipelineType.MEDICATION_CLARIFICATION.value]["failure_count"] >= 3

    def test_performance_metrics(self):
        """Test performance metrics for all pipelines"""
        self.orchestrator.register_pipeline(MockPipeline(PipelineType.CARE_STORY))
        self.orchestrator.register_pipeline(MockPipeline(PipelineType.MEDICATION_CLARIFICATION))

        metrics = self.orchestrator.get_performance_metrics()

        assert PipelineType.CARE_STORY.value in metrics
        assert PipelineType.MEDICATION_CLARIFICATION.value in metrics
        assert metrics[PipelineType.CARE_STORY.value]["is_available"] is True
        assert metrics[PipelineType.CARE_STORY.value]["average_response_time"] > 0
        assert metrics[PipelineType.CARE_STORY.value]["success_rate"] > 0

    def test_circuit_breaker_status_in_metrics(self):
        """Test circuit breaker status tracking in metrics"""
        pipeline = MockPipeline(PipelineType.UNDERSTANDING_VERIFICATION)
        self.orchestrator.register_pipeline(pipeline)

        metrics = self.orchestrator.get_performance_metrics()

        assert metrics[PipelineType.UNDERSTANDING_VERIFICATION.value]["circuit_breaker_open"] is False
        assert metrics[PipelineType.UNDERSTANDING_VERIFICATION.value]["failure_count"] == 0
