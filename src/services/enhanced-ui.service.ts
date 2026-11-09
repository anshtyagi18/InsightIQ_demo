/**
 * Enhanced UI Service - Performance Optimized
 * 
 * Provides smooth animations, optimized database persistence, and enhanced user experience
 * for all UI interactions. Optimized for 60fps performance while maintaining visual quality.
 */

import { dbStorage } from './db-storage.service';

export interface UIAnimationConfig {
  duration?: number;
  easing?: string;
  delay?: number;
  fillMode?: 'forwards' | 'backwards' | 'both' | 'none';
}

export interface PageTransitionConfig {
  enter: UIAnimationConfig;
  exit: UIAnimationConfig;
  name: string;
}

export interface UIPreferences {
  theme: 'dark';
  animations: boolean;
  reducedMotion: boolean;
  sidebarCollapsed: boolean;
  density: 'compact' | 'normal' | 'spacious';
  fontSize: 'small' | 'medium' | 'large';
  contrast: 'normal' | 'high';
}

class EnhancedUIService {
  private animationQueue: Array<{ element: HTMLElement; animation: Animation; priority: number }> = [];
  private isPerformanceMode = false;
  private prefersReducedMotion = false;
  private saveDebounceTimer: number | null = null;
  private elementCache = new Map<string, HTMLElement>();
  private animationTimeouts = new Set<number>();

  // Default UI preferences - always dark mode
  private defaultPreferences: UIPreferences = {
    theme: 'dark',
    animations: true,
    reducedMotion: false,
    sidebarCollapsed: false,
    density: 'normal',
    fontSize: 'medium',
    contrast: 'normal'
  };

  // Optimized page transitions with reduced GPU usage
  private pageTransitions: Record<string, PageTransitionConfig> = {
    slideLeft: {
      name: 'slideLeft',
      enter: { duration: 250, easing: 'cubic-bezier(0.25, 0.46, 0.45, 0.94)' }, // Smoother easing
      exit: { duration: 200, easing: 'cubic-bezier(0.55, 0.06, 0.68, 0.19)' }
    },
    slideRight: {
      name: 'slideRight',
      enter: { duration: 250, easing: 'cubic-bezier(0.25, 0.46, 0.45, 0.94)' },
      exit: { duration: 200, easing: 'cubic-bezier(0.55, 0.06, 0.68, 0.19)' }
    },
    fadeScale: {
      name: 'fadeScale',
      enter: { duration: 300, easing: 'cubic-bezier(0.25, 0.46, 0.45, 0.94)' },
      exit: { duration: 250, easing: 'cubic-bezier(0.55, 0.06, 0.68, 0.19)' }
    },
    slideUp: {
      name: 'slideUp',
      enter: { duration: 275, easing: 'cubic-bezier(0.25, 0.46, 0.45, 0.94)' },
      exit: { duration: 225, easing: 'cubic-bezier(0.55, 0.06, 0.68, 0.19)' }
    }
  };

  constructor() {
    this.detectUserPreferences();
    this.setupOptimizedPerformanceMonitoring();
    this.injectOptimizedGlobalStyles();
  }

  /**
   * Initialize UI service - loads user preferences and sets up animations
   */
  async initialize(): Promise<UIPreferences> {
    try {
      const preferences = await this.loadUserPreferences();
      await this.applyUIPreferences(preferences);
      return preferences;
    } catch (error) {
      console.warn('⚠️ Failed to initialize UI service, using defaults:', error);
      return this.defaultPreferences;
    }
  }

  /**
   * Load user preferences from database with caching
   */
  async loadUserPreferences(): Promise<UIPreferences> {
    try {
      const saved = await dbStorage.getItem('ui-preferences');
      if (saved) {
        const parsed = typeof saved === 'string' ? JSON.parse(saved) : saved;
        // Force theme to be dark
        return { ...this.defaultPreferences, ...parsed, theme: 'dark' };
      }
    } catch (error) {
      console.warn('Failed to load preferences from database:', error);
    }

    // Fallback to localStorage
    const localPrefs = localStorage.getItem('ui-preferences');
    if (localPrefs) {
      try {
        const parsed = JSON.parse(localPrefs);
        // Migrate to database (debounced) and force dark theme
        const darkModePrefs = { ...parsed, theme: 'dark' };
        this.debouncedSaveUserPreferences(darkModePrefs);
        return { ...this.defaultPreferences, ...darkModePrefs };
      } catch (error) {
        console.warn('Failed to parse local preferences:', error);
      }
    }

    return this.defaultPreferences;
  }

