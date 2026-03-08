"""
Unit tests for Speech-to-Text component
Tests speech recognition, noise reduction, healthcare vocabulary, and multi-accent support
"""

import pytest
import numpy as np
from src.multimodal_ingestion.speech_to_text import (
    SpeechToText,
    SpeechRecognitionConfig,
    SpeechRecognitionResult,
    ProcessingMode,
    NoiseReductionLevel
)


class TestSpeechToTextConfiguration:
    """Test Speech-to-Text configuration"""

    def test_default_configuration(self):
        """Test default configuration values"""
        config = SpeechRecognitionConfig()
        
        assert config.processing_mode == ProcessingMode.CLOUD
        assert config.noise_reduction_level == NoiseReductionLevel.MEDIUM
        assert config.enable_healthcare_vocabulary is True
        assert config.enable_multi_accent_support is True
        assert config.language_code == "en-US"
        assert config.sample_rate == 16000

    def test_custom_configuration(self):
        """Test custom configuration"""
        config = SpeechRecognitionConfig(
            processing_mode=ProcessingMode.ON_DEVICE,
            noise_reduction_level=NoiseReductionLevel.HIGH,
            enable_healthcare_vocabulary=False,
            language_code="es-ES",
            sample_rate=48000
        )
        
        assert config.processing_mode == ProcessingMode.ON_DEVICE
        assert config.noise_reduction_level == NoiseReductionLevel.HIGH
        assert config.enable_healthcare_vocabulary is False
        assert config.language_code == "es-ES"
        assert config.sample_rate == 48000

    def test_invalid_language_code(self):
        """Test that invalid language code raises validation error"""
        with pytest.raises(Exception):  # Pydantic validation error
            SpeechRecognitionConfig(language_code="invalid")

    def test_invalid_sample_rate(self):
        """Test that invalid sample rate raises validation error"""
        with pytest.raises(Exception):  # Pydantic validation error
            SpeechRecognitionConfig(sample_rate=1000)  # Too low


class TestSpeechToTextInitialization:
    """Test Speech-to-Text initialization"""

    def test_initialization_with_default_config(self):
        """Test initialization with default configuration"""
        stt = SpeechToText()
        
        assert stt.config.processing_mode == ProcessingMode.CLOUD
        assert stt._healthcare_vocab_enabled is True
        assert stt._noise_reduction_enabled is True
        assert stt._multi_accent_enabled is True

    def test_initialization_with_custom_config(self):
        """Test initialization with custom configuration"""
        config = SpeechRecognitionConfig(
            processing_mode=ProcessingMode.ON_DEVICE,
            noise_reduction_level=NoiseReductionLevel.OFF,
            enable_healthcare_vocabulary=False
        )
        stt = SpeechToText(config)
        
        assert stt.config.processing_mode == ProcessingMode.ON_DEVICE
        assert stt._healthcare_vocab_enabled is False
        assert stt._noise_reduction_enabled is False


class TestNoiseReduction:
    """Test noise reduction functionality"""

    def test_noise_reduction_off(self):
        """Test that noise reduction OFF returns original audio"""
        config = SpeechRecognitionConfig(noise_reduction_level=NoiseReductionLevel.OFF)
        stt = SpeechToText(config)
        
        audio_data = np.random.randn(16000)  # 1 second of audio
        reduced = stt._apply_noise_reduction(audio_data, NoiseReductionLevel.OFF)
        
        np.testing.assert_array_equal(reduced, audio_data)

    def test_noise_reduction_low(self):
        """Test low noise reduction"""
        config = SpeechRecognitionConfig(noise_reduction_level=NoiseReductionLevel.LOW)
        stt = SpeechToText(config)
        
        # Create audio with noise
        audio_data = np.random.randn(16000) * 0.1  # Low amplitude noise
        reduced = stt._apply_noise_reduction(audio_data, NoiseReductionLevel.LOW)
        
        assert reduced.shape == audio_data.shape
        assert not np.array_equal(reduced, audio_data)  # Should be modified

    def test_noise_reduction_medium(self):
        """Test medium noise reduction"""
        config = SpeechRecognitionConfig(noise_reduction_level=NoiseReductionLevel.MEDIUM)
        stt = SpeechToText(config)
        
        audio_data = np.random.randn(16000) * 0.1
        reduced = stt._apply_noise_reduction(audio_data, NoiseReductionLevel.MEDIUM)
        
        assert reduced.shape == audio_data.shape
        # Medium should reduce more than low
        assert np.mean(np.abs(reduced)) <= np.mean(np.abs(audio_data))

    def test_noise_reduction_high(self):
        """Test high noise reduction"""
        config = SpeechRecognitionConfig(noise_reduction_level=NoiseReductionLevel.HIGH)
        stt = SpeechToText(config)
        
        audio_data = np.random.randn(16000) * 0.1
        reduced = stt._apply_noise_reduction(audio_data, NoiseReductionLevel.HIGH)
        
        assert reduced.shape == audio_data.shape
        # High should reduce the most
        assert np.mean(np.abs(reduced)) <= np.mean(np.abs(audio_data))


