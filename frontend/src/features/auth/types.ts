/** Tipos del dominio de identidad compartidos por el frontend (espejo del API). */

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface Principal {
  user_id: string;
  tenant_id: string;
  role: string | null;
  permissions: string[];
}

export interface Role {
  id: string;
  slug: string;
  name: string;
  description: string;
  is_system: boolean;
  permissions: string[];
}

export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  role: Role | null;
  permissions: string[];
  last_login_at: string | null;
  created_at: string | null;
}

export interface CreateUserInput {
  email: string;
  full_name: string;
  password: string;
  role_slug: string;
  granted_permissions: string[];
  revoked_permissions: string[];
}