  /**
   * Debounced save user preferences to prevent excessive database calls
   */
  private debouncedSaveUserPreferences(preferences: Partial<UIPreferences>): void {
    if (this.saveDebounceTimer) {
      clearTimeout(this.saveDebounceTimer);
    }
    
    this.saveDebounceTimer = window.setTimeout(async () => {
      try {
        // Force theme to dark before saving
        const darkModePrefs = { ...preferences, theme: 'dark' as const };
        await dbStorage.setItem('ui-preferences', JSON.stringify(darkModePrefs));
        console.log('✅ UI preferences saved to database (forced dark mode)');
      } catch (error) {
        console.warn('⚠️ Failed to save preferences to database:', error);
        // Fallback to localStorage
        const darkModePrefs = { ...preferences, theme: 'dark' as const };
        localStorage.setItem('ui-preferences', JSON.stringify(darkModePrefs));
      }
    }, 500); // 500ms debounce
  }

  /**
   * Save user preferences to database (debounced)
   */
  async saveUserPreferences(preferences: Partial<UIPreferences>): Promise<void> {
    this.debouncedSaveUserPreferences(preferences);
  }

  /**
   * Apply UI preferences to the DOM with optimized DOM manipulation
   */
  async applyUIPreferences(preferences: UIPreferences): Promise<void> {
    const root = document.documentElement;

    // Batch DOM updates for better performance
    requestAnimationFrame(() => {
      // Always apply dark theme
      root.setAttribute('data-theme', 'dark');
      root.classList.add('dark');
      
      // Apply density
      root.setAttribute('data-density', preferences.density);
      
      // Apply font size
      root.setAttribute('data-font-size', preferences.fontSize);
      
      // Apply contrast
      root.setAttribute('data-contrast', preferences.contrast);
      
      // Apply reduced motion
      if (preferences.reducedMotion) {
        root.style.setProperty('--motion-duration', '0ms');
        root.classList.add('reduce-motion');
      } else {
        root.style.removeProperty('--motion-duration');
        root.classList.remove('reduce-motion');
      }
    });

    // Store current preferences (debounced) with forced dark theme
    this.debouncedSaveUserPreferences({ ...preferences, theme: 'dark' });
  }

  /**
   * Optimized element animation with intelligent caching
   */
  animateElement(
    element: HTMLElement,
    keyframes: Keyframe[],
    config: UIAnimationConfig = {},
    priority: number = 1
  ): Promise<void> {
    return new Promise((resolve) => {
      // Skip animation if reduced motion is preferred
      if (this.prefersReducedMotion && !config.duration) {
        resolve();
        return;
      }

      // Create optimized animation with GPU acceleration
      const optimizedKeyframes = keyframes.map(frame => ({
        ...frame,
        willChange: 'transform, opacity',
        transform: frame.transform || 'translateZ(0)' // Force GPU layer
      }));

      const animation = element.animate(optimizedKeyframes, {
        duration: config.duration || 200,
        easing: config.easing || 'ease-out',
        delay: config.delay || 0,
        fill: config.fillMode || 'forwards'
      });

      // Add to queue for performance monitoring
      this.animationQueue.push({ element, animation, priority });

      animation.addEventListener('finish', () => {
        this.removeFromAnimationQueue(animation);
        resolve();
      });

      animation.addEventListener('cancel', () => {
        this.removeFromAnimationQueue(animation);
        resolve();
      });
    });
  }

  /**
   * Optimized page transition with element caching
   */
  async transitionPage(
    fromElement: HTMLElement,
    toElement: HTMLElement,
    transitionType: keyof typeof this.pageTransitions = 'fadeScale'
  ): Promise<void> {
    if (this.prefersReducedMotion) return;

    const transition = this.pageTransitions[transitionType];
    
    try {
      // Use optimized animations
      const exitPromise = fromElement ? 
        this.animateElement(fromElement, this.getExitKeyframes(transitionType), transition.exit, 3) :
        Promise.resolve();
      
      const enterPromise = this.animateElement(toElement, this.getEnterKeyframes(transitionType), transition.enter, 3);
      
      await Promise.all([exitPromise, enterPromise]);
    } catch (error) {
      console.warn('Page transition failed:', error);
    }
  }

