import { IncomingMessage, ServerResponse } from 'http';
import { spawn } from 'child_process';
import path from 'path';
import { GoogleGenAI } from '@google/genai';

export interface QuestionAnalysisResult {
  status: string;
  question: string;
  intent: {
    metric?: string;
    dimension?: string;
    has_temporal: boolean;
    has_year: boolean;
    has_month: boolean;
    sub_questions: string[];
  };
  direct_answer: string;
  key_metrics: Array<{
    label: string;
    value: string;
    formatted?: string;
    numeric?: number;
    badge?: string;
    is_primary?: boolean;
  }>;
  charts: Array<{
    id: string;
    chart_type: 'bar' | 'line' | 'area' | 'pie' | 'scatter';
    title: string;
    subtitle?: string;
    x_key: string;
    y_keys: string[];
    x_label: string;
    y_label: string;
    legend?: string[];
    highlight_item?: {
      key: string;
      value: string;
      label: string;
    };
    data: Record<string, any>[];
    recharts_config: Record<string, any>;
    data_columns: string[];
  }>;
  calculations_summary: {
    total_rows_analyzed: number;
    metric_used?: string;
    columns_available: string[];
    timestamp: string;
  };
  ai_interpretation?: {
    summary: string;
    takeaways: string[];
    generated_at: string;
    model_used: string;
  };
}

let genAIClient: GoogleGenAI | null = null;
function getGenAI(): GoogleGenAI | null {
  const apiKey = process.env.GEMINI_API_KEY;
  if (!apiKey) return null;
  if (!genAIClient) {
    genAIClient = new GoogleGenAI({ apiKey });
  }
  return genAIClient;
}

/**
 * Robust in-process analytical calculation engine.
 * Computes exact mathematical aggregations, temporal groupings, categorical rankings, and visualizations.
 */
