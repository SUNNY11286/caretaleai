/**
 * Accessibility Module
 * Provides WCAG 2.1 AA compliance checks and accessibility features
 * for the CARETALE AI system.
 * 
 * References: Requirement 11 (Accessibility and Inclusion)
 */

import { AccessibilitySettings } from '../shared/types';

/**
 * WCAG 2.1 AA compliance levels
 */
export enum WCAGLevel {
  A = 'A',
  AA = 'AA',
  AAA = 'AAA',
}

/**
 * Accessibility compliance check result
 */
export interface ComplianceCheckResult {
  compliant: boolean;
  level: WCAGLevel;
  issues: AccessibilityIssue[];
  recommendations: string[];
}

/**
 * Accessibility issue details
 */
export interface AccessibilityIssue {
  criterion: string;
  severity: 'error' | 'warning' | 'info';
  description: string;
  element?: string;
}

/**
 * Color contrast ratio result
 */
export interface ContrastRatio {
  ratio: number;
  passesAA: boolean;
  passesAAA: boolean;
}

/**
 * Keyboard navigation configuration
 */
export interface KeyboardNavigationConfig {
  tabIndex: number;
  ariaLabel?: string;
  ariaDescribedBy?: string;
  role?: string;
  keyboardShortcuts: Map<string, string>;
}

/**
 * Accessibility Checker class
 * Implements WCAG 2.1 AA compliance checks
 */
export class AccessibilityChecker {
  /**
   * Check if content meets WCAG 2.1 AA compliance
   * @param content - HTML content to check
   * @param settings - Accessibility settings to apply
   * @returns Compliance check result
   */
  checkWCAGCompliance(
    content: string,
    settings: AccessibilitySettings
  ): ComplianceCheckResult {
    const issues: AccessibilityIssue[] = [];
    const recommendations: string[] = [];

    // Check for alt text on images (WCAG 1.1.1)
    if (this.hasImages(content) && !this.hasAltText(content)) {
      issues.push({
        criterion: '1.1.1 Non-text Content',
        severity: 'error',
        description: 'Images must have alternative text',
        element: 'img',
      });
    }

    // Check for proper heading structure (WCAG 1.3.1)
    if (!this.hasProperHeadingStructure(content)) {
      issues.push({
        criterion: '1.3.1 Info and Relationships',
        severity: 'warning',
        description: 'Heading structure should be hierarchical',
      });
    }

    // Check for color contrast (WCAG 1.4.3)
    const contrastIssues = this.checkColorContrast(content);
    issues.push(...contrastIssues);

    // Check for keyboard accessibility (WCAG 2.1.1)
    if (!this.isKeyboardAccessible(content)) {
      issues.push({
        criterion: '2.1.1 Keyboard',
        severity: 'error',
        description: 'All functionality must be keyboard accessible',
      });
    }

    // Check for focus indicators (WCAG 2.4.7)
    if (!this.hasFocusIndicators(content)) {
      issues.push({
        criterion: '2.4.7 Focus Visible',
        severity: 'error',
        description: 'Interactive elements must have visible focus indicators',
      });
    }

    // Check for ARIA labels (WCAG 4.1.2)
    if (!this.hasProperARIALabels(content)) {
      issues.push({
        criterion: '4.1.2 Name, Role, Value',
        severity: 'warning',
        description: 'Interactive elements should have proper ARIA labels',
      });
    }

    // Generate recommendations based on settings
    if (settings.screenReaderEnabled) {
      recommendations.push('Ensure all content is screen reader compatible');
    }
    if (settings.highContrastMode) {
      recommendations.push('Apply high contrast color scheme');
    }
    if (settings.keyboardNavigationOnly) {
      recommendations.push('Ensure all interactions are keyboard accessible');
    }

    const compliant = issues.filter((i) => i.severity === 'error').length === 0;

    return {
      compliant,
      level: WCAGLevel.AA,
      issues,
      recommendations,
    };
  }

  /**
   * Calculate color contrast ratio between foreground and background
   * @param foreground - Foreground color in hex format
   * @param background - Background color in hex format
   * @returns Contrast ratio result
   */
  calculateContrastRatio(foreground: string, background: string): ContrastRatio {
    const fgLuminance = this.getRelativeLuminance(foreground);
    const bgLuminance = this.getRelativeLuminance(background);

    const lighter = Math.max(fgLuminance, bgLuminance);
    const darker = Math.min(fgLuminance, bgLuminance);
    const ratio = (lighter + 0.05) / (darker + 0.05);

    return {
      ratio,
      passesAA: ratio >= 4.5, // WCAG AA requires 4.5:1 for normal text
      passesAAA: ratio >= 7.0, // WCAG AAA requires 7:1 for normal text
    };
  }

  /**
   * Apply high contrast mode to content
   * @param content - HTML content to modify
   * @returns Content with high contrast styles applied
   */
  applyHighContrastMode(content: string): string {
    // Apply high contrast color scheme
    const highContrastStyles = `
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
    `;

    return highContrastStyles + content.replace(/<body/g, '<body class="high-contrast"');
  }

