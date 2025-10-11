"use client";

import { useEffect, useState } from "react";
import { fetchActorCompensation, fetchLocationCompensation, updateActorCompensation, updateLocationCompensation, createActorCompensation, createLocationCompensation } from "../lib/compensation";
import { ActorCompensation, LocationCompensation } from "../lib/types";
import { parseApiError } from "../lib/utils";

interface CompensationViewProps {
  uploadId: string | null;
}

export default function CompensationView({ uploadId }: CompensationViewProps) {
  const [actors, setActors] = useState<ActorCompensation[]>([]);
  const [locations, setLocations] = useState<LocationCompensation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editingActor, setEditingActor] = useState<ActorCompensation | null>(null);
  const [editingLocation, setEditingLocation] = useState<LocationCompensation | null>(null);
  const [addingActor, setAddingActor] = useState(false);
  const [addingLocation, setAddingLocation] = useState(false);

  useEffect(() => {
    if (!uploadId) {
      setLoading(false);
      return;
    }

    const loadCompensation = async () => {
      setLoading(true);
      setError(null);
      try {
        const [actorData, locationData] = await Promise.all([
          fetchActorCompensation(),
          fetchLocationCompensation(),
        ]);
        setActors(actorData);
        setLocations(locationData);
      } catch (err) {
        setError(parseApiError(err, "Failed to load compensation data"));
      } finally {
        setLoading(false);
      }
    };

    loadCompensation();
  }, [uploadId]);

  const handleSaveActor = async (data: ActorCompensation) => {
    try {
      const updatedActor = await updateActorCompensation(data.id, data);
      setActors((prev) =>
        prev.map((actor) => (actor.id === updatedActor.id ? updatedActor : actor))
      );
      setEditingActor(null);
    } catch (err) {
      setError(parseApiError(err, "Failed to save actor compensation"));
    }
  };

  const handleCreateActor = async (data: Omit<ActorCompensation, 'id'>) => {
    try {
      const newActor = await createActorCompensation(data);
      setActors((prev) => [...prev, newActor]);
      setAddingActor(false);
    } catch (err) {
      setError(parseApiError(err, "Failed to create actor compensation"));
    }
  };

  const handleSaveLocation = async (data: LocationCompensation) => {
    try {
      const updatedLocation = await updateLocationCompensation(data.id, data);
      setLocations((prev) =>
        prev.map((location) => (location.id === updatedLocation.id ? updatedLocation : location))
      );
      setEditingLocation(null);
    } catch (err) {
      setError(parseApiError(err, "Failed to save location compensation"));
    }
  };

  const handleCreateLocation = async (data: Omit<LocationCompensation, 'id'>) => {
    try {
      const newLocation = await createLocationCompensation(data);
      setLocations((prev) => [...prev, newLocation]);
      setAddingLocation(false);
    } catch (err) {
      setError(parseApiError(err, "Failed to create location compensation"));
    }
  };

  if (!uploadId) {
    return (
      <div className="p-8 text-center text-gray-600">
        Upload a script to manage compensation
      </div>
    );
  }

  if (loading) {
    return <div className="p-8 text-center text-gray-600">Loading compensation data...</div>;
  }

  if (error) {
    return <div className="p-8 text-center text-red-600">Error: {error}</div>;
  }

  return (
    <div className="p-4">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">
          Actor & Location Compensation
        </h2>
        <p className="text-sm text-gray-600">
          Manage rates for cast, crew, and locations
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <div className="rounded-lg border border-gray-200 bg-white p-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Actor Rates</h3>
            <button onClick={() => setAddingActor(true)} className="rounded-md bg-blue-600 px-4 py-2 text-white">Add Actor</button>
          </div>
          <CompensationTable data={actors} type="actor" onEdit={(item) => setEditingActor(item as ActorCompensation)} />
        </div>

        <div className="rounded-lg border border-gray-200 bg-white p-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Location Fees</h3>
            <button onClick={() => setAddingLocation(true)} className="rounded-md bg-blue-600 px-4 py-2 text-white">Add Location</button>
          </div>
          <CompensationTable data={locations} type="location" onEdit={(item) => setEditingLocation(item as LocationCompensation)} />
        </div>
      </div>

      {editingActor && (
        <EditActorForm
          actor={editingActor}
          onSave={handleSaveActor}
          onCancel={() => setEditingActor(null)}
        />
      )}

      {addingActor && (
        <AddActorForm
          onSave={handleCreateActor}
          onCancel={() => setAddingActor(false)}
        />
      )}

      {editingLocation && (
        <EditLocationForm
          location={editingLocation}
          onSave={handleSaveLocation}
          onCancel={() => setEditingLocation(null)}
        />
      )}

      {addingLocation && (
        <AddLocationForm
          onSave={handleCreateLocation}
          onCancel={() => setAddingLocation(false)}
        />
      )}
    </div>
  );
}

interface CompensationTableProps {
  data: (ActorCompensation | LocationCompensation)[];
  type: "actor" | "location";
  onEdit: (item: ActorCompensation | LocationCompensation) => void;
}