export function runNativeQuestionEngine(
  data: Record<string, any>[],
  question: string,
  datasetName: string = 'Dataset'
): QuestionAnalysisResult {
  const sample = data[0] || {};
  const columns = Object.keys(sample);

  // 1. Detect metric column
  const metricCol =
    columns.find((c) => /^(sales|revenue|amount|profit|total|price|cost|score|volume|value|margin)$/i.test(c)) ||
    columns.find((c) => /sales|revenue|amount|profit|total|price|cost|score|volume|value/i.test(c)) ||
    columns.find((c) => typeof sample[c] === 'number') ||
    columns[1] ||
    columns[0];

  // 2. Detect date/temporal column
  const dateCol = columns.find((c) => /date|time|period|created|timestamp|order_date|month|year/i.test(c));

  // 3. Detect categorical column
  const catCol =
    columns.find((c) => c !== metricCol && c !== dateCol && /category|product|region|segment|channel|rep|country|state|dept|status/i.test(c)) ||
    columns.find((c) => c !== metricCol && c !== dateCol && typeof sample[c] === 'string') ||
    columns.find((c) => c !== metricCol);

  const qLower = question.toLowerCase();
  const isTemporal =
    qLower.includes('month') ||
    qLower.includes('year') ||
    qLower.includes('date') ||
    qLower.includes('trend') ||
    qLower.includes('period') ||
    qLower.includes('quarter') ||
    qLower.includes('daily') ||
    qLower.includes('when') ||
    (Boolean(dateCol) && !qLower.includes('category') && !qLower.includes('product') && !qLower.includes('region'));

  const totalRows = data.length;
  let totalSum = 0;
  let minVal = Infinity;
  let maxVal = -Infinity;

  for (const row of data) {
    const v = Number(row[metricCol]);
    if (!isNaN(v)) {
      totalSum += v;
      if (v < minVal) minVal = v;
      if (v > maxVal) maxVal = v;
    }
  }
  const avgVal = totalRows > 0 ? totalSum / totalRows : 0;

  const formatCurrency = (val: number) =>
    new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: val >= 1000 ? 0 : 2,
    }).format(val);

  let charts: QuestionAnalysisResult['charts'] = [];
  let keyMetrics: QuestionAnalysisResult['key_metrics'] = [];
  let directAnswer = '';
  let highlightItem: any = undefined;

  if (isTemporal && dateCol) {
    // Group by Date / Period
    const dateMap = new Map<string, { sum: number; count: number }>();
    for (const row of data) {
      let rawDate = String(row[dateCol] || '').trim();
      if (!rawDate) continue;
      // Truncate to YYYY-MM if long timestamp
      const match = rawDate.match(/^(\d{4}-\d{2})/);
      const periodKey = match ? match[1] : rawDate.substring(0, 10);
      const cur = dateMap.get(periodKey) || { sum: 0, count: 0 };
      const val = Number(row[metricCol]) || 0;
      cur.sum += val;
      cur.count += 1;
      dateMap.set(periodKey, cur);
    }

    const sortedPeriods = Array.from(dateMap.entries()).sort((a, b) => a[0].localeCompare(b[0]));
    const chartData = sortedPeriods.map(([period, stats]) => ({
      period,
      [metricCol]: Number(stats.sum.toFixed(2)),
      count: stats.count,
    }));

    // Find peak period
    let peakPeriod = '';
    let peakSum = -Infinity;
    for (const item of chartData) {
      if (item[metricCol] > peakSum) {
        peakSum = item[metricCol];
        peakPeriod = item.period;
      }
    }

    highlightItem = {
      key: 'period',
      value: peakPeriod,
      label: `Peak ${peakPeriod}: ${formatCurrency(peakSum)}`,
    };

    directAnswer = `The peak ${metricCol.toLowerCase()} occurred in ${peakPeriod} with ${formatCurrency(peakSum)}, contributing to an aggregate total of ${formatCurrency(totalSum)} across ${chartData.length} tracked intervals.`;

    keyMetrics = [
      {
        label: `Total ${metricCol}`,
        value: formatCurrency(totalSum),
        formatted: formatCurrency(totalSum),
        numeric: totalSum,
        is_primary: true,
      },
      {
        label: `Peak Period (${peakPeriod})`,
        value: formatCurrency(peakSum),
        formatted: formatCurrency(peakSum),
        numeric: peakSum,
        badge: 'Peak Volume',
      },
      {
        label: `Average per Record`,
        value: formatCurrency(avgVal),
        formatted: formatCurrency(avgVal),
        numeric: avgVal,
      },
      {
        label: `Intervals Analyzed`,
        value: String(chartData.length),
        formatted: `${chartData.length} Periods`,
        numeric: chartData.length,
      },
    ];

    charts.push({
      id: 'temporal_trend_chart',
      chart_type: 'area',
      title: `${metricCol.toUpperCase()} Trend Over Time`,
      subtitle: `Calculated distribution across ${chartData.length} temporal periods`,
      x_key: 'period',
      y_keys: [metricCol],
      x_label: 'Time Period',
      y_label: metricCol,
      legend: [metricCol],
      highlight_item: highlightItem,
      data: chartData,
      recharts_config: { stroke: '#3b82f6', fill: '#3b82f6', fillOpacity: 0.2 },
      data_columns: ['period', metricCol],
    });
  } else {
    // Categorical aggregation & ranking
    const dimCol = catCol || columns[0];
    const catMap = new Map<string, { sum: number; count: number }>();

    for (const row of data) {
      const rawCat = String(row[dimCol] || 'Unassigned').trim();
      const cur = catMap.get(rawCat) || { sum: 0, count: 0 };
      const val = Number(row[metricCol]) || 0;
      cur.sum += val;
      cur.count += 1;
      catMap.set(rawCat, cur);
    }

    const sortedCategories = Array.from(catMap.entries())
      .map(([cat, stats]) => ({
        category: cat,
        [metricCol]: Number(stats.sum.toFixed(2)),
        count: stats.count,
        share: totalSum > 0 ? Number(((stats.sum / totalSum) * 100).toFixed(1)) : 0,
      }))
      .sort((a, b) => b[metricCol] - a[metricCol])
      .slice(0, 15);

    const topCategory = sortedCategories[0] || { category: 'N/A', [metricCol]: 0, share: 0 };

    highlightItem = {
      key: 'category',
      value: topCategory.category,
      label: `Top: ${topCategory.category} (${formatCurrency(topCategory[metricCol])})`,
    };

    directAnswer = `The top-ranking ${dimCol} is "${topCategory.category}" with ${formatCurrency(topCategory[metricCol])} (${topCategory.share}% of total), followed by ${sortedCategories.length - 1} other segments.`;

    keyMetrics = [
      {
        label: `Total ${metricCol}`,
        value: formatCurrency(totalSum),
        formatted: formatCurrency(totalSum),
        numeric: totalSum,
        is_primary: true,
      },
      {
        label: `Top ${dimCol}`,
        value: topCategory.category,
        formatted: `${topCategory.category} (${topCategory.share}%)`,
        badge: 'Top Segment',
      },
      {
        label: `Top Volume`,
        value: formatCurrency(topCategory[metricCol]),
        formatted: formatCurrency(topCategory[metricCol]),
        numeric: topCategory[metricCol],
      },
      {
        label: `Distinct Segments`,
        value: String(catMap.size),
        formatted: `${catMap.size} Segments`,
        numeric: catMap.size,
      },
    ];

    charts.push({
      id: 'categorical_distribution_chart',
      chart_type: 'bar',
      title: `${metricCol.toUpperCase()} by ${dimCol}`,
      subtitle: `Ranked comparison of top ${sortedCategories.length} segments`,
      x_key: 'category',
      y_keys: [metricCol],
      x_label: dimCol,
      y_label: metricCol,
      legend: [metricCol],
      highlight_item: highlightItem,
      data: sortedCategories,
      recharts_config: { fill: '#3b82f6' },
      data_columns: ['category', metricCol],
    });
  }

  return {
    status: 'success',
    question,
    intent: {
      metric: metricCol,
      dimension: isTemporal ? dateCol : catCol,
      has_temporal: isTemporal,
      has_year: qLower.includes('year') || qLower.includes('20'),
      has_month: qLower.includes('month'),
      sub_questions: [],
    },
    direct_answer: directAnswer,
    key_metrics: keyMetrics,
    charts,
    calculations_summary: {
      total_rows_analyzed: totalRows,
      metric_used: metricCol,
      columns_available: columns,
      timestamp: new Date().toISOString(),
    },
  };
}

