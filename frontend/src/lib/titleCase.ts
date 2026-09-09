// Converts a raw FHIR status/criticality code (e.g. "entered-in-error",
// "unable-to-assess") into a readable title-cased label, without altering
// source-provided display text (which is left exactly as given elsewhere).
export function titleCase(value: string): string {
  return value
    .split(/[\s-]+/)
    .map((word) => (word ? word.charAt(0).toUpperCase() + word.slice(1) : word))
    .join(" ");
}
