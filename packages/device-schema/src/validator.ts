import Ajv, { ErrorObject } from 'ajv';
import addFormats from 'ajv-formats';
import { deviceModelSchema } from './schema.js';
import type { DeviceModel } from './types.js';

/**
 * Validation error details
 */
export interface ValidationError {
  path: string;
  message: string;
  keyword: string;
  params: Record<string, unknown>;
}

/**
 * Result of device model validation
 */
export interface ValidationResult {
  valid: boolean;
  errors: ValidationError[];
  model?: DeviceModel;
}

/**
 * Validator for device model JSON documents
 */
export class DeviceModelValidator {
  private ajv: Ajv;
  private validate: ReturnType<Ajv['compile']>;

  constructor() {
    this.ajv = new Ajv({
      allErrors: true,
      verbose: true,
      strict: true,
    });
    addFormats(this.ajv);
    this.validate = this.ajv.compile(deviceModelSchema);
  }

  /**
   * Validate a device model object
   */
  validateModel(data: unknown): ValidationResult {
    const valid = this.validate(data);

    if (valid) {
      return {
        valid: true,
        errors: [],
        model: data as DeviceModel,
      };
    }

    const errors = this.formatErrors(this.validate.errors || []);
    return {
      valid: false,
      errors,
    };
  }

  /**
   * Validate a JSON string
   */
  validateJson(jsonString: string): ValidationResult {
    try {
      const data = JSON.parse(jsonString);
      return this.validateModel(data);
    } catch (error) {
      return {
        valid: false,
        errors: [
          {
            path: '',
            message: `Invalid JSON: ${(error as Error).message}`,
            keyword: 'parse',
            params: {},
          },
        ],
      };
    }
  }

  /**
   * Format AJV errors into a more readable format
   */
  private formatErrors(errors: ErrorObject[]): ValidationError[] {
    return errors.map((error) => ({
      path: error.instancePath || '/',
      message: error.message || 'Unknown validation error',
      keyword: error.keyword,
      params: error.params,
    }));
  }

  /**
   * Get human-readable error messages
   */
  static formatErrorMessages(errors: ValidationError[]): string[] {
    return errors.map((error) => {
      const path = error.path || 'root';
      return `${path}: ${error.message}`;
    });
  }
}
