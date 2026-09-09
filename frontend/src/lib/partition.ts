// Splits a list into [known, uncertain] so callers never render both groups
// mixed together — see UncertainItems.tsx.
export function partitionByConfidence<T>(items: T[], isUncertain: (item: T) => boolean): [T[], T[]] {
  const known: T[] = [];
  const uncertain: T[] = [];
  for (const item of items) {
    (isUncertain(item) ? uncertain : known).push(item);
  }
  return [known, uncertain];
}
