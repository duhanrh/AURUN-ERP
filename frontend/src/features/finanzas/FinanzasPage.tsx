/**
 * Contabilidad y Tesorería (sección 7.12/7.13): página `page-finanzas` con sus 3
 * tabs (CxC/CxP, Libro Mayor, Balance General) + KPIs reales. Los asientos se
 * generan automáticamente desde compras/ventas; aquí se consultan y se registran
 * asientos manuales y pagos.
 */

import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { useAuthStore } from '../auth/authStore';
import { money } from '../operacion/format';
import {
  accountingKpis,
  balanceSheet,
  createManualEntry,
  listAccounts,
  listJournal,
  listPayables,
  listReceivables,
  registerPayment,
} from './finanzas.api';
import type {
  BalanceLine,
  CreateManualEntryInput,
  PartyBalance,
  RegisterPaymentInput,
} from './finanzas.types';
import { SOURCE_LABEL } from './finanzas.types';
import { JournalEntryModal } from './JournalEntryModal';
import { PaymentModal } from './PaymentModal';

type Tab = 'cartera' | 'mayor' | 'balance';

export function FinanzasPage() {
  const queryClient = useQueryClient();
  const canRead = useAuthStore((s) => s.hasPermission('accounting:access'));
  const canPostManual = useAuthStore((s) => s.hasPermission('accounting:manual_entry'));
  const canPay = useAuthStore((s) => s.hasPermission('treasury:manage'));
  const [tab, setTab] = useState<Tab>('cartera');
  const [entryModal, setEntryModal] = useState(false);
  const [payDirection, setPayDirection] = useState<'inbound' | 'outbound' | null>(null);

  const kpis = useQuery({ queryKey: ['accounting', 'kpis'], queryFn: accountingKpis, enabled: canRead });
  const journal = useQuery({ queryKey: ['accounting', 'journal'], queryFn: listJournal, enabled: canRead });
  const balance = useQuery({ queryKey: ['accounting', 'balance'], queryFn: balanceSheet, enabled: canRead });
  const receivables = useQuery({ queryKey: ['accounting', 'receivables'], queryFn: listReceivables, enabled: canRead });
  const payables = useQuery({ queryKey: ['accounting', 'payables'], queryFn: listPayables, enabled: canRead });
  const accounts = useQuery({ queryKey: ['accounting', 'accounts'], queryFn: listAccounts, enabled: canPostManual });

  const invalidate = async () => {
    await queryClient.invalidateQueries({ queryKey: ['accounting'] });
  };

  const entryMutation = useMutation({
    mutationFn: (input: CreateManualEntryInput) => createManualEntry(input),
    onSuccess: async () => {
      await invalidate();
      setEntryModal(false);
    },
  });
  const paymentMutation = useMutation({
    mutationFn: (input: RegisterPaymentInput) => registerPayment(input),
    onSuccess: async () => {
      await invalidate();
      setPayDirection(null);
    },
  });

  if (!canRead) {
    return (
      <div className="page-placeholder">
        <div className="ph-icon">🔒</div>
        <h2>Sin acceso</h2>
        <p>No tienes el permiso <code>accounting:access</code>.</p>
      </div>
    );
  }

  const k = kpis.data;

  return (
    <div className="module-page">
      <div className="kpi-grid">
        <KpiCard label="Ingresos acumulados" value={money(k?.total_income)} variant="gold" />
        <KpiCard label="Costos acumulados" value={money(k?.total_expense)} variant="red" />
        <KpiCard label="Utilidad neta" value={money(k?.net_income)} variant="green" />
        <KpiCard label="Flujo de caja" value={money(k?.cash_balance)} variant="blue" />
      </div>

      <div className="tab-bar">
        <button className={`tab ${tab === 'cartera' ? 'active' : ''}`} onClick={() => setTab('cartera')}>
          Cuentas por Cobrar / Pagar
        </button>
        <button className={`tab ${tab === 'mayor' ? 'active' : ''}`} onClick={() => setTab('mayor')}>
          Libro Mayor
        </button>
        <button className={`tab ${tab === 'balance' ? 'active' : ''}`} onClick={() => setTab('balance')}>
          Balance General
        </button>
      </div>

      {tab === 'cartera' ? (
        <div className="cartera-grid">
          <CarteraPanel
            title="Cuentas por Cobrar"
            rows={receivables.data ?? []}
            actionLabel="Registrar cobro"
            canAct={canPay}
            onAct={() => setPayDirection('inbound')}
          />
          <CarteraPanel
            title="Cuentas por Pagar"
            rows={payables.data ?? []}
            actionLabel="Registrar pago"
            canAct={canPay}
            onAct={() => setPayDirection('outbound')}
          />
        </div>
      ) : null}

      {tab === 'mayor' ? (
        <div className="table-wrap">
          <div className="section-head">
            <h2 className="section-title">Asientos contables recientes</h2>
            {canPostManual ? (
              <button className="btn btn-primary" onClick={() => setEntryModal(true)}>
                + Nuevo Asiento
              </button>
            ) : null}
          </div>
          <div className="ledger-entry head">
            <span>Fecha</span>
            <span>Cuenta / Detalle</span>
            <span className="num">Débito</span>
            <span className="num">Crédito</span>
          </div>
          {journal.data?.flatMap((entry) =>
            entry.lines.map((line, i) => (
              <div className="ledger-entry" key={`${entry.id}-${i}`}>
                <span className="ledger-date">{entry.entry_date}</span>
                <span className="ledger-desc">
                  <div className="ledger-account">{line.account_name}</div>
                  <div className="ledger-sub">
                    {SOURCE_LABEL[entry.source_type]} · {entry.memo}
                  </div>
                </span>
                <span className="ledger-debit">
                  {Number(line.debit) > 0 ? money(line.debit) : '—'}
                </span>
                <span className="ledger-credit">
                  {Number(line.credit) > 0 ? money(line.credit) : '—'}
                </span>
              </div>
            )),
          )}
          {journal.data?.length === 0 ? (
            <div className="empty-row" style={{ padding: '18px' }}>
              Aún no hay asientos. Se generan al aprobar compras y registrar ventas.
            </div>
          ) : null}
        </div>
      ) : null}

      {tab === 'balance' ? (
        <BalanceTab data={balance.data} />
      ) : null}

      {entryModal ? (
        <JournalEntryModal
          accounts={accounts.data ?? []}
          submitting={entryMutation.isPending}
          onSubmit={async (input) => {
            await entryMutation.mutateAsync(input);
          }}
          onClose={() => setEntryModal(false)}
        />
      ) : null}

      {payDirection ? (
        <PaymentModal
          direction={payDirection}
          parties={(payDirection === 'inbound' ? receivables.data : payables.data) ?? []}
          submitting={paymentMutation.isPending}
          onSubmit={async (input) => {
            await paymentMutation.mutateAsync(input);
          }}
          onClose={() => setPayDirection(null)}
        />
      ) : null}
    </div>
  );
}

