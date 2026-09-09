import type { PatientSummary } from "@/types/summary";

export function PatientHeader({ patient }: { patient: PatientSummary }) {
  return (
    <section className="card patient-header">
      <h1>{patient.name ?? "Name unavailable"}</h1>
      <dl>
        <div>
          <dt>DOB</dt>
          <dd>{patient.birth_date ?? "Unknown"}</dd>
        </div>
        <div>
          <dt>Gender</dt>
          <dd>{patient.gender ?? "Unknown"}</dd>
        </div>
        {patient.phone && (
          <div>
            <dt>Phone</dt>
            <dd>{patient.phone}</dd>
          </div>
        )}
        {patient.address && (
          <div>
            <dt>Address</dt>
            <dd>{patient.address}</dd>
          </div>
        )}
      </dl>
    </section>
  );
}
