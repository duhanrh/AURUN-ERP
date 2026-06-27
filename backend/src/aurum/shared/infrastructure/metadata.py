"""Registro central de metadatos para Alembic.

Importa todos los modelos ORM para que queden registrados en ``Base.metadata``
y ``alembic revision --autogenerate`` los detecte. Cada módulo nuevo añade aquí
su import de modelos.
"""

from __future__ import annotations

# Importar (con efecto secundario de registro) los modelos de cada módulo.
from aurum.modules.auth.infrastructure import models as _auth_models  # noqa: F401
from aurum.modules.inventory.infrastructure import models as _inventory_models  # noqa: F401
from aurum.modules.purchasing.infrastructure import models as _purchasing_models  # noqa: F401
from aurum.modules.quality.infrastructure import models as _quality_models  # noqa: F401
from aurum.modules.sales.infrastructure import models as _sales_models  # noqa: F401
from aurum.modules.tenants.infrastructure import models as _tenants_models  # noqa: F401
from aurum.modules.terceros.infrastructure import models as _terceros_models  # noqa: F401
from aurum.modules.transformation.infrastructure import (
    models as _transformation_models,  # noqa: F401
)
from aurum.modules.users.infrastructure import models as _users_models  # noqa: F401
from aurum.shared.infrastructure.base import Base

target_metadata = Base.metadata
