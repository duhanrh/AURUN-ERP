/** Modal "Nueva Orden de Transformación" (modal-transformacion, sección 7.4). */

import { useMemo, useState, type FormEvent } from 'react';

import { SearchableSelect, type SelectOption } from '../../components/SearchableSelect';
import { ApiError } from '../auth/api';
import { grams } from './format';
import type { CreateTransformationInput, Process } from './procesos.types';
import { PROCESS_LABEL } from './procesos.types';
import type { Lot, Material } from './types';

interface Props {
  lots: Lot[];
  materials: Material[];
  submitting: boolean;
  onSubmit: (input: CreateTransformationInput) => Promise<void>;
  onClose: () => void;
}

export function TransformationFormModal({ lots, materials, submitting, onSubmit, onClose }: Props) {
  const usable = useMemo(() => lots.filter((l) => Number(l.available_weight_g) > 0), [lots]);
  const [inputLotId, setInputLotId] = useState(usable[0]?.id ?? '');
  const [process, setProcess] = useState<Process>('acid_refining');
  const [quantity, setQuantity] = useState('');
  const [yieldPct, setYieldPct] = useState('95');
  const [outputMaterialId, setOutputMaterialId] = useState(materials[0]?.id ?? '');
  const [outputPurityPct, setOutputPurityPct] = useState('99.99');
  const [responsible, setResponsible] = useState('');
  const [error, setError] = useState<string | null>(null);

  const selectedLot = usable.find((l) => l.id === inputLotId) ?? null;

  const lotOptions: SelectOption[] = usable.map((l) => ({
    value: l.id,
    label: `${l.lot_code} · ${l.material_name}`,
    hint: grams(l.available_weight_g),
  }));
  const materialOptions: SelectOption[] = materials.map((m) => ({
    value: m.id,
    label: m.name,
    hint: m.code,
  }));

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    if (!inputLotId) return setError('Selecciona un lote de entrada.');
    if (!outputMaterialId) return setError('Selecciona el material de salida.');
    try {
      await onSubmit({
        input_lot_id: inputLotId,
        process,
        input_quantity_g: quantity,
        yield_fraction: String(Number(yieldPct) / 100),
        output_material_id: outputMaterialId,
        output_purity: String(Number(outputPurityPct) / 100),
        output_form: 'refined',
        responsible: responsible.trim() || null,
      });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'No se pudo crear la orden.');
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <form className="modal" onClick={(e) => e.stopPropagation()} onSubmit={handleSubmit}>
        <div className="modal-header">
          <h3>Nueva Orden de Transformación</h3>
          <button type="button" className="modal-close" onClick={onClose} aria-label="Cerrar">
            ✕
          </button>
        </div>
        <div className="modal-body">
          <label className="field">
            <span>Lote de entrada</span>
            <SearchableSelect
              options={lotOptions}
              value={inputLotId}
              onChange={setInputLotId}
              placeholder="Buscar lote con stock…"
              emptyText="Sin lotes con stock"
            />
          </label>
          <div className="field-row">
            <label className="field">
              <span>Proceso</span>
              <select value={process} onChange={(e) => setProcess(e.target.value as Process)}>
                {(Object.keys(PROCESS_LABEL) as Process[]).map((p) => (
                  <option key={p} value={p}>
                    {PROCESS_LABEL[p]}
                  </option>
                ))}
              </select>
            </label>
            <label className="field">
              <span>Cantidad a procesar (g)</span>
              <input
                type="number"
                min={0}
                step={0.0001}
                max={selectedLot ? Number(selectedLot.available_weight_g) : undefined}
                value={quantity}
                onChange={(e) => setQuantity(e.target.value)}
                required
              />
            </label>
          </div>
          <div className="field-row">
            <label className="field">
              <span>Material de salida</span>
              <SearchableSelect
                options={materialOptions}
                value={outputMaterialId}
                onChange={setOutputMaterialId}
                placeholder="Buscar material…"
              />
            </label>
            <label className="field">
              <span>Rendimiento (%)</span>
              <input
                type="number"
                min={0}
                max={100}
                step={0.01}
                value={yieldPct}
                onChange={(e) => setYieldPct(e.target.value)}
                required
              />
            </label>
          </div>
          <div className="field-row">
            <label className="field">
              <span>Pureza de salida (%)</span>
              <input
                type="number"
                min={0}
                max={100}
                step={0.01}
                value={outputPurityPct}
                onChange={(e) => setOutputPurityPct(e.target.value)}
                required
              />
            </label>
            <label className="field">
              <span>Responsable</span>
              <input value={responsible} onChange={(e) => setResponsible(e.target.value)} />
            </label>
          </div>
          {error ? <div className="login-error">{error}</div> : null}
        </div>
        <div className="modal-footer">
          <button type="button" className="btn btn-ghost" onClick={onClose}>
            Cancelar
          </button>
          <button
            type="submit"
            className="btn btn-primary"
            disabled={submitting || usable.length === 0}
          >
            {submitting ? 'Guardando…' : 'Crear orden'}
          </button>
        </div>
      </form>
    </div>
  );
}
