/**
 * Select con búsqueda (combobox) reutilizable. Filtra opciones por texto, navega con
 * teclado (↑/↓/Enter/Esc) y, si se le pasa `onCreateNew`, ofrece una fila
 * "➕ Crear «texto»" cuando lo escrito no coincide con ninguna opción — para crear el
 * registro al vuelo desde el propio campo (cliente, proveedor, etc.).
 */

import { useEffect, useId, useMemo, useRef, useState } from 'react';

export interface SelectOption {
  value: string;
  label: string;
  /** Texto secundario atenuado (p. ej. NIT o material). */
  hint?: string;
}

interface SearchableSelectProps {
  options: SelectOption[];
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  disabled?: boolean;
  /** Texto cuando no hay coincidencias. */
  emptyText?: string;
  /** Si se define, muestra una fila para crear con el texto escrito. */
  onCreateNew?: (query: string) => void;
  createLabel?: (query: string) => string;
}

export function SearchableSelect({
  options,
  value,
  onChange,
  placeholder = 'Buscar…',
  disabled = false,
  emptyText = 'Sin coincidencias',
  onCreateNew,
  createLabel = (q) => `Crear «${q}»`,
}: SearchableSelectProps) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [highlight, setHighlight] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const listId = useId();

  const selected = options.find((o) => o.value === value) ?? null;

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return options;
    return options.filter(
      (o) => o.label.toLowerCase().includes(q) || (o.hint ?? '').toLowerCase().includes(q),
    );
  }, [options, query]);

  const exactMatch = filtered.some((o) => o.label.toLowerCase() === query.trim().toLowerCase());
  const showCreate = Boolean(onCreateNew) && query.trim().length > 0 && !exactMatch;
  // Número total de filas navegables (opciones + posible fila "crear").
  const rowCount = filtered.length + (showCreate ? 1 : 0);

  useEffect(() => {
    if (!open) return;
    function onDocMouseDown(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener('mousedown', onDocMouseDown);
    return () => document.removeEventListener('mousedown', onDocMouseDown);
  }, [open]);

  function openMenu() {
    if (disabled) return;
    setQuery('');
    setHighlight(0);
    setOpen(true);
  }

  function choose(option: SelectOption) {
    onChange(option.value);
    setOpen(false);
  }

  function commitHighlight() {
    if (showCreate && highlight === filtered.length) {
      onCreateNew?.(query.trim());
      setOpen(false);
      return;
    }
    const option = filtered[highlight];
    if (option) choose(option);
  }

  function onKeyDown(e: React.KeyboardEvent) {
    if (!open && (e.key === 'ArrowDown' || e.key === 'Enter')) {
      openMenu();
      return;
    }
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setHighlight((h) => Math.min(h + 1, Math.max(rowCount - 1, 0)));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setHighlight((h) => Math.max(h - 1, 0));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      commitHighlight();
    } else if (e.key === 'Escape') {
      setOpen(false);
    }
  }

  return (
    <div className="ss" ref={containerRef}>
      <input
        ref={inputRef}
        className="ss-input"
        type="text"
        role="combobox"
        aria-expanded={open}
        aria-controls={listId}
        autoComplete="off"
        disabled={disabled}
        placeholder={selected ? selected.label : placeholder}
        value={open ? query : (selected?.label ?? '')}
        onFocus={openMenu}
        onClick={openMenu}
        onChange={(e) => {
          setQuery(e.target.value);
          setHighlight(0);
          if (!open) setOpen(true);
        }}
        onKeyDown={onKeyDown}
      />
      <span className="ss-caret" aria-hidden>
        ▾
      </span>

      {open ? (
        <ul className="ss-menu" id={listId} role="listbox">
          {filtered.map((o, i) => (
            <li
              key={o.value}
              role="option"
              aria-selected={o.value === value}
              className={`ss-option${i === highlight ? ' active' : ''}${
                o.value === value ? ' selected' : ''
              }`}
              onMouseDown={(e) => e.preventDefault()}
              onMouseEnter={() => setHighlight(i)}
              onClick={() => choose(o)}
            >
              <span className="ss-option-label">{o.label}</span>
              {o.hint ? <span className="ss-option-hint">{o.hint}</span> : null}
            </li>
          ))}

          {filtered.length === 0 && !showCreate ? (
            <li className="ss-empty">{emptyText}</li>
          ) : null}

          {showCreate ? (
            <li
              role="option"
              aria-selected={false}
              className={`ss-option ss-create${highlight === filtered.length ? ' active' : ''}`}
              onMouseDown={(e) => e.preventDefault()}
              onMouseEnter={() => setHighlight(filtered.length)}
              onClick={() => {
                onCreateNew?.(query.trim());
                setOpen(false);
              }}
            >
              <span className="ss-create-plus" aria-hidden>
                ＋
              </span>
              {createLabel(query.trim())}
            </li>
          ) : null}
        </ul>
      ) : null}
    </div>
  );
}
