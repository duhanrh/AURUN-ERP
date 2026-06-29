/**
 * Modal "Editar Usuario": cambia nombre, rol, estado activo y (opcionalmente) la
 * contraseña. No toca las excepciones de permisos por módulo (se conservan); para
 * un rediseño completo de permisos se usa el alta. La contraseña vacía no se envía.
 */

import { useState, type FormEvent } from 'react';

import { ApiError } from '../auth/api';
import type { Role, UpdateUserInput, User } from '../auth/types';

interface UserEditModalProps {
  user: User;
  roles: Role[];
  submitting: boolean;
  onSubmit: (input: UpdateUserInput) => Promise<void>;
  onClose: () => void;
}

export function UserEditModal({ user, roles, submitting, onSubmit, onClose }: UserEditModalProps) {
  const [fullName, setFullName] = useState(user.full_name);
  const [roleSlug, setRoleSlug] = useState(user.role?.slug ?? roles[0]?.slug ?? '');
  const [isActive, setIsActive] = useState(user.is_active);
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    const input: UpdateUserInput = {
      full_name: fullName.trim(),
      role_slug: roleSlug,
      is_active: isActive,
    };
    if (password) input.password = password;
    try {
      await onSubmit(input);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'No se pudo actualizar el usuario.');
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <form className="modal" onClick={(e) => e.stopPropagation()} onSubmit={handleSubmit}>
        <div className="modal-header">
          <h3>Editar Usuario</h3>
          <button type="button" className="modal-close" onClick={onClose} aria-label="Cerrar">
            ✕
          </button>
        </div>

        <div className="modal-body">
          <label className="field">
            <span>Nombre</span>
            <input value={fullName} onChange={(e) => setFullName(e.target.value)} required />
          </label>
          <label className="field">
            <span>Email</span>
            <input value={user.email} disabled />
          </label>
          <div className="field-row">
            <label className="field">
              <span>Rol</span>
              <select value={roleSlug} onChange={(e) => setRoleSlug(e.target.value)}>
                {roles.map((role) => (
                  <option key={role.slug} value={role.slug}>
                    {role.name}
                  </option>
                ))}
              </select>
            </label>
            <label className="field">
              <span>Estado</span>
              <select value={isActive ? '1' : '0'} onChange={(e) => setIsActive(e.target.value === '1')}>
                <option value="1">Activo</option>
                <option value="0">Inactivo</option>
              </select>
            </label>
          </div>
          <label className="field">
            <span>Nueva contraseña (opcional)</span>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              minLength={8}
              placeholder="Dejar vacío para no cambiar"
            />
          </label>
          {error ? <div className="login-error">{error}</div> : null}
        </div>

        <div className="modal-footer">
          <button type="button" className="btn btn-ghost" onClick={onClose}>
            Cancelar
          </button>
          <button type="submit" className="btn btn-primary" disabled={submitting}>
            {submitting ? 'Guardando…' : 'Guardar cambios'}
          </button>
        </div>
      </form>
    </div>
  );
}
