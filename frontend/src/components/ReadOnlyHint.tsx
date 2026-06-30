/**
 * Chip discreto "Solo lectura" que se muestra cuando el usuario puede ver un módulo
 * pero no tiene su permiso `:manage` para crear/editar. No es un botón deshabilitado
 * (eso sería para restricciones de estado): es contexto para que no se busque en vano
 * una acción que el rol no permite. La autorización real la impone el backend.
 */

interface ReadOnlyHintProps {
  /** Permiso de gestión que falta, p. ej. `inventory:manage`. */
  permission: string;
}

export function ReadOnlyHint({ permission }: ReadOnlyHintProps) {
  return (
    <span className="readonly-chip" title={`Necesitas el permiso "${permission}" para crear o editar`}>
      <span aria-hidden>🔒</span> Solo lectura
    </span>
  );
}
