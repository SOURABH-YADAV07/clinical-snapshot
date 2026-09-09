import type { ProblemSummary } from "@/types/summary";
import { CodeLabel } from "@/components/CodeLabel";
import { formatDate } from "@/lib/formatDate";
import { titleCase } from "@/lib/titleCase";

// Field-driven, not resource-id-based — routes correctly as source data changes.
export function isProblemUncertain(problem: ProblemSummary): boolean {
  return !problem.code.display_available || !problem.reference_resolved;
}

export function ProblemItem({ problem }: { problem: ProblemSummary }) {
  return (
    <li>
      <div className="item-title">
        <CodeLabel code={problem.code} />
      </div>
      <div className="item-meta">
        {titleCase(problem.verification_status ?? "unknown")} &middot;{" "}
        {titleCase(problem.clinical_status ?? "unknown")}
        {problem.onset && <> &middot; Onset {formatDate(problem.onset)}</>}
      </div>
    </li>
  );
}

export function Problems({ problems }: { problems: ProblemSummary[] }) {
  return (
    <section className="card">
      <h2>Active Problems</h2>
      {problems.length === 0 ? (
        <p className="empty">No active problems recorded.</p>
      ) : (
        <ul className="item-list">
          {problems.map((problem) => (
            <ProblemItem key={problem.id} problem={problem} />
          ))}
        </ul>
      )}
    </section>
  );
}