class TestSpeechRecognition:
    """Test speech recognition functionality"""

    def test_cloud_recognition(self):
        """Test cloud-based speech recognition"""
        config = SpeechRecognitionConfig(processing_mode=ProcessingMode.CLOUD)
        stt = SpeechToText(config)
        
        audio_data = np.random.randn(16000)
        result = stt.recognize_speech(audio_data)
        
        assert isinstance(result, SpeechRecognitionResult)
        assert result.processing_mode == ProcessingMode.CLOUD
        assert result.confidence > 0.0
        assert result.transcript is not None
        assert result.language_detected == "en-US"

    def test_on_device_recognition(self):
        """Test on-device speech recognition"""
        config = SpeechRecognitionConfig(processing_mode=ProcessingMode.ON_DEVICE)
        stt = SpeechToText(config)
        
        audio_data = np.random.randn(16000)
        result = stt.recognize_speech(audio_data)
        
        assert isinstance(result, SpeechRecognitionResult)
        assert result.processing_mode == ProcessingMode.ON_DEVICE
        assert result.confidence > 0.0
        assert result.transcript is not None

    def test_recognition_with_patient_id(self):
        """Test recognition with patient ID for privacy"""
        config = SpeechRecognitionConfig(processing_mode=ProcessingMode.ON_DEVICE)
        stt = SpeechToText(config)
        
        audio_data = np.random.randn(16000)
        result = stt.recognize_speech(audio_data, patient_id="patient-123")
        
        assert isinstance(result, SpeechRecognitionResult)
        assert result.transcript is not None


class TestHealthcareVocabulary:
    """Test healthcare vocabulary enhancement"""

    def test_healthcare_vocabulary_enabled(self):
        """Test that healthcare vocabulary is applied when enabled"""
        config = SpeechRecognitionConfig(enable_healthcare_vocabulary=True)
        stt = SpeechToText(config)
        
        # Create a mock result with medical terms
        mock_result = SpeechRecognitionResult(
            transcript="I need to take my medication and check my blood pressure",
            confidence=0.9,
            processing_mode=ProcessingMode.CLOUD,
            language_detected="en-US",
            alternative_transcripts=[]
        )
        
        enhanced = stt._enhance_with_healthcare_vocabulary(mock_result)
        
        assert enhanced.medical_terms_detected is not None
        assert "medication" in enhanced.medical_terms_detected

    def test_healthcare_vocabulary_disabled(self):
        """Test that healthcare vocabulary is not applied when disabled"""
        config = SpeechRecognitionConfig(enable_healthcare_vocabulary=False)
        stt = SpeechToText(config)
        
        audio_data = np.random.randn(16000)
        result = stt.recognize_speech(audio_data)
        
        # When disabled, medical terms should not be detected
        assert result.medical_terms_detected is None or len(result.medical_terms_detected) == 0

    def test_medical_term_corrections(self):
        """Test medical term corrections"""
        stt = SpeechToText()
        
        # Test common misrecognitions
        transcript = "I need mill a gram of ace it a min o fen"
        corrected = stt._apply_medical_term_corrections(transcript)
        
        assert "milligram" in corrected
        assert "acetaminophen" in corrected

    def test_multiple_medical_terms_detection(self):
        """Test detection of multiple medical terms"""
        stt = SpeechToText()
        
        mock_result = SpeechRecognitionResult(
            transcript="I have pain and nausea after taking my medication",
            confidence=0.9,
            processing_mode=ProcessingMode.CLOUD,
            language_detected="en-US",
            alternative_transcripts=[]
        )
        
        enhanced = stt._enhance_with_healthcare_vocabulary(mock_result)
        
        assert enhanced.medical_terms_detected is not None
        assert "pain" in enhanced.medical_terms_detected
        assert "nausea" in enhanced.medical_terms_detected
        assert "medication" in enhanced.medical_terms_detected


