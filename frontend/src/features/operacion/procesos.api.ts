/** Endpoints de Transformación y Calidad (Fase 5). */

import { request } from '../auth/api';
import type {
  CreateSampleInput,
  CreateTransformationInput,
  QualityKpis,
  QualitySample,
  TransformationKpis,
  TransformationOrder,
} from './procesos.types';

// ── Transformación ──
export const listTransformations = () => request<TransformationOrder[]>('/transformation/orders');
export const transformationKpis = () => request<TransformationKpis>('/transformation/kpis');
export const createTransformation = (input: CreateTransformationInput) =>
  request<TransformationOrder>('/transformation/orders', { method: 'POST', body: input });
export const advanceTransformation = (id: string) =>
  request<TransformationOrder>(`/transformation/orders/${id}/advance`, { method: 'POST' });
export const completeTransformation = (id: string) =>
  request<TransformationOrder>(`/transformation/orders/${id}/complete`, { method: 'POST' });
export const cancelTransformation = (id: string) =>
  request<TransformationOrder>(`/transformation/orders/${id}/cancel`, { method: 'POST' });

// ── Calidad ──
export const listSamples = () => request<QualitySample[]>('/quality/samples');
export const qualityKpis = () => request<QualityKpis>('/quality/kpis');
export const createSample = (input: CreateSampleInput) =>
  request<QualitySample>('/quality/samples', { method: 'POST', body: input });
