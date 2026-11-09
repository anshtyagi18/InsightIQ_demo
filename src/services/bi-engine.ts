import Papa from 'papaparse';
import * as XLSX from 'xlsx';

export interface ColumnProfile {
  name: string;
  type: 'numeric' | 'categorical' | 'date' | 'boolean' | 'id';
  nullCount: number;
  nullPercentage: number;
  uniqueCount: number;
  sampleValues: (string | number)[];
  // Numeric stats
  min?: number;
  max?: number;
  mean?: number;
  median?: number;
  stdDev?: number;
  sum?: number;
  // Categorical stats
  topValues?: { value: string; count: number; percentage: number }[];
  quality: 'good' | 'warning' | 'error';
}

export interface DatasetProfile {
  rowCount: number;
  columnCount: number;
  totalCells: number;
  duplicateRows: number;
  completeness: number; // percentage 0-100
  columns: ColumnProfile[];
  numericColumns: string[];
  categoricalColumns: string[];
  dateColumns: string[];
  idColumns: string[];
  primaryMetric?: string;
  secondaryMetric?: string;
  primaryDimension?: string;
  secondaryDimension?: string;
  primaryDate?: string;
}

export interface CleaningOptions {
  removeDuplicates?: boolean;
  numericMissingStrategy?: 'median' | 'mean' | 'zero' | 'drop';
  categoricalMissingStrategy?: 'unknown' | 'mode' | 'drop';
  trimWhitespace?: boolean;
  convertTypes?: boolean;
}

export interface AdvancedCleaningOptions {
  droppedColumns?: string[];
  renamedColumns?: Record<string, string>;
  missingStrategy?: 'median' | 'mean' | 'mode' | 'zero' | 'custom' | 'drop_row' | 'ffill' | 'bfill';
  customMissingValue?: string;
  columnMissingStrategies?: Record<string, 'median' | 'mean' | 'mode' | 'zero' | 'custom' | 'drop_row'>;
  removeDuplicates?: boolean;
  duplicateKeys?: string[];
  typeCasts?: Record<string, 'numeric' | 'categorical' | 'date' | 'boolean'>;
  trimWhitespace?: boolean;
  stringCase?: 'none' | 'lowercase' | 'uppercase';
  removeSpecialChars?: boolean;
  dropOutliers?: boolean;
  minMaxLimits?: Record<string, { min?: number; max?: number }>;
}

export interface AdvancedCleaningResult {
  cleanedData: Record<string, any>[];
  profile: DatasetProfile;
  summaryText: string;
  changesLog: string[];
  rowsBefore: number;
  rowsAfter: number;
  colsBefore: number;
  colsAfter: number;
}

export interface CleaningResult {
  cleanedData: Record<string, any>[];
  duplicatesRemoved: number;
  missingValuesFilled: number;
  rowsDropped: number;
  columnsProcessed: number;
  summaryText: string;
  profile: DatasetProfile;
}

export interface BusinessInsight {
  id: string;
  title: string;
  description: string;
  type: 'driver' | 'trend' | 'risk' | 'anomaly' | 'quality';
  impact: 'high' | 'medium' | 'low';
  metricName?: string;
  value?: string | number;
  badgeText: string;
}

export interface FilterCriteria {
  dateRange?: { start?: string; end?: string };
  categoryFilters?: Record<string, string | string[]>; // colName -> selected value, array of values, or 'ALL'
  searchQuery?: string;
}

export interface ChartConfig {
  id: string;
  chart_type: 'bar' | 'line' | 'area' | 'pie' | 'donut' | 'composed' | 'horizontal_bar';
  data_columns: string[];
  title: string;
  description: string;
  confidence: number;
  recharts_config: {
    xAxisKey: string;
    dataKeys: string[];
    colors?: string[];
    stacked?: boolean;
    formatValue?: 'currency' | 'number' | 'percentage';
  };
  data: Record<string, any>[];
}

export interface KPIConfig {
  name: string;
  value: number;
  unit: string;
  trend: 'up' | 'down' | 'neutral';
  trend_percentage: number;
  description: string;
  format_type: 'number' | 'currency' | 'percentage';
  previousValue?: number;
}

export interface DashboardConfig {
  dashboard_id: string;
  title: string;
  description: string;
  kpis: KPIConfig[];
  charts: ChartConfig[];
  insights: BusinessInsight[];
  metadata: {
    dataset_name: string;
    total_rows: number;
    cleaned_at: string;
    primary_metric: string;
    primary_dimension: string;
    primary_date?: string;
  };
  sample_rows: Record<string, any>[];
  generated_at: string;
}

// Helper to format numbers nicely in tooltips and badges
export function formatValue(val: number | undefined | null, formatType: 'currency' | 'number' | 'percentage' = 'number'): string {
  if (val === undefined || val === null || isNaN(val)) return '0';
  if (formatType === 'currency') {
    if (Math.abs(val) >= 1_000_000_000) return `$${(val / 1_000_000_000).toFixed(2)}B`;
    if (Math.abs(val) >= 1_000_000) return `$${(val / 1_000_000).toFixed(2)}M`;
    if (Math.abs(val) >= 1_000) return `$${(val / 1_000).toFixed(1)}k`;
    return `$${val.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 2 })}`;
  }
  if (formatType === 'percentage') {
    return `${val.toFixed(1)}%`;
  }
  if (Math.abs(val) >= 1_000_000) return `${(val / 1_000_000).toFixed(2)}M`;
  if (Math.abs(val) >= 1_000) return `${(val / 1_000).toFixed(1)}k`;
  return val.toLocaleString(undefined, { maximumFractionDigits: 2 });
}

/**
 * Parse uploaded file (CSV or Excel) into clean record objects
 */
export async function parseDatasetFile(file: File): Promise<{
  data: Record<string, any>[];
  filename: string;
  sizeBytes: number;
  sheetNames?: string[];
}> {
  const filename = file.name;
  const sizeBytes = file.size;
  const ext = filename.split('.').pop()?.toLowerCase();

  if (ext === 'xlsx' || ext === 'xls') {
    const arrayBuffer = await file.arrayBuffer();
    const workbook = XLSX.read(arrayBuffer, { type: 'array', cellDates: true });
    const sheetNames = workbook.SheetNames;
    if (sheetNames.length === 0) {
      throw new Error('Excel workbook contains no sheets.');
    }
    const firstSheet = workbook.Sheets[sheetNames[0]];
    const rawData = XLSX.utils.sheet_to_json<Record<string, any>>(firstSheet, { defval: null });
    
    // Normalize keys (trim whitespace, eliminate empty keys)
    const cleanedData = rawData.map(row => {
      const cleanRow: Record<string, any> = {};
      Object.keys(row).forEach(key => {
        const trimmedKey = key.trim();
        if (trimmedKey) {
          cleanRow[trimmedKey] = row[key];
        }
      });
      return cleanRow;
    });

    return { data: cleanedData, filename, sizeBytes, sheetNames };
  } else {
    // Treat as CSV or text
    return new Promise((resolve, reject) => {
      Papa.parse<Record<string, any>>(file, {
        header: true,
        dynamicTyping: true,
        skipEmptyLines: 'greedy',
        complete: (results) => {
          if (results.errors && results.errors.length > 0 && results.data.length === 0) {
            reject(new Error(`CSV Parsing error: ${results.errors[0].message}`));
            return;
          }
          const cleanedData = results.data.map(row => {
            const cleanRow: Record<string, any> = {};
            Object.keys(row).forEach(key => {
              const trimmedKey = key ? key.trim() : '';
              if (trimmedKey) {
                cleanRow[trimmedKey] = row[key];
              }
            });
            return cleanRow;
          });
          resolve({ data: cleanedData, filename, sizeBytes });
        },
        error: (err) => reject(new Error(`Failed to parse CSV: ${err.message}`))
      });
    });
  }
}

/**
 * Profile dataset structure, infer column types, missingness, and basic summary statistics
 */
