"use client";

import { useEffect, useState } from "react";
import { SceneGrid } from "../components/scene-grid";
import { DayBuilder } from "../components/day-builder";
import { UploadPanel } from "../components/upload-panel";
import { FlipboardView } from "../components/flipboard-view";
import { DayOutOfDaysView } from "../components/dood-view";
import CompensationView from "../components/compensation-view";
import { BreakdownView } from "../components/breakdown-view";
import { Scene, DayPlan } from "../lib/types";
import {
  fetchScenes,
  fetchDayPlans,
  requestAutoSchedule,
  uploadScript,
  fetchLatestUpload
} from "../lib/api";
import { parseApiError } from "../lib/utils"; // Import the utility

type TabType = "breakdown" | "flipboard" | "dood" | "compensation" | "breakdownsheets";

export default function HomePage() {
  const [scenes, setScenes] = useState<Scene[]>([]);
  const [days, setDays] = useState<DayPlan[]>([]);
  const [scheduleVersion, setScheduleVersion] = useState(0);
  const [uploadId, setUploadId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<TabType>("breakdown");

  const updateDays = (next: DayPlan[]) => {
    setDays(next);
    setScheduleVersion((prev) => prev + 1);
  };

  useEffect(() => {
    const load = async () => {
      try {
        const [sceneData, dayPlanData, latestUpload] = await Promise.all([
          fetchScenes(),
          fetchDayPlans(),
          fetchLatestUpload()
        ]);
        setScenes(sceneData);
        updateDays(dayPlanData);
        if (latestUpload) {
          setUploadId(latestUpload.upload_id);
        }
      } catch (err) {
        setError(parseApiError(err, "Failed to load data"));
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const handleUpload = async (file: File) => {
    setUploading(true);
    setError(null);
    try {
      const response = await uploadScript(file);
      setUploadId(response.upload_id);
      setScenes(response.scenes);
      const plan = await fetchDayPlans(response.upload_id);
      updateDays(plan);
    } catch (err) {
      setError(parseApiError(err, "Upload failed")); // Use the utility
    } finally {
      setUploading(false);
    }
  };

  const handleAutoSchedule = async () => {
    if (!uploadId) {
      return;
    }
    try {
      setError(null);
      const plan = await requestAutoSchedule(uploadId);
      updateDays(plan);
    } catch (err) {
      setError(parseApiError(err, "Failed to generate schedule")); // Use the utility
    }
  };

  const handleSceneUpdated = async (_scene?: Scene | null) => {
    setScheduleVersion((prev) => prev + 1);
  };

  const tabs: { id: TabType; label: string }[] = [
    { id: "breakdown", label: "Scene Breakdown" },
    { id: "breakdownsheets", label: "Breakdown Sheets" },
    { id: "flipboard", label: "Shooting Schedule" },
    { id: "dood", label: "Day Out Of Days" },
    { id: "compensation", label: "Compensation" },
  ];

  return (
    <main className="min-h-screen bg-slate-100 px-6 py-4">
      <div className="mx-auto flex max-w-7xl flex-col gap-4">
        <header className="mb-2 flex flex-col gap-1">
          <h1 className="text-3xl font-semibold text-gray-900">Scripty&apos;s Day Off</h1>
          <div className="text-sm text-gray-600">
            Smart breakdown, budgeting, and scheduling for film producers, ADs, and coordinators.
          </div>
        </header>

        <UploadPanel onUpload={handleUpload} disabled={uploading} />

        {loading && <div>Loading scenes…</div>}
        {error && (
          <div className="rounded border border-red-400 bg-red-50 p-3 text-red-700">{error}</div>
        )}

        {!loading && !error && (
          <>
            {/* Tab Navigation */}
            <div className="border-b border-gray-300">
              <nav className="flex gap-1">
                {tabs.map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`rounded-t-lg px-6 py-3 text-sm font-medium transition-colors ${
                      activeTab === tab.id
                        ? "border-b-2 border-blue-500 bg-white text-blue-600"
                        : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                    }`}
                  >
                    {tab.label}
                  </button>
                ))}
              </nav>
            </div>

            {/* Tab Content */}
            <div className="rounded-lg bg-white shadow-sm">
              {activeTab === "breakdown" && (
                <section className="grid gap-4 p-4 lg:grid-cols-[2fr,1fr]">
                  <SceneGrid
                    scenes={scenes}
                    onScenesChange={setScenes}
                    onSceneUpdated={handleSceneUpdated}
                    uploadId={uploadId}
                  />
                  <DayBuilder
                    scenes={scenes}
                    initialDays={days}
                    onPlansChange={updateDays}
                    onAutoSchedule={handleAutoSchedule}
                    autoSchedulingDisabled={!uploadId}
                    uploadId={uploadId}
                    onScenesChange={setScenes}
                    onSceneUpdated={handleSceneUpdated}
                  />
                </section>
              )}

              {activeTab === "flipboard" && (
                <FlipboardView
                  days={days}
                  scenes={scenes}
                  uploadId={uploadId}
                  onPlansChange={updateDays}
                  onScenesChange={setScenes}
                  onSceneUpdated={handleSceneUpdated}
                />
              )}

              {activeTab === "dood" && <DayOutOfDaysView uploadId={uploadId} version={scheduleVersion} />}

              {activeTab === "compensation" && (
                <div className="p-4">
                  <CompensationView uploadId={uploadId} />
                </div>
              )}

              {activeTab === "breakdownsheets" && uploadId && (
                <div className="h-[calc(100vh-300px)]">
                  <BreakdownView uploadId={uploadId} />
                </div>
              )}

              {activeTab === "breakdownsheets" && !uploadId && (
                <div className="p-8 text-center text-gray-600">
                  Upload a script to generate breakdown sheets
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </main>
  );
}