/**
 * Runs the Python QuestionChartEngine to perform calculations and prepare targeted chart data.
 * Gracefully falls back to the high-performance native calculation engine if Python is unavailable.
 */
export async function runPythonQuestionEngine(
  data: Record<string, any>[],
  question: string,
  datasetName: string = 'Dataset'
): Promise<QuestionAnalysisResult> {
  return new Promise((resolve) => {
    const scriptPath = path.resolve(process.cwd(), 'backend/src/services/question_chart_engine.py');
    const args = ['--question', question, '--name', datasetName];

    try {
      const pyProcess = spawn('python3', [scriptPath, ...args], {
        env: { ...process.env, PYTHONUNBUFFERED: '1' },
        cwd: process.cwd(),
      });

      let stdoutData = '';
      let stderrData = '';

      pyProcess.stdout.on('data', (chunk) => {
        stdoutData += chunk.toString();
      });

      pyProcess.stderr.on('data', (chunk) => {
        stderrData += chunk.toString();
      });

      pyProcess.on('close', (code) => {
        if (code !== 0) {
          console.warn(`Python QuestionChartEngine exited with code ${code}. Falling back to native calculation engine.`);
          resolve(runNativeQuestionEngine(data, question, datasetName));
          return;
        }

        try {
          const jsonStart = stdoutData.indexOf('{');
          const jsonEnd = stdoutData.lastIndexOf('}');
          if (jsonStart === -1 || jsonEnd === -1) {
            throw new Error('No JSON output returned from Python question engine');
          }
          const jsonStr = stdoutData.substring(jsonStart, jsonEnd + 1);
          const parsed = JSON.parse(jsonStr) as QuestionAnalysisResult;
          resolve(parsed);
        } catch {
          console.warn('Failed to parse Python question engine output. Falling back to native calculation engine.');
          resolve(runNativeQuestionEngine(data, question, datasetName));
        }
      });

      pyProcess.on('error', (err) => {
        console.warn(`Python QuestionChartEngine spawn error (${err.message}). Falling back to native calculation engine.`);
        resolve(runNativeQuestionEngine(data, question, datasetName));
      });

      // Write input data directly to stdin
      pyProcess.stdin.write(JSON.stringify(data));
      pyProcess.stdin.end();
    } catch {
      resolve(runNativeQuestionEngine(data, question, datasetName));
    }
  });
}

/**
 * AI interpretation layer:
 * Interprets the calculated dataset and outputs strategic business insights.
 * Explicitly DOES NOT perform calculations.
 */
