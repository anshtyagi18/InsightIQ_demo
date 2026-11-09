/**
 * Preline Top Header Component
 * Styled in Pure Smooth Z-Black (#09090b) with crisp zinc-800 borders.
 * Strictly greys-out and disables non-functional demo elements while keeping functional buttons active.
 */

import React, { useState } from 'react';
import { 
  Smartphone, 
  Monitor, 
  ExternalLink, 
  Moon, 
  Sun, 
  ChevronDown, 
  ArrowRight,
  UploadCloud
} from 'lucide-react';

interface PrelineTopHeaderProps {
  onUploadClick?: () => void;
  onExportClick?: () => void;
  isDarkMode?: boolean;
  onToggleDarkMode?: () => void;
}

export const PrelineTopHeader: React.FC<PrelineTopHeaderProps> = ({
  onUploadClick,
  onExportClick,
  isDarkMode = true,
  onToggleDarkMode,
}) => {
  const [activeDevice, setActiveDevice] = useState<'mobile' | 'desktop'>('desktop');

  return (
    <header className="w-full bg-[#09090b] border-b border-[#27272a] px-4 py-2.5 flex items-center justify-between select-none transition-colors">
      {/* Left: Title & Breadcrumbs */}
      <div className="flex flex-col">
        <div className="flex items-center gap-2">
          <span className="text-sm font-bold text-zinc-100 tracking-tight">
            Insightia Analytics Dashboard
          </span>
          <button 
            className="inline-flex items-center gap-1 text-[11px] font-medium text-zinc-400 bg-[#141418] border border-[#27272a] px-2 py-0.5 rounded opacity-40 cursor-not-allowed pointer-events-none select-none"
            title="Coming Soon"
          >
            <span>Preview</span>
            <span className="text-[9px] uppercase px-1 py-0.2 rounded bg-zinc-800 text-zinc-400 font-mono">Soon</span>
          </button>
        </div>

        <nav className="flex items-center gap-1.5 text-[11px] text-zinc-500 mt-0.5">
          <span>Insightia</span>
          <span>&gt;</span>
          <span>Analytics &amp; Intelligence</span>
          <span>&gt;</span>
          <span className="text-zinc-300 font-medium">Data Platform</span>
        </nav>
      </div>

      {/* Center: Device Viewport Switcher */}
      <div className="hidden md:flex items-center p-0.5 bg-[#121215] rounded-lg border border-[#27272a]">
        <button
          onClick={() => setActiveDevice('mobile')}
          className={`p-1.5 rounded-md text-zinc-400 hover:text-zinc-100 transition-all ${
            activeDevice === 'mobile' ? 'bg-[#22222a] border border-zinc-700/60 text-zinc-100 shadow-xs' : ''
          }`}
          title="Mobile Viewport Preview"
        >
          <Smartphone className="w-4 h-4" />
        </button>
        <button
          onClick={() => setActiveDevice('desktop')}
          className={`p-1.5 rounded-md text-zinc-400 hover:text-zinc-100 transition-all ${
            activeDevice === 'desktop' ? 'bg-[#22222a] border border-zinc-700/60 text-zinc-100 shadow-xs' : ''
          }`}
          title="Desktop Viewport"
        >
          <Monitor className="w-4 h-4" />
        </button>
        <button
          onClick={() => window.open(window.location.href, '_blank')}
          className="p-1.5 rounded-md text-zinc-400 hover:text-zinc-100 transition-all"
          title="Open in new window"
        >
          <ExternalLink className="w-4 h-4" />
        </button>
      </div>

      {/* Right: Theme, Font, Mode & CTA Button */}
      <div className="flex items-center gap-3">
        {/* Color Theme Selector (Disabled / Demo with Soon pill) */}
        <div 
          className="hidden sm:flex items-center gap-1.5 text-xs font-medium text-zinc-400 opacity-40 cursor-not-allowed pointer-events-none select-none"
          title="Theme Switcher - Coming Soon"
        >
          <span className="w-2.5 h-2.5 rounded-full bg-blue-500 ring-2 ring-blue-900/50" />
          <span>Themes</span>
          <span className="text-[9px] uppercase px-1 py-0.2 rounded bg-zinc-800 text-zinc-400 font-mono">Soon</span>
        </div>

        {/* Font Selector (Disabled / Demo with Soon pill) */}
        <div 
          className="hidden sm:flex items-center gap-1 text-xs font-medium text-zinc-400 opacity-40 cursor-not-allowed pointer-events-none select-none"
          title="Font Switcher - Coming Soon"
        >
          <span className="text-[11px] font-serif font-bold">Aa</span>
          <span>Inter</span>
          <span className="text-[9px] uppercase px-1 py-0.2 rounded bg-zinc-800 text-zinc-400 font-mono">Soon</span>
        </div>

        {/* Mode Toggle Button (Active & functional) */}
        <button
          onClick={onToggleDarkMode}
          className="p-1.5 text-zinc-400 hover:text-zinc-100 rounded-md hover:bg-[#18181d] border border-transparent hover:border-[#27272a] transition-colors cursor-pointer"
          title="Toggle Light/Dark Theme"
        >
          {isDarkMode ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4" />}
        </button>

        {/* Primary CTA Button: Upload Dataset */}
        <button
          onClick={onUploadClick}
          className="inline-flex items-center gap-1.5 bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs px-3.5 py-1.5 rounded-lg shadow-sm transition-colors cursor-pointer"
          title="Upload Dataset (.csv, .xlsx, .json)"
        >
          <UploadCloud className="w-3.5 h-3.5" />
          <span>Upload Data</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </button>
      </div>
    </header>
  );
};
