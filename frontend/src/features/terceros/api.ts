/**
 * Endpoints del módulo de Terceros (Clientes/Proveedores).
 *
 * Reutiliza el cliente HTTP de identidad (`request`), que adjunta el Bearer y
 * gestiona el refresh-on-401. Cada `kind` mapea a su recurso REST en plural.
 */

import { request } from '../auth/api';
import type { CreatePartyInput, Party, PartyKind, PartyKpis } from './types';

const RESOURCE: Record<PartyKind, string> = {
  customer: '/customers',
  supplier: '/suppliers',
};

export async function listParties(kind: PartyKind): Promise<Party[]> {
  return request<Party[]>(RESOURCE[kind]);
}

export async function fetchKpis(kind: PartyKind): Promise<PartyKpis> {
  return request<PartyKpis>(`${RESOURCE[kind]}/kpis`);
}

export async function createParty(kind: PartyKind, input: CreatePartyInput): Promise<Party> {
  return request<Party>(RESOURCE[kind], { method: 'POST', body: input });
}

export async function updateParty(
  kind: PartyKind,
  id: string,
  input: Partial<CreatePartyInput>,
): Promise<Party> {
  return request<Party>(`${RESOURCE[kind]}/${id}`, { method: 'PATCH', body: input });
}
