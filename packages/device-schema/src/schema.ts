import { readFileSync } from 'fs';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const schemaPath = join(__dirname, '..', 'schemas', 'device-model.schema.json');

/**
 * Load the device model JSON schema
 */
export const deviceModelSchema = JSON.parse(readFileSync(schemaPath, 'utf-8'));
