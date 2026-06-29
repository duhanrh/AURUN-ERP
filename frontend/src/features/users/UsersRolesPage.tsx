/**
 * Configuración → Usuarios y Roles (sección 7.2 / tab `config-usuarios`).
 *
 * Lista los usuarios del tenant y permite crear, editar, eliminar (baja lógica) y
 * restaurar (gated por `users:manage`; el backend lo exige igual). El backend impide
 * borrarse a sí mismo o dejar al tenant sin el último superusuario activo.
 */

import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  createUser,
  deleteUser,
  listRoles,
  listUsers,
  restoreUser,
  updateUser,
} from '../auth/api';
import { ApiError } from '../auth/api';
import { useAuthStore } from '../auth/authStore';
import type { CreateUserInput, UpdateUserInput, User } from '../auth/types';
import { UserEditModal } from './UserEditModal';
import { UserFormModal } from './UserFormModal';

export function UsersRolesPage() {
  const queryClient = useQueryClient();
  const canManage = useAuthStore((s) => s.hasPermission('users:manage'));
  const myId = useAuthStore((s) => s.principal?.user_id);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<User | null>(null);
  const [showDeleted, setShowDeleted] = useState(false);

  const usersQuery = useQuery({
    queryKey: ['users', { showDeleted }],
    queryFn: () => listUsers(showDeleted),
    enabled: canManage,
  });
  const rolesQuery = useQuery({ queryKey: ['roles'], queryFn: listRoles, enabled: canManage });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['users'] });

  const createMutation = useMutation({
    mutationFn: (input: CreateUserInput) => createUser(input),
    onSuccess: async () => {
      await invalidate();
      setModalOpen(false);
    },
  });
  const updateMutation = useMutation({
    mutationFn: ({ id, input }: { id: string; input: UpdateUserInput }) => updateUser(id, input),
    onSuccess: async () => {
      await invalidate();
      setEditing(null);
    },
  });
  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteUser(id),
    onSuccess: invalidate,
    onError: (e) => alert(e instanceof ApiError ? e.message : 'No se pudo eliminar.'),
  });
  const restoreMutation = useMutation({ mutationFn: (id: string) => restoreUser(id), onSuccess: invalidate });

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
      <div className="section-head">
        <div>
          <h2 className="section-title">Usuarios del tenant</h2>
          <p className="section-subtitle">
            {usersQuery.data ? `${usersQuery.data.length} usuario(s)` : 'Cargando…'}
          </p>
        </div>
        <div className="row-actions">
          <label className="toggle-deleted">
            <input
              type="checkbox"
              checked={showDeleted}
              onChange={(e) => setShowDeleted(e.target.checked)}
            />
            Mostrar eliminados
          </label>
          <button className="btn btn-primary" onClick={() => setModalOpen(true)}>
            + Nuevo Usuario
          </button>
        </div>
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
              <th />
            </tr>
          </thead>
          <tbody>
            {usersQuery.data?.map((user) => (
              <tr key={user.id} className={user.is_deleted ? 'row-deleted' : ''}>
                <td className="primary">{user.full_name}</td>
                <td>{user.email}</td>
                <td>{user.role?.name ?? '—'}</td>
                <td>
                  {user.is_deleted ? (
                    <span className="badge badge-red">Eliminado</span>
                  ) : (
                    <span className={`badge ${user.is_active ? 'badge-green' : 'badge-gray'}`}>
                      {user.is_active ? 'Activo' : 'Inactivo'}
                    </span>
                  )}
                </td>
                <td className="gold">
                  {user.permissions.filter((p) => p.endsWith(':access')).length}
                </td>
                <td>
                  <div className="row-actions">
                    {user.is_deleted ? (
                      <button
                        className="btn btn-sm btn-ghost"
                        disabled={restoreMutation.isPending}
                        onClick={() => restoreMutation.mutate(user.id)}
                      >
                        Restaurar
                      </button>
                    ) : (
                      <>
                        <button className="btn btn-sm btn-ghost" onClick={() => setEditing(user)}>
                          Editar
                        </button>
                        {user.id !== myId ? (
                          <button
                            className="btn btn-sm btn-ghost"
                            disabled={deleteMutation.isPending}
                            onClick={() => deleteMutation.mutate(user.id)}
                          >
                            Eliminar
                          </button>
                        ) : null}
                      </>
                    )}
                  </div>
                </td>
              </tr>
            ))}
            {usersQuery.data?.length === 0 ? (
              <tr>
                <td colSpan={6} className="empty-row">
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

      {editing ? (
        <UserEditModal
          user={editing}
          roles={rolesQuery.data ?? []}
          submitting={updateMutation.isPending}
          onSubmit={async (input) => {
            await updateMutation.mutateAsync({ id: editing.id, input });
          }}
          onClose={() => setEditing(null)}
        />
      ) : null}
    </div>
  );
}
