import type { AllergySummary } from "@/types/summary";
import { CodeLabel } from "@/components/CodeLabel";
import { UncertaintyNotes } from "@/components/UncertaintyNotes";

export function Allergies({ allergies }: { allergies: AllergySummary[] }) {
  return (
    <section className="card">
      <h2>Allergies</h2>
      {allergies.length === 0 ? (
        <p className="empty">No active allergies recorded.</p>
      ) : (
        <ul className="item-list">
          {allergies.map((allergy) => {
            const confirmed = allergy.verification_status === "confirmed";
            return (
              <li key={allergy.id} className={confirmed ? undefined : "unconfirmed"}>
                <div className="item-title">
                  <CodeLabel code={allergy.code} />
                </div>
                <div className="item-meta">
                  {confirmed ? "Confirmed" : `${allergy.verification_status ?? "Unknown"} · not confirmed`}
                  {allergy.criticality && <> &middot; Criticality: {allergy.criticality}</>}
                </div>
                <UncertaintyNotes notes={allergy.uncertainty_notes} />
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}
