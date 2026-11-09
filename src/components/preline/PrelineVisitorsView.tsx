/**
 * Preline Visitors View Component
 * Styled in Pure Smooth Z-Black (#0e0e11) with crisp zinc-800 separators.
 */

import React, { useState } from 'react';
import { 
  Users, 
  Smartphone, 
  Monitor, 
  Tablet, 
  Globe2, 
  TrendingUp, 
  TrendingDown, 
  Calendar, 
  Clock,
  ArrowUpRight
} from 'lucide-react';

interface PrelineVisitorsViewProps {
  totalRows?: number;
}

export const PrelineVisitorsView: React.FC<PrelineVisitorsViewProps> = ({
  totalRows = 54382,
}) => {
  const [timeRange, setTimeRange] = useState('Today');

  const devices = [
    { label: 'Desktop', percentage: 64, count: Math.round(totalRows * 0.64), icon: Monitor, color: 'bg-blue-500' },
    { label: 'Mobile', percentage: 31, count: Math.round(totalRows * 0.31), icon: Smartphone, color: 'bg-emerald-500' },
    { label: 'Tablet', percentage: 5, count: Math.round(totalRows * 0.05), icon: Tablet, color: 'bg-purple-500' },
  ];

  const browsers = [
    { name: 'Chrome', share: 62.4, color: 'bg-blue-500' },
    { name: 'Safari', share: 21.8, color: 'bg-sky-400' },
    { name: 'Edge', share: 9.7, color: 'bg-teal-500' },
    { name: 'Firefox', share: 4.5, color: 'bg-amber-500' },
    { name: 'Others', share: 1.6, color: 'bg-zinc-500' },
  ];

  const recentSessions = [
    { id: 'SES-9401', ip: '192.168.1.104', country: 'United States', flag: 'https://flagcdn.com/w40/us.png', browser: 'Chrome on macOS', duration: '4m 12s', pages: 6, status: 'Active' },
    { id: 'SES-9402', ip: '172.16.0.42', country: 'India', flag: 'https://flagcdn.com/w40/in.png', browser: 'Chrome on Android', duration: '2m 45s', pages: 3, status: 'Completed' },
    { id: 'SES-9403', ip: '10.0.4.19', country: 'Germany', flag: 'https://flagcdn.com/w40/de.png', browser: 'Firefox on Linux', duration: '0m 42s', pages: 1, status: 'Bounced' },
    { id: 'SES-9404', ip: '198.51.100.8', country: 'United Kingdom', flag: 'https://flagcdn.com/w40/gb.png', browser: 'Safari on iOS', duration: '5m 19s', pages: 8, status: 'Active' },
    { id: 'SES-9405', ip: '203.0.113.55', country: 'Brasil', flag: 'https://flagcdn.com/w40/br.png', browser: 'Edge on Windows', duration: '1m 30s', pages: 2, status: 'Completed' },
  ];

  return (
    <div className="space-y-6 select-none">
      {/* View Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-zinc-100">
            Visitors &amp; Demographics
          </h1>
          <p className="text-xs text-zinc-400 mt-0.5">
            Real-time traffic channels, operating systems, and device telemetry
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button className="inline-flex items-center gap-1.5 bg-[#141418] hover:bg-[#1b1b22] border border-[#27272a] text-xs font-medium text-zinc-200 px-3 py-1.5 rounded-lg shadow-2xs transition-colors">
            <Calendar className="w-3.5 h-3.5 text-zinc-400" />
            <span>{timeRange}</span>
            <span className="text-zinc-500">▾</span>
          </button>
        </div>
      </div>

      {/* 4 Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-[#0e0e11] rounded-xl border border-[#27272a] p-5 shadow-xs">
          <div className="flex items-center justify-between text-xs text-zinc-400 mb-2">
            <span>Total Visitors</span>
            <Users className="w-4 h-4 text-blue-400" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold text-zinc-100">
              {totalRows.toLocaleString()}
            </span>
            <span className="inline-flex items-center text-xs font-semibold text-emerald-400">
              <TrendingUp className="w-3.5 h-3.5 mr-0.5" /> 1.2%
            </span>
          </div>
          <p className="text-[11px] text-zinc-500 mt-1">vs. previous period</p>
        </div>

        <div className="bg-[#0e0e11] rounded-xl border border-[#27272a] p-5 shadow-xs">
          <div className="flex items-center justify-between text-xs text-zinc-400 mb-2">
            <span>Unique Sessions</span>
            <Globe2 className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold text-zinc-100">
              {Math.round(totalRows * 0.78).toLocaleString()}
            </span>
            <span className="inline-flex items-center text-xs font-semibold text-emerald-400">
              <TrendingUp className="w-3.5 h-3.5 mr-0.5" /> 4.8%
            </span>
          </div>
          <p className="text-[11px] text-zinc-500 mt-1">78% return rate</p>
        </div>

        <div className="bg-[#0e0e11] rounded-xl border border-[#27272a] p-5 shadow-xs">
          <div className="flex items-center justify-between text-xs text-zinc-400 mb-2">
            <span>Bounce Rate</span>
            <ArrowUpRight className="w-4 h-4 text-rose-400" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold text-zinc-100">
              32.4%
            </span>
            <span className="inline-flex items-center text-xs font-semibold text-emerald-400">
              <TrendingDown className="w-3.5 h-3.5 mr-0.5" /> 2.1%
            </span>
          </div>
          <p className="text-[11px] text-zinc-500 mt-1">Healthy threshold &lt; 40%</p>
        </div>

        <div className="bg-[#0e0e11] rounded-xl border border-[#27272a] p-5 shadow-xs">
          <div className="flex items-center justify-between text-xs text-zinc-400 mb-2">
            <span>Avg. Session Time</span>
            <Clock className="w-4 h-4 text-amber-400" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold text-zinc-100">
              2m 25s
            </span>
            <span className="inline-flex items-center text-xs font-semibold text-emerald-400">
              <TrendingUp className="w-3.5 h-3.5 mr-0.5" /> 3.0%
            </span>
          </div>
          <p className="text-[11px] text-zinc-500 mt-1">+14s vs benchmark</p>
        </div>
      </div>

      {/* Row 2: Devices & Browser Share */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Device Breakdown */}
        <div className="bg-[#0e0e11] rounded-xl border border-[#27272a] p-5 shadow-xs">
          <h3 className="text-sm font-bold text-zinc-100 mb-4">
            Device Distribution
          </h3>
          <div className="space-y-4">
            {devices.map((d) => {
              const Icon = d.icon;
              return (
                <div key={d.label}>
                  <div className="flex items-center justify-between text-xs mb-1.5">
                    <div className="flex items-center gap-2">
                      <Icon className="w-4 h-4 text-zinc-400" />
                      <span className="font-semibold text-zinc-200">{d.label}</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-zinc-400 font-mono text-[11px]">
                        {d.count.toLocaleString()} visits
                      </span>
                      <span className="font-bold text-zinc-100 font-mono w-10 text-right">
                        {d.percentage}%
                      </span>
                    </div>
                  </div>
                  <div className="w-full bg-[#18181d] h-2 rounded-full overflow-hidden">
                    <div
                      className={`h-2 rounded-full ${d.color}`}
                      style={{ width: `${d.percentage}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Browser Breakdown */}
        <div className="bg-[#0e0e11] rounded-xl border border-[#27272a] p-5 shadow-xs">
          <h3 className="text-sm font-bold text-zinc-100 mb-4">
            Browser Market Share
          </h3>
          <div className="space-y-3.5">
            {browsers.map((b) => (
              <div key={b.name} className="flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <span className={`w-2.5 h-2.5 rounded-full ${b.color}`} />
                  <span className="text-xs font-medium text-zinc-200">{b.name}</span>
                </div>
                <div className="flex items-center gap-4">
                  <div className="w-32 bg-[#18181d] h-1.5 rounded-full overflow-hidden hidden sm:block">
                    <div className={`h-1.5 rounded-full ${b.color}`} style={{ width: `${b.share}%` }} />
                  </div>
                  <span className="text-xs font-mono font-bold text-zinc-300 w-12 text-right">
                    {b.share}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Row 3: Active Visitor Sessions Stream Table */}
      <div className="bg-[#0e0e11] rounded-xl border border-[#27272a] overflow-hidden shadow-xs">
        <div className="p-4 border-b border-[#27272a] flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-zinc-100">
              Live Sessions Stream
            </h3>
            <p className="text-xs text-zinc-400">
              Direct telemetry from connected client nodes
            </p>
          </div>
          <span className="inline-flex items-center gap-1.5 text-xs text-emerald-400 font-semibold bg-emerald-500/10 px-2.5 py-1 rounded-full border border-emerald-500/20">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            Live Sync
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-[#27272a] text-xs">
            <thead className="bg-[#141418]">
              <tr>
                <th className="py-2.5 px-4 text-left font-semibold text-zinc-400">Session ID</th>
                <th className="py-2.5 px-4 text-left font-semibold text-zinc-400">Country</th>
                <th className="py-2.5 px-4 text-left font-semibold text-zinc-400">Environment</th>
                <th className="py-2.5 px-4 text-left font-semibold text-zinc-400">Duration</th>
                <th className="py-2.5 px-4 text-left font-semibold text-zinc-400">Pages</th>
                <th className="py-2.5 px-4 text-right font-semibold text-zinc-400">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#27272a]/60">
              {recentSessions.map((s) => (
                <tr key={s.id} className="hover:bg-[#141418] transition-colors">
                  <td className="py-2.5 px-4 font-mono font-medium text-zinc-100">{s.id}</td>
                  <td className="py-2.5 px-4">
                    <div className="flex items-center gap-2">
                      <img src={s.flag} alt={s.country} className="w-4 h-3 rounded-xs object-cover border border-[#27272a]" />
                      <span className="text-zinc-200">{s.country}</span>
                    </div>
                  </td>
                  <td className="py-2.5 px-4 text-zinc-400">{s.browser}</td>
                  <td className="py-2.5 px-4 font-mono text-zinc-400">{s.duration}</td>
                  <td className="py-2.5 px-4 font-mono text-zinc-400">{s.pages} views</td>
                  <td className="py-2.5 px-4 text-right">
                    <span
                      className={`inline-block px-2 py-0.5 rounded-full text-[10px] font-semibold border ${
                        s.status === 'Active'
                          ? 'bg-blue-500/10 text-blue-400 border-blue-500/20'
                          : s.status === 'Completed'
                          ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                          : 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                      }`}
                    >
                      {s.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
