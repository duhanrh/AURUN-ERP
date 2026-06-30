/** Endpoints de Configuración (Fase 7). */

import { request } from '../auth/api';
import type {
  ApiKey,
  Branding,
  BusinessParameters,
  ConversionResult,
  CreatedApiKey,
  CreateUnitInput,
  ModuleConfig,
  UnitOfMeasure,
  UpdateBrandingInput,
  UpdateUnitInput,
} from './config.types';

export const getBranding = () => request<Branding>('/configuration/branding');
export const updateBranding = (input: UpdateBrandingInput) =>
  request<Branding>('/configuration/branding', { method: 'PUT', body: input });
export const resetBranding = () =>
  request<Branding>('/configuration/branding', { method: 'DELETE' });

export const getParameters = () => request<BusinessParameters>('/configuration/parameters');
export const updateParameters = (input: BusinessParameters) =>
  request<BusinessParameters>('/configuration/parameters', { method: 'PUT', body: input });

export const listModules = () => request<ModuleConfig[]>('/configuration/modules');
export const setModule = (key: string, isActive: boolean) =>
  request<ModuleConfig>(`/configuration/modules/${key}`, {
    method: 'PUT',
    body: { is_active: isActive },
  });

export const listUnits = (includeDeleted = false) =>
  request<UnitOfMeasure[]>(`/configuration/units?include_deleted=${includeDeleted}`);
export const createUnit = (input: CreateUnitInput) =>
  request<UnitOfMeasure>('/configuration/units', { method: 'POST', body: input });
export const updateUnit = (id: string, input: UpdateUnitInput) =>
  request<UnitOfMeasure>(`/configuration/units/${id}`, { method: 'PATCH', body: input });
export const deleteUnit = (id: string) =>
  request<UnitOfMeasure>(`/configuration/units/${id}`, { method: 'DELETE' });
export const restoreUnit = (id: string) =>
  request<UnitOfMeasure>(`/configuration/units/${id}/restore`, { method: 'POST' });
export const convertUnits = (quantity: string, fromUnit: string, toUnit: string) =>
  request<ConversionResult>('/configuration/units/convert', {
    method: 'POST',
    body: { quantity, from_unit: fromUnit, to_unit: toUnit },
  });

export const listApiKeys = () => request<ApiKey[]>('/configuration/api-keys');
export const availableScopes = () =>
  request<{ scopes: string[] }>('/configuration/api-keys/scopes');
export const createApiKey = (name: string, scopes: string[]) =>
  request<CreatedApiKey>('/configuration/api-keys', { method: 'POST', body: { name, scopes } });
export const revokeApiKey = (id: string) =>
  request<ApiKey>(`/configuration/api-keys/${id}`, { method: 'DELETE' });
