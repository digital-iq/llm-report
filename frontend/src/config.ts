export interface RuntimeConfig {
  ORCHESTRATOR_URL: string;
}

export async function loadConfig(): Promise<RuntimeConfig> {
  const response = await fetch('/config/config.json', { cache: 'no-store' });
  if (!response.ok) {
    throw new Error('Failed to load runtime config');
  }
  return await response.json();
}
