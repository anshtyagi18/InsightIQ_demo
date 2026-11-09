/**
 * Intelligent Dataset Interpretation Service for InsightIQ
 * 
 * Strict architectural boundaries:
 * 1. Python/Pandas or Native analytical engine does ALL cleaning, calculations, and analysis.
 * 2. Only processed/structured statistical results are sent to Gemini.
 * 3. Gemini generates the main dashboard Summary, Key Insights, and Executive Business Insights
 *    based strictly on the actual dataset.
 * 4. Gemini identifies which specific charts are useful and explains why.
 * 5. Gemini must NOT create charts or perform calculations.
 * 6. The backend engine generates the recommended charts with correct titles, labels, values,
 *    legends, and Recharts formatting.
 * 7. Gemini API key is stored securely in backend environment variables and NEVER exposed to frontend.
 */

import { IncomingMessage, ServerResponse } from 'http';
import { GoogleGenAI } from '@google/genai';
import * as XLSX from 'xlsx';

export interface ColumnStat {
  column: string;
  type: 'numeric' | 'categorical' | 'date';
  null_count: number;
  distinct_count: number;
  sum?: number;
  mean?: number;
  median?: number;
  min?: number;
  max?: number;
  top_values?: Array<{ value: string; count: number; percentage: number }>;
}

export interface StructuredDatasetProfile {
  dataset_name: string;
  total_rows: number;
  total_columns: number;
  numeric_columns: string[];
  categorical_columns: string[];
  date_columns: string[];
  columns_stats: ColumnStat[];
  aggregations: Array<{
    metric: string;
    dimension: string;
    breakdown: Array<{ category: string; sum: number; mean: number; count: number }>;
  }>;
  temporal_trends: Array<{ period: string; value: number }>;
}

export interface GeminiInterpretation {
  executive_summary: string;
  key_insights: Array<{
    title: string;
    observation: string;
    metric_reference: string;
    impact: 'positive' | 'neutral' | 'negative';
  }>;
  executive_business_insights: Array<{
    strategic_theme: string;
    finding: string;
    actionable_recommendation: string;
    priority: 'high' | 'medium' | 'low';
  }>;
  recommended_charts: Array<{
    id: string;
    chart_type: 'bar' | 'line' | 'area' | 'pie' | 'scatter';
    title: string;
    description: string;
    metric_column: string;
    dimension_column: string;
    aggregation: 'sum' | 'mean' | 'count';
    why_useful: string;
  }>;
}

export interface GeneratedChart {
  id: string;
  title: string;
  description: string;
  why_useful: string;
  chart_type: string;
  metric_column: string;
  dimension_column: string;
  aggregation: string;
  data: Record<string, any>[];
  data_columns: string[];
  color: string;
  recharts_config: {
    type: string;
    dataKey: string;
    xAxisKey: string;
    fill: string;
    stroke: string;
    strokeWidth: number;
    height: number;
  };
}

/**
 * Step 1: Analytical Engine cleans data and computes ALL mathematical statistics.
 * No raw individual data rows are sent to Gemini.
 */
