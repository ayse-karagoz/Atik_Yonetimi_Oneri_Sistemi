import React from 'react';
import { ModelOptions, ModelMetrics } from '../types';
import { AVAILABLE_YEARS } from '../data/datasets';
import { SlidersHorizontal, MapPin, Calendar, Info, RotateCcw } from 'lucide-react';

interface SidebarProps {
  provinces: string[];
  selectedProvince: string;
  onSelectProvince: (province: string) => void;
  selectedYear: number;
  onSelectYear: (year: number) => void;
  options: ModelOptions;
  onOptionsChange: (newOptions: ModelOptions) => void;
  metrics: ModelMetrics;
}

export const Sidebar: React.FC<SidebarProps> = ({
  provinces,
  selectedProvince,
  onSelectProvince,
  selectedYear,
  onSelectYear,
  options,
  onOptionsChange,
  metrics,
}) => {
  return (
    <aside className="w-full lg:w-80 bg-white border-r border-slate-200 p-6 flex flex-col gap-6 shrink-0 shadow-sm">
      <div className="flex items-center gap-2 pb-4 border-b border-slate-100">
        <div className="w-10 h-10 rounded-xl bg-emerald-100 text-emerald-800 flex items-center justify-center text-xl font-bold">
          ♻️
        </div>
        <div>
          <h2 className="text-lg font-bold text-slate-800">Seçim & Parametreler</h2>
          <p className="text-xs text-slate-500">İl Atık Profili ve Katkı Analizi</p>
        </div>
      </div>

      {/* Year Selection */}
      <div className="flex flex-col gap-2">
        <label className="text-xs font-semibold text-slate-600 uppercase tracking-wider flex items-center gap-1.5">
          <Calendar className="w-3.5 h-3.5 text-emerald-600" />
          Veri Yılı
        </label>
        <div className="grid grid-cols-3 gap-2">
          {AVAILABLE_YEARS.map((yr) => (
            <button
              key={yr}
              type="button"
              onClick={() => onSelectYear(yr)}
              className={`py-2 px-3 text-sm font-semibold rounded-lg border transition-all ${
                selectedYear === yr
                  ? 'bg-emerald-700 text-white border-emerald-700 shadow-sm'
                  : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100'
              }`}
            >
              {yr}
            </button>
          ))}
        </div>
      </div>

      {/* Province Selection */}
      <div className="flex flex-col gap-2">
        <label
          htmlFor="province-select"
          className="text-xs font-semibold text-slate-600 uppercase tracking-wider flex items-center gap-1.5"
        >
          <MapPin className="w-3.5 h-3.5 text-emerald-600" />
          İl Seçimi
        </label>
        <div className="relative">
          <select
            id="province-select"
            value={selectedProvince}
            onChange={(e) => onSelectProvince(e.target.value)}
            className="w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2.5 text-slate-800 font-medium text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
          >
            {provinces.map((il) => (
              <option key={il} value={il}>
                {il}
              </option>
            ))}
          </select>
        </div>

        {/* Quick select buttons */}
        <div className="flex flex-wrap gap-1.5 mt-1">
          {['Sivas', 'İstanbul', 'Ankara', 'İzmir', 'Antalya', 'Diyarbakır'].map((city) => (
            <button
              key={city}
              type="button"
              onClick={() => onSelectProvince(city)}
              className={`text-xs px-2.5 py-1 rounded-md border transition-colors ${
                selectedProvince === city
                  ? 'bg-emerald-100 text-emerald-800 border-emerald-300 font-semibold'
                  : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
              }`}
            >
              {city}
            </button>
          ))}
        </div>
      </div>

      {/* Model Options */}
      <div className="flex flex-col gap-3 pt-4 border-t border-slate-100">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-slate-600 uppercase tracking-wider flex items-center gap-1.5">
            <SlidersHorizontal className="w-3.5 h-3.5 text-emerald-600" />
            Model Türü
          </span>
          <button
            type="button"
            title="Varsayılanlara dön"
            onClick={() => onOptionsChange({ modelType: 'ridge', ridgeAlpha: 1.0 })}
            className="text-xs text-slate-400 hover:text-slate-600 flex items-center gap-1"
          >
            <RotateCcw className="w-3 h-3" />
            Sıfırla
          </button>
        </div>

        <div className="grid grid-cols-2 gap-2">
          <button
            type="button"
            onClick={() => onOptionsChange({ ...options, modelType: 'ridge' })}
            className={`py-2 px-3 text-xs font-medium rounded-lg border text-center transition-all ${
              options.modelType === 'ridge'
                ? 'bg-emerald-50 border-emerald-500 text-emerald-900 font-semibold shadow-xs'
                : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50'
            }`}
          >
            Ridge Regresyon
          </button>
          <button
            type="button"
            onClick={() => onOptionsChange({ ...options, modelType: 'linear' })}
            className={`py-2 px-3 text-xs font-medium rounded-lg border text-center transition-all ${
              options.modelType === 'linear'
                ? 'bg-emerald-50 border-emerald-500 text-emerald-900 font-semibold shadow-xs'
                : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50'
            }`}
          >
            Doğrusal (Linear)
          </button>
        </div>

        {options.modelType === 'ridge' && (
          <div className="flex flex-col gap-1.5 bg-slate-50 p-3 rounded-lg border border-slate-200">
            <div className="flex justify-between items-center text-xs">
              <span className="text-slate-600 font-medium">Ridge Alpha (&alpha;):</span>
              <span className="font-mono font-bold text-emerald-700 bg-emerald-100/70 px-2 py-0.5 rounded">
                {options.ridgeAlpha.toFixed(1)}
              </span>
            </div>
            <input
              type="range"
              min="0.1"
              max="10.0"
              step="0.1"
              value={options.ridgeAlpha}
              onChange={(e) =>
                onOptionsChange({
                  ...options,
                  ridgeAlpha: parseFloat(e.target.value),
                })
              }
              className="w-full accent-emerald-600 cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-slate-400">
              <span>0.1 (Hassas)</span>
              <span>1.0 (Standart)</span>
              <span>10.0 (Düzgünleştirilmiş)</span>
            </div>
          </div>
        )}
      </div>

      {/* Model Captions */}
      <div className="flex flex-col gap-3 p-3.5 bg-[#f4f8f6] rounded-xl border border-[#e2ede8] text-xs text-slate-600">
        <div className="flex items-start gap-2">
          <Info className="w-4 h-4 text-emerald-700 shrink-0 mt-0.5" />
          <p className="leading-relaxed">
            Mesafeler, modelde kullanılan sekiz açıklayıcı değişken standartlaştırıldıktan sonra hesaplanır.
          </p>
        </div>
        <div className="pt-2 border-t border-[#d8e6df] font-medium text-slate-700">
          Ridge eğitim R²:{' '}
          <span className="font-bold font-mono text-emerald-800">
            {metrics.trainR2.toFixed(3)}
          </span>
          . Bu değer tahmin performansı iddiası değildir.
        </div>
      </div>

      <div className="text-[11px] text-slate-400 mt-auto leading-relaxed border-t border-slate-100 pt-4">
        Kaynak: TÜİK Belediye Atık İstatistikleri & Kültür ve Turizm Bakanlığı Konaklama Verileri.
      </div>
    </aside>
  );
};
