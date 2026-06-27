/** Tipos de Contabilidad y Tesorería (Fase 6), espejo del API `/accounting`. */

export type AccountType = 'asset' | 'liability' | 'equity' | 'income' | 'expense';
export type NormalBalance = 'debit' | 'credit';
export type SourceType = 'purchase' | 'sale' | 'sale_reversal' | 'payment' | 'manual';

export interface Account {
  id: string;
  code: string;
  name: string;
  type: AccountType;
  normal_balance: NormalBalance;
}

export interface LedgerLine {
  account_code: string;
  account_name: string;
  account_type: AccountType;
  debit: string;
  credit: string;
  party_id: string | null;
  party_name: string | null;
}

export interface JournalEntry {
  id: string;
  entry_code: string;
  entry_date: string;
  memo: string;
  source_type: SourceType;
  source_id: string | null;
  total_debit: string;
  total_credit: string;
  lines: LedgerLine[];
  created_at: string | null;
}

export interface AccountingKpis {
  total_income: string;
  total_expense: string;
  net_income: string;
  cash_balance: string;
  receivable_total: string;
  payable_total: string;
  journal_entries: number;
}

export interface BalanceLine {
  code: string;
  name: string;
  amount: string;
}

export interface BalanceSheet {
  assets: BalanceLine[];
  liabilities: BalanceLine[];
  equity: BalanceLine[];
  total_assets: string;
  total_liabilities: string;
  total_equity: string;
  result_for_period: string;
  is_balanced: boolean;
}

export interface PartyBalance {
  party_id: string | null;
  party_name: string;
  balance: string;
}

export interface ManualLineInput {
  account_code: string;
  debit?: string;
  credit?: string;
  party_id?: string | null;
  party_name?: string | null;
}

export interface CreateManualEntryInput {
  memo: string;
  entry_date?: string | null;
  lines: ManualLineInput[];
}

export interface RegisterPaymentInput {
  direction: 'inbound' | 'outbound';
  party_id: string;
  party_name: string;
  amount: string;
  cash_account_code?: string;
  memo?: string | null;
}

export const SOURCE_LABEL: Record<SourceType, string> = {
  purchase: 'Compra',
  sale: 'Venta',
  sale_reversal: 'Reversa venta',
  payment: 'Pago',
  manual: 'Manual',
};