function CompensationTable({ data, type, onEdit }: CompensationTableProps) {
  if (data.length === 0) {
    return <div className="text-center text-gray-500">No data available.</div>;
  }

  const isActor = type === "actor";
  const headers = isActor
    ? ["Actor Name", "Daily Rate", "Overtime Rate", "Union Status", ""]
    : ["Location Name", "Fee", ""];

  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200">
      <table className="min-w-full divide-y divide-gray-300">
        <thead className="bg-gray-50">
          <tr>
            {headers.map((header) => (
              <th key={header} className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-600">
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200 bg-white">
          {data.map((item) => (
            <tr key={item.id}>
              <td className="whitespace-nowrap px-4 py-3 font-medium text-gray-800">
                {isActor ? (item as ActorCompensation).actor_name : (item as LocationCompensation).location_name}
              </td>
              <td className="whitespace-nowrap px-4 py-3 text-gray-600">
                ${isActor ? (item as ActorCompensation).daily_rate : (item as LocationCompensation).fee}
              </td>
              {isActor && (
                <>
                  <td className="whitespace-nowrap px-4 py-3 text-gray-600">
                    ${(item as ActorCompensation).overtime_rate}
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-gray-600">
                    {(item as ActorCompensation).union_status}
                  </td>
                </>
              )}
              <td className="whitespace-nowrap px-4 py-3 text-right">
                <button onClick={() => onEdit(item)} className="text-blue-600 hover:underline">Edit</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function EditActorForm({
  actor,
  onSave,
  onCancel,
}: {
  actor: ActorCompensation;
  onSave: (data: ActorCompensation) => void;
  onCancel: () => void;
}) {
  const [formData, setFormData] = useState(actor);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave(formData);
  };

  return (
    <div className="fixed inset-0 z-10 overflow-y-auto bg-gray-500 bg-opacity-75">
      <div className="flex min-h-screen items-center justify-center">
        <div className="w-full max-w-lg rounded-lg bg-white p-6 shadow-xl">
          <h3 className="mb-4 text-lg font-semibold">Edit Actor Compensation</h3>
          <form onSubmit={handleSubmit}>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium">Actor Name</label>
                <input
                  type="text"
                  name="actor_name"
                  value={formData.actor_name}
                  onChange={handleChange}
                  className="w-full rounded-md border border-gray-300 p-2"
                />
              </div>
              <div>
                <label className="block text-sm font-medium">Daily Rate</label>
                <input
                  type="number"
                  name="daily_rate"
                  value={formData.daily_rate}
                  onChange={handleChange}
                  className="w-full rounded-md border border-gray-300 p-2"
                />
              </div>
              <div>
                <label className="block text-sm font-medium">Overtime Rate</label>
                <input
                  type="number"
                  name="overtime_rate"
                  value={formData.overtime_rate}
                  onChange={handleChange}
                  className="w-full rounded-md border border-gray-300 p-2"
                />
              </div>
              <div>
                <label className="block text-sm font-medium">Union Status</label>
                <select
                  name="union_status"
                  value={formData.union_status}
                  onChange={handleChange}
                  className="w-full rounded-md border border-gray-300 p-2"
                >
                  <option value="NON_SAG">NON_SAG</option>
                  <option value="SAG">SAG</option>
                </select>
              </div>
              <div className="col-span-2">
                <label className="block text-sm font-medium">Notes</label>
                <input
                  type="text"
                  name="notes"
                  value={formData.notes || ""}
                  onChange={handleChange}
                  className="w-full rounded-md border border-gray-300 p-2"
                />
              </div>
            </div>
            <div className="mt-4 flex justify-end gap-2">
              <button type="button" onClick={onCancel} className="rounded-md bg-gray-200 px-4 py-2">Cancel</button>
              <button type="submit" className="rounded-md bg-blue-600 px-4 py-2 text-white">Save</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

function AddActorForm({
  onSave,
  onCancel,
}: {
  onSave: (data: Omit<ActorCompensation, 'id'>) => void;
  onCancel: () => void;
}) {
  const [formData, setFormData] = useState<Omit<ActorCompensation, 'id'>>({
    actor_name: "",
    daily_rate: 0,
    overtime_rate: 0,
    union_status: "NON_SAG",
    notes: "",
    assigned_characters: [],
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave(formData);
  };

  return (
    <div className="fixed inset-0 z-10 overflow-y-auto bg-gray-500 bg-opacity-75">
      <div className="flex min-h-screen items-center justify-center">
        <div className="w-full max-w-lg rounded-lg bg-white p-6 shadow-xl">
          <h3 className="mb-4 text-lg font-semibold">Add Actor Compensation</h3>
          <form onSubmit={handleSubmit}>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium">Actor Name</label>
                <input
                  type="text"
                  name="actor_name"
                  value={formData.actor_name}
                  onChange={handleChange}
                  className="w-full rounded-md border border-gray-300 p-2"
                />
              </div>
              <div>
                <label className="block text-sm font-medium">Daily Rate</label>
                <input
                  type="number"
                  name="daily_rate"
                  value={formData.daily_rate}
                  onChange={handleChange}
                  className="w-full rounded-md border border-gray-300 p-2"
                />
              </div>
              <div>
                <label className="block text-sm font-medium">Overtime Rate</label>
                <input
                  type="number"
                  name="overtime_rate"
                  value={formData.overtime_rate}
                  onChange={handleChange}
                  className="w-full rounded-md border border-gray-300 p-2"
                />
              </div>
              <div>
                <label className="block text-sm font-medium">Union Status</label>
                <select
                  name="union_status"
                  value={formData.union_status}
                  onChange={handleChange}
                  className="w-full rounded-md border border-gray-300 p-2"
                >
                  <option value="NON_SAG">NON_SAG</option>
                  <option value="SAG">SAG</option>
                </select>
              </div>
              <div className="col-span-2">
                <label className="block text-sm font-medium">Notes</label>
                <input
                  type="text"
                  name="notes"
                  value={formData.notes || ""}
                  onChange={handleChange}
                  className="w-full rounded-md border border-gray-300 p-2"
                />
              </div>
            </div>
            <div className="mt-4 flex justify-end gap-2">
              <button type="button" onClick={onCancel} className="rounded-md bg-gray-200 px-4 py-2">Cancel</button>
              <button type="submit" className="rounded-md bg-blue-600 px-4 py-2 text-white">Save</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

function EditLocationForm({
  location,
  onSave,
  onCancel,
}: {
  location: LocationCompensation;
  onSave: (data: LocationCompensation) => void;
  onCancel: () => void;
}) {
  const [formData, setFormData] = useState(location);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave(formData);
  };

  return (
    <div className="fixed inset-0 z-10 overflow-y-auto bg-gray-500 bg-opacity-75">
      <div className="flex min-h-screen items-center justify-center">
        <div className="w-full max-w-lg rounded-lg bg-white p-6 shadow-xl">
          <h3 className="mb-4 text-lg font-semibold">Edit Location Compensation</h3>
          <form onSubmit={handleSubmit}>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium">Location Name</label>
                <input
                  type="text"
                  name="location_name"
                  value={formData.location_name}
                  onChange={handleChange}
                  className="w-full rounded-md border border-gray-300 p-2"
                />
              </div>
              <div>
                <label className="block text-sm font-medium">Fee</label>
                <input
                  type="number"
                  name="fee"
                  value={formData.fee}
                  onChange={handleChange}
                  className="w-full rounded-md border border-gray-300 p-2"
                />
              </div>
              <div className="col-span-2">
                <label className="block text-sm font-medium">Notes</label>
                <input
                  type="text"
                  name="notes"
                  value={formData.notes || ""}
                  onChange={handleChange}
                  className="w-full rounded-md border border-gray-300 p-2"
                />
              </div>
            </div>
            <div className="mt-4 flex justify-end gap-2">
              <button type="button" onClick={onCancel} className="rounded-md bg-gray-200 px-4 py-2">Cancel</button>
              <button type="submit" className="rounded-md bg-blue-600 px-4 py-2 text-white">Save</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

function AddLocationForm({
  onSave,
  onCancel,
}: {
  onSave: (data: Omit<LocationCompensation, 'id'>) => void;
  onCancel: () => void;
}) {
  const [formData, setFormData] = useState<Omit<LocationCompensation, 'id'>>({
    location_name: "",
    fee: 0,
    notes: "",
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave(formData);
  };

  return (
    <div className="fixed inset-0 z-10 overflow-y-auto bg-gray-500 bg-opacity-75">
      <div className="flex min-h-screen items-center justify-center">
        <div className="w-full max-w-lg rounded-lg bg-white p-6 shadow-xl">
          <h3 className="mb-4 text-lg font-semibold">Add Location Compensation</h3>
          <form onSubmit={handleSubmit}>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium">Location Name</label>
                <input
                  type="text"
                  name="location_name"
                  value={formData.location_name}
                  onChange={handleChange}
                  className="w-full rounded-md border border-gray-300 p-2"
                />
              </div>
              <div>
                <label className="block text-sm font-medium">Fee</label>
                <input
                  type="number"
                  name="fee"
                  value={formData.fee}
                  onChange={handleChange}
                  className="w-full rounded-md border border-gray-300 p-2"
                />
              </div>
              <div className="col-span-2">
                <label className="block text-sm font-medium">Notes</label>
                <input
                  type="text"
                  name="notes"
                  value={formData.notes || ""}
                  onChange={handleChange}
                  className="w-full rounded-md border border-gray-300 p-2"
                />
              </div>
            </div>
            <div className="mt-4 flex justify-end gap-2">
              <button type="button" onClick={onCancel} className="rounded-md bg-gray-200 px-4 py-2">Cancel</button>
              <button type="submit" className="rounded-md bg-blue-600 px-4 py-2 text-white">Save</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}