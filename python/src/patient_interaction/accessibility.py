"""
Accessibility Module
Provides WCAG 2.1 AA compliance checks and accessibility features
for the CARETALE AI system.

References: Requirement 11 (Accessibility and Inclusion)
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Optional
import re

from ..models.patient_profile import AccessibilitySettings


class WCAGLevel(str, Enum):
    """WCAG 2.1 AA compliance levels"""
    A = 'A'
    AA = 'AA'
    AAA = 'AAA'


@dataclass
class AccessibilityIssue:
    """Accessibility issue details"""
    criterion: str
    severity: str  # 'error', 'warning', or 'info'
    description: str
    element: Optional[str] = None


@dataclass
class ComplianceCheckResult:
    """Accessibility compliance check result"""
    compliant: bool
    level: WCAGLevel
    issues: List[AccessibilityIssue]
    recommendations: List[str]


@dataclass
class ContrastRatio:
    """Color contrast ratio result"""
    ratio: float
    passes_aa: bool
    passes_aaa: bool


@dataclass
class KeyboardNavigationConfig:
    """Keyboard navigation configuration"""
    tab_index: int
    aria_label: Optional[str] = None
    aria_described_by: Optional[str] = None
    role: Optional[str] = None
    keyboard_shortcuts: Optional[Dict[str, str]] = None


class AccessibilityChecker:
    """
    Accessibility Checker class
    Implements WCAG 2.1 AA compliance checks
    """

    def check_wcag_compliance(
        self,
        content: str,
        settings: AccessibilitySettings
    ) -> ComplianceCheckResult:
        """
        Check if content meets WCAG 2.1 AA compliance
        
        Args:
            content: HTML content to check
            settings: Accessibility settings to apply
            
        Returns:
            Compliance check result
        """
        issues: List[AccessibilityIssue] = []
        recommendations: List[str] = []

        # Check for alt text on images (WCAG 1.1.1)
        if self._has_images(content) and not self._has_alt_text(content):
            issues.append(AccessibilityIssue(
                criterion='1.1.1 Non-text Content',
                severity='error',
                description='Images must have alternative text',
                element='img'
            ))

        # Check for proper heading structure (WCAG 1.3.1)
        if not self._has_proper_heading_structure(content):
            issues.append(AccessibilityIssue(
                criterion='1.3.1 Info and Relationships',
                severity='warning',
                description='Heading structure should be hierarchical'
            ))

        # Check for color contrast (WCAG 1.4.3)
        contrast_issues = self._check_color_contrast(content)
        issues.extend(contrast_issues)

        # Check for keyboard accessibility (WCAG 2.1.1)
        if not self._is_keyboard_accessible(content):
            issues.append(AccessibilityIssue(
                criterion='2.1.1 Keyboard',
                severity='error',
                description='All functionality must be keyboard accessible'
            ))

        # Check for focus indicators (WCAG 2.4.7)
        if not self._has_focus_indicators(content):
            issues.append(AccessibilityIssue(
                criterion='2.4.7 Focus Visible',
                severity='error',
                description='Interactive elements must have visible focus indicators'
            ))

        # Check for ARIA labels (WCAG 4.1.2)
        if not self._has_proper_aria_labels(content):
            issues.append(AccessibilityIssue(
                criterion='4.1.2 Name, Role, Value',
                severity='warning',
                description='Interactive elements should have proper ARIA labels'
            ))

        # Generate recommendations based on settings
        if settings.screen_reader_enabled:
            recommendations.append('Ensure all content is screen reader compatible')
        if settings.high_contrast_mode:
            recommendations.append('Apply high contrast color scheme')
        if settings.keyboard_navigation_only:
            recommendations.append('Ensure all interactions are keyboard accessible')

        compliant = len([i for i in issues if i.severity == 'error']) == 0

        return ComplianceCheckResult(
            compliant=compliant,
            level=WCAGLevel.AA,
            issues=issues,
            recommendations=recommendations
        )

    def calculate_contrast_ratio(
        self,
        foreground: str,
        background: str
    ) -> ContrastRatio:
        """
        Calculate color contrast ratio between foreground and background
        
        Args:
            foreground: Foreground color in hex format
            background: Background color in hex format
            
        Returns:
            Contrast ratio result
        """
        fg_luminance = self._get_relative_luminance(foreground)
        bg_luminance = self._get_relative_luminance(background)

        lighter = max(fg_luminance, bg_luminance)
        darker = min(fg_luminance, bg_luminance)
        ratio = (lighter + 0.05) / (darker + 0.05)

        return ContrastRatio(
            ratio=ratio,
            passes_aa=ratio >= 4.5,  # WCAG AA requires 4.5:1 for normal text
            passes_aaa=ratio >= 7.0   # WCAG AAA requires 7:1 for normal text
        )

    def apply_high_contrast_mode(self, content: str) -> str:
        """
        Apply high contrast mode to content
        
        Args:
            content: HTML content to modify
            
        Returns:
            Content with high contrast styles applied
        """
        high_contrast_styles = """
      <style>
        .high-contrast {
          background-color: #000000;
          color: #FFFFFF;
        }
        .high-contrast a {
          color: #FFFF00;
        }
        .high-contrast button {
          background-color: #FFFFFF;
          color: #000000;
          border: 2px solid #FFFFFF;
        }
        .high-contrast .focus-visible {
          outline: 3px solid #FFFF00;
          outline-offset: 2px;
        }
      </style>
    """

        return high_contrast_styles + content.replace('<body', '<body class="high-contrast"')

    def generate_keyboard_nav_config(
        self,
        element_type: str,
        label: str
    ) -> KeyboardNavigationConfig:
        """
        Generate keyboard navigation configuration for an element
        
        Args:
            element_type: Type of element (button, link, input, etc.)
            label: Accessible label for the element
            
        Returns:
            Keyboard navigation configuration
        """
        shortcuts = {}

        # Define keyboard shortcuts based on element type
        if element_type == 'button':
            shortcuts = {
                'Enter': 'Activate button',
                'Space': 'Activate button'
            }
        elif element_type == 'link':
            shortcuts = {'Enter': 'Follow link'}
        elif element_type == 'input':
            shortcuts = {
                'Tab': 'Move to next field',
                'Shift+Tab': 'Move to previous field'
            }
        elif element_type == 'select':
            shortcuts = {
                'ArrowDown': 'Open dropdown',
                'ArrowUp': 'Navigate options',
                'Enter': 'Select option'
            }

        return KeyboardNavigationConfig(
            tab_index=0,
            aria_label=label,
            role='button' if element_type == 'div' else None,
            keyboard_shortcuts=shortcuts
        )

    def enhance_for_screen_reader(self, content: str) -> str:
        """
        Enhance content for screen reader compatibility
        
        Args:
            content: HTML content to enhance
            
        Returns:
            Screen reader compatible content
        """
        enhanced = content

        # Add ARIA landmarks
        enhanced = enhanced.replace('<header', '<header role="banner"')
        enhanced = enhanced.replace('<nav', '<nav role="navigation"')
        enhanced = enhanced.replace('<main', '<main role="main"')
        enhanced = enhanced.replace('<footer', '<footer role="contentinfo"')

        # Add skip navigation link
        skip_nav = '<a href="#main-content" class="skip-link">Skip to main content</a>'
        enhanced = enhanced.replace('<body', f'<body>\n{skip_nav}')

        # Ensure all images have alt text
        enhanced = re.sub(r'<img(?![^>]*alt=)', '<img alt=""', enhanced)

        # Add aria-live regions for dynamic content
        enhanced = enhanced.replace(
            '<div class="notification"',
            '<div class="notification" role="alert" aria-live="polite"'
        )

        return enhanced

    # Private helper methods

    def _has_images(self, content: str) -> bool:
        """Check if content contains images"""
        return bool(re.search(r'<img', content, re.IGNORECASE))

    def _has_alt_text(self, content: str) -> bool:
        """Check if all images have alt text"""
        img_tags = re.findall(r'<img[^>]*>', content, re.IGNORECASE)
        return all(re.search(r'alt=', tag, re.IGNORECASE) for tag in img_tags)

    def _has_proper_heading_structure(self, content: str) -> bool:
        """Check if headings are in proper hierarchical order"""
        headings = re.findall(r'<h[1-6]', content, re.IGNORECASE)
        if not headings:
            return True

        # Check if headings are in proper order (no skipping levels)
        last_level = 0
        for heading in headings:
            level = int(heading[2])
            if level > last_level + 1:
                return False
            last_level = level
        return True

    def _check_color_contrast(self, content: str) -> List[AccessibilityIssue]:
        """Check for color contrast issues"""
        issues = []
        
        # In a full implementation, this would parse CSS and check all color combinations
        # For now, we'll check for common patterns
        if 'color: #ccc' in content or 'color: #ddd' in content:
            issues.append(AccessibilityIssue(
                criterion='1.4.3 Contrast (Minimum)',
                severity='warning',
                description='Light gray text may not meet contrast requirements'
            ))

        return issues

    def _is_keyboard_accessible(self, content: str) -> bool:
        """Check if content is keyboard accessible"""
        interactive_elements = re.findall(
            r'<(button|a|input|select|textarea)',
            content,
            re.IGNORECASE
        )
        return len(interactive_elements) > 0 or not re.search(
            r'<div[^>]*onclick',
            content,
            re.IGNORECASE
        )

    def _has_focus_indicators(self, content: str) -> bool:
        """Check if CSS includes focus styles"""
        return bool(re.search(r':focus', content, re.IGNORECASE) or 
                   re.search(r'focus-visible', content, re.IGNORECASE))

    def _has_proper_aria_labels(self, content: str) -> bool:
        """Check if interactive elements have proper ARIA labels"""
        interactive_elements = re.findall(
            r'<(button|a|input)[^>]*>',
            content,
            re.IGNORECASE
        )
        if not interactive_elements:
            return True

        # Check if most interactive elements have aria-label or aria-labelledby
        with_labels = [
            el for el in interactive_elements
            if re.search(r'aria-label', el, re.IGNORECASE) or
               re.search(r'aria-labelledby', el, re.IGNORECASE) or
               re.search(r'>.*</', el, re.IGNORECASE)
        ]
        return len(with_labels) >= len(interactive_elements) * 0.8

    def _get_relative_luminance(self, hex_color: str) -> float:
        """Calculate relative luminance of a color"""
        # Remove # if present
        hex_color = hex_color.replace('#', '')
        
        # Convert to RGB
        r = int(hex_color[0:2], 16) / 255
        g = int(hex_color[2:4], 16) / 255
        b = int(hex_color[4:6], 16) / 255

        # Apply gamma correction
        r_linear = r / 12.92 if r <= 0.03928 else ((r + 0.055) / 1.055) ** 2.4
        g_linear = g / 12.92 if g <= 0.03928 else ((g + 0.055) / 1.055) ** 2.4
        b_linear = b / 12.92 if b <= 0.03928 else ((b + 0.055) / 1.055) ** 2.4

        # Calculate relative luminance
        return 0.2126 * r_linear + 0.7152 * g_linear + 0.0722 * b_linear
