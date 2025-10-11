import { DayOutOfDays } from "./types";
import { API_BASE_URL } from "./api";

export async function fetchDoodReport(uploadId: string): Promise<DayOutOfDays> {
  const res = await fetch(`${API_BASE_URL}/api/v1/dood/uploads/${uploadId}/dood`);
  if (!res.ok) {
    throw new Error("Failed to fetch DOOD report");
  }
  return res.json();
}
