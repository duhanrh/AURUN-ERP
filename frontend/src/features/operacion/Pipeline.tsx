/**
 * Componente reutilizable de "pipeline de etapas" (réplica de `.pipeline-steps`
 * de la maqueta, sección 7.4). Parametrizable por la lista de etapas y la actual;
 * refleja el estado real de la orden (etapas previas = done, actual = active,
 * siguientes = pending). Si está bloqueada, la etapa activa se marca en rojo.
 */

interface PipelineProps {
  stages: { key: string; label: string }[];
  currentStage: string;
  /** Si la orden está completada, todas las etapas se muestran como done. */
  completed?: boolean;
  /** Bloqueo por cuarentena (muestra rechazada): resalta la etapa activa. */
  blocked?: boolean;
}

export function Pipeline({ stages, currentStage, completed = false, blocked = false }: PipelineProps) {
  const currentIndex = stages.findIndex((s) => s.key === currentStage);

  function stateOf(index: number): 'done' | 'active' | 'pending' {
    if (completed) return 'done';
    if (index < currentIndex) return 'done';
    if (index === currentIndex) return 'active';
    return 'pending';
  }

  return (
    <div className="pipeline-steps">
      {stages.map((stage, index) => {
        const state = stateOf(index);
        const isBlockedActive = blocked && state === 'active';
        return (
          <div key={stage.key} className={`pipe-step ${state} ${isBlockedActive ? 'blocked' : ''}`}>
            <div className="pipe-dot">
              {state === 'done' ? '✓' : isBlockedActive ? '⚠' : index + 1}
            </div>
            <div className="pipe-label">{stage.label}</div>
          </div>
        );
      })}
    </div>
  );
}
