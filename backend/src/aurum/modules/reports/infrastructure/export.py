"""Serialización de un reporte a CSV descargable (con cabecera de marca).

Mantiene el mismo formato de cabecera del prototipo (`report-brand`): marca, título,
número de documento y fecha, seguido de la tabla de datos y el resumen.
"""

from __future__ import annotations

import csv
import io

from aurum.modules.reports.application.dto import ReportTable


def to_csv(table: ReportTable) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow([table.brand_name])
    writer.writerow([table.title])
    writer.writerow(["Documento", table.document_number])
    writer.writerow(["Generado", table.generated_at.isoformat(timespec="seconds")])
    writer.writerow([])
    writer.writerow(table.columns)
    writer.writerows(table.rows)
    if table.summary:
        writer.writerow([])
        writer.writerow(["Resumen"])
        for item in table.summary:
            writer.writerow([item.label, item.value])
    return buffer.getvalue()
