/** Tipos del núcleo operativo (Inventario, Compras, Ventas), espejo del API. */

export type LotForm = 'raw' | 'refined';
export type LotStatus = 'available' | 'reserved' | 'in_process' | 'low_stock' | 'quarantine';
export type PurchaseOrderStatus = 'pending_approval' | 'approved' | 'rejected' | 'cancelled';
export type SalesOrderStatus = 'pending_payment' | 'preparing' | 'completed' | 'cancelled';

export interface Material {
  id: string;
  code: string;
  name: string;
  symbol: string;
  is_active: boolean;
}

export interface Lot {
  id: string;
  lot_code: string;
  material_id: string;
  material_code: string;
  material_name: string;
  form: LotForm;
  declared_purity: string;
  gross_weight_g: string;
  available_weight_g: string;
  net_weight_g: string;
  price_per_oz: string;
  value_usd: string;
  status: LotStatus;
  location: string | null;
  supplier_id: string | null;
  entry_date: string | null;
  created_at: string | null;
}

export interface InventoryKpis {
  total_lots: number;
  total_gross_weight_g: string;
  total_value_usd: string;
  raw_lots: number;
  refined_lots: number;
}

export interface PurchaseOrder {
  id: string;
  order_code: string;
  supplier_id: string;
  supplier_name: string;
  material_id: string;
  material_name: string;
  quantity_g: string;
  declared_purity: string;
  form: LotForm;
  price_per_oz: string;
  total_usd: string;
  location: string | null;
  expected_delivery: string | null;
  status: PurchaseOrderStatus;
  lot_id: string | null;
  created_at: string | null;
}

export interface PurchasingKpis {
  total_orders: number;
  pending_approval: number;
  approved: number;
  total_amount_usd: string;
}

export interface SalesOrder {
  id: string;
  order_code: string;
  customer_id: string;
  customer_name: string;
  lot_id: string;
  lot_code: string;
  material_name: string;
  declared_purity: string;
  quantity_g: string;
  price_per_oz: string;
  total_usd: string;
  status: SalesOrderStatus;
  invoice_number: string | null;
  created_at: string | null;
}

export interface SalesKpis {
  total_orders: number;
  pending_payment: number;
  completed: number;
  total_amount_usd: string;
}

export interface CreateLotInput {
  material_id: string;
  form: LotForm;
  declared_purity: string;
  gross_weight_g: string;
  price_per_oz: string;
  location?: string | null;
  supplier_id?: string | null;
  status?: LotStatus;
}

export interface CreatePurchaseOrderInput {
  supplier_id: string;
  material_id: string;
  quantity_g: string;
  declared_purity: string;
  price_per_oz: string;
  form: LotForm;
  location?: string | null;
  expected_delivery?: string | null;
}

export interface CreateSalesOrderInput {
  customer_id: string;
  lot_id: string;
  quantity_g: string;
  price_per_oz: string;
  invoice_number?: string | null;
}

export const LOT_STATUS_LABEL: Record<LotStatus, string> = {
  available: 'Disponible',
  reserved: 'Reservado',
  in_process: 'En proceso',
  low_stock: 'Stock mínimo',
  quarantine: 'En cuarentena',
};
export const LOT_STATUS_BADGE: Record<LotStatus, string> = {
  available: 'badge-green',
  reserved: 'badge-blue',
  in_process: 'badge-gold',
  low_stock: 'badge-red',
  quarantine: 'badge-gray',
};

export const PO_STATUS_LABEL: Record<PurchaseOrderStatus, string> = {
  pending_approval: 'Pendiente aprobación',
  approved: 'Aprobada',
  rejected: 'Rechazada',
  cancelled: 'Cancelada',
};
export const PO_STATUS_BADGE: Record<PurchaseOrderStatus, string> = {
  pending_approval: 'badge-red',
  approved: 'badge-green',
  rejected: 'badge-gray',
  cancelled: 'badge-gray',
};

export const SO_STATUS_LABEL: Record<SalesOrderStatus, string> = {
  pending_payment: 'Pago pendiente',
  preparing: 'En preparación',
  completed: 'Completada',
  cancelled: 'Cancelada',
};
export const SO_STATUS_BADGE: Record<SalesOrderStatus, string> = {
  pending_payment: 'badge-red',
  preparing: 'badge-blue',
  completed: 'badge-green',
  cancelled: 'badge-gray',
};
