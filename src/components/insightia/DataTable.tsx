/**
 * High-Craft Enterprise Data Grid for Insightia.
 * High-performance virtualized table with search, sorting, pagination,
 * and inline missing value / outlier highlighting.
 */

import React, { useState, useMemo } from 'react';
import { 
  ChevronDown, 
  ChevronUp, 
  ChevronsUpDown, 
  Search, 
  ChevronLeft, 
  ChevronRight,
  Filter,
  Eye,
  AlertCircle
} from 'lucide-react';
import { ColumnProfile } from '@/services/data-intelligence.service';

interface DataTableProps {
  data: Record<string, any>[];
  columns: ColumnProfile[];
  totalRows: number;
}

export const DataTable: React.FC<DataTableProps> = ({ data, columns, totalRows }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [sortColumn, setSortColumn] = useState<string | null>(null);
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(15);
  const [visibleColumns, setVisibleColumns] = useState<Set<string>>(
    new Set(columns.map(c => c.name))
  );

  // Column definitions lookup
  const columnMap = useMemo(() => {
    const map = new Map<string, ColumnProfile>();
    columns.forEach(c => map.set(c.name, c));
    return map;
  }, [columns]);

  // Handle Sort
  const handleSort = (colName: string) => {
    if (sortColumn === colName) {
      if (sortDirection === 'asc') {
        setSortDirection('desc');
      } else {
        setSortColumn(null);
        setSortDirection('asc');
      }
    } else {
      setSortColumn(colName);
      setSortDirection('asc');
    }
  };

  // Filter & Sort Data
  const processedData = useMemo(() => {
    let result = [...data];

    // Global Search
    if (searchTerm.trim()) {
      const lower = searchTerm.toLowerCase();
      result = result.filter(row => 
        Object.values(row).some(val => 
          val !== null && val !== undefined && String(val).toLowerCase().includes(lower)
        )
      );
    }

    // Sort
    if (sortColumn) {
      result.sort((a, b) => {
        const valA = a[sortColumn];
        const valB = b[sortColumn];

        if (valA === null || valA === undefined) return 1;
        if (valB === null || valB === undefined) return -1;

        if (typeof valA === 'number' && typeof valB === 'number') {
          return sortDirection === 'asc' ? valA - valB : valB - valA;
        }

        const strA = String(valA);
        const strB = String(valB);
        return sortDirection === 'asc' 
          ? strA.localeCompare(strB) 
          : strB.localeCompare(strA);
      });
    }

    return result;
  }, [data, searchTerm, sortColumn, sortDirection]);

  // Pagination
  const totalPages = Math.ceil(processedData.length / pageSize) || 1;
  const paginatedData = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return processedData.slice(start, start + pageSize);
  }, [processedData, currentPage, pageSize]);

  const activeCols = columns.filter(c => visibleColumns.has(c.name));

  return (
    <div className="flex flex-col h-full bg-zinc-900 border border-zinc-800 rounded-lg overflow-hidden shadow-sm">
      {/* Table Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-3 border-b border-zinc-800 bg-zinc-900/80">
        <div className="flex items-center gap-2 flex-1 max-w-sm">
          <div className="relative w-full">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
            <input
              type="text"
              placeholder="Search across all columns..."
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setCurrentPage(1);
              }}
              className="w-full pl-9 pr-3 py-1.5 text-xs bg-zinc-950 border border-zinc-800 rounded-md text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-zinc-700 focus:ring-1 focus:ring-indigo-500/20"
            />
          </div>
          {searchTerm && (
            <button 
              onClick={() => setSearchTerm('')}
              className="text-xs text-zinc-400 hover:text-zinc-200 px-2 py-1"
            >
              Clear
            </button>
          )}
        </div>

        <div className="flex items-center gap-3 text-xs text-zinc-400">
          <span>Showing {paginatedData.length} of {processedData.length} records</span>
          <select
            value={pageSize}
            onChange={(e) => {
              setPageSize(Number(e.target.value));
              setCurrentPage(1);
            }}
            className="bg-zinc-950 border border-zinc-800 text-zinc-300 rounded px-2 py-1 focus:outline-none"
          >
            <option value={10}>10 rows</option>
            <option value={15}>15 rows</option>
            <option value={25}>25 rows</option>
            <option value={50}>50 rows</option>
          </select>
        </div>
      </div>

      {/* Grid Container */}
      <div className="flex-1 overflow-auto">
        <table className="w-full text-left text-xs border-collapse">
          <thead className="sticky top-0 z-10 bg-zinc-950/95 backdrop-blur-sm border-b border-zinc-800 text-zinc-300 font-medium">
            <tr>
              <th className="py-2.5 px-3 w-12 text-center text-zinc-500 font-mono">#</th>
              {activeCols.map((col) => {
                const isSorted = sortColumn === col.name;
                return (
                  <th
                    key={col.name}
                    onClick={() => handleSort(col.name)}
                    className="py-2.5 px-3 cursor-pointer hover:bg-zinc-800/50 transition-colors select-none whitespace-nowrap"
                  >
                    <div className="flex items-center gap-1.5">
                      <span className="font-semibold text-zinc-200">{col.name}</span>
                      <span className={`text-[10px] px-1 py-0.2 rounded font-mono font-normal ${
                        col.type === 'numeric' ? 'bg-indigo-950/80 text-indigo-300 border border-indigo-800/40' :
                        col.type === 'datetime' ? 'bg-cyan-950/80 text-cyan-300 border border-cyan-800/40' :
                        col.type === 'categorical' ? 'bg-emerald-950/80 text-emerald-300 border border-emerald-800/40' :
                        'bg-zinc-800 text-zinc-400'
                      }`}>
                        {col.type.slice(0, 3).toUpperCase()}
                      </span>
                      {col.missing_count > 0 && (
                        <span 
                          title={`${col.missing_count} missing values (${col.missing_pct}%)`}
                          className="w-1.5 h-1.5 rounded-full bg-amber-500"
                        />
                      )}
                      <span className="ml-auto text-zinc-500">
                        {isSorted ? (
                          sortDirection === 'asc' ? <ChevronUp className="w-3.5 h-3.5 text-indigo-400" /> : <ChevronDown className="w-3.5 h-3.5 text-indigo-400" />
                        ) : (
                          <ChevronsUpDown className="w-3 h-3 opacity-30 hover:opacity-100" />
                        )}
                      </span>
                    </div>
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-800/60 font-mono">
            {paginatedData.length === 0 ? (
              <tr>
                <td colSpan={activeCols.length + 1} className="py-12 text-center text-zinc-500">
                  No records match your query filter.
                </td>
              </tr>
            ) : (
              paginatedData.map((row, rowIdx) => {
                const actualIndex = (currentPage - 1) * pageSize + rowIdx + 1;
                return (
                  <tr 
                    key={rowIdx}
                    className="hover:bg-zinc-800/40 transition-colors group"
                  >
                    <td className="py-2 px-3 text-center text-zinc-500 text-[11px] select-none">
                      {actualIndex}
                    </td>
                    {activeCols.map((col) => {
                      const val = row[col.name];
                      const isNull = val === null || val === undefined || val === '';
                      
                      // Check if value is outlier
                      let isOutlier = false;
                      if (!isNull && col.type === 'numeric' && col.stats?.lower_bound !== undefined && col.stats?.upper_bound !== undefined) {
                        const numVal = Number(val);
                        if (!isNaN(numVal) && (numVal < col.stats.lower_bound || numVal > col.stats.upper_bound)) {
                          isOutlier = true;
                        }
                      }

                      return (
                        <td 
                          key={col.name}
                          className={`py-2 px-3 whitespace-nowrap text-zinc-200 text-xs ${
                            isNull ? 'bg-amber-950/20' : isOutlier ? 'bg-rose-950/15' : ''
                          }`}
                        >
                          {isNull ? (
                            <span className="inline-flex items-center gap-1 text-[11px] text-amber-400/90 font-sans italic bg-amber-950/60 px-1.5 py-0.5 rounded border border-amber-800/30">
                              <AlertCircle className="w-2.5 h-2.5" />
                              null
                            </span>
                          ) : isOutlier ? (
                            <span 
                              title={`Outlier beyond IQR boundary [${col.stats?.lower_bound} - ${col.stats?.upper_bound}]`}
                              className="text-rose-400 font-semibold inline-flex items-center gap-1"
                            >
                              {String(val)}
                              <span className="w-1 h-1 rounded-full bg-rose-500" />
                            </span>
                          ) : typeof val === 'number' ? (
                            <span className="text-zinc-100">{val.toLocaleString()}</span>
                          ) : (
                            <span className="text-zinc-300 font-sans">{String(val)}</span>
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
      <div className="flex items-center justify-between p-3 border-t border-zinc-800 bg-zinc-950/80 text-xs text-zinc-400">
        <div>
          Page <span className="text-zinc-200 font-medium">{currentPage}</span> of{' '}
          <span className="text-zinc-200 font-medium">{totalPages}</span>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
            disabled={currentPage === 1}
            className="p-1.5 rounded hover:bg-zinc-800 disabled:opacity-30 disabled:cursor-not-allowed text-zinc-300"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <span className="px-2 font-mono text-zinc-300">{currentPage}</span>
          <button
            onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
            disabled={currentPage >= totalPages}
            className="p-1.5 rounded hover:bg-zinc-800 disabled:opacity-30 disabled:cursor-not-allowed text-zinc-300"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};

