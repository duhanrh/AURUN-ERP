/** Endpoints de Contabilidad y Tesorería (Fase 6). */

import { request } from '../auth/api';
import type {
  Account,
  AccountingKpis,
  BalanceSheet,
  CreateManualEntryInput,
  JournalEntry,
  PartyBalance,
  RegisterPaymentInput,
} from './finanzas.types';

export const listAccounts = () => request<Account[]>('/accounting/accounts');
export const accountingKpis = () => request<AccountingKpis>('/accounting/kpis');
export const listJournal = () => request<JournalEntry[]>('/accounting/journal');
export const balanceSheet = () => request<BalanceSheet>('/accounting/balance-sheet');
export const listReceivables = () => request<PartyBalance[]>('/accounting/receivables');
export const listPayables = () => request<PartyBalance[]>('/accounting/payables');

export const createManualEntry = (input: CreateManualEntryInput) =>
  request<JournalEntry>('/accounting/journal', { method: 'POST', body: input });

export const registerPayment = (input: RegisterPaymentInput) =>
  request<JournalEntry>('/accounting/payments', { method: 'POST', body: input });
