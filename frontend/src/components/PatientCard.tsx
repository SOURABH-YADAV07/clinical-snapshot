import Link from "next/link";
import type { PatientListItem } from "@/types/summary";
import { formatDate } from "@/lib/formatDate";

export function PatientCard({ patient }: { patient: PatientListItem }) {
  return (
    <Link href={`/patients/${patient.id}`} className="card patient-card">
      <div className="patient-card-row">
        <span className="patient-card-label">Name :</span> {patient.name ?? "Name unavailable"}
        {!patient.is_canonical && <span className="badge">NCR</span>}
      </div>
      <div className="patient-card-row">
        <span className="patient-card-label">DOB :</span> {formatDate(patient.birth_date) ?? "Unknown"}
      </div>
      <div className="patient-card-row">
        <span className="patient-card-label">Contact :</span> {patient.phone ?? "Unknown"}
      </div>
    </Link>
  );
}
