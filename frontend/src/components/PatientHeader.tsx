import type { PatientSummary } from "@/types/summary";
import { formatDate } from "@/lib/formatDate";

const GENDER_ICONS: Record<string, string> = {
  male: "♂",
  female: "♀",
};

function formatGender(gender: string | null): string | null {
  if (!gender) {
    return null;
  }
  const titleCased = gender.charAt(0).toUpperCase() + gender.slice(1).toLowerCase();
  const icon = GENDER_ICONS[gender.toLowerCase()];
  return icon ? `${icon} ${titleCased}` : titleCased;
}

export function PatientHeader({ patient }: { patient: PatientSummary }) {
  return (
    <section className="card patient-header">
      <h1>{patient.name ?? "Name unavailable"}</h1>
      <dl>
        <div>
          <dt>DOB</dt>
          <dd>{formatDate(patient.birth_date) ?? "Unknown"}</dd>
        </div>
        <div>
          <dt>Gender</dt>
          <dd>{formatGender(patient.gender) ?? "Unknown"}</dd>
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
