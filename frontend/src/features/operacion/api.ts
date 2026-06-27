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

// ── Inventario ──
export const listMaterials = () => request<Material[]>('/inventory/materials');
export const listLots = () => request<Lot[]>('/inventory/lots');
export const inventoryKpis = () => request<InventoryKpis>('/inventory/kpis');
export const createLot = (input: CreateLotInput) =>
  request<Lot>('/inventory/lots', { method: 'POST', body: input });

// ── Compras ──
export const listPurchaseOrders = () => request<PurchaseOrder[]>('/purchasing/orders');
export const purchasingKpis = () => request<PurchasingKpis>('/purchasing/kpis');
export const createPurchaseOrder = (input: CreatePurchaseOrderInput) =>
  request<PurchaseOrder>('/purchasing/orders', { method: 'POST', body: input });
export const approvePurchaseOrder = (id: string) =>
  request<PurchaseOrder>(`/purchasing/orders/${id}/approve`, { method: 'POST' });
export const rejectPurchaseOrder = (id: string) =>
  request<PurchaseOrder>(`/purchasing/orders/${id}/reject`, { method: 'POST' });

// ── Ventas ──
export const listSalesOrders = () => request<SalesOrder[]>('/sales/orders');
export const salesKpis = () => request<SalesKpis>('/sales/kpis');
export const createSalesOrder = (input: CreateSalesOrderInput) =>
  request<SalesOrder>('/sales/orders', { method: 'POST', body: input });
export const setSalesStatus = (id: string, status: SalesOrderStatus) =>
  request<SalesOrder>(`/sales/orders/${id}/status`, { method: 'PATCH', body: { status } });

// ── Terceros (para selects de los modales) ──
export const listSuppliers = () => request<Party[]>('/suppliers');
export const listCustomers = () => request<Party[]>('/customers');
