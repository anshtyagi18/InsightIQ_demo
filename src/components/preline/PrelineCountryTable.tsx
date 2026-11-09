/**
 * Preline Country Table Component
 * Styled in Pure Smooth Z-Black (#0e0e11) with crisp zinc-800 separators.
 */

import React from 'react';

export interface CountryRow {
  id: string;
  name: string;
  code: string;
  flagUrl: string;
  visits: string;
  purchases: string;
  percentage: number;
}

export const DEFAULT_COUNTRIES: CountryRow[] = [
  {
    id: 'us',
    name: 'United States',
    code: 'US',
    flagUrl: 'https://flagcdn.com/w40/us.png',
    visits: '10,013',
    purchases: '$5,300',
    percentage: 85,
  },
  {
    id: 'in',
    name: 'India',
    code: 'IN',
    flagUrl: 'https://flagcdn.com/w40/in.png',
    visits: '8,545',
    purchases: '$5,300',
    percentage: 72,
  },
  {
    id: 'cn',
    name: 'China',
    code: 'CN',
    flagUrl: 'https://flagcdn.com/w40/cn.png',
    visits: '6,837',
    purchases: '$3,950',
    percentage: 58,
  },
  {
    id: 'br',
    name: 'Brasil',
    code: 'BR',
    flagUrl: 'https://flagcdn.com/w40/br.png',
    visits: '4,512',
    purchases: '$2,500',
    percentage: 42,
  },
  {
    id: 'de',
    name: 'Germany',
    code: 'DE',
    flagUrl: 'https://flagcdn.com/w40/de.png',
    visits: '3,795',
    purchases: '$1,150',
    percentage: 33,
  },
  {
    id: 'gb',
    name: 'United Kingdom',
    code: 'GB',
    flagUrl: 'https://flagcdn.com/w40/gb.png',
    visits: '2,100',
    purchases: '$1,050',
    percentage: 24,
  },
];

interface PrelineCountryTableProps {
  countries?: CountryRow[];
  selectedCountry?: string | null;
  onSelectCountry?: (country: string) => void;
}

export const PrelineCountryTable: React.FC<PrelineCountryTableProps> = ({
  countries = DEFAULT_COUNTRIES,
  selectedCountry,
  onSelectCountry,
}) => {
  return (
    <div className="flex flex-col h-full justify-between select-none">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-[#27272a]">
          <thead>
            <tr>
              <th scope="col" className="py-2.5 text-left text-xs font-semibold text-zinc-400 uppercase tracking-wider">
                Country
              </th>
              <th scope="col" className="py-2.5 text-right text-xs font-semibold text-zinc-400 uppercase tracking-wider">
                Visits
              </th>
              <th scope="col" className="py-2.5 text-right text-xs font-semibold text-zinc-400 uppercase tracking-wider">
                Purchases
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#27272a]/60">
            {countries.map((c) => {
              const isSelected = selectedCountry === c.name;
              return (
                <tr
                  key={c.id}
                  onClick={() => onSelectCountry?.(c.name)}
                  className={`hover:bg-[#141418] transition-colors cursor-pointer ${
                    isSelected ? 'bg-blue-600/15 border-l-2 border-blue-500' : ''
                  }`}
                >
                  <td className="py-2.5 whitespace-nowrap">
                    <div className="flex items-center gap-3">
                      <img
                        src={c.flagUrl}
                        alt={c.name}
                        className="w-5 h-3.5 object-cover rounded-xs shadow-xs border border-[#27272a]"
                        onError={(e) => {
                          (e.target as HTMLElement).style.display = 'none';
                        }}
                      />
                      <span className="text-sm font-medium text-zinc-200">
                        {c.name}
                      </span>
                    </div>
                  </td>
                  <td className="py-2.5 whitespace-nowrap text-right text-sm text-zinc-300 font-mono">
                    {c.visits}
                  </td>
                  <td className="py-2.5 whitespace-nowrap text-right text-sm font-semibold text-zinc-100 font-mono">
                    {c.purchases}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Subtle Horizontal Scroll / Progress Bar at bottom */}
      <div className="w-full mt-4 pt-2 border-t border-[#27272a]">
        <div className="w-full bg-[#18181d] h-1 rounded-full overflow-hidden">
          <div className="bg-[#27272a] h-1 w-1/3 rounded-full" />
        </div>
      </div>
    </div>
  );
};
