/**
 * Preline UI Data Table Component
 * Styled in Pure Smooth Z-Black (#0e0e11) with crisp zinc-800 separators.
 */

import React, { useState, useMemo } from 'react';
import { 
  Search, 
  ChevronUp, 
  ChevronDown, 
  ChevronsUpDown, 
  ChevronLeft, 
  ChevronRight,
  Download,
  AlertCircle
} from 'lucide-react';
import { ColumnProfile } from '@/services/data-intelligence.service';

interface PrelineDataGridProps {
  data: Record<string, any>[];
  columns: ColumnProfile[];
  totalRows: number;
  onExportCsv?: () => void;
  filterQuery?: string | null;
}

export const PrelineDataGrid: React.FC<PrelineDataGridProps> = ({
  data,
  columns,
  totalRows,
  onExportCsv,
  filterQuery,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [sortColumn, setSortColumn] = useState<string | null>(null);
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  const handleSort = (colName: string) => {
    if (sortColumn === colName) {
      if (sortDirection === 'asc') setSortDirection('desc');
      else {
        setSortColumn(null);
        setSortDirection('asc');
      }
    } else {
      setSortColumn(colName);
      setSortDirection('asc');
    }
  };

  const processedData = useMemo(() => {
    let list = [...data];

    // Optional country/region filter passed down from map selection
    if (filterQuery && filterQuery.trim()) {
      const fq = filterQuery.toLowerCase();
      list = list.filter((row) =>
        Object.values(row).some(
          (val) => val !== null && val !== undefined && String(val).toLowerCase().includes(fq)
        )
      );
    }

    if (searchTerm.trim()) {
      const q = searchTerm.toLowerCase();
      list = list.filter((row) =>
        Object.values(row).some(
          (val) => val !== null && val !== undefined && String(val).toLowerCase().includes(q)
        )
      );
    }

    if (sortColumn) {
      list.sort((a, b) => {
        const valA = a[sortColumn];
        const valB = b[sortColumn];
        if (valA === null || valA === undefined) return 1;
        if (valB === null || valB === undefined) return -1;
        if (typeof valA === 'number' && typeof valB === 'number') {
          return sortDirection === 'asc' ? valA - valB : valB - valA;
        }
        return sortDirection === 'asc'
          ? String(valA).localeCompare(String(valB))
          : String(valB).localeCompare(String(valA));
      });
    }

    return list;
  }, [data, searchTerm, filterQuery, sortColumn, sortDirection]);

  const totalPages = Math.ceil(processedData.length / pageSize) || 1;
  const paginatedData = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return processedData.slice(start, start + pageSize);
  }, [processedData, currentPage, pageSize]);

  return (
    <div className="bg-[#0e0e11] border border-[#27272a] rounded-xl overflow-hidden shadow-xs flex flex-col transition-colors">
      {/* Header Toolbar */}
      <div className="p-4 border-b border-[#27272a] flex flex-wrap items-center justify-between gap-3 bg-[#0e0e11]">
        <div className="flex items-center gap-2 flex-1 max-w-sm">
          <div className="relative w-full">
            <Search className="w-4 h-4 text-zinc-500 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search records..."
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setCurrentPage(1);
              }}
              className="w-full bg-[#141418] border border-[#27272a] rounded-lg pl-9 pr-3 py-1.5 text-xs text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-blue-500 transition-all"
            />
          </div>
          {searchTerm && (
            <button
              onClick={() => setSearchTerm('')}
              className="text-xs text-zinc-400 hover:text-zinc-100"
            >
              Clear
            </button>
          )}
        </div>

        <div className="flex items-center gap-3">
          <select
            value={pageSize}
            onChange={(e) => {
              setPageSize(Number(e.target.value));
              setCurrentPage(1);
            }}
            className="text-xs bg-[#141418] border border-[#27272a] rounded-lg px-2.5 py-1.5 text-zinc-300 focus:outline-none focus:border-blue-500"
          >
            <option value={10}>10 per page</option>
            <option value={20}>20 per page</option>
            <option value={50}>50 per page</option>
          </select>

          {onExportCsv && (
            <button
              onClick={onExportCsv}
              className="inline-flex items-center gap-1.5 text-xs font-medium bg-[#141418] hover:bg-[#1b1b22] border border-[#27272a] px-3 py-1.5 rounded-lg text-zinc-300 transition-colors"
            >
              <Download className="w-3.5 h-3.5 text-zinc-400" />
              <span>Export CSV</span>
            </button>
          )}
        </div>
      </div>

      {/* Table Container */}
      <div className="overflow-x-auto flex-1">
        <table className="min-w-full divide-y divide-[#27272a] text-left text-xs">
          <thead className="bg-[#141418] text-zinc-400 font-semibold select-none">
            <tr>
              <th className="py-3 px-4 w-12 text-center text-zinc-500 font-mono">#</th>
              {columns.map((col) => {
                const isSorted = sortColumn === col.name;
                return (
                  <th
                    key={col.name}
                    onClick={() => handleSort(col.name)}
                    className="py-3 px-4 cursor-pointer hover:bg-[#1b1b22] transition-colors whitespace-nowrap"
                  >
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-zinc-200">{col.name}</span>
                      <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-[#22222a] text-zinc-400 border border-[#27272a]">
                        {col.type.slice(0, 3).toUpperCase()}
                      </span>
                      {isSorted ? (
                        sortDirection === 'asc' ? (
                          <ChevronUp className="w-3.5 h-3.5 text-blue-400 ml-auto" />
                        ) : (
                          <ChevronDown className="w-3.5 h-3.5 text-blue-400 ml-auto" />
                        )
                      ) : (
                        <ChevronsUpDown className="w-3 h-3 text-zinc-600 opacity-60 ml-auto hover:opacity-100" />
                      )}
                    </div>
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody className="divide-y divide-[#27272a]/60 bg-[#0e0e11]">
            {paginatedData.length === 0 ? (
              <tr>
                <td colSpan={columns.length + 1} className="py-12 text-center text-zinc-500">
                  No matching records found.
                </td>
              </tr>
            ) : (
              paginatedData.map((row, idx) => {
                const rowNum = (currentPage - 1) * pageSize + idx + 1;
                return (
                  <tr key={idx} className="hover:bg-[#141418] transition-colors">
                    <td className="py-3 px-4 text-center text-zinc-500 font-mono text-[11px]">
                      {rowNum}
                    </td>
                    {columns.map((col) => {
                      const val = row[col.name];
                      const isNull = val === null || val === undefined || val === '';

                      return (
                        <td key={col.name} className="py-3 px-4 whitespace-nowrap text-zinc-300">
                          {isNull ? (
                            <span className="inline-flex items-center gap-1 text-[11px] text-amber-400 font-sans italic bg-amber-500/10 px-1.5 py-0.5 rounded border border-amber-500/20">
                              <AlertCircle className="w-2.5 h-2.5" />
                              null
                            </span>
                          ) : typeof val === 'number' ? (
                            <span className="font-mono text-zinc-100 font-medium">
                              {val.toLocaleString()}
                            </span>
                          ) : (
                            <span>{String(val)}</span>
                          )}
                        </td>
                      );
                    })}
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      <div className="p-3.5 border-t border-[#27272a] bg-[#0e0e11] flex items-center justify-between text-xs text-zinc-400">
        <div>
          Showing <span className="font-semibold text-zinc-200">{paginatedData.length}</span> of{' '}
          <span className="font-semibold text-zinc-200">{processedData.length}</span> entries
        </div>

        <div className="flex items-center gap-1">
          <button
            onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
            disabled={currentPage === 1}
            className="p-1.5 rounded-lg border border-[#27272a] bg-[#141418] hover:bg-[#1b1b22] disabled:opacity-30 disabled:cursor-not-allowed text-zinc-300"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>

          <span className="px-3 font-medium text-zinc-200">
            Page {currentPage} of {totalPages}
          </span>

          <button
            onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
            disabled={currentPage >= totalPages}
            className="p-1.5 rounded-lg border border-[#27272a] bg-[#141418] hover:bg-[#1b1b22] disabled:opacity-30 disabled:cursor-not-allowed text-zinc-300"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
