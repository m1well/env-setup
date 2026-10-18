import { defineConfig } from '@playwright/test';

export default defineConfig({ testDir: './src', use: { baseURL: 'http://localhost:4200' } });
