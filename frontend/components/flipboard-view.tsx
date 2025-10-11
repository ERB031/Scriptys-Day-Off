"use client";

import { Scene, DayPlan } from "../lib/types";

interface FlipboardViewProps {
  days: DayPlan[];
  scenes: Scene[];
  uploadId: string | null;
  onPlansChange: (days: DayPlan[]) => void;
  onScenesChange: (scenes: Scene[]) => void;
  onSceneUpdated: (scene?: Scene | null) => void;
}

export function FlipboardView({
  days,
  scenes,
  uploadId,
}: FlipboardViewProps) {
  if (!uploadId) {
    return (
      <div className="p-8 text-center text-gray-600">
        Upload a script to view the shooting schedule
      </div>
    );
  }

  if (days.length === 0) {
    return (
      <div className="p-8 text-center text-gray-600">
        No shooting days scheduled yet
      </div>
    );
  }

  return (
    <div className="p-4">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Shooting Schedule</h2>
        <p className="text-sm text-gray-600">
          Production schedule organized by shooting days
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {days.map((day) => {
          const dayScenes = scenes.filter((s) => s.schedule_day_id === day.id);

          return (
            <div
              key={day.id}
              className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm"
            >
              <div className="mb-4 flex items-start justify-between">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">
                    {day.name}
                  </h3>
                  {day.shooting_date && (
                    <p className="text-sm text-gray-600">
                      {new Date(day.shooting_date).toLocaleDateString()}
                    </p>
                  )}
                </div>
                <div className="text-right">
                  <div className="text-sm font-medium text-gray-900">
                    {day.total_pages_decimal.toFixed(2)} pages
                  </div>
                  <div className="text-sm text-gray-600">
                    {Math.floor(day.total_minutes / 60)}h{" "}
                    {Math.floor(day.total_minutes % 60)}m
                  </div>
                  <div className="text-sm font-medium text-green-600">
                    ${day.total_cost.toLocaleString()}
                  </div>
                </div>
              </div>

              {day.location_summary && day.location_summary.length > 0 && (
                <div className="mb-2">
                  <span className="text-xs font-medium text-gray-700">
                    Locations:
                  </span>
                  <span className="ml-2 text-xs text-gray-600">
                    {day.location_summary.join(", ")}
                  </span>
                </div>
              )}

              {day.cast_summary && day.cast_summary.length > 0 && (
                <div className="mb-4">
                  <span className="text-xs font-medium text-gray-700">
                    Cast:
                  </span>
                  <span className="ml-2 text-xs text-gray-600">
                    {day.cast_summary.join(", ")}
                  </span>
                </div>
              )}

              <div className="space-y-2">
                {dayScenes.map((scene) => (
                  <div
                    key={scene.id}
                    className="flex items-start justify-between rounded border border-gray-100 bg-gray-50 p-3"
                  >
                    <div className="flex-1">
                      <div className="font-medium text-gray-900">
                        {scene.name} - {scene.slugline}
                      </div>
                      {scene.synopsis && (
                        <div className="mt-1 text-sm text-gray-600">
                          {scene.synopsis}
                        </div>
                      )}
                      {scene.cast && scene.cast.length > 0 && (
                        <div className="mt-1 text-xs text-gray-500">
                          Cast: {scene.cast.join(", ")}
                        </div>
                      )}
                    </div>
                    <div className="ml-4 text-right text-sm">
                      <div className="text-gray-900">
                        {scene.page_decimal.toFixed(2)}pg
                      </div>
                      <div className="text-gray-600">
                        {Math.floor(scene.estimated_minutes)}m
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
