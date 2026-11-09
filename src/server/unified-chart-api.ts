/**
 * Unified Chart Pipeline Server API
 *
 * Architecture:
 * 1. Python performs ALL calculations (aggregations, descriptive statistics, trends, distributions).
 * 2. Gemini constructs the actual charts (chart type, dimension, metric, layout, titles) using Python's computed results.
 * 3. Gemini generates only a limited, essential set of charts (quality over quantity, matched to what dataset supports).
 * 4. Python computes the exact formatted series data for Recharts.
 * 5. Returns standard ChartConfig[] for the "analytical visualization" section.
 */

import { GoogleGenAI } from '@google/genai';
import { spawn } from 'child_process';
import path from 'path';

export interface UnifiedChartConstructionSpec {
  id: string;
  chart_type: 'bar' | 'line' | 'area' | 'donut' | 'pie' | 'composed' | 'horizontal_bar';
  metric_column: string;
  dimension_column: string;
  aggregation: 'sum' | 'mean' | 'count';
  title: string;
  description: string;
  confidence: number;
  format_value?: 'currency' | 'number' | 'percentage';
  colors?: string[];
  stacked?: boolean;
}

export interface CalculatedProfile {
  dataset_name: string;
  total_rows: number;
  total_columns: number;
  numeric_columns: string[];
  categorical_columns: string[];
  date_columns: string[];
  numeric_summaries: Record<string, any>;
  categorical_summaries: Record<string, any>;
  bivariate_aggregations: Array<{
    dimension: string;
    metric: string;
    items: Array<{ category: string; sum: number; mean: number; count: number }>;
  }>;
  temporal_aggregations: Array<{
    date_column: string;
    metric: string;
    timeline: Array<{ period: string; sum: number; mean: number; count: number }>;
  }>;
  correlations: Array<{
    col_a: string;
    col_b: string;
    pearson_r: number;
    strength: string;
  }>;
}

/**
 * Step 1: Execute Python to perform all data calculations and analytical profiling.
 */
export async function executePythonCalculations(
  rows: Record<string, any>[],
  datasetName: string = 'Dataset'
): Promise<CalculatedProfile> {
  return new Promise((resolve) => {
    try {
      const scriptPath = path.resolve(process.cwd(), 'backend/src/services/unified_chart_engine.py');
      const pyProcess = spawn('python3', [scriptPath, '--analyze']);

      let stdout = '';
      let stderr = '';

      pyProcess.stdout.on('data', (chunk) => {
        stdout += chunk.toString();
      });

      pyProcess.stderr.on('data', (chunk) => {
        stderr += chunk.toString();
      });

      pyProcess.on('close', (code) => {
        if (code === 0 && stdout.trim()) {
          try {
            const parsed = JSON.parse(stdout);
            resolve(parsed);
            return;
          } catch (err) {
            console.error('Failed to parse Python analytics output, using TS fallback:', err);
          }
        }
        if (stderr) {
          console.warn('Python chart engine stderr:', stderr);
        }
        resolve(fallbackTypeScriptCalculations(rows, datasetName));
      });

      pyProcess.on('error', (err) => {
        console.warn('Failed to spawn Python chart engine, using TS fallback:', err.message);
        resolve(fallbackTypeScriptCalculations(rows, datasetName));
      });

      // Send input JSON to Python via stdin
      pyProcess.stdin.write(JSON.stringify({ rows, dataset_name: datasetName }));
      pyProcess.stdin.end();
    } catch (err) {
      console.warn('Exception running Python chart engine, using TS fallback:', err);
      resolve(fallbackTypeScriptCalculations(rows, datasetName));
    }
  });
}

/**
 * Step 2: Gemini constructs the actual charts using Python's computed results.
 * Gemini does NOT calculate numbers. It selects 3 to 5 essential, high-impact charts.
 */
