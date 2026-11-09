
import { ReactNode } from "react";
import { LucideIcon } from "lucide-react";
import { GlassCard } from "@/components/ui/glass-card";

interface KPICardProps {
  title: string;
  value: string;
  change: string;
  changeType: "positive" | "negative" | "neutral";
  icon: LucideIcon;
  trend?: ReactNode;
}

export function KPICard({ title, value, change, changeType, icon: Icon, trend }: KPICardProps) {
  const changeColor = {
    positive: "text-green-400",
    negative: "text-red-400",
    neutral: "text-yellow-400",
  }[changeType];

  return (
    <GlassCard hover glow className="relative overflow-hidden">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-muted-foreground">{title}</p>
          <p className="text-3xl font-bold text-foreground mt-1">{value}</p>
          <p className={`text-sm mt-2 ${changeColor}`}>
            {change}
          </p>
        </div>
        <div className="p-3 rounded-full bg-gradient-to-r from-blue-500/20 to-purple-500/20 border border-blue-500/30">
          <Icon className="h-6 w-6 text-blue-400" />
        </div>
      </div>
      
      {trend && (
        <div className="mt-4 h-12">
          {trend}
        </div>
      )}
      
      {/* Glow effect */}
      <div className="absolute inset-0 bg-gradient-to-r from-blue-500/5 to-purple-500/5 opacity-0 hover:opacity-100 transition-opacity duration-300" />
    </GlassCard>
  );
}
