/** Tipos de Reportes (Fase 7), espejo del API `/reports`. */

export interface ReportType {
  key: string;
  title: string;
  description: string;
}

export interface SummaryItem {
  label: string;
  value: string;
}

export interface ReportTable {
  key: string;
  title: string;
  brand_name: string;
  document_number: string;
  generated_at: string;
  columns: string[];
  rows: string[][];
  summary: SummaryItem[];
}
