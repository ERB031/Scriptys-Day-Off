"use client";

import { Scene } from "../lib/types";

interface BreakdownSheetModalProps {
  scene: Scene | null;
  uploadId: string | null;
  onClose: () => void;
}

export function BreakdownSheetModal({
  scene,
  uploadId,
  onClose,
}: BreakdownSheetModalProps) {
  if (!scene) {
    return null;
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50"
      onClick={onClose}
    >
      <div
        className="max-h-[90vh] w-full max-w-4xl overflow-y-auto rounded-lg bg-white p-8 shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-4 flex items-start justify-between">
          <h2 className="text-2xl font-bold text-gray-900">
            {scene.name} - Breakdown Sheet
          </h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700"
          >
            <svg
              className="h-6 w-6"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        {/* Scene Header */}
        <div className="mb-6 border-b border-gray-200 pb-4">
          <div className="text-lg font-medium text-gray-900">
            {scene.slugline}
          </div>
          <div className="mt-2 flex gap-4 text-sm text-gray-600">
            <span>Pages: {scene.page_decimal.toFixed(2)}</span>
            <span>
              Estimated Time: {Math.floor(scene.estimated_minutes)}m
            </span>
            <span>
              Location: {scene.location} - {scene.day_night}
            </span>
          </div>
        </div>

        {/* Synopsis */}
        {scene.synopsis && (
          <div className="mb-6">
            <h3 className="mb-2 text-sm font-semibold uppercase tracking-wide text-gray-700">
              Synopsis
            </h3>
            <p className="text-gray-900">{scene.synopsis}</p>
          </div>
        )}

        {/* Cast */}
        {scene.cast && scene.cast.length > 0 && (
          <div className="mb-6">
            <h3 className="mb-2 text-sm font-semibold uppercase tracking-wide text-gray-700">
              Cast
            </h3>
            <div className="grid gap-2 md:grid-cols-2">
              {scene.cast.map((member, idx) => (
                <div
                  key={idx}
                  className="rounded border border-gray-200 bg-gray-50 px-3 py-2"
                >
                  {member}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Props */}
        {scene.props && scene.props.length > 0 && (
          <div className="mb-6">
            <h3 className="mb-2 text-sm font-semibold uppercase tracking-wide text-gray-700">
              Props
            </h3>
            <div className="grid gap-2 md:grid-cols-2">
              {scene.props.map((prop, idx) => (
                <div
                  key={idx}
                  className="rounded border border-gray-200 bg-gray-50 px-3 py-2"
                >
                  {prop}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Elements */}
        {scene.elements && scene.elements.length > 0 && (
          <div className="mb-6">
            <h3 className="mb-2 text-sm font-semibold uppercase tracking-wide text-gray-700">
              Production Elements
            </h3>
            <div className="space-y-4">
              {Object.entries(
                scene.elements.reduce(
                  (acc, el) => {
                    if (!acc[el.category_name]) {
                      acc[el.category_name] = [];
                    }
                    acc[el.category_name].push(el);
                    return acc;
                  },
                  {} as Record<string, typeof scene.elements>
                )
              ).map(([category, elements]) => (
                <div key={category}>
                  <h4 className="mb-2 text-sm font-medium text-gray-700">
                    {category}
                  </h4>
                  <div className="grid gap-2 md:grid-cols-2">
                    {elements.map((el, idx) => (
                      <div
                        key={idx}
                        className="rounded border border-gray-200 bg-gray-50 px-3 py-2"
                      >
                        <div className="font-medium">{el.element_name}</div>
                        {el.description && (
                          <div className="mt-1 text-sm text-gray-600">
                            {el.description}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Notes */}
        {scene.notes && scene.notes.length > 0 && (
          <div className="mb-6">
            <h3 className="mb-2 text-sm font-semibold uppercase tracking-wide text-gray-700">
              Notes
            </h3>
            <div className="space-y-2">
              {scene.notes.map((note, idx) => (
                <div
                  key={idx}
                  className="rounded border border-gray-200 bg-yellow-50 px-3 py-2"
                >
                  <div className="text-xs font-medium text-gray-600">
                    {note.note_type}
                  </div>
                  <div className="mt-1">{note.note_text}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Tags */}
        {scene.tags && scene.tags.length > 0 && (
          <div className="mb-6">
            <h3 className="mb-2 text-sm font-semibold uppercase tracking-wide text-gray-700">
              Tags
            </h3>
            <div className="flex flex-wrap gap-2">
              {scene.tags.map((tag, idx) => (
                <span
                  key={idx}
                  className="rounded-full bg-blue-100 px-3 py-1 text-sm text-blue-800"
                >
                  {tag.tag}
                </span>
              ))}
            </div>
          </div>
        )}

        <div className="mt-6 flex justify-end">
          <button
            onClick={onClose}
            className="rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
