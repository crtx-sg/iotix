/**
 * Device type enumeration
 */
export type DeviceType = 'sensor' | 'gateway' | 'actuator' | 'custom';

/**
 * Communication protocol enumeration
 */
export type Protocol = 'mqtt' | 'coap' | 'http';

/**
 * Data types for telemetry attributes
 */
export type DataType = 'number' | 'integer' | 'boolean' | 'string' | 'binary' | 'object' | 'array';

/**
 * Generator types for telemetry values
 */
export type GeneratorType = 'random' | 'sequence' | 'replay' | 'constant' | 'custom';

/**
 * Statistical distributions for random generator
 */
export type Distribution = 'uniform' | 'normal' | 'exponential';

/**
 * Trigger types for behaviors
 */
export type TriggerType = 'event' | 'schedule' | 'condition' | 'startup';

/**
 * Action types for behaviors
 */
export type ActionType = 'publish' | 'disconnect' | 'reconnect' | 'setState' | 'log' | 'custom';

/**
 * Connection settings for the device
 */
export interface Connection {
  broker?: string;
  port?: number;
  tls?: boolean;
  clientIdPattern?: string;
  topicPattern?: string;
  qos?: 0 | 1 | 2;
  keepAlive?: number;
  cleanSession?: boolean;
  username?: string;
  passwordRef?: string;
}

/**
 * Value generator configuration
 */
export interface Generator {
  type: GeneratorType;
  min?: number;
  max?: number;
  distribution?: Distribution;
  mean?: number;
  stddev?: number;
  rate?: number;
  start?: number;
  step?: number;
  wrap?: boolean;
  value?: unknown;
  dataFile?: string;
  loopReplay?: boolean;
  handler?: string;
  params?: Record<string, unknown>;
}

/**
 * Telemetry attribute definition
 */
export interface TelemetryAttribute {
  name: string;
  type: DataType;
  unit?: string;
  generator: Generator;
  intervalMs?: number;
  topic?: string;
}

/**
 * Command parameter definition
 */
export interface CommandParameter {
  name: string;
  type: 'number' | 'integer' | 'boolean' | 'string' | 'object';
  required?: boolean;
}

/**
 * Command response configuration
 */
export interface CommandResponse {
  topic?: string;
  template?: Record<string, unknown>;
}

/**
 * Command definition
 */
export interface Command {
  name: string;
  topic?: string;
  parameters?: CommandParameter[];
  handler?: string;
  response?: CommandResponse;
}

/**
 * Trigger definition for behaviors
 */
export interface Trigger {
  type: TriggerType;
  event?: string;
  schedule?: string;
  condition?: string;
}

/**
 * Action definition for behaviors
 */
export interface Action {
  type: ActionType;
  topic?: string;
  payload?: unknown;
  state?: Record<string, unknown>;
  duration?: number;
  message?: string;
  handler?: string;
  params?: Record<string, unknown>;
}

/**
 * Behavior definition
 */
export interface Behavior {
  name: string;
  trigger: Trigger;
  action: Action;
  enabled?: boolean;
}

/**
 * Complete device model definition
 */
export interface DeviceModel {
  id: string;
  name: string;
  description?: string;
  version?: string;
  type: DeviceType;
  protocol: Protocol;
  connection?: Connection;
  telemetry?: TelemetryAttribute[];
  commands?: Command[];
  behaviors?: Behavior[];
  metadata?: Record<string, unknown>;
}

/**
 * Device instance runtime state
 */
export interface DeviceInstanceState {
  id: string;
  modelId: string;
  status: 'created' | 'starting' | 'running' | 'stopping' | 'stopped' | 'error';
  connectionState: 'disconnected' | 'connecting' | 'connected' | 'reconnecting';
  createdAt: Date;
  startedAt?: Date;
  lastTelemetryAt?: Date;
  errorMessage?: string;
  customState?: Record<string, unknown>;
}