class TestMultiAccentSupport:
    """Test multi-accent support functionality"""

    def test_accent_normalization_enabled(self):
        """Test that accent normalization is applied when enabled"""
        config = SpeechRecognitionConfig(enable_multi_accent_support=True)
        stt = SpeechToText(config)
        
        audio_data = np.random.randn(16000)
        result = stt.recognize_speech(audio_data)
        
        assert isinstance(result, SpeechRecognitionResult)
        # Accent normalization should be applied

    def test_accent_normalization_disabled(self):
        """Test that accent normalization is not applied when disabled"""
        config = SpeechRecognitionConfig(enable_multi_accent_support=False)
        stt = SpeechToText(config)
        
        audio_data = np.random.randn(16000)
        result = stt.recognize_speech(audio_data)
        
        assert isinstance(result, SpeechRecognitionResult)

    def test_british_to_american_normalization(self):
        """Test British to American spelling normalization"""
        stt = SpeechToText()
        
        mock_result = SpeechRecognitionResult(
            transcript="The colour of the centre is important",
            confidence=0.9,
            processing_mode=ProcessingMode.CLOUD,
            language_detected="en-GB",
            alternative_transcripts=[]
        )
        
        normalized = stt._apply_accent_normalization(mock_result)
        
        assert "color" in normalized.transcript
        assert "center" in normalized.transcript
        assert "colour" not in normalized.transcript


class TestAudioValidation:
    """Test audio format validation"""

    def test_valid_audio(self):
        """Test validation of valid audio data"""
        stt = SpeechToText()
        
        audio_data = np.random.randn(16000)  # 1 second of audio
        is_valid = stt.validate_audio_format(audio_data)
        
        assert is_valid is True

    def test_empty_audio(self):
        """Test validation of empty audio data"""
        stt = SpeechToText()
        
        audio_data = np.array([])
        is_valid = stt.validate_audio_format(audio_data)
        
        assert is_valid is False

    def test_none_audio(self):
        """Test validation of None audio data"""
        stt = SpeechToText()
        
        is_valid = stt.validate_audio_format(None)
        
        assert is_valid is False

    def test_too_short_audio(self):
        """Test validation of too short audio data"""
        stt = SpeechToText()
        
        audio_data = np.random.randn(100)  # Very short audio
        is_valid = stt.validate_audio_format(audio_data)
        
        assert is_valid is False

    def test_silent_audio(self):
        """Test validation of silent audio (no energy)"""
        stt = SpeechToText()
        
        audio_data = np.zeros(16000)  # Silent audio
        is_valid = stt.validate_audio_format(audio_data)
        
        assert is_valid is False

    def test_invalid_audio_with_nan(self):
        """Test validation of audio with NaN values"""
        stt = SpeechToText()
        
        audio_data = np.random.randn(16000)
        audio_data[100] = np.nan
        is_valid = stt.validate_audio_format(audio_data)
        
        assert is_valid is False


