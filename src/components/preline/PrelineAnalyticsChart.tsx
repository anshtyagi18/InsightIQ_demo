/**
 * Preline Analytics Area & Trend Chart Component
 * Styled in Pure Smooth Z-Black (#0e0e11) with crisp zinc-800 separators.
 */

import React, { useState } from 'react';
import { 
  ResponsiveContainer, 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  Tooltip, 
  CartesianGrid 
} from 'recharts';
import { TrendingUp } from 'lucide-react';

export const SAMPLE_CHART_DATA = [
  { time: '00:00', visitors: 1420, sessions: 980 },
  { time: '03:00', visitors: 980, sessions: 710 },
  { time: '06:00', visitors: 2200, sessions: 1650 },
  { time: '09:00', visitors: 4800, sessions: 3900 },
  { time: '12:00', visitors: 6200, sessions: 5100 },
  { time: '15:00', visitors: 5800, sessions: 4750 },
  { time: '18:00', visitors: 7400, sessions: 6100 },
  { time: '21:00', visitors: 4900, sessions: 3800 },
];

interface PrelineAnalyticsChartProps {
  data?: any[];
  title?: string;
  totalValue?: string;
  trendPercentage?: string;
}

export const PrelineAnalyticsChart: React.FC<PrelineAnalyticsChartProps> = ({
  data = SAMPLE_CHART_DATA,
  title = "Visitors & Sessions Growth",
  totalValue = "54,382",
  trendPercentage = "+12.5%",
}) => {
  const [timeframe, setTimeframe] = useState<'12h' | '24h' | '7d' | '30d'>('24h');

  return (
    <div className="bg-[#0e0e11] rounded-xl border border-[#27272a] p-5 shadow-xs transition-colors select-none">
      {/* Header Row */}
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
        <div>
          <span className="text-xs font-semibold text-zinc-400 uppercase tracking-wider">
            {title}
          </span>
          <div className="flex items-baseline gap-2 mt-0.5">
            <span className="text-2xl font-bold tracking-tight text-zinc-100 font-sans">
              {totalValue}
            </span>
            <span className="inline-flex items-center gap-0.5 text-xs font-semibold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-1.5 py-0.5 rounded">
              <TrendingUp className="w-3 h-3 stroke-[2.5]" />
              {trendPercentage}
            </span>
          </div>
        </div>

        {/* Timeframe Pill Toggles */}
        <div className="flex items-center p-0.5 bg-[#141418] rounded-lg text-xs font-medium text-zinc-400 border border-[#27272a]">
          {(['12h', '24h', '7d', '30d'] as const).map((tf) => (
            <button
              key={tf}
              onClick={() => setTimeframe(tf)}
              className={`px-2.5 py-1 rounded-md transition-all ${
                timeframe === tf 
                  ? 'bg-[#22222a] border border-zinc-700/60 text-zinc-100 shadow-2xs font-semibold' 
                  : 'hover:text-zinc-200'
              }`}
            >
              {tf}
            </button>
          ))}
        </div>
      </div>

      {/* Chart Canvas */}
      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 10, right: 10, bottom: 0, left: -20 }}>
            <defs>
              <linearGradient id="blueGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.35} />
                <stop offset="95%" stopColor="#3B82F6" stopOpacity={0.0} />
              </linearGradient>
              <linearGradient id="slateGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#94A3B8" stopOpacity={0.2} />
                <stop offset="95%" stopColor="#94A3B8" stopOpacity={0.0} />
              </linearGradient>
            </defs>

            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#27272a" />

            <XAxis
              dataKey="time"
              stroke="#71717a"
              fontSize={11}
              tickLine={false}
              axisLine={{ stroke: '#27272a' }}
            />
            <YAxis
              stroke="#71717a"
              fontSize={11}
              tickLine={false}
              axisLine={false}
              tickFormatter={(v) => (v >= 1000 ? `${(v / 1000).toFixed(1)}k` : v)}
            />

            <Tooltip
              contentStyle={{
                backgroundColor: '#141418',
                borderRadius: '8px',
                border: '1px solid #27272a',
                boxShadow: '0 8px 16px -2px rgba(0, 0, 0, 0.5)',
                fontSize: '12px',
                color: '#F4F4F5',
              }}
            />

            <Area
              type="monotone"
              dataKey="visitors"
              name="Visitors"
              stroke="#3B82F6"
              strokeWidth={2.5}
              fillOpacity={1}
              fill="url(#blueGradient)"
            />
            <Area
              type="monotone"
              dataKey="sessions"
              name="Sessions"
              stroke="#71717a"
              strokeWidth={1.5}
              strokeDasharray="4 4"
              fillOpacity={1}
              fill="url(#slateGradient)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