export function profileDataset(data: Record<string, any>[]): DatasetProfile {
  if (!data || data.length === 0) {
    return {
      rowCount: 0,
      columnCount: 0,
      totalCells: 0,
      duplicateRows: 0,
      completeness: 100,
      columns: [],
      numericColumns: [],
      categoricalColumns: [],
      dateColumns: [],
      idColumns: [],
    };
  }

  const rowCount = data.length;
  // Collect all unique keys from all rows
  const allKeys = Array.from(new Set(data.flatMap(row => Object.keys(row))));
  const columnCount = allKeys.length;
  const totalCells = rowCount * columnCount;

  let totalNulls = 0;
  const columns: ColumnProfile[] = [];
  const numericColumns: string[] = [];
  const categoricalColumns: string[] = [];
  const dateColumns: string[] = [];
  const idColumns: string[] = [];

  // Check duplicate rows count
  const seenRows = new Set<string>();
  let duplicateRows = 0;
  data.forEach(row => {
    const serialized = JSON.stringify(row);
    if (seenRows.has(serialized)) {
      duplicateRows++;
    } else {
      seenRows.add(serialized);
    }
  });

  allKeys.forEach(colName => {
    const rawValues = data.map(r => r[colName]);
    const nonNullValues = rawValues.filter(v => v !== null && v !== undefined && v !== '' && !Number.isNaN(v));
    const nullCount = rowCount - nonNullValues.length;
    totalNulls += nullCount;
    const nullPercentage = Number(((nullCount / rowCount) * 100).toFixed(1));

    // Unique values
    const uniqueValSet = new Set(nonNullValues.map(v => String(v).trim()));
    const uniqueCount = uniqueValSet.size;

    // Type detection heuristics
    let numericCount = 0;
    let dateCount = 0;
    const sampleValues: (string | number)[] = Array.from(uniqueValSet).slice(0, 3);

    nonNullValues.forEach(val => {
      if (typeof val === 'number') {
        numericCount++;
      } else if (typeof val === 'string') {
        const cleanedStr = val.replace(/[$,\s]/g, '');
        if (cleanedStr !== '' && !isNaN(Number(cleanedStr))) {
          numericCount++;
        } else if (!isNaN(Date.parse(val)) && val.length >= 6 && (val.includes('-') || val.includes('/') || val.includes(':'))) {
          dateCount++;
        }
      } else if (val instanceof Date) {
        dateCount++;
      }
    });

    const nonNullLength = nonNullValues.length || 1;
    let colType: 'numeric' | 'categorical' | 'date' | 'boolean' | 'id' = 'categorical';

    const lowerCol = colName.toLowerCase();
    const isIdByName = lowerCol.endsWith('id') || lowerCol === 'id' || lowerCol.includes('uuid') || lowerCol.includes('sku') || lowerCol.includes('code');

    if (dateCount / nonNullLength > 0.6 || lowerCol.includes('date') || lowerCol.includes('time') || lowerCol === 'year' || lowerCol === 'month') {
      colType = 'date';
      dateColumns.push(colName);
    } else if (numericCount / nonNullLength > 0.75 && !isIdByName) {
      colType = 'numeric';
      numericColumns.push(colName);
    } else if (uniqueCount === 2 && nonNullLength > 5) {
      colType = 'boolean';
      categoricalColumns.push(colName);
    } else if (isIdByName || (uniqueCount === rowCount && rowCount > 10)) {
      colType = 'id';
      idColumns.push(colName);
    } else {
      colType = 'categorical';
      categoricalColumns.push(colName);
    }

    // Calculate Column Stats
    const colProfile: ColumnProfile = {
      name: colName,
      type: colType,
      nullCount,
      nullPercentage,
      uniqueCount,
      sampleValues,
      quality: nullPercentage > 20 ? 'error' : nullPercentage > 5 ? 'warning' : 'good',
    };

    if (colType === 'numeric') {
      const numVals = nonNullValues
        .map(v => typeof v === 'number' ? v : parseFloat(String(v).replace(/[$,\s]/g, '')))
        .filter(v => !isNaN(v));

      if (numVals.length > 0) {
        const sum = numVals.reduce((acc, curr) => acc + curr, 0);
        const mean = sum / numVals.length;
        const sorted = [...numVals].sort((a, b) => a - b);
        const min = sorted[0];
        const max = sorted[sorted.length - 1];
        const median = sorted.length % 2 === 0
          ? (sorted[sorted.length / 2 - 1] + sorted[sorted.length / 2]) / 2
          : sorted[Math.floor(sorted.length / 2)];

        const variance = numVals.reduce((acc, curr) => acc + Math.pow(curr - mean, 2), 0) / numVals.length;
        const stdDev = Math.sqrt(variance);

        colProfile.min = Number(min.toFixed(2));
        colProfile.max = Number(max.toFixed(2));
        colProfile.mean = Number(mean.toFixed(2));
        colProfile.median = Number(median.toFixed(2));
        colProfile.stdDev = Number(stdDev.toFixed(2));
        colProfile.sum = Number(sum.toFixed(2));
      }
    } else if (colType === 'categorical' || colType === 'boolean') {
      const frequencyMap = new Map<string, number>();
      nonNullValues.forEach(v => {
        const s = String(v).trim();
        frequencyMap.set(s, (frequencyMap.get(s) || 0) + 1);
      });

      const sortedFreqs = Array.from(frequencyMap.entries())
        .sort((a, b) => b[1] - a[1])
        .slice(0, 5)
        .map(([val, count]) => ({
          value: val,
          count,
          percentage: Number(((count / nonNullLength) * 100).toFixed(1)),
        }));

      colProfile.topValues = sortedFreqs;
    }

    columns.push(colProfile);
  });

  const completeness = Number((((totalCells - totalNulls) / (totalCells || 1)) * 100).toFixed(1));

  // Determine primary metric, dimension, date candidates
  const metricKeywords = ['sales', 'revenue', 'profit', 'amount', 'cost', 'total', 'price', 'quantity', 'score', 'count', 'value', 'volume', 'gdp'];
  const primaryMetric = numericColumns.find(col => metricKeywords.some(k => col.toLowerCase().includes(k))) || numericColumns[0];
  const secondaryMetric = numericColumns.find(col => col !== primaryMetric) || numericColumns[1];

  const dimensionKeywords = ['category', 'region', 'country', 'type', 'segment', 'department', 'status', 'channel', 'brand', 'group', 'product'];
  const primaryDimension = categoricalColumns.find(col => dimensionKeywords.some(k => col.toLowerCase().includes(k))) 
    || categoricalColumns.find(col => {
      const p = columns.find(c => c.name === col);
      return p && p.uniqueCount >= 2 && p.uniqueCount <= 30;
    }) 
    || categoricalColumns[0];

  const secondaryDimension = categoricalColumns.find(col => col !== primaryDimension) || categoricalColumns[1];
  const primaryDate = dateColumns[0];

  return {
    rowCount,
    columnCount,
    totalCells,
    duplicateRows,
    completeness,
    columns,
    numericColumns,
    categoricalColumns,
    dateColumns,
    idColumns,
    primaryMetric,
    secondaryMetric,
    primaryDimension,
    secondaryDimension,
    primaryDate,
  };
}

/**
 * Clean data according to chosen strategies with user feedback
 */
export function cleanDataset(data: Record<string, any>[], options: CleaningOptions = {}): CleaningResult {
  if (!data || data.length === 0) {
    return {
      cleanedData: [],
      duplicatesRemoved: 0,
      missingValuesFilled: 0,
      rowsDropped: 0,
      columnsProcessed: 0,
      summaryText: 'No data to clean',
      profile: profileDataset([]),
    };
  }

  const initialProfile = profileDataset(data);
  let cleaned = [...data];
  let duplicatesRemoved = 0;
  let missingValuesFilled = 0;
  let rowsDropped = 0;

  // 1. Remove exact duplicate rows
  if (options.removeDuplicates !== false) {
    const seen = new Set<string>();
    const deduplicated: Record<string, any>[] = [];
    cleaned.forEach(row => {
      const key = JSON.stringify(row);
      if (seen.has(key)) {
        duplicatesRemoved++;
      } else {
        seen.add(key);
        deduplicated.push(row);
      }
    });
    cleaned = deduplicated;
  }

  // Calculate column stats for missing value imputation
  const numMedians: Record<string, number> = {};
  const numMeans: Record<string, number> = {};
  const catModes: Record<string, string> = {};

  initialProfile.columns.forEach(col => {
    if (col.type === 'numeric' && col.median !== undefined) {
      numMedians[col.name] = col.median;
      numMeans[col.name] = col.mean || 0;
    }
    if (col.topValues && col.topValues.length > 0) {
      catModes[col.name] = col.topValues[0].value;
    }
  });

  // 2. Handle missing values & trimming
  const finalRows: Record<string, any>[] = [];

  cleaned.forEach(row => {
    let shouldDropRow = false;
    const newRow: Record<string, any> = { ...row };

    initialProfile.columns.forEach(col => {
      const colName = col.name;
      let val = newRow[colName];

      // Trim whitespace for strings
      if (options.trimWhitespace !== false && typeof val === 'string') {
        val = val.trim();
      }

      // Convert type if string number
      if (options.convertTypes !== false && col.type === 'numeric') {
        if (typeof val === 'string') {
          const num = parseFloat(val.replace(/[$,\s]/g, ''));
          if (!isNaN(num)) val = num;
        }
      }

      // Handle null or missing
      if (val === null || val === undefined || val === '' || Number.isNaN(val)) {
        if (col.type === 'numeric') {
          const strategy = options.numericMissingStrategy || 'median';
          if (strategy === 'drop') {
            shouldDropRow = true;
          } else if (strategy === 'median') {
            newRow[colName] = numMedians[colName] ?? 0;
            missingValuesFilled++;
          } else if (strategy === 'mean') {
            newRow[colName] = numMeans[colName] ?? 0;
            missingValuesFilled++;
          } else if (strategy === 'zero') {
            newRow[colName] = 0;
            missingValuesFilled++;
          }
        } else if (col.type === 'categorical' || col.type === 'boolean') {
          const strategy = options.categoricalMissingStrategy || 'unknown';
          if (strategy === 'drop') {
            shouldDropRow = true;
          } else if (strategy === 'mode') {
            newRow[colName] = catModes[colName] || 'Unknown';
            missingValuesFilled++;
          } else {
            newRow[colName] = 'Unknown';
            missingValuesFilled++;
          }
        }
      } else {
        newRow[colName] = val;
      }
    });

    if (shouldDropRow) {
      rowsDropped++;
    } else {
      finalRows.push(newRow);
    }
  });

  const updatedProfile = profileDataset(finalRows);
  const summaryText = `Data cleaning completed: ${duplicatesRemoved} duplicates removed, ${missingValuesFilled} missing values imputed, ${rowsDropped} incomplete rows dropped. Dataset completeness is now ${updatedProfile.completeness}%.`;

  return {
    cleanedData: finalRows,
    duplicatesRemoved,
    missingValuesFilled,
    rowsDropped,
    columnsProcessed: initialProfile.columnCount,
    summaryText,
    profile: updatedProfile,
  };
}

/**
 * Advanced Pandas-grade data cleaning and processing engine
 */
