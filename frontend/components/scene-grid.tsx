"use client";

import { useMemo } from "react";
import { ColumnDef, flexRender, getCoreRowModel, useReactTable } from "@tanstack/react-table";
import { Scene } from "../lib/types";
import clsx from "clsx";

type Props = {
  scenes: Scene[];
  onScenesChange?: (next: Scene[]) => void;
};

export function SceneGrid({ scenes }: Props) {
  const columns = useMemo<ColumnDef<Scene>[]>(
    () => [
      {
        header: "#",
        accessorKey: "sequence_index",
        cell: ({ getValue }) => getValue<number>() + 1,
        size: 50
      },
      {
        header: "Scene",
        accessorKey: "name"
      },
      {
        header: "Slugline",
        accessorKey: "slugline"
      },
      {
        header: "Pages (1/8ths)",
        accessorKey: "page_eighths",
        cell: ({ getValue }) => `${getValue<number>()} / 8`
      },
      {
        header: "Location",
        accessorKey: "location"
      },
      {
        header: "Cast",
        accessorKey: "cast",
        cell: ({ getValue }) => {
          const cast = getValue<string[]>();
          return cast.length ? cast.join(", ") : "—";
        }
      },
      {
        header: "Props",
        accessorKey: "props",
        cell: ({ getValue }) => {
          const props = getValue<string[]>();
          return props.length ? props.join(", ") : "—";
        }
      },
      {
        header: "Est. Cost",
        accessorKey: "estimated_cost",
        cell: ({ getValue }) => `$${getValue<number>().toFixed(2)}`
      }
    ],
    []
  );

  const table = useReactTable({
    data: scenes,
    columns,
    getCoreRowModel: getCoreRowModel()
  });

  return (
    <div className="overflow-hidden rounded border border-gray-200 bg-white shadow-sm">
      <div className="border-b border-gray-200 bg-gray-50 px-4 py-2 text-sm font-medium uppercase tracking-wide text-gray-600">
        Scene Breakdown
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            {table.getHeaderGroups().map(headerGroup => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map(header => (
                  <th
                    key={header.id}
                    scope="col"
                    className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-gray-600"
                  >
                    {header.isPlaceholder
                      ? null
                      : flexRender(header.column.columnDef.header, header.getContext())}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody className="divide-y divide-gray-200 bg-white">
            {table.getRowModel().rows.map(row => (
              <tr key={row.id} className="hover:bg-gray-50">
                {row.getVisibleCells().map(cell => (
                  <td
                    key={cell.id}
                    className={clsx(
                      "whitespace-nowrap px-3 py-2 text-sm text-gray-700",
                      cell.column.id === "estimated_cost" && "text-right tabular-nums"
                    )}
                  >
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