export async function constructChartsWithGemini(
  profile: CalculatedProfile
): Promise<UnifiedChartConstructionSpec[]> {
  const apiKey = process.env.GEMINI_API_KEY || process.env.GOOGLE_API_KEY;

  if (!apiKey) {
    console.log('GEMINI_API_KEY not found; using rule-based essential chart constructor');
    return constructEssentialChartsRuleBased(profile);
  }

  const ai = new GoogleGenAI({
    apiKey,
    httpOptions: {
      headers: {
        'User-Agent': 'aistudio-build',
      },
    },
  });

  const prompt = `
You are the Executive BI Architect for InsightIQ.
You have been provided with PRE-CALCULATED, verified statistical results from our Python/Pandas analytics engine.

CRITICAL DIRECTIVES:
1. Python has ALREADY performed all calculations, sums, averages, and group counts. DO NOT do any math.
2. DO NOT output code or markdown. Return ONLY valid JSON matching the schema below.
3. CONSTRUCT the actual charts (chart_type, dimension_column, metric_column, title, description, format_value).
4. STRICT ESSENTIAL SET RULE (Quality over Quantity):
   - Generate ONLY a limited, essential set of 3 to 5 high-impact charts.
   - DO NOT generate every possible combination or an exhaustive permutation matrix.
   - Select only the visualizations that answer the most critical business questions for this specific dataset.
   - If date columns exist with temporal trends, construct 1 chronological trend chart ('area' or 'line').
   - For primary categorical columns, construct 1 high-impact volume/value breakdown ('bar' or 'horizontal_bar').
   - If a categorical column has 3 to 7 categories, construct 1 share distribution ('donut').
   - If multiple strong numeric metrics or correlations exist, construct 1 comparative or composed chart ('composed' or 'bar').
5. Pick chart types strictly from: "bar", "line", "area", "donut", "composed", "horizontal_bar".
6. Pick metric_column strictly from: ${JSON.stringify(profile.numeric_columns)}.
7. Pick dimension_column strictly from: ${JSON.stringify([...profile.categorical_columns, ...profile.date_columns])}.

PRE-CALCULATED PYTHON STATISTICS:
${JSON.stringify(profile, null, 2)}

REQUIRED JSON RESPONSE SCHEMA:
{
  "charts": [
    {
      "id": "unified_chart_1",
      "chart_type": "bar | line | area | donut | composed | horizontal_bar",
      "metric_column": "Exact column name from numeric_columns",
      "dimension_column": "Exact column name from categorical_columns or date_columns",
      "aggregation": "sum | mean | count",
      "title": "Clear, professional executive chart title",
      "description": "Crisp 1-sentence description explaining what strategic intelligence this chart provides",
      "confidence": 0.95,
      "format_value": "currency | number | percentage"
    }
  ]
}
`;

  try {
    const response = await ai.models.generateContent({
      model: 'gemini-3.8-flash',
      contents: prompt,
      config: {
        temperature: 0.1,
        maxOutputTokens: 2048,
        responseMimeType: 'application/json',
      },
    });

    let text = response.text || '';
    text = text.trim();
    if (text.startsWith('```json')) text = text.slice(7);
    if (text.endsWith('```')) text = text.slice(0, -3);
    text = text.trim();

    const parsed = JSON.parse(text);
    const charts: UnifiedChartConstructionSpec[] = parsed.charts || [];

    if (Array.isArray(charts) && charts.length > 0) {
      // Enforce the 3-5 chart limit strictly
      return charts.slice(0, 5);
    }
    return constructEssentialChartsRuleBased(profile);
  } catch (err) {
    console.error('Gemini chart construction failed, falling back to rule-based essential constructor:', err);
    return constructEssentialChartsRuleBased(profile);
  }
}

/**
 * Step 3: Python executes series data generation for the constructed charts.
 */
export async function executePythonSeriesGeneration(
  rows: Record<string, any>[],
  specs: UnifiedChartConstructionSpec[]
): Promise<any[]> {
  return new Promise((resolve) => {
    try {
      const scriptPath = path.resolve(process.cwd(), 'backend/src/services/unified_chart_engine.py');
      const pyProcess = spawn('python3', [scriptPath, '--compute-series']);

      let stdout = '';
      let stderr = '';

      pyProcess.stdout.on('data', (chunk) => {
        stdout += chunk.toString();
      });

      pyProcess.stderr.on('data', (chunk) => {
        stderr += chunk.toString();
      });

      pyProcess.on('close', (code) => {
        if (code === 0 && stdout.trim()) {
          try {
            const parsed = JSON.parse(stdout);
            resolve(parsed);
            return;
          } catch (err) {
            console.error('Failed to parse Python series output, using TS fallback:', err);
          }
        }
        resolve(fallbackTypeScriptSeries(rows, specs));
      });

      pyProcess.on('error', (err) => {
        console.warn('Failed to spawn Python series engine, using TS fallback:', err.message);
        resolve(fallbackTypeScriptSeries(rows, specs));
      });

      pyProcess.stdin.write(JSON.stringify({ rows, chart_specs: specs }));
      pyProcess.stdin.end();
    } catch (err) {
      console.warn('Exception running Python series engine, using TS fallback:', err);
      resolve(fallbackTypeScriptSeries(rows, specs));
    }
  });
}

