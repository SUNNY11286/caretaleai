"""
Property-Based Tests for Multimodal Interface Component

Feature: caretale-ai
Property 1: Multimodal Input Processing Completeness

For any valid patient input (text, voice, or image), the Multimodal Interface
should successfully process the input and generate an appropriate response in
the requested output format(s).

**Validates: Requirements 1.1, 1.2, 1.3, 1.4**
"""

import pytest
from hypothesis import given, strategies as st, assume
from datetime import datetime

from src.patient_interaction.multimodal_interface import (
    MultimodalInterface,
    AudioBuffer,
    ImageBuffer,
    ImageFormat,
    Response,
)
from src.models.interaction_record import OutputFormat


# Custom strategies for generating valid inputs
@st.composite
def audio_buffer_strategy(draw):
    """Generate valid AudioBuffer instances"""
    # Generate audio data between 1KB and 100KB
    data_size = draw(st.integers(min_value=1024, max_value=102400))
    data = draw(st.binary(min_size=data_size, max_size=data_size))
    
    # Common sample rates
    sample_rate = draw(st.sampled_from([8000, 16000, 22050, 44100, 48000]))
    
    # Mono or stereo
    channels = draw(st.sampled_from([1, 2]))
    
    # Duration between 0.1 and 60 seconds
    duration = draw(st.floats(min_value=0.1, max_value=60.0))
    
    return AudioBuffer(
        data=data,
        sample_rate=sample_rate,
        channels=channels,
        duration=duration
    )


@st.composite
def image_buffer_strategy(draw):
    """Generate valid ImageBuffer instances"""
    # Generate image data between 1KB and 500KB
    data_size = draw(st.integers(min_value=1024, max_value=512000))
    data = draw(st.binary(min_size=data_size, max_size=data_size))
    
    # Common image dimensions
    width = draw(st.integers(min_value=100, max_value=4096))
    height = draw(st.integers(min_value=100, max_value=4096))
    
    # Supported formats
    format = draw(st.sampled_from([ImageFormat.JPEG, ImageFormat.PNG, ImageFormat.WEBP]))
    
    return ImageBuffer(
        data=data,
        width=width,
        height=height,
        format=format
    )


@st.composite
def patient_id_strategy(draw):
    """Generate valid patient IDs"""
    # Patient IDs: alphanumeric with hyphens, 5-50 characters
    prefix = draw(st.sampled_from(['patient', 'pat', 'p']))
    suffix = draw(st.text(
        alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd'), whitelist_characters='-'),
        min_size=1,
        max_size=45
    ))
    return f'{prefix}-{suffix}'


