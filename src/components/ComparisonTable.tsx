import React from 'react';
import { ProvinceComparison } from '../types';

interface ComparisonTableProps {
  data: ProvinceComparison[];
  onSelectProvince: (il: string) => void;
}

export const ComparisonTable: React.FC<ComparisonTableProps> = ({
  data,
  onSelectProvince,
}) => {
  return (
    <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs flex flex-col justify-between h-full">
      <div>
        <div className="flex items-center justify-between mb-1">
          <h3 className="text-base font-bold text-slate-800">İl karşılaştırması</h3>
          <span className="text-xs text-slate-400">Özet Tablo</span>
        </div>
        <p className="text-xs text-slate-500 mb-4">
          Seçilen, en benzer ve zıt profil illerinin atık metrikleri
        </p>

        <div className="overflow-x-auto border border-slate-200 rounded-lg">
          <table className="w-full text-left text-xs">
            <thead className="table-header border-b border-slate-200">
              <tr>
                <th className="py-2.5 px-3">Rol</th>
                <th className="py-2.5 px-3">İl</th>
                <th className="py-2.5 px-3 text-right">Kişi başı atık</th>
                <th className="py-2.5 px-3 text-right">Ulusal ort. fark</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {data.map((row) => {
                const diff = row.diffFromNationalAvg;
                const isPos = diff >= 0;
                const roleBadge = {
                  Seçilen: 'bg-emerald-100 text-emerald-800 font-bold',
                  Benzer: 'bg-teal-100 text-teal-800 font-semibold',
                  Zıt: 'bg-amber-100 text-amber-800 font-semibold',
                }[row.role];

                return (
                  <tr key={row.role} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-3 px-3">
                      <span className={`px-2 py-0.5 rounded text-[11px] ${roleBadge}`}>
                        {row.role}
                      </span>
                    </td>
                    <td className="py-3 px-3 font-semibold text-slate-900">
                      <button
                        type="button"
                        onClick={() => onSelectProvince(row.name)}
                        className="hover:text-emerald-700 hover:underline text-left cursor-pointer"
                        title={`${row.name} ilini seç`}
                      >
                        {row.name}
                      </button>
                    </td>
                    <td className="py-3 px-3 text-right font-mono font-bold text-slate-800">
                      {row.wastePerCapita.toFixed(2)}
                      <span className="text-[10px] text-slate-400 font-sans ml-1">kg/gün</span>
                    </td>
                    <td className="py-3 px-3 text-right font-mono font-medium">
                      <span
                        className={`inline-block px-1.5 py-0.5 rounded text-[11px] ${
                          isPos
                            ? 'text-rose-700 bg-rose-50 font-bold'
                            : 'text-emerald-700 bg-emerald-50 font-bold'
                        }`}
                      >
                        {diff >= 0 ? `+${diff.toFixed(2)}` : diff.toFixed(2)}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      <div className="mt-4 pt-3 border-t border-slate-100 text-[11px] text-slate-400">
        İl ismine tıklayarak o ilin detaylı profiline geçiş yapabilirsiniz.
      </div>
    </div>
  );
};
