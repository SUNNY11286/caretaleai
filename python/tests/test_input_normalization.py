"""
Unit tests for Input Normalization component
Tests text cleaning, entity extraction, intent classification, and request normalization
"""

import pytest
from src.multimodal_ingestion.input_normalization import (
    InputNormalization,
    InputNormalizationConfig,
    InputType,
    IntentType,
    EntityType,
    ExtractedEntity
)


class TestInputNormalization:
    """Test suite for Input Normalization component"""

    @pytest.fixture
    def normalizer(self):
        """Create input normalizer with default config"""
        return InputNormalization()

    @pytest.fixture
    def normalizer_custom(self):
        """Create input normalizer with custom config"""
        config = InputNormalizationConfig(
            enable_spell_correction=True,
            enable_entity_extraction=True,
            enable_intent_classification=True,
            min_confidence_threshold=0.7
        )
        return InputNormalization(config)

    # Text Cleaning Tests

    def test_clean_text_removes_extra_whitespace(self, normalizer):
        """Test that excessive whitespace is removed"""
        text = "How   do  I   take   my    medication?"
        cleaned = normalizer.clean_text(text)
        assert "  " not in cleaned
        assert cleaned == "How do I take my medication?"

    def test_clean_text_expands_abbreviations(self, normalizer):
        """Test that medical abbreviations are expanded"""
        text = "My bp is high and I need my meds"
        cleaned = normalizer.clean_text(text)
        assert "blood pressure" in cleaned
        assert "medications" in cleaned

    def test_clean_text_handles_empty_input(self, normalizer):
        """Test that empty input is handled gracefully"""
        assert normalizer.clean_text("") == ""
        assert normalizer.clean_text("   ") == ""

    def test_clean_text_spell_correction(self, normalizer):
        """Test that common misspellings are corrected"""
        text = "I have a perscription for ibuprofin"
        cleaned = normalizer.clean_text(text)
        assert "prescription" in cleaned
        assert "ibuprofen" in cleaned

    # Entity Extraction Tests

    def test_extract_medication_entities(self, normalizer):
        """Test extraction of medication entities"""
        text = "I'm taking aspirin and ibuprofen for pain"
        entities = normalizer.extract_entities(text)
        
        medication_entities = [e for e in entities if e.entity_type == EntityType.MEDICATION]
        assert len(medication_entities) >= 2
        
        medication_texts = [e.text.lower() for e in medication_entities]
        assert "aspirin" in medication_texts
        assert "ibuprofen" in medication_texts

    def test_extract_symptom_entities(self, normalizer):
        """Test extraction of symptom entities"""
        text = "I have pain, nausea, and dizziness"
        entities = normalizer.extract_entities(text)
        
        symptom_entities = [e for e in entities if e.entity_type == EntityType.SYMPTOM]
        assert len(symptom_entities) >= 3

    def test_extract_dosage_entities(self, normalizer):
        """Test extraction of dosage entities"""
        text = "Take 500mg twice daily"
        entities = normalizer.extract_entities(text)
        
        dosage_entities = [e for e in entities if e.entity_type == EntityType.DOSAGE]
        assert len(dosage_entities) >= 1
        assert any("500" in e.text for e in dosage_entities)

    def test_extract_frequency_entities(self, normalizer):
        """Test extraction of frequency entities"""
        text = "Take medication twice a day with meals"
        entities = normalizer.extract_entities(text)
        
        frequency_entities = [e for e in entities if e.entity_type == EntityType.FREQUENCY]
        assert len(frequency_entities) >= 1

    def test_extract_body_part_entities(self, normalizer):
        """Test extraction of body part entities"""
        text = "My chest and stomach hurt"
        entities = normalizer.extract_entities(text)
        
        body_part_entities = [e for e in entities if e.entity_type == EntityType.BODY_PART]
        assert len(body_part_entities) >= 2

    def test_extract_time_reference_entities(self, normalizer):
        """Test extraction of time reference entities"""
        text = "I have an appointment tomorrow morning"
        entities = normalizer.extract_entities(text)
        
        time_entities = [e for e in entities if e.entity_type == EntityType.TIME_REFERENCE]
        assert len(time_entities) >= 1

    def test_entity_deduplication(self, normalizer):
        """Test that overlapping entities are deduplicated"""
        text = "chest pain"
        entities = normalizer.extract_entities(text)
        
        # Should not have multiple entities at the same position
        positions = [(e.start_position, e.end_position) for e in entities]
        assert len(positions) == len(set(positions))

    # Intent Classification Tests

    def test_classify_medication_intent(self, normalizer):
        """Test classification of medication-related questions"""
        text = "How should I take my medication?"
        entities = normalizer.extract_entities(text)
        intent, confidence = normalizer.classify_intent(text, entities)
        
        assert intent == IntentType.MEDICATION_QUESTION
        assert confidence > 0.6

    def test_classify_care_story_intent(self, normalizer):
        """Test classification of care story requests"""
        text = "Can you explain my discharge instructions?"
        entities = normalizer.extract_entities(text)
        intent, confidence = normalizer.classify_intent(text, entities)
        
        assert intent == IntentType.CARE_STORY_REQUEST
        assert confidence > 0.6

    def test_classify_clarification_intent(self, normalizer):
        """Test classification of clarification requests"""
        text = "I'm confused about what you said, can you explain again?"
        entities = normalizer.extract_entities(text)
        intent, confidence = normalizer.classify_intent(text, entities)
        
        assert intent == IntentType.UNDERSTANDING_CLARIFICATION
        assert confidence > 0.6

    def test_classify_follow_up_intent(self, normalizer):
        """Test classification of follow-up queries"""
        text = "When is my next appointment?"
        entities = normalizer.extract_entities(text)
        intent, confidence = normalizer.classify_intent(text, entities)
        
        assert intent == IntentType.FOLLOW_UP_QUERY
        assert confidence > 0.6

    def test_classify_emergency_intent(self, normalizer):
        """Test classification of emergency situations"""
        text = "I'm having severe chest pain and can't breathe"
        entities = normalizer.extract_entities(text)
        intent, confidence = normalizer.classify_intent(text, entities)
        
        assert intent == IntentType.EMERGENCY
        assert confidence > 0.6

    def test_classify_general_question_fallback(self, normalizer):
        """Test fallback to general question for unclear intent"""
        text = "What is the weather like?"
        entities = normalizer.extract_entities(text)
        intent, confidence = normalizer.classify_intent(text, entities)
        
        assert intent == IntentType.GENERAL_QUESTION

    # Emergency Detection Tests

    def test_detect_emergency_keywords(self, normalizer):
        """Test detection of emergency keywords"""
        emergency_texts = [
            "I'm having a heart attack",
            "Call 911",
            "Severe chest pain",
            "Can't breathe",
            "Heavy bleeding"
        ]
        
        for text in emergency_texts:
            cleaned = normalizer.clean_text(text)
            is_emergency = normalizer._detect_emergency(cleaned)
            assert is_emergency, f"Failed to detect emergency in: {text}"

    def test_no_false_emergency_detection(self, normalizer):
        """Test that normal text doesn't trigger emergency"""
        normal_texts = [
            "How do I take my medication?",
            "When is my appointment?",
            "I have a mild headache"
        ]
        
        for text in normal_texts:
            cleaned = normalizer.clean_text(text)
            is_emergency = normalizer._detect_emergency(cleaned)
            assert not is_emergency, f"False emergency detected in: {text}"

    # Normalized Request Tests

    def test_normalize_input_creates_valid_request(self, normalizer):
        """Test that normalize_input creates a valid NormalizedRequest"""
        text = "How do I take my aspirin medication?"
        request = normalizer.normalize_input(text, InputType.TEXT, patient_id="P123")
        
        assert request.original_input == text
        assert request.cleaned_text != ""
        assert request.input_type == InputType.TEXT
        assert request.patient_id == "P123"
        assert request.intent in IntentType
        assert 0.0 <= request.intent_confidence <= 1.0
        assert isinstance(request.extracted_entities, list)

    def test_normalize_input_with_emergency(self, normalizer):
        """Test that emergency situations are properly flagged"""
        text = "I'm having severe chest pain"
        request = normalizer.normalize_input(text)
        
        assert request.requires_emergency_response
        assert request.intent == IntentType.EMERGENCY
        assert request.intent_confidence == 1.0

    def test_normalize_input_with_context(self, normalizer):
        """Test that context is preserved in normalized request"""
        text = "What medication should I take?"
        context = {"conversation_id": "conv123", "turn": 5}
        request = normalizer.normalize_input(text, context=context)
        
        assert request.context == context

    def test_normalize_input_truncates_long_text(self, normalizer):
        """Test that excessively long input is truncated"""
        long_text = "a" * 10000
        request = normalizer.normalize_input(long_text)
        
        assert len(request.original_input) <= normalizer.config.max_input_length

    def test_normalize_input_metadata(self, normalizer):
        """Test that metadata is populated correctly"""
        text = "How do I take aspirin?"
        request = normalizer.normalize_input(text)
        
        assert "input_length" in request.metadata
        assert "cleaned_length" in request.metadata
        assert "entity_count" in request.metadata
        assert request.metadata["input_length"] == len(text)

    # Input Validation Tests

    def test_validate_input_accepts_valid_text(self, normalizer):
        """Test that valid input passes validation"""
        valid, error = normalizer.validate_input("How do I take my medication?")
        assert valid
        assert error is None

    def test_validate_input_rejects_empty_text(self, normalizer):
        """Test that empty input is rejected"""
        valid, error = normalizer.validate_input("")
        assert not valid
        assert "empty" in error.lower()

    def test_validate_input_rejects_too_long_text(self, normalizer):
        """Test that excessively long input is rejected"""
        long_text = "a" * 10000
        valid, error = normalizer.validate_input(long_text)
        assert not valid
        assert "length" in error.lower()

    # Utility Method Tests

    def test_get_intent_description(self, normalizer):
        """Test that intent descriptions are returned"""
        for intent in IntentType:
            description = normalizer.get_intent_description(intent)
            assert isinstance(description, str)
            assert len(description) > 0

    def test_get_entity_summary(self, normalizer):
        """Test entity summary generation"""
        text = "I'm taking aspirin for chest pain"
        entities = normalizer.extract_entities(text)
        summary = normalizer.get_entity_summary(entities)
        
        assert isinstance(summary, dict)
        assert len(summary) > 0
        
        # Check that entity types are grouped
        for entity_type, entity_list in summary.items():
            assert isinstance(entity_list, list)
            assert all(isinstance(e, str) for e in entity_list)

    # Edge Cases

    def test_handle_special_characters(self, normalizer):
        """Test handling of special characters"""
        text = "How do I take my medication? (500mg)"
        request = normalizer.normalize_input(text)
        assert request.cleaned_text != ""

    def test_handle_unicode_characters(self, normalizer):
        """Test handling of unicode characters"""
        text = "¿Cómo tomo mi medicación?"
        request = normalizer.normalize_input(text)
        assert request.cleaned_text != ""

    def test_handle_mixed_case(self, normalizer):
        """Test handling of mixed case input"""
        text = "HoW Do I TaKe My MeDiCaTiOn?"
        request = normalizer.normalize_input(text)
        assert request.intent != IntentType.UNKNOWN

    def test_handle_multiple_sentences(self, normalizer):
        """Test handling of multiple sentences"""
        text = "I have chest pain. It started this morning. Should I be worried?"
        request = normalizer.normalize_input(text)
        assert len(request.extracted_entities) > 0

    # Configuration Tests

    def test_custom_confidence_threshold(self):
        """Test that custom confidence threshold is respected"""
        config = InputNormalizationConfig(min_confidence_threshold=0.9)
        normalizer = InputNormalization(config)
        
        text = "medication"  # Weak signal
        entities = normalizer.extract_entities(text)
        intent, confidence = normalizer.classify_intent(text, entities)
        
        # With high threshold, should fall back to general question
        if confidence < 0.9:
            assert intent == IntentType.GENERAL_QUESTION

    def test_disable_entity_extraction(self):
        """Test that entity extraction can be disabled"""
        config = InputNormalizationConfig(enable_entity_extraction=False)
        normalizer = InputNormalization(config)
        
        text = "I'm taking aspirin for pain"
        request = normalizer.normalize_input(text)
        
        assert len(request.extracted_entities) == 0

    def test_disable_intent_classification(self):
        """Test that intent classification can be disabled"""
        config = InputNormalizationConfig(enable_intent_classification=False)
        normalizer = InputNormalization(config)
        
        text = "How do I take my medication?"
        request = normalizer.normalize_input(text)
        
        assert request.intent == IntentType.UNKNOWN
        assert request.intent_confidence == 0.0

    def test_disable_spell_correction(self):
        """Test that spell correction can be disabled"""
        config = InputNormalizationConfig(enable_spell_correction=False)
        normalizer = InputNormalization(config)
        
        text = "perscription"  # Misspelled
        cleaned = normalizer.clean_text(text)
        
        # Should not be corrected
        assert "perscription" in cleaned or "prescription" not in cleaned


