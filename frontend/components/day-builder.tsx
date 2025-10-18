"use client";

import { CSSProperties, useEffect, useMemo, useState } from "react";
import clsx from "clsx";
import {
  DndContext,
  DragCancelEvent,
  DragEndEvent,
  DragStartEvent,
  DragOverlay,
  useDroppable,
  useDraggable
} from "@dnd-kit/core";
import { CSS } from "@dnd-kit/utilities";

import {
  API_BASE_URL,
  assignScenes,
  updateScheduleDayLocation,
  fetchLocationCompensation
} from "../lib/api";
import { DayPlan, Scene } from "../lib/types";

const MAX_SCRIPT_DAY = 20;
const UNASSIGNED_DROPPABLE_ID = "day-unassigned";

const LOCATION_COLOR_PALETTE = [
  "#1d4ed8",
  "#16a34a",
  "#f97316",
  "#a855f7",
  "#0ea5e9",
  "#d97706",
  "#ef4444",
  "#14b8a6",
  "#6366f1",
  "#e11d48"
];

const DOWNLOAD_BASE_URL = API_BASE_URL;

type DayBucket = {
  id: string;
  dayNumber: number;
  name: string;
  shootingLocation: string | null;
  locationSummary: string[];
  castSummary: string[];
  scenes: Scene[];
};

type Props = {
  scenes: Scene[];
  initialDays: DayPlan[];
  onPlansChange?: (next: DayPlan[]) => void;
  onAutoSchedule?: () => Promise<void> | void;
  autoSchedulingDisabled?: boolean;
  uploadId?: string | null;
  onScenesChange?: (next: Scene[]) => void;
  onSceneUpdated?: (scene?: Scene | null) => void;
};

const normalizeLocation = (location: string | null | undefined) =>
  (location ?? "").trim().toUpperCase();

const getLocationColor = (location: string, map: Map<string, string>) =>
  map.get(normalizeLocation(location));

