import React, { useState, useCallback } from 'react';
import { Search, SlidersHorizontal, X, Save, Download } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import { DatePicker } from '@/components/ui/date-picker';
import { FilterCriteria } from '@/utils/data-processing';

interface AdvancedFiltersProps {
  filters: FilterCriteria;
  onFiltersChange: (filters: FilterCriteria) => void;
  onExport?: () => void;
  availableCategories?: string[];
  className?: string;
}

interface FilterPreset {
  name: string;
  description: string;
  filters: FilterCriteria;
}

const DEFAULT_PRESETS: FilterPreset[] = [
  {
    name: 'Last 7 Days',
    description: 'Data from the past week',
    filters: {
      dateRange: {
        start: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000),
        end: new Date(),
      },
    },
  },
  {
    name: 'Last 30 Days',
    description: 'Data from the past month',
    filters: {
      dateRange: {
        start: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000),
        end: new Date(),
      },
    },
  },
  {
    name: 'Revenue Only',
    description: 'Filter to revenue-related data',
    filters: {
      categories: ['Revenue'],
    },
  },
  {
    name: 'High Value',
    description: 'Values above 750',
    filters: {
      valueRange: {
        min: 750,
        max: Infinity,
      },
    },
  },
];

export const AdvancedFilters: React.FC<AdvancedFiltersProps> = ({
  filters,
  onFiltersChange,
  onExport,
  availableCategories = ['Revenue', 'Users', 'Performance', 'Conversion'],
  className = '',
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState(filters.searchTerm || '');
  const [selectedCategories, setSelectedCategories] = useState<string[]>(filters.categories || []);
  const [valueRange, setValueRange] = useState({
    min: filters.valueRange?.min?.toString() || '',
    max: filters.valueRange?.max?.toString() || '',
  });
  const [dateRange, setDateRange] = useState({
    start: filters.dateRange?.start,
    end: filters.dateRange?.end,
  });

  const getActiveFiltersCount = useCallback(() => {
    let count = 0;
    if (filters.searchTerm) count++;
    if (filters.categories && filters.categories.length > 0) count++;
    if (filters.valueRange) count++;
    if (filters.dateRange) count++;
    return count;
  }, [filters]);

  const applyFilters = useCallback(() => {
    const newFilters: FilterCriteria = {};

    if (searchTerm.trim()) {
      newFilters.searchTerm = searchTerm.trim();
    }

    if (selectedCategories.length > 0) {
      newFilters.categories = selectedCategories;
    }

    if (valueRange.min || valueRange.max) {
      newFilters.valueRange = {
        min: valueRange.min ? parseFloat(valueRange.min) : -Infinity,
        max: valueRange.max ? parseFloat(valueRange.max) : Infinity,
      };
    }

    if (dateRange.start && dateRange.end) {
      newFilters.dateRange = {
        start: dateRange.start,
        end: dateRange.end,
      };
    }

    onFiltersChange(newFilters);
    setIsOpen(false);
  }, [searchTerm, selectedCategories, valueRange, dateRange, onFiltersChange]);

  const clearAllFilters = useCallback(() => {
    setSearchTerm('');
    setSelectedCategories([]);
    setValueRange({ min: '', max: '' });
    setDateRange({ start: undefined, end: undefined });
    onFiltersChange({});
  }, [onFiltersChange]);

  const applyPreset = useCallback((preset: FilterPreset) => {
    const { filters: presetFilters } = preset;
    
    setSearchTerm(presetFilters.searchTerm || '');
    setSelectedCategories(presetFilters.categories || []);
    setValueRange({
      min: presetFilters.valueRange?.min?.toString() || '',
      max: presetFilters.valueRange?.max === Infinity ? '' : presetFilters.valueRange?.max?.toString() || '',
    });
    setDateRange({
      start: presetFilters.dateRange?.start,
      end: presetFilters.dateRange?.end,
    });
    
    onFiltersChange(presetFilters);
    setIsOpen(false);
  }, [onFiltersChange]);

  const toggleCategory = useCallback((category: string) => {
    setSelectedCategories(prev => {
      if (prev.includes(category)) {
        return prev.filter(c => c !== category);
      } else {
        return [...prev, category];
      }
    });
  }, []);

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      {/* Quick Search */}
      <div className="relative">
        <Search className="h-4 w-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground" />
        <Input
          type="text"
          placeholder="Search data..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              applyFilters();
            }
          }}
          className="pl-10 w-48 glass-button"
        />
      </div>

      {/* Advanced Filters Popover */}
      <Popover open={isOpen} onOpenChange={setIsOpen}>
        <PopoverTrigger asChild>
          <Button variant="outline" className="relative glass-button">
            <SlidersHorizontal className="h-4 w-4 mr-2" />
            Advanced
            {getActiveFiltersCount() > 0 && (
              <span className="ml-2 px-2 py-0.5 bg-primary text-primary-foreground text-xs rounded-full">
                {getActiveFiltersCount()}
              </span>
            )}
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-96 z-[99999] bg-white dark:bg-slate-800 backdrop-blur-lg shadow-xl border border-border" align="end">
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h4 className="font-semibold text-foreground">Advanced Filters</h4>
              <Button variant="ghost" size="sm" onClick={() => setIsOpen(false)}>
                <X className="h-4 w-4" />
              </Button>
            </div>

            {/* Filter Presets */}
            <div className="space-y-2">
              <Label className="text-sm font-medium text-foreground">Quick Presets</Label>
              <div className="grid grid-cols-2 gap-2">
                {DEFAULT_PRESETS.map((preset) => (
                  <Button
                    key={preset.name}
                    variant="outline"
                    size="sm"
                    onClick={() => applyPreset(preset)}
                    className="text-left justify-start h-auto p-2"
                  >
                    <div>
                      <div className="text-xs font-medium">{preset.name}</div>
                      <div className="text-xs text-muted-foreground">{preset.description}</div>
                    </div>
                  </Button>
                ))}
              </div>
            </div>

            {/* Categories Filter */}
            <div className="space-y-2">
              <Label className="text-sm font-medium text-foreground">Categories</Label>
              <div className="flex flex-wrap gap-2">
                {availableCategories.map((category) => (
                  <Button
                    key={category}
                    variant={selectedCategories.includes(category) ? "default" : "outline"}
                    size="sm"
                    onClick={() => toggleCategory(category)}
                    className="text-xs"
                  >
                    {category}
                  </Button>
                ))}
              </div>
            </div>

            {/* Value Range Filter */}
            <div className="space-y-2">
              <Label className="text-sm font-medium text-foreground">Value Range</Label>
              <div className="flex items-center gap-2">
                <Input
                  type="number"
                  placeholder="Min"
                  value={valueRange.min}
                  onChange={(e) => setValueRange(prev => ({ ...prev, min: e.target.value }))}
                  className="bg-background text-foreground border-border"
                />
                <span className="text-muted-foreground">to</span>
                <Input
                  type="number"
                  placeholder="Max"
                  value={valueRange.max}
                  onChange={(e) => setValueRange(prev => ({ ...prev, max: e.target.value }))}
                  className="bg-background text-foreground border-border"
                />
              </div>
            </div>

            {/* Date Range Filter */}
            <div className="space-y-2">
              <Label className="text-sm font-medium text-foreground">Date Range</Label>
              <div className="flex items-center gap-2">
                <DatePicker
                  date={dateRange.start}
                  onDateChange={(date) => setDateRange(prev => ({ ...prev, start: date }))}
                  placeholder="Start date"
                  className="flex-1"
                />
                <span className="text-muted-foreground">to</span>
                <DatePicker
                  date={dateRange.end}
                  onDateChange={(date) => setDateRange(prev => ({ ...prev, end: date }))}
                  placeholder="End date"
                  className="flex-1"
                />
              </div>
            </div>

            {/* Actions */}
            <div className="flex justify-between pt-4 border-t border-border">
              <Button variant="outline" size="sm" onClick={clearAllFilters}>
                Clear All
              </Button>
              <div className="flex gap-2">
                {onExport && (
                  <Button variant="outline" size="sm" onClick={onExport}>
                    <Download className="h-4 w-4 mr-1" />
                    Export
                  </Button>
                )}
                <Button size="sm" onClick={applyFilters}>
                  Apply Filters
                </Button>
              </div>
            </div>
          </div>
        </PopoverContent>
      </Popover>

      {/* Active Filters Display */}
      {getActiveFiltersCount() > 0 && (
        <div className="flex items-center gap-2">
          {filters.searchTerm && (
            <span className="px-2 py-1 bg-primary/10 text-primary rounded-md text-sm flex items-center gap-1">
              Search: "{filters.searchTerm}"
              <button
                onClick={() => {
                  setSearchTerm('');
                  onFiltersChange({ ...filters, searchTerm: undefined });
                }}
                className="hover:text-red-500"
              >
                <X className="h-3 w-3" />
              </button>
            </span>
          )}
          
          {filters.categories && filters.categories.length > 0 && (
            <span className="px-2 py-1 bg-primary/10 text-primary rounded-md text-sm flex items-center gap-1">
              Categories: {filters.categories.join(', ')}
              <button
                onClick={() => {
                  setSelectedCategories([]);
                  onFiltersChange({ ...filters, categories: undefined });
                }}
                className="hover:text-red-500"
              >
                <X className="h-3 w-3" />
              </button>
            </span>
          )}
          
          {filters.valueRange && (
            <span className="px-2 py-1 bg-primary/10 text-primary rounded-md text-sm flex items-center gap-1">
              Range: {filters.valueRange.min} - {filters.valueRange.max === Infinity ? '∞' : filters.valueRange.max}
              <button
                onClick={() => {
                  setValueRange({ min: '', max: '' });
                  onFiltersChange({ ...filters, valueRange: undefined });
                }}
                className="hover:text-red-500"
              >
                <X className="h-3 w-3" />
              </button>
            </span>
          )}
          
          {filters.dateRange && (
            <span className="px-2 py-1 bg-primary/10 text-primary rounded-md text-sm flex items-center gap-1">
              Date: {filters.dateRange.start?.toLocaleDateString()} - {filters.dateRange.end?.toLocaleDateString()}
              <button
                onClick={() => {
                  setDateRange({ start: undefined, end: undefined });
                  onFiltersChange({ ...filters, dateRange: undefined });
                }}
                className="hover:text-red-500"
              >
                <X className="h-3 w-3" />
              </button>
            </span>
          )}
        </div>
      )}
    </div>
  );
}; 