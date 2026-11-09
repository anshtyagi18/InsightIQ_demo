/**
 * Unified Chart Service
 *
 * Calls the unified Python + Gemini pipeline:
 * - Python executes all statistical calculations and series data aggregations.
 * - Gemini constructs the essential charts (quality over quantity, 3-5 charts).
 * - Falls back to local essential charts if offline or unreachable.
 */

import { ChartConfig, DatasetProfile, generateCharts, profileDataset } from '@/services/bi-engine';

export async function fetchUnifiedCharts(
  data: Record<string, any>[],
  datasetName: string = 'Dataset'
): Promise<ChartConfig[]> {
  if (!data || data.length === 0) return [];

  try {
    const response = await fetch('/api/v1/charts/unified', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        data,
        dataset_name: datasetName,
      }),
    });

    if (!response.ok) {
      throw new Error(`Unified chart API failed with status ${response.status}`);
    }

    const json = await response.json();
    if (json && Array.isArray(json.charts) && json.charts.length > 0) {
      return json.charts;
    }
  } catch (err) {
    console.warn('Unified chart pipeline network call failed, using client-side essential fallback:', err);
  }

  // Fallback to essential client-side charts
  const profile = profileDataset(data);
  return generateCharts(data, profile);
}
