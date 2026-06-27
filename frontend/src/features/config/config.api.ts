/** Endpoints de Configuración (Fase 7). */

import { request } from '../auth/api';
import type {
  Branding,
  BusinessParameters,
  ModuleConfig,
  UpdateBrandingInput,
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
