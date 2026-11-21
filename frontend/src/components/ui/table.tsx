import { ArrowDown, ArrowUp, ChevronsUpDown } from 'lucide-react'
import { useState, type ReactNode } from 'react'
import { flexRender } from '@tanstack/react-table'
import { getCoreRowModel, getSortedRowModel, useLegacyTable, type LegacyColumnDef } from '@tanstack/react-table/legacy'
import { cn } from '@/lib/utils'

export type ColumnDef<T extends object> = LegacyColumnDef<T, any> // eslint-disable-line @typescript-eslint/no-explicit-any

/** Sortable data table on TanStack Table (legacy v8-style API of v9). */
export function DataTable<T extends object>({ data, columns, onRowClick, empty = 'Brak wyników.', rowClassName, getRowId, dense }:
  { data: T[]; columns: ColumnDef<T>[]; onRowClick?: (row: T) => void; empty?: ReactNode
    rowClassName?: (row: T) => string | undefined; getRowId?: (row: T) => string; dense?: boolean }) {
  const [sorting, setSorting] = useState<{ id: string; desc: boolean }[]>([])
  const table = useLegacyTable<T>({
    data, columns, state: { sorting }, onSortingChange: setSorting as never,
    getCoreRowModel: getCoreRowModel(), getSortedRowModel: getSortedRowModel(),
    getRowId: getRowId ? (r: T) => getRowId(r) : undefined,
  })
  return (
    <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
      <table className="w-full text-sm">
        <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
          {table.getHeaderGroups().map((hg) => (
            <tr key={hg.id}>
              {hg.headers.map((h) => {
                const canSort = h.column.getCanSort()
                const dir = h.column.getIsSorted()
                return (
                  <th key={h.id} scope="col" className={cn('px-3 font-medium', dense ? 'py-1.5' : 'py-2')}
                    aria-sort={dir === 'asc' ? 'ascending' : dir === 'desc' ? 'descending' : undefined}>
                    {h.isPlaceholder ? null : canSort ? (
                      <button className="inline-flex items-center gap-1 uppercase cursor-pointer hover:text-slate-800" onClick={h.column.getToggleSortingHandler()}>
                        {flexRender(h.column.columnDef.header, h.getContext())}
                        {dir === 'asc' ? <ArrowUp size={12} /> : dir === 'desc' ? <ArrowDown size={12} /> : <ChevronsUpDown size={12} className="opacity-40" />}
                      </button>
                    ) : flexRender(h.column.columnDef.header, h.getContext())}
                  </th>
                )
              })}
            </tr>
          ))}
        </thead>
        <tbody>
          {table.getRowModel().rows.length === 0 && (
            <tr><td colSpan={columns.length} className="px-3 py-8 text-center text-slate-500">{empty}</td></tr>
          )}
          {table.getRowModel().rows.map((row) => (
            <tr key={row.id}
              className={cn('border-t border-slate-100', onRowClick && 'cursor-pointer hover:bg-brand-soft/50', rowClassName?.(row.original))}
              onClick={onRowClick ? () => onRowClick(row.original) : undefined}
              onKeyDown={onRowClick ? (e) => { if (e.key === 'Enter') onRowClick(row.original) } : undefined}
              tabIndex={onRowClick ? 0 : undefined}>
              {row.getVisibleCells().map((c) => (
                <td key={c.id} className={cn('px-3 align-top', dense ? 'py-1.5' : 'py-2')}>{flexRender(c.column.columnDef.cell, c.getContext())}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
