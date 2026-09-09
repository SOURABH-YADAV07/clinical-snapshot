import type { ProblemSummary } from "@/types/summary";
import { CodeLabel } from "@/components/CodeLabel";
import { UncertaintyNotes } from "@/components/UncertaintyNotes";

export function Problems({ problems }: { problems: ProblemSummary[] }) {
  return (
    <section className="card">
      <h2>Active Problems</h2>
      {problems.length === 0 ? (
        <p className="empty">No active problems recorded.</p>
      ) : (
        <ul className="item-list">
          {problems.map((problem) => (
            <li key={problem.id}>
              <div className="item-title">
                <CodeLabel code={problem.code} />
              </div>
              <div className="item-meta">
                {problem.verification_status ?? "unknown"} &middot; {problem.clinical_status ?? "unknown"}
                {problem.onset && <> &middot; Onset {problem.onset}</>}
              </div>
              {problem.encounter_reference && !problem.reference_resolved && (
                <div className="flag">
                  Referenced encounter could not be resolved: {problem.encounter_reference}
                </div>
              )}
              <UncertaintyNotes notes={problem.uncertainty_notes} />
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
