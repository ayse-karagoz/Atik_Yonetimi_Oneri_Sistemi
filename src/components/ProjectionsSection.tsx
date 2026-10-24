import React from 'react';
import { ProvinceProjection } from '../types';
import { AlertTriangle, TrendingUp, Calendar, Info } from 'lucide-react';

interface ProjectionsSectionProps {
  provinceName: string;
  historicalValues: {
    2020: number;
    2022: number;
    2024: number;
  };
  projection?: ProvinceProjection;
}

export const ProjectionsSection: React.FC<ProjectionsSectionProps> = ({
  provinceName,
  historicalValues,
  projection,
}) => {
  if (!projection) {
    return null;
  }

  const scenarios = [
    {
      name: 'Düşük',
      value: projection.dusuk_senaryo,
      range80: `${projection.aralik_80_alt.toFixed(2)}–${projection.aralik_80_ust.toFixed(2)}`,
      range95: `${projection.aralik_95_alt.toFixed(2)}–${projection.aralik_95_ust.toFixed(2)}`,
    },
    {
      name: 'Baz',
      value: projection.baz_senaryo,
      range80: `${projection.aralik_80_alt.toFixed(2)}–${projection.aralik_80_ust.toFixed(2)}`,
      range95: `${projection.aralik_95_alt.toFixed(2)}–${projection.aralik_95_ust.toFixed(2)}`,
    },
    {
      name: 'Yüksek',
      value: projection.yuksek_senaryo,
      range80: `${projection.aralik_80_alt.toFixed(2)}–${projection.aralik_80_ust.toFixed(2)}`,
      range95: `${projection.aralik_95_alt.toFixed(2)}–${projection.aralik_95_ust.toFixed(2)}`,
    },
  ];

  return (
    <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-4">
      <div className="flex items-center justify-between pb-2 border-b border-slate-100">
        <div>
          <h3 className="text-base font-bold text-slate-800">
            {provinceName} için geçmiş değerler ve 2027 projeksiyonu
          </h3>
          <p className="text-xs text-slate-500">
            2020–2024 gerçekleşen gözlemler ve senaryo bazlı 3 yıllık ufuk projeksiyonu
          </p>
        </div>
        <span className="text-xs font-mono px-2 py-0.5 rounded bg-amber-50 text-amber-800 border border-amber-200 font-semibold">
          {projection.guvenilirlik} gösterge
        </span>
      </div>

      {/* 4 Metric Columns */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
          <span className="text-xs text-slate-500 font-medium flex items-center gap-1">
            <Calendar className="w-3 h-3 text-slate-400" />
            2020 gözlenen
          </span>
          <div className="text-lg font-mono font-bold text-slate-800 mt-1">
            {historicalValues[2020] !== undefined
              ? `${historicalValues[2020].toFixed(2)} kg/kişi-gün`
              : '–'}
          </div>
        </div>

        <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
          <span className="text-xs text-slate-500 font-medium flex items-center gap-1">
            <Calendar className="w-3 h-3 text-slate-400" />
            2022 gözlenen
          </span>
          <div className="text-lg font-mono font-bold text-slate-800 mt-1">
            {historicalValues[2022] !== undefined
              ? `${historicalValues[2022].toFixed(2)} kg/kişi-gün`
              : '–'}
          </div>
        </div>

        <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
          <span className="text-xs text-slate-500 font-medium flex items-center gap-1">
            <Calendar className="w-3 h-3 text-slate-400" />
            2024 gözlenen
          </span>
          <div className="text-lg font-mono font-bold text-slate-800 mt-1">
            {historicalValues[2024] !== undefined
              ? `${historicalValues[2024].toFixed(2)} kg/kişi-gün`
              : '–'}
          </div>
        </div>

        <div className="p-3 bg-amber-50/70 border border-amber-200 rounded-lg">
          <span className="text-xs text-amber-800 font-semibold flex items-center gap-1">
            <TrendingUp className="w-3 h-3 text-amber-700" />
            2027 baz senaryo
          </span>
          <div className="text-lg font-mono font-black text-amber-950 mt-1">
            {projection.baz_senaryo.toFixed(2)} kg/kişi-gün
          </div>
        </div>
      </div>

      {/* Warning Alert */}
      <div className="bg-amber-50 border border-amber-300 text-amber-900 p-3 rounded-lg flex items-start gap-2.5 text-xs">
        <AlertTriangle className="w-4 h-4 text-amber-700 shrink-0 mt-0.5" />
        <div className="leading-relaxed">
          <strong>2027 sayıları güvenilmez göstergedir:</strong> Geriye dönük sınamada yöntem, son bilinen il değeri bazını geçemedi. Bu değer gerçek gözlem değildir.
        </div>
      </div>

      {/* Scenario Table */}
      <div className="overflow-x-auto border border-slate-200 rounded-lg">
        <table className="w-full text-left text-xs">
          <thead className="table-header border-b border-slate-200">
            <tr>
              <th className="py-2 px-3">Senaryo</th>
              <th className="py-2 px-3 text-right">2027 kişi başı atık (kg/kişi-gün)</th>
              <th className="py-2 px-3 text-center">%80 aralık</th>
              <th className="py-2 px-3 text-center">%95 aralık</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 font-mono">
            {scenarios.map((sc) => (
              <tr key={sc.name} className="hover:bg-slate-50/60 transition-colors">
                <td className="py-2.5 px-3 font-sans font-semibold text-slate-800">
                  {sc.name}
                </td>
                <td className="py-2.5 px-3 text-right font-bold text-slate-900">
                  {sc.value.toFixed(2)}
                </td>
                <td className="py-2.5 px-3 text-center text-slate-600">
                  {sc.range80}
                </td>
                <td className="py-2.5 px-3 text-center text-slate-600">
                  {sc.range95}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Captions and Methodology Notes */}
      <div className="text-[11px] text-slate-500 space-y-1 pt-1 border-t border-slate-100">
        <p>
          <strong>Yöntem:</strong> {projection.yontem}. <strong>Ufuk:</strong> {projection.ufuk_yil} yıl.{' '}
          <strong>Çıktı is_synthetic:</strong> {projection.is_synthetic ? 'Evet (Sentetik)' : 'Hayır'}.
        </p>
        <p>
          <strong>Gerekçe:</strong> {projection.neden}
        </p>
        <p className="italic text-slate-400">
          Yalnızca 3 veri noktası kullanıldı. Aralıklar gösterilir; bu bir tahmin değildir.
        </p>
      </div>
    </div>
  );
};
