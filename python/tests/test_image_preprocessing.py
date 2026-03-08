"""
Unit tests for Image Preprocessing component
Tests image analysis, medication identification, confidence scoring, and safety scope limitations
"""

import pytest
import numpy as np
from src.multimodal_ingestion.image_preprocessing import (
    ImagePreprocessing,
    ImagePreprocessingConfig,
    ImageAnalysisResult,
    MedicationIdentification,
    ImageType,
    AnalysisScope,
    SafetyLevel
)


class TestImagePreprocessingConfiguration:
    """Test Image Preprocessing configuration"""

    def test_default_configuration(self):
        """Test default configuration values"""
        config = ImagePreprocessingConfig()
        
        assert config.max_image_size_mb == 10.0
        assert config.min_confidence_threshold == 0.7
        assert config.enable_medication_identification is True
        assert config.enable_wound_assessment is False  # Disabled for safety
        assert config.enable_device_recognition is True
        assert config.analysis_scope == AnalysisScope.IDENTIFICATION_ONLY
        assert config.max_processing_time_seconds == 30

    def test_custom_configuration(self):
        """Test custom configuration"""
        config = ImagePreprocessingConfig(
            max_image_size_mb=5.0,
            min_confidence_threshold=0.8,
            enable_medication_identification=False,
            enable_device_recognition=False,
            analysis_scope=AnalysisScope.EDUCATIONAL,
            max_processing_time_seconds=60
        )
        
        assert config.max_image_size_mb == 5.0
        assert config.min_confidence_threshold == 0.8
        assert config.enable_medication_identification is False
        assert config.enable_device_recognition is False
        assert config.analysis_scope == AnalysisScope.EDUCATIONAL

    def test_invalid_max_image_size(self):
        """Test that invalid max image size raises validation error"""
        with pytest.raises(Exception):  # Pydantic validation error
            ImagePreprocessingConfig(max_image_size_mb=100.0)  # Too large

    def test_invalid_confidence_threshold(self):
        """Test that invalid confidence threshold raises validation error"""
        with pytest.raises(Exception):  # Pydantic validation error
            ImagePreprocessingConfig(min_confidence_threshold=1.5)  # > 1.0


class TestImagePreprocessingInitialization:
    """Test Image Preprocessing initialization"""

    def test_initialization_with_default_config(self):
        """Test initialization with default configuration"""
        ip = ImagePreprocessing()
        
        assert ip.config.enable_medication_identification is True
        assert ip._medication_id_enabled is True
        assert ip._device_recognition_enabled is True
        assert ip._wound_assessment_enabled is False

    def test_initialization_with_custom_config(self):
        """Test initialization with custom configuration"""
        config = ImagePreprocessingConfig(
            enable_medication_identification=False,
            enable_device_recognition=False,
            enable_wound_assessment=False
        )
        ip = ImagePreprocessing(config)
        
        assert ip._medication_id_enabled is False
        assert ip._device_recognition_enabled is False
        assert ip._wound_assessment_enabled is False


