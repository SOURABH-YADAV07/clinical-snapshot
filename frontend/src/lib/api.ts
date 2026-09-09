// Backend API client. Every read uses cache: "no-store" — the backend
// re-normalizes on each request, so the frontend must never cache a
// possibly-stale summary either.
import type { PatientListItem, PatientSummaryResponse } from "@/types/summary";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export class PatientNotFoundError extends Error {}
export class BundleUploadError extends Error {}

export async function getPatientList(): Promise<PatientListItem[]> {
  const response = await fetch(`${API_BASE_URL}/api/patients`, {
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error(`Failed to load patient list (status ${response.status})`);
  }
  return response.json();
}

export async function uploadBundle(bundle: unknown): Promise<PatientListItem[]> {
  const response = await fetch(`${API_BASE_URL}/api/bundles`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(bundle),
  });

  if (!response.ok) {
    const data = await response.json().catch(() => null);
    throw new BundleUploadError(data?.detail ?? `Upload failed (status ${response.status})`);
  }

  return response.json();
}

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