export async function generateAIInterpretation(
  question: string,
  calculationResult: QuestionAnalysisResult
): Promise<{ summary: string; takeaways: string[]; generated_at: string; model_used: string }> {
  const client = getGenAI();

  // Factual context from calculations
  const primaryAnswer = calculationResult.direct_answer;
  const metricsContext = calculationResult.key_metrics
    .map((m) => `${m.label}: ${m.formatted || m.value} ${m.badge ? `(${m.badge})` : ''}`)
    .join('; ');

  const chartContext = calculationResult.charts
    .map((c) => {
      const samplePoints = c.data.slice(0, 5).map((d) => JSON.stringify(d)).join(', ');
      return `${c.title} (${c.chart_type} chart): sample [${samplePoints}]`;
    })
    .join('\n');

  if (client) {
    try {
      const prompt = `
You are an executive BI decision-support specialist.
The computational engine has completed all numerical calculations, aggregations, and chart data formatting for this user question.

User Question: "${question}"

Calculations and Findings:
- Direct Calculated Answer: ${primaryAnswer}
- Exact Metrics: ${metricsContext}
- Generated Visualizations:
${chartContext}

Task:
Interpret these calculated findings for business leaders in a concise, authoritative manner.
Rules:
1. DO NOT perform arithmetic or recalculations. Strictly interpret the facts provided above.
2. Structure your response as JSON with two fields:
   - "summary": A 2-paragraph executive narrative explaining the core answer, key trends, and drivers.
   - "takeaways": An array of 3 actionable business bullet points based on the findings.
`;

      const response = await client.models.generateContent({
        model: 'gemini-2.5-flash',
        contents: prompt,
        config: {
          responseMimeType: 'application/json',
        },
      });

      const responseText = response.text || '';
      const parsed = JSON.parse(responseText);

      return {
        summary: parsed.summary || primaryAnswer,
        takeaways: Array.isArray(parsed.takeaways) ? parsed.takeaways : [primaryAnswer],
        generated_at: new Date().toISOString(),
        model_used: 'gemini-2.5-flash',
      };
    } catch (aiErr) {
      console.warn('Gemini API call failed, falling back to rule-based executive summary:', aiErr);
    }
  }

  // Fallback executive interpretation derived from verified calculations
  const defaultTakeaways: string[] = [
    primaryAnswer,
    calculationResult.key_metrics.find((m) => m.badge)?.badge
      ? `Performance driver: ${calculationResult.key_metrics.find((m) => m.badge)?.label} stood out as key volume contributor.`
      : `Data aggregated across ${calculationResult.calculations_summary.total_rows_analyzed} transaction records.`,
    `Recommended action: Focus resource allocation on top-performing timeframes and high-yield segments.`,
  ];

  return {
    summary: `${primaryAnswer} Analysis of the dataset indicates clear volume distribution across the observed periods, highlighting operational peaks and baseline levels.`,
    takeaways: defaultTakeaways,
    generated_at: new Date().toISOString(),
    model_used: 'InsightIQ-RuleBased-Interpreter',
  };
}

/**
 * HTTP handler for Question-Driven Analytics API.
 */
export async function handleQuestionAnalysisApi(
  req: IncomingMessage,
  res: ServerResponse
): Promise<boolean> {
  const url = req.url || '';
  if (!url.startsWith('/api/v1/analytics/question') || req.method !== 'POST') {
    return false;
  }

  try {
    let body = '';
    for await (const chunk of req) {
      body += chunk;
    }

    const payload = JSON.parse(body || '{}');
    const { data, question, datasetName } = payload;

    if (!Array.isArray(data) || data.length === 0) {
      res.writeHead(400, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: 'No dataset records provided in request' }));
      return true;
    }

    if (!question || typeof question !== 'string' || question.trim().length === 0) {
      res.writeHead(400, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: 'Question string is required' }));
      return true;
    }

    // 1. Python calculation and chart preparation
    const pythonResult = await runPythonQuestionEngine(data, question, datasetName || 'Dataset');

    // 2. AI interpretation of the calculated results
    const aiInterpretation = await generateAIInterpretation(question, pythonResult);
    pythonResult.ai_interpretation = aiInterpretation;

    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(
      JSON.stringify({
        success: true,
        data: pythonResult,
      })
    );
    return true;
  } catch (error) {
    console.error('Error handling question analysis API:', error);
    res.writeHead(500, { 'Content-Type': 'application/json' });
    res.end(
      JSON.stringify({
        error: error instanceof Error ? error.message : 'Unknown server error',
      })
    );
    return true;
  }
}