/**
 * Rule-based Essential Chart Constructor (Fallback when Gemini is offline).
 * Conscientiously selects only 3-4 essential charts matched to what dataset supports.
 */
export function constructEssentialChartsRuleBased(
  profile: CalculatedProfile
): UnifiedChartConstructionSpec[] {
  const specs: UnifiedChartConstructionSpec[] = [];
  const { numeric_columns, categorical_columns, date_columns } = profile;

  if (numeric_columns.length === 0) return specs;

  const primaryMetric = numeric_columns[0];
  const secondaryMetric = numeric_columns[1] || primaryMetric;
  const isCurrency = /sales|revenue|profit|cost|price|amount|spend|budget/i.test(primaryMetric);
  const formatVal = isCurrency ? 'currency' : 'number';

  // 1. If Date exists: 1 Chronological Trend (Area or Line)
  if (date_columns.length > 0) {
    const dtCol = date_columns[0];
    specs.push({
      id: 'unified_chart_trend',
      chart_type: 'area',
      metric_column: primaryMetric,
      dimension_column: dtCol,
      aggregation: 'sum',
      title: `${primaryMetric} Trend Over Time`,
      description: `Chronological trajectory of ${primaryMetric} across ${dtCol} periods.`,
      confidence: 0.95,
      format_value: formatVal,
      colors: ['#3b82f6'],
    });
  }

  // 2. Primary Categorical Breakdown: 1 Bar or Horizontal Bar
  if (categorical_columns.length > 0) {
    const primaryCat = categorical_columns[0];
    const catStats = profile.categorical_summaries[primaryCat];
    const uniqueCount = catStats ? catStats.unique_count : 5;

    specs.push({
      id: 'unified_chart_breakdown',
      chart_type: uniqueCount > 8 ? 'horizontal_bar' : 'bar',
      metric_column: primaryMetric,
      dimension_column: primaryCat,
      aggregation: 'sum',
      title: `${primaryMetric} by ${primaryCat}`,
      description: `Aggregated distribution of ${primaryMetric} across key ${primaryCat} segments.`,
      confidence: 0.94,
      format_value: formatVal,
      colors: ['#6366f1'],
    });
  }

  // 3. Share Distribution: Donut Chart if there is a category with 3-8 items
  const donutCandidate = categorical_columns.find((c) => {
    const stats = profile.categorical_summaries[c];
    return stats && stats.unique_count >= 2 && stats.unique_count <= 8;
  });

  if (donutCandidate) {
    specs.push({
      id: 'unified_chart_distribution',
      chart_type: 'donut',
      metric_column: primaryMetric,
      dimension_column: donutCandidate,
      aggregation: 'sum',
      title: `${primaryMetric} Share by ${donutCandidate}`,
      description: `Proportional percentage contribution across ${donutCandidate} categories.`,
      confidence: 0.91,
      format_value: formatVal,
      colors: ['#3b82f6', '#10b981', '#f59e0b', '#ec4899', '#8b5cf6', '#06b6d4'],
    });
  } else if (categorical_columns.length > 1) {
    // Secondary Category Breakdown
    const secCat = categorical_columns[1];
    specs.push({
      id: 'unified_chart_sec_breakdown',
      chart_type: 'bar',
      metric_column: primaryMetric,
      dimension_column: secCat,
      aggregation: 'sum',
      title: `${primaryMetric} by ${secCat}`,
      description: `Segment analysis across ${secCat}.`,
      confidence: 0.90,
      format_value: formatVal,
      colors: ['#10b981'],
    });
  }

  // 4. If secondary numeric metric exists: 1 Composed or Comparative Chart
  if (numeric_columns.length >= 2 && categorical_columns.length > 0) {
    const primaryCat = categorical_columns[0];
    specs.push({
      id: 'unified_chart_comparison',
      chart_type: 'composed',
      metric_column: primaryMetric,
      dimension_column: primaryCat,
      aggregation: 'sum',
      title: `${primaryMetric} & ${secondaryMetric} by ${primaryCat}`,
      description: `Dual-metric comparative correlation across ${primaryCat}.`,
      confidence: 0.89,
      format_value: formatVal,
      colors: ['#3b82f6', '#f59e0b'],
    });
  }

  return specs.slice(0, 4);
}