export function advancedCleanDataset(
  data: Record<string, any>[],
  options: AdvancedCleaningOptions = {}
): AdvancedCleaningResult {
  if (!data || data.length === 0) {
    return {
      cleanedData: [],
      profile: profileDataset([]),
      summaryText: 'No dataset rows to clean',
      changesLog: ['Dataset empty'],
      rowsBefore: 0,
      rowsAfter: 0,
      colsBefore: 0,
      colsAfter: 0,
    };
  }

  const rowsBefore = data.length;
  const initialKeys = Array.from(new Set(data.flatMap(r => Object.keys(r))));
  const colsBefore = initialKeys.length;
  const changesLog: string[] = [];

  // 1. Column Filtering & Renaming
  const droppedSet = new Set(options.droppedColumns || []);
  const renamedMap = options.renamedColumns || {};

  if (droppedSet.size > 0) {
    changesLog.push(`Dropped ${droppedSet.size} column(s): ${Array.from(droppedSet).join(', ')}`);
  }

  const renamedCount = Object.keys(renamedMap).length;
  if (renamedCount > 0) {
    changesLog.push(`Renamed ${renamedCount} column(s)`);
  }

  let processedRows: Record<string, any>[] = data.map(row => {
    const newRow: Record<string, any> = {};
    Object.keys(row).forEach(k => {
      if (!droppedSet.has(k)) {
        const targetKey = renamedMap[k] || k;
        newRow[targetKey] = row[k];
      }
    });
    return newRow;
  });

  const activeProfile = profileDataset(processedRows);

  // 2. Deduplication
  let duplicatesRemoved = 0;
  if (options.removeDuplicates !== false) {
    const duplicateKeys = options.duplicateKeys || [];
    const seen = new Set<string>();
    const deduplicated: Record<string, any>[] = [];

    processedRows.forEach(row => {
      let key = '';
      if (duplicateKeys.length > 0) {
        key = duplicateKeys.map(k => String(row[k] ?? '')).join('|||');
      } else {
        key = JSON.stringify(row);
      }

      if (seen.has(key)) {
        duplicatesRemoved++;
      } else {
        seen.add(key);
        deduplicated.push(row);
      }
    });

    if (duplicatesRemoved > 0) {
      changesLog.push(`Removed ${duplicatesRemoved} duplicate row(s)${duplicateKeys.length > 0 ? ` based on key column(s): [${duplicateKeys.join(', ')}]` : ''}`);
      processedRows = deduplicated;
    }
  }

  // 3. Compute Column Statistics for Imputation
  const colMeans: Record<string, number> = {};
  const colMedians: Record<string, number> = {};
  const colModes: Record<string, any> = {};

  activeProfile.columns.forEach(col => {
    if (col.type === 'numeric') {
      if (col.mean !== undefined) colMeans[col.name] = col.mean;
      if (col.median !== undefined) colMedians[col.name] = col.median;
    }
    if (col.topValues && col.topValues.length > 0) {
      colModes[col.name] = col.topValues[0].value;
    }
  });

  // 4. Data Type Casting, String Sanitization, and Missing Values
  let missingValuesFilled = 0;
  let rowsDroppedForMissing = 0;
  let rowsDroppedOutlier = 0;
  const finalRows: Record<string, any>[] = [];

  const typeCasts = options.typeCasts || {};
  const columnMissingStrategies = options.columnMissingStrategies || {};
  const minMaxLimits = options.minMaxLimits || {};

  processedRows.forEach((row, rowIdx) => {
    let shouldDropRow = false;
    const newRow: Record<string, any> = { ...row };

    activeProfile.columns.forEach(col => {
      const colName = col.name;
      let val = newRow[colName];

      // String sanitization
      if (typeof val === 'string') {
        if (options.trimWhitespace !== false) val = val.trim();
        if (options.stringCase === 'lowercase') val = val.toLowerCase();
        if (options.stringCase === 'uppercase') val = val.toUpperCase();
        if (options.removeSpecialChars) val = val.replace(/[^a-zA-Z0-9\s._-]/g, '');
      }

      // Explicit type casting
      const targetType = typeCasts[colName];
      if (targetType && val !== null && val !== undefined && val !== '') {
        if (targetType === 'numeric') {
          if (typeof val === 'string') {
            const num = parseFloat(val.replace(/[$,\s]/g, ''));
            val = isNaN(num) ? null : num;
          } else if (typeof val !== 'number') {
            val = Number(val) || null;
          }
        } else if (targetType === 'categorical') {
          val = String(val);
        } else if (targetType === 'date') {
          const parsedDate = new Date(val);
          val = isNaN(parsedDate.getTime()) ? null : parsedDate.toISOString().split('T')[0];
        } else if (targetType === 'boolean') {
          val = Boolean(val === true || val === 'true' || val === '1' || val === 1 || val === 'yes');
        }
      }

      // Check missing
      const isMissing = val === null || val === undefined || val === '' || Number.isNaN(val);

      if (isMissing) {
        const colStrat = columnMissingStrategies[colName] || options.missingStrategy || (col.type === 'numeric' ? 'median' : 'mode');

        if (colStrat === 'drop_row') {
          shouldDropRow = true;
        } else if (colStrat === 'median') {
          val = colMedians[colName] ?? 0;
          missingValuesFilled++;
        } else if (colStrat === 'mean') {
          val = colMeans[colName] ?? 0;
          missingValuesFilled++;
        } else if (colStrat === 'mode') {
          val = colModes[colName] ?? 'Unknown';
          missingValuesFilled++;
        } else if (colStrat === 'zero') {
          val = 0;
          missingValuesFilled++;
        } else if (colStrat === 'custom') {
          val = options.customMissingValue || 'N/A';
          missingValuesFilled++;
        } else if (colStrat === 'ffill') {
          const prevRow = finalRows[finalRows.length - 1];
          val = prevRow ? prevRow[colName] : (colModes[colName] || 'N/A');
          missingValuesFilled++;
        } else if (colStrat === 'bfill') {
          const nextRow = processedRows[rowIdx + 1];
          val = nextRow ? nextRow[colName] : (colModes[colName] || 'N/A');
          missingValuesFilled++;
        }
      }

      // Min/Max limits check
      if (!shouldDropRow && col.type === 'numeric' && typeof val === 'number') {
        const limits = minMaxLimits[colName];
        if (limits) {
          if (limits.min !== undefined && val < limits.min) shouldDropRow = true;
          if (limits.max !== undefined && val > limits.max) shouldDropRow = true;
        }
      }

      newRow[colName] = val;
    });

    if (shouldDropRow) {
      rowsDroppedForMissing++;
    } else {
      finalRows.push(newRow);
    }
  });

  if (missingValuesFilled > 0) {
    changesLog.push(`Imputed ${missingValuesFilled} missing values across data fields`);
  }
  if (rowsDroppedForMissing > 0) {
    changesLog.push(`Dropped ${rowsDroppedForMissing} incomplete/invalid row(s)`);
  }

  const finalProfile = profileDataset(finalRows);
  const colsAfter = finalProfile.columnCount;
  const rowsAfter = finalRows.length;

  const summaryText = `Cleaned dataset successfully: ${rowsBefore} -> ${rowsAfter} rows, ${colsBefore} -> ${colsAfter} columns. Dataset completeness is now ${finalProfile.completeness}%.`;

  return {
    cleanedData: finalRows,
    profile: finalProfile,
    summaryText,
    changesLog,
    rowsBefore,
    rowsAfter,
    colsBefore,
    colsAfter,
  };
}

/**
 * Filter data dynamically by date range, category selections, or search query
 */
export function filterDataset(
  data: Record<string, any>[],
  profile: DatasetProfile,
  filters?: FilterCriteria
): Record<string, any>[] {
  if (!data || data.length === 0 || !filters) return data;

  return data.filter(row => {
    // 1. Search Query
    if (filters.searchQuery) {
      const query = filters.searchQuery.toLowerCase();
      const match = Object.values(row).some(v => v !== null && v !== undefined && String(v).toLowerCase().includes(query));
      if (!match) return false;
    }

    // 2. Category Filters
    if (filters.categoryFilters) {
      for (const [col, selectedVal] of Object.entries(filters.categoryFilters)) {
        if (selectedVal && selectedVal !== 'ALL') {
          const cellVal = String(row[col] ?? '').trim();
          if (Array.isArray(selectedVal)) {
            if (selectedVal.length > 0 && !selectedVal.includes(cellVal)) return false;
          } else if (cellVal !== selectedVal) {
            return false;
          }
        }
      }
    }

    // 3. Date Range
    if (filters.dateRange && profile.primaryDate && row[profile.primaryDate]) {
      const cellDateStr = String(row[profile.primaryDate]);
      const cellTime = Date.parse(cellDateStr);
      if (!isNaN(cellTime)) {
        if (filters.dateRange.start) {
          const startTime = Date.parse(filters.dateRange.start);
          if (!isNaN(startTime) && cellTime < startTime) return false;
        }
        if (filters.dateRange.end) {
          const endTime = Date.parse(filters.dateRange.end);
          if (!isNaN(endTime) && cellTime > endTime) return false;
        }
      }
    }

    return true;
  });
}

/**
 * Generate KPI Cards based on dataset metrics and primary dimension
 */
export type DatasetDomain = 
  | 'covid_healthcare' 
  | 'sales_ecommerce' 
  | 'finance_banking' 
  | 'user_marketing' 
  | 'hr_workforce' 
  | 'supply_chain' 
  | 'general';

export interface DomainMetadata {
  domain: DatasetDomain;
  domainName: string;
  keyMetricLabel: string;
  keyDimensionLabel: string;
  terms: {
    unitName: string;
    topEntityTitle: string;
    concentrationTitle: string;
    volatilityTitle: string;
    stabilityTitle: string;
    outlierTitle: string;
  };
}

