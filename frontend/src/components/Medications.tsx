import type { MedicationSummary } from "@/types/summary";
import { CodeLabel } from "@/components/CodeLabel";
import { UncertaintyNotes } from "@/components/UncertaintyNotes";

export function Medications({ medications }: { medications: MedicationSummary[] }) {
  return (
    <section className="card">
      <h2>Medications</h2>
      {medications.length === 0 ? (
        <p className="empty">No active medications recorded.</p>
      ) : (
        <ul className="item-list">
          {medications.map((medication) => (
            <li key={medication.id}>
              <div className="item-title">
                <CodeLabel code={medication.medication} />
              </div>
              {medication.instructions && <div className="item-meta">{medication.instructions}</div>}
              <UncertaintyNotes notes={medication.uncertainty_notes} />
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
