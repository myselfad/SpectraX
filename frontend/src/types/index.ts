export interface HealthResponse {
  status: string;
  model_loaded: boolean;
  device: string;
  version: string;
  upscale_factor: number;
}

export interface SpatialResolution {
  x: number;
  y: number;
}

export interface UploadResponse {
  job_id: string;
  filename: string;
  file_type: string;
  width: number;
  height: number;
  num_bands: number;
  band_names: string[];
  crs: string | null;
  spatial_resolution: SpatialResolution | null;
  nodata_value: number | null;
  file_size_bytes: number;
}

export interface ProcessRequest {
  job_id: string;
  scale_factor: number;
  selected_bands: string[];
  uncertainty_passes: number;
  processing_mode: string;
}

export interface ProcessResponse {
  job_id: string;
  status: string;
}

export interface PipelineStep {
  name: string;
  status: string; // 'pending' | 'running' | 'completed' | 'failed'
  duration_ms: number | null;
  message: string | null;
}

export interface StatusResponse {
  job_id: string;
  status: string;
  current_step: string | null;
  steps: PipelineStep[];
  progress_percent: number;
  error: string | null;
  started_at: string | null;
  completed_at: string | null;
}

export interface MetricsResult {
  observation_consistency: Record<string, number> | null;
  reference_metrics: Record<string, number> | null;
}

export interface ProcessingInfo {
  model_name: string;
  model_type: string;
  scale_factor: number;
  input_width: number;
  input_height: number;
  output_width: number;
  output_height: number;
  input_bands: number;
  processing_time_seconds: number;
  device: string;
  uncertainty_passes: number | null;
  nir_method: string;
}

export interface BandInfo {
  name: string;
  method: string;
  description: string;
}

export interface ResultsResponse {
  job_id: string;
  status: string;
  original_image_url: string;
  sr_image_url: string;
  sr_bands_url: Record<string, string> | null;
  uncertainty_map_url: string | null;
  reliability_map_url?: string | null;
  metrics: MetricsResult | null;
  processing_info: ProcessingInfo | null;
  band_info: BandInfo[] | null;
  export_available: string[];
  reliability?: any;
  outputs?: any;
}

export type AppStep = 'landing' | 'upload' | 'configure' | 'processing' | 'results';