export function DayBuilder({
  scenes,
  initialDays,
  onPlansChange,
  onAutoSchedule,
  autoSchedulingDisabled,
  uploadId,
  onScenesChange,
  onSceneUpdated
}: Props) {
  const [dragError, setDragError] = useState<string | null>(null);
  const [activeSceneId, setActiveSceneId] = useState<string | null>(null);
  const [filmingLocations, setFilmingLocations] = useState<string[]>([]);

  const totals = useMemo(() => {
    if (!initialDays.length) {
      return {
        totalCost: scenes.reduce((sum, scene) => sum + scene.estimated_cost, 0),
        totalPages: scenes.reduce((sum, scene) => sum + scene.page_decimal, 0),
        totalTime: scenes.reduce((sum, scene) => sum + scene.estimated_minutes, 0)
      };
    }

    return initialDays.reduce(
      (agg, day) => {
        agg.totalCost += day.total_cost;
        agg.totalPages += day.total_pages_decimal;
        agg.totalTime += day.total_minutes;
        return agg;
      },
      { totalCost: 0, totalPages: 0, totalTime: 0 }
    );
  }, [initialDays, scenes]);

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
    let cancelled = false;

    const loadLocations = async () => {
      try {
        const data = await fetchLocationCompensation();
        if (cancelled) {
          return;
        }
        const names = data
          .map((entry: { location_name?: string }) => (entry.location_name || "").trim())
          .filter(Boolean);
        setFilmingLocations(names);
      } catch (err) {
        console.error("Failed to load filming locations", err);
      }
    };

    loadLocations();

    const handleLocationsUpdated = () => {
      loadLocations();
    };

    if (typeof window !== "undefined") {
      window.addEventListener("filmingLocations:updated", handleLocationsUpdated);
    }

    return () => {
      cancelled = true;
      if (typeof window !== "undefined") {
        window.removeEventListener("filmingLocations:updated", handleLocationsUpdated);
      }
    };
  }, [uploadId]);

  const allLocations = useMemo(() => {
    const set = new Set<string>();
    filmingLocations.forEach(location => {
      if (location) {
        set.add(location);
      }
    });
    scenes.forEach(scene => {
      const value = (scene.location || "").trim();
      if (value) {
        set.add(value);
      }
    });
    return Array.from(set).sort((a, b) => a.localeCompare(b));
  }, [scenes, filmingLocations]);

  const [updatingDayLocation, setUpdatingDayLocation] = useState<number | null>(null);

  const { scheduledDays, unscheduledScenes } = useMemo(() => {
    const sortedScenes = [...scenes].sort(
      (a, b) => a.sequence_index - b.sequence_index
    );
    const unscheduled = sortedScenes.filter(scene => scene.script_day == null);

    const scenesByDay = new Map<number, Scene[]>();
    sortedScenes.forEach(scene => {
      if (scene.script_day != null) {
        const current = scenesByDay.get(scene.script_day) ?? [];
        current.push(scene);
        scenesByDay.set(scene.script_day, current);
      }
    });

    const dayNumberToPlan = new Map<number, DayPlan>();
    initialDays.forEach(day => {
      const numbers = new Set<number>();
      day.scenes.forEach(scene => {
        if (scene.script_day != null) {
          numbers.add(scene.script_day);
        }
      });
      if (numbers.size === 1) {
        const [dayNumber] = Array.from(numbers);
        dayNumberToPlan.set(dayNumber, day);
      }
    });

    const buckets: DayBucket[] = [];
    for (let dayNumber = 1; dayNumber <= MAX_SCRIPT_DAY; dayNumber += 1) {
      const plan = dayNumberToPlan.get(dayNumber);
      const dayScenes = scenesByDay.get(dayNumber) ?? [];

      const locationSummary =
        dayScenes.length > 0
          ? Array.from(new Set(dayScenes.map(scene => scene.location))).filter(Boolean)
          : plan?.location_summary ?? [];

      const castSummary =
        dayScenes.length > 0
          ? Array.from(new Set(dayScenes.flatMap(scene => scene.cast))).filter(Boolean)
          : plan?.cast_summary ?? [];

      const defaultName =
        locationSummary.length > 0
          ? `Day ${dayNumber} - ${locationSummary[0]}`
          : `Day ${dayNumber}`;

      buckets.push({
        id: plan?.id ?? `day-${dayNumber}`,
        dayNumber,
        name: plan?.name ?? defaultName,
        shootingLocation: plan?.shooting_location ?? null,
        locationSummary,
        castSummary,
        scenes: dayScenes.length > 0 ? dayScenes : plan?.scenes ?? []
      });
    }

    return {
      scheduledDays: buckets,
      unscheduledScenes: unscheduled
    };
  }, [initialDays, scenes]);

  const activeScene = useMemo(
    () => scenes.find(scene => scene.id === activeSceneId) ?? null,
    [scenes, activeSceneId]
  );

  const handleDragStart = (event: DragStartEvent) => {
    setDragError(null);
    setActiveSceneId(event.active.id as string);
  };

  const handleDragCancel = (_event: DragCancelEvent) => {
    setActiveSceneId(null);
  };

  const handleDragEnd = async (event: DragEndEvent) => {
    setActiveSceneId(null);
    const { active, over } = event;
    if (!over) {
      return;
    }

    const sceneId = active.id as string;
    const overId = String(over.id);

    const currentScene = scenes.find(scene => scene.id === sceneId);
    if (!currentScene) {
      return;
    }

    let targetDay: number | null;
    if (overId === UNASSIGNED_DROPPABLE_ID) {
      targetDay = null;
    } else {
      const match = overId.match(/^day-(\d+)$/);
      if (!match) {
        return;
      }
      targetDay = Number(match[1]);
      if (Number.isNaN(targetDay) || targetDay < 1 || targetDay > MAX_SCRIPT_DAY) {
        return;
      }
    }

    const currentDay = currentScene.script_day ?? null;
    if (currentDay === targetDay) {
      return;
    }

    try {
      setDragError(null);
      const payload = {
        scene_ids: [sceneId],
        script_day: targetDay
      };

      const updatedScenes = await assignScenes(payload);

      if (updatedScenes.length > 0) {
        const updates = new Map(updatedScenes.map(scene => [scene.id, scene]));
        onScenesChange?.(scenes.map(scene => updates.get(scene.id) ?? scene));
        onSceneUpdated?.(updatedScenes[0]);
      } else {
        onSceneUpdated?.(null);
      }
    } catch (error) {
      setDragError(
        error instanceof Error ? error.message : "Failed to reassign scene."
      );
    }
  };

  const handleDayLocationChange = async (dayNumber: number, nextLocation: string | null) => {
    try {
      setDragError(null);
      setUpdatingDayLocation(dayNumber);
      const trimmed = (nextLocation || "").trim();
      const plans = await updateScheduleDayLocation(dayNumber, {
        location: trimmed.length > 0 ? trimmed : null,
        upload_id: uploadId ?? undefined,
      });
      onPlansChange?.(plans);
    } catch (error) {
      setDragError(error instanceof Error ? error.message : "Failed to update day location.");
    } finally {
      setUpdatingDayLocation(null);
    }
  };

  return (
    <aside className="flex flex-col gap-4 rounded border border-gray-200 bg-white p-4 shadow-sm">
      <header className="flex flex-col gap-1">
        <h2 className="text-lg font-semibold text-gray-800">Day Builder</h2>
        <p className="text-sm text-gray-600">
          Drag scenes into day buckets to build your schedule (12 pages per day maximum).
        </p>
      </header>

      <section className="flex flex-col gap-1 rounded border border-slate-200 bg-slate-50 p-3 text-sm text-slate-700">
        <div className="flex justify-between">
          <span className="font-semibold text-slate-800">Total cost</span>
          <span>${totals.totalCost.toFixed(0)}</span>
        </div>
        <div className="flex justify-between">
          <span className="font-semibold text-slate-800">Total pages</span>
          <span>{totals.totalPages.toFixed(3)}</span>
        </div>
        <div className="flex justify-between">
          <span className="font-semibold text-slate-800">Total time</span>
          <span>{Math.round(totals.totalTime)} min</span>
        </div>
        <div className="flex justify-between">
          <span className="font-semibold text-slate-800">Scenes</span>
          <span>{scenes.length}</span>
        </div>
      </section>

      <button
        onClick={() => onAutoSchedule?.()}
        disabled={autoSchedulingDisabled}
        className="rounded bg-emerald-600 px-3 py-2 text-sm font-semibold text-white shadow hover:bg-emerald-500 disabled:cursor-not-allowed disabled:bg-emerald-300"
      >
        Run Auto-Scheduler
      </button>

      <div className="space-y-2">
        <div className="text-xs font-semibold text-slate-700 uppercase tracking-wide">Export Schedules</div>
        <div className="grid grid-cols-2 gap-2">
          <a
            href="#download-csv"
            onClick={event => {
              event.preventDefault();
              const query = uploadId ? `?upload_id=${uploadId}` : "";
              window.open(`${DOWNLOAD_BASE_URL}/schedule/export.csv${query}`, "_blank");
            }}
            className="rounded border border-slate-300 px-3 py-2 text-center text-xs font-semibold text-slate-700 hover:bg-slate-100"
          >
            📊 Day Budgets CSV
          </a>
          <a
            href="#download-pdf"
            onClick={event => {
              event.preventDefault();
              const query = uploadId ? `?upload_id=${uploadId}` : "";
              window.open(`${DOWNLOAD_BASE_URL}/schedule/export.pdf${query}`, "_blank");
            }}
            className="rounded border border-slate-300 px-3 py-2 text-center text-xs font-semibold text-slate-700 hover:bg-slate-100"
          >
            📄 Day Budgets PDF
          </a>
          <a
            href="#download-stripboard"
            onClick={event => {
              event.preventDefault();
              const query = uploadId ? `?upload_id=${uploadId}` : "";
              window.open(`${DOWNLOAD_BASE_URL}/schedule/stripboard/export.pdf${query}`, "_blank");
            }}
            className="rounded border border-slate-300 px-3 py-2 text-center text-xs font-semibold text-slate-700 hover:bg-slate-100"
          >
            📋 Stripboard PDF
          </a>
          <a
            href="#download-dood"
            onClick={event => {
              event.preventDefault();
              const query = uploadId ? `?upload_id=${uploadId}` : "";
              window.open(`${DOWNLOAD_BASE_URL}/schedule/dood/export.pdf${query}`, "_blank");
            }}
            className="rounded border border-slate-300 px-3 py-2 text-center text-xs font-semibold text-slate-700 hover:bg-slate-100"
          >
            📅 DOOD PDF
          </a>
        </div>
      </div>

      {dragError && (
        <div className="rounded border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-600">
          {dragError}
        </div>
      )}

      <DndContext
        onDragStart={handleDragStart}
        onDragEnd={handleDragEnd}
        onDragCancel={handleDragCancel}
      >
        <div className="space-y-3">
          <DayColumn
            droppableId={UNASSIGNED_DROPPABLE_ID}
            title="Unassigned Scenes"
            dayNumber={null}
            locationSummary={[]}
            castSummary={[]}
            scenes={unscheduledScenes}
            locationColorMap={locationColorMap}
            availableLocations={allLocations}
            shootingLocation={null}
            onLocationChange={undefined}
            isUpdating={false}
          />
          {scheduledDays.map(day => (
            <DayColumn
              key={day.dayNumber}
              droppableId={`day-${day.dayNumber}`}
              title={day.name}
              dayNumber={day.dayNumber}
              locationSummary={day.locationSummary}
              castSummary={day.castSummary}
              scenes={day.scenes}
              locationColorMap={locationColorMap}
              availableLocations={allLocations}
              shootingLocation={day.shootingLocation}
              onLocationChange={location => {
                if ((location ?? null) === (day.shootingLocation ?? null)) {
                  return;
                }
                handleDayLocationChange(day.dayNumber, location);
              }}
              isUpdating={updatingDayLocation === day.dayNumber}
            />
          ))}
        </div>

        <DragOverlay>
          {activeScene ? (
            <SceneCard
              scene={activeScene}
              locationColor={
                getLocationColor(activeScene.location, locationColorMap) ?? "#94a3b8"
              }
              isOverlay
            />
          ) : null}
        </DragOverlay>
      </DndContext>
    </aside>
  );
}

