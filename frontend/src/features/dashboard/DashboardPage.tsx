/**
 * Dashboard ejecutivo (sección 7.16): réplica de `page-dashboard` con datos reales.
 * KPI cards, ticker de precios spot, alertas por reglas, stock por material y
 * transacciones recientes. Todo se calcula en el backend a partir de datos del tenant.
 */

import { useQuery } from '@tanstack/react-query';

import { useAuthStore } from '../auth/authStore';
import { grams, money } from '../operacion/format';
import { dashboardSummary } from './dashboard.api';
import type { Alert, MaterialStock, RecentTransaction, SpotPrice } from './dashboard.types';

const ALERT_ICON: Record<Alert['level'], string> = {
  critical: '⚠',
  warning: '⚠',
  info: 'ℹ',
};
const ALERT_CLASS: Record<Alert['level'], string> = {
  critical: 'warn',
  warning: 'warn',
  info: 'info',
};

export function DashboardPage() {
  const canRead = useAuthStore((s) => s.hasPermission('dashboard:access'));
  const summary = useQuery({ queryKey: ['dashboard', 'summary'], queryFn: dashboardSummary, enabled: canRead });

  if (!canRead) {
    return (
      <div className="page-placeholder">
        <div className="ph-icon">🔒</div>
        <h2>Sin acceso</h2>
        <p>No tienes el permiso <code>dashboard:access</code>.</p>
      </div>
    );
  }

  const d = summary.data;
  const k = d?.kpis;

  return (
    <div className="module-page">
      <Ticker prices={d?.spot_prices ?? []} />

      <div className="kpi-grid">
        <KpiCard label="Valor de inventario" value={money(k?.inventory_value_usd)} variant="gold" />
        <KpiCard label="Ventas acumuladas" value={money(k?.sales_total_usd)} variant="green" />
        <KpiCard label="Utilidad neta" value={money(k?.net_income_usd)} variant="blue" />
        <KpiCard label="Flujo de caja" value={money(k?.cash_balance_usd)} variant="" />
      </div>

      <div className="dashboard-grid">
        <div className="table-wrap">
          <div className="section-head">
            <h2 className="section-title">Transacciones recientes</h2>
          </div>
          <table className="table">
            <thead>
              <tr>
                <th>Tipo</th>
                <th>Documento</th>
                <th>Tercero</th>
                <th className="num">Monto</th>
              </tr>
            </thead>
            <tbody>
              {d?.recent_transactions.map((t) => (
                <TransactionRow key={`${t.kind}-${t.code}`} t={t} />
              ))}
              {d?.recent_transactions.length === 0 ? (
                <tr>
                  <td colSpan={4} className="empty-row">Sin movimientos todavía.</td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>

        <div className="panel-card">
          <div className="section-head">
            <h3 className="section-title">Alertas</h3>
          </div>
          <div className="alert-list">
            {d?.alerts.map((a, i) => (
              <div className={`alert-item ${ALERT_CLASS[a.level]}`} key={i}>
                <span className="alert-icon">{ALERT_ICON[a.level]}</span>
                <span className="alert-text">{a.message}</span>
              </div>
            ))}
            {d?.alerts.length === 0 ? (
              <div className="alert-item ok">
                <span className="alert-icon">✓</span>
                <span className="alert-text">Todo en orden. Sin alertas activas.</span>
              </div>
            ) : null}
          </div>
        </div>
      </div>

      <div className="section-head">
        <h2 className="section-title">Inventario por material</h2>
        <span className="section-subtitle">Stock mínimo: {grams(d?.min_stock_g)}</span>
      </div>
      <div className="material-grid">
        {d?.material_stock.map((m) => (
          <MaterialCard key={m.code} m={m} />
        ))}
      </div>
    </div>
  );
}

function Ticker({ prices }: { prices: SpotPrice[] }) {
  if (prices.length === 0) return null;
  return (
    <div className="ticker-strip">
      {prices.map((p) => {
        const up = Number(p.change_pct) >= 0;
        return (
          <div className="ticker-item" key={p.symbol}>
            <span className="ticker-symbol">{p.symbol}</span>
            <span className="ticker-price">{money(p.price_usd_per_oz)}/oz</span>
            <span className={`ticker-change ${up ? 'up' : 'down'}`}>
              {up ? '▲' : '▼'} {p.change_pct}%
            </span>
            {p.stale ? <span className="ticker-stale" title="Último precio conocido">⏱</span> : null}
          </div>
        );
      })}
    </div>
  );
}

function TransactionRow({ t }: { t: RecentTransaction }) {
  return (
    <tr>
      <td>
        <span className={`badge ${t.kind === 'sale' ? 'badge-green' : 'badge-blue'}`}>
          {t.kind === 'sale' ? 'Venta' : 'Compra'}
        </span>
      </td>
      <td className="primary">{t.code}</td>
      <td>{t.party_name}</td>
      <td className="num gold">{money(t.amount_usd)}</td>
    </tr>
  );
}

function MaterialCard({ m }: { m: MaterialStock }) {
  return (
    <div className={`material-card${m.is_critical ? ' critical' : ''}`}>
      <div className="material-head">
        <span className="material-symbol">{m.symbol}</span>
        <span className="material-name">{m.name}</span>
        {m.is_critical ? <span className="badge badge-red">Stock bajo</span> : null}
      </div>
      <div className="material-weight">{grams(m.available_weight_g)}</div>
      <div className="material-value">{money(m.value_usd)}</div>
      <div className="material-code">{m.code}</div>
    </div>
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