class TestMultimodalInputProcessingCompleteness:
    """
    Property 1: Multimodal Input Processing Completeness
    
    For any valid patient input (text, voice, or image), the Multimodal Interface
    should successfully process the input and generate an appropriate response in
    the requested output format(s).
    
    **Validates: Requirements 1.1, 1.2, 1.3, 1.4**
    """

    @given(
        text=st.text(min_size=1, max_size=5000),
        patient_id=patient_id_strategy()
    )
    @pytest.mark.asyncio
    async def test_property_text_input_processing_completeness(self, text, patient_id):
        """
        Property 1.1: Text Input Processing
        
        **Validates: Requirement 1.1**
        
        WHEN a patient provides text input, THE Multimodal_Interface SHALL
        process and respond with appropriate text output.
        """
        # Ensure text is not just whitespace
        assume(text.strip())
        
        interface = MultimodalInterface()
        
        # Process text input
        response = await interface.process_text_input(text, patient_id)
        
        # Verify response is generated
        assert response is not None, "Response should be generated for valid text input"
        assert isinstance(response, Response), "Response should be a Response object"
        
        # Verify response has required fields
        assert response.response_id, "Response should have a response ID"
        assert response.content, "Response should have content"
        assert isinstance(response.timestamp, datetime), "Response should have a timestamp"
        
        # Verify appropriate output format (Requirement 1.1)
        assert response.format == OutputFormat.TEXT, \
            "Text input should produce TEXT format output"
        
        # Verify output format options are provided (Requirement 1.4)
        assert response.accessibility_features, \
            "Response should include accessibility features"
        assert isinstance(response.accessibility_features, list), \
            "Accessibility features should be a list"
        assert len(response.accessibility_features) > 0, \
            "At least one accessibility feature should be provided"

    @given(
        audio=audio_buffer_strategy(),
        patient_id=patient_id_strategy()
    )
    @pytest.mark.asyncio
    async def test_property_voice_input_processing_completeness(self, audio, patient_id):
        """
        Property 1.2: Voice Input Processing
        
        **Validates: Requirement 1.2**
        
        WHEN a patient provides voice input, THE Multimodal_Interface SHALL
        convert speech to text and provide voice response options.
        """
        interface = MultimodalInterface()
        
        # Process voice input
        response = await interface.process_voice_input(audio, patient_id)
        
        # Verify response is generated
        assert response is not None, "Response should be generated for valid voice input"
        assert isinstance(response, Response), "Response should be a Response object"
        
        # Verify response has required fields
        assert response.response_id, "Response should have a response ID"
        assert response.content, "Response should have content"
        assert isinstance(response.timestamp, datetime), "Response should have a timestamp"
        
        # Verify appropriate output format (Requirement 1.2)
        assert response.format == OutputFormat.AUDIO, \
            "Voice input should produce AUDIO format output"
        
        # Verify voice response options are provided (Requirement 1.2, 1.4)
        assert response.accessibility_features, \
            "Response should include accessibility features"
        assert 'audio-output' in response.accessibility_features or \
               'transcript-available' in response.accessibility_features, \
            "Voice response should include audio output or transcript options"

    @given(
        image=image_buffer_strategy(),
        patient_id=patient_id_strategy()
    )
    @pytest.mark.asyncio
    async def test_property_image_input_processing_completeness(self, image, patient_id):
        """
        Property 1.3: Image Input Processing
        
        **Validates: Requirement 1.3**
        
        WHEN a patient provides image input, THE Multimodal_Interface SHALL
        analyze the image and provide relevant guidance.
        """
        interface = MultimodalInterface()
        
        # Process image input
        response = await interface.process_image_input(image, patient_id)
        
        # Verify response is generated
        assert response is not None, "Response should be generated for valid image input"
        assert isinstance(response, Response), "Response should be a Response object"
        
        # Verify response has required fields
        assert response.response_id, "Response should have a response ID"
        assert response.content, "Response should have content"
        assert isinstance(response.timestamp, datetime), "Response should have a timestamp"
        
        # Verify appropriate output format (Requirement 1.3)
        assert response.format == OutputFormat.VISUAL, \
            "Image input should produce VISUAL format output"
        
        # Verify output format options are provided (Requirement 1.4)
        assert response.accessibility_features, \
            "Response should include accessibility features"
        assert 'alt-text-provided' in response.accessibility_features or \
               'high-contrast-available' in response.accessibility_features, \
            "Visual response should include alt-text or high-contrast options"

    @given(
        content=st.text(min_size=1, max_size=5000),
        format=st.sampled_from([OutputFormat.TEXT, OutputFormat.AUDIO, OutputFormat.VISUAL, OutputFormat.MIXED])
    )
    @pytest.mark.asyncio
    async def test_property_output_format_options_provided(self, content, format):
        """
        Property 1.4: Output Format Options
        
        **Validates: Requirement 1.4**
        
        WHEN generating outputs, THE Multimodal_Interface SHALL offer multiple
        format options including text, audio, and visual aids.
        """
        # Ensure content is not just whitespace
        assume(content.strip())
        
        interface = MultimodalInterface()
        
        # Format response in requested format
        response = await interface.format_response(content, format)
        
        # Verify response is generated
        assert response is not None, "Response should be generated for any valid format"
        assert response.format == format, "Response should match requested format"
        
        # Verify accessibility features are provided for the format
        assert response.accessibility_features, \
            "Response should include accessibility features"
        assert isinstance(response.accessibility_features, list), \
            "Accessibility features should be a list"
        assert len(response.accessibility_features) > 0, \
            "At least one accessibility feature should be provided"
        
        # Verify format-specific features
        if format == OutputFormat.TEXT:
            assert any(feat in response.accessibility_features 
                      for feat in ['screen-reader-compatible', 'keyboard-navigable', 'resizable-text']), \
                "TEXT format should include text-specific accessibility features"
        elif format == OutputFormat.AUDIO:
            assert any(feat in response.accessibility_features 
                      for feat in ['audio-output', 'transcript-available', 'playback-controls']), \
                "AUDIO format should include audio-specific accessibility features"
        elif format == OutputFormat.VISUAL:
            assert any(feat in response.accessibility_features 
                      for feat in ['alt-text-provided', 'high-contrast-available', 'zoom-support']), \
                "VISUAL format should include visual-specific accessibility features"
        elif format == OutputFormat.MIXED:
            # MIXED format should include features from multiple modalities
            assert len(response.accessibility_features) >= 3, \
                "MIXED format should include features from multiple modalities"
