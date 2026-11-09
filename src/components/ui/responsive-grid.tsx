import React from 'react';
import { cn } from '@/lib/utils';

interface ResponsiveGridProps {
  children: React.ReactNode;
  className?: string;
  cols?: {
    default?: number;
    sm?: number;
    md?: number;
    lg?: number;
    xl?: number;
    '2xl'?: number;
  };
  gap?: number | string;
  autoFit?: boolean;
  minChildWidth?: string;
}

export const ResponsiveGrid: React.FC<ResponsiveGridProps> = ({
  children,
  className = '',
  cols = { default: 1, md: 2, lg: 3 },
  gap = 6,
  autoFit = false,
  minChildWidth = '300px',
}) => {
  const getGridClasses = () => {
    if (autoFit) {
      return `grid auto-fit-grid gap-${gap}`;
    }

    const gridClasses = ['grid'];
    
    if (cols.default) gridClasses.push(`grid-cols-${cols.default}`);
    if (cols.sm) gridClasses.push(`sm:grid-cols-${cols.sm}`);
    if (cols.md) gridClasses.push(`md:grid-cols-${cols.md}`);
    if (cols.lg) gridClasses.push(`lg:grid-cols-${cols.lg}`);
    if (cols.xl) gridClasses.push(`xl:grid-cols-${cols.xl}`);
    if (cols['2xl']) gridClasses.push(`2xl:grid-cols-${cols['2xl']}`);
    
    gridClasses.push(`gap-${gap}`);
    
    return gridClasses.join(' ');
  };

  const style = autoFit ? {
    gridTemplateColumns: `repeat(auto-fit, minmax(${minChildWidth}, 1fr))`
  } : undefined;

  return (
    <div 
      className={cn(getGridClasses(), className)}
      style={style}
    >
      {children}
    </div>
  );
};

// Predefined grid layouts
export const KpiGrid: React.FC<{ children: React.ReactNode; className?: string }> = ({
  children,
  className = '',
}) => (
  <ResponsiveGrid
    cols={{ default: 1, sm: 2, lg: 4 }}
    gap={6}
    className={className}
  >
    {children}
  </ResponsiveGrid>
);

export const ChartGrid: React.FC<{ children: React.ReactNode; className?: string }> = ({
  children,
  className = '',
}) => (
  <ResponsiveGrid
    cols={{ default: 1, lg: 2 }}
    gap={8}
    className={className}
  >
    {children}
  </ResponsiveGrid>
);

export const DashboardGrid: React.FC<{ children: React.ReactNode; className?: string }> = ({
  children,
  className = '',
}) => (
  <ResponsiveGrid
    autoFit
    minChildWidth="320px"
    gap={6}
    className={className}
  >
    {children}
  </ResponsiveGrid>
);

// Enhanced card component with better spacing and interactions
interface EnhancedCardProps {
  children: React.ReactNode;
  className?: string;
  variant?: 'glass' | 'neumorphism' | 'elevated';
  padding?: 'sm' | 'md' | 'lg' | 'xl';
  hover?: boolean;
  clickable?: boolean;
  onClick?: () => void;
}

export const EnhancedCard: React.FC<EnhancedCardProps> = ({
  children,
  className = '',
  variant = 'glass',
  padding = 'md',
  hover = true,
  clickable = false,
  onClick,
}) => {
  const getVariantClass = () => {
    switch (variant) {
      case 'glass':
        return 'glass-card';
      case 'neumorphism':
        return 'neumorphism';
      case 'elevated':
        return 'bg-card border rounded-2xl shadow-2xl';
      default:
        return 'glass-card';
    }
  };

  const getPaddingClass = () => {
    switch (padding) {
      case 'sm':
        return 'p-4';
      case 'md':
        return 'p-6';
      case 'lg':
        return 'p-8';
      case 'xl':
        return 'p-10';
      default:
        return 'p-6';
    }
  };

  return (
    <div
      className={cn(
        getVariantClass(),
        getPaddingClass(),
        'transition-all duration-300',
        {
          'hover:scale-[1.02] hover:shadow-xl': hover,
          'cursor-pointer': clickable || onClick,
          'focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2': clickable || onClick,
        },
        className
      )}
      onClick={onClick}
      role={clickable || onClick ? 'button' : undefined}
      tabIndex={clickable || onClick ? 0 : undefined}
      onKeyDown={(e) => {
        if ((clickable || onClick) && (e.key === 'Enter' || e.key === ' ')) {
          e.preventDefault();
          onClick?.();
        }
      }}
    >
      {children}
    </div>
  );
};

// Section wrapper with consistent spacing
interface SectionProps {
  children: React.ReactNode;
  className?: string;
  title?: string;
  subtitle?: string;
  headerActions?: React.ReactNode;
  spacing?: 'sm' | 'md' | 'lg' | 'xl';
}

export const Section: React.FC<SectionProps> = ({
  children,
  className = '',
  title,
  subtitle,
  headerActions,
  spacing = 'lg',
}) => {
  const getSpacingClass = () => {
    switch (spacing) {
      case 'sm':
        return 'space-y-4';
      case 'md':
        return 'space-y-6';
      case 'lg':
        return 'space-y-8';
      case 'xl':
        return 'space-y-12';
      default:
        return 'space-y-8';
    }
  };

  return (
    <section className={cn(getSpacingClass(), className)}>
      {(title || subtitle || headerActions) && (
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="space-y-1">
            {title && (
              <h2 className="text-2xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
                {title}
              </h2>
            )}
            {subtitle && (
              <p className="text-muted-foreground text-sm">{subtitle}</p>
            )}
          </div>
          {headerActions && (
            <div className="flex items-center gap-3">
              {headerActions}
            </div>
          )}
        </div>
      )}
      {children}
    </section>
  );
}; 