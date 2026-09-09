import { getPatientSummary, PatientNotFoundError } from "@/lib/api";
import type { PatientSummaryResponse } from "@/types/summary";
import { PatientHeader } from "@/components/PatientHeader";
import { Problems } from "@/components/Problems";
import { Medications } from "@/components/Medications";
import { Allergies } from "@/components/Allergies";
import { Encounters } from "@/components/Encounters";
import { Observations } from "@/components/Observations";
import { DataQuality } from "@/components/DataQuality";

const PATIENT_ID = "patient-001";

export default async function Home() {
  let summary: PatientSummaryResponse | null = null;
  let errorMessage: string | null = null;

  try {
    summary = await getPatientSummary(PATIENT_ID);
  } catch (error) {
    errorMessage =
      error instanceof PatientNotFoundError
        ? `Patient '${PATIENT_ID}' was not found.`
        : `Could not load the clinical snapshot. Is the backend running at ${
            process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000"
          }?`;
  }

  if (errorMessage) {
    return (
      <main className="page">
        <p className="error">{errorMessage}</p>
      </main>
    );
  }

  if (!summary) {
    return null;
  }

  return (
    <main className="page">
      <PatientHeader patient={summary.patient} />
      <div className="grid two-col">
        <Problems problems={summary.problems} />
        <Medications medications={summary.medications} />
      </div>
      <div className="grid two-col">
        <Allergies allergies={summary.allergies} />
        <Encounters encounters={summary.encounters} />
      </div>
      <Observations observations={summary.observations} />
      <DataQuality flags={summary.data_quality} />
    </main>
  );
}
