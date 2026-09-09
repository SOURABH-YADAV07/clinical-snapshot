import type { ObservationSummary } from "@/types/summary";
import { CodeLabel } from "@/components/CodeLabel";
import { formatDate } from "@/lib/formatDate";

export function isObservationUncertain(observation: ObservationSummary): boolean {
  return !observation.code.display_available || !observation.reference_resolved;
}

export function ObservationItem({ observation }: { observation: ObservationSummary }) {
  return (
    <li>
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
        {observation.effective && <> &middot; {formatDate(observation.effective)}</>}
      </div>
    </li>
  );
}

export function Observations({ observations }: { observations: ObservationSummary[] }) {
  return (
    <section className="card">
      <h2>Relevant Observations</h2>
      {observations.length === 0 ? (
        <p className="empty">No relevant observations recorded.</p>
      ) : (
        <ul className="item-list">
          {observations.map((observation) => (
            <ObservationItem key={observation.id} observation={observation} />
          ))}
        </ul>
      )}
    </section>
  );
}
