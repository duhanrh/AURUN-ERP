/**
 * Catálogo de permisos de acceso por módulo para el checklist de `modal-usuario`
 * (sección 7.2). Los códigos coinciden con el catálogo de plataforma del backend
 * (`users/domain/permissions.py`). El acceso efectivo de un usuario se calcula como
 * permisos del rol ± estas excepciones por módulo.
 */

export interface ModulePermission {
  code: string;
  label: string;
}

export const MODULE_PERMISSIONS: ModulePermission[] = [
  { code: 'dashboard:access', label: 'Dashboard' },
  { code: 'inventory:access', label: 'Inventario' },
  { code: 'purchasing:access', label: 'Compras' },
  { code: 'sales:access', label: 'Ventas' },
  { code: 'transformation:access', label: 'Transformación' },
  { code: 'suppliers:access', label: 'Proveedores' },
  { code: 'customers:access', label: 'Clientes' },
  { code: 'quality:access', label: 'Calidad / Lab' },
  { code: 'accounting:access', label: 'Contabilidad' },
  { code: 'reports:access', label: 'Reportes' },
  { code: 'configuration:access', label: 'Configuración' },
];
