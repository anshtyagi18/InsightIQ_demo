import React, { Suspense } from "react";
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { ThemeProvider } from "@/contexts/ThemeContext";
import { useCursorGlow } from "@/hooks/useCursorGlow";
import { useNavigationTransitions } from "@/hooks/useNavigationTransitions";
import { enhancedUI } from "@/services/enhanced-ui.service";
import { useEffect } from "react";
import { PageLoadingFallback } from "@/components/ui/loading-spinner";

// Lazy load all pages for optimal bundle splitting
const Homepage = React.lazy(() => import("./pages/homepage"));
const Index = React.lazy(() => import("./pages/Index"));
const NotFound = React.lazy(() => import("./pages/NotFound"));
const ProviderManager = React.lazy(() => import("./pages/ProviderManager"));

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Add default caching and error handling
      staleTime: 5 * 60 * 1000, // 5 minutes
      retry: 2,
      refetchOnWindowFocus: false,
    },
  },
});

// Global settings
const ENABLE_CUSTOM_CURSOR = false; // Set to true to enable custom cursor glow effect

// Enhanced App Component with Navigation Transitions
const AppContent = () => {
  // Global cursor glow - disabled by default for better performance and cursor visibility
  useCursorGlow(ENABLE_CUSTOM_CURSOR);
  
  // Enable smooth navigation transitions
  const { isTransitioning } = useNavigationTransitions({
    enabled: true,
    defaultTransition: 'fadeScale',
    preserveScrollPosition: false
  });

  // Initialize enhanced UI service on app start
  useEffect(() => {
    const initializeEnhancedUI = async () => {
      try {
        console.log('🎨 Initializing Enhanced UI Service...');
        await enhancedUI.initialize();
        console.log('✅ Enhanced UI Service initialized successfully');
      } catch (error) {
        console.warn('⚠️ Enhanced UI Service initialization failed:', error);
      }
    };

    initializeEnhancedUI();
  }, []);

  return (
    <div className={`app-container ${isTransitioning ? 'transitioning' : ''}`}>
      <Suspense fallback={<PageLoadingFallback text="Loading application..." />}>
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={
            <Suspense fallback={<PageLoadingFallback text="Loading dashboard..." />}>
              <Index />
            </Suspense>
          } />
          <Route path="/datasets" element={
            <Suspense fallback={<PageLoadingFallback text="Loading datasets..." />}>
              <Index />
            </Suspense>
          } />
          <Route path="/workspace" element={
            <Suspense fallback={<PageLoadingFallback text="Loading Insightia Studio..." />}>
              <Index />
            </Suspense>
          } />
          <Route path="/studio" element={
            <Suspense fallback={<PageLoadingFallback text="Loading Insightia Studio..." />}>
              <Index />
            </Suspense>
          } />
          <Route path="/analytics" element={
            <Suspense fallback={<PageLoadingFallback text="Loading analytics..." />}>
              <Index />
            </Suspense>
          } />
          <Route path="/charts" element={
            <Suspense fallback={<PageLoadingFallback text="Loading charts..." />}>
              <Index />
            </Suspense>
          } />
          <Route path="/cleaning" element={
            <Suspense fallback={<PageLoadingFallback text="Loading cleaning..." />}>
              <Index />
            </Suspense>
          } />
          <Route path="/insights" element={
            <Suspense fallback={<PageLoadingFallback text="Loading insights..." />}>
              <Index />
            </Suspense>
          } />
          <Route path="/chat" element={
            <Suspense fallback={<PageLoadingFallback text="Loading chat..." />}>
              <Index />
            </Suspense>
          } />
          <Route path="/forecasting" element={
            <Suspense fallback={<PageLoadingFallback text="Loading forecasting..." />}>
              <Index />
            </Suspense>
          } />
          <Route path="/profile" element={
            <Suspense fallback={<PageLoadingFallback text="Loading profile..." />}>
              <Index />
            </Suspense>
          } />
          <Route path="/provider" element={
            <Suspense fallback={<PageLoadingFallback text="Loading provider manager..." />}>
              <ProviderManager />
            </Suspense>
          } />
          {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
          <Route path="*" element={
            <Suspense fallback={<PageLoadingFallback text="Loading page..." />}>
              <NotFound />
            </Suspense>
          } />
        </Routes>
      </Suspense>
    </div>
  );
};

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <ThemeProvider>
          <TooltipProvider>
            <AppContent />
            <Toaster />
            <Sonner />
          </TooltipProvider>
        </ThemeProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
