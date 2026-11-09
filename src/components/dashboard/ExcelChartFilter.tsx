import React, { useState, useMemo, useEffect } from 'react';
import { 
  Filter, 
  Search, 
  Check, 
  Minus, 
  RotateCcw, 
  X,
  SlidersHorizontal,
  ChevronDown,
  TrendingUp,
  TrendingDown,
  Layers,
  ListFilter,
  CheckCircle2,
  ArrowDownUp
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

export type FilterRuleType = 
  | 'none'
  | 'top_n'
  | 'bottom_n'
  | 'greater_than'
  | 'greater_than_or_equal'
  | 'less_than'
  | 'less_than_or_equal'
  | 'equals'
  | 'not_equals'
  | 'between'
  | 'above_average'
  | 'below_average'
  | 'contains'
  | 'starts_with';

export interface ColumnFilterRule {
  type: FilterRuleType;
  value?: number | string;
  value2?: number | string;
  targetMetric?: string;
}

export interface ColumnFilterConfig {
  selectedValues?: string[];
  rule?: ColumnFilterRule;
}

export type ColumnFilterState = {
  [column: string]: string[] | ColumnFilterConfig;
};

// Helper to determine if a filter config is active
export function isFilterActive(filter: string[] | ColumnFilterConfig | undefined, allValuesCount = 0): boolean {
  if (!filter) return false;
  if (Array.isArray(filter)) {
    return filter.length > 0 && (allValuesCount === 0 || filter.length < allValuesCount);
  }
  if (filter.rule && filter.rule.type !== 'none') return true;
  if (filter.selectedValues && filter.selectedValues.length > 0 && (allValuesCount === 0 || filter.selectedValues.length < allValuesCount)) {
    return true;
  }
  return false;
}

// Helper to get formatted summary badge text for a column filter
export function getFilterBadgeText(col: string, filter: string[] | ColumnFilterConfig | undefined): string {
  if (!filter) return '';
  if (Array.isArray(filter)) {
    return `${filter.length} selected`;
  }
  if (filter.rule && filter.rule.type !== 'none') {
    const { type, value, value2, targetMetric } = filter.rule;
    const metricSuffix = targetMetric && targetMetric !== col ? ` by ${targetMetric}` : '';
    switch (type) {
      case 'top_n':
        return `Top ${value || 10}${metricSuffix}`;
      case 'bottom_n':
        return `Bottom ${value || 10}${metricSuffix}`;
      case 'greater_than':
        return `> ${value}`;
      case 'greater_than_or_equal':
        return `>= ${value}`;
      case 'less_than':
        return `< ${value}`;
      case 'less_than_or_equal':
        return `<= ${value}`;
      case 'between':
        return `${value} to ${value2}`;
      case 'equals':
        return `= ${value}`;
      case 'not_equals':
        return `≠ ${value}`;
      case 'above_average':
        return `Above Avg${metricSuffix}`;
      case 'below_average':
        return `Below Avg${metricSuffix}`;
      case 'contains':
        return `Contains "${value}"`;
      case 'starts_with':
        return `Starts "${value}"`;
      default:
        break;
    }
  }
  if (filter.selectedValues && filter.selectedValues.length > 0) {
    return `${filter.selectedValues.length} selected`;
  }
  return 'Active';
}

// Master function to execute all active filters on a dataset
export function applyExcelFilters(
  rawData: Record<string, any>[],
  activeFilters: ColumnFilterState
): Record<string, any>[] {
  if (!rawData || rawData.length === 0) return [];
  const filterKeys = Object.keys(activeFilters).filter((k) => isFilterActive(activeFilters[k]));
  if (filterKeys.length === 0) return rawData;

  let filtered = [...rawData];

  for (const col of filterKeys) {
    const f = activeFilters[col];
    if (!f) continue;

    // 1. Direct array of selected values
    if (Array.isArray(f)) {
      if (f.length > 0) {
        filtered = filtered.filter((row) => {
          const rawVal = row[col];
          const strVal = rawVal !== undefined && rawVal !== null && String(rawVal).trim() !== ''
            ? String(rawVal).trim()
            : '(Blank)';
          return f.includes(strVal);
        });
      }
      continue;
    }

    // 2. Rule evaluation
    const config = f as ColumnFilterConfig;
    if (config.rule && config.rule.type !== 'none') {
      const { type, value, value2, targetMetric } = config.rule;
      const metricCol = targetMetric || col;

      if (type === 'top_n' || type === 'bottom_n') {
        const n = Math.max(1, Number(value) || 10);
        // Sort filtered rows by the metric column (or current column)
        const sorted = [...filtered].sort((a, b) => {
          const numA = Number(a[metricCol]) || 0;
          const numB = Number(b[metricCol]) || 0;
          return type === 'top_n' ? numB - numA : numA - numB;
        });
        filtered = sorted.slice(0, n);
      } else if (type === 'above_average' || type === 'below_average') {
        const nums = filtered.map((r) => Number(r[metricCol])).filter((n) => !isNaN(n));
        const avg = nums.length > 0 ? nums.reduce((a, b) => a + b, 0) / nums.length : 0;
        filtered = filtered.filter((row) => {
          const num = Number(row[metricCol]);
          if (isNaN(num)) return false;
          return type === 'above_average' ? num > avg : num < avg;
        });
      } else if (type === 'greater_than') {
        const threshold = Number(value);
        if (!isNaN(threshold)) {
          filtered = filtered.filter((row) => {
            const num = Number(row[col]);
            return !isNaN(num) && num > threshold;
          });
        }
      } else if (type === 'greater_than_or_equal') {
        const threshold = Number(value);
        if (!isNaN(threshold)) {
          filtered = filtered.filter((row) => {
            const num = Number(row[col]);
            return !isNaN(num) && num >= threshold;
          });
        }
      } else if (type === 'less_than') {
        const threshold = Number(value);
        if (!isNaN(threshold)) {
          filtered = filtered.filter((row) => {
            const num = Number(row[col]);
            return !isNaN(num) && num < threshold;
          });
        }
      } else if (type === 'less_than_or_equal') {
        const threshold = Number(value);
        if (!isNaN(threshold)) {
          filtered = filtered.filter((row) => {
            const num = Number(row[col]);
            return !isNaN(num) && num <= threshold;
          });
        }
      } else if (type === 'between') {
        const min = Number(value);
        const max = Number(value2);
        if (!isNaN(min) && !isNaN(max)) {
          const low = Math.min(min, max);
          const high = Math.max(min, max);
          filtered = filtered.filter((row) => {
            const num = Number(row[col]);
            return !isNaN(num) && num >= low && num <= high;
          });
        }
      } else if (type === 'equals') {
        const target = String(value ?? '').trim().toLowerCase();
        filtered = filtered.filter((row) => String(row[col] ?? '').trim().toLowerCase() === target);
      } else if (type === 'not_equals') {
        const target = String(value ?? '').trim().toLowerCase();
        filtered = filtered.filter((row) => String(row[col] ?? '').trim().toLowerCase() !== target);
      } else if (type === 'contains') {
        const q = String(value ?? '').trim().toLowerCase();
        if (q) {
          filtered = filtered.filter((row) => String(row[col] ?? '').toLowerCase().includes(q));
        }
      } else if (type === 'starts_with') {
        const q = String(value ?? '').trim().toLowerCase();
        if (q) {
          filtered = filtered.filter((row) => String(row[col] ?? '').toLowerCase().startsWith(q));
        }
      }
    }

    // 3. Values list if also present in config
    if (config.selectedValues && config.selectedValues.length > 0) {
      filtered = filtered.filter((row) => {
        const rawVal = row[col];
        const strVal = rawVal !== undefined && rawVal !== null && String(rawVal).trim() !== ''
          ? String(rawVal).trim()
          : '(Blank)';
        return config.selectedValues!.includes(strVal);
      });
    }
  }

  return filtered;
}

interface ExcelChartFilterProps {
  data: Record<string, any>[];
  availableColumns: string[];
  activeFilters: ColumnFilterState;
  onApplyFilters: (newFilters: ColumnFilterState) => void;
  onResetAllFilters: () => void;
  defaultColumn?: string;
}

export const ExcelChartFilter: React.FC<ExcelChartFilterProps> = ({
  data = [],
  availableColumns = [],
  activeFilters = {},
  onApplyFilters,
  onResetAllFilters,
  defaultColumn,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<'values' | 'top_bottom' | 'rules'>('values');
  
  const [selectedColumn, setSelectedColumn] = useState<string>(
    defaultColumn && availableColumns.includes(defaultColumn)
      ? defaultColumn
      : availableColumns[0] || ''
  );

  // Staged filter state for the active popover session
  const [searchQuery, setSearchQuery] = useState('');
  const [stagedSelection, setStagedSelection] = useState<string[]>([]);
  
  // Staged Advanced Rules
  const [stagedRuleType, setStagedRuleType] = useState<FilterRuleType>('none');
  const [stagedRuleValue, setStagedRuleValue] = useState<string>('10');
  const [stagedRuleValue2, setStagedRuleValue2] = useState<string>('');
  const [stagedTargetMetric, setStagedTargetMetric] = useState<string>('');

  // Update selectedColumn if defaultColumn changes or columns change
  useEffect(() => {
    if (defaultColumn && availableColumns.includes(defaultColumn)) {
      setSelectedColumn(defaultColumn);
    } else if (availableColumns.length > 0 && !availableColumns.includes(selectedColumn)) {
      setSelectedColumn(availableColumns[0]);
    }
  }, [defaultColumn, availableColumns, selectedColumn]);

  // Extract all distinct values and numeric metrics
  const { allValues, valueCounts, numericColumns, isColumnNumeric } = useMemo(() => {
    if (!selectedColumn || !data || data.length === 0) {
      return { allValues: [], valueCounts: {}, numericColumns: [], isColumnNumeric: false };
    }

    const counts: Record<string, number> = {};
    const valuesSet = new Set<string>();
    let numCount = 0;

    data.forEach((row) => {
      const rawVal = row[selectedColumn];
      if (typeof rawVal === 'number' || (rawVal !== null && rawVal !== '' && !isNaN(Number(rawVal)))) {
        numCount++;
      }

      const strVal = rawVal !== undefined && rawVal !== null && String(rawVal).trim() !== ''
        ? String(rawVal).trim()
        : '(Blank)';
      
      counts[strVal] = (counts[strVal] || 0) + 1;
      valuesSet.add(strVal);
    });

    // Detect numeric columns across the dataset for Top N metric ranking
    const numCols = availableColumns.filter((col) => {
      const sample = data.find((r) => r[col] !== undefined && r[col] !== null);
      if (!sample) return false;
      const v = sample[col];
      return typeof v === 'number' || (!isNaN(Number(v)) && String(v).trim() !== '');
    });

    const sortedValues = Array.from(valuesSet).sort((a, b) => {
      if (a === '(Blank)') return 1;
      if (b === '(Blank)') return -1;
      return a.localeCompare(b, undefined, { numeric: true, sensitivity: 'base' });
    });

    return { 
      allValues: sortedValues, 
      valueCounts: counts, 
      numericColumns: numCols,
      isColumnNumeric: numCount > data.length * 0.5
    };
  }, [data, selectedColumn, availableColumns]);

  // Sync staged state when popover opens or column changes
  useEffect(() => {
    if (isOpen && selectedColumn) {
      const current = activeFilters[selectedColumn];
      if (current) {
        if (Array.isArray(current)) {
          setStagedSelection([...current]);
          setStagedRuleType('none');
          setStagedRuleValue('10');
          setStagedRuleValue2('');
          setStagedTargetMetric('');
          setActiveTab('values');
        } else {
          setStagedSelection(current.selectedValues ? [...current.selectedValues] : [...allValues]);
          if (current.rule && current.rule.type !== 'none') {
            setStagedRuleType(current.rule.type);
            setStagedRuleValue(current.rule.value !== undefined ? String(current.rule.value) : '10');
            setStagedRuleValue2(current.rule.value2 !== undefined ? String(current.rule.value2) : '');
            setStagedTargetMetric(current.rule.targetMetric || '');
            if (['top_n', 'bottom_n', 'above_average', 'below_average'].includes(current.rule.type)) {
              setActiveTab('top_bottom');
            } else {
              setActiveTab('rules');
            }
          } else {
            setStagedRuleType('none');
            setActiveTab('values');
          }
        }
      } else {
        // By default, all values selected and no rule
        setStagedSelection([...allValues]);
        setStagedRuleType('none');
        setStagedRuleValue('10');
        setStagedRuleValue2('');
        setStagedTargetMetric(numericColumns.length > 0 ? numericColumns[0] : selectedColumn);
        setActiveTab('values');
      }
      setSearchQuery('');
    }
  }, [isOpen, selectedColumn, allValues, activeFilters, numericColumns]);

  // Filter values based on search query
  const filteredValues = useMemo(() => {
    if (!searchQuery.trim()) return allValues;
    const q = searchQuery.toLowerCase().trim();
    return allValues.filter((v) => v.toLowerCase().includes(q));
  }, [allValues, searchQuery]);

  // Check state of (Select All)
  const isAllFilteredSelected = filteredValues.length > 0 && filteredValues.every((v) => stagedSelection.includes(v));
  const isSomeFilteredSelected = filteredValues.some((v) => stagedSelection.includes(v)) && !isAllFilteredSelected;

  const toggleSelectAll = () => {
    if (isAllFilteredSelected) {
      setStagedSelection((prev) => prev.filter((v) => !filteredValues.includes(v)));
    } else {
      setStagedSelection((prev) => Array.from(new Set([...prev, ...filteredValues])));
    }
  };

  const toggleValue = (value: string) => {
    setStagedSelection((prev) =>
      prev.includes(value) ? prev.filter((v) => v !== value) : [...prev, value]
    );
  };

  const handleSelectOnly = (value: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setStagedSelection([value]);
  };

  // Quick Preset for Top/Bottom Rules
  const applyPresetRule = (type: FilterRuleType, count = '10') => {
    setStagedRuleType(type);
    setStagedRuleValue(count);
    if (!stagedTargetMetric && numericColumns.length > 0) {
      setStagedTargetMetric(numericColumns[0]);
    }
  };

  const handleApply = () => {
    const isFullValues = stagedSelection.length === allValues.length || stagedSelection.length === 0;
    const hasActiveRule = stagedRuleType !== 'none';
    const newFilters: ColumnFilterState = { ...activeFilters };

    if (!hasActiveRule && isFullValues) {
      delete newFilters[selectedColumn];
    } else if (hasActiveRule) {
      newFilters[selectedColumn] = {
        rule: {
          type: stagedRuleType,
          value: stagedRuleValue,
          value2: stagedRuleValue2,
          targetMetric: stagedTargetMetric || (isColumnNumeric ? selectedColumn : numericColumns[0]),
        },
        selectedValues: isFullValues ? undefined : stagedSelection,
      };
    } else {
      // Just value list filter
      newFilters[selectedColumn] = stagedSelection;
    }

    onApplyFilters(newFilters);
    setIsOpen(false);
  };

  const handleResetCurrentColumn = () => {
    setStagedSelection([...allValues]);
    setStagedRuleType('none');
    setStagedRuleValue('10');
    setStagedRuleValue2('');
    const newFilters: ColumnFilterState = { ...activeFilters };
    delete newFilters[selectedColumn];
    onApplyFilters(newFilters);
    setIsOpen(false);
  };

  const isCurrentColumnFiltered = isFilterActive(activeFilters[selectedColumn], allValues.length);

  const totalActiveFilterCount = Object.keys(activeFilters).filter(
    (k) => isFilterActive(activeFilters[k])
  ).length;

  return (
    <div className="flex items-center gap-1.5">
      <Popover open={isOpen} onOpenChange={setIsOpen}>
        <PopoverTrigger asChild>
          <Button
            variant="outline"
            size="sm"
            className={`h-7 px-2.5 text-xs font-normal gap-1.5 transition-all ${
              totalActiveFilterCount > 0
                ? 'bg-emerald-500/20 border-emerald-500/50 text-emerald-300 hover:bg-emerald-500/30'
                : 'bg-slate-950 border-slate-700 text-slate-300 hover:text-white hover:bg-slate-800'
            }`}
            title="Excel-style & Top/Bottom Filters"
          >
            <Filter className={`w-3.5 h-3.5 ${totalActiveFilterCount > 0 ? 'text-emerald-400' : 'text-slate-400'}`} />
            <span className="hidden sm:inline">
              {totalActiveFilterCount > 0 ? `Filter (${totalActiveFilterCount})` : 'Filter'}
            </span>
            <ChevronDown className="w-3 h-3 opacity-60 ml-0.5" />
          </Button>
        </PopoverTrigger>

        <PopoverContent
          align="end"
          className="w-88 p-0 bg-slate-900 border-slate-700 text-white shadow-2xl z-50 rounded-xl overflow-hidden"
        >
          {/* Header */}
          <div className="p-3 bg-slate-950 border-b border-slate-800 space-y-2.5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5">
                <SlidersHorizontal className="w-3.5 h-3.5 text-emerald-400" />
                <span className="text-xs font-semibold text-white">Excel Chart Filter</span>
              </div>
              {isCurrentColumnFiltered && (
                <Badge variant="outline" className="border-emerald-500/40 text-emerald-300 bg-emerald-500/10 text-[10px] py-0">
                  {getFilterBadgeText(selectedColumn, activeFilters[selectedColumn])}
                </Badge>
              )}
            </div>

            {/* Column Selector */}
            {availableColumns.length > 1 && (
              <div className="space-y-1">
                <label className="text-[11px] text-slate-400">Column to Filter:</label>
                <Select
                  value={selectedColumn}
                  onValueChange={(val) => {
                    setSelectedColumn(val);
                  }}
                >
                  <SelectTrigger className="h-7 bg-slate-900 border-slate-700 text-xs text-white">
                    <SelectValue placeholder="Select column" />
                  </SelectTrigger>
                  <SelectContent className="bg-slate-900 border-slate-700 text-white text-xs z-50">
                    {availableColumns.map((col) => (
                      <SelectItem key={col} value={col}>
                        <div className="flex items-center justify-between w-full gap-2">
                          <span>{col}</span>
                          {isFilterActive(activeFilters[col]) && (
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                          )}
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}

            {/* Filter Mode Navigation Tabs */}
            <div className="grid grid-cols-3 gap-1 bg-slate-900 p-0.5 rounded-lg border border-slate-800 text-[11px]">
              <button
                type="button"
                onClick={() => setActiveTab('values')}
                className={`py-1 rounded font-medium flex items-center justify-center gap-1 transition-all ${
                  activeTab === 'values'
                    ? 'bg-emerald-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                <ListFilter className="w-3 h-3" />
                Values
              </button>
              <button
                type="button"
                onClick={() => setActiveTab('top_bottom')}
                className={`py-1 rounded font-medium flex items-center justify-center gap-1 transition-all ${
                  activeTab === 'top_bottom'
                    ? 'bg-emerald-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                <ArrowDownUp className="w-3 h-3" />
                Top / Bottom
              </button>
              <button
                type="button"
                onClick={() => setActiveTab('rules')}
                className={`py-1 rounded font-medium flex items-center justify-center gap-1 transition-all ${
                  activeTab === 'rules'
                    ? 'bg-emerald-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                <Layers className="w-3 h-3" />
                Rules (&gt;, &lt;)
              </button>
            </div>
          </div>

          {/* TAB 1: VALUES CHECKLIST (EXCEL-STYLE) */}
          {activeTab === 'values' && (
            <div className="p-2 space-y-2">
              {/* Search Box */}
              <div className="relative px-1">
                <Search className="w-3.5 h-3.5 absolute left-3 top-2 text-slate-400" />
                <Input
                  placeholder={`Search ${selectedColumn} values...`}
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-8 h-7 text-xs bg-slate-950 border-slate-700 text-white placeholder:text-slate-500"
                />
                {searchQuery && (
                  <button
                    onClick={() => setSearchQuery('')}
                    className="absolute right-3 top-2 text-slate-400 hover:text-white"
                  >
                    <X className="w-3 h-3" />
                  </button>
                )}
              </div>

              {/* Quick Actions */}
              <div className="flex items-center justify-between px-1 text-[11px]">
                <button
                  type="button"
                  onClick={() => setStagedSelection([...allValues])}
                  className="text-slate-400 hover:text-emerald-400 transition-colors"
                >
                  Select All
                </button>
                <span className="text-slate-700">•</span>
                <button
                  type="button"
                  onClick={() => setStagedSelection([])}
                  className="text-slate-400 hover:text-red-400 transition-colors"
                >
                  Clear All
                </button>
                <span className="text-slate-700">•</span>
                <span className="text-slate-500">
                  {stagedSelection.length} of {allValues.length} selected
                </span>
              </div>

              {/* Checklist Scroll Area */}
              <div className="max-h-48 overflow-y-auto px-1 space-y-0.5 divide-y divide-slate-800/40">
                <div
                  onClick={toggleSelectAll}
                  className="flex items-center justify-between px-2 py-1.5 rounded hover:bg-slate-800/80 cursor-pointer select-none text-xs font-medium text-slate-200"
                >
                  <div className="flex items-center gap-2">
                    <div
                      className={`flex h-4 w-4 items-center justify-center rounded border transition-colors ${
                        isAllFilteredSelected
                          ? 'bg-emerald-500 border-emerald-500 text-white'
                          : isSomeFilteredSelected
                          ? 'bg-emerald-500/50 border-emerald-500 text-white'
                          : 'border-slate-600 bg-slate-950/60'
                      }`}
                    >
                      {isAllFilteredSelected && <Check className="h-3 w-3" />}
                      {isSomeFilteredSelected && <Minus className="h-3 w-3" />}
                    </div>
                    <span>(Select All{searchQuery ? ' Search Results' : ''})</span>
                  </div>
                  <span className="text-[10px] text-slate-400">{filteredValues.length}</span>
                </div>

                {filteredValues.length === 0 ? (
                  <div className="py-6 text-center text-xs text-slate-500">
                    No matching values found
                  </div>
                ) : (
                  filteredValues.map((val) => {
                    const isSelected = stagedSelection.includes(val);
                    return (
                      <div
                        key={val}
                        onClick={() => toggleValue(val)}
                        className="group flex items-center justify-between px-2 py-1.5 rounded hover:bg-slate-800/80 cursor-pointer select-none text-xs text-slate-200 transition-colors"
                      >
                        <div className="flex items-center gap-2 min-w-0 pr-2">
                          <div
                            className={`flex h-4 w-4 shrink-0 items-center justify-center rounded border transition-colors ${
                              isSelected
                                ? 'bg-emerald-500 border-emerald-500 text-white'
                                : 'border-slate-600 bg-slate-950/60'
                            }`}
                          >
                            {isSelected && <Check className="h-3 w-3" />}
                          </div>
                          <span className="truncate" title={val}>{val}</span>
                        </div>

                        <div className="flex items-center gap-1.5 shrink-0">
                          <button
                            type="button"
                            onClick={(e) => handleSelectOnly(val, e)}
                            className="opacity-0 group-hover:opacity-100 text-[10px] text-emerald-400 hover:underline px-1 py-0.5"
                            title="Select only this item"
                          >
                            Only
                          </button>
                          <span className="text-[10px] text-slate-500 bg-slate-950 px-1.5 py-0.5 rounded border border-slate-800">
                            {valueCounts[val] || 0}
                          </span>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </div>
          )}

          {/* TAB 2: TOP / BOTTOM FILTERS (TOP 10, BOTTOM 10, ETC.) */}
          {activeTab === 'top_bottom' && (
            <div className="p-3 space-y-3">
              <div className="text-[11px] text-slate-400 font-medium">
                Quick Top &amp; Bottom Presets:
              </div>

              {/* Quick Preset Buttons Grid */}
              <div className="grid grid-cols-2 gap-1.5">
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  onClick={() => applyPresetRule('top_n', '10')}
                  className={`h-8 text-xs justify-start gap-1.5 border-slate-700 ${
                    stagedRuleType === 'top_n' && stagedRuleValue === '10'
                      ? 'bg-emerald-600/30 border-emerald-500 text-emerald-300'
                      : 'bg-slate-950 text-slate-200 hover:bg-slate-800'
                  }`}
                >
                  <TrendingUp className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Top 10</span>
                </Button>

                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  onClick={() => applyPresetRule('bottom_n', '10')}
                  className={`h-8 text-xs justify-start gap-1.5 border-slate-700 ${
                    stagedRuleType === 'bottom_n' && stagedRuleValue === '10'
                      ? 'bg-emerald-600/30 border-emerald-500 text-emerald-300'
                      : 'bg-slate-950 text-slate-200 hover:bg-slate-800'
                  }`}
                >
                  <TrendingDown className="w-3.5 h-3.5 text-red-400" />
                  <span>Bottom 10</span>
                </Button>

                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  onClick={() => applyPresetRule('top_n', '5')}
                  className={`h-8 text-xs justify-start gap-1.5 border-slate-700 ${
                    stagedRuleType === 'top_n' && stagedRuleValue === '5'
                      ? 'bg-emerald-600/30 border-emerald-500 text-emerald-300'
                      : 'bg-slate-950 text-slate-200 hover:bg-slate-800'
                  }`}
                >
                  <TrendingUp className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Top 5</span>
                </Button>

                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  onClick={() => applyPresetRule('bottom_n', '5')}
                  className={`h-8 text-xs justify-start gap-1.5 border-slate-700 ${
                    stagedRuleType === 'bottom_n' && stagedRuleValue === '5'
                      ? 'bg-emerald-600/30 border-emerald-500 text-emerald-300'
                      : 'bg-slate-950 text-slate-200 hover:bg-slate-800'
                  }`}
                >
                  <TrendingDown className="w-3.5 h-3.5 text-red-400" />
                  <span>Bottom 5</span>
                </Button>

                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  onClick={() => applyPresetRule('top_n', '25')}
                  className={`h-8 text-xs justify-start gap-1.5 border-slate-700 ${
                    stagedRuleType === 'top_n' && stagedRuleValue === '25'
                      ? 'bg-emerald-600/30 border-emerald-500 text-emerald-300'
                      : 'bg-slate-950 text-slate-200 hover:bg-slate-800'
                  }`}
                >
                  <TrendingUp className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Top 25</span>
                </Button>

                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  onClick={() => applyPresetRule('bottom_n', '25')}
                  className={`h-8 text-xs justify-start gap-1.5 border-slate-700 ${
                    stagedRuleType === 'bottom_n' && stagedRuleValue === '25'
                      ? 'bg-emerald-600/30 border-emerald-500 text-emerald-300'
                      : 'bg-slate-950 text-slate-200 hover:bg-slate-800'
                  }`}
                >
                  <TrendingDown className="w-3.5 h-3.5 text-red-400" />
                  <span>Bottom 25</span>
                </Button>

                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  onClick={() => applyPresetRule('above_average')}
                  className={`h-8 text-xs justify-start gap-1.5 border-slate-700 ${
                    stagedRuleType === 'above_average'
                      ? 'bg-emerald-600/30 border-emerald-500 text-emerald-300'
                      : 'bg-slate-950 text-slate-200 hover:bg-slate-800'
                  }`}
                >
                  <TrendingUp className="w-3.5 h-3.5 text-cyan-400" />
                  <span>Above Average</span>
                </Button>

                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  onClick={() => applyPresetRule('below_average')}
                  className={`h-8 text-xs justify-start gap-1.5 border-slate-700 ${
                    stagedRuleType === 'below_average'
                      ? 'bg-emerald-600/30 border-emerald-500 text-emerald-300'
                      : 'bg-slate-950 text-slate-200 hover:bg-slate-800'
                  }`}
                >
                  <TrendingDown className="w-3.5 h-3.5 text-amber-400" />
                  <span>Below Average</span>
                </Button>
              </div>

              {/* Custom Top/Bottom Configuration */}
              <div className="pt-2 border-t border-slate-800 space-y-2">
                <div className="text-[11px] text-slate-400 font-medium">Custom Top / Bottom:</div>
                <div className="flex items-center gap-2">
                  <Select
                    value={stagedRuleType === 'bottom_n' ? 'bottom_n' : 'top_n'}
                    onValueChange={(val: any) => setStagedRuleType(val)}
                  >
                    <SelectTrigger className="h-7 w-24 bg-slate-950 border-slate-700 text-xs">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-slate-900 border-slate-700 text-white text-xs z-50">
                      <SelectItem value="top_n">Top</SelectItem>
                      <SelectItem value="bottom_n">Bottom</SelectItem>
                    </SelectContent>
                  </Select>

                  <Input
                    type="number"
                    min="1"
                    max="1000"
                    value={stagedRuleValue}
                    onChange={(e) => {
                      setStagedRuleValue(e.target.value);
                      if (stagedRuleType !== 'bottom_n') setStagedRuleType('top_n');
                    }}
                    placeholder="10"
                    className="h-7 w-20 text-xs bg-slate-950 border-slate-700 text-white"
                  />
                  <span className="text-xs text-slate-400">items</span>
                </div>

                {/* Optional Metric to Rank by */}
                {numericColumns.length > 1 && (
                  <div className="space-y-1 pt-1">
                    <label className="text-[11px] text-slate-400">Rank By Metric Column:</label>
                    <Select
                      value={stagedTargetMetric || numericColumns[0]}
                      onValueChange={(val) => setStagedTargetMetric(val)}
                    >
                      <SelectTrigger className="h-7 bg-slate-950 border-slate-700 text-xs text-white">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-slate-900 border-slate-700 text-white text-xs z-50">
                        {numericColumns.map((col) => (
                          <SelectItem key={col} value={col}>
                            {col}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                )}
              </div>

              {/* Active Rule Indicator */}
              {stagedRuleType !== 'none' && (
                <div className="flex items-center justify-between p-2 rounded bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs">
                  <div className="flex items-center gap-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                    <span>Rule: {getFilterBadgeText(selectedColumn, { rule: { type: stagedRuleType, value: stagedRuleValue, value2: stagedRuleValue2, targetMetric: stagedTargetMetric } })}</span>
                  </div>
                  <button
                    type="button"
                    onClick={() => setStagedRuleType('none')}
                    className="text-slate-400 hover:text-red-400"
                    title="Remove rule"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                </div>
              )}
            </div>
          )}

          {/* TAB 3: NUMBER & COMPARISON RULES (GREATER THAN, LESS THAN, ETC.) */}
          {activeTab === 'rules' && (
            <div className="p-3 space-y-3">
              <div className="space-y-1">
                <label className="text-[11px] text-slate-400">Condition:</label>
                <Select
                  value={stagedRuleType}
                  onValueChange={(val: any) => setStagedRuleType(val)}
                >
                  <SelectTrigger className="h-7 bg-slate-950 border-slate-700 text-xs text-white">
                    <SelectValue placeholder="Select condition" />
                  </SelectTrigger>
                  <SelectContent className="bg-slate-900 border-slate-700 text-white text-xs z-50">
                    <SelectItem value="none">No Rule / All</SelectItem>
                    <SelectItem value="greater_than">Greater Than (&gt;)</SelectItem>
                    <SelectItem value="greater_than_or_equal">Greater Than or Equal (&gt;=)</SelectItem>
                    <SelectItem value="less_than">Less Than (&lt;)</SelectItem>
                    <SelectItem value="less_than_or_equal">Less Than or Equal (&lt;=)</SelectItem>
                    <SelectItem value="between">Between (min to max)</SelectItem>
                    <SelectItem value="equals">Equals (=)</SelectItem>
                    <SelectItem value="not_equals">Does Not Equal (≠)</SelectItem>
                    <SelectItem value="contains">Contains text</SelectItem>
                    <SelectItem value="starts_with">Starts with</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Value Input(s) */}
              {stagedRuleType !== 'none' && (
                <div className="space-y-2">
                  <div className="space-y-1">
                    <label className="text-[11px] text-slate-400">
                      {stagedRuleType === 'between' ? 'Minimum Value:' : 'Target Value:'}
                    </label>
                    <Input
                      type={['greater_than', 'greater_than_or_equal', 'less_than', 'less_than_or_equal', 'between'].includes(stagedRuleType) ? 'number' : 'text'}
                      value={stagedRuleValue}
                      onChange={(e) => setStagedRuleValue(e.target.value)}
                      placeholder="e.g. 1000"
                      className="h-7 text-xs bg-slate-950 border-slate-700 text-white"
                    />
                  </div>

                  {stagedRuleType === 'between' && (
                    <div className="space-y-1">
                      <label className="text-[11px] text-slate-400">Maximum Value:</label>
                      <Input
                        type="number"
                        value={stagedRuleValue2}
                        onChange={(e) => setStagedRuleValue2(e.target.value)}
                        placeholder="e.g. 5000"
                        className="h-7 text-xs bg-slate-950 border-slate-700 text-white"
                      />
                    </div>
                  )}
                </div>
              )}

              {/* Active Rule Indicator */}
              {stagedRuleType !== 'none' && (
                <div className="flex items-center justify-between p-2 rounded bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs">
                  <div className="flex items-center gap-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                    <span>Rule: {getFilterBadgeText(selectedColumn, { rule: { type: stagedRuleType, value: stagedRuleValue, value2: stagedRuleValue2, targetMetric: stagedTargetMetric } })}</span>
                  </div>
                  <button
                    type="button"
                    onClick={() => setStagedRuleType('none')}
                    className="text-slate-400 hover:text-red-400"
                    title="Remove rule"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Action Footer (Clear/Reset, Cancel, Apply) */}
          <div className="p-2.5 bg-slate-950 border-t border-slate-800 flex items-center justify-between gap-2">
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={handleResetCurrentColumn}
              className="h-7 px-2 text-xs text-slate-400 hover:text-red-400 hover:bg-red-500/10"
              title="Clear filter on this column"
            >
              <RotateCcw className="w-3 h-3 mr-1" />
              Clear / Reset
            </Button>

            <div className="flex items-center gap-1.5">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setIsOpen(false)}
                className="h-7 px-2.5 text-xs border-slate-700 bg-slate-900 text-slate-300 hover:text-white"
              >
                Cancel
              </Button>
              <Button
                type="button"
                size="sm"
                onClick={handleApply}
                className="h-7 px-3 text-xs bg-emerald-600 hover:bg-emerald-500 text-white font-medium shadow-md shadow-emerald-900/30"
              >
                <Check className="w-3 h-3 mr-1" />
                Apply
              </Button>
            </div>
          </div>
        </PopoverContent>
      </Popover>

      {/* Quick Reset Button when any filter is active */}
      {totalActiveFilterCount > 0 && (
        <Button
          variant="ghost"
          size="sm"
          onClick={onResetAllFilters}
          className="h-7 px-1.5 text-xs text-slate-400 hover:text-red-400 hover:bg-red-500/10"
          title="Reset all filters"
        >
          <X className="w-3 h-3" />
        </Button>
      )}
    </div>
  );
};

export default ExcelChartFilter;