export function calculateDatasetProfile(
  rows: Record<string, any>[],
  datasetName: string = 'Uploaded Dataset'
): { profile: StructuredDatasetProfile; cleanedRows: Record<string, any>[] } {
  if (!rows || rows.length === 0) {
    throw new Error('Dataset contains no records');
  }

  const cleanedRows: Record<string, any>[] = [];
  const rawCols = Object.keys(rows[0] || {});
  const sample = rows[0] || {};

  // Detect column types
  const numericCols: string[] = [];
  const dateCols: string[] = [];
  const categoricalCols: string[] = [];

  for (const col of rawCols) {
    const colLower = col.toLowerCase();
    const isDateName = /date|time|year|month|period|timestamp|created/i.test(colLower);

    let numericCount = 0;
    let dateCount = 0;
    const testLimit = Math.min(rows.length, 50);

    for (let i = 0; i < testLimit; i++) {
      const val = rows[i][col];
      if (val === null || val === undefined || val === '') continue;

      if (typeof val === 'number') {
        numericCount++;
      } else if (typeof val === 'string') {
        const cleanStr = val.replace(/[$€£¥%]/g, '').replace(/,/g, '').trim();
        if (!isNaN(Number(cleanStr)) && cleanStr !== '') {
          numericCount++;
        } else if (isDateName && !isNaN(Date.parse(val))) {
          dateCount++;
        }
      }
    }

    if (numericCount > testLimit * 0.5) {
      numericCols.push(col);
    } else if (dateCount > testLimit * 0.3 || isDateName) {
      dateCols.push(col);
    } else {
      categoricalCols.push(col);
    }
  }

  // Normalize rows
  for (const row of rows) {
    const cleanRow: Record<string, any> = {};
    for (const col of rawCols) {
      const val = row[col];
      if (numericCols.includes(col)) {
        if (typeof val === 'number') {
          cleanRow[col] = val;
        } else if (typeof val === 'string') {
          const num = Number(val.replace(/[$€£¥%]/g, '').replace(/,/g, '').trim());
          cleanRow[col] = isNaN(num) ? 0 : num;
        } else {
          cleanRow[col] = 0;
        }
      } else if (dateCols.includes(col)) {
        cleanRow[col] = val ? String(val) : 'N/A';
      } else {
        cleanRow[col] = val !== null && val !== undefined ? String(val).trim() : 'Unknown';
      }
    }
    cleanedRows.push(cleanRow);
  }

  const totalRows = cleanedRows.length;
  const columnsStats: ColumnStat[] = [];

  // Compute Numeric Statistics
  for (const col of numericCols) {
    const values = cleanedRows.map((r) => Number(r[col]) || 0);
    const sum = values.reduce((a, b) => a + b, 0);
    const mean = totalRows > 0 ? sum / totalRows : 0;
    const sorted = [...values].sort((a, b) => a - b);
    const min = sorted[0] ?? 0;
    const max = sorted[sorted.length - 1] ?? 0;
    const median = sorted[Math.floor(sorted.length / 2)] ?? 0;

    columnsStats.push({
      column: col,
      type: 'numeric',
      null_count: rows.filter((r) => r[col] === null || r[col] === undefined || r[col] === '').length,
      distinct_count: new Set(values).size,
      sum: Math.round(sum * 100) / 100,
      mean: Math.round(mean * 100) / 100,
      median: Math.round(median * 100) / 100,
      min: Math.round(min * 100) / 100,
      max: Math.round(max * 100) / 100,
    });
  }

  // Compute Categorical Statistics
  for (const col of categoricalCols) {
    const counts: Record<string, number> = {};
    for (const r of cleanedRows) {
      const v = String(r[col] || 'Unknown');
      counts[v] = (counts[v] || 0) + 1;
    }
    const sortedEntries = Object.entries(counts).sort((a, b) => b[1] - a[1]);
    const topValues = sortedEntries.slice(0, 5).map(([val, count]) => ({
      value: val,
      count,
      percentage: Math.round((count / totalRows) * 1000) / 10,
    }));

    columnsStats.push({
      column: col,
      type: 'categorical',
      null_count: rows.filter((r) => r[col] === null || r[col] === undefined || r[col] === '').length,
      distinct_count: sortedEntries.length,
      top_values: topValues,
    });
  }

  // Calculate Primary Aggregations (e.g. Top Numeric by Top Categorical)
  const aggregations: Array<{
    metric: string;
    dimension: string;
    breakdown: Array<{ category: string; sum: number; mean: number; count: number }>;
  }> = [];

  if (numericCols.length > 0 && categoricalCols.length > 0) {
    const primaryNum = numericCols[0];
    const primaryCat = categoricalCols[0];

    const catSums: Record<string, { sum: number; count: number }> = {};
    for (const r of cleanedRows) {
      const cat = String(r[primaryCat] || 'Unknown');
      const val = Number(r[primaryNum]) || 0;
      if (!catSums[cat]) catSums[cat] = { sum: 0, count: 0 };
      catSums[cat].sum += val;
      catSums[cat].count += 1;
    }

    const breakdown = Object.entries(catSums)
      .map(([category, stats]) => ({
        category,
        sum: Math.round(stats.sum * 100) / 100,
        mean: Math.round((stats.sum / stats.count) * 100) / 100,
        count: stats.count,
      }))
      .sort((a, b) => b.sum - a.sum)
      .slice(0, 10);

    aggregations.push({
      metric: primaryNum,
      dimension: primaryCat,
      breakdown,
    });
  }

  // Calculate Temporal Trends if Date column exists
  const temporalTrends: Array<{ period: string; value: number }> = [];
  if (dateCols.length > 0 && numericCols.length > 0) {
    const primaryDate = dateCols[0];
    const primaryNum = numericCols[0];
    const periodSums: Record<string, number> = {};

    for (const r of cleanedRows) {
      const dStr = String(r[primaryDate] || '');
      let period = dStr;
      if (dStr.length >= 7) {
        period = dStr.substring(0, 7); // YYYY-MM
      }
      periodSums[period] = (periodSums[period] || 0) + (Number(r[primaryNum]) || 0);
    }

    const sortedPeriods = Object.keys(periodSums).sort().slice(0, 12);
    for (const p of sortedPeriods) {
      temporalTrends.push({
        period: p,
        value: Math.round(periodSums[p] * 100) / 100,
      });
    }
  }

  return {
    profile: {
      dataset_name: datasetName,
      total_rows: totalRows,
      total_columns: rawCols.length,
      numeric_columns: numericCols,
      categorical_columns: categoricalCols,
      date_columns: dateCols,
      columns_stats: columnsStats,
      aggregations,
      temporal_trends: temporalTrends,
    },
    cleanedRows,
  };
}

