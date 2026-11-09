import { useEffect, useRef, useCallback } from 'react';
import { useLocation, useNavigationType } from 'react-router-dom';
import { enhancedUI } from '../services/enhanced-ui.service';

interface NavigationTransitionOptions {
  enabled?: boolean;
  defaultTransition?: 'slideLeft' | 'slideRight' | 'fadeScale' | 'slideUp';
  preserveScrollPosition?: boolean;
}

export function useNavigationTransitions(options: NavigationTransitionOptions = {}) {
  const location = useLocation();
  const navigationType = useNavigationType();
  const previousLocationRef = useRef<string | null>(null);
  const isInitialLoad = useRef(true);
  const isTransitioningRef = useRef(false);
  const elementCacheRef = useRef(new Map<string, HTMLElement>());

  const {
    enabled = true,
    defaultTransition = 'fadeScale',
    preserveScrollPosition = false
  } = options;

  // Optimized element getter with caching
  const getCachedElement = useCallback((selector: string): HTMLElement | null => {
    if (elementCacheRef.current.has(selector)) {
      const cached = elementCacheRef.current.get(selector);
      if (cached && document.contains(cached)) {
        return cached;
      } else {
        elementCacheRef.current.delete(selector);
      }
    }

    const element = document.querySelector(selector) as HTMLElement;
    if (element) {
      elementCacheRef.current.set(selector, element);
    }
    return element;
  }, []);

  // Debounced page transition handler
  const handlePageTransition = useCallback(async () => {
    if (!enabled || isTransitioningRef.current) return;

    // Skip transition on initial page load
    if (isInitialLoad.current) {
      isInitialLoad.current = false;
      
      // Optimized initial entrance
      const mainElement = getCachedElement('main') || getCachedElement('[data-page]');
      if (mainElement) {
        await enhancedUI.animateComponentEntrance(mainElement, 'fade');
      }
      return;
    }

    isTransitioningRef.current = true;

    try {
      // Get main content element (cached)
      const currentPage = getCachedElement('main') || getCachedElement('[data-page]');
      if (!currentPage) return;

      // Determine transition type (simplified logic)
      let transitionType = defaultTransition;
      
      if (navigationType === 'POP') {
        transitionType = 'slideRight';
      }

      // Add transition class for CSS-based animations
      currentPage.classList.add('page-transition-enter');
      document.body.classList.add('transitioning');

      // Use requestAnimationFrame for smooth animation
      await new Promise<void>((resolve) => {
        requestAnimationFrame(async () => {
          try {
            // Animate page entrance
            await enhancedUI.animateComponentEntrance(currentPage, 'fade');
            
            // Handle scroll optimization
            if (!preserveScrollPosition && 'scrollTo' in window) {
              window.scrollTo({ top: 0, behavior: 'auto' }); // Use auto for better performance
            }
            
            resolve();
          } catch (error) {
            console.warn('Animation failed:', error);
            resolve();
          }
        });
      });

    } catch (error) {
      console.warn('Page transition failed:', error);
    } finally {
      // Clean up with optimized timing
      setTimeout(() => {
        const currentPage = getCachedElement('main') || getCachedElement('[data-page]');
        if (currentPage) {
          currentPage.classList.remove('page-transition-enter');
        }
        document.body.classList.remove('transitioning');
        isTransitioningRef.current = false;
      }, 150); // Reduced cleanup delay
    }
  }, [location.pathname, navigationType, enabled, defaultTransition, preserveScrollPosition, getCachedElement]);

  useEffect(() => {
    // Only trigger transition if location actually changed
    if (previousLocationRef.current !== location.pathname) {
      // Use requestIdleCallback for better performance if available
      if ('requestIdleCallback' in window) {
        requestIdleCallback(() => handlePageTransition(), { timeout: 100 });
      } else {
        // Fallback to setTimeout for older browsers
        setTimeout(handlePageTransition, 0);
      }
      previousLocationRef.current = location.pathname;
    }
  }, [location.pathname, handlePageTransition]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      elementCacheRef.current.clear();
      isTransitioningRef.current = false;
    };
  }, []);

  return {
    isTransitioning: isTransitioningRef.current,
    currentPath: location.pathname,
    navigationType
  };
}

// Optimized hook for specific page components
export function usePageAnimations(pageId: string) {
  const pageRef = useRef<HTMLElement | null>(null);
  const hasAnimatedRef = useRef(false);

  useEffect(() => {
    // Prevent duplicate animations
    if (hasAnimatedRef.current) return;

    const animatePageElements = async () => {
      try {
        const page = pageRef.current || document.querySelector(`[data-page="${pageId}"]`) as HTMLElement;
        if (!page) return;

        hasAnimatedRef.current = true;

        // Animate main page container first
        await enhancedUI.animateComponentEntrance(page, 'fade');

        // Optimize child element animation
        const animatableElements = page.querySelectorAll('[data-animate]');
        if (animatableElements.length > 0) {
          // Limit number of animated elements for performance
          const elementsToAnimate = Array.from(animatableElements).slice(0, 6); // Max 6 elements
          
          // Use Promise.all with staggered delays for better performance
          const animationPromises = elementsToAnimate.map((element, index) => {
            return new Promise<void>((resolve) => {
              setTimeout(async () => {
                try {
                  await enhancedUI.animateComponentEntrance(element as HTMLElement, 'slide');
                } catch (error) {
                  console.warn(`Element animation failed:`, error);
                } finally {
                  resolve();
                }
              }, index * 50); // Reduced stagger delay
            });
          });

          await Promise.all(animationPromises);
        }
      } catch (error) {
        console.warn(`Page animation failed for ${pageId}:`, error);
      }
    };

    // Use requestIdleCallback for better performance
    if ('requestIdleCallback' in window) {
      requestIdleCallback(() => animatePageElements(), { timeout: 200 });
    } else {
      // Fallback for older browsers
      setTimeout(animatePageElements, 16); // ~1 frame delay
    }

    // Reset animation flag when page changes
    return () => {
      hasAnimatedRef.current = false;
    };
  }, [pageId]);

  return { pageRef };
} 