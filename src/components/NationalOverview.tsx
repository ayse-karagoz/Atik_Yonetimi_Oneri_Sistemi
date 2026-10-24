import React, { useState } from 'react';
import { FullAnalysisResult } from '../types';
import { BarChart3, Search, TrendingUp, Layers, CheckCircle2 } from 'lucide-react';

interface NationalOverviewProps {
  analysis: FullAnalysisResult;
  onSelectProvince: (il: string) => void;
  selectedProvince: string;
}

export const NationalOverview: React.FC<NationalOverviewProps> = ({
  analysis,
  onSelectProvince,
  selectedProvince,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [sortField, setSortField] = useState<'waste' | 'pred' | 'diff' | 'abs'>('waste');
  const [sortAsc, setSortAsc] = useState(false);

  const filteredProvinces = analysis.provinceList
    .map((name) => analysis.provinces[name])
    .filter((p) => p && p.name.toLowerCase().includes(searchTerm.toLowerCase()));

  filteredProvinces.sort((a, b) => {
    let valA = 0;
    let valB = 0;
    if (sortField === 'waste') {
      valA = a.wastePerCapita;
      valB = b.wastePerCapita;
    } else if (sortField === 'pred') {
      valA = a.predictedWaste;
      valB = b.predictedWaste;
    } else if (sortField === 'diff') {
      valA = a.wastePerCapita - analysis.nationalAverage;
      valB = b.wastePerCapita - analysis.nationalAverage;
    } else if (sortField === 'abs') {
      valA = a.totalAbsContribution;
      valB = b.totalAbsContribution;
    }
    return sortAsc ? valA - valB : valB - valA;
  });

  const toggleSort = (field: 'waste' | 'pred' | 'diff' | 'abs') => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Global Feature Importance Card */}
      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-emerald-700" />
            <h3 className="text-base font-bold text-slate-800">
              Küresel Değişken Önemi ({analysis.year})
            </h3>
          </div>
          <span className="text-xs text-slate-500 font-mono">
            81 İl Ortalaması Mutlak Katkı
          </span>
        </div>
        <p className="text-xs text-slate-500 mb-4">
          Değişkenlerin Türkiye genelinde kişi başı atık miktarını açıklamada sağladığı ortalama katkı payları
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2.5">
            {analysis.globalFeatures.map((f, idx) => (
              <div key={f.variable} className="text-xs">
                <div className="flex justify-between items-center mb-1">
                  <span className="font-semibold text-slate-700">
                    <span className="text-slate-400 font-mono mr-1.5">{idx + 1}.</span>
                    {f.variable}
                  </span>
                  <div className="flex items-center gap-2 font-mono">
                    <span className="text-slate-500">
                      katsayı: {f.standardizedCoef >= 0 ? `+${f.standardizedCoef.toFixed(3)}` : f.standardizedCoef.toFixed(3)}
                    </span>
                    <span className="font-bold text-emerald-800 bg-emerald-50 px-1.5 py-0.5 rounded">
                      %{f.globalImportancePct.toFixed(1)}
                    </span>
                  </div>
                </div>
                <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-emerald-600 rounded-full transition-all duration-300"
                    style={{ width: `${f.globalImportancePct}%` }}
                  />
                </div>
              </div>
            ))}
          </div>

          {/* Model Metrics Summary */}
          <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 flex flex-col justify-between text-xs">
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5 mb-3">
                <Layers className="w-4 h-4 text-emerald-700" />
                Model & Veri Seti İstatistikleri
              </span>

              <div className="space-y-2 font-mono">
                <div className="flex justify-between pb-1.5 border-b border-slate-200">
                  <span className="text-slate-500">Model Türü:</span>
                  <span className="font-bold text-slate-800 uppercase">{analysis.metrics.modelType}</span>
                </div>
                {analysis.metrics.modelType === 'ridge' && (
                  <div className="flex justify-between pb-1.5 border-b border-slate-200">
                    <span className="text-slate-500">Ridge Alpha (&alpha;):</span>
                    <span className="font-bold text-slate-800">{analysis.metrics.ridgeAlpha}</span>
                  </div>
                )}
                <div className="flex justify-between pb-1.5 border-b border-slate-200">
                  <span className="text-slate-500">Gözlem Sayısı (İller):</span>
                  <span className="font-bold text-slate-800">{analysis.metrics.observationCount}</span>
                </div>
                <div className="flex justify-between pb-1.5 border-b border-slate-200">
                  <span className="text-slate-500">Özellik Sayısı:</span>
                  <span className="font-bold text-slate-800">{analysis.metrics.featureCount}</span>
                </div>
                <div className="flex justify-between pb-1.5 border-b border-slate-200">
                  <span className="text-slate-500">Eğitim R² Skoru:</span>
                  <span className="font-bold text-emerald-800 text-sm">
                    {analysis.metrics.trainR2.toFixed(3)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Türkiye Kişi Başı Ortalama:</span>
                  <span className="font-bold text-slate-800 text-sm">
                    {analysis.nationalAverage.toFixed(2)} kg/gün
                  </span>
                </div>
              </div>
            </div>

            <p className="mt-4 pt-3 border-t border-slate-200 text-[11px] text-slate-500 italic">
              {analysis.metrics.note}
            </p>
          </div>
        </div>
      </div>

      {/* 81 Provinces Full Table */}
      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
          <div>
            <h3 className="text-base font-bold text-slate-800">
              Türkiye İller Tablosu ({analysis.year})
            </h3>
            <p className="text-xs text-slate-500">
              81 ilin kişi başı atık miktarı, model kestirimi ve profil eşleşmeleri
            </p>
          </div>

          <div className="relative w-full sm:w-64">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="İl ara (örn. Sivas, Van)..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
            />
          </div>
        </div>

        <div className="overflow-x-auto border border-slate-200 rounded-lg max-h-96 overflow-y-auto">
          <table className="w-full text-left text-xs">
            <thead className="table-header sticky top-0 bg-slate-50 border-b border-slate-200 shadow-xs">
              <tr>
                <th className="py-2.5 px-3">İl</th>
                <th
                  onClick={() => toggleSort('waste')}
                  className="py-2.5 px-3 text-right cursor-pointer hover:bg-slate-100"
                >
                  Kişi Başı Atık {sortField === 'waste' ? (sortAsc ? '↑' : '↓') : ''}
                </th>
                <th
                  onClick={() => toggleSort('diff')}
                  className="py-2.5 px-3 text-right cursor-pointer hover:bg-slate-100"
                >
                  Ort. Fark {sortField === 'diff' ? (sortAsc ? '↑' : '↓') : ''}
                </th>
                <th
                  onClick={() => toggleSort('pred')}
                  className="py-2.5 px-3 text-right cursor-pointer hover:bg-slate-100"
                >
                  Model Tahmini {sortField === 'pred' ? (sortAsc ? '↑' : '↓') : ''}
                </th>
                <th className="py-2.5 px-3">En Benzer İl (Mesafe)</th>
                <th className="py-2.5 px-3">En Zıt İl (Mesafe)</th>
                <th className="py-2.5 px-3 text-center">İşlem</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-mono">
              {filteredProvinces.map((p) => {
                const isSelected = p.name === selectedProvince;
                const diff = p.wastePerCapita - analysis.nationalAverage;

                return (
                  <tr
                    key={p.name}
                    className={`transition-colors ${
                      isSelected ? 'bg-emerald-50/70 font-semibold' : 'hover:bg-slate-50/60'
                    }`}
                  >
                    <td className="py-2.5 px-3 font-sans font-semibold text-slate-800">
                      <div className="flex items-center gap-1.5">
                        {isSelected && <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />}
                        <span>{p.name}</span>
                      </div>
                    </td>
                    <td className="py-2.5 px-3 text-right font-bold text-slate-900">
                      {p.wastePerCapita.toFixed(2)}
                    </td>
                    <td className="py-2.5 px-3 text-right font-medium">
                      <span
                        className={`px-1.5 py-0.5 rounded text-[11px] ${
                          diff >= 0 ? 'text-rose-700 bg-rose-50' : 'text-emerald-700 bg-emerald-50'
                        }`}
                      >
                        {diff >= 0 ? `+${diff.toFixed(2)}` : diff.toFixed(2)}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-right text-slate-600">
                      {p.predictedWaste.toFixed(2)}
                    </td>
                    <td className="py-2.5 px-3 font-sans text-slate-700">
                      <span className="font-medium">{p.nearestProvince}</span>{' '}
                      <span className="text-slate-400 font-mono text-[11px]">
                        ({p.nearestDistance.toFixed(2)})
                      </span>
                    </td>
                    <td className="py-2.5 px-3 font-sans text-slate-700">
                      <span className="font-medium">{p.oppositeProvince}</span>{' '}
                      <span className="text-slate-400 font-mono text-[11px]">
                        ({p.oppositeDistance.toFixed(2)})
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-center font-sans">
                      <button
                        type="button"
                        onClick={() => onSelectProvince(p.name)}
                        className={`text-xs px-2.5 py-1 rounded transition-colors ${
                          isSelected
                            ? 'bg-emerald-600 text-white font-semibold'
                            : 'bg-slate-100 hover:bg-emerald-100 text-slate-700 hover:text-emerald-800'
                        }`}
                      >
                        {isSelected ? 'Seçili' : 'Profili Aç'}
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
