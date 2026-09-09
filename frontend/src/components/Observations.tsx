import type { ObservationSummary } from "@/types/summary";
import { CodeLabel } from "@/components/CodeLabel";
import { UncertaintyNotes } from "@/components/UncertaintyNotes";

export function Observations({ observations }: { observations: ObservationSummary[] }) {
  return (
    <section className="card">
      <h2>Relevant Observations</h2>
      {observations.length === 0 ? (
        <p className="empty">No relevant observations recorded.</p>
      ) : (
        <ul className="item-list">
          {observations.map((observation) => (
            <li key={observation.id}>
              <div className="item-title">
                <CodeLabel code={observation.code} />
              </div>
              <div className="item-meta">
                {observation.values.map((value, index) => (
                  <span className="obs-value" key={index}>
                    {value.code?.display ? `${value.code.display}: ` : ""}
                    {value.value ?? "—"} {value.unit ?? ""}
                  </span>
                ))}
                {observation.effective && <> &middot; {observation.effective}</>}
              </div>
              {observation.encounter_reference && !observation.reference_resolved && (
                <div className="flag">
                  Referenced encounter could not be resolved: {observation.encounter_reference}
                </div>
              )}
              <UncertaintyNotes notes={observation.uncertainty_notes} />
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
