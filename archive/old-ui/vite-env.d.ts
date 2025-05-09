/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string;
  readonly VITE_WS_URL: string;
  readonly VITE_AUTH_ENABLED: string;
  readonly VITE_AUTH_TOKEN_KEY: string;
  readonly VITE_ENABLE_COST_MANAGEMENT: string;
  readonly VITE_ENABLE_REAL_TIME_UPDATES: string;
  readonly VITE_APP_NAME: string;
  readonly VITE_DEFAULT_THEME: string;
  readonly VITE_LOG_LEVEL: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
} 