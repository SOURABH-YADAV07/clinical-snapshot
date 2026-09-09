import Link from "next/link";
import type { PatientListItem } from "@/types/summary";

export function PatientCard({ patient }: { patient: PatientListItem }) {
  return (
    <Link href={`/patients/${patient.id}`} className="card patient-card">
      <div className="item-title">{patient.name ?? "Name unavailable"}</div>
      <div className="item-meta">
        DOB: {patient.birth_date ?? "Unknown"}
        {!patient.is_canonical && <span className="badge">Non-canonical record</span>}
      </div>
      {patient.note && <p className="empty">{patient.note}</p>}
    </Link>
  );
}
