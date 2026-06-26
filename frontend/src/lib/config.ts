/** Configuración del cliente: URL base del API (sección 3.x). */

export const API_BASE_URL =
  (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, '') ??
  'http://localhost:8000';

/** Prefijo versionado del API de negocio (coincide con `AURUM_API_PREFIX`). */
export const API_PREFIX = '/api/v1';