class TestImageValidation:
    """Test image validation functionality"""

    def test_valid_image(self):
        """Test validation of valid image data"""
        ip = ImagePreprocessing()
        
        # Create valid RGB image
        image_data = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)
        is_valid = ip.validate_image(image_data)
        
        assert is_valid is True

    def test_valid_grayscale_image(self):
        """Test validation of valid grayscale image"""
        ip = ImagePreprocessing()
        
        # Create valid grayscale image
        image_data = np.random.randint(0, 256, (480, 640), dtype=np.uint8)
        is_valid = ip.validate_image(image_data)
        
        assert is_valid is True

    def test_empty_image(self):
        """Test validation of empty image data"""
        ip = ImagePreprocessing()
        
        image_data = np.array([])
        is_valid = ip.validate_image(image_data)
        
        assert is_valid is False

    def test_none_image(self):
        """Test validation of None image data"""
        ip = ImagePreprocessing()
        
        is_valid = ip.validate_image(None)
        
        assert is_valid is False

    def test_too_small_image(self):
        """Test validation of too small image"""
        ip = ImagePreprocessing()
        
        # Image smaller than 100x100
        image_data = np.random.randint(0, 256, (50, 50, 3), dtype=np.uint8)
        is_valid = ip.validate_image(image_data)
        
        assert is_valid is False

    def test_invalid_dimensions(self):
        """Test validation of image with invalid dimensions"""
        ip = ImagePreprocessing()
        
        # 1D array (invalid)
        image_data = np.random.randint(0, 256, (1000,), dtype=np.uint8)
        is_valid = ip.validate_image(image_data)
        
        assert is_valid is False

    def test_image_with_nan(self):
        """Test validation of image with NaN values"""
        ip = ImagePreprocessing()
        
        image_data = np.random.rand(480, 640, 3)
        image_data[100, 100, 0] = np.nan
        is_valid = ip.validate_image(image_data)
        
        assert is_valid is False

    def test_too_large_image(self):
        """Test validation of too large image"""
        config = ImagePreprocessingConfig(max_image_size_mb=1.0)
        ip = ImagePreprocessing(config)
        
        # Create very large image (> 1MB)
        image_data = np.random.randint(0, 256, (2000, 2000, 3), dtype=np.uint8)
        is_valid = ip.validate_image(image_data)
        
        assert is_valid is False


class TestImageQualityAssessment:
    """Test image quality assessment"""

    def test_high_quality_image(self):
        """Test quality assessment of high quality image"""
        ip = ImagePreprocessing()
        
        # Create high resolution, well-lit image
        image_data = np.random.randint(100, 150, (1920, 1080, 3), dtype=np.uint8)
        quality = ip._assess_image_quality(image_data)
        
        assert 0.0 <= quality <= 1.0
        assert quality > 0.5  # Should be reasonably high

    def test_low_quality_image(self):
        """Test quality assessment of low quality image"""
        ip = ImagePreprocessing()
        
        # Create low resolution, poorly lit image
        image_data = np.random.randint(0, 50, (320, 240, 3), dtype=np.uint8)
        quality = ip._assess_image_quality(image_data)
        
        assert 0.0 <= quality <= 1.0

    def test_grayscale_quality_assessment(self):
        """Test quality assessment of grayscale image"""
        ip = ImagePreprocessing()
        
        image_data = np.random.randint(0, 256, (640, 480), dtype=np.uint8)
        quality = ip._assess_image_quality(image_data)
        
        assert 0.0 <= quality <= 1.0


class TestImageTypeClassification:
    """Test image type classification"""

    def test_classify_medication_pill(self):
        """Test classification of medication pill image"""
        ip = ImagePreprocessing()
        
        # Create image with circular objects (simulated pill)
        image_data = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)
        image_type, confidence = ip._classify_image_type(image_data)
        
        assert isinstance(image_type, ImageType)
        assert 0.0 <= confidence <= 1.0

    def test_classify_medication_bottle(self):
        """Test classification of medication bottle image"""
        ip = ImagePreprocessing()
        
        # Create image with text (simulated label)
        image_data = np.ones((480, 640, 3), dtype=np.uint8) * 128
        # Add high contrast regions to simulate text
        image_data[100:150, 200:400] = 255
        image_data[160:210, 200:400] = 0
        
        image_type, confidence = ip._classify_image_type(image_data)
        
        assert isinstance(image_type, ImageType)
        assert 0.0 <= confidence <= 1.0

    def test_classify_unknown_image(self):
        """Test classification of unknown image type"""
        ip = ImagePreprocessing()
        
        # Create uniform image (no distinguishing features)
        image_data = np.ones((480, 640, 3), dtype=np.uint8) * 128
        image_type, confidence = ip._classify_image_type(image_data)
        
        assert isinstance(image_type, ImageType)
        assert 0.0 <= confidence <= 1.0


