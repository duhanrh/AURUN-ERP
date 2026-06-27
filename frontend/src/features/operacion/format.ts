/** Formateadores compartidos por las pantallas de operación. */

const USD = new Intl.NumberFormat('es-CO', {
  style: 'currency',
  currency: 'USD',
  maximumFractionDigits: 0,
});

/** Formatea un importe (string o number) como USD sin decimales. */
export function money(value: string | number | null | undefined): string {
  if (value === null || value === undefined) return '—';
  const n = typeof value === 'string' ? Number(value) : value;
  return Number.isFinite(n) ? USD.format(n) : '—';
}

/** Formatea un peso en gramos: usa kg cuando es grande, con separadores. */
export function grams(value: string | number | null | undefined): string {
  if (value === null || value === undefined) return '—';
  const n = typeof value === 'string' ? Number(value) : value;
  if (!Number.isFinite(n)) return '—';
  if (n >= 1000) return `${(n / 1000).toLocaleString('es-CO', { maximumFractionDigits: 2 })} kg`;
  return `${n.toLocaleString('es-CO', { maximumFractionDigits: 2 })} g`;
}

/** Convierte una pureza fracción (0–1) a porcentaje legible. */
export function purityPct(value: string | number | null | undefined): string {
  if (value === null || value === undefined) return '—';
  const n = typeof value === 'string' ? Number(value) : value;
  return Number.isFinite(n) ? `${(n * 100).toLocaleString('es-CO', { maximumFractionDigits: 2 })}%` : '—';
}
