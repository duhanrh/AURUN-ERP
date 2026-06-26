/**
 * Modal "Nuevo Usuario" (réplica de `modal-usuario`, sección 7.2): nombre, email
 * corporativo, contraseña, rol y checklist de módulos con acceso.
 *
 * Al elegir un rol, los módulos se pre-marcan según los permisos de ese rol. Al
 * guardar se calculan las excepciones por usuario (sección 10.3): los módulos
 * marcados que el rol no incluye se envían como `granted_permissions`, y los
 * desmarcados que el rol sí incluye como `revoked_permissions`.
 */

import { useMemo, useState, type FormEvent } from 'react';

import { ApiError } from '../auth/api';
import type { CreateUserInput, Role } from '../auth/types';
import { MODULE_PERMISSIONS } from './modules';

interface UserFormModalProps {
  roles: Role[];
  submitting: boolean;
  onSubmit: (input: CreateUserInput) => Promise<void>;
  onClose: () => void;
}

export function UserFormModal({ roles, submitting, onSubmit, onClose }: UserFormModalProps) {
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [roleSlug, setRoleSlug] = useState(roles[0]?.slug ?? '');
  const [checked, setChecked] = useState<Set<string>>(new Set());
  const [touchedModules, setTouchedModules] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const selectedRole = useMemo(
    () => roles.find((r) => r.slug === roleSlug) ?? null,
    [roles, roleSlug],
  );

  // Módulos efectivos mostrados: si el usuario no ha tocado el checklist, refleja
  // los permisos del rol; si los tocó, respeta su selección.
  const effectiveChecked = touchedModules
    ? checked
    : new Set(selectedRole?.permissions ?? []);

  function toggleModule(code: string) {
    const next = new Set(effectiveChecked);
    if (next.has(code)) next.delete(code);
    else next.add(code);
    setChecked(next);
    setTouchedModules(true);
  }

  function onRoleChange(slug: string) {
    setRoleSlug(slug);
    setTouchedModules(false);
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    const rolePerms = new Set(selectedRole?.permissions ?? []);
    const granted = [...effectiveChecked].filter(
      (c) => !rolePerms.has(c) && MODULE_PERMISSIONS.some((m) => m.code === c),
    );
    const revoked = MODULE_PERMISSIONS.map((m) => m.code).filter(
      (c) => rolePerms.has(c) && !effectiveChecked.has(c),
    );
    try {
      await onSubmit({
        email: email.trim(),
        full_name: fullName.trim(),
        password,
        role_slug: roleSlug,
        granted_permissions: granted,
        revoked_permissions: revoked,
      });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'No se pudo crear el usuario.');
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <form className="modal" onClick={(e) => e.stopPropagation()} onSubmit={handleSubmit}>
        <div className="modal-header">
          <h3>Nuevo Usuario</h3>
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
            <span>Email corporativo</span>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="usuario@empresa.com"
              required
            />
          </label>

          <label className="field">
            <span>Contraseña temporal</span>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              minLength={8}
              required
            />
          </label>

          <label className="field">
            <span>Rol</span>
            <select value={roleSlug} onChange={(e) => onRoleChange(e.target.value)}>
              {roles.map((role) => (
                <option key={role.slug} value={role.slug}>
                  {role.name}
                </option>
              ))}
            </select>
          </label>

          <div className="field">
            <span>Módulos con acceso</span>
            <div className="module-checklist">
              {MODULE_PERMISSIONS.map((module) => (
                <label key={module.code} className="check-item">
                  <input
                    type="checkbox"
                    checked={effectiveChecked.has(module.code)}
                    onChange={() => toggleModule(module.code)}
                  />
                  <span>{module.label}</span>
                </label>
              ))}
            </div>
          </div>

          {error ? <div className="login-error">{error}</div> : null}
        </div>

        <div className="modal-footer">
          <button type="button" className="btn btn-ghost" onClick={onClose}>
            Cancelar
          </button>
          <button type="submit" className="btn btn-primary" disabled={submitting}>
            {submitting ? 'Guardando…' : 'Crear usuario'}
          </button>
        </div>
      </form>
    </div>
  );
}
