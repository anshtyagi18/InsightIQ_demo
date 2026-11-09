
import { Bell, Check, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { GlassCard } from "@/components/ui/glass-card";
import { useNotifications } from "@/hooks/useNotifications";
import { cn } from "@/lib/utils";

export function NotificationsDropdown() {
  const { notifications, isOpen, setIsOpen, markAsRead, markAllAsRead, unreadCount } = useNotifications();

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'success': return 'bg-green-500';
      case 'warning': return 'bg-yellow-500';
      case 'error': return 'bg-red-500';
      default: return 'bg-blue-500';
    }
  };

  return (
    <div className="relative" style={{ zIndex: 999999 }}>
      <Button
        variant="ghost"
        size="sm"
        className="relative glass-button hover:scale-105 transition-all duration-200 p-2"
        onClick={() => setIsOpen(!isOpen)}
      >
        <Bell className="h-5 w-5" />
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 h-5 w-5 rounded-full bg-red-500 text-xs text-white flex items-center justify-center animate-pulse">
            {unreadCount}
          </span>
        )}
      </Button>

      {isOpen && (
        <>
          <div
            className="fixed inset-0"
            style={{ zIndex: 999997 }}
            onClick={() => setIsOpen(false)}
          />
          <div 
            className="absolute right-0 top-full mt-2 w-80 max-h-96"
            style={{ zIndex: 999998 }}
          >
            <GlassCard className="p-0 max-h-96 overflow-hidden shadow-2xl bg-white/95 dark:bg-slate-800/95 backdrop-blur-lg border border-border">
              <div className="p-4 border-b border-border flex items-center justify-between">
                <h3 className="font-semibold text-foreground">Notifications</h3>
                <div className="flex gap-2">
                  <Button 
                    size="sm" 
                    variant="ghost" 
                    onClick={markAllAsRead}
                    className="text-xs hover:bg-muted text-foreground"
                  >
                    <Check className="h-3 w-3 mr-1" />
                    Mark all read
                  </Button>
                  <Button 
                    size="sm" 
                    variant="ghost" 
                    onClick={() => setIsOpen(false)}
                    className="hover:bg-muted text-foreground"
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              </div>
              
              <div className="max-h-72 overflow-y-auto">
                {notifications.map((notification) => (
                  <div 
                    key={notification.id}
                    className={cn(
                      "p-4 border-b border-border cursor-pointer hover:bg-muted/50 transition-colors",
                      !notification.read && "bg-muted/30"
                    )}
                    onClick={() => markAsRead(notification.id)}
                  >
                    <div className="flex items-start gap-3">
                      <div className={cn("w-2 h-2 rounded-full mt-2 flex-shrink-0", getTypeColor(notification.type))} />
                      <div className="flex-1 min-w-0">
                        <h4 className="text-sm font-medium text-foreground">{notification.title}</h4>
                        <p className="text-xs text-muted-foreground mt-1">{notification.message}</p>
                        <p className="text-xs text-muted-foreground mt-2">
                          {notification.timestamp.toLocaleTimeString()}
                        </p>
                      </div>
                      {!notification.read && (
                        <div className="w-2 h-2 bg-blue-500 rounded-full flex-shrink-0 mt-2" />
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </GlassCard>
          </div>
        </>
      )}
    </div>
  );
}
