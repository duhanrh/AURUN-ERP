/** Endpoint del Dashboard (Fase 7). */

import { request } from '../auth/api';
import type { DashboardSummary } from './dashboard.types';

export const dashboardSummary = () => request<DashboardSummary>('/dashboard/summary');
