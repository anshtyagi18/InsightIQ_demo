import React, { useEffect, useRef, useState } from 'react';
import { cn } from '@/lib/utils';

interface MotionWrapperProps {
  children: React.ReactNode;
  className?: string;
  delay?: number;
  duration?: number;
  variant?: 'fadeIn' | 'slideUp' | 'slideDown' | 'slideLeft' | 'slideRight' | 'scaleIn' | 'stagger';
  threshold?: number;
  once?: boolean;
  staggerDelay?: number;
}

export const MotionWrapper: React.FC<MotionWrapperProps> = ({
  children,
  className = '',
  delay = 0,
  duration = 0.5,
  variant = 'fadeIn',
  threshold = 0.1,
  once = true,
  staggerDelay = 0.1,
}) => {
  const [isVisible, setIsVisible] = useState(false);
  const [hasAnimated, setHasAnimated] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && (!once || !hasAnimated)) {
          setTimeout(() => {
            setIsVisible(true);
            if (once) setHasAnimated(true);
          }, delay * 1000);
        } else if (!once && !entry.isIntersecting) {
          setIsVisible(false);
        }
      },
      { threshold }
    );

    if (ref.current) {
      observer.observe(ref.current);
    }

    return () => observer.disconnect();
  }, [delay, threshold, once, hasAnimated]);

  const getAnimationClass = () => {
    const base = 'transition-all duration-500 ease-out';
    
    if (!isVisible) {
      switch (variant) {
        case 'fadeIn':
          return `${base} opacity-0`;
        case 'slideUp':
          return `${base} opacity-0 translate-y-8`;
        case 'slideDown':
          return `${base} opacity-0 -translate-y-8`;
        case 'slideLeft':
          return `${base} opacity-0 translate-x-8`;
        case 'slideRight':
          return `${base} opacity-0 -translate-x-8`;
        case 'scaleIn':
          return `${base} opacity-0 scale-95`;
        case 'stagger':
          return `${base} opacity-0 translate-y-4`;
        default:
          return `${base} opacity-0`;
      }
    }

    return `${base} opacity-100 translate-x-0 translate-y-0 scale-100`;
  };

  if (variant === 'stagger' && React.Children.count(children) > 1) {
    return (
      <div ref={ref} className={cn('space-y-4', className)}>
        {React.Children.map(children, (child, index) => (
          <div
            key={index}
            className={getAnimationClass()}
            style={{
              transitionDelay: isVisible ? `${index * staggerDelay}s` : '0s',
              transitionDuration: `${duration}s`,
            }}
          >
            {child}
          </div>
        ))}
      </div>
    );
  }

  return (
    <div
      ref={ref}
      className={cn(getAnimationClass(), className)}
      style={{
        transitionDuration: `${duration}s`,
      }}
    >
      {children}
    </div>
  );
};

// Predefined motion components for common use cases
export const FadeIn: React.FC<Omit<MotionWrapperProps, 'variant'>> = (props) => (
  <MotionWrapper {...props} variant="fadeIn" />
);

export const SlideUp: React.FC<Omit<MotionWrapperProps, 'variant'>> = (props) => (
  <MotionWrapper {...props} variant="slideUp" />
);

export const SlideDown: React.FC<Omit<MotionWrapperProps, 'variant'>> = (props) => (
  <MotionWrapper {...props} variant="slideDown" />
);

export const ScaleIn: React.FC<Omit<MotionWrapperProps, 'variant'>> = (props) => (
  <MotionWrapper {...props} variant="scaleIn" />
);

export const StaggerContainer: React.FC<Omit<MotionWrapperProps, 'variant'>> = (props) => (
  <MotionWrapper {...props} variant="stagger" />
);

// Enhanced button with micro-interactions
interface EnhancedButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'glass' | 'glass-primary' | 'neumorphism';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  icon?: React.ReactNode;
  iconPosition?: 'left' | 'right';
}

export const EnhancedButton: React.FC<EnhancedButtonProps> = ({
  children,
  className = '',
  variant = 'glass',
  size = 'md',
  loading = false,
  icon,
  iconPosition = 'left',
  disabled,
  ...props
}) => {
  const [isPressed, setIsPressed] = useState(false);

  const getVariantClass = () => {
    switch (variant) {
      case 'glass':
        return 'glass-button';
      case 'glass-primary':
        return 'glass-button-primary';
      case 'neumorphism':
        return 'neumorphism';
      default:
        return 'glass-button';
    }
  };

  const getSizeClass = () => {
    switch (size) {
      case 'sm':
        return 'px-3 py-1.5 text-sm';
      case 'md':
        return 'px-4 py-2 text-base';
      case 'lg':
        return 'px-6 py-3 text-lg';
      default:
        return 'px-4 py-2 text-base';
    }
  };

  return (
    <button
      className={cn(
        getVariantClass(),
        getSizeClass(),
        'relative overflow-hidden flex items-center gap-2 justify-center',
        'focus:ring-2 focus:ring-purple-500 focus:ring-offset-2',
        'active:scale-95 transition-all duration-150',
        {
          'opacity-50 cursor-not-allowed': disabled || loading,
          'transform scale-95': isPressed && !disabled && !loading,
        },
        className
      )}
      disabled={disabled || loading}
      onMouseDown={() => setIsPressed(true)}
      onMouseUp={() => setIsPressed(false)}
      onMouseLeave={() => setIsPressed(false)}
      {...props}
    >
      {loading && (
        <div className="absolute inset-0 flex items-center justify-center bg-inherit">
          <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
        </div>
      )}
      <div className={cn('flex items-center gap-2', { 'opacity-0': loading })}>
        {icon && iconPosition === 'left' && <span className="shrink-0">{icon}</span>}
        {children}
        {icon && iconPosition === 'right' && <span className="shrink-0">{icon}</span>}
      </div>
    </button>
  );
}; 