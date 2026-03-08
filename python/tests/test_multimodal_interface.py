"""
Unit Tests for Multimodal Interface Component
Tests text, voice, and image input processing, response formatting,
and accessibility features.
"""

import pytest
from datetime import datetime

from src.patient_interaction.multimodal_interface import (
    MultimodalInterface,
    AudioBuffer,
    ImageBuffer,
    ImageFormat,
    Response,
    FormattedResponse
)
from src.models.interaction_record import OutputFormat
from src.models.patient_profile import AccessibilitySettings


@pytest.fixture
def multimodal_interface():
    """Fixture to create a MultimodalInterface instance"""
    return MultimodalInterface()


class TestProcessTextInput:
    """Tests for processTextInput method"""

    @pytest.mark.asyncio
    async def test_process_valid_text_input(self, multimodal_interface):
        """Test processing valid text input successfully"""
        text = 'What medications should I take today?'
        patient_id = 'patient-123'

        response = await multimodal_interface.process_text_input(text, patient_id)

        assert response is not None
        assert response.response_id.startswith('resp_')
        assert text in response.content
        assert patient_id in response.content
        assert response.format == OutputFormat.TEXT
        assert isinstance(response.timestamp, datetime)
        assert 'screen-reader-compatible' in response.accessibility_features
        assert 'keyboard-navigable' in response.accessibility_features

    @pytest.mark.asyncio
    async def test_empty_text_input_raises_error(self, multimodal_interface):
        """Test that empty text input raises ValueError"""
        patient_id = 'patient-123'

        with pytest.raises(ValueError, match='Text input cannot be empty'):
            await multimodal_interface.process_text_input('', patient_id)

    @pytest.mark.asyncio
    async def test_whitespace_only_text_input_raises_error(self, multimodal_interface):
        """Test that whitespace-only text input raises ValueError"""
        patient_id = 'patient-123'

        with pytest.raises(ValueError, match='Text input cannot be empty'):
            await multimodal_interface.process_text_input('   ', patient_id)

    @pytest.mark.asyncio
    async def test_missing_patient_id_raises_error(self, multimodal_interface):
        """Test that missing patient ID raises ValueError"""
        text = 'What medications should I take today?'

        with pytest.raises(ValueError, match='Patient ID is required'):
            await multimodal_interface.process_text_input(text, '')


class TestProcessVoiceInput:
    """Tests for processVoiceInput method"""

    @pytest.mark.asyncio
    async def test_process_valid_voice_input(self, multimodal_interface):
        """Test processing valid voice input successfully"""
        audio = AudioBuffer(
            data=b'\x00' * 1024,
            sample_rate=44100,
            channels=2,
            duration=5.5
        )
        patient_id = 'patient-456'

        response = await multimodal_interface.process_voice_input(audio, patient_id)

        assert response is not None
        assert response.response_id.startswith('resp_')
        assert '5.5s' in response.content
        assert '44100Hz' in response.content
        assert patient_id in response.content
        assert response.format == OutputFormat.AUDIO
        assert isinstance(response.timestamp, datetime)
        assert 'audio-output' in response.accessibility_features
        assert 'transcript-available' in response.accessibility_features

    @pytest.mark.asyncio
    async def test_empty_audio_buffer_raises_error(self, multimodal_interface):
        """Test that empty audio buffer raises ValueError"""
        audio = AudioBuffer(
            data=b'',
            sample_rate=44100,
            channels=2,
            duration=0
        )
        patient_id = 'patient-456'

        with pytest.raises(ValueError, match='Audio buffer cannot be empty'):
            await multimodal_interface.process_voice_input(audio, patient_id)

    @pytest.mark.asyncio
    async def test_missing_patient_id_for_voice_raises_error(self, multimodal_interface):
        """Test that missing patient ID raises ValueError"""
        audio = AudioBuffer(
            data=b'\x00' * 1024,
            sample_rate=44100,
            channels=2,
            duration=5.5
        )

        with pytest.raises(ValueError, match='Patient ID is required'):
            await multimodal_interface.process_voice_input(audio, '')


class TestProcessImageInput:
    """Tests for processImageInput method"""

    @pytest.mark.asyncio
    async def test_process_valid_image_input(self, multimodal_interface):
        """Test processing valid image input successfully"""
        image = ImageBuffer(
            data=b'\x00' * 2048,
            width=800,
            height=600,
            format=ImageFormat.JPEG
        )
        patient_id = 'patient-789'

        response = await multimodal_interface.process_image_input(image, patient_id)

        assert response is not None
        assert response.response_id.startswith('resp_')
        assert '800x600' in response.content
        assert 'jpeg' in response.content
        assert patient_id in response.content
        assert response.format == OutputFormat.VISUAL
        assert isinstance(response.timestamp, datetime)
        assert 'alt-text-provided' in response.accessibility_features
        assert 'high-contrast-available' in response.accessibility_features

    @pytest.mark.asyncio
    async def test_empty_image_buffer_raises_error(self, multimodal_interface):
        """Test that empty image buffer raises ValueError"""
        image = ImageBuffer(
            data=b'',
            width=0,
            height=0,
            format=ImageFormat.JPEG
        )
        patient_id = 'patient-789'

        with pytest.raises(ValueError, match='Image buffer cannot be empty'):
            await multimodal_interface.process_image_input(image, patient_id)

    @pytest.mark.asyncio
    async def test_missing_patient_id_for_image_raises_error(self, multimodal_interface):
        """Test that missing patient ID raises ValueError"""
        image = ImageBuffer(
            data=b'\x00' * 2048,
            width=800,
            height=600,
            format=ImageFormat.JPEG
        )

        with pytest.raises(ValueError, match='Patient ID is required'):
            await multimodal_interface.process_image_input(image, '')

    @pytest.mark.asyncio
    async def test_handle_different_image_formats(self, multimodal_interface):
        """Test handling different image formats"""
        formats = [ImageFormat.JPEG, ImageFormat.PNG, ImageFormat.WEBP]
        patient_id = 'patient-789'

        for fmt in formats:
            image = ImageBuffer(
                data=b'\x00' * 2048,
                width=800,
                height=600,
                format=fmt
            )

            response = await multimodal_interface.process_image_input(image, patient_id)
            assert fmt.value in response.content


