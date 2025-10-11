"use client";

import {
  CSSProperties,
  useEffect,
  useMemo,
  useState,
  type MouseEvent as ReactMouseEvent,
} from "react";
import clsx from "clsx";
import {
  assignScenes,
  deleteScene as deleteSceneApi,
  updateScene,
  SceneUpdatePayload,
  BatchSceneAssignmentPayload
} from "../lib/api";
import { Scene } from "../lib/types";
import { BreakdownSheetModal } from "./breakdown-sheet-modal";

type Props = {
  scenes: Scene[];
  onScenesChange?: (next: Scene[]) => void;
  onSceneUpdated?: (scene: Scene | null) => void;
  uploadId?: string | null;
};

type SceneDraft = {
  location?: string;
  cast?: string;
  script_day?: string;
};

const MAX_SCRIPT_DAY = 20;
const DAY_OPTIONS = Array.from({ length: MAX_SCRIPT_DAY }, (_, index) => (index + 1).toString());
const DAY_COLOR_PALETTE = [
  "#fefce8",
  "#ffe4e6",
  "#e0f2fe",
  "#ede9fe",
  "#dcfce7",
  "#fce7f3",
  "#fef2f2",
  "#e2e8f0",
  "#faf5ff",
  "#fff7ed"
];

const LOCATION_COLOR_PALETTE = [
  "#1d4ed8",
  "#16a34a",
  "#f97316",
  "#a855f7",
  "#d97706",
  "#0ea5e9",
  "#f43f5e",
  "#14b8a6",
  "#9333ea",
  "#e11d48"
];

const normalizeLocation = (location: string | null | undefined) =>
  (location ?? "").trim().toUpperCase();

const getDayColor = (scriptDay: number | null | undefined) => {
  if (!scriptDay) {
    return undefined;
  }
  return DAY_COLOR_PALETTE[(scriptDay - 1) % DAY_COLOR_PALETTE.length];
};

const getLocationColor = (location: string, map: Map<string, string>) =>
  map.get(normalizeLocation(location));

