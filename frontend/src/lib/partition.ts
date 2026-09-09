export function partitionByConfidence<T>(items: T[], isUncertain: (item: T) => boolean): [T[], T[]] {
  const known: T[] = [];
  const uncertain: T[] = [];
  for (const item of items) {
    (isUncertain(item) ? uncertain : known).push(item);
  }
  return [known, uncertain];
}
