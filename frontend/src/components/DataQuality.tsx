import type { DataQualityFlag } from "@/types/summary";

export function DataQuality({ flags }: { flags: DataQualityFlag[] }) {
  return (
    <section className="card data-quality">
      <h2>Data Quality &amp; Uncertainty</h2>
      {flags.length === 0 ? (
        <p className="empty">No data-quality issues identified for this snapshot.</p>
      ) : (
        <ul className="data-quality-log">
          {flags.map((flag, index) => (
            <li key={index}>
              {flag.resource_type && flag.resource_id && (
                <span className="flag-source">
                  {flag.resource_type} {flag.resource_id}:{" "}
                </span>
              )}
              {flag.message}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
