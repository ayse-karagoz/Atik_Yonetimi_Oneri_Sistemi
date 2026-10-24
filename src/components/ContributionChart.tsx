import React from 'react';
import { VariableContribution } from '../types';

interface ContributionChartProps {
  contributions: VariableContribution[];
}

export const ContributionChart: React.FC<ContributionChartProps> = ({ contributions }) => {
  // Sort by contribution value descending or keep original order
  const maxAbs = Math.max(
    0.05,
    ...contributions.map((c) => Math.abs(c.contribution))
  );

  return (
    <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs flex flex-col justify-between h-full">
      <div>
        <div className="flex items-center justify-between mb-1">
          <h3 className="text-base font-bold text-slate-800">İlişkili faktörler</h3>
          <span className="text-xs text-slate-500 font-mono">Katkı (z-birim)</span>
        </div>
        <p className="text-xs text-slate-500 mb-4">
          Pozitif değerler model tahminini yükseltir, negatif değerler düşürür.
        </p>

        <div className="space-y-3">
          {contributions.map((item) => {
            const isPos = item.contribution >= 0;
            const widthPct = Math.min(100, (Math.abs(item.contribution) / maxAbs) * 100);

            return (
              <div key={item.variable} className="text-xs">
                <div className="flex justify-between items-center mb-1">
                  <span className="font-medium text-slate-700 truncate max-w-[200px]" title={item.variable}>
                    {item.variable}
                  </span>
                  <div className="flex items-center gap-1.5 font-mono">
                    <span
                      className={`font-bold ${
                        isPos ? 'text-emerald-700' : 'text-rose-700'
                      }`}
                    >
                      {item.contribution >= 0
                        ? `+${item.contribution.toFixed(3)}`
                        : item.contribution.toFixed(3)}
                    </span>
                    <span className="text-[10px] text-slate-400">
                      ({item.relativeSharePct.toFixed(1)}%)
                    </span>
                  </div>
                </div>

                {/* Horizontal divergent bar with center line */}
                <div className="h-4 bg-slate-100 rounded flex items-center relative overflow-hidden">
                  {/* Center vertical baseline at 50% */}
                  <div className="absolute left-1/2 top-0 bottom-0 w-0.5 bg-slate-300 z-10" />

                  {isPos ? (
                    // Right half (50% to 100%)
                    <div
                      className="h-full bg-emerald-500/80 rounded-r transition-all duration-300 absolute left-1/2"
                      style={{ width: `${widthPct / 2}%` }}
                    />
                  ) : (
                    // Left half (0% to 50%)
                    <div
                      className="h-full bg-rose-500/80 rounded-l transition-all duration-300 absolute right-1/2"
                      style={{ width: `${widthPct / 2}%` }}
                    />
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500">
        <div className="flex items-center gap-3">
          <span className="inline-flex items-center gap-1">
            <span className="w-2.5 h-2.5 rounded-sm bg-rose-500/80" />
            Atık Tahminini Düşüren (&minus;)
          </span>
          <span className="inline-flex items-center gap-1">
            <span className="w-2.5 h-2.5 rounded-sm bg-emerald-500/80" />
            Atık Tahminini Yükselten (+)
          </span>
        </div>
      </div>
    </div>
  );
};
