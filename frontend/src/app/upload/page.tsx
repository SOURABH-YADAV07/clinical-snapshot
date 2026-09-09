"use client";

import { useState } from "react";
import Link from "next/link";
import { uploadBundle, BundleUploadError } from "@/lib/api";
import type { PatientListItem } from "@/types/summary";

type Status =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "success"; patients: PatientListItem[] }
  | { kind: "error"; message: string };

export default function UploadPage() {
  const [status, setStatus] = useState<Status>({ kind: "idle" });

  async function handleFileChange(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) {
      return;
    }

    setStatus({ kind: "loading" });

    let parsed: unknown;
    try {
      const text = await file.text();
      parsed = JSON.parse(text);
    } catch {
      setStatus({ kind: "error", message: "That file isn't valid JSON." });
      return;
    }

    try {
      const patients = await uploadBundle(parsed);
      setStatus({ kind: "success", patients });
    } catch (error) {
      const message = error instanceof BundleUploadError ? error.message : "Could not upload the bundle.";
      setStatus({ kind: "error", message });
    }
  }

  return (
    <main className="page">
      <section className="card upload-card">
        <h2>Upload a FHIR Bundle</h2>
        <p className="empty">
          Upload a FHIR R4 Bundle JSON file. It&apos;s parsed and reconciled the same way as the
          built-in data, and any patients it contains will appear on the{" "}
          <Link href="/patients">Patients</Link> page.
        </p>

        <label className="upload-dropzone">
          <input type="file" accept=".json,application/json" onChange={handleFileChange} />
          {status.kind === "loading" ? "Uploading…" : "Choose a .json file"}
        </label>

        {status.kind === "error" && <p className="error">{status.message}</p>}

        {status.kind === "success" && (
          <div className="upload-result">
            <p>
              Found {status.patients.length} patient{status.patients.length === 1 ? "" : "s"}:
            </p>
            <ul className="item-list">
              {status.patients.map((patient) => (
                <li key={patient.id}>
                  <Link href={`/patients/${patient.id}`} className="item-title">
                    {patient.name ?? "Name unavailable"}
                  </Link>
                </li>
              ))}
            </ul>
            <Link href="/patients" className="back-link">
              View all patients &rarr;
            </Link>
          </div>
        )}
      </section>
    </main>
  );
}
