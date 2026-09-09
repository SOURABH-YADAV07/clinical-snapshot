import Link from "next/link";

export default function HomePage() {
  return (
    <main className="page">
      <section className="hero">
        <h1 className="hero-title">Welcome to Clinical Snapshot</h1>
        <p className="hero-subtitle">
          A safe, scannable view of a patient&apos;s active problems, medications,
          allergies, encounters, and observations &mdash; reconciled from a raw
          FHIR bundle, with missing or uncertain information shown plainly
          instead of hidden or guessed.
        </p>
        <Link href="/patients" className="hero-cta">
          View Patients &rarr;
        </Link>
      </section>
    </main>
  );
}
