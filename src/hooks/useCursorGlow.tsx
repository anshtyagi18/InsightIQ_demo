import { useEffect, useRef } from 'react';

// Global flag to prevent multiple cursor instances
let cursorInstance: HTMLElement | null = null;
let isEnabled = false;

export function useCursorGlow(enabled: boolean = false) {
  const hasInitialized = useRef(false);

  useEffect(() => {
    // Only initialize once per app and only if enabled
    if (hasInitialized.current || !enabled || cursorInstance) {
      return;
    }

    // Check if device supports hover (not on touch devices)
    const supportsHover = window.matchMedia('(hover: hover)').matches;
    if (!supportsHover) {
      return;
    }

    hasInitialized.current = true;
    isEnabled = true;

    // Add custom cursor class to body
    document.body.classList.add('custom-cursor-enabled');

    // Create cursor element
    const cursor = document.createElement('div');
    cursor.className = 'cursor-glow';
    document.body.appendChild(cursor);
    cursorInstance = cursor;

    // Use throttled mouse movement for better performance
    let animationFrame: number;
    
    const moveCursor = (e: MouseEvent) => {
      if (animationFrame) {
        cancelAnimationFrame(animationFrame);
      }
      
      animationFrame = requestAnimationFrame(() => {
        if (cursor && document.body.contains(cursor)) {
          cursor.style.transform = `translate(${e.clientX - 10}px, ${e.clientY - 10}px)`;
          cursor.style.opacity = '1';
        }
      });
    };

    const hideCursor = () => {
      if (cursor) {
        cursor.style.opacity = '0';
      }
    };

    const showCursor = () => {
      if (cursor) {
        cursor.style.opacity = '1';
      }
    };

    // Add event listeners with passive flag for better performance
    document.addEventListener('mousemove', moveCursor, { passive: true });
    document.addEventListener('mouseleave', hideCursor, { passive: true });
    document.addEventListener('mouseenter', showCursor, { passive: true });

    // Cleanup function
    return () => {
      if (animationFrame) {
        cancelAnimationFrame(animationFrame);
      }
      
      document.removeEventListener('mousemove', moveCursor);
      document.removeEventListener('mouseleave', hideCursor);
      document.removeEventListener('mouseenter', showCursor);
      
      if (cursor && document.body.contains(cursor)) {
        document.body.removeChild(cursor);
      }
      
      document.body.classList.remove('custom-cursor-enabled');
      cursorInstance = null;
      isEnabled = false;
      hasInitialized.current = false;
    };
  }, [enabled]);
}

// Export a function to disable cursor globally if needed
export function disableCursorGlow() {
  if (cursorInstance && document.body.contains(cursorInstance)) {
    document.body.removeChild(cursorInstance);
  }
  document.body.classList.remove('custom-cursor-enabled');
  cursorInstance = null;
  isEnabled = false;
}
