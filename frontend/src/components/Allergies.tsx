import type { AllergySummary } from "@/types/summary";
import { CodeLabel } from "@/components/CodeLabel";
import { titleCase } from "@/lib/titleCase";

// Allergies have no encounter reference, so unconfirmed status stands in for it.
export function isAllergyUncertain(allergy: AllergySummary): boolean {
  return !allergy.code.display_available || allergy.verification_status !== "confirmed";
}

export function AllergyItem({ allergy }: { allergy: AllergySummary }) {
  const confirmed = allergy.verification_status === "confirmed";
  return (
    <li className={confirmed ? undefined : "unconfirmed"}>
      <div className="item-title">
        <CodeLabel code={allergy.code} />
      </div>
      <div className="item-meta">
        {confirmed ? "Confirmed" : `${titleCase(allergy.verification_status ?? "Unknown")} · Not Confirmed`}
        {allergy.criticality && <> &middot; Criticality: {titleCase(allergy.criticality)}</>}
      </div>
    </li>
  );
}

export function Allergies({ allergies }: { allergies: AllergySummary[] }) {
  return (
    <section className="card">
      <h2>Allergies</h2>
      {allergies.length === 0 ? (
        <p className="empty">No active allergies recorded.</p>
      ) : (
        <ul className="item-list">
          {allergies.map((allergy) => (
            <AllergyItem key={allergy.id} allergy={allergy} />
          ))}
        </ul>
      )}
    </section>
  );
}
