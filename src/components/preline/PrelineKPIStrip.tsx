/**
 * Preline KPI Strip Component
 * 4-Segment Horizontal KPI card styled in Pure Smooth Z-Black (#0e0e11)
 * with crisp zinc-800 dividers and blue active top line.
 */

import React from 'react';
import { Users, UserPlus, RotateCcw, Clock, TrendingUp, TrendingDown } from 'lucide-react';

export interface KPIData {
  activeSegment?: number;
  onSelectSegment?: (index: number) => void;
  users?: string;
  usersTrend?: string;
  isUsersPositive?: boolean;
  newUsers?: string;
  newUsersTrend?: string;
  isNewUsersPositive?: boolean;
  returningUsers?: string;
  returningUsersTrend?: string;
  isReturningPositive?: boolean;
  avgEngagement?: string;
  avgEngagementTrend?: string;
  isEngagementPositive?: boolean;
}

export const PrelineKPIStrip: React.FC<KPIData> = ({
  activeSegment = 0,
  onSelectSegment,
  users = "54,382",
  usersTrend = "1.2%",
  isUsersPositive = true,
  newUsers = "3,301",
  newUsersTrend = "5.2%",
  isNewUsersPositive = false,
  returningUsers = "50,402",
  returningUsersTrend = "14.7%",
  isReturningPositive = false,
  avgEngagement = "2m 25s",
  avgEngagementTrend = "3%",
  isEngagementPositive = true,
}) => {
  const segments = [
    {
      id: 0,
      icon: Users,
      label: "Users",
      value: users,
      trend: usersTrend,
      positive: isUsersPositive,
    },
    {
      id: 1,
      icon: UserPlus,
      label: "New users",
      value: newUsers,
      trend: newUsersTrend,
      positive: isNewUsersPositive,
    },
    {
      id: 2,
      icon: RotateCcw,
      label: "Returning users",
      value: returningUsers,
      trend: returningUsersTrend,
      positive: isReturningPositive,
    },
    {
      id: 3,
      icon: Clock,
      label: "Avg. engagement time",
      value: avgEngagement,
      trend: avgEngagementTrend,
      positive: isEngagementPositive,
    },
  ];

  return (
    <div className="bg-[#0e0e11] rounded-xl border border-[#27272a] overflow-hidden shadow-xs transition-colors">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 divide-y sm:divide-y-0 sm:divide-x divide-[#27272a]">
        {segments.map((seg, idx) => {
          const Icon = seg.icon;
          const isActive = activeSegment === idx;

          return (
            <div
              key={seg.id}
              onClick={() => onSelectSegment?.(idx)}
              className={`relative p-5 cursor-pointer transition-all duration-150 ${
                isActive ? 'bg-[#141418]' : 'bg-[#0e0e11] hover:bg-[#121216]'
              }`}
            >
              {/* Top Active Line Indicator (Vibrant Blue) */}
              {isActive && (
                <div className="absolute top-0 left-0 right-0 h-[3px] bg-blue-500 shadow-sm shadow-blue-500/50" />
              )}

              {/* Header: Icon + Label */}
              <div className="flex items-center gap-2 mb-2 text-zinc-400">
                <Icon className={`w-4 h-4 ${isActive ? 'text-blue-400' : 'text-zinc-500'}`} />
                <span className="text-sm font-medium text-zinc-300">
                  {seg.label}
                </span>
              </div>

              {/* Value and Trend Badge Row */}
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold tracking-tight text-zinc-100 font-sans">
                  {seg.value}
                </span>

                <span
                  className={`inline-flex items-center gap-0.5 text-xs font-semibold ${
                    seg.positive ? 'text-emerald-400' : 'text-rose-400'
                  }`}
                >
                  {seg.positive ? (
                    <TrendingUp className="w-3.5 h-3.5 stroke-[2.5]" />
                  ) : (
                    <TrendingDown className="w-3.5 h-3.5 stroke-[2.5]" />
                  )}
                  <span>{seg.trend}</span>
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
