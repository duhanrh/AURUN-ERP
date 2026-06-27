/** Tipos del Dashboard (Fase 7), espejo del API `/dashboard/summary`. */

export interface DashboardKpis {
  inventory_value_usd: string;
  inventory_weight_g: string;
  total_lots: number;
  sales_total_usd: string;
  sales_count: number;
  purchases_pending: number;
  net_income_usd: string;
  cash_balance_usd: string;
  receivable_usd: string;
  payable_usd: string;
}

export interface Alert {
  level: 'critical' | 'warning' | 'info';
  category: string;
  message: string;
}

export interface MaterialStock {
  code: string;
  name: string;
  symbol: string;
  available_weight_g: string;
  value_usd: string;
  is_critical: boolean;
}

export interface RecentTransaction {
  kind: 'sale' | 'purchase';
  code: string;
  party_name: string;
  amount_usd: string;
  status: string;
  created_at: string | null;
}

export interface SpotPrice {
  symbol: string;
  name: string;
  price_usd_per_oz: string;
  change_pct: string;
  stale: boolean;
}

export interface DashboardSummary {
  kpis: DashboardKpis;
  alerts: Alert[];
  material_stock: MaterialStock[];
  recent_transactions: RecentTransaction[];
  spot_prices: SpotPrice[];
  min_stock_g: string;
}