/**
 * Formats series results into standard ChartConfig objects for the UI.
 */
export function formatUnifiedChartConfigs(
  specsWithSeries: any[],
  rawProfile: CalculatedProfile
): any[] {
  const palette = [
    '#3b82f6',
    '#10b981',
    '#6366f1',
    '#f59e0b',
    '#06b6d4',
    '#ec4899',
    '#8b5cf6',
  ];

  return specsWithSeries.map((item, idx) => {
    const chartType = (item.chart_type || 'bar').toLowerCase();
    const metricCol = item.metric_column || rawProfile.numeric_columns[0] || 'value';
    const dimCol = item.dimension_column || rawProfile.categorical_columns[0] || 'category';
    const primaryColor = palette[idx % palette.length];

    const isCurrency =
      item.format_value === 'currency' ||
      /sales|revenue|profit|cost|price|amount|spend/i.test(metricCol);

    return {
      id: item.id || `unified_chart_${idx + 1}`,
      chart_type: chartType,
      data_columns: [dimCol, metricCol],
      title: item.title || `${metricCol} by ${dimCol}`,
      description: item.description || `Analysis of ${metricCol} across ${dimCol}.`,
      confidence: item.confidence || 0.92,
      recharts_config: {
        xAxisKey: dimCol,
        dataKeys: [metricCol],
        colors: item.colors || [primaryColor],
        formatValue: isCurrency ? 'currency' : 'number',
        stacked: item.stacked || false,
      },
      data: item.data || [],
    };
  });
}

/**
 * End-to-End Unified Chart Pipeline Handler.
 */
export async function runUnifiedChartPipeline(
  rows: Record<string, any>[],
  datasetName: string = 'Dataset'
): Promise<any[]> {
  if (!rows || rows.length === 0) return [];

  // Step 1: Python calculates all statistics and breakdowns
  const profile = await executePythonCalculations(rows, datasetName);

  // Step 2: Gemini constructs the essential charts (or fallback to essential rule-based constructor)
  const chartSpecs = await constructChartsWithGemini(profile);

  // Step 3: Python calculates the exact series data
  const seriesResults = await executePythonSeriesGeneration(rows, chartSpecs);

  // Step 4: Map to standard ChartConfig format
  return formatUnifiedChartConfigs(seriesResults, profile);
}

/**
 * Fallback TypeScript Calculations (used if Python subprocess is interrupted).
 */
