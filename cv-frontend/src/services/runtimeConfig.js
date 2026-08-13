const configuredApiBaseUrl = (import.meta.env.VITE_API_BASE_URL || '').trim().replace(/\/$/, '');

function resolveApiBaseUrl() {
  if (configuredApiBaseUrl) return configuredApiBaseUrl;
  if (typeof window !== 'undefined') return window.location.origin;
  return 'http://127.0.0.1:8000';
}

export const resolvedApiBaseUrl = resolveApiBaseUrl();
export const relativeApiBaseUrl = configuredApiBaseUrl || '/';
export const resolvedWsBaseUrl = resolvedApiBaseUrl.replace(/^http/, 'ws').replace(/\/$/, '');
