/**
 * AURA Client SDK - WebSocket Client with Conversation Acceleration
 */

export { AURAClient, ConversationSpeedometer } from './client';
export type { ClientConfig, ClientStats, MessageStats } from './client';

export {
  MetadataEntry,
  MetadataKind,
  classifyIntentFromMetadata,
  predictCompressionRatioFromMetadata,
  computeMetadataSignature,
} from './metadata';

export const VERSION = '1.0.0';
