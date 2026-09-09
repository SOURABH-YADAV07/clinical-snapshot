import type { EncounterSummary } from "@/types/summary";
import { CodeLabel } from "@/components/CodeLabel";
import { formatDate } from "@/lib/formatDate";

export function isEncounterUncertain(encounter: EncounterSummary): boolean {
  return !encounter.type || !encounter.type.display_available;
}

export function EncounterItem({ encounter }: { encounter: EncounterSummary }) {
  return (
    <li>
      <div className="item-title">
        <CodeLabel code={encounter.type} />
      </div>
      <div className="item-meta">
        {formatDate(encounter.start) ?? "Start date unknown"}
        {encounter.age_days_at_snapshot != null && (
          <> &middot; {encounter.age_days_at_snapshot} days before snapshot</>
        )}
      </div>
    </li>
  );
}

export function Encounters({ encounters }: { encounters: EncounterSummary[] }) {
  return (
    <section className="card">
      <h2>Recent Encounters</h2>
      {encounters.length === 0 ? (
        <p className="empty">No recent encounters recorded.</p>
      ) : (
        <ul className="item-list">
          {encounters.map((encounter) => (
            <EncounterItem key={encounter.id} encounter={encounter} />
          ))}
        </ul>
      )}
    </section>
  );
}
