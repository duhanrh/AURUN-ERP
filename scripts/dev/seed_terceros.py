"""Siembra proveedores y clientes de prueba (Fase 3 — Terceros).

Uso (desde la raíz del repo, con el backend corriendo en :8000):

    set AURUM_SEED_TENANT=<tenant_id>      # opcional, por defecto el de la GUIA
    set PYTHONUTF8=1
    backend\\.venv\\Scripts\\python.exe scripts\\dev\\seed_terceros.py

Re-ejecutable: los terceros ya existentes se omiten (409) en vez de duplicarse.
Maneja UTF-8 correctamente (sembrar con `curl` desde la terminal corrompe los
acentos y el backend responde 400).
"""

from __future__ import annotations

import os
import sys

import httpx

BASE = os.environ.get("AURUM_SEED_BASE", "http://localhost:8000/api/v1")
TENANT = os.environ.get("AURUM_SEED_TENANT", "da1bb041-b7ac-43d3-a2ea-d587b59704fe")
EMAIL = os.environ.get("AURUM_SEED_EMAIL", "admin@acme.example.com")
PASSWORD = os.environ.get("AURUM_SEED_PASSWORD", "Admin-12345")

SUPPLIERS = [
    dict(legal_name="Minera del Chocó S.A.S.", tax_id="901.234.567-1", country="CO", city="Chocó",
         contact_name="Andrés Ramírez", phone="+57 312 445 9081", email="contacto@mineradelchoco.co",
         main_material="Oro Crudo", certifications="RUC, RUCOM", rating=4.6, status="active"),
    dict(legal_name="Goldtech Internacional S.A.", tax_id="900.112.334-5", country="CO", city="Bogotá",
         contact_name="Laura Jiménez", phone="+57 310 220 7744", email="ventas@goldtech.co",
         main_material="Oro / Platino", certifications="ISO 9001, RUC", rating=4.4, status="active"),
    dict(legal_name="Plata Andina Ltda.", tax_id="890.445.221-3", country="CO", city="Medellín",
         contact_name="Felipe Ortiz", phone="+57 300 556 1290", email="felipe@plataandina.co",
         main_material="Plata Refinada", certifications="RUCOM", rating=3.8, status="active"),
    dict(legal_name="PlatGroup LATAM", tax_id="PE-20458821", country="PE", city="Lima",
         contact_name="Rosa Vargas", phone="+51 988 234 091", email="rvargas@platgroup.pe",
         main_material="Platino / Paladio", certifications="ISO 9001", rating=4.1, status="evaluation"),
    dict(legal_name="Mineros del Cauca", tax_id="845.778.902-9", country="CO", city="Cauca",
         contact_name="Hernán Quintero", phone="+57 318 902 4471", email="hquintero@minerosdelcauca.co",
         main_material="Oro Crudo", certifications="RUCOM", rating=3.5, status="inactive"),
]

CUSTOMERS = [
    dict(legal_name="Banco de la República", tax_id="860.005.235-2", city="Bogotá",
         segment="Institución Financiera", contact_name="Marcela Duque", phone="+57 601 343 1111",
         email="tesoreria@banrep.gov.co", preferred_material="Oro 24K Barras", status="active"),
    dict(legal_name="Joyería Oro & Arte S.A.S.", tax_id="811.223.456-7", city="Medellín",
         segment="Joyería / Retail", contact_name="Tatiana Restrepo", phone="+57 304 778 5512",
         email="compras@oroyarte.co", preferred_material="Oro 18K / 24K", credit_limit=50000, status="active"),
    dict(legal_name="Global Metals Corp.", tax_id="900.778.123-4", city="Barranquilla",
         segment="Exportador", contact_name="Eduardo Salas", phone="+57 315 667 9023",
         email="esalas@globalmetals.com", preferred_material="Platino / Paladio", credit_limit=30000,
         status="evaluation"),
    dict(legal_name="Silver & Sons Ltd.", tax_id="805.334.778-1", city="Cali", segment="Industria",
         contact_name="Camila Hoyos", phone="+57 312 884 0091", email="choyos@silversons.com",
         preferred_material="Plata .999", status="active"),
]


def main() -> None:
    login = httpx.post(f"{BASE}/auth/login", headers={"X-Tenant-ID": TENANT},
                       json={"email": EMAIL, "password": PASSWORD})
    login.raise_for_status()
    token = login.json()["access_token"]
    auth = {"Authorization": f"Bearer {token}"}

    for resource, rows in (("suppliers", SUPPLIERS), ("customers", CUSTOMERS)):
        created = skipped = 0
        for row in rows:
            r = httpx.post(f"{BASE}/{resource}", headers=auth, json=row)
            if r.status_code == 201:
                created += 1
            elif r.status_code == 409:
                skipped += 1  # ya existía (re-ejecución)
            else:
                print(f"  x {resource}: {row['legal_name']} -> {r.status_code} {r.text}", file=sys.stderr)
        print(f"{resource}: {created} creados, {skipped} ya existían")


if __name__ == "__main__":
    main()
