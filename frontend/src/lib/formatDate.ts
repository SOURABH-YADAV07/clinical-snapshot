const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

const FULL_DATE_RE = /^\d{4}-\d{2}-\d{2}/;

// Only reformats dates with at least day precision (e.g. "1958-03-12" -> "12 Mar 1958").
// Coarser values (e.g. a bare year "2019") are returned unchanged rather than padded with
// a fabricated day/month — see docs/README.md, "Resolved Decisions" #2.
export function formatDate(value: string | null): string | null {
  if (!value || !FULL_DATE_RE.test(value)) {
    return value;
  }
  const [year, month, day] = value.slice(0, 10).split("-").map(Number);
  return `${day} ${MONTHS[month - 1]} ${year}`;
}