class TestEntityExtraction:
    """Focused tests for entity extraction functionality"""

    @pytest.fixture
    def normalizer(self):
        return InputNormalization()

    def test_entity_confidence_scores(self, normalizer):
        """Test that entities have confidence scores"""
        text = "Take aspirin 500mg twice daily"
        entities = normalizer.extract_entities(text)
        
        for entity in entities:
            assert 0.0 <= entity.confidence <= 1.0

    def test_entity_positions(self, normalizer):
        """Test that entity positions are correct"""
        text = "Take aspirin for pain"
        entities = normalizer.extract_entities(text)
        
        for entity in entities:
            assert entity.start_position >= 0
            assert entity.end_position > entity.start_position
            assert entity.end_position <= len(text)
            
            # Verify position matches text
            extracted = text[entity.start_position:entity.end_position]
            assert entity.text.lower() in extracted.lower()

    def test_entity_normalization(self, normalizer):
        """Test that entity values are normalized"""
        text = "Take 500 mg of medication"
        entities = normalizer.extract_entities(text)
        
        dosage_entities = [e for e in entities if e.entity_type == EntityType.DOSAGE]
        if dosage_entities:
            # Normalized value should have no spaces
            assert " " not in dosage_entities[0].normalized_value


class TestIntentClassification:
    """Focused tests for intent classification functionality"""

    @pytest.fixture
    def normalizer(self):
        return InputNormalization()

    def test_intent_confidence_range(self, normalizer):
        """Test that intent confidence is in valid range"""
        texts = [
            "How do I take my medication?",
            "What are my discharge instructions?",
            "I'm confused",
            "When is my appointment?",
            "Emergency help needed"
        ]
        
        for text in texts:
            entities = normalizer.extract_entities(text)
            intent, confidence = normalizer.classify_intent(text, entities)
            assert 0.0 <= confidence <= 1.0

    def test_entity_boosting(self, normalizer):
        """Test that entities boost related intents"""
        # Text with medication entity should boost medication intent
        text_with_med = "What about aspirin?"
        entities_with_med = normalizer.extract_entities(text_with_med)
        intent_with_med, conf_with_med = normalizer.classify_intent(
            text_with_med, entities_with_med
        )
        
        # Text without medication entity
        text_without_med = "What about it?"
        entities_without_med = normalizer.extract_entities(text_without_med)
        intent_without_med, conf_without_med = normalizer.classify_intent(
            text_without_med, entities_without_med
        )
        
        # Medication intent should be more likely with medication entity
        if intent_with_med == IntentType.MEDICATION_QUESTION:
            assert conf_with_med > 0.5
