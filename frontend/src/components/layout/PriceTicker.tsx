/**
 * Ticker de precios spot (XAU/XAG/XPT/XPD) — réplica visual de `.ticker-strip`.
 *
 * En Fase 1 muestra valores estáticos de referencia. En Fase 7 se alimentará de
 * un adaptador real al proveedor de precios spot, con caché (secciones 7.16/3.8).
 */

interface TickerEntry {
  symbol: string;
  price: string;
  change: string;
  direction: 'up' | 'down';
}

const PLACEHOLDER_PRICES: TickerEntry[] = [
  { symbol: 'XAU', price: '$3,342.80', change: '+0.8%', direction: 'up' },
  { symbol: 'XAG', price: '$32.45', change: '+1.2%', direction: 'up' },
  { symbol: 'XPT', price: '$1,018.60', change: '-0.3%', direction: 'down' },
  { symbol: 'XPD', price: '$1,124.20', change: '+0.5%', direction: 'up' },
];

export function PriceTicker() {
  return (
    <div className="ticker-strip">
      {PLACEHOLDER_PRICES.map((t) => (
        <div className="ticker-item" key={t.symbol}>
          <span className="ticker-symbol">{t.symbol}</span>
          <span className="ticker-price">{t.price}</span>
          <span className={`ticker-change ${t.direction}`}>
            {t.direction === 'up' ? '▲' : '▼'} {t.change}
          </span>
        </div>
      ))}
    </div>
  );
}
