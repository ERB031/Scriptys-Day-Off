"use client";

import { ChangeEvent, useRef, useState } from "react";

type Props = {
  onUpload: (file: File) => Promise<void>;
  disabled?: boolean;
};

export function UploadPanel({ onUpload, disabled }: Props) {
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState<"idle" | "uploading">("idle");
  const inputRef = useRef<HTMLInputElement | null>(null);

  const handleFileChange = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }
    setError(null);
    setProgress("uploading");
    try {
      await onUpload(file);
      if (inputRef.current) {
        inputRef.current.value = "";
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed.");
    } finally {
      setProgress("idle");
    }
  };

  return (
    <section className="rounded border border-dashed border-gray-300 bg-white p-4 shadow-sm">
      <header className="mb-2 flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-gray-800">Upload Script</h2>
          <p className="text-sm text-gray-600">
            Drop in your Final Draft `.fdx` to auto-create the scene breakdown. PDF support is coming soon.
          </p>
        </div>
        <button
          onClick={() => inputRef.current?.click()}
          disabled={disabled || progress === "uploading"}
          className="rounded bg-blue-600 px-3 py-1.5 text-sm font-medium text-white shadow hover:bg-blue-500 disabled:cursor-not-allowed disabled:bg-blue-300"
        >
          {progress === "uploading" ? "Uploading…" : "Upload Your Script"}
        </button>
      </header>
      <input
        ref={inputRef}
        type="file"
        accept=".fdx"
        onChange={handleFileChange}
        className="hidden"
        disabled={disabled || progress === "uploading"}
      />
      {error && <div className="rounded border border-red-400 bg-red-50 p-2 text-sm text-red-700">{error}</div>}
      <div className="text-xs text-gray-500">
        We parse sluglines, cast, and page lengths in 1/8ths automatically. You can fine tune details from the grid.
      </div>
    </section>
  );
}