type DayColumnProps = {
  droppableId: string;
  title: string;
  dayNumber: number | null;
  locationSummary: string[];
  castSummary: string[];
  scenes: Scene[];
  locationColorMap: Map<string, string>;
  availableLocations: string[];
  shootingLocation: string | null;
  onLocationChange?: (location: string | null) => void;
  isUpdating?: boolean;
};
function DayColumn({
  droppableId,
  title,
  dayNumber,
  locationSummary,
  castSummary,
  scenes,
  locationColorMap,
  availableLocations,
  shootingLocation,
  onLocationChange,
  isUpdating = false
}: DayColumnProps) {
  const { setNodeRef, isOver } = useDroppable({ id: droppableId });

  const totalPages = scenes.reduce((sum, scene) => sum + scene.page_decimal, 0);
  const totalMinutes = scenes.reduce((sum, scene) => sum + scene.estimated_minutes, 0);
  const totalCost = scenes.reduce((sum, scene) => sum + scene.estimated_cost, 0);

  return (
    <article
      ref={setNodeRef}
      className={clsx(
        "rounded border border-slate-200 bg-white p-3 transition-colors",
        isOver && "ring-2 ring-indigo-400 bg-indigo-50/60"
      )}
    >
      <header className="mb-2 flex justify-between text-sm">
        <span className="font-semibold text-slate-800">
          {title}
          {dayNumber ? ` (Day ${dayNumber})` : ""}
        </span>
        <span className="text-slate-500">{totalPages.toFixed(3)} pgs</span>
      </header>
      {dayNumber && onLocationChange && (
        <div className="mb-2 text-xs">
          <label className="mb-1 block font-semibold text-slate-700">
            Shooting Location
          </label>
          <select
            value={shootingLocation ?? ""}
            onChange={event => onLocationChange(event.target.value || null)}
            disabled={isUpdating}
            className="w-full rounded border border-slate-300 bg-white px-2 py-1 text-xs focus:outline-none focus:ring-2 focus:ring-indigo-400 disabled:cursor-not-allowed disabled:bg-slate-100"
          >
            <option value="">Auto (dominant scene location)</option>
            {availableLocations.map(location => (
              <option key={location} value={location}>
                {location}
              </option>
            ))}
          </select>
        </div>
      )}
      <div className="mb-2 grid grid-cols-2 gap-2 text-xs text-slate-600">
        <div>
          <div className="font-semibold text-slate-700">Locations</div>
          <div>{locationSummary.join(", ") || "-"}</div>
        </div>
        <div>
          <div className="font-semibold text-slate-700">Cast</div>
          <div>{castSummary.join(", ") || "-"}</div>
        </div>
      </div>
      <div className="space-y-2">
        {scenes.length === 0 ? (
          <div className="rounded border border-dashed border-slate-300 p-2 text-center text-xs text-slate-400">
            Drag scenes here
          </div>
        ) : (
          scenes.map(scene => (
            <DraggableSceneCard
              key={scene.id}
              scene={scene}
              locationColor={
                getLocationColor(scene.location, locationColorMap) ?? "#94a3b8"
              }
            />
          ))
        )}
      </div>
      <footer className="mt-2 flex justify-between text-[11px] font-semibold text-slate-500">
        <span>${totalCost.toFixed(0)}</span>
        <span>{Math.round(totalMinutes)} min</span>
      </footer>
    </article>
  );
}

