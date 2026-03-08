"""
Property-Based Tests for Accessibility Standards Compliance

Feature: caretale-ai
Property 2: Accessibility Standards Compliance

For any patient interaction, the Multimodal Interface should provide WCAG 2.1 AA
compliant outputs with appropriate accessibility features based on patient needs.

**Validates: Requirements 1.5, 11.1, 11.2, 11.3, 11.4, 11.5**
"""

import pytest
from hypothesis import given, strategies as st, assume, settings
from unittest.mock import patch

from src.patient_interaction.multimodal_interface import MultimodalInterface
from src.patient_interaction.accessibility import (
    AccessibilityChecker,
    WCAGLevel,
)
from src.models.patient_profile import AccessibilitySettings


# Custom strategies for generating accessibility settings

@st.composite
def accessibility_settings_strategy(draw):
    """Generate valid AccessibilitySettings instances with various configurations"""
    return AccessibilitySettings(
        screen_reader_enabled=draw(st.booleans()),
        high_contrast_mode=draw(st.booleans()),
        font_size=draw(st.sampled_from(['small', 'medium', 'large', 'extra-large'])),
        voice_output_enabled=draw(st.booleans()),
        keyboard_navigation_only=draw(st.booleans())
    )


@st.composite
def html_content_strategy(draw):
    """Generate HTML content with various accessibility challenges"""
    content_options = [
        # Content with images
        '<div><img src="test.jpg" alt="Test image"><p>Content with image</p></div>',
        '<div><img src="test.jpg"><p>Content with image missing alt text</p></div>',
        
        # Content with headings
        '<div><h1>Title</h1><h2>Subtitle</h2><p>Content</p></div>',
        '<div><h1>Title</h1><h3>Skipped level</h3><p>Content</p></div>',
        
        # Content with interactive elements
        '<div><button>Click me</button><a href="#">Link</a></div>',
        '<div><button aria-label="Submit">Submit</button><a href="#" aria-label="Home">Home</a></div>',
        '<div onclick="alert()">Clickable div</div>',
        
        # Content with color contrast issues
        '<div style="color: #ccc; background: #fff;">Low contrast text</div>',
        '<div style="color: #000; background: #fff;">Good contrast text</div>',
        
        # Content with focus indicators
        '<style>button:focus { outline: 2px solid blue; }</style><button>Focusable</button>',
        '<button>No focus style</button>',
        
        # Complex content
        """
        <div>
          <header role="banner"><h1>Care Instructions</h1></header>
          <nav role="navigation"><a href="#main">Skip to content</a></nav>
          <main role="main" id="main">
            <h2>Medication Schedule</h2>
            <p>Take your medication as prescribed.</p>
            <img src="pill.jpg" alt="Medication reminder">
            <button aria-label="Set reminder">Set Reminder</button>
          </main>
          <footer role="contentinfo">Contact your care team</footer>
        </div>
        """,
    ]
    return draw(st.sampled_from(content_options))


@st.composite
def patient_id_strategy(draw):
    """Generate valid patient IDs"""
    prefix = draw(st.sampled_from(['patient', 'pat', 'p']))
    suffix = draw(st.text(
        alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd'), whitelist_characters='-'),
        min_size=1,
        max_size=45
    ))
    return f'{prefix}-{suffix}'


@st.composite
def hex_color_strategy(draw):
    """Generate hex colors for contrast testing"""
    hex_chars = '0123456789ABCDEF'
    color = ''.join(draw(st.lists(st.sampled_from(hex_chars), min_size=6, max_size=6)))
    return f'#{color}'


