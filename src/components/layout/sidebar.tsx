import { Link, useLocation } from "react-router-dom";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  Database,
  User,
  Menu,
  X,
  GitCompare,
  Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { useTheme } from "@/contexts/ThemeContext";

const navigation = [
  { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { name: "Datasets", href: "/datasets", icon: Database },
  { name: "Profile", href: "/profile", icon: User },
];

export function Sidebar() {
  const { sidebarCollapsed, toggleSidebar } = useTheme();
  const location = useLocation();

  const SidebarContent = () => (
    <div className="flex h-full flex-col glass-card border-0 rounded-none lg:rounded-2xl m-0 lg:m-4 overflow-hidden">
      {/* Header */}
      <div className={cn(
        "flex items-center border-b border-white/10 transition-all duration-300",
        sidebarCollapsed ? "h-16 px-2 justify-center" : "h-16 px-4 justify-between"
      )}>
        {!sidebarCollapsed && (
          <div className="flex items-center space-x-3">
            <div className="relative flex items-center justify-center">
              <div className="h-8 w-8 rounded-lg bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-600 flex items-center justify-center shadow-lg">
                <Sparkles className="w-4 h-4 text-white" />
              </div>
            </div>
            <div className="flex flex-col">
              <span className="text-lg font-bold bg-gradient-to-r from-blue-400 via-indigo-300 to-purple-400 bg-clip-text text-transparent">InsightIQ</span>
              <span className="text-xs text-blue-300/70">Intelligence Platform</span>
            </div>
          </div>
        )}
        
        <Button
          variant="ghost"
          size="sm"
          onClick={toggleSidebar}
          className={cn(
            "hover:bg-white/10 text-white/80 hover:text-white transition-all duration-300",
            sidebarCollapsed ? "h-10 w-10 p-0" : "h-8 w-8 p-0"
          )}
        >
          {sidebarCollapsed ? <Menu className="h-5 w-5" /> : <X className="h-4 w-4" />}
        </Button>
      </div>

      {/* Navigation */}
      <nav className={cn(
        "flex-1 transition-all duration-300",
        sidebarCollapsed ? "px-2 py-4 space-y-3" : "px-4 py-6 space-y-2"
      )}>
        {navigation.map((item) => {
          const isActive = location.pathname === item.href;
          return (
            <Link
              key={item.name}
              to={item.href}
              className={cn(
                "flex items-center text-sm font-medium rounded-lg transition-all duration-300 group relative",
                isActive
                  ? "bg-white/10 text-white border border-white/20"
                  : "text-white/60 hover:text-white hover:bg-white/5",
                sidebarCollapsed 
                  ? "justify-center p-3 w-12 h-12" 
                  : "px-3 py-2.5"
              )}
              title={sidebarCollapsed ? item.name : undefined}
            >
              <item.icon className={cn(
                "flex-shrink-0 transition-all duration-300",
                isActive ? "text-blue-400" : "text-current",
                sidebarCollapsed ? "h-5 w-5" : "h-5 w-5 mr-3"
              )} />
              
              {!sidebarCollapsed && (
                <span className="truncate">{item.name}</span>
              )}
              
              {/* Active indicator */}
              {isActive && !sidebarCollapsed && (
                <div className="ml-auto w-2 h-2 bg-blue-400 rounded-full"></div>
              )}
              
              {/* Active indicator for collapsed state */}
              {isActive && sidebarCollapsed && (
                <div className="absolute -right-1 top-1/2 transform -translate-y-1/2 w-1 h-6 bg-blue-400 rounded-full"></div>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Workspace indicator */}
      <div className={cn(
        "border-t border-white/10 transition-all duration-300",
        sidebarCollapsed ? "p-2" : "p-4"
      )}>
        <div className={cn(
          "flex items-center transition-all duration-300",
          sidebarCollapsed ? "justify-center" : "space-x-3"
        )}>
          <div className="relative flex-shrink-0">
            <div className={cn(
              "rounded-full bg-gradient-to-r from-blue-500 to-indigo-600 flex items-center justify-center transition-all duration-300",
              sidebarCollapsed ? "h-10 w-10" : "h-8 w-8"
            )}>
              <span className={cn(
                "text-white font-bold",
                sidebarCollapsed ? "text-sm" : "text-xs"
              )}>
                IQ
              </span>
            </div>
            <div className={cn(
              "absolute bg-emerald-500 rounded-full border border-background transition-all duration-300",
              sidebarCollapsed 
                ? "-bottom-1 -right-1 w-4 h-4" 
                : "-bottom-0.5 -right-0.5 w-3 h-3"
            )}></div>
          </div>
          
          {!sidebarCollapsed && (
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-white truncate">
                InsightIQ Workspace
              </p>
              <p className="text-xs text-white/60 truncate">Active Environment</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );

  return (
    <div
      className={cn(
        "hidden lg:flex lg:flex-col transition-all duration-300 flex-shrink-0 sticky top-0 h-screen",
        sidebarCollapsed ? "lg:w-20" : "lg:w-64"
      )}
    >
      <SidebarContent />
    </div>
  );
}