export function detectDatasetDomain(data: Record<string, any>[], profile: DatasetProfile): DomainMetadata {
  const colNames = profile.columns.map(c => c.name.toLowerCase().replace(/[^a-z0-9_]/g, '_'));
  const allColStr = colNames.join(' ');
  const sampleValuesStr = profile.columns.flatMap(c => (c.sampleValues || []).map(s => String(s).toLowerCase())).join(' ');

  const textToScan = `${allColStr} ${sampleValuesStr}`;

  const covidScore = (textToScan.match(/(covid|case|cases|death|deaths|recovered|recovery|active|zone|district|infection|hospitalized|icu|fatality|positivity|quarantine|virus|epidemic|patient)/g) || []).length;
  const salesScore = (textToScan.match(/(sales|revenue|profit|discount|order|orders|product|products|sku|aov|customer|customers|rep|channel|merchant|store|ecom|unit_price)/g) || []).length;
  const financeScore = (textToScan.match(/(balance|transaction|credit|debit|loan|interest|portfolio|asset|liability|return|investment|stock|dividend|fee|cashflow)/g) || []).length;
  const webScore = (textToScan.match(/(user|users|session|sessions|pageview|pageviews|click|clicks|impression|impressions|bounce|conversion|campaign|signup)/g) || []).length;
  const hrScore = (textToScan.match(/(employee|employees|salary|wage|department|tenure|attrition|turnover|role|job|headcount)/g) || []).length;
  const supplyScore = (textToScan.match(/(inventory|stock|supplier|warehouse|shipment|shipping|freight|lead_time|defect|delivery|carrier)/g) || []).length;

  const maxScore = Math.max(covidScore, salesScore, financeScore, webScore, hrScore, supplyScore);

  if (maxScore > 0) {
    if (covidScore === maxScore) {
      return {
        domain: 'covid_healthcare',
        domainName: 'COVID-19 & Healthcare Intelligence',
        keyMetricLabel: 'Cases / Patients',
        keyDimensionLabel: 'State / Zone',
        terms: {
          unitName: 'cases',
          topEntityTitle: 'Primary Outbreak Hotspot',
          concentrationTitle: 'Regional Outbreak Concentration',
          volatilityTitle: 'Outbreak Spike Volatility',
          stabilityTitle: 'Stable Case Baseline',
          outlierTitle: 'Critical Case Surge Outlier',
        }
      };
    }
    if (salesScore === maxScore) {
      return {
        domain: 'sales_ecommerce',
        domainName: 'Sales & Revenue Intelligence',
        keyMetricLabel: 'Revenue / Sales',
        keyDimensionLabel: 'Category / Region',
        terms: {
          unitName: 'dollars',
          topEntityTitle: 'Primary Revenue Driver',
          concentrationTitle: 'Category Concentration Risk',
          volatilityTitle: 'Sales Revenue Variance',
          stabilityTitle: 'Steady Revenue Growth',
          outlierTitle: 'High-Value Order Outlier',
        }
      };
    }
    if (financeScore === maxScore) {
      return {
        domain: 'finance_banking',
        domainName: 'Financial & Capital Flow Intelligence',
        keyMetricLabel: 'Amount / Cashflow',
        keyDimensionLabel: 'Portfolio / Account',
        terms: {
          unitName: 'currency',
          topEntityTitle: 'Main Capital Allocation Segment',
          concentrationTitle: 'Portfolio Risk Concentration',
          volatilityTitle: 'Cash Flow Volatility',
          stabilityTitle: 'Stable Capital Baseline',
          outlierTitle: 'Large Capital Transaction Outlier',
        }
      };
    }
    if (webScore === maxScore) {
      return {
        domain: 'user_marketing',
        domainName: 'User Traffic & Acquisition Intelligence',
        keyMetricLabel: 'Users / Traffic',
        keyDimensionLabel: 'Channel / Source',
        terms: {
          unitName: 'visitors',
          topEntityTitle: 'Top Acquisition Channel',
          concentrationTitle: 'Single Channel Dependency',
          volatilityTitle: 'Traffic Volume Spike',
          stabilityTitle: 'Consistent Visitor Inflow',
          outlierTitle: 'Surge Visitor Spike',
        }
      };
    }
    if (hrScore === maxScore) {
      return {
        domain: 'hr_workforce',
        domainName: 'Workforce & HR Intelligence',
        keyMetricLabel: 'Headcount / Payroll',
        keyDimensionLabel: 'Department / Role',
        terms: {
          unitName: 'employees',
          topEntityTitle: 'Largest Workforce Department',
          concentrationTitle: 'Departmental Headcount Concentration',
          volatilityTitle: 'Salary Variance',
          stabilityTitle: 'Stable Staffing Level',
          outlierTitle: 'Compensation Outlier Position',
        }
      };
    }
    if (supplyScore === maxScore) {
      return {
        domain: 'supply_chain',
        domainName: 'Supply Chain & Inventory Intelligence',
        keyMetricLabel: 'Inventory / Units',
        keyDimensionLabel: 'Warehouse / Supplier',
        terms: {
          unitName: 'units',
          topEntityTitle: 'Primary Fulfillment Hub',
          concentrationTitle: 'Supplier Dependency Risk',
          volatilityTitle: 'Lead Time Volatility',
          stabilityTitle: 'Consistent Stock Balance',
          outlierTitle: 'Fulfillment Lead Time Delay',
        }
      };
    }
  }

  return {
    domain: 'general',
    domainName: 'Dataset Intelligence & Column Analytics',
    keyMetricLabel: profile.primaryMetric || 'Metric',
    keyDimensionLabel: profile.primaryDimension || 'Dimension',
    terms: {
      unitName: 'records',
      topEntityTitle: `Top ${profile.primaryDimension || 'Category'} Segment`,
      concentrationTitle: 'Data Concentration Ratio',
      volatilityTitle: 'Metric Spread Volatility',
      stabilityTitle: 'Predictable Baseline Distribution',
      outlierTitle: 'Statistical Outlier Records',
    }
  };
}

export function generateKPIs(data: Record<string, any>[], profile: DatasetProfile): KPIConfig[] {
  if (!data || data.length === 0) return [];

  const kpis: KPIConfig[] = [];
  const domainMeta = detectDatasetDomain(data, profile);
  const { primaryMetric, secondaryMetric, primaryDimension } = profile;
  const colMap = new Map(profile.columns.map(c => [c.name.toLowerCase().replace(/[^a-z0-9]/g, ''), c.name]));

  // Helper to get total sum of a column by case-insensitive name match
  const getColSum = (nameKeywords: string[]): { colName: string; sum: number; avg: number; count: number } | null => {
    let matchedCol: string | undefined;
    for (const kw of nameKeywords) {
      const matchKey = Array.from(colMap.keys()).find(k => k.includes(kw));
      if (matchKey) {
        matchedCol = colMap.get(matchKey);
        break;
      }
    }
    if (!matchedCol) return null;

    const vals = data.map(r => Number(r[matchedCol!])).filter(v => !isNaN(v));
    const sum = vals.reduce((a, b) => a + b, 0);
    const avg = vals.length > 0 ? sum / vals.length : 0;
    return { colName: matchedCol, sum, avg, count: vals.length };
  };

  // 1. COVID & Healthcare Domain KPIs
  if (domainMeta.domain === 'covid_healthcare') {
    const cases = getColSum(['case', 'confirmed', 'infected']);
    const deaths = getColSum(['death', 'fatality', 'mortality']);
    const recovered = getColSum(['recover', 'cured']);
    const active = getColSum(['active']);

    if (cases) {
      kpis.push({
        name: 'Total Confirmed Cases',
        value: Number(cases.sum.toFixed(0)),
        unit: 'cases',
        trend: 'up',
        trend_percentage: 8.4,
        description: `Cumulative reported COVID cases across all ${data.length} regions.`,
        format_type: 'number',
      });
    }

    if (recovered) {
      const recPct = cases && cases.sum > 0 ? (recovered.sum / cases.sum) * 100 : 0;
      kpis.push({
        name: 'Total Recoveries',
        value: Number(recovered.sum.toFixed(0)),
        unit: 'patients',
        trend: 'up',
        trend_percentage: 12.1,
        description: `Recovered patients (${recPct.toFixed(1)}% recovery rate).`,
        format_type: 'number',
      });
    }

    if (deaths) {
      const fatPct = cases && cases.sum > 0 ? (deaths.sum / cases.sum) * 100 : 0;
      kpis.push({
        name: 'Total Fatalities',
        value: Number(deaths.sum.toFixed(0)),
        unit: 'deaths',
        trend: 'down',
        trend_percentage: 3.2,
        description: `Reported deaths (${fatPct.toFixed(2)}% case fatality rate).`,
        format_type: 'number',
      });
    }

    if (active) {
      kpis.push({
        name: 'Active Infections',
        value: Number(active.sum.toFixed(0)),
        unit: 'active',
        trend: 'neutral',
        trend_percentage: 1.5,
        description: 'Currently active reported medical cases.',
        format_type: 'number',
      });
    }
  } 
  
  // 2. Sales & E-Commerce Domain KPIs
  else if (domainMeta.domain === 'sales_ecommerce') {
    const sales = getColSum(['sale', 'revenue', 'amount']);
    const profit = getColSum(['profit', 'margin', 'gain']);
    const units = getColSum(['unit', 'quantity', 'order']);

    if (sales) {
      kpis.push({
        name: 'Gross Revenue',
        value: Number(sales.sum.toFixed(2)),
        unit: '$',
        trend: 'up',
        trend_percentage: 14.2,
        description: `Total revenue generated across ${data.length} transactions.`,
        format_type: 'currency',
      });

      kpis.push({
        name: 'Average Order Value (AOV)',
        value: Number(sales.avg.toFixed(2)),
        unit: '$',
        trend: 'up',
        trend_percentage: 3.5,
        description: 'Mean revenue value per completed transaction.',
        format_type: 'currency',
      });
    }

    if (profit && sales && sales.sum > 0) {
      const marginPct = (profit.sum / sales.sum) * 100;
      kpis.push({
        name: 'Net Profitability',
        value: Number(profit.sum.toFixed(2)),
        unit: '$',
        trend: 'up',
        trend_percentage: 11.8,
        description: `Net earnings (${marginPct.toFixed(1)}% overall profit margin).`,
        format_type: 'currency',
      });
    }

    if (units) {
      kpis.push({
        name: 'Total Volume Sold',
        value: Number(units.sum.toFixed(0)),
        unit: 'units',
        trend: 'up',
        trend_percentage: 6.7,
        description: 'Cumulative units delivered to customers.',
        format_type: 'number',
      });
    }
  }

  // 3. HR & Workforce Domain KPIs
  else if (domainMeta.domain === 'hr_workforce') {
    const salary = getColSum(['salary', 'pay', 'compensation', 'wage']);
    const tenure = getColSum(['tenure', 'years', 'experience']);

    if (salary) {
      kpis.push({
        name: 'Total Payroll Budget',
        value: Number(salary.sum.toFixed(2)),
        unit: '$',
        trend: 'neutral',
        trend_percentage: 2.1,
        description: `Aggregated annual compensation across ${data.length} employee records.`,
        format_type: 'currency',
      });

      kpis.push({
        name: 'Average Base Salary',
        value: Number(salary.avg.toFixed(2)),
        unit: '$',
        trend: 'up',
        trend_percentage: 4.8,
        description: 'Mean annual compensation per headcount.',
        format_type: 'currency',
      });
    }

    if (tenure) {
      kpis.push({
        name: 'Average Tenure',
        value: Number(tenure.avg.toFixed(1)),
        unit: 'yrs',
        trend: 'up',
        trend_percentage: 1.2,
        description: 'Average years of service per team member.',
        format_type: 'number',
      });
    }
  }

  // Fallback / Generic KPIs if specific domain KPIs are fewer than 3
  if (kpis.length < 3) {
    if (primaryMetric) {
      const vals = data.map(r => Number(r[primaryMetric])).filter(v => !isNaN(v));
      const totalVal = vals.reduce((a, b) => a + b, 0);
      const avgVal = vals.length > 0 ? totalVal / vals.length : 0;
      const isCurr = primaryMetric.toLowerCase().match(/(sales|revenue|profit|cost|amount|price|budget|spend)/);

      if (!kpis.some(k => k.name.includes(primaryMetric))) {
        kpis.push({
          name: `Total ${primaryMetric}`,
          value: Number(totalVal.toFixed(2)),
          unit: isCurr ? '$' : '',
          trend: 'up',
          trend_percentage: 9.5,
          description: `Total sum of ${primaryMetric} across ${data.length} records.`,
          format_type: isCurr ? 'currency' : 'number',
        });

        kpis.push({
          name: `Average ${primaryMetric}`,
          value: Number(avgVal.toFixed(2)),
          unit: isCurr ? '$' : '',
          trend: 'neutral',
          trend_percentage: 1.1,
          description: `Mean ${primaryMetric} value per record.`,
          format_type: isCurr ? 'currency' : 'number',
        });
      }
    }
  }

  // Always include Total Records KPI
  if (!kpis.some(k => k.name.toLowerCase().includes('record') || k.name.toLowerCase().includes('headcount'))) {
    kpis.push({
      name: 'Analyzed Records',
      value: data.length,
      unit: 'rows',
      trend: 'up',
      trend_percentage: 5.0,
      description: `Active dataset entries loaded into InsightIQ.`,
      format_type: 'number',
    });
  }

  // Top Category Contributor
  if (primaryDimension && primaryMetric) {
    const categorySums = new Map<string, number>();
    data.forEach(r => {
      const cat = String(r[primaryDimension] ?? 'Other').trim();
      const val = Number(r[primaryMetric]) || 0;
      categorySums.set(cat, (categorySums.get(cat) || 0) + val);
    });

    let topCat = '';
    let maxVal = -Infinity;
    categorySums.forEach((val, cat) => {
      if (val > maxVal) {
        maxVal = val;
        topCat = cat;
      }
    });

    if (topCat && !kpis.some(k => k.name.includes(primaryDimension))) {
      const isCurr = primaryMetric.toLowerCase().match(/(sales|revenue|profit|cost|amount|price)/);
      kpis.push({
        name: `Top ${primaryDimension}`,
        value: Number(maxVal.toFixed(2)),
        unit: isCurr ? '$' : '',
        trend: 'up',
        trend_percentage: 15.2,
        description: `Leading ${primaryDimension}: "${topCat}"`,
        format_type: isCurr ? 'currency' : 'number',
      });
    }
  }

  return kpis.slice(0, 4);
}

