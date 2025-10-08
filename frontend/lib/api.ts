import { DayPlan, RateCard, Scene, SceneUploadResponse, UploadSnapshot } from "./types";

export const API_BASE_URL =
  typeof window === "undefined"
    ? process.env.BACKEND_URL || "http://localhost:8000"
    : process.env.NEXT_PUBLIC_BACKEND_URL || process.env.BACKEND_URL || "http://localhost:8000";

async function parseResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export async function fetchScenes(): Promise<Scene[]> {
  const res = await fetch(`${API_BASE_URL}/scenes`);
  return parseResponse<Scene[]>(res);
}

export async function fetchDayPlans(): Promise<DayPlan[]> {
  const res = await fetch(`${API_BASE_URL}/schedule/days`);
  return parseResponse<DayPlan[]>(res);
}

export async function uploadScript(
  file: File,
  options: { parseOnly?: boolean } = {}
): Promise<SceneUploadResponse> {
  const formData = new FormData();
  formData.append("file", file);
  if (options.parseOnly) {
    formData.append("parse_only", "true");
  }
  const res = await fetch(`${API_BASE_URL}/ingest/script`, {
    method: "POST",
    body: formData
  });
  return parseResponse<SceneUploadResponse>(res);
}

export async function requestAutoSchedule(uploadId: string): Promise<DayPlan[]> {
  const res = await fetch(`${API_BASE_URL}/schedule/auto`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ upload_id: uploadId })
  });
  return parseResponse<DayPlan[]>(res);
}

export async function fetchRateCards(): Promise<RateCard[]> {
  const res = await fetch(`${API_BASE_URL}/rate_cards`);
  return parseResponse<RateCard[]>(res);
}

export async function fetchLatestUpload(): Promise<UploadSnapshot | null> {
  const res = await fetch(`${API_BASE_URL}/ingest/latest`);
  if (res.status === 404) {
    return null;
  }
  return parseResponse<UploadSnapshot | null>(res);
}
