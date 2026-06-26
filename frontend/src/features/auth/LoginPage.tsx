/**
 * Pantalla de login (Fase 2). Fiel al Design System oscuro/dorado de la maqueta.
 *
 * En desarrollo, además de email y contraseña se solicita el identificador del
 * tenant (UUID), que viaja como `X-Tenant-ID`; en producción esto se resolverá por
 * subdominio (sección 5.3) y el campo desaparecerá.
 */

import { useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';

import { ApiError, fetchMe, login } from './api';
import { useAuthStore } from './authStore';

export function LoginPage() {
  const navigate = useNavigate();
  const setTokens = useAuthStore((s) => s.setTokens);
  const setTenantId = useAuthStore((s) => s.setTenantId);
  const setPrincipal = useAuthStore((s) => s.setPrincipal);
  const storedTenant = useAuthStore((s) => s.tenantId);

  const [tenant, setTenant] = useState(storedTenant ?? '');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setLoading(true);
    try {
      setTenantId(tenant.trim());
      const tokens = await login(tenant.trim(), email.trim(), password);
      setTokens(tokens);
      setPrincipal(await fetchMe());
      navigate('/dashboard', { replace: true });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'No se pudo iniciar sesión.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login-screen">
      <form className="login-card" onSubmit={handleSubmit}>
        <div className="login-brand">
          <div className="logo-icon">◆</div>
          <div>
            <h1>AURUM ERP</h1>
            <span>Minería de metales preciosos</span>
          </div>
        </div>

        <h2 className="login-title">Iniciar sesión</h2>

        <label className="field">
          <span>Tenant (UUID)</span>
          <input
            value={tenant}
            onChange={(e) => setTenant(e.target.value)}
            placeholder="00000000-0000-0000-0000-000000000000"
            autoComplete="off"
            required
          />
        </label>

        <label className="field">
          <span>Email corporativo</span>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="usuario@empresa.com"
            autoComplete="username"
            required
          />
        </label>

        <label className="field">
          <span>Contraseña</span>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
            required
          />
        </label>

        {error ? <div className="login-error">{error}</div> : null}

        <button className="btn btn-primary btn-block" type="submit" disabled={loading}>
          {loading ? 'Entrando…' : 'Entrar'}
        </button>
      </form>
    </div>
  );
}
