import Link from "next/link";
import { getPatientSummary, PatientNotFoundError } from "@/lib/api";
import type { PatientSummaryResponse } from "@/types/summary";
import { partitionByConfidence } from "@/lib/partition";
import { PatientHeader } from "@/components/PatientHeader";
import { Problems, isProblemUncertain } from "@/components/Problems";
import { Medications, isMedicationUncertain } from "@/components/Medications";
import { Allergies, isAllergyUncertain } from "@/components/Allergies";
import { Encounters, isEncounterUncertain } from "@/components/Encounters";
import { Observations, isObservationUncertain } from "@/components/Observations";
import { UncertainItems } from "@/components/UncertainItems";
import { DataQuality } from "@/components/DataQuality";

export default async function PatientSnapshotPage({
  params,
}: {
  params: Promise<{ patientId: string }>;
}) {
  const { patientId } = await params;

  let summary: PatientSummaryResponse | null = null;
  let errorMessage: string | null = null;

  try {
    summary = await getPatientSummary(patientId);
  } catch (error) {
    errorMessage =
      error instanceof PatientNotFoundError
        ? `Patient '${patientId}' was not found.`
        : `Could not load the clinical snapshot. Is the backend running at ${
            process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000"
          }?`;
  }

  if (errorMessage) {
    return (
      <main className="page">
        <Link href="/patients" className="back-link">
          &larr; Back to patients
        </Link>
        <p className="error">{errorMessage}</p>
      </main>
    );
  }

  if (!summary) {
    return null;
  }

  // Split into known vs. uncertain per section: known items render in their
  // normal section below; uncertain ones render only in UncertainItems, so
  // an item never appears twice or gets silently dropped.
  const [knownProblems, uncertainProblems] = partitionByConfidence(summary.problems, isProblemUncertain);
  const [knownMedications, uncertainMedications] = partitionByConfidence(
    summary.medications,
    isMedicationUncertain
  );
  const [knownAllergies, uncertainAllergies] = partitionByConfidence(summary.allergies, isAllergyUncertain);
  const [knownEncounters, uncertainEncounters] = partitionByConfidence(
    summary.encounters,
    isEncounterUncertain
  );
  const [knownObservations, uncertainObservations] = partitionByConfidence(
    summary.observations,
    isObservationUncertain
  );

  return (
    <main className="page">
      <Link href="/patients" className="back-link">
        &larr; Back to patients
      </Link>
      <PatientHeader patient={summary.patient} />
      <div className="grid two-col">
        <Problems problems={knownProblems} />
        <Medications medications={knownMedications} />
      </div>
      <div className="grid two-col">
        <Allergies allergies={knownAllergies} />
        <Encounters encounters={knownEncounters} />
      </div>
      <Observations observations={knownObservations} />
      <UncertainItems
        problems={uncertainProblems}
        medications={uncertainMedications}
        allergies={uncertainAllergies}
        encounters={uncertainEncounters}
        observations={uncertainObservations}
      />
      <DataQuality flags={summary.data_quality} />
    </main>
  );
}
