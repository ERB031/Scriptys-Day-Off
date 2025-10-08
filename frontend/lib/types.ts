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
  props: string[];
  script_day: number | null;
  schedule_day_id: string | null;
};

export type DayPlan = {
  id: string;
  name: string;
  shooting_date: string | null;
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
