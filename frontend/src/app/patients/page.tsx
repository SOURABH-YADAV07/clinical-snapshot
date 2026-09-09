import { getPatientList } from "@/lib/api";
import { PatientCard } from "@/components/PatientCard";

export default async function PatientListPage() {
  let patients;
  try {
    patients = await getPatientList();
  } catch {
    return (
      <main className="page">
        <p className="error">
          Could not load the patient list. Is the backend running at{" "}
          {process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000"}?
        </p>
      </main>
    );
  }

  return (
    <main className="page">
      <h1>Patients</h1>
      {patients.length === 0 ? (
        <p className="empty">No patients found.</p>
      ) : (
        <div className="patient-list">
          {patients.map((patient) => (
            <PatientCard key={patient.id} patient={patient} />
          ))}
        </div>
      )}
    </main>
  );
}
