// frontend/src/components/dsl/singleton.ts
// DSL Singleton - Lazy loading and centralized access pattern

import { DslEngine } from './dsl.engine';

let instance: DslEngine | null = null;

/**
 * Get DSL Engine singleton instance
 * Auto-initializes on first access
 */
export function getDslEngine(): DslEngine {
  if (!instance) {
    instance = new DslEngine();
  }
  return instance;
}

/**
 * Initialize DSL Engine eagerly (optional)
 * Can be called during app startup for better performance
 */
export async function initializeDslEngine(): Promise<DslEngine> {
  const engine = getDslEngine();
  await engine.initialize();
  return engine;
}

/**
 * Reset DSL Engine (mainly for testing)
 */
export function resetDslEngine(): void {
  instance = null;
}

/**
 * Check if DSL Engine is created and initialized
 */
export function isDslEngineReady(): boolean {
  return instance !== null && instance.isInitialized();
}
