import React from 'react';
import { cn } from '@/lib/utils';

interface SkeletonProps {
  className?: string;
  variant?: 'default' | 'text' | 'circular' | 'rectangular';
  width?: string | number;
  height?: string | number;
  animate?: boolean;
}

export const Skeleton: React.FC<SkeletonProps> = ({
  className = '',
  variant = 'default',
  width,
  height,
  animate = true,
}) => {
  const baseClasses = cn(
    'bg-gradient-to-r from-muted/50 via-muted/70 to-muted/50',
    'border border-border/30',
    {
      'rounded-lg': variant === 'default' || variant === 'rectangular',
      'rounded-full': variant === 'circular',
      'rounded-md h-4': variant === 'text',
      'animate-pulse': animate,
    },
    className
  );

  const style: React.CSSProperties = {};
  if (width) style.width = width;
  if (height) style.height = height;

  return <div className={baseClasses} style={style} />;
};

// Chart skeleton component
export const ChartSkeleton: React.FC<{ height?: number; className?: string }> = ({
  height = 300,
  className = '',
}) => (
  <div className={cn('space-y-4', className)}>
    <div className="flex items-center justify-between">
      <Skeleton width={120} height={20} />
      <Skeleton width={80} height={32} />
    </div>
    <Skeleton width="100%" height={height} className="rounded-xl" />
  </div>
);

// KPI Card skeleton component
export const KpiCardSkeleton: React.FC<{ className?: string }> = ({ className = '' }) => (
  <div className={cn('glass-card p-6 space-y-3', className)}>
    <div className="flex items-center justify-between">
      <Skeleton width={100} height={16} />
      <Skeleton variant="circular" width={20} height={20} />
    </div>
    <Skeleton width={80} height={32} />
    <Skeleton width={120} height={14} />
  </div>
);

// Filter skeleton component
export const FilterSkeleton: React.FC<{ className?: string }> = ({ className = '' }) => (
  <div className={cn('flex items-center gap-3', className)}>
    <Skeleton width={200} height={40} className="rounded-xl" />
    <Skeleton width={120} height={40} className="rounded-xl" />
    <Skeleton width={100} height={40} className="rounded-xl" />
    <Skeleton width={100} height={40} className="rounded-xl" />
  </div>
);

// Insights panel skeleton
export const InsightsSkeleton: React.FC<{ className?: string }> = ({ className = '' }) => (
  <div className={cn('glass-card p-6 space-y-4', className)}>
    <Skeleton width={150} height={20} />
    <div className="space-y-3">
      {Array.from({ length: 4 }).map((_, i) => (
        <div key={i} className="flex justify-between items-center">
          <Skeleton width={80} height={14} />
          <Skeleton width={60} height={14} />
        </div>
      ))}
    </div>
  </div>
);

// Data table skeleton
export const DataTableSkeleton: React.FC<{ rows?: number; className?: string }> = ({
  rows = 5,
  className = '',
}) => (
  <div className={cn('space-y-3', className)}>
    {/* Header */}
    <div className="flex items-center gap-4">
      {Array.from({ length: 4 }).map((_, i) => (
        <Skeleton key={i} width={100} height={16} />
      ))}
    </div>
    {/* Rows */}
    {Array.from({ length: rows }).map((_, i) => (
      <div key={i} className="flex items-center gap-4">
        {Array.from({ length: 4 }).map((_, j) => (
          <Skeleton key={j} width={80} height={14} />
        ))}
      </div>
    ))}
  </div>
); 