class TestMedicationIdentification:
    """Test medication identification functionality"""

    def test_analyze_medication_pill_without_patient_data(self):
        """Test medication pill analysis without patient medication data"""
        ip = ImagePreprocessing()
        
        image_data = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)
        result = ip._analyze_medication_pill(image_data, None)
        
        assert isinstance(result, ImageAnalysisResult)
        assert result.image_type == ImageType.MEDICATION_PILL
        assert result.safety_level in [SafetyLevel.SAFE, SafetyLevel.REQUIRES_REVIEW]
        assert len(result.descriptive_findings) > 0

    def test_analyze_medication_pill_with_patient_data(self):
        """Test medication pill analysis with patient medication data"""
        ip = ImagePreprocessing()
        
        patient_medications = ["Acetaminophen", "Ibuprofen"]
        image_data = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)
        result = ip._analyze_medication_pill(image_data, patient_medications)
        
        assert isinstance(result, ImageAnalysisResult)
        assert result.image_type == ImageType.MEDICATION_PILL

    def test_analyze_medication_bottle(self):
        """Test medication bottle analysis"""
        ip = ImagePreprocessing()
        
        image_data = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)
        result = ip._analyze_medication_bottle(image_data, None)
        
        assert isinstance(result, ImageAnalysisResult)
        assert result.image_type == ImageType.MEDICATION_BOTTLE
        assert result.safety_level in [SafetyLevel.SAFE, SafetyLevel.REQUIRES_REVIEW]

    def test_medication_identification_confidence(self):
        """Test that medication identification includes confidence scores"""
        ip = ImagePreprocessing()
        
        image_data = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)
        result = ip._analyze_medication_pill(image_data, None)
        
        assert 0.0 <= result.confidence <= 1.0


class TestMedicalDeviceRecognition:
    """Test medical device recognition"""

    def test_analyze_medical_device(self):
        """Test medical device analysis"""
        ip = ImagePreprocessing()
        
        image_data = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)
        result = ip._analyze_medical_device(image_data)
        
        assert isinstance(result, ImageAnalysisResult)
        assert result.image_type == ImageType.MEDICAL_DEVICE
        assert result.safety_level == SafetyLevel.SAFE
        assert result.requires_care_team_review is True  # Always requires review

    def test_device_recognition_disabled(self):
        """Test that device recognition can be disabled"""
        config = ImagePreprocessingConfig(enable_device_recognition=False)
        ip = ImagePreprocessing(config)
        
        assert ip._device_recognition_enabled is False


class TestDischargeDocumentAnalysis:
    """Test discharge document analysis"""

    def test_analyze_discharge_document(self):
        """Test discharge document analysis"""
        ip = ImagePreprocessing()
        
        image_data = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)
        result = ip._analyze_discharge_document(image_data)
        
        assert isinstance(result, ImageAnalysisResult)
        assert result.image_type == ImageType.DISCHARGE_DOCUMENT
        assert result.safety_level == SafetyLevel.SAFE
        assert len(result.descriptive_findings) > 0


