import { describe, it, expect } from 'vitest';
import { DeviceModelValidator } from '../src/validator.js';

describe('DeviceModelValidator', () => {
  const validator = new DeviceModelValidator();

  describe('validateModel', () => {
    it('should validate a minimal valid device model', () => {
      const model = {
        id: 'test-sensor',
        name: 'Test Sensor',
        type: 'sensor',
        protocol: 'mqtt',
      };

      const result = validator.validateModel(model);
      expect(result.valid).toBe(true);
      expect(result.errors).toHaveLength(0);
      expect(result.model).toEqual(model);
    });

    it('should validate a complete device model', () => {
      const model = {
        id: 'temperature-sensor-v1',
        name: 'Temperature Sensor',
        description: 'A temperature sensor',
        version: '1.0.0',
        type: 'sensor',
        protocol: 'mqtt',
        connection: {
          broker: 'localhost',
          port: 1883,
          qos: 1,
        },
        telemetry: [
          {
            name: 'temperature',
            type: 'number',
            unit: 'celsius',
            generator: {
              type: 'random',
              min: 18,
              max: 28,
              distribution: 'uniform',
            },
            intervalMs: 5000,
          },
        ],
        commands: [
          {
            name: 'setInterval',
            parameters: [
              {
                name: 'interval',
                type: 'integer',
                required: true,
              },
            ],
          },
        ],
        behaviors: [
          {
            name: 'lowBattery',
            trigger: {
              type: 'condition',
              condition: 'battery < 20',
            },
            action: {
              type: 'publish',
              topic: 'alerts',
              payload: { alert: 'lowBattery' },
            },
          },
        ],
      };

      const result = validator.validateModel(model);
      expect(result.valid).toBe(true);
      expect(result.errors).toHaveLength(0);
    });

    it('should reject model with missing required fields', () => {
      const model = {
        id: 'test-sensor',
        // missing: name, type, protocol
      };

      const result = validator.validateModel(model);
      expect(result.valid).toBe(false);
      expect(result.errors.length).toBeGreaterThan(0);
      expect(result.errors.some((e) => e.message.includes('name'))).toBe(true);
    });

    it('should reject model with invalid device type', () => {
      const model = {
        id: 'test-sensor',
        name: 'Test Sensor',
        type: 'invalid-type',
        protocol: 'mqtt',
      };

      const result = validator.validateModel(model);
      expect(result.valid).toBe(false);
      expect(result.errors.some((e) => e.path.includes('type'))).toBe(true);
    });

    it('should reject model with invalid protocol', () => {
      const model = {
        id: 'test-sensor',
        name: 'Test Sensor',
        type: 'sensor',
        protocol: 'invalid-protocol',
      };

      const result = validator.validateModel(model);
      expect(result.valid).toBe(false);
      expect(result.errors.some((e) => e.path.includes('protocol'))).toBe(true);
    });

    it('should reject model with invalid id pattern', () => {
      const model = {
        id: '123-invalid', // must start with letter
        name: 'Test Sensor',
        type: 'sensor',
        protocol: 'mqtt',
      };

      const result = validator.validateModel(model);
      expect(result.valid).toBe(false);
      expect(result.errors.some((e) => e.path.includes('id'))).toBe(true);
    });

    it('should reject model with invalid port number', () => {
      const model = {
        id: 'test-sensor',
        name: 'Test Sensor',
        type: 'sensor',
        protocol: 'mqtt',
        connection: {
          port: 70000, // exceeds max 65535
        },
      };

      const result = validator.validateModel(model);
      expect(result.valid).toBe(false);
      expect(result.errors.some((e) => e.path.includes('port'))).toBe(true);
    });

    it('should reject telemetry with missing generator', () => {
      const model = {
        id: 'test-sensor',
        name: 'Test Sensor',
        type: 'sensor',
        protocol: 'mqtt',
        telemetry: [
          {
            name: 'temperature',
            type: 'number',
            // missing: generator
          },
        ],
      };

      const result = validator.validateModel(model);
      expect(result.valid).toBe(false);
    });

    it('should validate all generator types', () => {
      const generatorTypes = ['random', 'sequence', 'replay', 'constant', 'custom'];

      for (const generatorType of generatorTypes) {
        const model = {
          id: 'test-sensor',
          name: 'Test Sensor',
          type: 'sensor',
          protocol: 'mqtt',
          telemetry: [
            {
              name: 'value',
              type: 'number',
              generator: { type: generatorType },
            },
          ],
        };

        const result = validator.validateModel(model);
        expect(result.valid).toBe(true);
      }
    });

    it('should validate all device types', () => {
      const deviceTypes = ['sensor', 'gateway', 'actuator', 'custom'];

      for (const deviceType of deviceTypes) {
        const model = {
          id: 'test-device',
          name: 'Test Device',
          type: deviceType,
          protocol: 'mqtt',
        };

        const result = validator.validateModel(model);
        expect(result.valid).toBe(true);
      }
    });

    it('should validate all protocols', () => {
      const protocols = ['mqtt', 'coap', 'http'];

      for (const protocol of protocols) {
        const model = {
          id: 'test-device',
          name: 'Test Device',
          type: 'sensor',
          protocol: protocol,
        };

        const result = validator.validateModel(model);
        expect(result.valid).toBe(true);
      }
    });

    it('should reject additional properties', () => {
      const model = {
        id: 'test-sensor',
        name: 'Test Sensor',
        type: 'sensor',
        protocol: 'mqtt',
        unknownProperty: 'value',
      };

      const result = validator.validateModel(model);
      expect(result.valid).toBe(false);
    });
  });

  describe('validateJson', () => {
    it('should validate valid JSON string', () => {
      const json = JSON.stringify({
        id: 'test-sensor',
        name: 'Test Sensor',
        type: 'sensor',
        protocol: 'mqtt',
      });

      const result = validator.validateJson(json);
      expect(result.valid).toBe(true);
    });

    it('should reject invalid JSON syntax', () => {
      const json = '{ invalid json }';

      const result = validator.validateJson(json);
      expect(result.valid).toBe(false);
      expect(result.errors.some((e) => e.keyword === 'parse')).toBe(true);
    });
  });

  describe('formatErrorMessages', () => {
    it('should format error messages as readable strings', () => {
      const model = {
        id: '123-invalid',
        name: 'Test Sensor',
        type: 'invalid',
        protocol: 'mqtt',
      };

      const result = validator.validateModel(model);
      const messages = DeviceModelValidator.formatErrorMessages(result.errors);

      expect(messages.length).toBeGreaterThan(0);
      expect(messages.every((m) => typeof m === 'string')).toBe(true);
    });
  });
});