  /**
   * Generate keyboard navigation configuration for an element
   * @param elementType - Type of element (button, link, input, etc.)
   * @param label - Accessible label for the element
   * @returns Keyboard navigation configuration
   */
  generateKeyboardNavConfig(
    elementType: string,
    label: string
  ): KeyboardNavigationConfig {
    const shortcuts = new Map<string, string>();

    // Define keyboard shortcuts based on element type
    switch (elementType) {
      case 'button':
        shortcuts.set('Enter', 'Activate button');
        shortcuts.set('Space', 'Activate button');
        break;
      case 'link':
        shortcuts.set('Enter', 'Follow link');
        break;
      case 'input':
        shortcuts.set('Tab', 'Move to next field');
        shortcuts.set('Shift+Tab', 'Move to previous field');
        break;
      case 'select':
        shortcuts.set('ArrowDown', 'Open dropdown');
        shortcuts.set('ArrowUp', 'Navigate options');
        shortcuts.set('Enter', 'Select option');
        break;
    }

    return {
      tabIndex: 0,
      ariaLabel: label,
      role: elementType === 'div' ? 'button' : undefined,
      keyboardShortcuts: shortcuts,
    };
  }

  /**
   * Enhance content for screen reader compatibility
   * @param content - HTML content to enhance
   * @returns Screen reader compatible content
   */
  enhanceForScreenReader(content: string): string {
    let enhanced = content;

    // Add ARIA landmarks
    enhanced = enhanced.replace(/<header/g, '<header role="banner"');
    enhanced = enhanced.replace(/<nav/g, '<nav role="navigation"');
    enhanced = enhanced.replace(/<main/g, '<main role="main"');
    enhanced = enhanced.replace(/<footer/g, '<footer role="contentinfo"');

    // Add skip navigation link
    const skipNav = '<a href="#main-content" class="skip-link">Skip to main content</a>';
    enhanced = enhanced.replace(/<body/g, `<body>\n${skipNav}`);

    // Ensure all images have alt text
    enhanced = enhanced.replace(/<img(?![^>]*alt=)/g, '<img alt=""');

    // Add aria-live regions for dynamic content
    enhanced = enhanced.replace(
      /<div class="notification"/g,
      '<div class="notification" role="alert" aria-live="polite"'
    );

    return enhanced;
  }

  // Private helper methods

  private hasImages(content: string): boolean {
    return /<img/i.test(content);
  }

  private hasAltText(content: string): boolean {
    const imgTags = content.match(/<img[^>]*>/gi) || [];
    return imgTags.every((tag) => /alt=/i.test(tag));
  }

  private hasProperHeadingStructure(content: string): boolean {
    const headings = content.match(/<h[1-6]/gi) || [];
    if (headings.length === 0) return true;

    // Check if headings are in proper order (no skipping levels)
    let lastLevel = 0;
    for (const heading of headings) {
      const level = parseInt(heading.charAt(2));
      if (level > lastLevel + 1) return false;
      lastLevel = level;
    }
    return true;
  }

  private checkColorContrast(content: string): AccessibilityIssue[] {
    const issues: AccessibilityIssue[] = [];
    
    // In a full implementation, this would parse CSS and check all color combinations
    // For now, we'll check for common patterns
    if (content.includes('color: #ccc') || content.includes('color: #ddd')) {
      issues.push({
        criterion: '1.4.3 Contrast (Minimum)',
        severity: 'warning',
        description: 'Light gray text may not meet contrast requirements',
      });
    }

    return issues;
  }

  private isKeyboardAccessible(content: string): boolean {
    // Check for interactive elements without tabindex or proper roles
    const interactiveElements = content.match(/<(button|a|input|select|textarea)/gi) || [];
    return interactiveElements.length > 0 || !/<div[^>]*onclick/i.test(content);
  }

  private hasFocusIndicators(content: string): boolean {
    // Check if CSS includes focus styles
    return /:focus/i.test(content) || /focus-visible/i.test(content);
  }

  private hasProperARIALabels(content: string): boolean {
    const interactiveElements = content.match(/<(button|a|input)[^>]*>/gi) || [];
    if (interactiveElements.length === 0) return true;

    // Check if most interactive elements have aria-label or aria-labelledby
    const withLabels = interactiveElements.filter(
      (el) => /aria-label/i.test(el) || /aria-labelledby/i.test(el) || />.*<\//i.test(el)
    );
    return withLabels.length >= interactiveElements.length * 0.8;
  }

  private getRelativeLuminance(hexColor: string): number {
    // Remove # if present
    const hex = hexColor.replace('#', '');
    
    // Convert to RGB
    const r = parseInt(hex.substr(0, 2), 16) / 255;
    const g = parseInt(hex.substr(2, 2), 16) / 255;
    const b = parseInt(hex.substr(4, 2), 16) / 255;

    // Apply gamma correction
    const rLinear = r <= 0.03928 ? r / 12.92 : Math.pow((r + 0.055) / 1.055, 2.4);
    const gLinear = g <= 0.03928 ? g / 12.92 : Math.pow((g + 0.055) / 1.055, 2.4);
    const bLinear = b <= 0.03928 ? b / 12.92 : Math.pow((b + 0.055) / 1.055, 2.4);

    // Calculate relative luminance
    return 0.2126 * rLinear + 0.7152 * gLinear + 0.0722 * bLinear;
  }
}