class TestSafetyBoundaries:
    """Test safety boundary enforcement"""

    def test_safety_checks_low_confidence(self):
        """Test that low confidence results require review"""
        config = ImagePreprocessingConfig(min_confidence_threshold=0.8)
        ip = ImagePreprocessing(config)
        
        # Create result with low confidence
        result = ImageAnalysisResult(
            image_type=ImageType.MEDICATION_PILL,
            confidence=0.5,  # Below threshold
            safety_level=SafetyLevel.SAFE,
            analysis_scope=AnalysisScope.IDENTIFICATION_ONLY,
            descriptive_findings=["Test finding"]
        )
        
        checked_result = ip._apply_safety_checks(result)
        
        assert checked_result.requires_care_team_review is True
        assert checked_result.safety_level == SafetyLevel.REQUIRES_REVIEW

    def test_safety_checks_high_confidence(self):
        """Test that high confidence results pass safety checks"""
        config = ImagePreprocessingConfig(min_confidence_threshold=0.7)
        ip = ImagePreprocessing(config)
        
        # Create result with high confidence
        result = ImageAnalysisResult(
            image_type=ImageType.MEDICATION_PILL,
            confidence=0.9,  # Above threshold
            safety_level=SafetyLevel.SAFE,
            analysis_scope=AnalysisScope.IDENTIFICATION_ONLY,
            descriptive_findings=["Identified medication"]
        )
        
        checked_result = ip._apply_safety_checks(result)
        
        assert checked_result.safety_level == SafetyLevel.SAFE

    def test_prohibited_analysis_detection(self):
        """Test detection of prohibited analysis types"""
        ip = ImagePreprocessing()
        
        # Create result with prohibited content
        result = ImageAnalysisResult(
            image_type=ImageType.WOUND,
            confidence=0.9,
            safety_level=SafetyLevel.SAFE,
            analysis_scope=AnalysisScope.IDENTIFICATION_ONLY,
            descriptive_findings=["This appears to be a diagnosis of infection"]
        )
        
        checked_result = ip._apply_safety_checks(result)
        
        assert checked_result.safety_level == SafetyLevel.OUT_OF_SCOPE
        assert checked_result.out_of_scope_reason is not None

    def test_get_safety_boundaries(self):
        """Test getting safety boundaries"""
        ip = ImagePreprocessing()
        
        boundaries = ip.get_safety_boundaries()
        
        assert "capabilities" in boundaries
        assert "limitations" in boundaries
        assert "prohibited_analyses" in boundaries
        assert len(boundaries["capabilities"]) > 0
        assert len(boundaries["limitations"]) > 0
        assert "diagnosis" in boundaries["prohibited_analyses"]


class TestAnalysisScope:
    """Test analysis scope enforcement"""

    def test_identification_only_scope(self):
        """Test identification only analysis scope"""
        config = ImagePreprocessingConfig(
            analysis_scope=AnalysisScope.IDENTIFICATION_ONLY
        )
        ip = ImagePreprocessing(config)
        
        assert ip.config.analysis_scope == AnalysisScope.IDENTIFICATION_ONLY

    def test_educational_scope(self):
        """Test educational analysis scope"""
        config = ImagePreprocessingConfig(
            analysis_scope=AnalysisScope.EDUCATIONAL
        )
        ip = ImagePreprocessing(config)
        
        assert ip.config.analysis_scope == AnalysisScope.EDUCATIONAL

    def test_verification_scope(self):
        """Test verification analysis scope"""
        config = ImagePreprocessingConfig(
            analysis_scope=AnalysisScope.VERIFICATION
        )
        ip = ImagePreprocessing(config)
        
        assert ip.config.analysis_scope == AnalysisScope.VERIFICATION


class TestSupportedImageTypes:
    """Test supported image types"""

    def test_get_supported_types_all_enabled(self):
        """Test getting supported types with all features enabled"""
        config = ImagePreprocessingConfig(
            enable_medication_identification=True,
            enable_device_recognition=True
        )
        ip = ImagePreprocessing(config)
        
        supported = ip.get_supported_image_types()
        
        assert ImageType.MEDICATION_PILL in supported
        assert ImageType.MEDICATION_BOTTLE in supported
        assert ImageType.MEDICAL_DEVICE in supported
        assert ImageType.DISCHARGE_DOCUMENT in supported

    def test_get_supported_types_medication_disabled(self):
        """Test getting supported types with medication identification disabled"""
        config = ImagePreprocessingConfig(
            enable_medication_identification=False,
            enable_device_recognition=True
        )
        ip = ImagePreprocessing(config)
        
        supported = ip.get_supported_image_types()
        
        assert ImageType.MEDICATION_PILL not in supported
        assert ImageType.MEDICATION_BOTTLE not in supported
        assert ImageType.MEDICAL_DEVICE in supported
        assert ImageType.DISCHARGE_DOCUMENT in supported

    def test_get_supported_types_device_disabled(self):
        """Test getting supported types with device recognition disabled"""
        config = ImagePreprocessingConfig(
            enable_medication_identification=True,
            enable_device_recognition=False
        )
        ip = ImagePreprocessing(config)
        
        supported = ip.get_supported_image_types()
        
        assert ImageType.MEDICATION_PILL in supported
        assert ImageType.MEDICATION_BOTTLE in supported
        assert ImageType.MEDICAL_DEVICE not in supported


