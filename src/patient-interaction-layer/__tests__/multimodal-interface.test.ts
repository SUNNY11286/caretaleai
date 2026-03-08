/**
 * Unit Tests for Multimodal Interface Component
 * Tests text, voice, and image input processing, response formatting,
 * and accessibility features.
 */

import { MultimodalInterface, AudioBuffer, ImageBuffer } from '../multimodal-interface';
import { OutputFormat } from '../../shared/types';

describe('MultimodalInterface', () => {
  let multimodalInterface: MultimodalInterface;

  beforeEach(() => {
    multimodalInterface = new MultimodalInterface();
  });

  describe('processTextInput', () => {
    it('should process valid text input successfully', async () => {
      const text = 'What medications should I take today?';
      const patientId = 'patient-123';

      const response = await multimodalInterface.processTextInput(text, patientId);

      expect(response).toBeDefined();
      expect(response.responseId).toMatch(/^resp_/);
      expect(response.content).toContain(text);
      expect(response.content).toContain(patientId);
      expect(response.format).toBe(OutputFormat.TEXT);
      expect(response.timestamp).toBeInstanceOf(Date);
      expect(response.accessibilityFeatures).toContain('screen-reader-compatible');
      expect(response.accessibilityFeatures).toContain('keyboard-navigable');
    });

    it('should throw error for empty text input', async () => {
      const patientId = 'patient-123';

      await expect(multimodalInterface.processTextInput('', patientId)).rejects.toThrow(
        'Text input cannot be empty'
      );
    });

    it('should throw error for whitespace-only text input', async () => {
      const patientId = 'patient-123';

      await expect(multimodalInterface.processTextInput('   ', patientId)).rejects.toThrow(
        'Text input cannot be empty'
      );
    });

    it('should throw error for missing patient ID', async () => {
      const text = 'What medications should I take today?';

      await expect(multimodalInterface.processTextInput(text, '')).rejects.toThrow(
        'Patient ID is required'
      );
    });
  });

  describe('processVoiceInput', () => {
    it('should process valid voice input successfully', async () => {
      const audio: AudioBuffer = {
        data: new ArrayBuffer(1024),
        sampleRate: 44100,
        channels: 2,
        duration: 5.5,
      };
      const patientId = 'patient-456';

      const response = await multimodalInterface.processVoiceInput(audio, patientId);

      expect(response).toBeDefined();
      expect(response.responseId).toMatch(/^resp_/);
      expect(response.content).toContain('5.5s');
      expect(response.content).toContain('44100Hz');
      expect(response.content).toContain(patientId);
      expect(response.format).toBe(OutputFormat.AUDIO);
      expect(response.timestamp).toBeInstanceOf(Date);
      expect(response.accessibilityFeatures).toContain('audio-output');
      expect(response.accessibilityFeatures).toContain('transcript-available');
    });

    it('should throw error for empty audio buffer', async () => {
      const audio: AudioBuffer = {
        data: new ArrayBuffer(0),
        sampleRate: 44100,
        channels: 2,
        duration: 0,
      };
      const patientId = 'patient-456';

      await expect(multimodalInterface.processVoiceInput(audio, patientId)).rejects.toThrow(
        'Audio buffer cannot be empty'
      );
    });

    it('should throw error for missing patient ID', async () => {
      const audio: AudioBuffer = {
        data: new ArrayBuffer(1024),
        sampleRate: 44100,
        channels: 2,
        duration: 5.5,
      };

      await expect(multimodalInterface.processVoiceInput(audio, '')).rejects.toThrow(
        'Patient ID is required'
      );
    });
  });

  describe('processImageInput', () => {
    it('should process valid image input successfully', async () => {
      const image: ImageBuffer = {
        data: new ArrayBuffer(2048),
        width: 800,
        height: 600,
        format: 'jpeg',
      };
      const patientId = 'patient-789';

      const response = await multimodalInterface.processImageInput(image, patientId);

      expect(response).toBeDefined();
      expect(response.responseId).toMatch(/^resp_/);
      expect(response.content).toContain('800x600');
      expect(response.content).toContain('jpeg');
      expect(response.content).toContain(patientId);
      expect(response.format).toBe(OutputFormat.VISUAL);
      expect(response.timestamp).toBeInstanceOf(Date);
      expect(response.accessibilityFeatures).toContain('alt-text-provided');
      expect(response.accessibilityFeatures).toContain('high-contrast-available');
    });

    it('should throw error for empty image buffer', async () => {
      const image: ImageBuffer = {
        data: new ArrayBuffer(0),
        width: 0,
        height: 0,
        format: 'jpeg',
      };
      const patientId = 'patient-789';

      await expect(multimodalInterface.processImageInput(image, patientId)).rejects.toThrow(
        'Image buffer cannot be empty'
      );
    });

    it('should throw error for missing patient ID', async () => {
      const image: ImageBuffer = {
        data: new ArrayBuffer(2048),
        width: 800,
        height: 600,
        format: 'jpeg',
      };

      await expect(multimodalInterface.processImageInput(image, '')).rejects.toThrow(
        'Patient ID is required'
      );
    });

    it('should handle different image formats', async () => {
      const formats: Array<'jpeg' | 'png' | 'webp'> = ['jpeg', 'png', 'webp'];
      const patientId = 'patient-789';

      for (const format of formats) {
        const image: ImageBuffer = {
          data: new ArrayBuffer(2048),
          width: 800,
          height: 600,
          format,
        };

        const response = await multimodalInterface.processImageInput(image, patientId);
        expect(response.content).toContain(format);
      }
    });
  });

  describe('formatResponse', () => {
    it('should format response as text', async () => {
      const content = 'Take your medication at 8 AM';
      const format = OutputFormat.TEXT;

      const response = await multimodalInterface.formatResponse(content, format);

      expect(response).toBeDefined();
      expect(response.responseId).toMatch(/^resp_/);
      expect(response.content).toBe(content);
      expect(response.format).toBe(OutputFormat.TEXT);
      expect(response.timestamp).toBeInstanceOf(Date);
      expect(response.accessibilityFeatures).toContain('screen-reader-compatible');
      expect(response.accessibilityFeatures).toContain('keyboard-navigable');
      expect(response.accessibilityFeatures).toContain('resizable-text');
    });

    it('should format response as audio', async () => {
      const content = 'Take your medication at 8 AM';
      const format = OutputFormat.AUDIO;

      const response = await multimodalInterface.formatResponse(content, format);

      expect(response.format).toBe(OutputFormat.AUDIO);
      expect(response.accessibilityFeatures).toContain('audio-output');
      expect(response.accessibilityFeatures).toContain('transcript-available');
      expect(response.accessibilityFeatures).toContain('playback-controls');
    });

    it('should format response as visual', async () => {
      const content = 'Medication schedule diagram';
      const format = OutputFormat.VISUAL;

      const response = await multimodalInterface.formatResponse(content, format);

      expect(response.format).toBe(OutputFormat.VISUAL);
      expect(response.accessibilityFeatures).toContain('alt-text-provided');
      expect(response.accessibilityFeatures).toContain('high-contrast-available');
      expect(response.accessibilityFeatures).toContain('zoom-support');
    });

    it('should format response as mixed', async () => {
      const content = 'Comprehensive care instructions';
      const format = OutputFormat.MIXED;

      const response = await multimodalInterface.formatResponse(content, format);

      expect(response.format).toBe(OutputFormat.MIXED);
      expect(response.accessibilityFeatures).toContain('screen-reader-compatible');
      expect(response.accessibilityFeatures).toContain('audio-output');
      expect(response.accessibilityFeatures).toContain('alt-text-provided');
      expect(response.accessibilityFeatures).toContain('keyboard-navigable');
      expect(response.accessibilityFeatures).toContain('high-contrast-available');
    });

    it('should throw error for empty content', async () => {
      const format = OutputFormat.TEXT;

      await expect(multimodalInterface.formatResponse('', format)).rejects.toThrow(
        'Content cannot be empty'
      );
    });

    it('should throw error for whitespace-only content', async () => {
      const format = OutputFormat.TEXT;

      await expect(multimodalInterface.formatResponse('   ', format)).rejects.toThrow(
        'Content cannot be empty'
      );
    });
  });

  describe('getAccessibilityOptions', () => {
    it('should return accessibility settings for valid patient ID', () => {
      const patientId = 'patient-123';

      const settings = multimodalInterface.getAccessibilityOptions(patientId);

      expect(settings).toBeDefined();
      expect(settings).toHaveProperty('screenReaderEnabled');
      expect(settings).toHaveProperty('highContrastMode');
      expect(settings).toHaveProperty('fontSize');
      expect(settings).toHaveProperty('voiceOutputEnabled');
      expect(settings).toHaveProperty('keyboardNavigationOnly');
      expect(typeof settings.screenReaderEnabled).toBe('boolean');
      expect(typeof settings.highContrastMode).toBe('boolean');
      expect(['small', 'medium', 'large', 'extra-large']).toContain(settings.fontSize);
      expect(typeof settings.voiceOutputEnabled).toBe('boolean');
      expect(typeof settings.keyboardNavigationOnly).toBe('boolean');
    });

    it('should throw error for missing patient ID', () => {
      expect(() => multimodalInterface.getAccessibilityOptions('')).toThrow(
        'Patient ID is required'
      );
    });

    it('should return default settings', () => {
      const patientId = 'patient-123';

      const settings = multimodalInterface.getAccessibilityOptions(patientId);

      expect(settings.screenReaderEnabled).toBe(false);
      expect(settings.highContrastMode).toBe(false);
      expect(settings.fontSize).toBe('medium');
      expect(settings.voiceOutputEnabled).toBe(false);
      expect(settings.keyboardNavigationOnly).toBe(false);
    });
  });
});
