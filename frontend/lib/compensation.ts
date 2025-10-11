import { ActorCompensation, LocationCompensation } from "./types";
import { API_BASE_URL } from "./api";

export async function fetchActorCompensation(): Promise<ActorCompensation[]> {
  const res = await fetch(`${API_BASE_URL}/api/v1/compensation/actors`);
  if (!res.ok) {
    throw new Error("Failed to fetch actor compensation");
  }
  return res.json();
}

export async function fetchLocationCompensation(): Promise<LocationCompensation[]> {
  const res = await fetch(`${API_BASE_URL}/api/v1/compensation/locations`);
  if (!res.ok) {
    throw new Error("Failed to fetch location compensation");
  }
  return res.json();
}

export async function updateActorCompensation(actorId: number, data: ActorCompensation): Promise<ActorCompensation> {
  const res = await fetch(`${API_BASE_URL}/api/v1/compensation/actors/${actorId}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    throw new Error("Failed to update actor compensation");
  }
  return res.json();
}

export async function updateLocationCompensation(locationId: number, data: LocationCompensation): Promise<LocationCompensation> {
  const res = await fetch(`${API_BASE_URL}/api/v1/compensation/locations/${locationId}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    throw new Error("Failed to update location compensation");
  }
  return res.json();
}

export async function createActorCompensation(data: Omit<ActorCompensation, 'id'>): Promise<ActorCompensation> {
  const res = await fetch(`${API_BASE_URL}/api/v1/compensation/actors`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    throw new Error("Failed to create actor compensation");
  }
  return res.json();
}

export async function createLocationCompensation(data: Omit<LocationCompensation, 'id'>): Promise<LocationCompensation> {
  const res = await fetch(`${API_BASE_URL}/api/v1/compensation/locations`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    throw new Error("Failed to create location compensation");
  }
  return res.json();
}
