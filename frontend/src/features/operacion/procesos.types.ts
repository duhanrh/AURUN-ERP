/** Tipos de Transformación y Calidad (Fase 5), espejo del API. */

export type Stage = 'reception' | 'analysis' | 'melting' | 'refining' | 'certified';
export type TransformationStatus = 'in_progress' | 'completed' | 'cancelled';
export type Process =
  | 'acid_refining'
  | 'melting_alloy'
  | 'rolling'
  | 'granulation'
  | 'purification';
export type AnalysisMethod = 'cupellation' | 'xrf' | 'fire_assay' | 'gravimetry';
export type SampleResult = 'pending' | 'approved' | 'rejected';

export interface TransformationOrder {
  id: string;
  order_code: string;
  input_lot_id: string;
  input_lot_code: string;
  input_material_name: string;
  process: Process;
  input_quantity_g: string;
  yield_fraction: string;
  output_material_id: string;
  output_material_name: string;
  output_form: 'raw' | 'refined';
  output_purity: string;
  expected_output_g: string;
  stage: Stage;
  status: TransformationStatus;
  blocked: boolean;
  responsible: string | null;
  started_at: string | null;
  expected_end: string | null;
  output_lot_id: string | null;
  created_at: string | null;
  is_deleted: boolean;
}

export interface TransformationKpis {
  total_orders: number;
  in_progress: number;
  completed: number;
  blocked: number;
}

export interface QualitySample {
  id: string;
  sample_code: string;
  lot_id: string;
  lot_code: string;
  material_name: string;
  method: AnalysisMethod;
  declared_purity: string;
  measured_purity: string;
  difference: string;
  analyst: string | null;
  result: SampleResult;
  sampled_at: string | null;
  created_at: string | null;
  is_deleted: boolean;
}

export interface QualityKpis {
  total_samples: number;
  approved: number;
  rejected: number;
  pending: number;
}

export interface CreateTransformationInput {
  input_lot_id: string;
  process: Process;
  input_quantity_g: string;
  yield_fraction: string;
  output_material_id: string;
  output_purity: string;
  output_form: 'raw' | 'refined';
  responsible?: string | null;
}

export interface CreateSampleInput {
  lot_id: string;
  method: AnalysisMethod;
  measured_purity: string;
  result: SampleResult;
  analyst?: string | null;
}

export const STAGE_ORDER: Stage[] = ['reception', 'analysis', 'melting', 'refining', 'certified'];
export const STAGE_LABEL: Record<Stage, string> = {
  reception: 'Recepción',
  analysis: 'Análisis',
  melting: 'Fundición',
  refining: 'Refinado',
  certified: 'Certificado',
};

export const PROCESS_LABEL: Record<Process, string> = {
  acid_refining: 'Refinación ácida',
  melting_alloy: 'Fusión / Aleación',
  rolling: 'Laminado',
  granulation: 'Granulación',
  purification: 'Purificación',
};

export const METHOD_LABEL: Record<AnalysisMethod, string> = {
  cupellation: 'Copelación',
  xrf: 'XRF',
  fire_assay: 'Ensayo de fuego',
  gravimetry: 'Gravimetría',
};

export const TS_STATUS_LABEL: Record<TransformationStatus, string> = {
  in_progress: 'En curso',
  completed: 'Completada',
  cancelled: 'Cancelada',
};
export const TS_STATUS_BADGE: Record<TransformationStatus, string> = {
  in_progress: 'badge-blue',
  completed: 'badge-green',
  cancelled: 'badge-gray',
};

export const RESULT_LABEL: Record<SampleResult, string> = {
  pending: 'Pendiente',
  approved: 'Aprobado',
  rejected: 'Rechazado',
};
export const RESULT_BADGE: Record<SampleResult, string> = {
  pending: 'badge-gold',
  approved: 'badge-green',
  rejected: 'badge-red',
};
