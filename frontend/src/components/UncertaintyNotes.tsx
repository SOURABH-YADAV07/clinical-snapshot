export function UncertaintyNotes({ notes }: { notes: string[] }) {
  if (notes.length === 0) {
    return null;
  }
  return (
    <ul className="uncertainty-notes">
      {notes.map((note) => (
        <li key={note}>{note}</li>
      ))}
    </ul>
  );
}
