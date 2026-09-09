import type {
  AllergySummary,
  EncounterSummary,
  MedicationSummary,
  ObservationSummary,
  ProblemSummary,
} from "@/types/summary";
import type { ReactNode } from "react";
import { ProblemItem } from "@/components/Problems";
import { MedicationItem } from "@/components/Medications";
import { AllergyItem } from "@/components/Allergies";
import { EncounterItem } from "@/components/Encounters";
import { ObservationItem } from "@/components/Observations";

interface UncertainItemsProps {
  problems: ProblemSummary[];
  medications: MedicationSummary[];
  allergies: AllergySummary[];
  encounters: EncounterSummary[];
  observations: ObservationSummary[];
}

function UncertainGroup({ label, children }: { label: string; children: ReactNode }) {
  return (
    <>
      <div className="data-quality-group-label">{label}</div>
      <ul className="item-list">{children}</ul>
    </>
  );
}

export function UncertainItems({
  problems,
  medications,
  allergies,
  encounters,
  observations,
}: UncertainItemsProps) {
  const hasItems =
    problems.length > 0 ||
    medications.length > 0 ||
    allergies.length > 0 ||
    encounters.length > 0 ||
    observations.length > 0;

  return (
    <section className="card">
      <h2>Incomplete or Unverified Items</h2>
      {!hasItems ? (
        <p className="empty">No incomplete or unverified items for this patient.</p>
      ) : (
        <>
          {problems.length > 0 && (
            <UncertainGroup label="Problems">
              {problems.map((problem) => (
                <ProblemItem key={problem.id} problem={problem} />
              ))}
            </UncertainGroup>
          )}
          {medications.length > 0 && (
            <UncertainGroup label="Medications">
              {medications.map((medication) => (
                <MedicationItem key={medication.id} medication={medication} />
              ))}
            </UncertainGroup>
          )}
          {allergies.length > 0 && (
            <UncertainGroup label="Allergies">
              {allergies.map((allergy) => (
                <AllergyItem key={allergy.id} allergy={allergy} />
              ))}
            </UncertainGroup>
          )}
          {encounters.length > 0 && (
            <UncertainGroup label="Encounters">
              {encounters.map((encounter) => (
                <EncounterItem key={encounter.id} encounter={encounter} />
              ))}
            </UncertainGroup>
          )}
          {observations.length > 0 && (
            <UncertainGroup label="Observations">
              {observations.map((observation) => (
                <ObservationItem key={observation.id} observation={observation} />
              ))}
            </UncertainGroup>
          )}
        </>
      )}
    </section>
  );
}
