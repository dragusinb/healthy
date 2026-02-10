// User types
export interface User {
  id: number;
  email: string;
  is_admin?: boolean;
  linked_accounts?: LinkedAccount[];
}

export interface LinkedAccount {
  id: number;
  provider_name: string;
  username: string;
  status: 'OK' | 'ERROR' | 'SYNCING';
  error_type?: string;
  error_acknowledged?: boolean;
  last_sync?: string;
}

// Dashboard types
export interface DashboardStats {
  documents_count: number;
  biomarkers_count: number;
  alerts_count: number;
}

export interface HealthOverview {
  profile: {
    full_name?: string;
    age?: number;
    gender?: string;
    blood_type?: string;
  } | null;
  profile_complete: boolean;
  timeline: {
    first_record_date?: string;
    tracking_duration?: string;
    total_documents?: number;
  } | null;
  health_status: {
    has_analysis: boolean;
    last_analysis_date?: string;
    days_since_analysis?: number;
  } | null;
  ai_summary?: string;
  reminders_count: number;
  reminders?: Array<{
    test_name: string;
    due_date: string;
  }>;
}

// Biomarker types
export interface Biomarker {
  id: number;
  name: string;
  canonical_name?: string;
  value: number | string;
  unit: string;
  range: string;
  status: 'normal' | 'high' | 'low';
  date: string;
  document_id?: number;
  provider?: string;
}

export interface BiomarkerGroup {
  canonical_name: string;
  has_issues: boolean;
  latest_date?: string;
  latest: Biomarker;
  history: Biomarker[];
}

export interface EvolutionData {
  name: string;
  history: Biomarker[];
  reference_range?: string;
  unit?: string;
}

// Document types
export interface Document {
  id: number;
  filename: string;
  document_date: string | null;
  provider: string | null;
  is_processed: boolean;
  patient_name: string | null;
  patient_cnp_prefix?: string;
  created_at: string;
}

export interface DocumentStats {
  total_documents: number;
  total_biomarkers: number;
  by_provider: Record<string, number>;
}

// Profile types
export interface Profile {
  full_name: string;
  date_of_birth: string;
  gender: string;
  height_cm: number | string;
  weight_kg: number | string;
  blood_type: string;
  allergies: string[];
  chronic_conditions: string[];
  current_medications: string[];
  smoking_status: string;
  alcohol_consumption: string;
  physical_activity: string;
}

// Auth types
export interface LoginResponse {
  access_token: string;
  token_type: string;
  recovery_key?: string;
  needs_password_setup?: boolean;
  needs_vault_unlock?: boolean;
}

export interface RegisterResponse {
  access_token: string;
  token_type: string;
  recovery_key?: string;
}

// API Error type
export interface ApiError {
  detail: string;
  status_code?: number;
}