function CarteraPanel({
  title,
  rows,
  actionLabel,
  canAct,
  onAct,
}: {
  title: string;
  rows: PartyBalance[];
  actionLabel: string;
  canAct: boolean;
  onAct: () => void;
}) {
  return (
    <div className="cartera-panel">
      <div className="section-head">
        <h3 className="section-title">{title}</h3>
        {canAct ? (
          <button className="btn btn-sm btn-primary" onClick={onAct} disabled={!rows.length}>
            {actionLabel}
          </button>
        ) : null}
      </div>
      <table className="table">
        <thead>
          <tr>
            <th>Tercero</th>
            <th className="num">Saldo</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.party_id ?? r.party_name}>
              <td className="primary">{r.party_name}</td>
              <td className="num gold">{money(r.balance)}</td>
            </tr>
          ))}
          {rows.length === 0 ? (
            <tr>
              <td colSpan={2} className="empty-row">
                Sin saldos pendientes.
              </td>
            </tr>
          ) : null}
        </tbody>
      </table>
    </div>
  );
}

function BalanceTab({ data }: { data: import('./finanzas.types').BalanceSheet | undefined }) {
  if (!data) return <div className="table-wrap" style={{ padding: '18px' }}>Cargando…</div>;
  return (
    <div className="table-wrap balance-wrap">
      <div className="section-head">
        <h2 className="section-title">Balance General</h2>
        <span className={`badge ${data.is_balanced ? 'badge-green' : 'badge-red'}`}>
          {data.is_balanced ? 'Cuadrado' : 'Descuadrado'}
        </span>
      </div>
      <div className="balance-grid">
        <div>
          <BalanceSection title="Activos" lines={data.assets} total={data.total_assets} />
          <BalanceSection title="Pasivos" lines={data.liabilities} total={data.total_liabilities} />
        </div>
        <div>
          <BalanceSection
            title="Patrimonio"
            lines={data.equity}
            total={data.total_equity}
            totalVariant="green"
          />
        </div>
      </div>
    </div>
  );
}

function BalanceSection({
  title,
  lines,
  total,
  totalVariant,
}: {
  title: string;
  lines: BalanceLine[];
  total: string;
  totalVariant?: string;
}) {
  return (
    <>
      <div className="balance-section-title">{title}</div>
      {lines.map((line) => (
        <div className="balance-row" key={line.code}>
          <span className="label">{line.name}</span>
          <span className="val">{money(line.amount)}</span>
        </div>
      ))}
      <div className="balance-row total">
        <span className="label">Total {title}</span>
        <span className={`val ${totalVariant ?? 'gold'}`}>{money(total)}</span>
      </div>
    </>
  );
}

function KpiCard({ label, value, variant }: { label: string; value: string | number; variant: string }) {
  return (
    <div className={`kpi-card ${variant}`}>
      <span className="kpi-value">{value}</span>
      <span className="kpi-label">{label}</span>
    </div>
  );
}
