import { dependencyMap } from "../components/setting-modal/constant";

export const resolveFullPermissions = (selected: string[]): string[] => {
  const result = new Set<string>();

  const resolve = (perm: string) => {
    if (result.has(perm)) return;
    result.add(perm);
    for (const dep of dependencyMap[perm] || []) {
      resolve(dep);
    }
  };

  selected.forEach(resolve);
  return Array.from(result);
};

export const computeAutoAssignedMap = (
  selected: string[]
): Record<string, string[]> => {
  const autoAssigned: Record<string, string[]> = {};
  const visited = new Set<string>();

  const resolve = (perm: string, root: string) => {
    for (const dep of dependencyMap[perm] || []) {
      const key = `${root}->${dep}`;
      if (visited.has(key)) continue;
      visited.add(key);

      if (!selected.includes(dep)) {
        if (!autoAssigned[dep]) autoAssigned[dep] = [];
        if (!autoAssigned[dep].includes(root)) autoAssigned[dep].push(root);
        resolve(dep, root);
      }
    }
  };

  selected.forEach((perm) => resolve(perm, perm));
  return autoAssigned;
};

export const removeSelectionAndUpdate = (
  toRemove: string,
  trueSelected: string[]
): {
  updatedSelected: string[];
  autoAssignedMap: Record<string, string[]>;
  trueSelected: string[];
} => {
  const newTrueSelected = trueSelected.filter((r) => r !== toRemove);
  const resolved = resolveFullPermissions(newTrueSelected);
  const newAutoMap = computeAutoAssignedMap(newTrueSelected);

  return {
    updatedSelected: resolved,
    autoAssignedMap: newAutoMap,
    trueSelected: newTrueSelected,
  };
};
