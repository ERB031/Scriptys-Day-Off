"use client";

import { useMemo } from "react";
import { DayPlan, Scene } from "../lib/types";

type Props = {
  scenes: Scene[];
  initialDays: DayPlan[];
  onPlansChange?: (next: DayPlan[]) => void;
  onAutoSchedule?: () => Promise<void> | void;
  autoSchedulingDisabled?: boolean;
  uploadId?: string | null;
};

export function DayBuilder({
  scenes,
  initialDays,
  onAutoSchedule,
  autoSchedulingDisabled,
  uploadId
}: Props) {
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
  const backendBaseUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

  return (
    <aside className="flex flex-col gap-4 rounded border border-gray-200 bg-white p-4 shadow-sm">
      <header className="flex flex-col gap-1">
        <h2 className="text-lg font-semibold text-gray-800">Day Builder</h2>
        <p className="text-sm text-gray-600">
          Auto-schedule scenes by shared locations and cast, then fine-tune manually. Drag-and-drop editing is on the
          roadmap.
        </p>
      </header>
      <section className="flex flex-col gap-1 rounded border border-slate-200 bg-slate-50 p-3 text-sm text-slate-700">
        <div className="flex justify-between">
          <span className="font-semibold text-slate-800">Total cost</span>
          <span>${totals.totalCost.toFixed(0)}</span>
        </div>
        <div className="flex justify-between">
          <span className="font-semibold text-slate-800">Total pages</span>
          <span>{totals.totalPages.toFixed(2)}</span>
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

      <div className="flex gap-2">
        <a
          href="#download-csv"
          onClick={event => {
            event.preventDefault();
            const query = uploadId ? `?upload_id=${uploadId}` : "";
            window.open(`${backendBaseUrl}/schedule/export.csv${query}`, "_blank");
          }}
          className="flex-1 rounded border border-slate-300 px-3 py-2 text-center text-xs font-semibold text-slate-700 hover:bg-slate-100"
        >
          Download CSV
        </a>
        <a
          href="#download-pdf"
          onClick={event => {
            event.preventDefault();
            const query = uploadId ? `?upload_id=${uploadId}` : "";
            window.open(`${backendBaseUrl}/schedule/export.pdf${query}`, "_blank");
          }}
          className="flex-1 rounded border border-slate-300 px-3 py-2 text-center text-xs font-semibold text-slate-700 hover:bg-slate-100"
        >
          Download PDF
        </a>
      </div>

      <div className="space-y-3">
        {initialDays.length === 0 && (
          <div className="rounded border border-dashed border-gray-300 p-3 text-center text-sm text-gray-500">
            Upload a script and run the auto-scheduler to see a draft shooting plan.
          </div>
        )}
        {initialDays.map(day => (
          <article key={day.id} className="rounded border border-slate-200 p-3">
            <header className="mb-2 flex justify-between text-sm">
              <span className="font-semibold text-slate-800">{day.name}</span>
              <span className="text-slate-600">{day.total_pages_decimal.toFixed(2)} pgs</span>
            </header>
            <div className="mb-2 grid grid-cols-2 gap-2 text-xs text-slate-600">
              <div>
                <div className="font-semibold text-slate-700">Locations</div>
                <div>{day.location_summary.join(", ") || "—"}</div>
              </div>
              <div>
                <div className="font-semibold text-slate-700">Cast</div>
                <div>{day.cast_summary.join(", ") || "—"}</div>
              </div>
            </div>
            <div className="text-xs text-slate-600">
              {day.scenes.map(scene => (
                <div key={scene.id} className="flex justify-between">
                  <span>
                    #{scene.sequence_index + 1} · {scene.slugline}
                  </span>
                  <span>{scene.page_decimal.toFixed(2)} pgs</span>
                </div>
              ))}
            </div>
            <footer className="mt-2 flex justify-between text-xs font-semibold text-slate-700">
              <span>Cost ${day.total_cost.toFixed(0)}</span>
              <span>{Math.round(day.total_minutes)} min</span>
            </footer>
          </article>
        ))}
      </div>
    </aside>
  );
}
