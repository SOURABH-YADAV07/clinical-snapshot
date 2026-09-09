export interface CodeDisplay {
  system: string | null;
  code: string | null;
  display: string | null;
  display_available: boolean;
}

export interface PatientSummary {
  id: string;
  name: string | null;
  birth_date: string | null;
  gender: string | null;
  phone: string | null;
  address: string | null;
}

export interface EncounterSummary {
  id: string;
  type: CodeDisplay | null;
  status: string | null;
  start: string | null;
  end: string | null;
  age_days_at_snapshot: number | null;
  uncertainty_notes: string[];
}

export interface ProblemSummary {
  id: string;
  code: CodeDisplay;
  clinical_status: string | null;
  verification_status: string | null;
  onset: string | null;
  encounter: EncounterSummary | null;
  encounter_reference: string | null;
  reference_resolved: boolean;
  uncertainty_notes: string[];
}

export interface MedicationSummary {
  id: string;
  medication: CodeDisplay;
  instructions: string | null;
  authored_on: string | null;
  status: string | null;
  uncertainty_notes: string[];
}

export interface AllergySummary {
  id: string;
  code: CodeDisplay;
  clinical_status: string | null;
  verification_status: string | null;
  criticality: string | null;
  uncertainty_notes: string[];
}

export interface ObservationValue {
  code: CodeDisplay | null;
  value: number | null;
  unit: string | null;
}

export interface ObservationSummary {
  id: string;
  code: CodeDisplay;
  values: ObservationValue[];
  effective: string | null;
  encounter: EncounterSummary | null;
  encounter_reference: string | null;
  reference_resolved: boolean;
  uncertainty_notes: string[];
}

export interface DataQualityFlag {
  message: string;
  resource_type: string | null;
  resource_id: string | null;
}

export interface PatientSummaryResponse {
  patient: PatientSummary;
  problems: ProblemSummary[];
  medications: MedicationSummary[];
  allergies: AllergySummary[];
  encounters: EncounterSummary[];
  observations: ObservationSummary[];
  data_quality: DataQualityFlag[];
}
