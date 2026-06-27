/**
 * Cliente HTTP del API de AURUM y endpoints de identidad.
 *
 * - Adjunta `Authorization: Bearer` desde el store en las peticiones autenticadas.
 * - Adjunta `X-Tenant-ID` en login/refresh (apoyo de desarrollo, sección 5.3).
 * - Ante un 401 en una petición autenticada intenta **una** rotación de refresh
 *   token y reintenta; si falla, limpia la sesión.
 */

import { API_BASE_URL, API_PREFIX } from '../../lib/config';
import { useAuthStore } from './authStore';
import type { CreateUserInput, Principal, Role, TokenPair, User } from './types';

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;

  constructor(status: number, code: string, message: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
  }
}

interface RequestOptions {
  method?: string;
  body?: unknown;
  auth?: boolean;
  tenantId?: string;
}

async function rawRequest(path: string, opts: RequestOptions): Promise<Response> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  const state = useAuthStore.getState();

  if (opts.auth !== false && state.accessToken) {
    headers.Authorization = `Bearer ${state.accessToken}`;
  }
  const tenantId = opts.tenantId ?? state.tenantId;
  if (tenantId) headers['X-Tenant-ID'] = tenantId;

  return fetch(`${API_BASE_URL}${API_PREFIX}${path}`, {
    method: opts.method ?? 'GET',
    headers,
    body: opts.body === undefined ? undefined : JSON.stringify(opts.body),
  });
}

async function parseError(response: Response): Promise<ApiError> {
  let code = 'error';
  let message = response.statusText;
  try {
    const data = await response.json();
    code = data.error ?? code;
    message = data.message ?? message;
  } catch {
    /* respuesta sin cuerpo JSON */
  }
  return new ApiError(response.status, code, message);
}

async function tryRefresh(): Promise<boolean> {
  const { refreshToken, tenantId, setTokens, clear } = useAuthStore.getState();
  if (!refreshToken) return false;
  const response = await rawRequest('/auth/refresh', {
    method: 'POST',
    auth: false,
    tenantId: tenantId ?? undefined,
    body: { refresh_token: refreshToken },
  });
  if (!response.ok) {
    clear();
    return false;
  }
  setTokens((await response.json()) as TokenPair);
  return true;
}

export async function request<T>(path: string, opts: RequestOptions = {}): Promise<T> {
  let response = await rawRequest(path, opts);

  if (response.status === 401 && opts.auth !== false) {
    if (await tryRefresh()) {
      response = await rawRequest(path, opts);
    }
  }
  if (!response.ok) throw await parseError(response);
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

// ── Endpoints ──
export async function login(tenantId: string, email: string, password: string): Promise<TokenPair> {
  return request<TokenPair>('/auth/login', {
    method: 'POST',
    auth: false,
    tenantId,
    body: { email, password },
  });
}

export async function fetchMe(): Promise<Principal> {
  return request<Principal>('/auth/me');
}

export async function logout(refreshToken: string): Promise<void> {
  await request<void>('/auth/logout', { method: 'POST', body: { refresh_token: refreshToken } });
}

export async function listUsers(): Promise<User[]> {
  return request<User[]>('/users');
}

export async function createUser(input: CreateUserInput): Promise<User> {
  return request<User>('/users', { method: 'POST', body: input });
}

export async function listRoles(): Promise<Role[]> {
  return request<Role[]>('/roles');
}