class TestAccessibilityStandardsCompliance:
    """
    Property 2: Accessibility Standards Compliance
    
    For any patient interaction, the Multimodal Interface should provide WCAG 2.1 AA
    compliant outputs with appropriate accessibility features based on patient needs.
    
    **Validates: Requirements 1.5, 11.1, 11.2, 11.3, 11.4, 11.5**
    """

    @given(
        content=html_content_strategy(),
        patient_id=patient_id_strategy(),
        settings=accessibility_settings_strategy()
    )
    @settings(max_examples=100)
    def test_property_wcag_aa_compliance(self, content, patient_id, settings):
        """
        Property 2.1: WCAG 2.1 AA Compliance
        
        **Validates: Requirements 1.5, 11.1**
        
        THE Multimodal_Interface SHALL comply with WCAG 2.1 AA accessibility standards.
        """
        checker = AccessibilityChecker()
        
        # Check WCAG compliance
        compliance_result = checker.check_wcag_compliance(content, settings)
        
        # Verify compliance check is performed
        assert compliance_result is not None, "Compliance check should return a result"
        assert hasattr(compliance_result, 'compliant'), "Result should have compliant field"
        assert hasattr(compliance_result, 'level'), "Result should have level field"
        assert hasattr(compliance_result, 'issues'), "Result should have issues field"
        assert hasattr(compliance_result, 'recommendations'), "Result should have recommendations field"
        
        # Verify level is AA
        assert compliance_result.level == WCAGLevel.AA, "Compliance level should be AA"
        
        # Verify issues are properly categorized
        assert isinstance(compliance_result.issues, list), "Issues should be a list"
        for issue in compliance_result.issues:
            assert hasattr(issue, 'criterion'), "Issue should have criterion"
            assert hasattr(issue, 'severity'), "Issue should have severity"
            assert hasattr(issue, 'description'), "Issue should have description"
            assert issue.severity in ['error', 'warning', 'info'], \
                f"Severity should be error, warning, or info, got {issue.severity}"
        
        # If compliant, there should be no error-level issues
        if compliance_result.compliant:
            error_issues = [i for i in compliance_result.issues if i.severity == 'error']
            assert len(error_issues) == 0, "Compliant content should have no error-level issues"
        
        # Verify recommendations are provided based on settings
        assert isinstance(compliance_result.recommendations, list), \
            "Recommendations should be a list"
        if settings.screen_reader_enabled:
            assert any('screen reader' in r.lower() for r in compliance_result.recommendations), \
                "Screen reader recommendations should be provided when enabled"
        if settings.high_contrast_mode:
            assert any('high contrast' in r.lower() for r in compliance_result.recommendations), \
                "High contrast recommendations should be provided when enabled"

    @given(
        content=html_content_strategy(),
        patient_id=patient_id_strategy()
    )
    @settings(max_examples=100)
    def test_property_screen_reader_compatibility(self, content, patient_id):
        """
        Property 2.2: Screen Reader Compatibility
        
        **Validates: Requirements 11.2**
        
        WHEN patients have visual impairments, THE Multimodal_Interface SHALL
        provide screen reader compatible outputs.
        """
        checker = AccessibilityChecker()
        
        # Apply screen reader enhancements
        enhanced = checker.enhance_for_screen_reader(content)
        
        # Verify screen reader enhancements are applied
        assert enhanced is not None, "Enhanced content should be returned"
        assert isinstance(enhanced, str), "Enhanced content should be a string"
        
        # Check for ARIA landmarks
        has_landmarks = any(role in enhanced for role in [
            'role="banner"', 'role="navigation"', 'role="main"', 'role="contentinfo"'
        ])
        
        # Check for skip navigation
        has_skip_nav = 'skip' in enhanced.lower() and 'content' in enhanced.lower()
        
        # Check for alt text on images
        import re
        img_tags = re.findall(r'<img[^>]*>', enhanced, re.IGNORECASE)
        all_images_have_alt = all(re.search(r'alt=', tag, re.IGNORECASE) for tag in img_tags) if img_tags else True
        
        # At least some screen reader features should be present
        assert has_landmarks or has_skip_nav or all_images_have_alt, \
            "Screen reader enhancements should include landmarks, skip nav, or alt text"

    @given(
        content=st.text(min_size=10, max_size=1000),
        patient_id=patient_id_strategy()
    )
    @settings(max_examples=100)
    @pytest.mark.asyncio
    async def test_property_visual_alternatives_for_hearing_impaired(self, content, patient_id):
        """
        Property 2.3: Visual Alternatives for Hearing Impairments
        
        **Validates: Requirements 11.3**
        
        WHEN patients have hearing impairments, THE Multimodal_Interface SHALL
        offer visual alternatives to audio content.
        """
        # Ensure content is not just whitespace
        assume(content.strip())
        
        interface = MultimodalInterface()
        
        # Request audio format output
        from src.models.interaction_record import OutputFormat
        audio_response = await interface.format_response(content, OutputFormat.AUDIO)
        
        # Verify visual alternatives are available
        assert audio_response.accessibility_features is not None, \
            "Accessibility features should be provided"
        
        # Audio output should include transcript or visual alternatives
        has_visual_alternative = any(
            'transcript' in feat.lower() or 
            'text' in feat.lower() or
            'visual' in feat.lower()
            for feat in audio_response.accessibility_features
        )
        
        assert has_visual_alternative, \
            "Audio output should include transcript or visual alternatives"

    @given(
        foreground=hex_color_strategy(),
        background=hex_color_strategy()
    )
    @settings(max_examples=100)
    def test_property_color_contrast_compliance(self, foreground, background):
        """
        Property 2.4: Color Contrast Compliance
        
        **Validates: Requirements 11.1**
        
        Color contrast ratios should meet WCAG AA standards (4.5:1 for normal text).
        """
        checker = AccessibilityChecker()
        
        # Calculate contrast ratio
        contrast_result = checker.calculate_contrast_ratio(foreground, background)
        
        # Verify contrast result structure
        assert contrast_result is not None, "Contrast result should be returned"
        assert hasattr(contrast_result, 'ratio'), "Result should have ratio field"
        assert hasattr(contrast_result, 'passes_aa'), "Result should have passes_aa field"
        assert hasattr(contrast_result, 'passes_aaa'), "Result should have passes_aaa field"
        
        # Verify ratio is a positive number
        assert contrast_result.ratio > 0, "Contrast ratio should be positive"
        assert not (contrast_result.ratio != contrast_result.ratio), "Ratio should not be NaN"  # NaN check
        
        # Verify AA/AAA flags are consistent with ratio
        if contrast_result.ratio >= 4.5:
            assert contrast_result.passes_aa, \
                f"Ratio {contrast_result.ratio} >= 4.5 should pass AA"
        else:
            assert not contrast_result.passes_aa, \
                f"Ratio {contrast_result.ratio} < 4.5 should not pass AA"
        
        if contrast_result.ratio >= 7.0:
            assert contrast_result.passes_aaa, \
                f"Ratio {contrast_result.ratio} >= 7.0 should pass AAA"
        else:
            assert not contrast_result.passes_aaa, \
                f"Ratio {contrast_result.ratio} < 7.0 should not pass AAA"
        
        # AAA passing implies AA passing
        if contrast_result.passes_aaa:
            assert contrast_result.passes_aa, \
                "AAA passing should imply AA passing"

    @given(
        element_type=st.sampled_from(['button', 'link', 'input', 'select', 'div']),
        label=st.text(min_size=1, max_size=100)
    )
    @settings(max_examples=100)
    def test_property_keyboard_navigation_support(self, element_type, label):
        """
        Property 2.5: Keyboard Navigation Support
        
        **Validates: Requirements 11.1**
        
        All interactive elements should be keyboard accessible with proper
        navigation configuration.
        """
        # Ensure label is not just whitespace
        assume(label.strip())
        
        checker = AccessibilityChecker()
        
        # Generate keyboard navigation config
        nav_config = checker.generate_keyboard_nav_config(element_type, label)
        
        # Verify navigation config structure
        assert nav_config is not None, "Navigation config should be returned"
        assert hasattr(nav_config, 'tab_index'), "Config should have tab_index"
        assert hasattr(nav_config, 'aria_label'), "Config should have aria_label"
        assert hasattr(nav_config, 'keyboard_shortcuts'), "Config should have keyboard_shortcuts"
        
        # Verify tabIndex is set for keyboard accessibility
        assert nav_config.tab_index == 0, "Tab index should be 0 for keyboard accessibility"
        
        # Verify aria label is provided
        assert nav_config.aria_label == label, "ARIA label should match provided label"
        
        # Verify keyboard shortcuts are defined
        assert nav_config.keyboard_shortcuts is not None, "Keyboard shortcuts should be defined"
        assert len(nav_config.keyboard_shortcuts) > 0, "At least one keyboard shortcut should be defined"
        
        # Verify element-specific shortcuts
        if element_type == 'button':
            assert 'Enter' in nav_config.keyboard_shortcuts or \
                   'Space' in nav_config.keyboard_shortcuts, \
                "Button should have Enter or Space shortcut"
        elif element_type == 'link':
            assert 'Enter' in nav_config.keyboard_shortcuts, \
                "Link should have Enter shortcut"

    @given(
        content=html_content_strategy(),
        patient_id=patient_id_strategy()
    )
    @settings(max_examples=100)
    def test_property_high_contrast_mode_application(self, content, patient_id):
        """
        Property 2.6: High Contrast Mode Application
        
        **Validates: Requirements 11.1**
        
        When high contrast mode is enabled, appropriate styles should be applied
        to ensure visibility.
        """
        checker = AccessibilityChecker()
        
        # Apply high contrast mode
        high_contrast = checker.apply_high_contrast_mode(content)
        
        # Verify high contrast styles are applied
        assert high_contrast is not None, "High contrast content should be returned"
        assert isinstance(high_contrast, str), "High contrast content should be a string"
        
        # Check for high contrast class
        assert 'high-contrast' in high_contrast, \
            "High contrast class should be applied"
        
        # Check for high contrast styles
        assert 'background-color' in high_contrast, \
            "Background color should be specified"
        assert 'color' in high_contrast, \
            "Text color should be specified"
        
        # Verify styles include high contrast colors
        import re
        has_black_background = bool(re.search(r'#000000|#000|black', high_contrast, re.IGNORECASE))
        has_white_text = bool(re.search(r'#FFFFFF|#FFF|white', high_contrast, re.IGNORECASE))
        
        assert has_black_background or has_white_text, \
            "High contrast mode should include black/white colors"

    @given(
        content=html_content_strategy(),
        patient_id=patient_id_strategy(),
        settings=accessibility_settings_strategy()
    )
    @settings(max_examples=100)
    def test_property_accessibility_features_match_patient_needs(self, content, patient_id, settings):
        """
        Property 2.7: Accessibility Features Based on Patient Needs
        
        **Validates: Requirements 1.5, 11.4, 11.5**
        
        Appropriate accessibility features should be provided based on patient
        accessibility settings and needs.
        """
        interface = MultimodalInterface()
        checker = AccessibilityChecker()
        
        # Mock the accessibility settings for this patient
        with patch.object(interface, 'get_accessibility_options', return_value=settings):
            # Apply accessibility enhancements
            enhanced = interface.apply_accessibility_enhancements(content, patient_id)
            
            # Verify enhancements match settings
            assert enhanced is not None, "Enhanced content should be returned"
            
            # If screen reader enabled, check for screen reader features
            if settings.screen_reader_enabled:
                has_screen_reader_features = (
                    any(role in enhanced for role in [
                        'role="banner"', 'role="navigation"', 'role="main"', 'role="contentinfo"'
                    ]) or
                    'skip' in enhanced.lower() and 'content' in enhanced.lower() or
                    'aria-' in enhanced
                )
                assert has_screen_reader_features, \
                    "Screen reader features should be present when enabled"
            
            # If high contrast mode enabled, check for high contrast styles
            if settings.high_contrast_mode:
                assert 'high-contrast' in enhanced, \
                    "High contrast class should be applied when enabled"
            
            # If font size is not medium, check for font size adjustment
            if settings.font_size != 'medium':
                assert 'font-size' in enhanced, \
                    "Font size adjustment should be applied when not medium"
