"use client";

import { useEffect, useState } from "react";
import { SceneGrid } from "../components/scene-grid";
import { DayBuilder } from "../components/day-builder";
import { UploadPanel } from "../components/upload-panel";
import { Scene, DayPlan } from "../lib/types";
import {
  fetchScenes,
  fetchDayPlans,
  requestAutoSchedule,
  uploadScript,
  fetchLatestUpload
} from "../lib/api";

export default function HomePage() {
  const [scenes, setScenes] = useState<Scene[]>([]);
  const [days, setDays] = useState<DayPlan[]>([]);
  const [uploadId, setUploadId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const [sceneData, dayPlanData, latestUpload] = await Promise.all([
          fetchScenes(),
          fetchDayPlans(),
          fetchLatestUpload()
        ]);
        setScenes(sceneData);
        setDays(dayPlanData);
        if (latestUpload) {
          setUploadId(latestUpload.upload_id);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load data");
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
      const plan = await requestAutoSchedule(response.upload_id);
      setDays(plan);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
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
      setDays(plan);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate schedule");
    }
  };

  return (
    <main className="min-h-screen bg-slate-100 px-6 py-4">
      <div className="mx-auto flex max-w-6xl flex-col gap-4">
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
          <section className="grid gap-4 lg:grid-cols-[2fr,1fr]">
          <SceneGrid scenes={scenes} onScenesChange={setScenes} />
          <DayBuilder
            scenes={scenes}
            initialDays={days}
            onPlansChange={setDays}
            onAutoSchedule={handleAutoSchedule}
            autoSchedulingDisabled={!uploadId}
            uploadId={uploadId}
          />
        </section>
      )}
      </div>
    </main>
  );
}