class TestCompleteAnalysisWorkflow:
    """Test complete image analysis workflow"""

    def test_analyze_valid_image(self):
        """Test complete analysis of valid image"""
        ip = ImagePreprocessing()
        
        # Create valid image
        image_data = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)
        result = ip.analyze_image(image_data)
        
        assert isinstance(result, ImageAnalysisResult)
        assert result.image_type in ImageType
        assert 0.0 <= result.confidence <= 1.0
        assert result.safety_level in SafetyLevel
        assert result.processing_time_ms > 0.0
        assert 0.0 <= result.image_quality_score <= 1.0

    def test_analyze_invalid_image(self):
        """Test analysis of invalid image"""
        ip = ImagePreprocessing()
        
        # Create invalid image (too small)
        image_data = np.random.randint(0, 256, (50, 50, 3), dtype=np.uint8)
        result = ip.analyze_image(image_data)
        
        assert result.image_type == ImageType.UNKNOWN
        assert result.confidence == 0.0
        assert result.safety_level == SafetyLevel.OUT_OF_SCOPE
        assert "Invalid" in result.descriptive_findings[0]

    def test_analyze_with_patient_context(self):
        """Test analysis with patient context"""
        ip = ImagePreprocessing()
        
        patient_medications = ["Acetaminophen", "Ibuprofen"]
        image_data = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)
        
        result = ip.analyze_image(
            image_data,
            patient_id="patient-123",
            patient_medications=patient_medications
        )
        
        assert isinstance(result, ImageAnalysisResult)

    def test_processing_time_tracking(self):
        """Test that processing time is tracked"""
        ip = ImagePreprocessing()
        
        image_data = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)
        result = ip.analyze_image(image_data)
        
        assert result.processing_time_ms > 0.0
        assert result.processing_time_ms < 10000  # Should be less than 10 seconds


class TestTextExtraction:
    """Test text extraction functionality"""

    def test_detect_text_presence(self):
        """Test text presence detection"""
        ip = ImagePreprocessing()
        
        # Create image with high contrast (simulating text)
        image_data = np.ones((480, 640, 3), dtype=np.uint8) * 128
        image_data[100:150, 200:400] = 255
        image_data[160:210, 200:400] = 0
        
        has_text = ip._detect_text_presence(image_data)
        
        assert isinstance(has_text, (bool, np.bool_))

    def test_detect_text_in_uniform_image(self):
        """Test text detection in uniform image (no text)"""
        ip = ImagePreprocessing()
        
        # Create uniform image
        image_data = np.ones((480, 640, 3), dtype=np.uint8) * 128
        has_text = ip._detect_text_presence(image_data)
        
        assert isinstance(has_text, (bool, np.bool_))

    def test_parse_ndc_code(self):
        """Test NDC code parsing"""
        ip = ImagePreprocessing()
        
        text_with_ndc = "NDC: 12345-6789-01 Medication Name"
        ndc = ip._parse_ndc_code(text_with_ndc)
        
        assert ndc == "12345-6789-01"

    def test_parse_ndc_code_not_found(self):
        """Test NDC code parsing when not present"""
        ip = ImagePreprocessing()
        
        text_without_ndc = "Medication Name 500mg"
        ndc = ip._parse_ndc_code(text_without_ndc)
        
        assert ndc is None


