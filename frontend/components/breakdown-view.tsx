"use client";

import { useState, useEffect } from "react";
import { Scene, SceneElement, ElementCategory } from "../lib/types";
import { fetchScenes, addSceneElement, fetchElementCategories } from "../lib/api";

interface BreakdownViewProps {
  uploadId: string;
}

export function BreakdownView({ uploadId }: BreakdownViewProps) {
  const [scenes, setScenes] = useState<Scene[]>([]);
  const [loading, setLoading] = useState(true);
  const [addingElement, setAddingElement] = useState<Scene | null>(null);
  const [categories, setCategories] = useState<ElementCategory[]>([]);

  useEffect(() => {
    const loadData = async () => {
      try {
        const [scenesData, categoriesData] = await Promise.all([
          fetchScenes(uploadId),
          fetchElementCategories(),
        ]);
        setScenes(scenesData);
        setCategories(categoriesData);
      } catch (err) {
        console.error("Failed to load data:", err);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [uploadId]);

  const handleCreateElement = async (data: Omit<SceneElement, 'id' | 'created_at' | 'updated_at'>) => {
    try {
      const newElement = await addSceneElement(data.scene_id, data);
      setScenes((prev) =>
        prev.map((scene) =>
          scene.id === newElement.scene_id
            ? { ...scene, elements: [...(scene.elements || []), newElement] }
            : scene
        )
      );
      setAddingElement(null);
    } catch (err) {
      console.error("Failed to create element:", err);
    }
  };

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center p-8">
        <div className="text-gray-600">Loading breakdown sheets...</div>
      </div>
    );
  }

  if (scenes.length === 0) {
    return (
      <div className="flex h-full items-center justify-center p-8">
        <div className="text-gray-600">No scenes available</div>
      </div>
    );
  }

  return (
    <div className="h-full overflow-auto bg-white p-4">
      <table className="min-w-full divide-y divide-gray-300 border border-gray-200">
        <thead className="bg-gray-100">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-600">Scene</th>
            <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-600">Slugline</th>
            <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-600">Pages</th>
            <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-600">Time</th>
            <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-600">Cast</th>
            <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-600">Elements</th>
            <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-600"></th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200">
          {scenes.map((scene) => (
            <tr key={scene.id}>
              <td className="whitespace-nowrap px-4 py-3 text-sm font-medium text-gray-800">{scene.name}</td>
              <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-600">{scene.slugline}</td>
              <td className="whitespace-nowrapusp px-4 py-3 text-sm text-gray-600">{scene.page_decimal.toFixed(2)}</td>
              <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-600">{Math.floor(scene.estimated_minutes)}m</td>
              <td className="px-4 py-3 text-sm text-gray-600">
                <div className="flex flex-wrap gap-1">
                  {scene.cast.map((member, idx) => (
                    <ElementPill key={idx} element={{ element_name: member, category_color: "#D1D5DB" }} />
                  ))}
                </div>
              </td>
              <td className="px-4 py-3 text-sm text-gray-600">
                <div className="flex flex-wrap gap-1">
                  {scene.elements?.map((element, idx) => (
                    <ElementPill key={idx} element={element} />
                  ))}
                </div>
              </td>
              <td className="whitespace-nowrap px-4 py-3 text-right">
                <button onClick={() => setAddingElement(scene)} className="text-blue-600 hover:underline">Add Element</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {addingElement && (
        <AddElementForm
          scene={addingElement}
          categories={categories}
          onSave={handleCreateElement}
          onCancel={() => setAddingElement(null)}
        />
      )}
    </div>
  );
}

function ElementPill({ element }: { element: { element_name: string, category_color: string } }) {
  return (
    <span
      className="rounded-full px-2 py-1 text-xs font-medium"
      style={{ backgroundColor: element.category_color, color: "#111827" }}
    >
      {element.element_name}
    </span>
  );
}

function AddElementForm({
  scene,
  categories,
  onSave,
  onCancel,
}: {
  scene: Scene;
  categories: ElementCategory[];
  onSave: (data: Omit<SceneElement, 'id' | 'created_at' | 'updated_at'>) => void;
  onCancel: () => void;
}) {
  const [formData, setFormData] = useState<Omit<SceneElement, 'id' | 'created_at' | 'updated_at'>>({
    scene_id: scene.id,
    category_id: categories[0]?.id || 1,
    category_name: categories[0]?.category_name || "",
    category_color: categories[0]?.color || "#D1D5DB",
    element_name: "",
    description: "",
    quantity: 1,
    notes: "",
    is_critical: false,
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;

    if (name === "category_id") {
      const categoryId = parseInt(value);
      const selectedCategory = categories.find((cat) => cat.id === categoryId);
      setFormData((prev) => ({
        ...prev,
        category_id: categoryId,
        category_name: selectedCategory?.category_name || "",
        category_color: selectedCategory?.color || "#D1D5DB",
      }));
    } else {
      const isCheckbox = type === 'checkbox';
      const isNumber = type === 'number';
      setFormData((prev) => ({ ...prev, [name]: isCheckbox ? (e.target as HTMLInputElement).checked : isNumber ? parseInt(value) : value }));
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave(formData);
  };

  return (
    <div className="fixed inset-0 z-10 overflow-y-auto bg-gray-500 bg-opacity-75">
      <div className="flex min-h-screen items-center justify-center">
        <div className="w-full max-w-lg rounded-lg bg-white p-6 shadow-xl">
          <h3 className="mb-4 text-lg font-semibold">Add Element to {scene.name}</h3>
          <form onSubmit={handleSubmit}>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium">Element Name</label>
                <input
                  type="text"
                  name="element_name"
                  value={formData.element_name}
                  onChange={handleChange}
                  className="w-full rounded-md border border-gray-300 p-2"
                />
              </div>
              <div>
                <label className="block text-sm font-medium">Category</label>
                <select
                  name="category_id"
                  value={formData.category_id}
                  onChange={handleChange}
                  className="w-full rounded-md border border-gray-300 p-2"
                >
                  {categories.map((cat) => (
                    <option key={cat.id} value={cat.id}>
                      {cat.category_name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium">Quantity</label>
                <input
                  type="number"
                  name="quantity"
                  value={formData.quantity}
                  onChange={handleChange}
                  className="w-full rounded-md border border-gray-300 p-2"
                />
              </div>
              <div className="col-span-2">
                <label className="block text-sm font-medium">Description</label>
                <input
                  type="text"
                  name="description"
                  value={formData.description || ""}
                  onChange={handleChange}
                  className="w-full rounded-md border border-gray-300 p-2"
                />
              </div>
              <div className="col-span-2">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    name="is_critical"
                    checked={formData.is_critical}
                    onChange={handleChange}
                    className="rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50"
                  />
                  <span className="ml-2">Is Critical</span>
                </label>
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