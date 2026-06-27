/**
 * Listado de Terceros (Clientes o Proveedores) — secciones 7.5/7.6.
 *
 * Cabecera con KPIs, tabla clicable (cada fila abre la ficha 360° en el
 * `DetailDrawer` reutilizable) y alta vía `PartyFormModal`. El botón de alta se
 * oculta sin el permiso `<recurso>:manage` (la autorización real la impone el
 * backend, sección 10.2). Parametrizado por `kind` para no duplicar la pantalla.
 */

import { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { useAuthStore } from '../auth/authStore';
import { createParty, fetchKpis, listParties } from './api';
import { DetailDrawer, type DrawerSection, type DrawerStat } from './DetailDrawer';
import { PartyFormModal } from './PartyFormModal';
import { STATUS_BADGE, STATUS_LABEL, type CreatePartyInput, type Party, type PartyKind } from './types';

interface PartiesPageProps {
  kind: PartyKind;
}

function initialsOf(name: string): string {
  const parts = name.replace(/[^\p{L}\s]/gu, '').trim().split(/\s+/);
  return ((parts[0]?.[0] ?? '') + (parts[1]?.[0] ?? '')).toUpperCase() || '··';
}

function money(value: number | null): string {
  if (value === null) return '—';
  return new Intl.NumberFormat('es-CO', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
  }).format(value);
}

