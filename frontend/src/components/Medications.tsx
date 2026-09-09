import type { MedicationSummary } from "@/types/summary";
import { CodeLabel } from "@/components/CodeLabel";

export function isMedicationUncertain(medication: MedicationSummary): boolean {
  return !medication.medication.display_available;
}

export function MedicationItem({ medication }: { medication: MedicationSummary }) {
  return (
    <li>
      <div className="item-title">
        <CodeLabel code={medication.medication} />
      </div>
      {medication.instructions && <div className="item-meta">{medication.instructions}</div>}
    </li>
  );
}

export function Medications({ medications }: { medications: MedicationSummary[] }) {
  return (
    <section className="card">
      <h2>Medications</h2>
      {medications.length === 0 ? (
        <p className="empty">No active medications recorded.</p>
      ) : (
        <ul className="item-list">
          {medications.map((medication) => (
            <MedicationItem key={medication.id} medication={medication} />
          ))}
        </ul>
      )}
    </section>
  );
}
