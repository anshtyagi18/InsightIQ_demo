import React, { Suspense } from "react";
import { useLocation } from "react-router-dom";
import { useTheme } from "@/contexts/ThemeContext";
import { usePageAnimations } from "@/hooks/useNavigationTransitions";
import { Sidebar } from "@/components/layout/sidebar";
import { PageLoadingFallback, ComponentLoadingFallback } from "@/components/ui/loading-spinner";

// Lazy load main page components for better performance
const Dashboard = React.lazy(() => import("./dashboard"));
const Profile = React.lazy(() => import("./profile"));
const Datasets = React.lazy(() => import("./datasets"));
const Analytics = React.lazy(() => import("./analytics").then(m => ({ default: m.Analytics })));
const InsightiaStudio = React.lazy(() => import("@/components/insightia/InsightiaWorkspace").then(m => ({ default: m.InsightiaWorkspace })));

export default function Index() {
  const location = useLocation();
  const { sidebarCollapsed } = useTheme();
  const { pageRef } = usePageAnimations('main-content');
  
  // Determine page ID for animations
  const getPageId = () => {
    switch (location.pathname) {
      case "/datasets":
        return "datasets";
      case "/profile":
        return "profile";
      case "/analytics":
        return "analytics";
      default:
        return "dashboard";
    }
  };

  const getPageTitle = () => {
    switch (location.pathname) {
      case "/datasets":
        return "Datasets Workspace";
      case "/profile":
        return "User Profile";
      case "/analytics":
        return "Workflow Analytics";
      default:
        return "Analytics Dashboard";
    }
  };

  const renderContent = () => {
    switch (location.pathname) {
      case "/datasets":
        return (
          <Suspense fallback={<ComponentLoadingFallback text="Loading Datasets..." height="60vh" />}>
            <div data-animate data-page="datasets">
              <Datasets />
            </div>
          </Suspense>
        );
      case "/profile":
        return (
          <Suspense fallback={<ComponentLoadingFallback text="Loading Profile..." height="60vh" />}>
            <div data-animate data-page="profile">
              <Profile />
            </div>
          </Suspense>
        );
      case "/analytics":
        return (
          <Suspense fallback={<ComponentLoadingFallback text="Loading Workflow Analytics..." height="60vh" />}>
            <div data-animate data-page="analytics">
              <Analytics />
            </div>
          </Suspense>
        );
      default:
        return (
          <Suspense fallback={<ComponentLoadingFallback text="Loading Dashboard..." height="60vh" />}>
            <div data-animate data-page="dashboard">
              <Dashboard />
            </div>
          </Suspense>
        );
    }
  };

  const isDashboard = getPageId() === "dashboard";

  if (isDashboard) {
    return (
      <div className="h-screen w-screen overflow-hidden bg-[#09090b]">
        <Suspense fallback={<ComponentLoadingFallback text="Loading Analytics Dashboard..." height="100vh" />}>
          <Dashboard />
        </Suspense>
      </div>
    );
  }

  if (getPageId() === "datasets" || location.pathname === "/workspace" || location.pathname === "/studio") {
    return (
      <div className="h-screen w-screen overflow-hidden bg-[#09090b]">
        <Suspense fallback={<ComponentLoadingFallback text="Loading Insightia Studio..." height="100vh" />}>
          <InsightiaStudio />
        </Suspense>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex w-full bg-[#09090b] overflow-hidden" data-page-container>
      <Sidebar data-sidebar />
      <main 
        ref={pageRef}
        className={`flex-1 p-4 md:p-6 overflow-y-auto transition-all duration-300 will-change-transform ${
          sidebarCollapsed ? 'lg:ml-0' : 'lg:ml-0'
        }`}
        data-page={getPageId()}
        aria-label={`${getPageTitle()} - Main Content`}
      >
        <div className="h-full w-full">
          {renderContent()}
        </div>
      </main>
    </div>
  );
}