/**
 * Step 2: Send ONLY the processed/structured results to Gemini.
 * Gemini interprets data and recommends useful charts with business rationale.
 * Gemini does NOT perform calculations or create charts.
 */
export async function interpretWithGemini(
  profile: StructuredDatasetProfile
): Promise<GeminiInterpretation> {
  const apiKey = process.env.GEMINI_API_KEY || process.env.GOOGLE_API_KEY;
  if (!apiKey) {
    console.warn('GEMINI_API_KEY not configured, using deterministic rule-based interpretation');
    return generateRuleBasedInterpretation(profile);
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
You are the Executive Chief Data Scientist for InsightIQ.
You are given pre-computed statistical analytics for a dataset. All mathematical cleaning, aggregations,
and profiling have ALREADY been accurately performed by the backend engine.

STRICT INSTRUCTIONS:
1. DO NOT perform calculations or math.
2. DO NOT output chart SVGs, HTML, or raw chart code.
3. GROUND ALL INSIGHTS strictly on the actual calculated numbers provided below. Quote exact figures and metrics.
4. Avoid generic platitudes like "sales are good" or "monitor metrics regularly".
5. Recommend 3 to 5 SPECIFIC CHARTS that are genuinely useful for this dataset, explaining WHY each chart is useful.
6. Return ONLY valid JSON matching the exact schema below.

PRE-CALCULATED DATASET PROFILE:
${JSON.stringify(profile, null, 2)}

REQUIRED JSON RESPONSE SCHEMA:
{
  "executive_summary": "2 to 3 sentences delivering an executive narrative of the dataset, directly referencing total rows (${profile.total_rows}) and primary metric sums/averages.",
  "key_insights": [
    {
      "title": "Concise factual insight title",
      "observation": "Factual observation citing actual calculated figures from the data profile",
      "metric_reference": "Column name",
      "impact": "positive | neutral | negative"
    }
  ],
  "executive_business_insights": [
    {
      "strategic_theme": "e.g. Volume Concentration, Market Variance, or Operational Momentum",
      "finding": "Business finding directly supported by the pre-computed metrics",
      "actionable_recommendation": "Concrete operational recommendation based on the data findings",
      "priority": "high | medium | low"
    }
  ],
  "recommended_charts": [
    {
      "id": "chart_1",
      "chart_type": "bar | line | area | pie | scatter",
      "title": "Business title for the chart",
      "description": "What this chart visualizes",
      "metric_column": "Exact numeric column name from numeric_columns",
      "dimension_column": "Exact categorical or date column from columns",
      "aggregation": "sum | mean | count",
      "why_useful": "Precise rationale explaining why this visualization provides high-value intelligence for this specific dataset"
    }
  ]
}
`;

  try {
    const response = await ai.models.generateContent({
      model: 'gemini-3.8-flash',
      contents: prompt,
      config: {
        temperature: 0.2,
        maxOutputTokens: 2048,
        responseMimeType: 'application/json',
      },
    });

    let text = response.text || '';
    text = text.trim();
    if (text.startsWith('```json')) text = text.slice(7);
    if (text.endsWith('```')) text = text.slice(0, -3);
    text = text.trim();

    const parsed: GeminiInterpretation = JSON.parse(text);
    return parsed;
  } catch (err) {
    console.error('Gemini interpretation error, falling back to rule-based engine:', err);
    return generateRuleBasedInterpretation(profile);
  }
}

/**
 * Step 3: Backend engine generates the recommended charts with correct titles,
 * labels, values, legends, and Recharts formatting.
 */
