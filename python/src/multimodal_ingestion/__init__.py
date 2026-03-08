"""
Multimodal Ingestion Layer
Exports for speech-to-text, image preprocessing, and input normalization components
"""

from .speech_to_text import SpeechToText, SpeechRecognitionConfig, SpeechRecognitionResult
from .image_preprocessing import (
    ImagePreprocessing,
    ImagePreprocessingConfig,
    ImageAnalysisResult,
    MedicationIdentification,
    ImageType,
    AnalysisScope,
    SafetyLevel
)
from .input_normalization import (
    InputNormalization,
    InputNormalizationConfig,
    NormalizedRequest,
    ExtractedEntity,
    InputType,
    IntentType,
    EntityType
)

__all__ = [
    'SpeechToText',
    'SpeechRecognitionConfig',
    'SpeechRecognitionResult',
    'ImagePreprocessing',
    'ImagePreprocessingConfig',
    'ImageAnalysisResult',
    'MedicationIdentification',
    'ImageType',
    'AnalysisScope',
    'SafetyLevel',
    'InputNormalization',
    'InputNormalizationConfig',
    'NormalizedRequest',
    'ExtractedEntity',
    'InputType',
    'IntentType',
    'EntityType'
]
