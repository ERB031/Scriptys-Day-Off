export type UnionStatus = "SAG" | "NON_SAG";

export type SceneCastAssignment = {
  character_name: string;
  actor_id: number | null;
  actor_name: string | null;
  union_status: UnionStatus | null;
};

export type Scene = {
  id: string;
  name: string;
  sequence_index: number;
  slugline: string;
  page_eighths: number;
  page_decimal: number;
  estimated_minutes: number;
  location: string;
  day_night: "DAY" | "NIGHT" | "INT" | "EXT" | "INT/EXT" | "OTHER";
  estimated_cost: number;
  cast: string[];
  cast_details: SceneCastAssignment[];
  props: string[];
  script_day: number | null;
  schedule_day_id: string | null;
  synopsis?: string | null;
  tags?: SceneTag[];
  notes?: SceneNote[];
  elements?: SceneElement[];
};

export type DayPlan = {
  id: string;
  name: string;
  shooting_date: string | null;
  shooting_location: string | null;
  total_cost: number;
  total_minutes: number;
  total_pages_decimal: number;
  location_summary: string[];
  cast_summary: string[];
  scenes: Scene[];
};

export type SceneUploadResponse = {
  upload_id: string;
  scenes: Scene[];
};

export type UploadSnapshot = {
  upload_id: string;
  original_filename: string;
  total_scenes: number;
  total_pages_decimal: number;
};

export type RateCard = {
  id: number;
  category: string;
  item_name: string;
  unit: string;
  base_rate: number;
  overtime_rate: number;
  is_default: boolean;
};

export type ActorCompensation = {
  id: number;
  actor_name: string;
  daily_rate: number;
  overtime_rate: number;
  union_status: UnionStatus;
  notes?: string | null;
  assigned_characters: string[];
};

export type CharacterAssignment = {
  id: number | null;
  upload_id: string;
  character_name: string;
  actor_id: number | null;
  actor_name: string | null;
  union_status: UnionStatus | null;
  scene_count: number;
  day_count: number;
  total_cost: number;
  created_at: string | null;
  updated_at: string | null;
};

export type ElementCategory = {
  id: number;
  category_name: string;
  display_order: number;
  description: string | null;
  color: string;
};

export type SceneTag = {
  id: number;
  scene_id: string;
  tag: string;
  created_at: string;
};

export type NoteType = "GENERAL" | "CAMERA" | "LIGHTING" | "PRODUCTION" | "SOUND" | "STUNTS" | "VFX" | "OTHER";

export type SceneNote = {
  id: number;
  scene_id: string;
  note_text: string;
  note_type: NoteType;
  created_at: string;
  updated_at: string;
};

export type SceneElement = {
  id: number;
  scene_id: string;
  category_id: number;
  category_name: string;
  category_color: string;
  element_name: string;
  description: string | null;
  quantity: number;
  notes: string | null;
  is_critical: boolean;
  created_at: string;
  updated_at: string;
};

export type MasterElement = {
  id: number;
  upload_id: string;
  category_id: number;
  category_name: string;
  element_name: string;
  description: string | null;
  total_scenes: number;
  notes: string | null;
  created_at: string;
  updated_at: string;
};

export type BreakdownSheet = {
  scene_id: string;
  scene_name: string;
  scene_number: string;
  slugline: string;
  int_ext: string;
  day_night: string;
  location: string;
  script_day: number | null;
  page_count: number;
  estimated_minutes: number;
  description: string;
  cast_members: SceneElement[];
  extras: SceneElement[];
  props: SceneElement[];
  set_dressing: SceneElement[];
  wardrobe: SceneElement[];
  makeup_hair: SceneElement[];
  vehicles_animals: SceneElement[];
  sound_fx: SceneElement[];
  special_effects: SceneElement[];
  stunts: SceneElement[];
  general_notes: string[];
  camera_notes: string[];
  lighting_notes: string[];
  production_notes: string[];
  tags: string[];
};

export type DayOutOfDays = {
  shooting_days: number[];
  cast_members: CastMemberDays[];
};

export type CastMemberDays = {
  cast_member_name: string;
  days: Record<number, string>;
};

export type LocationCompensation = {
  id: number;
  location_name: string;
  fee: number;
  notes: string | null;
};