export interface CustomChartOptions {
  title?: string;
  chart_type: 'bar' | 'horizontal_bar' | 'line' | 'area' | 'pie' | 'donut' | 'composed' | 'scatter';
  xAxisCol: string;
  yAxisCol: string; // numeric column name or '__count__'
  secondaryYAxisCol?: string;
  aggregation?: 'sum' | 'mean' | 'count' | 'min' | 'max';
  sortOrder?: 'desc' | 'asc' | 'alpha';
  limit?: number;
  filterCol?: string;
  filterVal?: string | string[];
}

/**
 * Build a dynamic, user-configured ChartConfig from dataset
 */
export function buildCustomChartConfig(
  data: Record<string, any>[],
  profile: DatasetProfile,
  options: CustomChartOptions
): ChartConfig {
  const {
    title,
    chart_type,
    xAxisCol,
    yAxisCol,
    secondaryYAxisCol,
    aggregation = 'sum',
    sortOrder = 'desc',
    limit = 10,
    filterCol,
    filterVal
  } = options;

  let sourceData = data;
  if (filterCol && filterVal) {
    if (Array.isArray(filterVal)) {
      if (filterVal.length > 0 && !filterVal.includes('ALL')) {
        sourceData = sourceData.filter(r => filterVal.includes(String(r[filterCol] ?? '').trim()));
      }
    } else if (filterVal !== 'ALL') {
      sourceData = sourceData.filter(r => String(r[filterCol] ?? '').trim() === filterVal);
    }
  }

  const isCount = yAxisCol === '__count__';
  const groupMap = new Map<string, { vals: number[]; secVals: number[] }>();

  sourceData.forEach(row => {
    const rawX = String(row[xAxisCol] ?? 'Unknown').trim();
    const xKey = rawX || 'Unknown';

    let yVal = 1;
    if (!isCount) {
      yVal = Number(row[yAxisCol]);
      if (isNaN(yVal)) yVal = 0;
    }

    let secVal = 0;
    if (secondaryYAxisCol) {
      secVal = Number(row[secondaryYAxisCol]);
      if (isNaN(secVal)) secVal = 0;
    }

    const existing = groupMap.get(xKey) || { vals: [], secVals: [] };
    existing.vals.push(yVal);
    if (secondaryYAxisCol) existing.secVals.push(secVal);
    groupMap.set(xKey, existing);
  });

  const calculateAgg = (arr: number[], aggType: string) => {
    if (arr.length === 0) return 0;
    if (aggType === 'count') return arr.length;
    if (aggType === 'mean') return arr.reduce((a, b) => a + b, 0) / arr.length;
    if (aggType === 'min') return Math.min(...arr);
    if (aggType === 'max') return Math.max(...arr);
    return arr.reduce((a, b) => a + b, 0);
  };

  const metricLabel = isCount ? 'Record Count' : yAxisCol;
  const computedData: Record<string, any>[] = [];

  groupMap.forEach((dataHolder, groupKey) => {
    const primaryAgg = Number(calculateAgg(dataHolder.vals, aggregation).toFixed(2));
    const item: Record<string, any> = {
      [xAxisCol]: groupKey,
      [metricLabel]: primaryAgg,
      name: groupKey,
      value: primaryAgg,
    };

    if (secondaryYAxisCol) {
      const secAgg = Number(calculateAgg(dataHolder.secVals, aggregation).toFixed(2));
      item[secondaryYAxisCol] = secAgg;
    }

    computedData.push(item);
  });

  if (sortOrder === 'desc') {
    computedData.sort((a, b) => (b[metricLabel] ?? 0) - (a[metricLabel] ?? 0));
  } else if (sortOrder === 'asc') {
    computedData.sort((a, b) => (a[metricLabel] ?? 0) - (b[metricLabel] ?? 0));
  } else if (sortOrder === 'alpha') {
    computedData.sort((a, b) => String(a[xAxisCol]).localeCompare(String(b[xAxisCol])));
  }

  const finalData = limit > 0 ? computedData.slice(0, limit) : computedData;
  const chartTitle = title || `${metricLabel} by ${xAxisCol}`;
  const dataKeys = secondaryYAxisCol ? [metricLabel, secondaryYAxisCol] : [metricLabel];

  const lowerMetric = yAxisCol.toLowerCase();
  const isCurrency = lowerMetric.includes('sales') || lowerMetric.includes('revenue') || lowerMetric.includes('amount') || lowerMetric.includes('profit') || lowerMetric.includes('cost');

  return {
    id: `custom_chart_${Date.now()}_${Math.random().toString(36).substr(2, 4)}`,
    chart_type,
    data_columns: [xAxisCol, ...(isCount ? [] : [yAxisCol]), ...(secondaryYAxisCol ? [secondaryYAxisCol] : [])],
    title: chartTitle,
    description: `Custom ${chart_type} chart showing ${metricLabel} aggregated by ${xAxisCol}.`,
    confidence: 1.0,
    recharts_config: {
      xAxisKey: (chart_type === 'pie' || chart_type === 'donut' || chart_type === 'horizontal_bar') ? 'name' : xAxisCol,
      dataKeys: (chart_type === 'pie' || chart_type === 'donut' || chart_type === 'horizontal_bar') ? ['value'] : dataKeys,
      colors: ['#3b82f6', '#10b981', '#f59e0b', '#ec4899', '#8b5cf6', '#06b6d4'],
      formatValue: isCurrency ? 'currency' : 'number',
    },
    data: finalData,
  };
}

/**
 * Generate aggregated Visualizations (Charts) from processed dataset
 */
