/**
 * Preline UI World Map Component
 * Styled in Pure Smooth Z-Black with dark graphite inactive continents
 * and electric blue active highlighted territories with glow.
 */

import React, { useState } from 'react';

interface PrelineWorldMapProps {
  onSelectCountry?: (country: string) => void;
  selectedCountry?: string | null;
}

export const PrelineWorldMap: React.FC<PrelineWorldMapProps> = ({
  onSelectCountry,
  selectedCountry,
}) => {
  const [hoveredCountry, setHoveredCountry] = useState<string | null>(null);

  return (
    <div className="relative w-full h-[320px] flex items-center justify-center p-2 select-none">
      <svg
        viewBox="0 0 1000 500"
        className="w-full h-full max-h-[300px] overflow-visible"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          <filter id="map-glow" x="-15%" y="-15%" width="130%" height="130%">
            <feDropShadow dx="0" dy="2" stdDeviation="4" floodColor="#3b82f6" floodOpacity="0.35" />
          </filter>
        </defs>

        {/* --- INACTIVE BASE CONTINENTS (Dark Graphite #1e2026 with #2c303a borders) --- */}
        <g fill="#1e2026" stroke="#2c303a" strokeWidth="0.8" className="transition-colors">
          {/* North America (Canada & Northern lands) */}
          <path d="M120 70 L260 50 L340 70 L300 120 L230 140 L160 110 Z" />
          <path d="M140 100 L240 100 L260 150 L190 170 L130 140 Z" />
          {/* Greenland */}
          <path d="M340 30 L400 35 L380 90 L330 85 Z" />
          {/* Mexico & Central America */}
          <path d="M150 210 L230 200 L240 260 L210 270 L170 230 Z" />
          {/* South America (Rest of Latin America) */}
          <path d="M220 270 L280 270 L270 340 L230 380 L220 450 L190 350 Z" />
          {/* Africa */}
          <path d="M460 180 L560 180 L570 260 L540 370 L480 370 L460 270 Z" />
          {/* Europe (Rest of Europe) */}
          <path d="M460 80 L540 70 L550 140 L460 160 Z" />
          <path d="M430 120 L480 110 L470 160 L420 160 Z" />
          {/* Russia / North Asia */}
          <path d="M560 60 L850 50 L840 140 L650 150 L560 110 Z" />
          {/* South East Asia & Japan */}
          <path d="M760 210 L840 210 L820 290 L760 260 Z" />
          <path d="M830 140 L860 140 L840 200 L820 190 Z" />
          {/* Australia & Oceania */}
          <path d="M780 330 L890 330 L880 420 L780 410 Z" />
        </g>

        {/* --- ACTIVE HIGHLIGHTED COUNTRIES (Electric Royal Blue #2563EB / #3B82F6) --- */}
        {/* 1. United States & Alaska */}
        <g
          className="cursor-pointer transition-all duration-200"
          onMouseEnter={() => setHoveredCountry('United States')}
          onMouseLeave={() => setHoveredCountry(null)}
          onClick={() => onSelectCountry?.('United States')}
        >
          {/* Alaska */}
          <path
            d="M80 65 L135 60 L130 120 L75 110 Z"
            fill={selectedCountry === 'United States' || hoveredCountry === 'United States' ? '#3b82f6' : '#2563eb'}
            stroke="#60a5fa"
            strokeWidth="0.8"
            filter="url(#map-glow)"
          />
          {/* Main Continental USA */}
          <path
            d="M140 145 L285 135 L275 210 L160 215 Z"
            fill={selectedCountry === 'United States' || hoveredCountry === 'United States' ? '#3b82f6' : '#2563eb'}
            stroke="#60a5fa"
            strokeWidth="0.8"
            filter="url(#map-glow)"
          />
        </g>

        {/* 2. Brasil */}
        <g
          className="cursor-pointer transition-all duration-200"
          onMouseEnter={() => setHoveredCountry('Brasil')}
          onMouseLeave={() => setHoveredCountry(null)}
          onClick={() => onSelectCountry?.('Brasil')}
        >
          <path
            d="M260 270 L345 275 L330 365 L270 360 L245 300 Z"
            fill={selectedCountry === 'Brasil' || hoveredCountry === 'Brasil' ? '#3b82f6' : '#2563eb'}
            stroke="#60a5fa"
            strokeWidth="0.8"
            filter="url(#map-glow)"
          />
        </g>

        {/* 3. United Kingdom */}
        <g
          className="cursor-pointer transition-all duration-200"
          onMouseEnter={() => setHoveredCountry('United Kingdom')}
          onMouseLeave={() => setHoveredCountry(null)}
          onClick={() => onSelectCountry?.('United Kingdom')}
        >
          <path
            d="M455 105 L475 105 L470 140 L450 135 Z"
            fill={selectedCountry === 'United Kingdom' || hoveredCountry === 'United Kingdom' ? '#3b82f6' : '#2563eb'}
            stroke="#60a5fa"
            strokeWidth="0.8"
            filter="url(#map-glow)"
          />
        </g>

        {/* 4. Germany */}
        <g
          className="cursor-pointer transition-all duration-200"
          onMouseEnter={() => setHoveredCountry('Germany')}
          onMouseLeave={() => setHoveredCountry(null)}
          onClick={() => onSelectCountry?.('Germany')}
        >
          <path
            d="M485 110 L510 110 L508 140 L483 140 Z"
            fill={selectedCountry === 'Germany' || hoveredCountry === 'Germany' ? '#3b82f6' : '#2563eb'}
            stroke="#60a5fa"
            strokeWidth="0.8"
            filter="url(#map-glow)"
          />
        </g>

        {/* 5. India */}
        <g
          className="cursor-pointer transition-all duration-200"
          onMouseEnter={() => setHoveredCountry('India')}
          onMouseLeave={() => setHoveredCountry(null)}
          onClick={() => onSelectCountry?.('India')}
        >
          <path
            d="M660 190 L710 185 L705 255 L675 285 L650 220 Z"
            fill={selectedCountry === 'India' || hoveredCountry === 'India' ? '#3b82f6' : '#2563eb'}
            stroke="#60a5fa"
            strokeWidth="0.8"
            filter="url(#map-glow)"
          />
        </g>

        {/* 6. China */}
        <g
          className="cursor-pointer transition-all duration-200"
          onMouseEnter={() => setHoveredCountry('China')}
          onMouseLeave={() => setHoveredCountry(null)}
          onClick={() => onSelectCountry?.('China')}
        >
          <path
            d="M680 145 L810 140 L795 215 L710 215 L675 165 Z"
            fill={selectedCountry === 'China' || hoveredCountry === 'China' ? '#3b82f6' : '#2563eb'}
            stroke="#60a5fa"
            strokeWidth="0.8"
            filter="url(#map-glow)"
          />
        </g>
      </svg>

      {/* Floating Hover Indicator Tooltip */}
      {hoveredCountry && (
        <div className="absolute top-4 left-4 bg-[#141418] border border-[#27272a] text-zinc-100 px-2.5 py-1 rounded text-xs font-medium shadow-lg pointer-events-none">
          Active Territory: <span className="text-blue-400 font-bold">{hoveredCountry}</span>
        </div>
      )}
    </div>
  );
};