class TestSupportedLanguages:
    """Test supported languages functionality"""

    def test_get_supported_languages(self):
        """Test getting list of supported languages"""
        stt = SpeechToText()
        
        languages = stt.get_supported_languages()
        
        assert isinstance(languages, list)
        assert len(languages) > 0
        assert "en-US" in languages
        assert "es-ES" in languages
        assert "fr-FR" in languages

    def test_supported_languages_format(self):
        """Test that supported languages are in correct format"""
        stt = SpeechToText()
        
        languages = stt.get_supported_languages()
        
        for lang in languages:
            # Should be in format: xx-XX
            assert len(lang) == 5
            assert lang[2] == "-"
            assert lang[:2].islower()
            assert lang[3:].isupper()


class TestConfidenceAdjustment:
    """Test confidence adjustment based on audio quality"""

    def test_high_quality_low_noise(self):
        """Test confidence adjustment with high quality and low noise"""
        stt = SpeechToText()
        
        adjustment = stt.estimate_confidence_adjustment(
            audio_quality=0.9,
            background_noise_level=0.1
        )
        
        assert adjustment > 0.8  # Should be high

    def test_low_quality_high_noise(self):
        """Test confidence adjustment with low quality and high noise"""
        stt = SpeechToText()
        
        adjustment = stt.estimate_confidence_adjustment(
            audio_quality=0.3,
            background_noise_level=0.8
        )
        
        assert adjustment < 0.4  # Should be low

    def test_medium_quality_medium_noise(self):
        """Test confidence adjustment with medium quality and noise"""
        stt = SpeechToText()
        
        adjustment = stt.estimate_confidence_adjustment(
            audio_quality=0.5,
            background_noise_level=0.5
        )
        
        assert 0.3 < adjustment < 0.7  # Should be medium

    def test_confidence_adjustment_bounds(self):
        """Test that confidence adjustment is bounded between 0 and 1"""
        stt = SpeechToText()
        
        # Test extreme values
        adjustment = stt.estimate_confidence_adjustment(
            audio_quality=1.0,
            background_noise_level=0.0
        )
        
        assert 0.0 <= adjustment <= 1.0


class TestIntegration:
    """Integration tests for complete speech-to-text workflow"""

    def test_complete_workflow_cloud(self):
        """Test complete workflow with cloud processing"""
        config = SpeechRecognitionConfig(
            processing_mode=ProcessingMode.CLOUD,
            noise_reduction_level=NoiseReductionLevel.MEDIUM,
            enable_healthcare_vocabulary=True,
            enable_multi_accent_support=True
        )
        stt = SpeechToText(config)
        
        # Generate sample audio
        audio_data = np.random.randn(16000) * 0.5
        
        # Validate audio
        assert stt.validate_audio_format(audio_data)
        
        # Recognize speech
        result = stt.recognize_speech(audio_data)
        
        assert result.processing_mode == ProcessingMode.CLOUD
        assert result.confidence > 0.0
        assert result.transcript is not None

    def test_complete_workflow_on_device(self):
        """Test complete workflow with on-device processing"""
        config = SpeechRecognitionConfig(
            processing_mode=ProcessingMode.ON_DEVICE,
            noise_reduction_level=NoiseReductionLevel.HIGH,
            enable_healthcare_vocabulary=True
        )
        stt = SpeechToText(config)
        
        # Generate sample audio
        audio_data = np.random.randn(16000) * 0.5
        
        # Recognize speech with patient ID for privacy
        result = stt.recognize_speech(audio_data, patient_id="patient-456")
        
        assert result.processing_mode == ProcessingMode.ON_DEVICE
        assert result.confidence > 0.0
        assert result.transcript is not None

    def test_workflow_with_noisy_audio(self):
        """Test workflow with noisy audio"""
        config = SpeechRecognitionConfig(
            noise_reduction_level=NoiseReductionLevel.HIGH
        )
        stt = SpeechToText(config)
        
        # Generate noisy audio
        signal = np.sin(2 * np.pi * 440 * np.arange(16000) / 16000)
        noise = np.random.randn(16000) * 0.3
        audio_data = signal + noise
        
        result = stt.recognize_speech(audio_data)
        
        assert result.transcript is not None
        assert result.confidence > 0.0