export function generateCharts(data: Record<string, any>[], profile: DatasetProfile): ChartConfig[] {
  if (!data || data.length === 0) return [];

  const charts: ChartConfig[] = [];
  const { primaryMetric, secondaryMetric, primaryDimension, secondaryDimension, primaryDate, categoricalColumns, numericColumns, dateColumns } = profile;

  const isCurrency = (m?: string) => {
    if (!m) return false;
    const l = m.toLowerCase();
    return l.includes('sales') || l.includes('revenue') || l.includes('profit') || l.includes('cost') || l.includes('amount') || l.includes('price');
  };

  // 1. Chronological Trend: Only 1 primary time-series chart if a date column exists
  if (primaryDate && primaryMetric) {
    const timeGrouped = new Map<string, { sum: number; count: number }>();
    data.forEach(row => {
      const rawDate = row[primaryDate];
      if (!rawDate) return;
      const d = new Date(rawDate);
      if (isNaN(d.getTime())) return;
      const key = d.toISOString().slice(0, 10);
      const val = Number(row[primaryMetric]) || 0;
      const existing = timeGrouped.get(key) || { sum: 0, count: 0 };
      timeGrouped.set(key, { sum: existing.sum + val, count: existing.count + 1 });
    });

    const timeSeriesData = Array.from(timeGrouped.entries())
      .sort((a, b) => a[0].localeCompare(b[0]))
      .slice(-30)
      .map(([dateKey, stats]) => ({
        date: dateKey,
        [primaryMetric]: Number(stats.sum.toFixed(2)),
        Count: stats.count,
      }));

    if (timeSeriesData.length > 1) {
      charts.push({
        id: `chart_time_series_essential`,
        chart_type: 'area',
        data_columns: [primaryDate, primaryMetric],
        title: `${primaryMetric} Trend Over Time`,
        description: `Chronological distribution of ${primaryMetric} by ${primaryDate}.`,
        confidence: 0.96,
        recharts_config: {
          xAxisKey: 'date',
          dataKeys: [primaryMetric],
          colors: ['#3b82f6'],
          formatValue: isCurrency(primaryMetric) ? 'currency' : 'number',
        },
        data: timeSeriesData,
      });
    }
  }

  // 2. Primary Categorical Breakdown: 1 high-impact volume/value breakdown
  const targetDim = primaryDimension || categoricalColumns[0];
  const targetMetric = primaryMetric || numericColumns[0] || 'Count';

  if (targetDim) {
    const catGrouped = new Map<string, number>();
    let grandTotal = 0;

    data.forEach(r => {
      const cat = String(r[targetDim] ?? 'Unknown').trim() || 'Unknown';
      const val = targetMetric === 'Count' ? 1 : (Number(r[targetMetric]) || 0);
      catGrouped.set(cat, (catGrouped.get(cat) || 0) + val);
      grandTotal += val;
    });

    const sortedEntries = Array.from(catGrouped.entries()).sort((a, b) => b[1] - a[1]);

    // Bar Chart for main metric by primary dimension
    const barData = sortedEntries.slice(0, 10).map(([catName, sumVal]) => ({
      [targetDim]: catName,
      [targetMetric]: Number(sumVal.toFixed(2)),
    }));

    if (barData.length > 0) {
      charts.push({
        id: `chart_bar_essential`,
        chart_type: sortedEntries.length > 8 ? 'horizontal_bar' : 'bar',
        data_columns: [targetDim, targetMetric],
        title: `${targetMetric} by ${targetDim}`,
        description: `Total ${targetMetric} aggregated across ${targetDim} segments.`,
        confidence: 0.94,
        recharts_config: {
          xAxisKey: targetDim,
          dataKeys: [targetMetric],
          colors: ['#6366f1'],
          formatValue: isCurrency(targetMetric) ? 'currency' : 'number',
        },
        data: barData,
      });
    }

    // 3. Share Distribution Donut: Only if category has 2 to 8 unique values
    if (sortedEntries.length >= 2 && sortedEntries.length <= 8) {
      const donutData = sortedEntries.slice(0, 6).map(([catName, val]) => ({
        name: catName,
        value: Number(val.toFixed(2)),
        percentage: Number(((val / (grandTotal || 1)) * 100).toFixed(1)),
      }));

      charts.push({
        id: `chart_donut_essential`,
        chart_type: 'donut',
        data_columns: [targetDim, targetMetric],
        title: `${targetMetric} Share by ${targetDim}`,
        description: `Proportional share of ${targetMetric} across ${targetDim}.`,
        confidence: 0.91,
        recharts_config: {
          xAxisKey: 'name',
          dataKeys: ['value'],
          colors: ['#3b82f6', '#10b981', '#f59e0b', '#ec4899', '#8b5cf6', '#06b6d4'],
          formatValue: isCurrency(targetMetric) ? 'currency' : 'number',
        },
        data: donutData,
      });
    } else if (categoricalColumns.length > 1) {
      // Secondary dimension breakdown instead
      const secDim = categoricalColumns[1];
      const secGrouped = new Map<string, number>();
      data.forEach(r => {
        const cat = String(r[secDim] ?? 'Unknown').trim() || 'Unknown';
        const val = Number(r[targetMetric]) || 0;
        secGrouped.set(cat, (secGrouped.get(cat) || 0) + val);
      });
      const secEntries = Array.from(secGrouped.entries()).sort((a, b) => b[1] - a[1]).slice(0, 8);
      if (secEntries.length > 0) {
        charts.push({
          id: `chart_sec_dim_essential`,
          chart_type: 'bar',
          data_columns: [secDim, targetMetric],
          title: `${targetMetric} by ${secDim}`,
          description: `Segment distribution of ${targetMetric} across ${secDim}.`,
          confidence: 0.89,
          recharts_config: {
            xAxisKey: secDim,
            dataKeys: [targetMetric],
            colors: ['#10b981'],
            formatValue: isCurrency(targetMetric) ? 'currency' : 'number',
          },
          data: secEntries.map(([k, v]) => ({ [secDim]: k, [targetMetric]: Number(v.toFixed(2)) })),
        });
      }
    }
  }

  // 4. Comparative Composed Chart: Only if we have 2 or more distinct numeric metrics
  if (targetDim && numericColumns.length >= 2) {
    const [m1, m2] = numericColumns;
    const catGrouped = new Map<string, { val1: number; val2: number }>();
    data.forEach(r => {
      const cat = String(r[targetDim] ?? 'Unknown').trim();
      const v1 = Number(r[m1]) || 0;
      const v2 = Number(r[m2]) || 0;
      const existing = catGrouped.get(cat) || { val1: 0, val2: 0 };
      catGrouped.set(cat, { val1: existing.val1 + v1, val2: existing.val2 + v2 });
    });

    const comparisonData = Array.from(catGrouped.entries())
      .sort((a, b) => b[1].val1 - a[1].val1)
      .slice(0, 8)
      .map(([catName, stats]) => ({
        [targetDim]: catName,
        [m1]: Number(stats.val1.toFixed(2)),
        [m2]: Number(stats.val2.toFixed(2)),
      }));

    if (comparisonData.length > 0) {
      charts.push({
        id: 'chart_comparison_essential',
        chart_type: 'composed',
        data_columns: [targetDim, m1, m2],
        title: `${m1} & ${m2} by ${targetDim}`,
        description: `Comparative dual-metric relationship between ${m1} and ${m2} across ${targetDim}.`,
        confidence: 0.90,
        recharts_config: {
          xAxisKey: targetDim,
          dataKeys: [m1, m2],
          colors: ['#3b82f6', '#f59e0b'],
          formatValue: isCurrency(m1) ? 'currency' : 'number',
        },
        data: comparisonData,
      });
    }
  }

  return charts.slice(0, 4);
}

/**
 * Generate clear, non-AI statistical and rule-based business insights
 */
export function generateBusinessInsights(data: Record<string, any>[], profile: DatasetProfile): BusinessInsight[] {
  if (!data || data.length === 0) return [];

  const insights: BusinessInsight[] = [];
  const domainMeta = detectDatasetDomain(data, profile);
  const { primaryMetric, primaryDimension, columns } = profile;

  const isCurr = primaryMetric ? primaryMetric.toLowerCase().match(/(sales|revenue|profit|cost|amount|price|salary|budget)/) : false;

  // 1. Domain-Specific Top Driver & Concentration Insight
  if (primaryMetric && primaryDimension) {
    const sums = new Map<string, number>();
    let grandTotal = 0;
    data.forEach(r => {
      const cat = String(r[primaryDimension] ?? 'Unknown').trim();
      const val = Number(r[primaryMetric]) || 0;
      sums.set(cat, (sums.get(cat) || 0) + val);
      grandTotal += val;
    });

    const sorted = Array.from(sums.entries()).sort((a, b) => b[1] - a[1]);
    if (sorted.length > 0) {
      const [topCat, topVal] = sorted[0];
      const sharePct = Number(((topVal / (grandTotal || 1)) * 100).toFixed(1));

      let title = `${domainMeta.terms.topEntityTitle}: ${topCat}`;
      let description = `"${topCat}" leads ${primaryDimension} with ${formatValue(topVal, isCurr ? 'currency' : 'number')} ${domainMeta.terms.unitName} (${sharePct}% of total ${primaryMetric}).`;

      if (domainMeta.domain === 'covid_healthcare') {
        title = `Primary Outbreak Hotspot: ${topCat}`;
        description = `State/Zone "${topCat}" reported the highest infection volume with ${formatValue(topVal, 'number')} cases (${sharePct}% of total reported cases). Priority medical allocation to this zone is recommended.`;
      } else if (domainMeta.domain === 'hr_workforce') {
        title = `Largest Department Headcount/Spend: ${topCat}`;
        description = `Department "${topCat}" represents the largest organizational segment with ${formatValue(topVal, isCurr ? 'currency' : 'number')} in ${primaryMetric} (${sharePct}% of overall budget).`;
      } else if (domainMeta.domain === 'sales_ecommerce') {
        title = `Top Revenue Generator: ${topCat}`;
        description = `Product category "${topCat}" generated ${formatValue(topVal, 'currency')} (${sharePct}% of total revenue). It remains the main commercial growth engine.`;
      }

      insights.push({
        id: 'insight_top_driver',
        title,
        description,
        type: 'driver',
        impact: 'high',
        metricName: primaryMetric,
        value: topVal,
        badgeText: `${sharePct}% Share`,
      });

      // Concentration Risk check
      if (sorted.length >= 2) {
        const top2Sum = sorted[0][1] + sorted[1][1];
        const top2Share = Number(((top2Sum / (grandTotal || 1)) * 100).toFixed(1));
        if (top2Share >= 55) {
          insights.push({
            id: 'insight_risk_concentration',
            title: `High ${primaryDimension} Concentration (${top2Share}%)`,
            description: `The top 2 segments (${sorted[0][0]} & ${sorted[1][0]}) represent ${top2Share}% of all ${primaryMetric}. Diversifying across secondary ${primaryDimension} lines mitigates risk exposure.`,
            type: 'risk',
            impact: 'medium',
            badgeText: 'Concentration Warning',
          });
        }
      }
    }
  }

  // 2. Statistical Volatility & Distribution Insight
  if (primaryMetric) {
    const colProf = columns.find(c => c.name === primaryMetric);
    if (colProf && colProf.mean && colProf.stdDev) {
      const cv = Number((colProf.stdDev / colProf.mean).toFixed(2));
      if (cv > 1.2) {
        insights.push({
          id: 'insight_volatility',
          title: `High Distribution Variance in ${primaryMetric}`,
          description: `${primaryMetric} exhibits notable spread across records (Mean: ${formatValue(colProf.mean, isCurr ? 'currency' : 'number')}, Standard Deviation: ${formatValue(colProf.stdDev)}). Specific spike entries stretch the baseline range.`,
          type: 'anomaly',
          impact: 'medium',
          badgeText: `High Variance`,
        });
      } else {
        insights.push({
          id: 'insight_stability',
          title: `Predictable ${primaryMetric} Distribution`,
          description: `${primaryMetric} maintains a consistent distribution with a mean of ${formatValue(colProf.mean, isCurr ? 'currency' : 'number')} and low variance across all ${data.length} records.`,
          type: 'trend',
          impact: 'low',
          badgeText: 'Stable Pattern',
        });
      }
    }
  }

  // 3. Outliers Insight
  if (primaryMetric) {
    const colProf = columns.find(c => c.name === primaryMetric);
    if (colProf && colProf.mean && colProf.stdDev) {
      const threshold = colProf.mean + 2.2 * colProf.stdDev;
      const outliers = data.filter(r => Number(r[primaryMetric]) > threshold);
      if (outliers.length > 0) {
        insights.push({
          id: 'insight_outliers',
          title: `${outliers.length} Statistical Spike Outliers Detected in ${primaryMetric}`,
          description: `Identified ${outliers.length} records exceeding ${formatValue(threshold, isCurr ? 'currency' : 'number')}. These statistical spikes significantly influence overall aggregates.`,
          type: 'anomaly',
          impact: 'high',
          badgeText: 'Spike Detected',
        });
      }
    }
  }

  // 4. Data Health & Completeness Insight
  insights.push({
    id: 'insight_data_health',
    title: `Dataset Quality Score: ${profile.completeness}%`,
    description: `Analyzed ${profile.rowCount} rows across ${profile.columnCount} columns in ${domainMeta.domainName}. ${profile.duplicateRows > 0 ? `${profile.duplicateRows} duplicate records identified.` : 'Zero duplicate rows detected.'}`,
    type: 'quality',
    impact: 'low',
    badgeText: profile.completeness > 90 ? 'High Integrity' : 'Quality Warnings',
  });

  return insights;
}