  /**
   * Optimized sidebar toggle with cached element reference
   */
  async toggleSidebar(sidebarElement: HTMLElement, isCollapsed: boolean): Promise<boolean> {
    const newCollapsed = !isCollapsed;
    
    try {
      if (!this.prefersReducedMotion && sidebarElement) {
        // Use CSS transitions for better performance
        sidebarElement.style.transition = 'transform 250ms cubic-bezier(0.25, 0.46, 0.45, 0.94)';
        sidebarElement.setAttribute('data-collapsed', newCollapsed.toString());
      }
      
      // Save state (debounced)
      this.debouncedSaveUserPreferences({ sidebarCollapsed: newCollapsed });
      
      return newCollapsed;
    } catch (error) {
      console.warn('Sidebar toggle failed:', error);
      return newCollapsed;
    }
  }

  /**
   * Optimized theme toggle with smooth transition
   */
  async toggleTheme(currentTheme: 'dark'): Promise<'dark'> {
    const newTheme = currentTheme;
    
    try {
      if (!this.prefersReducedMotion) {
        // Add theme transition overlay for smooth effect
        const overlay = document.createElement('div');
        overlay.className = 'theme-transition-overlay';
        document.body.appendChild(overlay);
        
        // Optimize with requestAnimationFrame
        requestAnimationFrame(() => {
          document.documentElement.setAttribute('data-theme', newTheme);
          document.documentElement.classList.add('dark');
        });
        
        // Remove overlay after transition
        setTimeout(() => {
          if (overlay.parentNode) {
            overlay.parentNode.removeChild(overlay);
          }
        }, 150); // Reduced duration
      } else {
        document.documentElement.setAttribute('data-theme', newTheme);
        document.documentElement.classList.add('dark');
      }
      
      // Save theme preference (debounced)
      this.debouncedSaveUserPreferences({ theme: newTheme });
      
      return newTheme;
    } catch (error) {
      console.warn('Theme toggle failed:', error);
      document.documentElement.setAttribute('data-theme', newTheme);
      document.documentElement.classList.add('dark');
      return newTheme;
    }
  }

  /**
   * Optimized component entrance animation
   */
  async animateComponentEntrance(element: HTMLElement, type: 'fade' | 'slide' | 'scale' = 'fade'): Promise<void> {
    // Skip if element is already animating
    if (element.classList.contains('animating')) {
      return;
    }

    element.classList.add('animating');

    const animations = {
      fade: [
        { opacity: 0, transform: 'translateY(5px)' }, // Reduced movement
        { opacity: 1, transform: 'translateY(0)' }
      ],
      slide: [
        { transform: 'translateX(-10px)', opacity: 0 }, // Reduced movement
        { transform: 'translateX(0)', opacity: 1 }
      ],
      scale: [
        { transform: 'scale(0.98)', opacity: 0 }, // Reduced scale
        { transform: 'scale(1)', opacity: 1 }
      ]
    };

    try {
      await this.animateElement(
        element,
        animations[type],
        { duration: 200, easing: 'cubic-bezier(0.25, 0.46, 0.45, 0.94)' } // Faster, smoother
      );
    } finally {
      element.classList.remove('animating');
    }
  }

  /**
   * Batch save multiple UI states with debouncing
   */
  async batchSaveUIState(states: Record<string, any>): Promise<void> {
    // Use debounced saving for better performance
    Object.entries(states).forEach(([key, value]) => {
      this.debouncedSaveUserPreferences({ [key]: value });
    });
  }

  // Private helper methods

  private detectUserPreferences(): void {
    // Detect reduced motion preference
    this.prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    
    // Detect performance capabilities
    const connection = (navigator as any).connection;
    if (connection && (connection.effectiveType === 'slow-2g' || connection.effectiveType === '2g')) {
      this.isPerformanceMode = true;
    }
  }

  private setupOptimizedPerformanceMonitoring(): void {
    // Reduced monitoring frequency for better performance
    setInterval(() => {
      if (this.animationQueue.length > 8) { // Increased threshold
        console.warn('⚡ High animation load detected, cancelling low priority animations');
        // Cancel low priority animations
        this.animationQueue
          .filter(item => item.priority === 1)
          .slice(0, 3) // Only cancel first 3 to prevent jarring effect
          .forEach(item => item.animation.cancel());
      }
    }, 2000); // Reduced frequency
  }

  private removeFromAnimationQueue(animation: Animation): void {
    const index = this.animationQueue.findIndex(item => item.animation === animation);
    if (index > -1) {
      this.animationQueue.splice(index, 1);
    }
  }

