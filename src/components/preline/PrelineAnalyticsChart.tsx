/**
 * Preline Analytics Area, Line & Distribution Chart Component
 * Fully reactive & dynamically bound to active DatasetProfile.
 * Pure Smooth Z-Black (#0e0e11) with crisp zinc-800 borders.
 */

import React, { useState, useMemo } from 'react';
import { 
  ResponsiveContainer, 
  AreaChart, 
  Area, 
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis, 
  YAxis, 
  Tooltip, 
  CartesianGrid,
  Legend
} from 'recharts';
import { TrendingUp, BarChart3, LineChart as LineIcon, AreaChart as AreaIcon } from 'lucide-react';
import { DatasetProfile } from '@/services/data-intelligence.service';

export interface PrelineAnalyticsChartProps {
  profile?: DatasetProfile | null;
  data?: any[];
  title?: string;
  totalValue?: string;
  trendPercentage?: string;
}

export const PrelineAnalyticsChart: React.FC<PrelineAnalyticsChartProps> = ({
  profile,
  data: fallbackData,
  title: customTitle,
  totalValue: customTotal,
  trendPercentage = "+12.5%",
}) => {
  const [activeTab, setActiveTab] = useState<'overview' | 'trends' | 'distribution'>('overview');

  // Derive dynamic axes and data points from active profile
  const { chartData, xKey, yKey1, yKey2, displayTitle, displayTotal } = useMemo(() => {
    if (!profile || !profile.preview || profile.preview.length === 0) {
      const defaultData = fallbackData || [
        { name: '00:00', visitors: 1420, sessions: 980 },
        { name: '03:00', visitors: 980, sessions: 710 },
        { name: '06:00', visitors: 2200, sessions: 1650 },
        { name: '09:00', visitors: 4800, sessions: 3900 },
        { name: '12:00', visitors: 6200, sessions: 5100 },
        { name: '15:00', visitors: 5800, sessions: 4750 },
        { name: '18:00', visitors: 7400, sessions: 6100 },
        { name: '21:00', visitors: 4900, sessions: 3800 },
      ];
      return {
        chartData: defaultData,
        xKey: 'name',
        yKey1: 'visitors',
        yKey2: 'sessions',
        displayTitle: customTitle || 'Visitors & Sessions Growth',
        displayTotal: customTotal || '54,382'
      };
    }

    // Find candidate numeric columns
    const numCols = profile.columns
      .filter((c) => c.type === 'numeric' || c.type === 'integer' || c.type === 'float')
      .map((c) => c.name);

    // Find candidate categorical / date columns
    const catCols = profile.columns
      .filter((c) => c.type === 'categorical' || c.type === 'string' || c.type === 'datetime')
      .map((c) => c.name);

    // Pick primary numeric metric
    const preferredMetrics = ['Revenue', 'Sales', 'TotalCharges', 'MonthlyCharges', 'Price', 'NetIncome', 'GrossProfit', 'Expenses', 'Amount'];
    const yCol1 = preferredMetrics.find((m) => numCols.includes(m)) || numCols[0] || 'Metric';
    const remainingNum = numCols.filter((c) => c !== yCol1);
    const yCol2 = remainingNum[0] || null;

    // Pick dimension / category
    const preferredDimensions = ['Category', 'Date', 'Month', 'Region', 'Product', 'Customer_Segment', 'Contract', 'Gender'];
    const xCol = preferredDimensions.find((d) => catCols.includes(d)) || catCols[0] || 'Index';

    if (activeTab === 'distribution') {
      // Group by xCol and sum or average yCol1
      const grouped: Record<string, { count: number; total: number }> = {};
      profile.preview.forEach((row) => {
        const key = String(row[xCol] || 'Other');
        const val = Number(row[yCol1]) || 0;
        if (!grouped[key]) grouped[key] = { count: 0, total: 0 };
        grouped[key].count += 1;
        grouped[key].total += val;
      });

      const distData = Object.entries(grouped)
        .map(([k, v]) => ({
          name: k,
          [yCol1]: Math.round(v.total / (v.count || 1)),
          count: v.count
        }))
        .slice(0, 10);

      const totalVal = distData.reduce((acc, d) => acc + (d[yCol1] || 0), 0);
      return {
        chartData: distData,
        xKey: 'name',
        yKey1: yCol1,
        yKey2: 'count',
        displayTitle: `${yCol1} Distribution by ${xCol}`,
        displayTotal: `$${totalVal.toLocaleString()}`
      };
    }

    // Overview & Trends: Sequential / time samples from preview
    const sampleSize = Math.min(20, profile.preview.length);
    const step = Math.max(1, Math.floor(profile.preview.length / sampleSize));
    const sequentialData: any[] = [];
    let sumTotal = 0;

    for (let i = 0; i < profile.preview.length && sequentialData.length < sampleSize; i += step) {
      const row = profile.preview[i];
      const val1 = Number(row[yCol1]) || 0;
      sumTotal += val1;
      const point: any = {
        name: String(row[xCol] || `Row #${i + 1}`),
        [yCol1]: Math.round(val1)
      };
      if (yCol2) {
        point[yCol2] = Math.round(Number(row[yCol2]) || 0);
      }
      sequentialData.push(point);
    }

    // Compute estimated dataset metric total
    const meanVal = sumTotal / (sequentialData.length || 1);
    const estimatedDatasetTotal = Math.round(meanVal * profile.total_rows);

    return {
      chartData: sequentialData,
      xKey: 'name',
      yKey1: yCol1,
      yKey2: yCol2,
      displayTitle: `${yCol1} Analytics (${profile.dataset_name})`,
      displayTotal: estimatedDatasetTotal > 1000 ? `$${estimatedDatasetTotal.toLocaleString()}` : `${estimatedDatasetTotal}`
    };
  }, [profile, fallbackData, customTitle, customTotal, activeTab]);

  return (
    <div className="bg-[#0e0e11] rounded-xl border border-[#27272a] p-5 shadow-xs transition-colors select-none">
      {/* Header Row */}
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
        <div>
          <span className="text-xs font-semibold text-zinc-400 uppercase tracking-wider">
            {displayTitle}
          </span>
          <div className="flex items-baseline gap-2 mt-0.5">
            <span className="text-2xl font-bold tracking-tight text-zinc-100 font-sans">
              {displayTotal}
            </span>
            <span className="inline-flex items-center gap-0.5 text-xs font-semibold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-1.5 py-0.5 rounded">
              <TrendingUp className="w-3 h-3 stroke-[2.5]" />
              {trendPercentage}
            </span>
          </div>
        </div>

        {/* View Switcher Tabs: Overview | Trends | Distribution */}
        <div className="flex items-center p-0.5 bg-[#141418] rounded-lg text-xs font-medium text-zinc-400 border border-[#27272a]">
          <button
            onClick={() => setActiveTab('overview')}
            className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md transition-all ${
              activeTab === 'overview'
                ? 'bg-[#22222a] border border-zinc-700/60 text-zinc-100 shadow-2xs font-semibold'
                : 'hover:text-zinc-200'
            }`}
          >
            <AreaIcon className="w-3.5 h-3.5 text-blue-400" />
            <span>Overview</span>
          </button>

          <button
            onClick={() => setActiveTab('trends')}
            className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md transition-all ${
              activeTab === 'trends'
                ? 'bg-[#22222a] border border-zinc-700/60 text-zinc-100 shadow-2xs font-semibold'
                : 'hover:text-zinc-200'
            }`}
          >
            <LineIcon className="w-3.5 h-3.5 text-indigo-400" />
            <span>Trends</span>
          </button>

          <button
            onClick={() => setActiveTab('distribution')}
            className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md transition-all ${
              activeTab === 'distribution'
                ? 'bg-[#22222a] border border-zinc-700/60 text-zinc-100 shadow-2xs font-semibold'
                : 'hover:text-zinc-200'
            }`}
          >
            <BarChart3 className="w-3.5 h-3.5 text-emerald-400" />
            <span>Distribution</span>
          </button>
        </div>
      </div>

      {/* Chart Canvas */}
      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          {activeTab === 'overview' ? (
            <AreaChart data={chartData} margin={{ top: 10, right: 10, bottom: 0, left: -20 }}>
              <defs>
                <linearGradient id="chartGradientBlue" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.35} />
                  <stop offset="95%" stopColor="#3B82F6" stopOpacity={0.0} />
                </linearGradient>
                <linearGradient id="chartGradientIndigo" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#818CF8" stopOpacity={0.2} />
                  <stop offset="95%" stopColor="#818CF8" stopOpacity={0.0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#27272a" />
              <XAxis dataKey={xKey} stroke="#71717a" tick={{ fontSize: 11, fill: '#a1a1aa' }} tickLine={false} axisLine={false} />
              <YAxis stroke="#71717a" tick={{ fontSize: 11, fill: '#a1a1aa' }} tickLine={false} axisLine={false} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#121216',
                  borderColor: '#27272a',
                  borderRadius: '0.75rem',
                  fontSize: '12px',
                  color: '#f4f4f5',
                  boxShadow: '0 4px 12px rgba(0,0,0,0.5)'
                }}
              />
              <Area type="monotone" dataKey={yKey1} stroke="#3B82F6" strokeWidth={2} fillOpacity={1} fill="url(#chartGradientBlue)" />
              {yKey2 && (
                <Area type="monotone" dataKey={yKey2} stroke="#818CF8" strokeWidth={2} fillOpacity={1} fill="url(#chartGradientIndigo)" />
              )}
            </AreaChart>
          ) : activeTab === 'trends' ? (
            <LineChart data={chartData} margin={{ top: 10, right: 10, bottom: 0, left: -20 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#27272a" />
              <XAxis dataKey={xKey} stroke="#71717a" tick={{ fontSize: 11, fill: '#a1a1aa' }} tickLine={false} axisLine={false} />
              <YAxis stroke="#71717a" tick={{ fontSize: 11, fill: '#a1a1aa' }} tickLine={false} axisLine={false} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#121216',
                  borderColor: '#27272a',
                  borderRadius: '0.75rem',
                  fontSize: '12px',
                  color: '#f4f4f5',
                }}
              />
              <Line type="monotone" dataKey={yKey1} stroke="#3B82F6" strokeWidth={2.5} dot={{ r: 3, fill: '#3B82F6' }} activeDot={{ r: 6 }} />
              {yKey2 && (
                <Line type="monotone" dataKey={yKey2} stroke="#10B981" strokeWidth={2} strokeDasharray="4 4" dot={{ r: 2, fill: '#10B981' }} />
              )}
            </LineChart>
          ) : (
            <BarChart data={chartData} margin={{ top: 10, right: 10, bottom: 0, left: -20 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#27272a" />
              <XAxis dataKey={xKey} stroke="#71717a" tick={{ fontSize: 11, fill: '#a1a1aa' }} tickLine={false} axisLine={false} />
              <YAxis stroke="#71717a" tick={{ fontSize: 11, fill: '#a1a1aa' }} tickLine={false} axisLine={false} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#121216',
                  borderColor: '#27272a',
                  borderRadius: '0.75rem',
                  fontSize: '12px',
                  color: '#f4f4f5',
                }}
              />
              <Bar dataKey={yKey1} fill="#3B82F6" radius={[4, 4, 0, 0]} />
            </BarChart>
          )}
        </ResponsiveContainer>
      </div>
    </div>
  );
};