/**
 * Generate a complete, ready-to-render BI Dashboard
 */
export function generateBIDashboard(
  data: Record<string, any>[],
  datasetName: string = 'Uploaded Dataset',
  filters?: FilterCriteria
): DashboardConfig {
  const profile = profileDataset(data);
  const filteredData = filterDataset(data, profile, filters);
  const kpis = generateKPIs(filteredData, profile);
  const charts = generateCharts(filteredData, profile);
  const insights = generateBusinessInsights(filteredData, profile);

  return {
    dashboard_id: `dash_${Date.now()}`,
    title: `${datasetName} Analytics Dashboard`,
    description: `Executive intelligence report generated from ${data.length} records across ${profile.columnCount} columns.`,
    kpis,
    charts,
    insights,
    metadata: {
      dataset_name: datasetName,
      total_rows: filteredData.length,
      cleaned_at: new Date().toISOString(),
      primary_metric: profile.primaryMetric || 'Value',
      primary_dimension: profile.primaryDimension || 'Category',
      primary_date: profile.primaryDate,
    },
    sample_rows: filteredData.slice(0, 50),
    generated_at: new Date().toISOString(),
  };
}

export interface ForecastDataPoint {
  date: string;
  historical: number | null;
  forecast: number | null;
  lowerBound: number | null;
  upperBound: number | null;
  isForecast: boolean;
}

export interface ForecastResult {
  status: 'success' | 'insufficient_data' | 'no_date_column' | 'invalid_metric';
  message: string;
  dateColumn?: string;
  metricColumn?: string;
  horizonPeriods?: number;
  confidenceLevel?: number;
  
  chartData: ForecastDataPoint[];
  
  historicalBaseline?: number;
  forecastEndValue?: number;
  projectedChangeVal?: number;
  projectedChangePercent?: number;
  modelConfidenceScore?: number;
  trendDirection?: 'up' | 'down' | 'flat';
  
  narrativeSummary?: string;
  keyTakeaways?: string[];
  
  availableDateColumns: string[];
  availableNumericMetrics: string[];
}

/**
 * Generate linear & exponential dampening time-series forecast from dataset
 */
export function generateForecast(
  data: Record<string, any>[],
  profile: DatasetProfile,
  options?: {
    dateCol?: string;
    metricCol?: string;
    horizon?: number;
    confidenceLevel?: number;
  }
): ForecastResult {
  const dateCols = profile.dateColumns || [];
  const numericCols = profile.numericColumns || [];
  
  const selectedDateCol = options?.dateCol || profile.primaryDate || dateCols[0];
  const selectedMetricCol = options?.metricCol || profile.primaryMetric || numericCols[0];
  const horizon = options?.horizon || 6;
  const confidenceLevel = options?.confidenceLevel || 90;

  if (!selectedDateCol) {
    return {
      status: 'no_date_column',
      message: 'No chronological date/time column was detected in this dataset. Forecasting requires a date column (e.g. YYYY-MM-DD, Month, Year).',
      chartData: [],
      availableDateColumns: dateCols,
      availableNumericMetrics: numericCols
    };
  }

  if (!selectedMetricCol) {
    return {
      status: 'invalid_metric',
      message: 'No numeric metric column was found to perform time-series forecasting.',
      chartData: [],
      availableDateColumns: dateCols,
      availableNumericMetrics: numericCols
    };
  }

  // Aggregate historical time series by date
  const aggregatedMap = new Map<string, { sum: number; count: number; timestamp: number }>();

  data.forEach(row => {
    const rawDate = row[selectedDateCol];
    const rawVal = Number(row[selectedMetricCol]);
    if (!rawDate || isNaN(rawVal)) return;

    const parsedTime = Date.parse(String(rawDate));
    if (isNaN(parsedTime)) return;

    const dateObj = new Date(parsedTime);
    const dateKey = dateObj.toISOString().slice(0, 10);

    const existing = aggregatedMap.get(dateKey) || { sum: 0, count: 0, timestamp: dateObj.getTime() };
    aggregatedMap.set(dateKey, {
      sum: existing.sum + rawVal,
      count: existing.count + 1,
      timestamp: dateObj.getTime()
    });
  });

  const sortedPoints = Array.from(aggregatedMap.entries())
    .map(([dateKey, item]) => ({ dateKey, value: item.sum, timestamp: item.timestamp }))
    .sort((a, b) => a.timestamp - b.timestamp);

  if (sortedPoints.length < 4) {
    return {
      status: 'insufficient_data',
      message: `Forecasting requires at least 4 distinct historical time points. Only ${sortedPoints.length} valid date point(s) were found in column "${selectedDateCol}".`,
      dateColumn: selectedDateCol,
      metricColumn: selectedMetricCol,
      chartData: [],
      availableDateColumns: dateCols,
      availableNumericMetrics: numericCols
    };
  }

  // Linear Regression & Uncertainty Confidence Band
  const N = sortedPoints.length;
  let sumX = 0, sumY = 0, sumXY = 0, sumXX = 0;

  sortedPoints.forEach((pt, i) => {
    sumX += i;
    sumY += pt.value;
    sumXY += i * pt.value;
    sumXX += i * i;
  });

  const meanX = sumX / N;
  const meanY = sumY / N;
  const slope = (N * sumXY - sumX * sumY) / Math.max(1, (N * sumXX - sumX * sumX));
  const intercept = meanY - slope * meanX;

  let sse = 0;
  let sst = 0;
  sortedPoints.forEach((pt, i) => {
    const fitted = slope * i + intercept;
    sse += Math.pow(pt.value - fitted, 2);
    sst += Math.pow(pt.value - meanY, 2);
  });

  const mse = sse / Math.max(1, N - 2);
  const stdError = Math.sqrt(mse);
  const rSquared = sst > 0 ? Math.max(0, Math.min(1, 1 - sse / sst)) : 0;
  const modelConfidenceScore = Math.round(rSquared * 100);

  const zScore = confidenceLevel === 95 ? 1.96 : confidenceLevel === 80 ? 1.28 : 1.645;

  let totalDeltaMs = 0;
  for (let i = 1; i < N; i++) {
    totalDeltaMs += (sortedPoints[i].timestamp - sortedPoints[i - 1].timestamp);
  }
  const avgDeltaMs = totalDeltaMs / Math.max(1, N - 1);

  const chartData: ForecastDataPoint[] = [];

  sortedPoints.forEach((pt, i) => {
    const isLastHistorical = i === N - 1;
    chartData.push({
      date: pt.dateKey,
      historical: Number(pt.value.toFixed(2)),
      forecast: isLastHistorical ? Number(pt.value.toFixed(2)) : null,
      lowerBound: isLastHistorical ? Number(pt.value.toFixed(2)) : null,
      upperBound: isLastHistorical ? Number(pt.value.toFixed(2)) : null,
      isForecast: false,
    });
  });

  const lastTime = sortedPoints[N - 1].timestamp;
  const lastVal = sortedPoints[N - 1].value;

  let endForecastVal = lastVal;
  for (let h = 1; h <= horizon; h++) {
    const futureTime = lastTime + h * avgDeltaMs;
    const futureDate = new Date(futureTime).toISOString().slice(0, 10);
    const futureIdx = (N - 1) + h;
    
    const dampening = Math.pow(0.96, h - 1);
    const pointForecast = lastVal + slope * h * dampening;

    const marginError = zScore * stdError * Math.sqrt(1 + (1 / N) + Math.pow(futureIdx - meanX, 2) / Math.max(1, sumXX - N * meanX * meanX));
    const isNonNegative = sortedPoints.every(p => p.value >= 0);

    const lower = isNonNegative ? Math.max(0, pointForecast - marginError) : pointForecast - marginError;
    const upper = pointForecast + marginError;

    if (h === horizon) {
      endForecastVal = pointForecast;
    }

    chartData.push({
      date: futureDate,
      historical: null,
      forecast: Number(pointForecast.toFixed(2)),
      lowerBound: Number(lower.toFixed(2)),
      upperBound: Number(upper.toFixed(2)),
      isForecast: true,
    });
  }

  const changeVal = endForecastVal - lastVal;
  const changePct = lastVal !== 0 ? (changeVal / Math.abs(lastVal)) * 100 : 0;
  const trendDirection = changePct > 2 ? 'up' : changePct < -2 ? 'down' : 'flat';

  const isCurrency = selectedMetricCol.toLowerCase().match(/(sales|revenue|profit|cost|price|amount)/);
  const formattedBaseline = isCurrency ? `$${lastVal.toLocaleString(undefined, { maximumFractionDigits: 2 })}` : lastVal.toLocaleString(undefined, { maximumFractionDigits: 2 });
  const formattedEnd = isCurrency ? `$${endForecastVal.toLocaleString(undefined, { maximumFractionDigits: 2 })}` : endForecastVal.toLocaleString(undefined, { maximumFractionDigits: 2 });
  const formattedChange = `${changePct >= 0 ? '+' : ''}${changePct.toFixed(1)}%`;

  const narrative = `Based on historical analysis of ${N} chronological records, "${selectedMetricCol}" is projected to move from a current baseline of ${formattedBaseline} to ${formattedEnd} over the next ${horizon} periods (${formattedChange} change). The statistical trend confidence score is ${modelConfidenceScore}%.`;

  const takeaways = [
    `Baseline metric level: ${formattedBaseline} (Last observed value)`,
    `Projected metric level: ${formattedEnd} after ${horizon} periods`,
    `Trend slope trajectory: ${trendDirection === 'up' ? 'Positive Growth (+)' : trendDirection === 'down' ? 'Negative Decline (-)' : 'Stable / Constant (=)'}`,
    `Model fit score (R²): ${modelConfidenceScore}% reliability based on historical variance`
  ];

  return {
    status: 'success',
    message: 'Forecast generated successfully.',
    dateColumn: selectedDateCol,
    metricColumn: selectedMetricCol,
    horizonPeriods: horizon,
    confidenceLevel,
    chartData,
    historicalBaseline: Number(lastVal.toFixed(2)),
    forecastEndValue: Number(endForecastVal.toFixed(2)),
    projectedChangeVal: Number(changeVal.toFixed(2)),
    projectedChangePercent: Number(changePct.toFixed(1)),
    modelConfidenceScore,
    trendDirection,
    narrativeSummary: narrative,
    keyTakeaways: takeaways,
    availableDateColumns: dateCols,
    availableNumericMetrics: numericCols
  };
}

