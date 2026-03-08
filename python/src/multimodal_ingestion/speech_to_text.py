"""
Speech-to-Text Component
Converts patient voice inputs to text for processing with healthcare-specific features.

Features:
- Healthcare vocabulary recognition
- Noise reduction
- Multi-accent support
- Privacy-preserving processing option

References: Design Document Multimodal Ingestion Layer
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, List, Dict
import numpy as np
from pydantic import BaseModel, Field


class ProcessingMode(str, Enum):
    """Speech processing mode"""
    CLOUD = "cloud"  # Cloud-based ASR with full features
    ON_DEVICE = "on_device"  # Privacy-preserving on-device processing


class NoiseReductionLevel(str, Enum):
    """Noise reduction intensity level"""
    OFF = "off"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class SpeechRecognitionConfig(BaseModel):
    """Configuration for speech recognition"""
    processing_mode: ProcessingMode = ProcessingMode.CLOUD
    noise_reduction_level: NoiseReductionLevel = NoiseReductionLevel.MEDIUM
    enable_healthcare_vocabulary: bool = True
    enable_multi_accent_support: bool = True
    language_code: str = Field(default="en-US", pattern=r"^[a-z]{2}-[A-Z]{2}$")
    sample_rate: int = Field(default=16000, ge=8000, le=48000)
    enable_profanity_filter: bool = False
    enable_automatic_punctuation: bool = True


@dataclass
class SpeechRecognitionResult:
    """Result of speech recognition"""
    transcript: str
    confidence: float  # 0.0 to 1.0
    processing_mode: ProcessingMode
    language_detected: str
    alternative_transcripts: List[str]
    word_timestamps: Optional[List[Dict[str, float]]] = None
    medical_terms_detected: Optional[List[str]] = None


class SpeechToText:
    """
    Speech-to-Text Component
    Converts patient voice inputs to text with healthcare-specific optimizations
    """

    # Healthcare vocabulary for enhanced recognition
    HEALTHCARE_VOCABULARY = {
        # Common medical terms
        "medication", "prescription", "dosage", "milligram", "tablet",
        "capsule", "injection", "inhaler", "antibiotic", "painkiller",
        # Symptoms
        "pain", "nausea", "dizziness", "fever", "headache", "fatigue",
        "shortness of breath", "chest pain", "abdominal pain",
        # Body parts
        "heart", "lung", "kidney", "liver", "stomach", "intestine",
        "brain", "spine", "joint", "muscle", "bone",
        # Procedures
        "surgery", "operation", "procedure", "examination", "test",
        "scan", "x-ray", "MRI", "CT scan", "ultrasound",
        # Care instructions
        "follow-up", "appointment", "discharge", "recovery", "rehabilitation",
        "physical therapy", "wound care", "diet", "exercise", "rest",
        # Common medications
        "aspirin", "ibuprofen", "acetaminophen", "insulin", "metformin",
        "lisinopril", "atorvastatin", "omeprazole", "albuterol",
    }

    def __init__(self, config: Optional[SpeechRecognitionConfig] = None):
        """
        Initialize Speech-to-Text component
        
        Args:
            config: Speech recognition configuration
        """
        self.config = config or SpeechRecognitionConfig()
        self._initialize_recognizer()

    def _initialize_recognizer(self) -> None:
        """Initialize the speech recognition engine based on configuration"""
        # In a real implementation, this would initialize the actual ASR engine
        # For now, we'll set up the configuration
        self._healthcare_vocab_enabled = self.config.enable_healthcare_vocabulary
        self._noise_reduction_enabled = self.config.noise_reduction_level != NoiseReductionLevel.OFF
        self._multi_accent_enabled = self.config.enable_multi_accent_support

    def recognize_speech(
        self,
        audio_data: np.ndarray,
        patient_id: Optional[str] = None
    ) -> SpeechRecognitionResult:
        """
        Convert speech audio to text
        
        Args:
            audio_data: Audio data as numpy array
            patient_id: Optional patient ID for privacy-preserving processing
            
        Returns:
            Speech recognition result with transcript and metadata
        """
        # Apply noise reduction if enabled
        if self._noise_reduction_enabled:
            audio_data = self._apply_noise_reduction(
                audio_data,
                self.config.noise_reduction_level
            )

        # Perform speech recognition based on processing mode
        if self.config.processing_mode == ProcessingMode.ON_DEVICE:
            result = self._recognize_on_device(audio_data)
        else:
            result = self._recognize_cloud(audio_data)

        # Enhance with healthcare vocabulary if enabled
        if self._healthcare_vocab_enabled:
            result = self._enhance_with_healthcare_vocabulary(result)

        # Apply multi-accent support if enabled
        if self._multi_accent_enabled:
            result = self._apply_accent_normalization(result)

        return result

    def _apply_noise_reduction(
        self,
        audio_data: np.ndarray,
        level: NoiseReductionLevel
    ) -> np.ndarray:
        """
        Apply noise reduction to audio data
        
        Args:
            audio_data: Raw audio data
            level: Noise reduction level
            
        Returns:
            Noise-reduced audio data
        """
        if level == NoiseReductionLevel.OFF:
            return audio_data

        # Noise reduction strength based on level
        reduction_factors = {
            NoiseReductionLevel.LOW: 0.3,
            NoiseReductionLevel.MEDIUM: 0.5,
            NoiseReductionLevel.HIGH: 0.7
        }
        factor = reduction_factors.get(level, 0.5)

        # Simple noise reduction using spectral subtraction approach
        # In a real implementation, this would use advanced DSP techniques
        # For now, we'll simulate noise reduction
        
        # Estimate noise floor (first 0.5 seconds assumed to be silence/noise)
        noise_sample_size = min(int(0.5 * self.config.sample_rate), len(audio_data) // 10)
        if noise_sample_size > 0:
            noise_floor = np.mean(np.abs(audio_data[:noise_sample_size]))
            
            # Apply noise gate
            threshold = noise_floor * (1 + factor)
            audio_data = np.where(
                np.abs(audio_data) > threshold,
                audio_data,
                audio_data * (1 - factor)
            )

        return audio_data

    def _recognize_cloud(self, audio_data: np.ndarray) -> SpeechRecognitionResult:
        """
        Perform cloud-based speech recognition
        
        Args:
            audio_data: Processed audio data
            
        Returns:
            Recognition result
        """
        # In a real implementation, this would call a cloud ASR service
        # (e.g., Google Cloud Speech-to-Text, AWS Transcribe, Azure Speech)
        # For now, we'll return a simulated result
        
        # Simulate recognition with high confidence for cloud processing
        transcript = self._simulate_recognition(audio_data)
        
        return SpeechRecognitionResult(
            transcript=transcript,
            confidence=0.92,
            processing_mode=ProcessingMode.CLOUD,
            language_detected=self.config.language_code,
            alternative_transcripts=[],
            word_timestamps=None,
            medical_terms_detected=[]
        )

    def _recognize_on_device(self, audio_data: np.ndarray) -> SpeechRecognitionResult:
        """
        Perform on-device speech recognition for privacy
        
        Args:
            audio_data: Processed audio data
            
        Returns:
            Recognition result
        """
        # In a real implementation, this would use an on-device ASR model
        # (e.g., Vosk, Mozilla DeepSpeech, or a custom model)
        # For now, we'll return a simulated result with slightly lower confidence
        
        transcript = self._simulate_recognition(audio_data)
        
        return SpeechRecognitionResult(
            transcript=transcript,
            confidence=0.85,
            processing_mode=ProcessingMode.ON_DEVICE,
            language_detected=self.config.language_code,
            alternative_transcripts=[],
            word_timestamps=None,
            medical_terms_detected=[]
        )

    def _simulate_recognition(self, audio_data: np.ndarray) -> str:
        """
        Simulate speech recognition (placeholder for actual ASR)
        
        Args:
            audio_data: Audio data
            
        Returns:
            Simulated transcript
        """
        # This is a placeholder that would be replaced with actual ASR
        # For testing purposes, we'll return a sample transcript
        return "Sample transcript from audio data"

    def _enhance_with_healthcare_vocabulary(
        self,
        result: SpeechRecognitionResult
    ) -> SpeechRecognitionResult:
        """
        Enhance recognition result with healthcare vocabulary
        
        Args:
            result: Initial recognition result
            
        Returns:
            Enhanced result with medical terms identified
        """
        transcript_lower = result.transcript.lower()
        medical_terms = []

        # Identify medical terms in the transcript
        for term in self.HEALTHCARE_VOCABULARY:
            if term in transcript_lower:
                medical_terms.append(term)

        # Apply healthcare-specific corrections
        corrected_transcript = self._apply_medical_term_corrections(result.transcript)

        return SpeechRecognitionResult(
            transcript=corrected_transcript,
            confidence=result.confidence,
            processing_mode=result.processing_mode,
            language_detected=result.language_detected,
            alternative_transcripts=result.alternative_transcripts,
            word_timestamps=result.word_timestamps,
            medical_terms_detected=medical_terms if medical_terms else None
        )

    def _apply_medical_term_corrections(self, transcript: str) -> str:
        """
        Apply common medical term corrections
        
        Args:
            transcript: Original transcript
            
        Returns:
            Corrected transcript
        """
        # Common misrecognitions and their corrections
        corrections = {
            "mill a gram": "milligram",
            "mill a grams": "milligrams",
            "ace it a min o fen": "acetaminophen",
            "i view pro fin": "ibuprofen",
            "follow up": "follow-up",
            "x ray": "x-ray",
            "ct scan": "CT scan",
            "mri": "MRI",
        }

        corrected = transcript
        for wrong, right in corrections.items():
            corrected = corrected.replace(wrong, right)

        return corrected

    def _apply_accent_normalization(
        self,
        result: SpeechRecognitionResult
    ) -> SpeechRecognitionResult:
        """
        Apply accent normalization to improve recognition across accents
        
        Args:
            result: Recognition result
            
        Returns:
            Normalized result
        """
        # In a real implementation, this would use accent-adaptive models
        # or post-processing to normalize accent-specific variations
        
        # For now, we'll apply some common accent-related corrections
        normalized_transcript = result.transcript
        
        # Common accent variations
        accent_normalizations = {
            # British vs American spellings that might affect recognition
            "colour": "color",
            "favour": "favor",
            "centre": "center",
        }
        
        for variant, standard in accent_normalizations.items():
            normalized_transcript = normalized_transcript.replace(variant, standard)

        return SpeechRecognitionResult(
            transcript=normalized_transcript,
            confidence=result.confidence,
            processing_mode=result.processing_mode,
            language_detected=result.language_detected,
            alternative_transcripts=result.alternative_transcripts,
            word_timestamps=result.word_timestamps,
            medical_terms_detected=result.medical_terms_detected
        )

    def get_supported_languages(self) -> List[str]:
        """
        Get list of supported language codes
        
        Returns:
            List of supported language codes (e.g., ['en-US', 'es-ES'])
        """
        # In a real implementation, this would query the ASR service
        return [
            "en-US",  # English (United States)
            "en-GB",  # English (United Kingdom)
            "es-ES",  # Spanish (Spain)
            "es-MX",  # Spanish (Mexico)
            "fr-FR",  # French (France)
            "de-DE",  # German (Germany)
            "it-IT",  # Italian (Italy)
            "pt-BR",  # Portuguese (Brazil)
            "zh-CN",  # Chinese (Simplified)
            "ja-JP",  # Japanese (Japan)
            "ko-KR",  # Korean (South Korea)
        ]

    def validate_audio_format(
        self,
        audio_data: np.ndarray,
        expected_sample_rate: Optional[int] = None
    ) -> bool:
        """
        Validate audio format and quality
        
        Args:
            audio_data: Audio data to validate
            expected_sample_rate: Expected sample rate (uses config if not provided)
            
        Returns:
            True if audio format is valid
        """
        if audio_data is None or len(audio_data) == 0:
            return False

        # Check if audio data is in valid range
        if not np.isfinite(audio_data).all():
            return False

        # Check minimum duration (at least 0.1 seconds)
        sample_rate = expected_sample_rate or self.config.sample_rate
        min_samples = int(0.1 * sample_rate)
        if len(audio_data) < min_samples:
            return False

        # Check if audio has sufficient energy (not just silence)
        rms_energy = np.sqrt(np.mean(audio_data ** 2))
        if rms_energy < 0.001:  # Very low energy threshold
            return False

        return True

    def estimate_confidence_adjustment(
        self,
        audio_quality: float,
        background_noise_level: float
    ) -> float:
        """
        Estimate confidence adjustment based on audio quality
        
        Args:
            audio_quality: Audio quality score (0.0 to 1.0)
            background_noise_level: Background noise level (0.0 to 1.0)
            
        Returns:
            Confidence adjustment factor (0.0 to 1.0)
        """
        # Higher quality and lower noise = higher confidence
        quality_factor = audio_quality * 0.6
        noise_factor = (1.0 - background_noise_level) * 0.4
        
        return min(1.0, quality_factor + noise_factor)