type SceneCardProps = {
  scene: Scene;
  locationColor: string;
  isOverlay?: boolean;
};

function SceneCard({ scene, locationColor, isOverlay = false }: SceneCardProps) {
  const castPreview = scene.cast.slice(0, 3).join(", ");
  const castSuffix = scene.cast.length > 3 ? "." : "";

  return (
    <div
      className={clsx(
        "rounded border border-slate-200 bg-white p-2 text-xs shadow-sm",
        isOverlay && "shadow-lg ring-2 ring-indigo-400"
      )}
    >
      <div className="flex items-center justify-between">
        <span className="font-semibold text-slate-700">
          #{scene.sequence_index + 1}
        </span>
        <span className="inline-flex items-center gap-1 text-[10px] uppercase text-slate-500">
          <span
            className="inline-block h-2 w-2 rounded-full"
            style={{ backgroundColor: locationColor }}
          />
          {scene.location || "-"}
        </span>
      </div>
      <div className="mt-1 text-slate-600">{scene.slugline}</div>
      <div className="mt-2 flex justify-between text-[10px] text-slate-500">
        <span>{scene.page_decimal.toFixed(3)} pgs</span>
        <span>
          {castPreview}
          {castSuffix}
        </span>
      </div>
    </div>
  );
}

type DraggableSceneCardProps = {
  scene: Scene;
  locationColor: string;
};

function DraggableSceneCard({ scene, locationColor }: DraggableSceneCardProps) {
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
    id: scene.id
  });

  const style: CSSProperties | undefined = transform
    ? {
        transform: CSS.Transform.toString(transform),
        zIndex: isDragging ? 1000 : undefined
      }
    : undefined;

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={clsx("cursor-grab", isDragging && "opacity-60")}
      {...listeners}
      {...attributes}
    >
      <SceneCard scene={scene} locationColor={locationColor} />
    </div>
  );
}
