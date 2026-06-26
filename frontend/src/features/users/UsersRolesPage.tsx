/**
 * Configuración → Usuarios y Roles (sección 7.2 / tab `config-usuarios`).
 *
 * Lista los usuarios del tenant y permite crear nuevos (gated por `users:manage`,
 * sección 10.2: el botón se oculta sin permiso y, además, el backend lo exige).
 */

import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { createUser, listRoles, listUsers } from '../auth/api';
import { useAuthStore } from '../auth/authStore';
import type { CreateUserInput } from '../auth/types';
import { UserFormModal } from './UserFormModal';

export function UsersRolesPage() {
  const queryClient = useQueryClient();
  const canManage = useAuthStore((s) => s.hasPermission('users:manage'));
  const [modalOpen, setModalOpen] = useState(false);

  const usersQuery = useQuery({ queryKey: ['users'], queryFn: listUsers, enabled: canManage });
  const rolesQuery = useQuery({ queryKey: ['roles'], queryFn: listRoles, enabled: canManage });

  const createMutation = useMutation({
    mutationFn: (input: CreateUserInput) => createUser(input),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['users'] });
      setModalOpen(false);
    },
  });

  if (!canManage) {
    return (
      <div className="page-placeholder">
        <div className="ph-icon">🔒</div>
        <h2>Sin acceso</h2>
        <p>No tienes el permiso <code>users:manage</code> para gestionar usuarios y roles.</p>
      </div>
    );
  }

  return (
    <div className="config-section">
      <div className="tab-bar">
        <div className="tab disabled">Apariencia / Marca</div>
        <div className="tab disabled">Módulos</div>
        <div className="tab disabled">Parámetros</div>
        <div className="tab active">Usuarios y Roles</div>
      </div>

      <div className="section-head">
        <div>
          <h2 className="section-title">Usuarios del tenant</h2>
          <p className="section-subtitle">
            {usersQuery.data ? `${usersQuery.data.length} usuario(s)` : 'Cargando…'}
          </p>
        </div>
        <button className="btn btn-primary" onClick={() => setModalOpen(true)}>
          + Nuevo Usuario
        </button>
      </div>

      {usersQuery.isError ? (
        <div className="login-error">No se pudieron cargar los usuarios.</div>
      ) : null}

      <div className="table-wrap">
        <table className="table">
          <thead>
            <tr>
              <th>Nombre</th>
              <th>Email</th>
              <th>Rol</th>
              <th>Estado</th>
              <th>Módulos</th>
            </tr>
          </thead>
          <tbody>
            {usersQuery.data?.map((user) => (
              <tr key={user.id}>
                <td className="primary">{user.full_name}</td>
                <td>{user.email}</td>
                <td>{user.role?.name ?? '—'}</td>
                <td>
                  <span className={`badge ${user.is_active ? 'badge-green' : 'badge-red'}`}>
                    {user.is_active ? 'Activo' : 'Inactivo'}
                  </span>
                </td>
                <td className="gold">
                  {user.permissions.filter((p) => p.endsWith(':access')).length}
                </td>
              </tr>
            ))}
            {usersQuery.data?.length === 0 ? (
              <tr>
                <td colSpan={5} className="empty-row">
                  Aún no hay usuarios.
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>

      {modalOpen ? (
        <UserFormModal
          roles={rolesQuery.data ?? []}
          submitting={createMutation.isPending}
          onSubmit={async (input) => {
            await createMutation.mutateAsync(input);
          }}
          onClose={() => setModalOpen(false)}
        />
      ) : null}
    </div>
  );
}
