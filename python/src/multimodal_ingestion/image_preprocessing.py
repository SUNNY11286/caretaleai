"""
Image Preprocessing Component
Analyzes patient-submitted images for relevant medical context with strict safety boundaries.

Features:
- Medication identification from pill/bottle images
- Medical context analysis (wound assessment, medical device recognition)
- Confidence scoring for all analyses
- Strict safety scope limitations (no diagnostic capabilities)

References: Design Document Multimodal Ingestion Layer
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, List, Dict, Tuple
import numpy as np
from pydantic import BaseModel, Field


class ImageType(str, Enum):
    """Type of medical image submitted"""
    MEDICATION_PILL = "medication_pill"
    MEDICATION_BOTTLE = "medication_bottle"
    WOUND = "wound"
    MEDICAL_DEVICE = "medical_device"
    DISCHARGE_DOCUMENT = "discharge_document"
    UNKNOWN = "unknown"


class AnalysisScope(str, Enum):
    """Scope of image analysis - enforces safety boundaries"""
    IDENTIFICATION_ONLY = "identification_only"  # Only identify objects, no medical interpretation
    EDUCATIONAL = "educational"  # Provide educational context only
    VERIFICATION = "verification"  # Verify against known patient data


class SafetyLevel(str, Enum):
    """Safety level for image analysis results"""
    SAFE = "safe"  # Safe to provide to patient
    REQUIRES_REVIEW = "requires_review"  # Needs care team review
    OUT_OF_SCOPE = "out_of_scope"  # Beyond system capabilities


class ImagePreprocessingConfig(BaseModel):
    """Configuration for image preprocessing"""
    max_image_size_mb: float = Field(default=10.0, ge=0.1, le=50.0)
    min_confidence_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    enable_medication_identification: bool = True
    enable_wound_assessment: bool = False  # Disabled by default for safety
    enable_device_recognition: bool = True
    analysis_scope: AnalysisScope = AnalysisScope.IDENTIFICATION_ONLY
    max_processing_time_seconds: int = Field(default=30, ge=1, le=120)


@dataclass
class MedicationIdentification:
    """Result of medication identification"""
    medication_name: Optional[str]
    imprint_code: Optional[str]  # Pill imprint/code
    ndc_code: Optional[str]  # National Drug Code from bottle
    dosage: Optional[str]
    form: Optional[str]  # tablet, capsule, liquid, etc.
    confidence: float
    matched_from_patient_records: bool = False


@dataclass
class ImageAnalysisResult:
    """Result of image preprocessing and analysis"""
    image_type: ImageType
    confidence: float  # Overall confidence in analysis
    safety_level: SafetyLevel
    analysis_scope: AnalysisScope
    
    # Medication identification results
    medication_identification: Optional[MedicationIdentification] = None
    
    # General findings (non-diagnostic)
    descriptive_findings: List[str] = None
    
    # Safety flags
    requires_care_team_review: bool = False
    out_of_scope_reason: Optional[str] = None
    
    # Metadata
    processing_time_ms: float = 0.0
    image_quality_score: float = 0.0
    
    def __post_init__(self):
        if self.descriptive_findings is None:
            self.descriptive_findings = []


class ImagePreprocessing:
    """
    Image Preprocessing Component
    Analyzes patient-submitted images with strict medical safety boundaries
    """

    # Medication database (simplified - in production would use comprehensive drug database)
    MEDICATION_DATABASE = {
        # Format: imprint_code -> (name, dosage, form)
        "L544": ("Acetaminophen", "500mg", "tablet"),
        "IBU200": ("Ibuprofen", "200mg", "tablet"),
        "M357": ("Hydrocodone/Acetaminophen", "5mg/500mg", "tablet"),
        "A10": ("Amlodipine", "10mg", "tablet"),
        "L368": ("Naproxen Sodium", "220mg", "tablet"),
    }

    # Safety scope boundaries - what we explicitly DO NOT do
    PROHIBITED_ANALYSES = {
        "diagnosis",
        "disease_identification",
        "condition_assessment",
        "treatment_recommendation",
        "medical_interpretation",
        "severity_grading",
        "prognosis",
    }

    def __init__(self, config: Optional[ImagePreprocessingConfig] = None):
        """
        Initialize Image Preprocessing component
        
        Args:
            config: Image preprocessing configuration
        """
        self.config = config or ImagePreprocessingConfig()
        self._initialize_analyzers()

    def _initialize_analyzers(self) -> None:
        """Initialize image analysis components"""
        # In a real implementation, this would load ML models for:
        # - Object detection
        # - OCR for text extraction
        # - Image classification
        # For now, we'll set up configuration flags
        self._medication_id_enabled = self.config.enable_medication_identification
        self._device_recognition_enabled = self.config.enable_device_recognition
        self._wound_assessment_enabled = self.config.enable_wound_assessment

    def analyze_image(
        self,
        image_data: np.ndarray,
        patient_id: Optional[str] = None,
        patient_medications: Optional[List[str]] = None
    ) -> ImageAnalysisResult:
        """
        Analyze patient-submitted image with safety boundaries
        
        Args:
            image_data: Image data as numpy array (H, W, C)
            patient_id: Optional patient ID for context
            patient_medications: Optional list of patient's known medications
            
        Returns:
            Image analysis result with confidence scores and safety flags
        """
        import time
        start_time = time.time()

        # Validate image
        if not self.validate_image(image_data):
            return self._create_invalid_image_result()

        # Assess image quality
        quality_score = self._assess_image_quality(image_data)
        
        # Classify image type
        image_type, type_confidence = self._classify_image_type(image_data)
        
        # Perform type-specific analysis
        result = self._analyze_by_type(
            image_data,
            image_type,
            patient_medications
        )
        
        # Apply safety checks
        result = self._apply_safety_checks(result)
        
        # Calculate processing time
        processing_time = (time.time() - start_time) * 1000  # Convert to ms
        
        # Update result with metadata
        result.processing_time_ms = processing_time
        result.image_quality_score = quality_score
        
        return result

    def _classify_image_type(
        self,
        image_data: np.ndarray
    ) -> Tuple[ImageType, float]:
        """
        Classify the type of medical image
        
        Args:
            image_data: Image data
            
        Returns:
            Tuple of (image_type, confidence)
        """
        # In a real implementation, this would use a trained classifier
        # For now, we'll use simple heuristics based on image characteristics
        
        height, width = image_data.shape[:2]
        aspect_ratio = width / height if height > 0 else 1.0
        
        # Analyze image features
        has_text = self._detect_text_presence(image_data)
        has_circular_objects = self._detect_circular_objects(image_data)
        
        # Simple classification logic
        if has_circular_objects and not has_text:
            return ImageType.MEDICATION_PILL, 0.75
        elif has_text and aspect_ratio > 0.5:
            return ImageType.MEDICATION_BOTTLE, 0.80
        elif has_text and aspect_ratio < 0.5:
            return ImageType.DISCHARGE_DOCUMENT, 0.70
        else:
            return ImageType.UNKNOWN, 0.50

    def _detect_text_presence(self, image_data: np.ndarray) -> bool:
        """Detect if image contains text (simplified)"""
        # In production, would use OCR or text detection model
        # For now, check for high-contrast edges that might indicate text
        if len(image_data.shape) == 3:
            gray = np.mean(image_data, axis=2)
        else:
            gray = image_data
        
        # Simple edge detection
        edges = np.abs(np.diff(gray, axis=0)).sum() + np.abs(np.diff(gray, axis=1)).sum()
        normalized_edges = edges / (gray.shape[0] * gray.shape[1])
        
        return normalized_edges > 10.0  # Threshold for text presence

    def _detect_circular_objects(self, image_data: np.ndarray) -> bool:
        """Detect circular objects (pills) in image (simplified)"""
        # In production, would use object detection model
        # For now, return False as placeholder
        return False

    def _analyze_by_type(
        self,
        image_data: np.ndarray,
        image_type: ImageType,
        patient_medications: Optional[List[str]]
    ) -> ImageAnalysisResult:
        """
        Perform type-specific image analysis
        
        Args:
            image_data: Image data
            image_type: Classified image type
            patient_medications: Patient's known medications
            
        Returns:
            Analysis result
        """
        if image_type == ImageType.MEDICATION_PILL:
            return self._analyze_medication_pill(image_data, patient_medications)
        elif image_type == ImageType.MEDICATION_BOTTLE:
            return self._analyze_medication_bottle(image_data, patient_medications)
        elif image_type == ImageType.MEDICAL_DEVICE:
            return self._analyze_medical_device(image_data)
        elif image_type == ImageType.DISCHARGE_DOCUMENT:
            return self._analyze_discharge_document(image_data)
        else:
            return self._create_unknown_type_result(image_type)

    def _analyze_medication_pill(
        self,
        image_data: np.ndarray,
        patient_medications: Optional[List[str]]
    ) -> ImageAnalysisResult:
        """
        Analyze medication pill image
        
        Args:
            image_data: Image data
            patient_medications: Patient's known medications
            
        Returns:
            Analysis result with medication identification
        """
        # Extract pill features
        imprint_code = self._extract_pill_imprint(image_data)
        
        # Attempt medication identification
        medication_id = None
        confidence = 0.0
        matched_from_records = False
        
        if imprint_code and imprint_code in self.MEDICATION_DATABASE:
            name, dosage, form = self.MEDICATION_DATABASE[imprint_code]
            confidence = 0.85
            
            # Check if matches patient's known medications
            if patient_medications and name in patient_medications:
                matched_from_records = True
                confidence = 0.95
            
            medication_id = MedicationIdentification(
                medication_name=name,
                imprint_code=imprint_code,
                ndc_code=None,
                dosage=dosage,
                form=form,
                confidence=confidence,
                matched_from_patient_records=matched_from_records
            )
        
        # Create result
        descriptive_findings = []
        if medication_id:
            descriptive_findings.append(
                f"Identified as {medication_id.medication_name} {medication_id.dosage}"
            )
            if matched_from_records:
                descriptive_findings.append("Matches your prescribed medications")
        else:
            descriptive_findings.append("Unable to identify medication from image")
        
        return ImageAnalysisResult(
            image_type=ImageType.MEDICATION_PILL,
            confidence=confidence,
            safety_level=SafetyLevel.SAFE,
            analysis_scope=self.config.analysis_scope,
            medication_identification=medication_id,
            descriptive_findings=descriptive_findings,
            requires_care_team_review=not matched_from_records if medication_id else True
        )

    def _analyze_medication_bottle(
        self,
        image_data: np.ndarray,
        patient_medications: Optional[List[str]]
    ) -> ImageAnalysisResult:
        """
        Analyze medication bottle/label image
        
        Args:
            image_data: Image data
            patient_medications: Patient's known medications
            
        Returns:
            Analysis result with medication identification
        """
        # Extract text from label using OCR
        extracted_text = self._extract_text_from_image(image_data)
        
        # Parse medication information
        medication_name = self._parse_medication_name(extracted_text)
        ndc_code = self._parse_ndc_code(extracted_text)
        dosage = self._parse_dosage(extracted_text)
        
        # Create medication identification
        medication_id = None
        confidence = 0.0
        matched_from_records = False
        
        if medication_name:
            confidence = 0.80
            
            # Check against patient records
            if patient_medications and medication_name in patient_medications:
                matched_from_records = True
                confidence = 0.95
            
            medication_id = MedicationIdentification(
                medication_name=medication_name,
                imprint_code=None,
                ndc_code=ndc_code,
                dosage=dosage,
                form="unknown",
                confidence=confidence,
                matched_from_patient_records=matched_from_records
            )
        
        descriptive_findings = []
        if medication_id:
            descriptive_findings.append(
                f"Medication label shows: {medication_id.medication_name}"
            )
            if medication_id.dosage:
                descriptive_findings.append(f"Dosage: {medication_id.dosage}")
            if matched_from_records:
                descriptive_findings.append("Matches your prescribed medications")
        else:
            descriptive_findings.append("Unable to read medication label clearly")
        
        return ImageAnalysisResult(
            image_type=ImageType.MEDICATION_BOTTLE,
            confidence=confidence,
            safety_level=SafetyLevel.SAFE,
            analysis_scope=self.config.analysis_scope,
            medication_identification=medication_id,
            descriptive_findings=descriptive_findings,
            requires_care_team_review=not matched_from_records if medication_id else True
        )

    def _analyze_medical_device(
        self,
        image_data: np.ndarray
    ) -> ImageAnalysisResult:
        """
        Analyze medical device image (non-diagnostic)
        
        Args:
            image_data: Image data
            
        Returns:
            Analysis result with device identification
        """
        # Identify device type (non-diagnostic)
        device_type = self._identify_device_type(image_data)
        
        descriptive_findings = []
        confidence = 0.0
        
        if device_type:
            descriptive_findings.append(f"Appears to be a {device_type}")
            confidence = 0.75
        else:
            descriptive_findings.append("Unable to identify medical device")
            confidence = 0.30
        
        return ImageAnalysisResult(
            image_type=ImageType.MEDICAL_DEVICE,
            confidence=confidence,
            safety_level=SafetyLevel.SAFE,
            analysis_scope=self.config.analysis_scope,
            descriptive_findings=descriptive_findings,
            requires_care_team_review=True
        )

    def _analyze_discharge_document(
        self,
        image_data: np.ndarray
    ) -> ImageAnalysisResult:
        """
        Analyze discharge document image
        
        Args:
            image_data: Image data
            
        Returns:
            Analysis result
        """
        # Extract text from document
        extracted_text = self._extract_text_from_image(image_data)
        
        descriptive_findings = [
            "Document image detected",
            "Please use text input for better accuracy with discharge documents"
        ]
        
        return ImageAnalysisResult(
            image_type=ImageType.DISCHARGE_DOCUMENT,
            confidence=0.70,
            safety_level=SafetyLevel.SAFE,
            analysis_scope=self.config.analysis_scope,
            descriptive_findings=descriptive_findings,
            requires_care_team_review=False
        )

    def _extract_pill_imprint(self, image_data: np.ndarray) -> Optional[str]:
        """
        Extract imprint code from pill image
        
        Args:
            image_data: Image data
            
        Returns:
            Imprint code if found
        """
        # In production, would use OCR specialized for pill imprints
        # For now, return None as placeholder
        return None

    def _extract_text_from_image(self, image_data: np.ndarray) -> str:
        """
        Extract text from image using OCR
        
        Args:
            image_data: Image data
            
        Returns:
            Extracted text
        """
        # In production, would use OCR library (Tesseract, Google Vision, etc.)
        # For now, return empty string as placeholder
        return ""

    def _parse_medication_name(self, text: str) -> Optional[str]:
        """Parse medication name from extracted text"""
        # In production, would use NLP to extract medication names
        return None

    def _parse_ndc_code(self, text: str) -> Optional[str]:
        """Parse NDC code from extracted text"""
        # NDC format: XXXXX-XXXX-XX
        import re
        ndc_pattern = r'\d{5}-\d{4}-\d{2}'
        match = re.search(ndc_pattern, text)
        return match.group(0) if match else None

    def _parse_dosage(self, text: str) -> Optional[str]:
        """Parse dosage from extracted text"""
        # In production, would use NLP to extract dosage information
        return None

    def _identify_device_type(self, image_data: np.ndarray) -> Optional[str]:
        """Identify medical device type (non-diagnostic)"""
        # In production, would use object detection model
        return None

    def _apply_safety_checks(
        self,
        result: ImageAnalysisResult
    ) -> ImageAnalysisResult:
        """
        Apply safety checks to ensure analysis stays within scope
        
        Args:
            result: Initial analysis result
            
        Returns:
            Safety-checked result
        """
        # Check if confidence meets threshold
        if result.confidence < self.config.min_confidence_threshold:
            result.requires_care_team_review = True
            result.safety_level = SafetyLevel.REQUIRES_REVIEW
        
        # Ensure no prohibited analyses
        for finding in result.descriptive_findings:
            finding_lower = finding.lower()
            for prohibited in self.PROHIBITED_ANALYSES:
                if prohibited in finding_lower:
                    result.safety_level = SafetyLevel.OUT_OF_SCOPE
                    result.out_of_scope_reason = (
                        f"Analysis contains prohibited content: {prohibited}"
                    )
                    result.descriptive_findings = [
                        "This type of analysis is beyond the system's scope. "
                        "Please consult your healthcare provider."
                    ]
                    break
        
        return result

    def _assess_image_quality(self, image_data: np.ndarray) -> float:
        """
        Assess image quality for analysis
        
        Args:
            image_data: Image data
            
        Returns:
            Quality score (0.0 to 1.0)
        """
        # Check resolution
        height, width = image_data.shape[:2]
        min_resolution = 480
        resolution_score = min(1.0, min(height, width) / min_resolution)
        
        # Check brightness
        if len(image_data.shape) == 3:
            brightness = np.mean(image_data)
        else:
            brightness = np.mean(image_data)
        
        # Optimal brightness is around 128 (mid-range)
        brightness_score = 1.0 - abs(brightness - 128) / 128
        
        # Check sharpness (using variance of Laplacian)
        if len(image_data.shape) == 3:
            gray = np.mean(image_data, axis=2)
        else:
            gray = image_data
        
        # Simple sharpness metric
        laplacian_var = np.var(np.diff(gray, axis=0)) + np.var(np.diff(gray, axis=1))
        sharpness_score = min(1.0, laplacian_var / 1000.0)
        
        # Weighted average
        quality_score = (
            resolution_score * 0.4 +
            brightness_score * 0.3 +
            sharpness_score * 0.3
        )
        
        return quality_score

    def validate_image(self, image_data: np.ndarray) -> bool:
        """
        Validate image format and size
        
        Args:
            image_data: Image data to validate
            
        Returns:
            True if image is valid
        """
        if image_data is None or image_data.size == 0:
            return False

        # Check dimensions
        if len(image_data.shape) not in [2, 3]:
            return False

        # Check if image has valid dimensions
        height, width = image_data.shape[:2]
        if height < 100 or width < 100:
            return False

        # Check if values are in valid range
        if not np.isfinite(image_data).all():
            return False

        # Check image size (approximate MB calculation)
        size_mb = image_data.nbytes / (1024 * 1024)
        if size_mb > self.config.max_image_size_mb:
            return False

        return True

    def _create_invalid_image_result(self) -> ImageAnalysisResult:
        """Create result for invalid image"""
        return ImageAnalysisResult(
            image_type=ImageType.UNKNOWN,
            confidence=0.0,
            safety_level=SafetyLevel.OUT_OF_SCOPE,
            analysis_scope=self.config.analysis_scope,
            descriptive_findings=["Invalid image format or size"],
            out_of_scope_reason="Invalid image data",
            requires_care_team_review=False
        )

    def _create_unknown_type_result(self, image_type: ImageType) -> ImageAnalysisResult:
        """Create result for unknown image type"""
        return ImageAnalysisResult(
            image_type=image_type,
            confidence=0.0,
            safety_level=SafetyLevel.REQUIRES_REVIEW,
            analysis_scope=self.config.analysis_scope,
            descriptive_findings=["Unable to determine image type"],
            requires_care_team_review=True
        )

    def get_supported_image_types(self) -> List[ImageType]:
        """
        Get list of supported image types
        
        Returns:
            List of supported image types
        """
        supported = [ImageType.DISCHARGE_DOCUMENT]
        
        if self.config.enable_medication_identification:
            supported.extend([
                ImageType.MEDICATION_PILL,
                ImageType.MEDICATION_BOTTLE
            ])
        
        if self.config.enable_device_recognition:
            supported.append(ImageType.MEDICAL_DEVICE)
        
        return supported

    def get_safety_boundaries(self) -> Dict[str, List[str]]:
        """
        Get explicit safety boundaries for image analysis
        
        Returns:
            Dictionary of what the system does and does not do
        """
        return {
            "capabilities": [
                "Identify medications from pills or bottles",
                "Recognize common medical devices",
                "Extract text from documents",
                "Provide educational context about identified items"
            ],
            "limitations": [
                "Cannot diagnose medical conditions",
                "Cannot assess disease severity",
                "Cannot recommend treatments",
                "Cannot interpret medical test results",
                "Cannot provide medical advice"
            ],
            "prohibited_analyses": list(self.PROHIBITED_ANALYSES)
        }
