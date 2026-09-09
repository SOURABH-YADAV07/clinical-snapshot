import type { PatientSummaryResponse } from "@/types/summary";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export class PatientNotFoundError extends Error {}

export async function getPatientSummary(patientId: string): Promise<PatientSummaryResponse> {
  const response = await fetch(`${API_BASE_URL}/api/patients/${patientId}/summary`, {
    cache: "no-store",
  });

  if (response.status === 404) {
    throw new PatientNotFoundError(`Patient '${patientId}' not found`);
  }
  if (!response.ok) {
    throw new Error(`Failed to load patient summary (status ${response.status})`);
  }

  return response.json();
}
