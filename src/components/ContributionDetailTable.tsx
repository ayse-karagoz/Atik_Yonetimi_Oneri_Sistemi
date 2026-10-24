import React, { useState } from 'react';
import { VariableContribution } from '../types';
import { ChevronDown, ChevronUp, Eye, EyeOff } from 'lucide-react';

interface ContributionDetailTableProps {
  provinceName: string;
  contributions: VariableContribution[];
}

export const ContributionDetailTable: React.FC<ContributionDetailTableProps> = ({
  provinceName,
  contributions,
}) => {
  const [showAdvanced, setShowAdvanced] = useState(false);

  return (
    <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-3">
        <div>
          <h3 className="text-base font-bold text-slate-800">
            {provinceName} için katkı ayrıntısı
          </h3>
          <p className="text-xs text-slate-500">
            Sekiz açıklayıcı değişkenin model tahminindeki bağıl ağırlıkları
          </p>
        </div>

        <button
          type="button"
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="self-start sm:self-auto text-xs font-medium text-emerald-800 hover:text-emerald-950 bg-emerald-50 px-2.5 py-1.5 rounded-lg border border-emerald-200 flex items-center gap-1.5 transition-colors"
        >
          {showAdvanced ? (
            <>
              <EyeOff className="w-3.5 h-3.5" />
              Basit Görünüm
            </>
          ) : (
            <>
              <Eye className="w-3.5 h-3.5" />
              Ham Değerleri & Z-Skorları Göster
            </>
          )}
        </button>
      </div>

      <div className="overflow-x-auto border border-slate-200 rounded-lg">
        <table className="w-full text-left text-xs">
          <thead className="table-header border-b border-slate-200">
            <tr>
              <th className="py-2.5 px-3">Değişken</th>
              <th className="py-2.5 px-3">Etki yönü</th>
              {showAdvanced && (
                <>
                  <th className="py-2.5 px-3 text-right">Ham Değer</th>
                  <th className="py-2.5 px-3 text-right">Z-Skor</th>
                  <th className="py-2.5 px-3 text-right">Standart Katsayı</th>
                </>
              )}
              <th className="py-2.5 px-3 text-right">Katkı (standartlaştırılmış birim)</th>
              <th className="py-2.5 px-3 text-right">Göreli katkı payı (%)</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {contributions.map((row) => {
              const isPositive = row.contribution >= 0;

              return (
                <tr key={row.variable} className="hover:bg-slate-50/70 transition-colors">
                  <td className="py-3 px-3 font-semibold text-slate-800">
                    {row.variable}
                  </td>
                  <td className="py-3 px-3">
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold ${
                        isPositive
                          ? 'bg-emerald-100 text-emerald-800'
                          : 'bg-rose-100 text-rose-800'
                      }`}
                    >
                      {row.direction}
                    </span>
                  </td>
                  {showAdvanced && (
                    <>
                      <td className="py-3 px-3 text-right font-mono text-slate-600">
                        {row.rawValue.toLocaleString('tr-TR', { maximumFractionDigits: 2 })}
                      </td>
                      <td className="py-3 px-3 text-right font-mono text-slate-600">
                        {row.standardizedValue >= 0
                          ? `+${row.standardizedValue.toFixed(3)}`
                          : row.standardizedValue.toFixed(3)}
                      </td>
                      <td className="py-3 px-3 text-right font-mono text-slate-600">
                        {row.coefficient >= 0
                          ? `+${row.coefficient.toFixed(3)}`
                          : row.coefficient.toFixed(3)}
                      </td>
                    </>
                  )}
                  <td className="py-3 px-3 text-right font-mono font-bold">
                    <span
                      className={isPositive ? 'text-emerald-700' : 'text-rose-700'}
                    >
                      {row.contribution >= 0
                        ? `+${row.contribution.toFixed(3)}`
                        : row.contribution.toFixed(3)}
                    </span>
                  </td>
                  <td className="py-3 px-3 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <div className="w-16 bg-slate-100 h-2 rounded-full overflow-hidden hidden sm:block">
                        <div
                          className="bg-emerald-600 h-full rounded-full"
                          style={{ width: `${Math.min(100, row.relativeSharePct)}%` }}
                        />
                      </div>
                      <span className="font-mono font-bold text-slate-800">
                        {row.relativeSharePct.toFixed(1)}%
                      </span>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="mt-3 text-xs text-slate-500 italic">
        Model, tahmin yapmak için değil, gerçek atık değerinin hangi değişkenlerle ilişkili olduğunu görünür kılmak için kullanılır.
      </div>
    </div>
  );
};
