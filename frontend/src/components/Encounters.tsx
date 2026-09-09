import type { EncounterSummary } from "@/types/summary";
import { CodeLabel } from "@/components/CodeLabel";
import { UncertaintyNotes } from "@/components/UncertaintyNotes";

export function Encounters({ encounters }: { encounters: EncounterSummary[] }) {
  return (
    <section className="card">
      <h2>Recent Encounters</h2>
      {encounters.length === 0 ? (
        <p className="empty">No recent encounters recorded.</p>
      ) : (
        <ul className="item-list">
          {encounters.map((encounter) => (
            <li key={encounter.id}>
              <div className="item-title">
                <CodeLabel code={encounter.type} />
              </div>
              <div className="item-meta">
                {encounter.start ?? "Start date unknown"}
                {encounter.age_days_at_snapshot != null && (
                  <> &middot; {encounter.age_days_at_snapshot} days before snapshot</>
                )}
              </div>
              <UncertaintyNotes notes={encounter.uncertainty_notes} />
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