class TestFormatResponse:
    """Tests for formatResponse method"""

    @pytest.mark.asyncio
    async def test_format_response_as_text(self, multimodal_interface):
        """Test formatting response as text"""
        content = 'Take your medication at 8 AM'
        format_type = OutputFormat.TEXT

        response = await multimodal_interface.format_response(content, format_type)

        assert response is not None
        assert response.response_id.startswith('resp_')
        assert response.content == content
        assert response.format == OutputFormat.TEXT
        assert isinstance(response.timestamp, datetime)
        assert 'screen-reader-compatible' in response.accessibility_features
        assert 'keyboard-navigable' in response.accessibility_features
        assert 'resizable-text' in response.accessibility_features

    @pytest.mark.asyncio
    async def test_format_response_as_audio(self, multimodal_interface):
        """Test formatting response as audio"""
        content = 'Take your medication at 8 AM'
        format_type = OutputFormat.AUDIO

        response = await multimodal_interface.format_response(content, format_type)

        assert response.format == OutputFormat.AUDIO
        assert 'audio-output' in response.accessibility_features
        assert 'transcript-available' in response.accessibility_features
        assert 'playback-controls' in response.accessibility_features

    @pytest.mark.asyncio
    async def test_format_response_as_visual(self, multimodal_interface):
        """Test formatting response as visual"""
        content = 'Medication schedule diagram'
        format_type = OutputFormat.VISUAL

        response = await multimodal_interface.format_response(content, format_type)

        assert response.format == OutputFormat.VISUAL
        assert 'alt-text-provided' in response.accessibility_features
        assert 'high-contrast-available' in response.accessibility_features
        assert 'zoom-support' in response.accessibility_features

    @pytest.mark.asyncio
    async def test_format_response_as_mixed(self, multimodal_interface):
        """Test formatting response as mixed"""
        content = 'Comprehensive care instructions'
        format_type = OutputFormat.MIXED

        response = await multimodal_interface.format_response(content, format_type)

        assert response.format == OutputFormat.MIXED
        assert 'screen-reader-compatible' in response.accessibility_features
        assert 'audio-output' in response.accessibility_features
        assert 'alt-text-provided' in response.accessibility_features
        assert 'keyboard-navigable' in response.accessibility_features
        assert 'high-contrast-available' in response.accessibility_features

    @pytest.mark.asyncio
    async def test_empty_content_raises_error(self, multimodal_interface):
        """Test that empty content raises ValueError"""
        format_type = OutputFormat.TEXT

        with pytest.raises(ValueError, match='Content cannot be empty'):
            await multimodal_interface.format_response('', format_type)

    @pytest.mark.asyncio
    async def test_whitespace_only_content_raises_error(self, multimodal_interface):
        """Test that whitespace-only content raises ValueError"""
        format_type = OutputFormat.TEXT

        with pytest.raises(ValueError, match='Content cannot be empty'):
            await multimodal_interface.format_response('   ', format_type)


class TestGetAccessibilityOptions:
    """Tests for getAccessibilityOptions method"""

    def test_return_accessibility_settings_for_valid_patient_id(self, multimodal_interface):
        """Test returning accessibility settings for valid patient ID"""
        patient_id = 'patient-123'

        settings = multimodal_interface.get_accessibility_options(patient_id)

        assert settings is not None
        assert hasattr(settings, 'screen_reader_enabled')
        assert hasattr(settings, 'high_contrast_mode')
        assert hasattr(settings, 'font_size')
        assert hasattr(settings, 'voice_output_enabled')
        assert hasattr(settings, 'keyboard_navigation_only')
        assert isinstance(settings.screen_reader_enabled, bool)
        assert isinstance(settings.high_contrast_mode, bool)
        assert settings.font_size in ['small', 'medium', 'large', 'extra-large']
        assert isinstance(settings.voice_output_enabled, bool)
        assert isinstance(settings.keyboard_navigation_only, bool)

    def test_missing_patient_id_raises_error(self, multimodal_interface):
        """Test that missing patient ID raises ValueError"""
        with pytest.raises(ValueError, match='Patient ID is required'):
            multimodal_interface.get_accessibility_options('')

    def test_return_default_settings(self, multimodal_interface):
        """Test returning default accessibility settings"""
        patient_id = 'patient-123'

        settings = multimodal_interface.get_accessibility_options(patient_id)

        assert settings.screen_reader_enabled is False
        assert settings.high_contrast_mode is False
        assert settings.font_size == 'medium'
        assert settings.voice_output_enabled is False
        assert settings.keyboard_navigation_only is False
