import { useCallback, useMemo, useState } from 'react';
import type { PitchKey } from './constants';

export function useHeatMapSelections<T>(zoneMap: Map<number, T>, cells: T[]) {
  const [selectedZoneId, setSelectedZoneId] = useState<number | null>(null);
  const [selectedPitchKey, setSelectedPitchKey] = useState<PitchKey | null>(null);

  const onZoneSelect = useCallback((zoneId: number) => {
    setSelectedZoneId((prev) => {
      const next = prev === zoneId ? null : zoneId;
      if (next !== null) {
        setSelectedPitchKey(null);
      }
      return next;
    });
  }, []);

  const onPitchSelect = useCallback((pitchKey: PitchKey) => {
    setSelectedPitchKey((prev) => {
      const next = prev === pitchKey ? null : pitchKey;
      if (next !== null) {
        setSelectedZoneId(null);
      }
      return next;
    });
  }, []);

  const resolvedPitchKey = useMemo<PitchKey | null>(
    () => (selectedZoneId ? null : selectedPitchKey),
    [selectedPitchKey, selectedZoneId],
  );

  const activeCells = useMemo(() => {
    if (!selectedZoneId) return cells;
    const selected = zoneMap.get(selectedZoneId);
    return selected ? [selected] : cells;
  }, [cells, selectedZoneId, zoneMap]);

  const clearSelections = useCallback(() => {
    setSelectedZoneId(null);
    setSelectedPitchKey(null);
  }, []);

  const hasSelection = useMemo(
    () => selectedZoneId !== null || selectedPitchKey !== null,
    [selectedPitchKey, selectedZoneId],
  );

  return {
    selectedZoneId,
    selectedPitchKey,
    resolvedPitchKey,
    activeCells,
    onZoneSelect,
    onPitchSelect,
    clearSelections,
    hasSelection,
  } as const;
}