class TestEdgeCases:
    """Test edge cases and error conditions"""

    def test_analyze_grayscale_image(self):
        """Test analysis of grayscale image"""
        ip = ImagePreprocessing()
        
        # Create grayscale image
        image_data = np.random.randint(0, 256, (480, 640), dtype=np.uint8)
        result = ip.analyze_image(image_data)
        
        assert isinstance(result, ImageAnalysisResult)

    def test_analyze_very_large_valid_image(self):
        """Test analysis of large but valid image"""
        config = ImagePreprocessingConfig(max_image_size_mb=20.0)
        ip = ImagePreprocessing(config)
        
        # Create large image (but within limits)
        image_data = np.random.randint(0, 256, (1920, 1080, 3), dtype=np.uint8)
        result = ip.analyze_image(image_data)
        
        assert isinstance(result, ImageAnalysisResult)

    def test_analyze_square_image(self):
        """Test analysis of square image"""
        ip = ImagePreprocessing()
        
        # Create square image
        image_data = np.random.randint(0, 256, (640, 640, 3), dtype=np.uint8)
        result = ip.analyze_image(image_data)
        
        assert isinstance(result, ImageAnalysisResult)

    def test_analyze_portrait_image(self):
        """Test analysis of portrait orientation image"""
        ip = ImagePreprocessing()
        
        # Create portrait image (height > width)
        image_data = np.random.randint(0, 256, (640, 480, 3), dtype=np.uint8)
        result = ip.analyze_image(image_data)
        
        assert isinstance(result, ImageAnalysisResult)

    def test_medication_database_lookup(self):
        """Test medication database lookup"""
        ip = ImagePreprocessing()
        
        # Check that medication database exists and has entries
        assert len(ip.MEDICATION_DATABASE) > 0
        assert "L544" in ip.MEDICATION_DATABASE

    def test_prohibited_analyses_list(self):
        """Test prohibited analyses list"""
        ip = ImagePreprocessing()
        
        # Check that prohibited analyses are defined
        assert len(ip.PROHIBITED_ANALYSES) > 0
        assert "diagnosis" in ip.PROHIBITED_ANALYSES
        assert "treatment_recommendation" in ip.PROHIBITED_ANALYSES


class TestIntegration:
    """Integration tests for complete image preprocessing workflow"""

    def test_complete_medication_workflow(self):
        """Test complete medication identification workflow"""
        config = ImagePreprocessingConfig(
            enable_medication_identification=True,
            min_confidence_threshold=0.7
        )
        ip = ImagePreprocessing(config)
        
        # Create medication image
        image_data = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)
        patient_medications = ["Acetaminophen"]
        
        # Validate image
        assert ip.validate_image(image_data)
        
        # Analyze image
        result = ip.analyze_image(
            image_data,
            patient_id="patient-789",
            patient_medications=patient_medications
        )
        
        # Verify result
        assert isinstance(result, ImageAnalysisResult)
        assert result.safety_level in SafetyLevel
        assert len(result.descriptive_findings) > 0

    def test_complete_device_workflow(self):
        """Test complete medical device recognition workflow"""
        config = ImagePreprocessingConfig(
            enable_device_recognition=True
        )
        ip = ImagePreprocessing(config)
        
        # Create device image
        image_data = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)
        
        # Analyze image
        result = ip.analyze_image(image_data)
        
        # Verify result
        assert isinstance(result, ImageAnalysisResult)
        assert result.processing_time_ms > 0.0

    def test_workflow_with_safety_checks(self):
        """Test workflow with comprehensive safety checks"""
        config = ImagePreprocessingConfig(
            min_confidence_threshold=0.8,
            analysis_scope=AnalysisScope.IDENTIFICATION_ONLY
        )
        ip = ImagePreprocessing(config)
        
        # Create image
        image_data = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)
        
        # Analyze with safety checks
        result = ip.analyze_image(image_data)
        
        # Verify safety checks were applied
        assert result.analysis_scope == AnalysisScope.IDENTIFICATION_ONLY
        assert result.safety_level in SafetyLevel
        
        # Verify no prohibited content
        boundaries = ip.get_safety_boundaries()
        for finding in result.descriptive_findings:
            for prohibited in boundaries["prohibited_analyses"]:
                assert prohibited not in finding.lower()
