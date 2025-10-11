"use client";

import { useEffect, useState } from "react";
import { fetchDoodReport } from "../lib/dood";
import { DayOutOfDays } from "../lib/types";
import { parseApiError } from "../lib/utils";

interface DayOutOfDaysViewProps {
  uploadId: string | null;
  version: number;
}

const STATUS_STYLES: Record<string, { symbol: string; className: string; description: string }> = {
  S: { symbol: "S", className: "bg-green-500 text-white", description: "Start" },
  W: { symbol: "W", className: "bg-blue-500 text-white", description: "Work" },
  H: { symbol: "H", className: "bg-yellow-400 text-gray-800", description: "Hold" },
  F: { symbol: "F", className: "bg-red-500 text-white", description: "Finish" },
  I: { symbol: "I", className: "bg-gray-200 text-gray-500", description: "Idle" },
};

export function DayOutOfDaysView({ uploadId, version }: DayOutOfDaysViewProps) {
  const [dood, setDood] = useState<DayOutOfDays | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!uploadId) {
      setLoading(false);
      return;
    }

    const loadDood = async () => {
      setLoading(true);
      setError(null);
      try {
        const report = await fetchDoodReport(uploadId);
        setDood(report);
      } catch (err) {
        setError(parseApiError(err, "Failed to load Day Out of Days report"));
      } finally {
        setLoading(false);
      }
    };

    loadDood();
  }, [uploadId, version]);

  if (!uploadId) {
    return (
      <div className="p-8 text-center text-gray-600">
        Upload a script to view Day Out of Days report
      </div>
    );
  }

  if (loading) {
    return <div className="p-8 text-center text-gray-600">Loading DOOD report...</div>;
  }

  if (error) {
    return <div className="p-8 text-center text-red-600">Error: {error}</div>;
  }

  if (!dood || dood.cast_members.length === 0) {
    return (
      <div className="p-8 text-center text-gray-600">
        No cast members found to generate a DOOD report.
      </div>
    );
  }

  return (
    <div className="p-4">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Day Out of Days</h2>
        <p className="text-sm text-gray-600">
          Cast availability and scheduling report (v{version})
        </p>
      </div>

      <div className="overflow-x-auto rounded-lg border border-gray-200">
        <table className="min-w-full divide-y divide-gray-300">
          <thead className="bg-gray-100">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-600">
                Cast Member
              </th>
              {dood.shooting_days.map((day) => (
                <th key={day} className="px-4 py-3 text-center text-xs font-semibold uppercase tracking-wider text-gray-600">
                  Day {day}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 bg-white">
            {dood.cast_members.map((member) => (
              <tr key={member.cast_member_name}>
                <td className="whitespace-nowrap px-4 py-3 font-medium text-gray-800">
                  {member.cast_member_name}
                </td>
                {dood.shooting_days.map((day) => {
                  const status = member.days[day] || "I";
                  const style = STATUS_STYLES[status] || STATUS_STYLES.I;
                  return (
                    <td key={day} className={`text-center font-mono text-sm ${style.className}`}>
                      {style.symbol}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="mt-6 flex flex-wrap items-center gap-4 rounded-lg bg-gray-50 p-4">
        <h3 className="text-sm font-semibold text-gray-700">Legend:</h3>
        {Object.values(STATUS_STYLES).map((style) => (
          <div key={style.description} className="flex items-center gap-2">
            <div className={`h-5 w-5 text-center text-sm font-mono ${style.className}`}>
              {style.symbol}
            </div>
            <span className="text-xs text-gray-600">{style.description}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
