import {
  ActorCompensation,
  CharacterAssignment,
  DayPlan,
  RateCard,
  Scene,
  SceneUploadResponse,
  UnionStatus,
  UploadSnapshot,
  ElementCategory,
  SceneTag,
  SceneNote,
  SceneElement,
  MasterElement,
  BreakdownSheet,
  NoteType,
} from "./types";

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

export async function fetchScenes(uploadId?: string): Promise<Scene[]> {
  const query = uploadId ? `?upload_id=${encodeURIComponent(uploadId)}` : "";
  const res = await fetch(`${API_BASE_URL}/api/v1/scenes${query}`);
  return parseResponse<Scene[]>(res);
}

export async function fetchDayPlans(): Promise<DayPlan[]> {
  const res = await fetch(`${API_BASE_URL}/api/v1/schedule/days`);
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
  const res = await fetch(`${API_BASE_URL}/api/v1/ingest/script`, {
    method: "POST",
    body: formData
  });
  return parseResponse<SceneUploadResponse>(res);
}

export async function requestAutoSchedule(uploadId: string): Promise<DayPlan[]> {
  const res = await fetch(`${API_BASE_URL}/api/v1/schedule/auto`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ upload_id: uploadId })
  });
  return parseResponse<DayPlan[]>(res);
}

export async function fetchRateCards(): Promise<RateCard[]> {
  const res = await fetch(`${API_BASE_URL}/api/v1/rate_cards`);
  return parseResponse<RateCard[]>(res);
}

export async function fetchLatestUpload(): Promise<UploadSnapshot | null> {
  const res = await fetch(`${API_BASE_URL}/api/v1/ingest/latest`);
  if (res.status === 404) {
    return null;
  }
  return parseResponse<UploadSnapshot | null>(res);
}

export type SceneUpdatePayload = {
  location?: string;
  cast?: string[];
  script_day?: number | null;
};

export async function updateScene(sceneId: string, payload: SceneUpdatePayload): Promise<Scene> {
  const res = await fetch(`${API_BASE_URL}/api/v1/scenes/${sceneId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  return parseResponse<Scene>(res);
}

export type BatchSceneAssignmentPayload = {
  scene_ids: string[];
  script_day?: number | null;
  location?: string;
};

export async function assignScenes(payload: BatchSceneAssignmentPayload): Promise<Scene[]> {
  const res = await fetch(`${API_BASE_URL}/api/v1/scenes/assignments/batch`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  return parseResponse<Scene[]>(res);
}

export async function deleteScene(sceneId: string): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/api/v1/scenes/${sceneId}`, {
    method: "DELETE"
  });
  if (!res.ok) {
    const message = await res.text();
    throw new Error(message || `Failed to delete scene ${sceneId}`);
  }
}

export async function fetchFlipboard(): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/api/v1/schedule/flipboard`);
  return parseResponse(res);
}

export async function fetchDayOutOfDays(uploadId?: string): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/api/v1/schedule/dood${uploadId ? `?upload_id=${encodeURIComponent(uploadId)}` : ""}`);
  return parseResponse(res);
}

// Actor Compensation APIs
export async function fetchActorCompensation(uploadId?: string): Promise<ActorCompensation[]> {
  const query = uploadId ? `?upload_id=${encodeURIComponent(uploadId)}` : "";
  const res = await fetch(`${API_BASE_URL}/api/v1/compensation/actors${query}`);
  return parseResponse(res);
}

export async function createActorCompensation(data: {
  actor_name: string;
  daily_rate: number;
  overtime_rate: number;
  union_status: UnionStatus;
  notes?: string | null;
}): Promise<ActorCompensation> {
  const res = await fetch(`${API_BASE_URL}/api/v1/compensation/actors`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return parseResponse(res);
}

export async function updateActorCompensation(
  id: number,
  data: {
    daily_rate?: number;
    overtime_rate?: number;
    union_status?: UnionStatus;
    notes?: string | null;
  }
): Promise<ActorCompensation> {
  const res = await fetch(`${API_BASE_URL}/api/v1/compensation/actors/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return parseResponse(res);
}

export async function deleteActorCompensation(id: number): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/api/v1/compensation/actors/${id}`, {
    method: "DELETE",
  });
  if (!res.ok) {
    const message = await res.text();
    throw new Error(message || `Failed to delete actor compensation ${id}`);
  }
}

// Location Compensation APIs
export async function fetchLocationCompensation(): Promise<any[]> {
  const res = await fetch(`${API_BASE_URL}/api/v1/compensation/locations`);
  return parseResponse(res);
}

export async function createLocationCompensation(data: {
  location_name: string;
  daily_fee: number;
  permits_cost: number;
  insurance_cost: number;
  notes?: string;
}): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/api/v1/compensation/locations`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return parseResponse(res);
}

export async function updateLocationCompensation(id: number, data: {
  daily_fee?: number;
  permits_cost?: number;
  insurance_cost?: number;
  notes?: string;
}): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/api/v1/compensation/locations/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return parseResponse(res);
}

export async function deleteLocationCompensation(id: number): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/api/v1/compensation/locations/${id}`, {
    method: "DELETE",
  });
  if (!res.ok) {
    const message = await res.text();
    throw new Error(message || `Failed to delete location compensation ${id}`);
  }
}

export async function syncActorCompensation(): Promise<any[]> {
  const res = await fetch(`${API_BASE_URL}/api/v1/compensation/actors/sync`, {
    method: "POST"
  });
  return parseResponse(res);
}
export async function fetchCharacterAssignments(uploadId?: string): Promise<CharacterAssignment[]> {
  const query = uploadId ? `?upload_id=${encodeURIComponent(uploadId)}` : "";
  const res = await fetch(`${API_BASE_URL}/api/v1/compensation/characters${query}`);
  const payload = await parseResponse<{ characters: CharacterAssignment[] }>(res);
  return payload.characters;
}

