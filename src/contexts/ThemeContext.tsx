import { createContext, useContext, useState, useEffect, useCallback, useMemo, ReactNode } from 'react';
import { dbStorage } from '../services/db-storage.service';
import { enhancedUI, UIPreferences } from '../services/enhanced-ui.service';

type Theme = 'dark';

interface ThemeContextType {
  theme: Theme;
  sidebarCollapsed: boolean;
  toggleSidebar: () => Promise<void>;
  isLoading: boolean;
  preferences: UIPreferences;
  updatePreferences: (newPrefs: Partial<UIPreferences>) => Promise<void>;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme] = useState<Theme>('dark');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [preferences, setPreferences] = useState<UIPreferences>({
    theme: 'dark',
    animations: true,
    reducedMotion: false,
    sidebarCollapsed: false,
    density: 'normal',
    fontSize: 'medium',
    contrast: 'normal'
  });

  const toggleSidebar = useCallback(async () => {
    try {
      // Find sidebar element for animation (cached lookup)
      const sidebarElement = document.querySelector('[data-sidebar]') as HTMLElement;
      
      if (sidebarElement) {
        // Use enhanced UI service for smooth sidebar animation
        const newCollapsed = await enhancedUI.toggleSidebar(sidebarElement, sidebarCollapsed);
        setSidebarCollapsed(newCollapsed);
        
        // Update preferences state efficiently
        setPreferences(prev => ({ ...prev, sidebarCollapsed: newCollapsed }));
      } else {
        // Fallback: instant toggle
        const newCollapsed = !sidebarCollapsed;
        setSidebarCollapsed(newCollapsed);
        
        // Save to database (debounced)
        await dbStorage.setItem('sidebar-collapsed', JSON.stringify(newCollapsed));
      }
    } catch (error) {
      console.warn('⚠️ Sidebar toggle failed:', error);
      // Fallback: instant toggle with localStorage
      const newCollapsed = !sidebarCollapsed;
      setSidebarCollapsed(newCollapsed);
      localStorage.setItem('sidebar-collapsed', JSON.stringify(newCollapsed));
    }
  }, [sidebarCollapsed]);

  const updatePreferences = useCallback(async (newPrefs: Partial<UIPreferences>) => {
    try {
      // Force theme to always be dark
      const updatedPrefs = { ...newPrefs, theme: 'dark' as const };
      
      // Use functional state update for better performance
      setPreferences(prev => {
        const mergedPrefs = { ...prev, ...updatedPrefs };
        
        // Apply preferences using enhanced UI service (async, non-blocking)
        enhancedUI.applyUIPreferences(mergedPrefs).catch(error => {
          console.warn('⚠️ Failed to apply preferences:', error);
        });
        
        return mergedPrefs;
      });
      
      // Update sidebar state if changed
      if (updatedPrefs.sidebarCollapsed !== undefined && updatedPrefs.sidebarCollapsed !== sidebarCollapsed) {
        setSidebarCollapsed(updatedPrefs.sidebarCollapsed);
      }
      
      console.log('✅ UI preferences updated:', updatedPrefs);
    } catch (error) {
      console.warn('⚠️ Failed to update preferences:', error);
    }
  }, [sidebarCollapsed]);

  // Load saved preferences on component mount
  useEffect(() => {
    let isMounted = true;

    const loadUserPreferences = async () => {
      setIsLoading(true);
      
      try {
        // Initialize enhanced UI service and load preferences
        const loadedPrefs = await enhancedUI.initialize();
        
        if (isMounted) {
          // Force theme to dark mode
          const darkModePrefs = { ...loadedPrefs, theme: 'dark' as const };
          setPreferences(darkModePrefs);
          setSidebarCollapsed(darkModePrefs.sidebarCollapsed);
          
          console.log(`🎨 Loaded UI preferences (forced dark mode):`, darkModePrefs);
          
          // Legacy migration: check for old localStorage values
          await migrateLegacyPreferences();
        }
        
      } catch (error) {
        console.warn('⚠️ Failed to load preferences, using fallbacks:', error);
        
        if (isMounted) {
          // Fallback to legacy localStorage loading
          await loadLegacyPreferences();
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    const migrateLegacyPreferences = async () => {
      try {
        let needsMigration = false;
        const updates: Partial<UIPreferences> = { theme: 'dark' }; // Force dark theme
        
        // Check for legacy sidebar preference
        const legacySidebar = localStorage.getItem('sidebar-collapsed');
        if (legacySidebar) {
          const collapsed = JSON.parse(legacySidebar);
          if (collapsed !== sidebarCollapsed) {
            updates.sidebarCollapsed = collapsed;
            needsMigration = true;
          }
        }
        
        // Always migrate to ensure dark theme is set
        needsMigration = true;
        
        // If migration needed, update preferences and clear legacy data
        if (needsMigration && isMounted) {
          await updatePreferences(updates);
          
          // Clear migrated localStorage items
          localStorage.removeItem('theme-preference');
          localStorage.removeItem('sidebar-collapsed');
          
          console.log('🔄 Migrated legacy preferences to database (forced dark mode)');
        }
      } catch (error) {
        console.warn('Migration failed:', error);
      }
    };

    const loadLegacyPreferences = async () => {
      try {
        // Always set dark theme regardless of saved preference
        if (isMounted) {
          document.documentElement.setAttribute('data-theme', 'dark');
          document.documentElement.classList.add('dark');
        }
        
        // Load sidebar preference  
        const savedSidebar = localStorage.getItem('sidebar-collapsed');
        if (savedSidebar) {
          try {
            const collapsed = JSON.parse(savedSidebar);
            if (isMounted) {
              setSidebarCollapsed(collapsed);
            }
          } catch (error) {
            console.warn('Failed to parse sidebar preference:', error);
          }
        }
        
        console.log('📱 Loaded legacy preferences with forced dark mode');
      } catch (error) {
        console.warn('Failed to load legacy preferences:', error);
      }
    };

    loadUserPreferences();

    return () => {
      isMounted = false;
    };
  }, [updatePreferences, sidebarCollapsed]);

  // Ensure dark theme is always applied
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', 'dark');
    document.documentElement.classList.add('dark');
  }, []);

  // Memoized context value for performance optimization
  const contextValue = useMemo(() => ({
    theme,
    sidebarCollapsed,
    toggleSidebar,
    isLoading,
    preferences,
    updatePreferences
  }), [theme, sidebarCollapsed, toggleSidebar, isLoading, preferences, updatePreferences]);

  return (
    <ThemeContext.Provider value={contextValue}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}