export function SceneGrid({ scenes, onScenesChange, onSceneUpdated, uploadId }: Props) {
  const [drafts, setDrafts] = useState<Record<string, SceneDraft>>({});
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [lastSelectedId, setLastSelectedId] = useState<string | null>(null);
  const [batchDay, setBatchDay] = useState("");
  const [batchLocation, setBatchLocation] = useState("");
  const [savingId, setSavingId] = useState<string | null>(null);
  const [rowDeletingId, setRowDeletingId] = useState<string | null>(null);
  const [bulkDeleting, setBulkDeleting] = useState(false);
  const [batchProcessing, setBatchProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [breakdownScene, setBreakdownScene] = useState<Scene | null>(null);

  const locationColorMap = useMemo(() => {
    const map = new Map<string, string>();
    let index = 0;
    scenes.forEach(scene => {
      const key = normalizeLocation(scene.location);
      if (!key) {
        return;
      }
      if (!map.has(key)) {
        map.set(key, LOCATION_COLOR_PALETTE[index % LOCATION_COLOR_PALETTE.length]);
        index += 1;
      }
    });
    return map;
  }, [scenes]);

  useEffect(() => {
    setDrafts({});
    setSelectedIds(prev => {
      const next = new Set<string>();
      scenes.forEach(scene => {
        if (prev.has(scene.id)) {
          next.add(scene.id);
        }
      });
      return next;
    });
  }, [scenes]);

  useEffect(() => {
    if (!breakdownScene) {
      return;
    }
    const stillExists = scenes.some(scene => scene.id === breakdownScene.id);
    if (!stillExists) {
      setBreakdownScene(null);
    }
  }, [breakdownScene, scenes]);

  const handleDraftChange = (sceneId: string, field: keyof SceneDraft, value: string) => {
    setError(null);
    setDrafts(prev => ({
      ...prev,
      [sceneId]: {
        ...prev[sceneId],
        [field]: value
      }
    }));
  };

  const resetDraft = (sceneId: string) => {
    setError(null);
    setDrafts(prev => {
      const { [sceneId]: _removed, ...rest } = prev;
      return rest;
    });
  };

  const removeDrafts = (sceneIds: string[]) => {
    setDrafts(prev => {
      const next = { ...prev };
      sceneIds.forEach(id => {
        delete next[id];
      });
      return next;
    });
  };

  const closeBreakdownModal = () => {
    setBreakdownScene(null);
  };

  const handleRowDoubleClick = (
    event: ReactMouseEvent<HTMLTableRowElement>,
    scene: Scene
  ) => {
    const target = event.target as HTMLElement | null;
    if (target && target.closest("input, select, textarea, button, a, [role='button']")) {
      return;
    }
    setBreakdownScene(scene);
  };

  const buildUpdatePayload = (scene: Scene, draft: SceneDraft | undefined): SceneUpdatePayload | null => {
    if (!draft) {
      return null;
    }

    const payload: SceneUpdatePayload = {};

    if (draft.location !== undefined) {
      const nextLocation = draft.location.trim();
      if (nextLocation !== scene.location) {
        payload.location = nextLocation;
      }
    }

    if (draft.cast !== undefined) {
      const nextCast = draft.cast
        .split(",")
        .map(entry => entry.trim())
        .filter(Boolean);
      const currentCastKey = scene.cast.map(entry => entry.trim()).join("|");
      const nextCastKey = nextCast.join("|");
      if (nextCastKey !== currentCastKey) {
        payload.cast = nextCast;
      }
    }

    if (draft.script_day !== undefined) {
      const trimmed = draft.script_day.trim();
      if (trimmed === "") {
        if (scene.script_day !== null && scene.script_day !== undefined) {
          payload.script_day = null;
        }
      } else {
        const parsed = Number.parseInt(trimmed, 10);
        if (Number.isNaN(parsed) || parsed < 1 || parsed > MAX_SCRIPT_DAY) {
          throw new Error(`Shooting day must be a whole number between 1 and ${MAX_SCRIPT_DAY}.`);
        }
        if (scene.script_day !== parsed) {
          payload.script_day = parsed;
        }
      }
    }

    return Object.keys(payload).length > 0 ? payload : null;
  };

  const handleSave = async (scene: Scene) => {
    const draft = drafts[scene.id];
    try {
      const payload = buildUpdatePayload(scene, draft);
      if (!payload) {
        resetDraft(scene.id);
        return;
      }
      setError(null);
      setSavingId(scene.id);
      const updated = await updateScene(scene.id, payload);
      if (onScenesChange) {
        onScenesChange(
          scenes.map(existing => (existing.id === updated.id ? updated : existing))
        );
      }
      onSceneUpdated?.(updated);
      resetDraft(scene.id);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Unable to update scene details.";
      setError(message);
    } finally {
      setSavingId(null);
    }
  };

  const hasChanges = (scene: Scene) => {
    try {
      const payload = buildUpdatePayload(scene, drafts[scene.id]);
      return payload !== null;
    } catch {
      return true;
    }
  };

  const toggleSelect = (sceneId: string, shiftKey: boolean = false) => {
    if (shiftKey && lastSelectedId && lastSelectedId !== sceneId) {
      // Shift-click: select range
      const lastIndex = scenes.findIndex(s => s.id === lastSelectedId);
      const currentIndex = scenes.findIndex(s => s.id === sceneId);

      if (lastIndex !== -1 && currentIndex !== -1) {
        const start = Math.min(lastIndex, currentIndex);
        const end = Math.max(lastIndex, currentIndex);
        const rangeIds = scenes.slice(start, end + 1).map(s => s.id);

        setSelectedIds(prev => {
          const next = new Set(prev);
          rangeIds.forEach(id => next.add(id));
          return next;
        });
        setLastSelectedId(sceneId);
        return;
      }
    }

    // Regular click: toggle individual selection
    setSelectedIds(prev => {
      const next = new Set(prev);
      if (next.has(sceneId)) {
        next.delete(sceneId);
      } else {
        next.add(sceneId);
      }
      return next;
    });
    setLastSelectedId(sceneId);
  };

  const toggleSelectAll = (checked: boolean) => {
    if (!checked) {
      setSelectedIds(new Set());
      return;
    }
    setSelectedIds(new Set(scenes.map(scene => scene.id)));
  };

  const clearSelection = () => {
    setSelectedIds(new Set());
  };

  const handleDeleteScene = async (sceneId: string) => {
    setError(null);
    setRowDeletingId(sceneId);
    try {
      await deleteSceneApi(sceneId);
      const nextScenes = scenes.filter(scene => scene.id !== sceneId);
      onScenesChange?.(nextScenes);
      setSelectedIds(prev => {
        const next = new Set(prev);
        next.delete(sceneId);
        return next;
      });
      removeDrafts([sceneId]);
      onSceneUpdated?.(nextScenes[0] ?? null);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to delete scene.";
      setError(message);
    } finally {
      setRowDeletingId(null);
    }
  };

  const handleDeleteSelected = async () => {
    if (selectedIds.size === 0) {
      setError("Select at least one scene to delete.");
      return;
    }
    setError(null);
    setBulkDeleting(true);
    try {
      const ids = Array.from(selectedIds);
      for (const id of ids) {
        await deleteSceneApi(id);
      }
      const remaining = scenes.filter(scene => !selectedIds.has(scene.id));
      onScenesChange?.(remaining);
      setSelectedIds(new Set());
      removeDrafts(ids);
      onSceneUpdated?.(remaining[0] ?? null);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to delete selected scenes.";
      setError(message);
    } finally {
      setBulkDeleting(false);
    }
  };

  const handleAssignSelected = async () => {
    if (selectedIds.size === 0) {
      setError("Select at least one scene before assigning.");
      return;
    }

    const payload: BatchSceneAssignmentPayload = {
      scene_ids: Array.from(selectedIds)
    };

    const trimmedLocation = batchLocation.trim();
    if (trimmedLocation) {
      payload.location = trimmedLocation;
    }

    const trimmedDay = batchDay.trim();
    if (trimmedDay) {
      const parsed = Number.parseInt(trimmedDay, 10);
      if (Number.isNaN(parsed) || parsed < 1 || parsed > MAX_SCRIPT_DAY) {
        setError(`Day must be a number between 1 and ${MAX_SCRIPT_DAY}.`);
        return;
      }
      payload.script_day = parsed;
    } else if (trimmedLocation) {
      setError("Specify a shooting day when assigning a location.");
      return;
    }

    if (payload.location === undefined && payload.script_day === undefined) {
      setError("Provide a location, a shooting day, or both before assigning.");
      return;
    }

    if (
      payload.location !== undefined &&
      payload.script_day !== undefined
    ) {
      const allIdsForDay = scenes
        .filter(scene => scene.script_day === payload.script_day)
        .map(scene => scene.id);
      payload.scene_ids = Array.from(
        new Set([...payload.scene_ids, ...allIdsForDay])
      );
    }

    setError(null);
    setBatchProcessing(true);
    try {
      const updatedScenes = await assignScenes(payload);
      if (updatedScenes.length === 0) {
        setError("No scenes were updated.");
        return;
      }
      const updates = new Map(updatedScenes.map(scene => [scene.id, scene]));
      const nextScenes = scenes.map(scene => updates.get(scene.id) ?? scene);
      onScenesChange?.(nextScenes);
      removeDrafts(updatedScenes.map(scene => scene.id));
      setBatchDay("");
      setBatchLocation("");
      onSceneUpdated?.(updatedScenes[0] ?? null);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to assign scenes.";
      setError(message);
    } finally {
      setBatchProcessing(false);
    }
  };

  const selectedCount = selectedIds.size;
  const isAllSelected = scenes.length > 0 && selectedCount === scenes.length;

  return (
    <div className="flex flex-col rounded border border-gray-200 bg-white shadow-sm max-h-[calc(100vh-200px)]">
      <div className="border-b border-gray-200 bg-gray-50 px-4 py-2 text-sm font-semibold uppercase tracking-wide text-gray-600">
        Scene Breakdown
      </div>
      <div className="sticky top-0 z-10 flex flex-wrap items-center gap-3 border-b border-gray-200 bg-white px-4 py-3 text-sm text-gray-700 shadow-md">
        <div className="font-semibold text-gray-800">
          Selected {selectedCount} / {scenes.length}
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <select
            value={batchDay}
            onChange={event => setBatchDay(event.target.value)}
            className="w-28 rounded border border-slate-300 px-2 py-1 text-sm bg-white"
          >
            <option value="">Select day</option>
            {DAY_OPTIONS.map(day => (
              <option key={day} value={day}>
                Day {day}
              </option>
            ))}
          </select>
          <div className="flex items-center gap-2">
            <span className="inline-block h-3 w-3 rounded-full bg-slate-300" aria-hidden />
            <input
              value={batchLocation}
              onChange={event => setBatchLocation(event.target.value)}
              placeholder="Location"
              className="w-48 rounded border border-slate-300 px-2 py-1 text-sm"
            />
          </div>
          <button
            onClick={handleAssignSelected}
            disabled={batchProcessing || selectedCount === 0}
            className="rounded bg-blue-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-blue-500 disabled:cursor-not-allowed disabled:bg-blue-300"
          >
            {batchProcessing ? "Assigning..." : "Assign Selected"}
          </button>
          <button
            onClick={clearSelection}
            disabled={selectedCount === 0}
            className="rounded border border-slate-300 px-3 py-1.5 text-xs font-semibold text-slate-600 hover:bg-slate-100 disabled:cursor-not-allowed disabled:text-slate-400"
          >
            Clear Selection
          </button>
          <button
            onClick={handleDeleteSelected}
            disabled={bulkDeleting || selectedCount === 0}
            className="rounded border border-red-400 px-3 py-1.5 text-xs font-semibold text-red-600 hover:bg-red-50 disabled:cursor-not-allowed disabled:border-red-200 disabled:text-red-300"
          >
            {bulkDeleting ? "Deleting..." : "Delete Selected"}
          </button>
        </div>
      </div>
      {error && (
        <div className="border-b border-red-200 bg-red-50 px-4 py-2 text-sm text-red-700">
          {error}
        </div>
      )}
      <div className="overflow-auto flex-1">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50 sticky top-0 z-[9]">
            <tr>
              <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-gray-600 bg-gray-50">
                <input
                  type="checkbox"
                  checked={isAllSelected}
                  onChange={event => toggleSelectAll(event.target.checked)}
                />
              </th>
              <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-gray-600 bg-gray-50">
                #
              </th>
              <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-gray-600 bg-gray-50">
                Scene
              </th>
              <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-gray-600 bg-gray-50">
                Slugline
              </th>
              <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-gray-600 bg-gray-50">
                Pages (1/8ths)
              </th>
              <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-gray-600 bg-gray-50">
                Pages (decimal)
              </th>
              <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-gray-600 bg-gray-50">
                Location
              </th>
              <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-gray-600 bg-gray-50">
                Cast
              </th>
              <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-gray-600 bg-gray-50">
                Shooting Day
              </th>
              <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-gray-600 bg-gray-50">
                Est. Cost
              </th>
              <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-gray-600 bg-gray-50">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 bg-white">
            {scenes.map(scene => {
              const draft = drafts[scene.id];
              const locationValue = draft?.location ?? scene.location;
              const castValue = draft?.cast ?? scene.cast.join(", ");
              const scriptDayValue =
                draft?.script_day ?? (scene.script_day !== null && scene.script_day !== undefined
                  ? scene.script_day.toString()
                  : "");
              const isSaving = savingId === scene.id;
              const disableSave = !hasChanges(scene) || isSaving;
              const isSelected = selectedIds.has(scene.id);
              const dayColor = getDayColor(scene.script_day);
              const locationColor =
                getLocationColor(scene.location, locationColorMap) ?? "#cbd5f5";
              const rowStyle: CSSProperties = {
                backgroundColor: !isSelected && dayColor ? dayColor : undefined,
                borderLeft: `6px solid ${locationColor}`,
              };

              return (
                <tr
                  key={scene.id}
                  className={clsx(
                    "align-top transition-colors",
                    isSelected ? "bg-blue-100" : "hover:bg-slate-100"
                  )}
                  style={rowStyle}
                  onDoubleClick={(event) => handleRowDoubleClick(event, scene)}
                >
                  <td className="px-3 py-2 text-sm text-gray-700">
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={(e) => toggleSelect(scene.id, (e.nativeEvent as PointerEvent).shiftKey)}
                    />
                  </td>
                  <td className="px-3 py-2 text-sm text-gray-700">{scene.sequence_index + 1}</td>
                  <td className="px-3 py-2 text-sm text-gray-700">{scene.name}</td>
                  <td className="px-3 py-2 text-sm text-gray-700">{scene.slugline}</td>
                  <td className="px-3 py-2 text-sm text-gray-700">{scene.page_eighths} / 8</td>
                  <td className="px-3 py-2 text-sm text-gray-700">{scene.page_decimal.toFixed(3)}</td>
                  <td className="px-3 py-2 text-sm text-gray-700">
                    <div className="flex items-center gap-2">
                      <span
                        className="inline-block h-3 w-3 rounded-full border border-white shadow-sm"
                        style={{ backgroundColor: locationColor }}
                        aria-hidden
                      />
                      <input
                        value={locationValue}
                        onChange={event =>
                          handleDraftChange(scene.id, "location", event.target.value)
                        }
                        className="w-full rounded border border-slate-300 px-2 py-1 text-sm"
                      />
                    </div>
                  </td>
                  <td className="px-3 py-2 text-sm text-gray-700">
                    <input
                      value={castValue}
                      onChange={event => handleDraftChange(scene.id, "cast", event.target.value)}
                      className="w-full rounded border border-slate-300 px-2 py-1 text-sm"
                      placeholder="Actor names separated by commas"
                    />
                  </td>
                  <td className="px-3 py-2 text-sm text-gray-700">
                    <select
                      value={scriptDayValue}
                      onChange={event =>
                        handleDraftChange(scene.id, "script_day", event.target.value)
                      }
                      className="w-24 rounded border border-slate-300 px-2 py-1 text-sm bg-white"
                    >
                      <option value="">Unassigned</option>
                      {DAY_OPTIONS.map(day => (
                        <option key={day} value={day}>
                          Day {day}
                        </option>
                      ))}
                    </select>
                  </td>
                  <td className="px-3 py-2 text-right text-sm text-gray-700 tabular-nums">
                    ${scene.estimated_cost.toFixed(2)}
                  </td>
                  <td className="px-3 py-2 text-sm">
                    <div className="flex flex-wrap gap-2">
                      <button
                        onClick={() => handleSave(scene)}
                        disabled={disableSave}
                        className="rounded bg-emerald-600 px-3 py-1 text-xs font-semibold text-white hover:bg-emerald-500 disabled:cursor-not-allowed disabled:bg-emerald-300"
                      >
                        {isSaving ? "Saving..." : "Save"}
                      </button>
                      <button
                        onClick={() => resetDraft(scene.id)}
                        disabled={!draft}
                        className="rounded border border-slate-300 px-3 py-1 text-xs font-semibold text-slate-600 hover:bg-slate-100 disabled:cursor-not-allowed disabled:text-slate-400"
                      >
                        Reset
                      </button>
                      <button
                        onClick={() => handleDeleteScene(scene.id)}
                        disabled={bulkDeleting || rowDeletingId === scene.id}
                        className="rounded border border-red-400 px-3 py-1 text-xs font-semibold text-red-600 hover:bg-red-50 disabled:cursor-not-allowed disabled:border-red-200 disabled:text-red-300"
                      >
                        {rowDeletingId === scene.id ? "Deleting..." : "Delete"}
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <div className="border-t border-gray-200 bg-gray-50 px-4 py-2 text-xs text-gray-500">
        Tip: Use comma-separated values for cast (e.g., &quot;Alex, Jordan, Pat&quot;). Assign shooting
        days (1-20) and locations here to influence the auto-scheduler (12 pages maximum per day, up to 20 shooting days).
      </div>
      <BreakdownSheetModal scene={breakdownScene} uploadId={uploadId} onClose={closeBreakdownModal} />
    </div>
  );
}






