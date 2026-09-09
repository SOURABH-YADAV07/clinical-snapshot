import type { CodeDisplay } from "@/types/summary";

export function CodeLabel({ code }: { code: CodeDisplay | null }) {
  if (!code) {
    return null;
  }
  if (code.display_available && code.display) {
    return <span>{code.display}</span>;
  }
  return (
    <span className="code-unavailable">
      Code: {code.code ?? "unknown"} &mdash; <em>Display name unavailable</em>
    </span>
  );
}
