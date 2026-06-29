/** Endpoints del núcleo operativo (Inventario, Compras, Ventas). */

import { request } from '../auth/api';
import type { Party } from '../terceros/types';
import type {
  CreateLotInput,
  CreatePurchaseOrderInput,
  CreateSalesOrderInput,
  InventoryKpis,
  Lot,
  Material,
  PurchaseOrder,
  PurchasingKpis,
  SalesKpis,
  SalesOrder,
  SalesOrderStatus,
} from './types';

const withDeleted = (path: string, includeDeleted: boolean) =>
  includeDeleted ? `${path}?include_deleted=true` : path;

// ── Inventario ──
export const listMaterials = () => request<Material[]>('/inventory/materials');
export const listLots = (includeDeleted = false) =>
  request<Lot[]>(withDeleted('/inventory/lots', includeDeleted));
export const inventoryKpis = () => request<InventoryKpis>('/inventory/kpis');
export const createLot = (input: CreateLotInput) =>
  request<Lot>('/inventory/lots', { method: 'POST', body: input });
export const updateLot = (id: string, input: { location?: string | null; status?: string }) =>
  request<Lot>(`/inventory/lots/${id}`, { method: 'PATCH', body: input });
export const deleteLot = (id: string) =>
  request<Lot>(`/inventory/lots/${id}`, { method: 'DELETE' });
export const restoreLot = (id: string) =>
  request<Lot>(`/inventory/lots/${id}/restore`, { method: 'POST' });

// ── Compras ──
export const listPurchaseOrders = (includeDeleted = false) =>
  request<PurchaseOrder[]>(withDeleted('/purchasing/orders', includeDeleted));
export const purchasingKpis = () => request<PurchasingKpis>('/purchasing/kpis');
export const createPurchaseOrder = (input: CreatePurchaseOrderInput) =>
  request<PurchaseOrder>('/purchasing/orders', { method: 'POST', body: input });
export const approvePurchaseOrder = (id: string) =>
  request<PurchaseOrder>(`/purchasing/orders/${id}/approve`, { method: 'POST' });
export const rejectPurchaseOrder = (id: string) =>
  request<PurchaseOrder>(`/purchasing/orders/${id}/reject`, { method: 'POST' });
export const deletePurchaseOrder = (id: string) =>
  request<PurchaseOrder>(`/purchasing/orders/${id}`, { method: 'DELETE' });
export const restorePurchaseOrder = (id: string) =>
  request<PurchaseOrder>(`/purchasing/orders/${id}/restore`, { method: 'POST' });

// ── Ventas ──
export const listSalesOrders = (includeDeleted = false) =>
  request<SalesOrder[]>(withDeleted('/sales/orders', includeDeleted));
export const salesKpis = () => request<SalesKpis>('/sales/kpis');
export const createSalesOrder = (input: CreateSalesOrderInput) =>
  request<SalesOrder>('/sales/orders', { method: 'POST', body: input });
export const setSalesStatus = (id: string, status: SalesOrderStatus) =>
  request<SalesOrder>(`/sales/orders/${id}/status`, { method: 'PATCH', body: { status } });
export const deleteSalesOrder = (id: string) =>
  request<SalesOrder>(`/sales/orders/${id}`, { method: 'DELETE' });
export const restoreSalesOrder = (id: string) =>
  request<SalesOrder>(`/sales/orders/${id}/restore`, { method: 'POST' });

// ── Terceros (para selects de los modales) ──
export const listSuppliers = () => request<Party[]>('/suppliers');
export const listCustomers = () => request<Party[]>('/customers');