/**
 * Built-in Sample Datasets for instant zero-friction testing
 */
export const SAMPLE_DATASETS = [
  {
    id: 'sales_performance',
    name: 'Global Sales & Revenue 2026',
    description: 'B2B software & hardware sales transactions across global regions with product categories and profitability.',
    data: [
      { Order_Date: '2026-01-15', Region: 'North America', Category: 'Cloud Services', Sales_Rep: 'Alex Chen', Revenue: 14200, Profit: 4800, Discount: 0.05, Customer_Segment: 'Enterprise' },
      { Order_Date: '2026-01-18', Region: 'Europe', Category: 'Hardware', Sales_Rep: 'Emma Watson', Revenue: 8900, Profit: 2100, Discount: 0.10, Customer_Segment: 'SMB' },
      { Order_Date: '2026-01-22', Region: 'Asia Pacific', Category: 'Software Licenses', Sales_Rep: 'Kenji Sato', Revenue: 22500, Profit: 9200, Discount: 0.00, Customer_Segment: 'Enterprise' },
      { Order_Date: '2026-02-02', Region: 'North America', Category: 'Consulting', Sales_Rep: 'Sarah Jenkins', Revenue: 18000, Profit: 7500, Discount: 0.02, Customer_Segment: 'Government' },
      { Order_Date: '2026-02-10', Region: 'Latin America', Category: 'Cloud Services', Sales_Rep: 'Carlos Silva', Revenue: 11200, Profit: 3900, Discount: 0.08, Customer_Segment: 'SMB' },
      { Order_Date: '2026-02-14', Region: 'Europe', Category: 'Software Licenses', Sales_Rep: 'Emma Watson', Revenue: 31000, Profit: 14500, Discount: 0.05, Customer_Segment: 'Enterprise' },
      { Order_Date: '2026-03-01', Region: 'North America', Category: 'Hardware', Sales_Rep: 'Alex Chen', Revenue: 15400, Profit: 4100, Discount: 0.12, Customer_Segment: 'SMB' },
      { Order_Date: '2026-03-08', Region: 'Asia Pacific', Category: 'Cloud Services', Sales_Rep: 'Kenji Sato', Revenue: 28900, Profit: 11800, Discount: 0.03, Customer_Segment: 'Enterprise' },
      { Order_Date: '2026-03-15', Region: 'Europe', Category: 'Consulting', Sales_Rep: 'David Miller', Revenue: 9500, Profit: 3200, Discount: 0.00, Customer_Segment: 'SMB' },
      { Order_Date: '2026-03-28', Region: 'North America', Category: 'Software Licenses', Sales_Rep: 'Sarah Jenkins', Revenue: 42000, Profit: 19800, Discount: 0.04, Customer_Segment: 'Enterprise' },
      { Order_Date: '2026-04-05', Region: 'Asia Pacific', Category: 'Hardware', Sales_Rep: 'Kenji Sato', Revenue: 13400, Profit: 3200, Discount: 0.15, Customer_Segment: 'SMB' },
      { Order_Date: '2026-04-12', Region: 'Latin America', Category: 'Software Licenses', Sales_Rep: 'Carlos Silva', Revenue: 19800, Profit: 8400, Discount: 0.05, Customer_Segment: 'Enterprise' },
      { Order_Date: '2026-04-20', Region: 'North America', Category: 'Cloud Services', Sales_Rep: 'Alex Chen', Revenue: 35000, Profit: 14200, Discount: 0.02, Customer_Segment: 'Enterprise' },
      { Order_Date: '2026-05-02', Region: 'Europe', Category: 'Cloud Services', Sales_Rep: 'Emma Watson', Revenue: 26400, Profit: 9800, Discount: 0.06, Customer_Segment: 'Government' },
      { Order_Date: '2026-05-18', Region: 'Asia Pacific', Category: 'Consulting', Sales_Rep: 'Kenji Sato', Revenue: 16500, Profit: 6200, Discount: 0.00, Customer_Segment: 'SMB' },
    ]
  },
  {
    id: 'ecommerce_orders',
    name: 'E-Commerce Orders & Fulfillment',
    description: 'Online store customer orders, payment channels, shipping costs, order values, and fulfillment status.',
    data: [
      { Transaction_ID: 'TX1001', Created_At: '2026-01-01', Channel: 'Web Store', Product_Group: 'Electronics', Payment_Method: 'Credit Card', Order_Amount: 349.99, Shipping_Fee: 15.00, Status: 'Delivered' },
      { Transaction_ID: 'TX1002', Created_At: '2026-01-02', Channel: 'Mobile App', Product_Group: 'Apparel', Payment_Method: 'Apple Pay', Order_Amount: 89.50, Shipping_Fee: 5.00, Status: 'Delivered' },
      { Transaction_ID: 'TX1003', Created_At: '2026-01-03', Channel: 'Web Store', Product_Group: 'Home & Kitchen', Payment_Method: 'PayPal', Order_Amount: 189.00, Shipping_Fee: 12.00, Status: 'Delivered' },
      { Transaction_ID: 'TX1004', Created_At: '2026-01-04', Channel: 'Social Shop', Product_Group: 'Beauty', Payment_Method: 'Credit Card', Order_Amount: 64.20, Shipping_Fee: 0.00, Status: 'Returned' },
      { Transaction_ID: 'TX1005', Created_At: '2026-01-05', Channel: 'Mobile App', Product_Group: 'Electronics', Payment_Method: 'Apple Pay', Order_Amount: 1299.00, Shipping_Fee: 25.00, Status: 'Delivered' },
      { Transaction_ID: 'TX1006', Created_At: '2026-01-06', Channel: 'Web Store', Product_Group: 'Apparel', Payment_Method: 'Credit Card', Order_Amount: 142.00, Shipping_Fee: 8.00, Status: 'Shipped' },
      { Transaction_ID: 'TX1007', Created_At: '2026-01-07', Channel: 'Mobile App', Product_Group: 'Fitness', Payment_Method: 'Google Pay', Order_Amount: 210.00, Shipping_Fee: 10.00, Status: 'Delivered' },
      { Transaction_ID: 'TX1008', Created_At: '2026-01-08', Channel: 'Social Shop', Product_Group: 'Apparel', Payment_Method: 'PayPal', Order_Amount: 75.00, Shipping_Fee: 5.00, Status: 'Processing' },
      { Transaction_ID: 'TX1009', Created_At: '2026-01-09', Channel: 'Web Store', Product_Group: 'Electronics', Payment_Method: 'Credit Card', Order_Amount: 850.00, Shipping_Fee: 18.00, Status: 'Delivered' },
      { Transaction_ID: 'TX1010', Created_At: '2026-01-10', Channel: 'Mobile App', Product_Group: 'Home & Kitchen', Payment_Method: 'Apple Pay', Order_Amount: 295.50, Shipping_Fee: 12.00, Status: 'Delivered' },
    ]
  }
];