export function generateRecommendedCharts(
  cleanedRows: Record<string, any>[],
  recommendations: GeminiInterpretation['recommended_charts']
): GeneratedChart[] {
  const generated: GeneratedChart[] = [];
  const palette = ['#3b82f6', '#10b981', '#8b5cf6', '#f59e0b', '#06b6d4', '#ec4899', '#6366f1'];

  for (let i = 0; i < recommendations.length; i++) {
    const rec = recommendations[i];
    try {
      const metricCol = rec.metric_column;
      const dimCol = rec.dimension_column;
      const agg = rec.aggregation || 'sum';
      const chartType = rec.chart_type || 'bar';

      // Group and aggregate data
      const groups: Record<string, { sum: number; count: number }> = {};
      for (const row of cleanedRows) {
        const dimVal = String(row[dimCol] ?? 'Unknown');
        const metricVal = Number(row[metricCol]) || 0;
        if (!groups[dimVal]) groups[dimVal] = { sum: 0, count: 0 };
        groups[dimVal].sum += metricVal;
        groups[dimVal].count += 1;
      }

      let chartData = Object.entries(groups).map(([cat, val]) => {
        const finalVal =
          agg === 'mean' ? val.sum / val.count : agg === 'count' ? val.count : val.sum;
        const rounded = Math.round(finalVal * 100) / 100;
        const isMoney = /revenue|sales|cost|price|profit|amount/i.test(metricCol);
        return {
          [dimCol]: cat,
          [metricCol]: rounded,
          name: cat,
          value: rounded,
          formatted_value: isMoney ? `$${rounded.toLocaleString()}` : rounded.toLocaleString(),
        };
      });

      // Sort
      if (['line', 'area'].includes(chartType) && /date|time|period|year|month/i.test(dimCol)) {
        chartData.sort((a, b) => a[dimCol].localeCompare(b[dimCol]));
        chartData = chartData.slice(0, 15);
      } else {
        chartData.sort((a, b) => b.value - a.value);
        chartData = chartData.slice(0, 10);
      }

      const color = palette[i % palette.length];

      generated.push({
        id: rec.id || `chart_${i + 1}`,
        title: rec.title || `${metricCol} by ${dimCol}`,
        description: rec.description || `Breakdown of ${metricCol} across ${dimCol}`,
        why_useful: rec.why_useful || 'Reveals core performance patterns across segments.',
        chart_type: chartType,
        metric_column: metricCol,
        dimension_column: dimCol,
        aggregation: agg,
        data: chartData,
        data_columns: [dimCol, metricCol],
        color,
        recharts_config: {
          type: chartType.charAt(0).toUpperCase() + chartType.slice(1) + 'Chart',
          dataKey: metricCol,
          xAxisKey: dimCol,
          fill: color,
          stroke: color,
          strokeWidth: 2,
          height: 320,
        },
      });
    } catch (err) {
      console.error(`Failed to generate recommended chart ${rec.id}:`, err);
    }
  }

  return generated;
}

/**
 * Deterministic fallback interpretation when Gemini API is offline or without key.
 */
