import React from 'react';
import { cn } from '@/lib/utils';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
  text?: string;
  variant?: 'default' | 'page' | 'component';
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 'md',
  className,
  text,
  variant = 'default'
}) => {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8',
    xl: 'w-12 h-12'
  };

  const variantClasses = {
    default: 'border-primary border-t-transparent',
    page: 'border-blue-500 border-t-transparent',
    component: 'border-muted-foreground border-t-transparent'
  };

  if (variant === 'page') {
    return (
      <div className="min-h-[50vh] flex flex-col items-center justify-center space-y-4">
        <div className="relative">
          {/* Main spinner */}
          <div 
            className={cn(
              'animate-spin rounded-full border-2',
              sizeClasses[size],
              variantClasses[variant],
              className
            )}
            role="status"
            aria-label="Loading"
          />
          
          {/* Pulsing inner circle */}
          <div 
            className={cn(
              'absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 rounded-full bg-blue-500/20 animate-pulse',
              {
                'w-2 h-2': size === 'sm',
                'w-3 h-3': size === 'md',
                'w-4 h-4': size === 'lg',
                'w-6 h-6': size === 'xl'
              }
            )}
          />
        </div>
        
        {text && (
          <div className="text-center space-y-2">
            <p className="text-sm font-medium text-muted-foreground animate-pulse">
              {text}
            </p>
            <div className="flex items-center justify-center space-x-1">
              <div className="w-1 h-1 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
              <div className="w-1 h-1 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
              <div className="w-1 h-1 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
            </div>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="flex items-center justify-center space-x-2">
      <div 
        className={cn(
          'animate-spin rounded-full border-2',
          sizeClasses[size],
          variantClasses[variant],
          className
        )}
        role="status"
        aria-label="Loading"
      />
      {text && (
        <span className="text-sm text-muted-foreground animate-pulse">
          {text}
        </span>
      )}
    </div>
  );
};

// Page loading component for lazy loading
export const PageLoadingFallback: React.FC<{ 
  text?: string;
  className?: string;
}> = ({ 
  text = "Loading page...",
  className 
}) => (
  <div className={cn("min-h-screen flex flex-col items-center justify-center", className)}>
    <LoadingSpinner 
      size="xl" 
      variant="page" 
      text={text} 
    />
  </div>
);

// Component loading fallback for smaller lazy components
export const ComponentLoadingFallback: React.FC<{ 
  text?: string;
  className?: string;
  height?: string;
}> = ({ 
  text = "Loading...",
  className,
  height = "200px"
}) => (
  <div 
    className={cn("flex items-center justify-center", className)}
    style={{ minHeight: height }}
  >
    <LoadingSpinner 
      size="lg" 
      variant="component" 
      text={text} 
    />
  </div>
); 