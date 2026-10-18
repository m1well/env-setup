import { inject, InjectionToken } from '@angular/core';

const CONFIG_PATH = '/assets/config.json';

export const SETTINGS = new InjectionToken<string>('settings');

export async function loadConfig(): Promise<unknown> {
  const response = await fetch(CONFIG_PATH, { cache: 'no-store' });
  return response.json();
}

export function settings(): string {
  return inject(SETTINGS);
}
