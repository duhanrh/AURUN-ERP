/** Endpoints de Transformación y Calidad (Fase 5). */

import { request } from '../auth/api';
import type {
  CreateSampleInput,
  CreateTransformationInput,
  QualityKpis,
  QualitySample,
  TransformationKpis,
  TransformationOrder,
  UpdateSampleInput,
  UpdateTransformationInput,
} from './procesos.types';

// ── Transformación ──
export const listTransformations = (includeDeleted = false) =>
  request<TransformationOrder[]>(
    `/transformation/orders${includeDeleted ? '?include_deleted=true' : ''}`,
  );
export const transformationKpis = () => request<TransformationKpis>('/transformation/kpis');
export const createTransformation = (input: CreateTransformationInput) =>
  request<TransformationOrder>('/transformation/orders', { method: 'POST', body: input });
export const updateTransformation = (id: string, input: UpdateTransformationInput) =>
  request<TransformationOrder>(`/transformation/orders/${id}`, { method: 'PATCH', body: input });
export const advanceTransformation = (id: string) =>
  request<TransformationOrder>(`/transformation/orders/${id}/advance`, { method: 'POST' });
export const completeTransformation = (id: string) =>
  request<TransformationOrder>(`/transformation/orders/${id}/complete`, { method: 'POST' });
export const cancelTransformation = (id: string) =>
  request<TransformationOrder>(`/transformation/orders/${id}/cancel`, { method: 'POST' });
export const deleteTransformation = (id: string) =>
  request<TransformationOrder>(`/transformation/orders/${id}`, { method: 'DELETE' });
export const restoreTransformation = (id: string) =>
  request<TransformationOrder>(`/transformation/orders/${id}/restore`, { method: 'POST' });

// ── Calidad ──
export const listSamples = (includeDeleted = false) =>
  request<QualitySample[]>(`/quality/samples${includeDeleted ? '?include_deleted=true' : ''}`);
export const qualityKpis = () => request<QualityKpis>('/quality/kpis');
export const createSample = (input: CreateSampleInput) =>
  request<QualitySample>('/quality/samples', { method: 'POST', body: input });
export const updateSample = (id: string, input: UpdateSampleInput) =>
  request<QualitySample>(`/quality/samples/${id}`, { method: 'PATCH', body: input });
export const deleteSample = (id: string) =>
  request<QualitySample>(`/quality/samples/${id}`, { method: 'DELETE' });
export const restoreSample = (id: string) =>
  request<QualitySample>(`/quality/samples/${id}/restore`, { method: 'POST' });