function fallbackTypeScriptCalculations(
  rows: Record<string, any>[],
  datasetName: string
): CalculatedProfile {
  const totalRows = rows.length;
  if (totalRows === 0) {
    return {
      dataset_name: datasetName,
      total_rows: 0,
      total_columns: 0,
      numeric_columns: [],
      categorical_columns: [],
      date_columns: [],
      numeric_summaries: {},
      categorical_summaries: {},
      bivariate_aggregations: [],
      temporal_aggregations: [],
      correlations: [],
    };
  }

  const sample = rows[0];
  const allCols = Object.keys(sample);
  const numericCols: string[] = [];
  const dateCols: string[] = [];
  const categoricalCols: string[] = [];

  allCols.forEach((col) => {
    const colLower = col.toLowerCase();
    const isDate =
      colLower.includes('date') ||
      colLower.includes('time') ||
      colLower.includes('year') ||
      colLower.includes('month');

    if (isDate) {
      dateCols.push(col);
      return;
    }

    const numCount = rows.filter((r) => {
      const v = r[col];
      return v !== null && v !== undefined && v !== '' && !isNaN(Number(v));
    }).length;

    if (numCount / totalRows > 0.5) {
      numericCols.push(col);
    } else {
      categoricalCols.push(col);
    }
  });

  const numericSummaries: Record<string, any> = {};
  numericCols.forEach((col) => {
    const vals = rows
      .map((r) => Number(r[col]))
      .filter((n) => !isNaN(n));
    const sum = vals.reduce((a, b) => a + b, 0);
    const mean = vals.length > 0 ? sum / vals.length : 0;
    numericSummaries[col] = {
      sum: Math.round(sum * 100) / 100,
      mean: Math.round(mean * 100) / 100,
      count: vals.length,
    };
  });

  const categoricalSummaries: Record<string, any> = {};
  categoricalCols.forEach((col) => {
    const map: Record<string, number> = {};
    rows.forEach((r) => {
      const k = String(r[col] ?? 'Unknown');
      map[k] = (map[k] || 0) + 1;
    });
    categoricalSummaries[col] = {
      unique_count: Object.keys(map).length,
    };
  });

  return {
    dataset_name: datasetName,
    total_rows: totalRows,
    total_columns: allCols.length,
    numeric_columns: numericCols,
    categorical_columns: categoricalCols,
    date_columns: dateCols,
    numeric_summaries: numericSummaries,
    categorical_summaries: categoricalSummaries,
    bivariate_aggregations: [],
    temporal_aggregations: [],
    correlations: [],
  };
}

/**
 * Fallback TypeScript Series Generator (used if Python subprocess is interrupted).
 */
function fallbackTypeScriptSeries(
  rows: Record<string, any>[],
  specs: UnifiedChartConstructionSpec[]
): any[] {
  return specs.map((spec) => {
    const metric = spec.metric_column;
    const dim = spec.dimension_column;
    const agg = spec.aggregation || 'sum';

    const groups: Record<string, { sum: number; count: number }> = {};
    rows.forEach((r) => {
      const k = String(r[dim] ?? 'Unknown').trim() || 'Unknown';
      const v = Number(r[metric]) || 0;
      if (!groups[k]) groups[k] = { sum: 0, count: 0 };
      groups[k].sum += v;
      groups[k].count += 1;
    });

    const isMoney = /sales|revenue|profit|cost|price|amount/i.test(metric);
    const data = Object.entries(groups)
      .map(([cat, stats]) => {
        const val = agg === 'mean' ? stats.sum / stats.count : stats.sum;
        const rounded = Math.round(val * 100) / 100;
        return {
          [dim]: cat,
          [metric]: rounded,
          name: cat,
          value: rounded,
          formatted_value: isMoney ? `$${rounded.toLocaleString()}` : rounded.toLocaleString(),
        };
      })
      .sort((a, b) => b.value - a.value)
      .slice(0, 10);

    return {
      ...spec,
      data,
    };
  });
}

/**
 * API handler for POST /api/v1/charts/unified
 */
export async function handleUnifiedChartApi(req: any, res: any): Promise<boolean> {
  if (req.method === 'OPTIONS') {
    res.writeHead(200, {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    });
    res.end();
    return true;
  }

  if (req.method !== 'POST') {
    res.writeHead(405, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'Method Not Allowed' }));
    return true;
  }

  try {
    let bodyStr = '';
    for await (const chunk of req) {
      bodyStr += chunk;
    }
    const body = bodyStr ? JSON.parse(bodyStr) : {};
    const rawData = body.data || [];
    const datasetName = body.dataset_name || 'Dataset';

    if (!rawData || rawData.length === 0) {
      res.writeHead(400, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: 'No data records provided' }));
      return true;
    }

    const charts = await runUnifiedChartPipeline(rawData, datasetName);

    res.writeHead(200, {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Credentials': 'true',
    });
    res.end(
      JSON.stringify({
        status: 'success',
        charts,
        generated_at: new Date().toISOString(),
        engine: 'python-pandas-calculations + gemini-construction',
      })
    );
    return true;
  } catch (err) {
    console.error('Unified chart API error:', err);
    res.writeHead(500, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: (err as Error).message }));
    return true;
  }
}
