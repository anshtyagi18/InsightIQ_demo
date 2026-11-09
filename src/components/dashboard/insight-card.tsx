
import { ReactNode } from "react";
import { LucideIcon } from "lucide-react";
import { GlassCard } from "@/components/ui/glass-card";
import { Badge } from "@/components/ui/badge";

interface InsightCardProps {
  title: string;
  description: string;
  icon: LucideIcon;
  priority: "high" | "medium" | "low";
  tags?: string[];
  action?: ReactNode;
}

export function InsightCard({ title, description, icon: Icon, priority, tags, action }: InsightCardProps) {
  const priorityColors = {
    high: "bg-red-500/25 text-red-200 dark:text-red-100 border-red-500/40 font-bold",
    medium: "bg-yellow-500/25 text-yellow-200 dark:text-yellow-100 border-yellow-500/40 font-bold",
    low: "bg-emerald-500/25 text-emerald-200 dark:text-emerald-100 border-emerald-500/40 font-bold",
  };

  return (
    <GlassCard hover className="animate-slide-up border border-slate-700/80 bg-slate-900/90">
      <div className="flex items-start space-x-4">
        <div className="p-2 rounded-lg bg-gradient-to-r from-blue-500/20 to-purple-500/20 border border-blue-400/40">
          <Icon className="h-5 w-5 text-blue-300 dark:text-blue-200" />
        </div>
        
        <div className="flex-1">
          <div className="flex items-center justify-between mb-2">
            <h4 className="font-bold text-white dark:text-white text-base tracking-tight">{title}</h4>
            <Badge variant="outline" className={priorityColors[priority]}>
              {priority}
            </Badge>
          </div>
          
          <p className="text-slate-100 dark:text-white/90 text-sm mb-3 font-normal leading-relaxed">{description}</p>
          
          {tags && (
            <div className="flex flex-wrap gap-2 mb-3">
              {tags.map((tag) => (
                <Badge key={tag} variant="secondary" className="bg-slate-950 text-slate-100 dark:bg-slate-950 dark:text-slate-100 border border-slate-700/80 hover:bg-slate-800">
                  {tag}
                </Badge>
              ))}
            </div>
          )}
          
          {action && (
            <div className="mt-3">
              {action}
            </div>
          )}
        </div>
      </div>
    </GlassCard>
  );
}