  private getEnterKeyframes(transitionType: string): Keyframe[] {
    const keyframes = {
      slideLeft: [
        { transform: 'translateX(50px)', opacity: 0 }, // Reduced movement
        { transform: 'translateX(0)', opacity: 1 }
      ],
      slideRight: [
        { transform: 'translateX(-50px)', opacity: 0 }, // Reduced movement
        { transform: 'translateX(0)', opacity: 1 }
      ],
      fadeScale: [
        { transform: 'scale(0.98)', opacity: 0 }, // Reduced scale
        { transform: 'scale(1)', opacity: 1 }
      ],
      slideUp: [
        { transform: 'translateY(10px)', opacity: 0 }, // Reduced movement
        { transform: 'translateY(0)', opacity: 1 }
      ]
    };
    return keyframes[transitionType as keyof typeof keyframes] || keyframes.fadeScale;
  }

  private getExitKeyframes(transitionType: string): Keyframe[] {
    const keyframes = {
      slideLeft: [
        { transform: 'translateX(0)', opacity: 1 },
        { transform: 'translateX(-50px)', opacity: 0 } // Reduced movement
      ],
      slideRight: [
        { transform: 'translateX(0)', opacity: 1 },
        { transform: 'translateX(50px)', opacity: 0 } // Reduced movement
      ],
      fadeScale: [
        { transform: 'scale(1)', opacity: 1 },
        { transform: 'scale(1.02)', opacity: 0 } // Reduced scale
      ],
      slideUp: [
        { transform: 'translateY(0)', opacity: 1 },
        { transform: 'translateY(-10px)', opacity: 0 } // Reduced movement
      ]
    };
    return keyframes[transitionType as keyof typeof keyframes] || keyframes.fadeScale;
  }

  private injectOptimizedGlobalStyles(): void {
    const styles = `
      :root {
        --motion-duration: 250ms;
        --motion-easing: cubic-bezier(0.25, 0.46, 0.45, 0.94);
        --motion-easing-decelerate: cubic-bezier(0.0, 0.0, 0.2, 1);
        --motion-easing-accelerate: cubic-bezier(0.4, 0.0, 1, 1);
      }

      /* Reduced motion optimizations */
      .reduce-motion * {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
        transition-delay: 0ms !important;
      }

      /* Optimized transitions */
      .smooth-transition {
        transition: all var(--motion-duration) var(--motion-easing);
      }

      .page-transition-enter {
        animation: pageEnterOptimized var(--motion-duration) var(--motion-easing);
      }

      .page-transition-exit {
        animation: pageExitOptimized calc(var(--motion-duration) * 0.8) var(--motion-easing-accelerate);
      }

      /* Optimized keyframes with reduced movement */
      @keyframes pageEnterOptimized {
        from {
          opacity: 0;
          transform: translateY(5px);
        }
        to {
          opacity: 1;
          transform: translateY(0);
        }
      }

      @keyframes pageExitOptimized {
        from {
          opacity: 1;
          transform: translateY(0);
        }
        to {
          opacity: 0;
          transform: translateY(-5px);
        }
      }

      /* Performance optimizations */
      .will-change-transform {
        will-change: transform;
      }

      .will-change-opacity {
        will-change: opacity;
      }

      .gpu-accelerated {
        transform: translateZ(0);
        backface-visibility: hidden;
        perspective: 1000px;
      }

      /* Optimized animating class */
      .animating {
        pointer-events: none; /* Prevent interaction during animation */
      }
    `;

    // Check if styles already injected
    if (!document.querySelector('#enhanced-ui-styles')) {
      const styleSheet = document.createElement('style');
      styleSheet.id = 'enhanced-ui-styles';
      styleSheet.textContent = styles;
      document.head.appendChild(styleSheet);
    }
  }

  /**
   * Cleanup method to prevent memory leaks
   */
  cleanup(): void {
    // Clear debounce timer
    if (this.saveDebounceTimer) {
      clearTimeout(this.saveDebounceTimer);
    }

    // Clear animation timeouts
    this.animationTimeouts.forEach(timeout => clearTimeout(timeout));
    this.animationTimeouts.clear();

    // Cancel all running animations
    this.animationQueue.forEach(item => item.animation.cancel());
    this.animationQueue = [];

    // Clear element cache
    this.elementCache.clear();
  }
}

// Export singleton instance
export const enhancedUI = new EnhancedUIService();
export default enhancedUI;