export function PartiesPage({ kind }: PartiesPageProps) {
  const isSupplier = kind === 'supplier';
  const resource = isSupplier ? 'suppliers' : 'customers';
  const queryClient = useQueryClient();
  const canRead = useAuthStore((s) => s.hasPermission(`${resource}:access`));
  const canManage = useAuthStore((s) => s.hasPermission(`${resource}:manage`));

  const [modalOpen, setModalOpen] = useState(false);
  const [selected, setSelected] = useState<Party | null>(null);

  const listQuery = useQuery({
    queryKey: [resource],
    queryFn: () => listParties(kind),
    enabled: canRead,
  });
  const kpisQuery = useQuery({
    queryKey: [resource, 'kpis'],
    queryFn: () => fetchKpis(kind),
    enabled: canRead,
  });

  const createMutation = useMutation({
    mutationFn: (input: CreatePartyInput) => createParty(kind, input),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: [resource] });
      setModalOpen(false);
    },
  });

  const drawer = useMemo(() => (selected ? buildDrawer(selected, isSupplier) : null), [selected, isSupplier]);

  if (!canRead) {
    return (
      <div className="page-placeholder">
        <div className="ph-icon">🔒</div>
        <h2>Sin acceso</h2>
        <p>
          No tienes el permiso <code>{resource}:access</code> para ver este módulo.
        </p>
      </div>
    );
  }

  const kpis = kpisQuery.data;
  const entity = isSupplier ? 'proveedor' : 'cliente';

  return (
    <div className="module-page">
      <div className="kpi-grid">
        <KpiCard label={isSupplier ? 'Proveedores' : 'Clientes'} value={kpis?.total} variant="gold" />
        <KpiCard label="Activos" value={kpis?.active} variant="green" />
        <KpiCard label="En evaluación" value={kpis?.evaluation} variant="blue" />
        <KpiCard label="Inactivos" value={kpis?.inactive} variant="" />
      </div>

      <div className="section-head">
        <div>
          <h2 className="section-title">{isSupplier ? 'Directorio de proveedores' : 'Directorio de clientes'}</h2>
          <p className="section-subtitle">
            {listQuery.data ? `${listQuery.data.length} ${entity}(s) registrados` : 'Cargando…'}
          </p>
        </div>
        {canManage ? (
          <button className="btn btn-primary" onClick={() => setModalOpen(true)}>
            + Nuevo {isSupplier ? 'Proveedor' : 'Cliente'}
          </button>
        ) : null}
      </div>

      {listQuery.isError ? (
        <div className="login-error">No se pudieron cargar los terceros.</div>
      ) : null}

      <div className="table-wrap">
        <table className="table">
          <thead>
            <tr>
              <th>{isSupplier ? 'Razón social' : 'Nombre'}</th>
              <th>NIT / Documento</th>
              <th>{isSupplier ? 'Material' : 'Segmento'}</th>
              <th>Contacto</th>
              <th>{isSupplier ? 'Rating' : 'Crédito'}</th>
              <th>Estado</th>
            </tr>
          </thead>
          <tbody>
            {listQuery.data?.map((party) => (
              <tr key={party.id} className="row-clickable" onClick={() => setSelected(party)}>
                <td className="primary">{party.legal_name}</td>
                <td>{party.tax_id}</td>
                <td>{(isSupplier ? party.main_material : party.segment) ?? '—'}</td>
                <td>{party.contact_name ?? '—'}</td>
                <td className="gold">
                  {isSupplier
                    ? party.rating !== null
                      ? `${party.rating.toFixed(1)}/5`
                      : '—'
                    : party.credit_limit !== null
                      ? money(party.credit_limit)
                      : 'N/A'}
                </td>
                <td>
                  <span className={`badge ${STATUS_BADGE[party.status]}`}>
                    {STATUS_LABEL[party.status]}
                  </span>
                </td>
              </tr>
            ))}
            {listQuery.data?.length === 0 ? (
              <tr>
                <td colSpan={6} className="empty-row">
                  Aún no hay {entity}s registrados.
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>

      {drawer ? (
        <DetailDrawer
          open={selected !== null}
          onClose={() => setSelected(null)}
          initials={drawer.initials}
          title={drawer.title}
          subtitle={drawer.subtitle}
          badge={drawer.badge}
          stats={drawer.stats}
          sections={drawer.sections}
        />
      ) : null}

      {modalOpen ? (
        <PartyFormModal
          kind={kind}
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

function KpiCard({ label, value, variant }: { label: string; value?: number; variant: string }) {
  return (
    <div className={`kpi-card ${variant}`}>
      <span className="kpi-value">{value ?? '—'}</span>
      <span className="kpi-label">{label}</span>
    </div>
  );
}

interface DrawerModel {
  initials: string;
  title: string;
  subtitle: string;
  badge: { label: string; className: string };
  stats: DrawerStat[];
  sections: DrawerSection[];
}

function buildDrawer(party: Party, isSupplier: boolean): DrawerModel {
  const location = isSupplier ? party.country : party.city;
  const classifier = isSupplier ? party.main_material : party.segment;
  const subtitle = [classifier, location].filter(Boolean).join(' • ') || '—';

  const stats: DrawerStat[] = isSupplier
    ? [
        { label: 'Rating', value: party.rating !== null ? `${party.rating.toFixed(1)}/5` : '—', tone: 'gold' },
        { label: 'Saldo CxP', value: '—', tone: 'red' },
        { label: 'Órdenes', value: '—' },
      ]
    : [
        { label: 'Crédito', value: party.credit_limit !== null ? money(party.credit_limit) : 'N/A', tone: 'gold' },
        { label: 'Saldo CxC', value: '—', tone: 'red' },
        { label: 'Órdenes', value: '—' },
      ];

  const contact: DrawerSection = {
    title: 'Contacto',
    rows: [
      { label: 'Persona', value: party.contact_name },
      { label: 'Teléfono', value: party.phone },
      { label: 'Email', value: party.email },
    ],
  };

  const detail: DrawerSection = isSupplier
    ? {
        title: 'Información del proveedor',
        rows: [
          { label: 'NIT / RUC', value: party.tax_id },
          { label: 'País / Región', value: party.country },
          { label: 'Material principal', value: party.main_material },
          { label: 'Certificaciones', value: party.certifications },
        ],
      }
    : {
        title: 'Información del cliente',
        rows: [
          { label: 'NIT / Documento', value: party.tax_id },
          { label: 'Ciudad', value: party.city },
          { label: 'Segmento', value: party.segment },
          { label: 'Material preferente', value: party.preferred_material },
        ],
      };

  return {
    initials: initialsOf(party.legal_name),
    title: party.legal_name,
    subtitle,
    badge: { label: STATUS_LABEL[party.status], className: STATUS_BADGE[party.status] },
    stats,
    sections: [detail, contact],
  };
}