function generateRuleBasedInterpretation(profile: StructuredDatasetProfile): GeminiInterpretation {
  const totalRows = profile.total_rows;
  const numCol = profile.numeric_columns[0] || 'Value';
  const catCol = profile.categorical_columns[0] || 'Category';

  const numStat = profile.columns_stats.find((s) => s.column === numCol);
  const catStat = profile.columns_stats.find((s) => s.column === catCol);

  const totalSum = numStat?.sum ?? 0;
  const avgVal = numStat?.mean ?? 0;
  const topCat = catStat?.top_values?.[0]?.value ?? 'Top Segment';
  const topPct = catStat?.top_values?.[0]?.percentage ?? 0;

  return {
    executive_summary: `The dataset contains ${totalRows.toLocaleString()} observations across ${profile.total_columns} attributes. Primary quantitative performance in ${numCol} totals $${totalSum.toLocaleString()} with an average of $${avgVal.toLocaleString()} per record. Distribution is concentrated in ${catCol}, with ${topCat} representing ${topPct}% of activity.`,
    key_insights: [
      {
        title: `Total Volume in ${numCol}`,
        observation: `Aggregate ${numCol} reached $${totalSum.toLocaleString()} with a median value of $${numStat?.median ?? 0}.`,
        metric_reference: numCol,
        impact: 'positive',
      },
      {
        title: `Primary Segment Dominance (${catCol})`,
        observation: `${topCat} accounts for ${topPct}% of records, indicating significant category concentration.`,
        metric_reference: catCol,
        impact: 'neutral',
      },
      {
        title: 'Operational Baseline',
        observation: `Mean ${numCol} benchmark sits at $${avgVal.toLocaleString()} per observation.`,
        metric_reference: numCol,
        impact: 'neutral',
      },
    ],
    executive_business_insights: [
      {
        strategic_theme: 'Category Concentration',
        finding: `Throughput is heavily weighted toward ${topCat} (${topPct}% volume).`,
        actionable_recommendation: `Align capacity and operational workflows to support demand in ${topCat} while investigating growth opportunities in secondary segments.`,
        priority: 'high',
      },
      {
        strategic_theme: 'Yield & Anomaly Detection',
        finding: `Baseline performance average of $${avgVal.toLocaleString()} provides a dependable benchmark.`,
        actionable_recommendation: `Implement monitoring thresholds for outliers deviating significantly from standard performance norms.`,
        priority: 'medium',
      },
    ],
    recommended_charts: [
      {
        id: 'chart_1',
        chart_type: 'bar',
        title: `${numCol} by ${catCol}`,
        description: `Comparative breakdown of ${numCol} across top ${catCol} segments`,
        metric_column: numCol,
        dimension_column: catCol,
        aggregation: 'sum',
        why_useful: `Highlights primary volume drivers and exposes segment skew across ${catCol}.`,
      },
      ...(profile.date_columns.length > 0
        ? [
            {
              id: 'chart_2',
              chart_type: 'area' as const,
              title: `${numCol} Trend Over Time`,
              description: `Chronological trajectory of ${numCol}`,
              metric_column: numCol,
              dimension_column: profile.date_columns[0],
              aggregation: 'sum' as const,
              why_useful: `Uncovers temporal momentum, peak periods, and seasonal trajectories.`,
            },
          ]
        : []),
    ],
  };
}

/**
 * HTTP Request Handler for /api/v1/analytics/interpret
 */
export async function handleDatasetInterpretationApi(
  req: IncomingMessage,
  res: ServerResponse
): Promise<boolean> {
  const url = req.url || '';
  if (!url.startsWith('/api/v1/analytics/interpret') && !url.startsWith('/api/v1/files/interpret')) {
    return false;
  }

  if (req.method !== 'POST') {
    res.writeHead(405, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'Method not allowed' }));
    return true;
  }

  try {
    let bodyStr = '';
    for await (const chunk of req) {
      bodyStr += chunk;
    }
    const body = bodyStr ? JSON.parse(bodyStr) : {};
    const rawData: Record<string, any>[] = body.data || [];
    const datasetName = body.dataset_name || 'Uploaded Dataset';

    if (!rawData || rawData.length === 0) {
      res.writeHead(400, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: 'No data records provided for interpretation' }));
      return true;
    }

    // Step 1: Analytical calculations
    const { profile, cleanedRows } = calculateDatasetProfile(rawData, datasetName);

    // Step 2: Gemini interpretation (summary, insights, chart recommendations)
    const interpretation = await interpretWithGemini(profile);

    // Step 3: Backend chart generation with exact values and formatting
    const charts = generateRecommendedCharts(cleanedRows, interpretation.recommended_charts);

    const result = {
      status: 'success',
      dataset_name: datasetName,
      dataset_summary: {
        total_rows: profile.total_rows,
        total_columns: profile.total_columns,
        numeric_columns: profile.numeric_columns,
        categorical_columns: profile.categorical_columns,
        date_columns: profile.date_columns,
        primary_metric: profile.numeric_columns[0] || null,
        primary_dimension: profile.categorical_columns[0] || null,
      },
      calculated_metrics: profile.columns_stats,
      aggregations: profile.aggregations,
      temporal_trends: profile.temporal_trends,
      ai_interpretation: {
        executive_summary: interpretation.executive_summary,
        key_insights: interpretation.key_insights,
        executive_business_insights: interpretation.executive_business_insights,
        recommended_charts: interpretation.recommended_charts,
        ai_model: 'gemini-3.8-flash',
      },
      charts,
    };

    res.writeHead(200, {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Credentials': 'true',
    });
    res.end(JSON.stringify(result));
    return true;
  } catch (err) {
    console.error('Error in handleDatasetInterpretationApi:', err);
    res.writeHead(500, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: (err as Error).message }));
    return true;
  }
}
