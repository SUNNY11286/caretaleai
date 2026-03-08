"""
Input Normalization Component
Creates consistent internal representations from diverse inputs through text cleaning,
entity extraction, and intent classification.

Features:
- Text cleaning and preprocessing
- Medical entity extraction
- Intent classification for routing
- Standardized request object creation

References: Design Document Multimodal Ingestion Layer
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import re


class InputType(str, Enum):
    """Type of input received"""
    TEXT = "text"
    VOICE_TRANSCRIPT = "voice_transcript"
    IMAGE_ANALYSIS = "image_analysis"


class IntentType(str, Enum):
    """Classified intent for routing to appropriate pipeline"""
    CARE_STORY_REQUEST = "care_story_request"
    MEDICATION_QUESTION = "medication_question"
    UNDERSTANDING_CLARIFICATION = "understanding_clarification"
    FOLLOW_UP_QUERY = "follow_up_query"
    GENERAL_QUESTION = "general_question"
    EMERGENCY = "emergency"
    UNKNOWN = "unknown"


class EntityType(str, Enum):
    """Types of entities that can be extracted"""
    MEDICATION = "medication"
    SYMPTOM = "symptom"
    BODY_PART = "body_part"
    PROCEDURE = "procedure"
    TIME_REFERENCE = "time_reference"
    DOSAGE = "dosage"
    FREQUENCY = "frequency"


@dataclass
class ExtractedEntity:
    """Represents an extracted entity from input text"""
    entity_type: EntityType
    text: str
    normalized_value: str
    confidence: float
    start_position: int
    end_position: int


class NormalizedRequest(BaseModel):
    """Standardized request object for AI orchestrator"""
    original_input: str
    cleaned_text: str
    input_type: InputType
    intent: IntentType
    intent_confidence: float
    extracted_entities: List[ExtractedEntity]
    patient_id: Optional[str] = None
    context: Dict[str, Any] = Field(default_factory=dict)
    requires_emergency_response: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class InputNormalizationConfig(BaseModel):
    """Configuration for input normalization"""
    enable_spell_correction: bool = True
    enable_entity_extraction: bool = True
    enable_intent_classification: bool = True
    min_confidence_threshold: float = Field(default=0.6, ge=0.0, le=1.0)
    max_input_length: int = Field(default=5000, ge=100, le=50000)
    enable_profanity_filter: bool = False


class InputNormalization:
    """
    Input Normalization Component
    Processes diverse inputs into standardized request objects
    """

    # Emergency keywords that trigger immediate flagging
    EMERGENCY_KEYWORDS = {
        "emergency", "911", "chest pain", "can't breathe", "can't breathe",
        "severe pain", "bleeding heavily", "heavy bleeding", "unconscious", "seizure",
        "heart attack", "stroke", "suicide", "overdose", "choking",
        "severe bleeding", "difficulty breathing", "unresponsive"
    }

    # Intent classification patterns
    INTENT_PATTERNS = {
        IntentType.MEDICATION_QUESTION: [
            r'\b(medication|medicine|pill|drug|prescription|dose|dosage)\b',
            r'\b(take|taking|when to take|how to take|how much)\b',
            r'\b(side effect|interaction|contraindication)\b'
        ],
        IntentType.CARE_STORY_REQUEST: [
            r'\b(discharge|care plan|instructions|what should i do)\b',
            r'\b(explain|understand|tell me about|what does)\b',
            r'\b(recovery|healing|getting better)\b'
        ],
        IntentType.UNDERSTANDING_CLARIFICATION: [
            r'\b(confused|don\'t understand|unclear|what does.*mean)\b',
            r'\b(explain again|clarify|help me understand)\b',
            r'\b(i don\'t get|not sure|uncertain)\b'
        ],
        IntentType.FOLLOW_UP_QUERY: [
            r'\b(appointment|follow.?up|when should i|schedule)\b',
            r'\b(reminder|remind me|notification)\b',
            r'\b(next step|what\'s next|then what)\b'
        ],
        IntentType.EMERGENCY: [
            r'\b(emergency|urgent|911|help)\b',
            r'\b(severe|intense|unbearable|extreme)\b.*\b(pain|bleeding)\b',
            r'\b(can\'t breathe|difficulty breathing|chest pain)\b'
        ]
    }

    # Medical entity patterns
    ENTITY_PATTERNS = {
        EntityType.MEDICATION: [
            # Common medication names
            r'\b(aspirin|ibuprofen|acetaminophen|tylenol|advil|insulin|metformin)\b',
            r'\b(lisinopril|atorvastatin|omeprazole|albuterol|gabapentin)\b',
            r'\b(antibiotic|painkiller|blood thinner|beta.?blocker)\b'
        ],
        EntityType.SYMPTOM: [
            r'\b(pain|ache|nausea|dizziness|fever|headache|fatigue)\b',
            r'\b(swelling|redness|itching|rash|cough|congestion)\b',
            r'\b(shortness of breath|chest pain|abdominal pain)\b'
        ],
        EntityType.BODY_PART: [
            r'\b(head|neck|chest|abdomen|stomach|back|arm|leg|hand|foot)\b',
            r'\b(heart|lung|kidney|liver|brain|spine|joint|muscle|bone)\b',
            r'\b(eye|ear|nose|throat|mouth|tooth|teeth)\b'
        ],
        EntityType.DOSAGE: [
            r'\b(\d+)\s*(mg|milligram|g|gram|ml|milliliter|mcg|microgram)\b',
            r'\b(one|two|three|four|five)\s*(tablet|pill|capsule|dose)\b'
        ],
        EntityType.FREQUENCY: [
            r'\b(once|twice|three times|four times)\s*(a|per)?\s*(day|daily|week|weekly)\b',
            r'\b(every|each)\s*(\d+)?\s*(hour|day|week|morning|evening|night)\b',
            r'\b(before|after|with)\s*(meal|food|breakfast|lunch|dinner)\b'
        ],
        EntityType.TIME_REFERENCE: [
            r'\b(today|tomorrow|yesterday|tonight)\b',
            r'\b(this|next|last)\s*(morning|afternoon|evening|night|week|month)\b',
            r'\b(in|after)\s*(\d+)\s*(hour|day|week|month)\b'
        ]
    }

    # Common medical abbreviations and their expansions
    MEDICAL_ABBREVIATIONS = {
        "bp": "blood pressure",
        "hr": "heart rate",
        "temp": "temperature",
        "rx": "prescription",
        "med": "medication",
        "meds": "medications",
        "appt": "appointment",
        "dr": "doctor",
        "pt": "patient",
        "tx": "treatment",
        "dx": "diagnosis",
        "sx": "symptoms",
        "hx": "history",
        "po": "by mouth",
        "prn": "as needed",
        "bid": "twice daily",
        "tid": "three times daily",
        "qid": "four times daily",
        "qd": "once daily",
        "hs": "at bedtime",
        "ac": "before meals",
        "pc": "after meals"
    }

    def __init__(self, config: Optional[InputNormalizationConfig] = None):
        """
        Initialize Input Normalization component
        
        Args:
            config: Input normalization configuration
        """
        self.config = config or InputNormalizationConfig()
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Compile regex patterns for efficiency"""
        self._intent_patterns_compiled = {
            intent: [re.compile(pattern, re.IGNORECASE) 
                    for pattern in patterns]
            for intent, patterns in self.INTENT_PATTERNS.items()
        }
        
        self._entity_patterns_compiled = {
            entity_type: [re.compile(pattern, re.IGNORECASE)
                         for pattern in patterns]
            for entity_type, patterns in self.ENTITY_PATTERNS.items()
        }

    def normalize_input(
        self,
        input_text: str,
        input_type: InputType = InputType.TEXT,
        patient_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> NormalizedRequest:
        """
        Normalize input into standardized request object
        
        Args:
            input_text: Raw input text
            input_type: Type of input (text, voice transcript, image analysis)
            patient_id: Optional patient identifier
            context: Optional context information
            
        Returns:
            Normalized request object ready for orchestrator routing
        """
        # Validate input length
        if len(input_text) > self.config.max_input_length:
            input_text = input_text[:self.config.max_input_length]

        # Clean the input text
        cleaned_text = self.clean_text(input_text)

        # Check for emergency
        requires_emergency = self._detect_emergency(cleaned_text)

        # Extract entities
        entities = []
        if self.config.enable_entity_extraction:
            entities = self.extract_entities(cleaned_text)

        # Classify intent
        intent = IntentType.UNKNOWN
        intent_confidence = 0.0
        if self.config.enable_intent_classification:
            intent, intent_confidence = self.classify_intent(cleaned_text, entities)

        # Override intent if emergency detected
        if requires_emergency:
            intent = IntentType.EMERGENCY
            intent_confidence = 1.0

        # Create normalized request
        return NormalizedRequest(
            original_input=input_text,
            cleaned_text=cleaned_text,
            input_type=input_type,
            intent=intent,
            intent_confidence=intent_confidence,
            extracted_entities=entities,
            patient_id=patient_id,
            context=context or {},
            requires_emergency_response=requires_emergency,
            metadata={
                "input_length": len(input_text),
                "cleaned_length": len(cleaned_text),
                "entity_count": len(entities)
            }
        )

    def clean_text(self, text: str) -> str:
        """
        Clean and preprocess input text
        
        Args:
            text: Raw input text
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""

        # Convert to lowercase for processing (preserve original for display)
        cleaned = text.strip()

        # Remove excessive whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned)

        # Expand common medical abbreviations
        cleaned = self._expand_abbreviations(cleaned)

        # Apply spell correction if enabled
        if self.config.enable_spell_correction:
            cleaned = self._apply_spell_correction(cleaned)

        # Remove profanity if enabled
        if self.config.enable_profanity_filter:
            cleaned = self._filter_profanity(cleaned)

        return cleaned.strip()

    def _expand_abbreviations(self, text: str) -> str:
        """
        Expand common medical abbreviations
        
        Args:
            text: Input text
            
        Returns:
            Text with expanded abbreviations
        """
        # Create word boundary pattern for each abbreviation
        expanded = text
        for abbr, expansion in self.MEDICAL_ABBREVIATIONS.items():
            # Match abbreviation with word boundaries
            pattern = r'\b' + re.escape(abbr) + r'\b'
            expanded = re.sub(pattern, expansion, expanded, flags=re.IGNORECASE)
        
        return expanded

    def _apply_spell_correction(self, text: str) -> str:
        """
        Apply basic spell correction for common medical terms
        
        Args:
            text: Input text
            
        Returns:
            Spell-corrected text
        """
        # Common misspellings and corrections
        corrections = {
            "medecine": "medicine",
            "perscription": "prescription",
            "docter": "doctor",
            "symtom": "symptom",
            "symtoms": "symptoms",
            "apointment": "appointment",
            "ibuprofin": "ibuprofen",
            "acetominophen": "acetaminophen",
            "dizzy": "dizzy",
            "nausia": "nausea",
            "feaver": "fever"
        }

        corrected = text
        for wrong, right in corrections.items():
            pattern = r'\b' + re.escape(wrong) + r'\b'
            corrected = re.sub(pattern, right, corrected, flags=re.IGNORECASE)

        return corrected

    def _filter_profanity(self, text: str) -> str:
        """
        Filter profanity from text
        
        Args:
            text: Input text
            
        Returns:
            Filtered text
        """
        # In production, would use a comprehensive profanity filter
        # For now, return text as-is
        return text

    def _detect_emergency(self, text: str) -> bool:
        """
        Detect emergency situations from text
        
        Args:
            text: Cleaned input text
            
        Returns:
            True if emergency detected
        """
        text_lower = text.lower()
        
        # Check for emergency keywords
        for keyword in self.EMERGENCY_KEYWORDS:
            if keyword in text_lower:
                return True

        # Check for emergency patterns
        emergency_patterns = self._intent_patterns_compiled.get(
            IntentType.EMERGENCY, []
        )
        for pattern in emergency_patterns:
            if pattern.search(text):
                return True

        return False

    def extract_entities(self, text: str) -> List[ExtractedEntity]:
        """
        Extract medical entities from text
        
        Args:
            text: Cleaned input text
            
        Returns:
            List of extracted entities
        """
        entities = []

        # Extract each entity type
        for entity_type, patterns in self._entity_patterns_compiled.items():
            for pattern in patterns:
                for match in pattern.finditer(text):
                    entity = ExtractedEntity(
                        entity_type=entity_type,
                        text=match.group(0),
                        normalized_value=self._normalize_entity_value(
                            match.group(0),
                            entity_type
                        ),
                        confidence=0.85,  # Base confidence for pattern matching
                        start_position=match.start(),
                        end_position=match.end()
                    )
                    entities.append(entity)

        # Remove duplicate entities (same position)
        entities = self._deduplicate_entities(entities)

        return entities

    def _normalize_entity_value(
        self,
        text: str,
        entity_type: EntityType
    ) -> str:
        """
        Normalize entity value for consistency
        
        Args:
            text: Entity text
            entity_type: Type of entity
            
        Returns:
            Normalized value
        """
        # Convert to lowercase for normalization
        normalized = text.lower().strip()

        # Type-specific normalization
        if entity_type == EntityType.MEDICATION:
            # Standardize medication names
            normalized = normalized.replace("-", " ")
        elif entity_type == EntityType.DOSAGE:
            # Standardize dosage format
            normalized = re.sub(r'\s+', '', normalized)
        elif entity_type == EntityType.FREQUENCY:
            # Standardize frequency expressions
            normalized = normalized.replace("per", "a")

        return normalized

    def _deduplicate_entities(
        self,
        entities: List[ExtractedEntity]
    ) -> List[ExtractedEntity]:
        """
        Remove duplicate entities based on position overlap
        
        Args:
            entities: List of extracted entities
            
        Returns:
            Deduplicated list
        """
        if not entities:
            return []

        # Sort by start position
        sorted_entities = sorted(entities, key=lambda e: e.start_position)

        # Remove overlapping entities, keeping higher confidence ones
        deduplicated = []
        for entity in sorted_entities:
            # Check if overlaps with any existing entity
            overlaps = False
            for existing in deduplicated:
                if self._entities_overlap(entity, existing):
                    overlaps = True
                    # Replace if higher confidence
                    if entity.confidence > existing.confidence:
                        deduplicated.remove(existing)
                        deduplicated.append(entity)
                    break

            if not overlaps:
                deduplicated.append(entity)

        return deduplicated

    def _entities_overlap(
        self,
        entity1: ExtractedEntity,
        entity2: ExtractedEntity
    ) -> bool:
        """
        Check if two entities overlap in position
        
        Args:
            entity1: First entity
            entity2: Second entity
            
        Returns:
            True if entities overlap
        """
        return not (
            entity1.end_position <= entity2.start_position or
            entity2.end_position <= entity1.start_position
        )

    def classify_intent(
        self,
        text: str,
        entities: List[ExtractedEntity]
    ) -> tuple[IntentType, float]:
        """
        Classify the intent of the input text
        
        Args:
            text: Cleaned input text
            entities: Extracted entities
            
        Returns:
            Tuple of (intent_type, confidence)
        """
        # Score each intent based on pattern matches
        intent_scores = {}

        for intent, patterns in self._intent_patterns_compiled.items():
            score = 0.0
            matches = 0

            for pattern in patterns:
                if pattern.search(text):
                    matches += 1

            if matches > 0:
                # Score based on number of pattern matches
                score = min(1.0, 0.5 + (matches * 0.2))
                intent_scores[intent] = score

        # Boost scores based on entity types
        entity_type_counts = {}
        for entity in entities:
            entity_type_counts[entity.entity_type] = \
                entity_type_counts.get(entity.entity_type, 0) + 1

        # Medication entities boost medication intent
        if EntityType.MEDICATION in entity_type_counts:
            intent_scores[IntentType.MEDICATION_QUESTION] = \
                min(1.0, intent_scores.get(IntentType.MEDICATION_QUESTION, 0.0) + 0.2)

        # Time references boost follow-up intent
        if EntityType.TIME_REFERENCE in entity_type_counts:
            intent_scores[IntentType.FOLLOW_UP_QUERY] = \
                min(1.0, intent_scores.get(IntentType.FOLLOW_UP_QUERY, 0.0) + 0.1)

        # Get highest scoring intent
        if intent_scores:
            best_intent = max(intent_scores.items(), key=lambda x: x[1])
            if best_intent[1] >= self.config.min_confidence_threshold:
                return best_intent[0], min(1.0, best_intent[1])  # Cap at 1.0

        # Default to general question if no strong intent detected
        return IntentType.GENERAL_QUESTION, 0.5

    def validate_input(self, text: str) -> tuple[bool, Optional[str]]:
        """
        Validate input text
        
        Args:
            text: Input text to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not text or not text.strip():
            return False, "Input text is empty"

        if len(text) > self.config.max_input_length:
            return False, f"Input exceeds maximum length of {self.config.max_input_length}"

        # Check for valid characters (allow most unicode)
        if not text.isprintable() and not any(c.isspace() for c in text):
            return False, "Input contains invalid characters"

        return True, None

    def get_intent_description(self, intent: IntentType) -> str:
        """
        Get human-readable description of intent
        
        Args:
            intent: Intent type
            
        Returns:
            Description string
        """
        descriptions = {
            IntentType.CARE_STORY_REQUEST: "Request for care plan explanation or discharge instructions",
            IntentType.MEDICATION_QUESTION: "Question about medications, dosage, or side effects",
            IntentType.UNDERSTANDING_CLARIFICATION: "Request for clarification or additional explanation",
            IntentType.FOLLOW_UP_QUERY: "Question about appointments, reminders, or next steps",
            IntentType.GENERAL_QUESTION: "General health-related question",
            IntentType.EMERGENCY: "Emergency situation requiring immediate attention",
            IntentType.UNKNOWN: "Unable to determine intent"
        }
        return descriptions.get(intent, "Unknown intent type")

    def get_entity_summary(self, entities: List[ExtractedEntity]) -> Dict[str, List[str]]:
        """
        Get summary of extracted entities grouped by type
        
        Args:
            entities: List of extracted entities
            
        Returns:
            Dictionary mapping entity types to lists of entity texts
        """
        summary = {}
        for entity in entities:
            entity_type_str = entity.entity_type.value
            if entity_type_str not in summary:
                summary[entity_type_str] = []
            summary[entity_type_str].append(entity.text)

        return summary