export async function assignCharacterToActor(data: {
  character_name: string;
  actor_id: number | null;
  upload_id?: string | null;
}): Promise<CharacterAssignment> {
  const res = await fetch(`${API_BASE_URL}/api/v1/compensation/characters/assign`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return parseResponse(res);
}

export async function syncLocationCompensation(): Promise<any[]> {
  const res = await fetch(`${API_BASE_URL}/api/v1/compensation/locations/sync`, {
    method: "POST"
  });
  return parseResponse(res);
}

export async function updateScheduleDayLocation(
  scriptDay: number,
  data: { location: string | null; upload_id?: string | null }
): Promise<DayPlan[]> {
  const res = await fetch(`${API_BASE_URL}/api/v1/schedule/days/${scriptDay}/location`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return parseResponse(res);
}

// ============================================================================
// Element Categories (Taxonomy)
// ============================================================================

export async function fetchElementCategories(): Promise<ElementCategory[]> {
  const res = await fetch(`${API_BASE_URL}/api/v1/elements/categories`);
  return parseResponse(res);
}

// ============================================================================
// Scene Tags
// ============================================================================

export async function addSceneTag(sceneId: string, tag: string): Promise<SceneTag> {
  const res = await fetch(`${API_BASE_URL}/api/v1/elements/scenes/${sceneId}/tags`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ tag }),
  });
  return parseResponse(res);
}

export async function fetchSceneTags(sceneId: string): Promise<SceneTag[]> {
  const res = await fetch(`${API_BASE_URL}/api/v1/elements/scenes/${sceneId}/tags`);
  return parseResponse(res);
}

export async function deleteSceneTag(sceneId: string, tagId: number): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/api/v1/elements/scenes/${sceneId}/tags/${tagId}`, {
    method: "DELETE",
  });
  if (!res.ok) {
    const message = await res.text();
    throw new Error(message || `Failed to delete tag ${tagId}`);
  }
}

// ============================================================================
// Scene Notes
// ============================================================================

export async function addSceneNote(
  sceneId: string,
  noteText: string,
  noteType: NoteType = "GENERAL"
): Promise<SceneNote> {
  const res = await fetch(`${API_BASE_URL}/api/v1/elements/scenes/${sceneId}/notes`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ note_text: noteText, note_type: noteType }),
  });
  return parseResponse(res);
}

export async function fetchSceneNotes(sceneId: string): Promise<SceneNote[]> {
  const res = await fetch(`${API_BASE_URL}/api/v1/elements/scenes/${sceneId}/notes`);
  return parseResponse(res);
}

export async function updateSceneNote(
  sceneId: string,
  noteId: number,
  data: { note_text?: string; note_type?: NoteType }
): Promise<SceneNote> {
  const res = await fetch(`${API_BASE_URL}/api/v1/elements/scenes/${sceneId}/notes/${noteId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return parseResponse(res);
}

export async function deleteSceneNote(sceneId: string, noteId: number): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/api/v1/elements/scenes/${sceneId}/notes/${noteId}`, {
    method: "DELETE",
  });
  if (!res.ok) {
    const message = await res.text();
    throw new Error(message || `Failed to delete note ${noteId}`);
  }
}

// ============================================================================
// Scene Elements
// ============================================================================

export async function addSceneElement(
  sceneId: string,
  data: {
    category_id: number;
    element_name: string;
    description?: string | null;
    quantity?: number;
    notes?: string | null;
    is_critical?: boolean;
  }
): Promise<SceneElement> {
  const res = await fetch(`${API_BASE_URL}/api/v1/elements/scenes/${sceneId}/elements`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return parseResponse(res);
}

export async function fetchSceneElements(sceneId: string): Promise<SceneElement[]> {
  const res = await fetch(`${API_BASE_URL}/api/v1/elements/scenes/${sceneId}/elements`);
  return parseResponse(res);
}

export async function updateSceneElement(
  sceneId: string,
  elementId: number,
  data: {
    category_id?: number;
    element_name?: string;
    description?: string | null;
    quantity?: number;
    notes?: string | null;
    is_critical?: boolean;
  }
): Promise<SceneElement> {
  const res = await fetch(`${API_BASE_URL}/api/v1/elements/scenes/${sceneId}/elements/${elementId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return parseResponse(res);
}

export async function deleteSceneElement(sceneId: string, elementId: number): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/api/v1/elements/scenes/${sceneId}/elements/${elementId}`, {
    method: "DELETE",
  });
  if (!res.ok) {
    const message = await res.text();
    throw new Error(message || `Failed to delete element ${elementId}`);
  }
}

// ============================================================================
// Master Elements List
// ============================================================================

export async function fetchMasterElements(
  uploadId: string,
  categoryId?: number
): Promise<MasterElement[]> {
  const query = categoryId ? `?category_id=${categoryId}` : "";
  const res = await fetch(`${API_BASE_URL}/api/v1/elements/uploads/${uploadId}/master-elements${query}`);
  return parseResponse(res);
}

// ============================================================================
// Breakdown Sheets
// ============================================================================

export async function fetchBreakdownSheet(sceneId: string): Promise<BreakdownSheet> {
  const res = await fetch(`${API_BASE_URL}/api/v1/breakdown/scenes/${sceneId}/breakdown`);
  return parseResponse(res);
}

export async function fetchAllBreakdownSheets(uploadId: string): Promise<BreakdownSheet[]> {
  const res = await fetch(`${API_BASE_URL}/api/v1/breakdown/uploads/${uploadId}/breakdown-sheets`);
  return parseResponse(res);
}
