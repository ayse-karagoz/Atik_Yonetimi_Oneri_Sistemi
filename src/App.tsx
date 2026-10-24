import React, { useState, useMemo } from 'react';
import { rawDatasets, AVAILABLE_YEARS, recommendations, projections } from './data/datasets';
import { ModelOptions } from './types';
import { runModelAnalysis } from './utils/modelEngine';
import { Sidebar } from './components/Sidebar';
import { ProvinceCards } from './components/ProvinceCards';
import { DominantFactorsCallout } from './components/DominantFactorsCallout';
import { ProjectionsSection } from './components/ProjectionsSection';
import { RecommendationsSection } from './components/RecommendationsSection';
import { ContributionChart } from './components/ContributionChart';
import { ComparisonTable } from './components/ComparisonTable';
import { ContributionDetailTable } from './components/ContributionDetailTable';
import { NationalOverview } from './components/NationalOverview';
import { BarChart2, Map, ShieldCheck, Database, Sparkles } from 'lucide-react';

export const App: React.FC = () => {
  const [selectedYear, setSelectedYear] = useState<number>(2022);
  const [selectedProvince, setSelectedProvince] = useState<string>('Sivas');
  const [options, setOptions] = useState<ModelOptions>({
    modelType: 'ridge',
    ridgeAlpha: 1.0,
  });
  const [activeTab, setActiveTab] = useState<'profile' | 'national'>('profile');

  // Run statistical analysis dynamically for chosen year
  const dataset = rawDatasets[selectedYear] || rawDatasets[2022];
  const analysis = useMemo(() => {
    return runModelAnalysis(dataset, options);
  }, [dataset, options]);

  // Current province analysis
  const currentProvince =
    analysis.provinces[selectedProvince] ||
    analysis.provinces[analysis.provinceList[0]];

  const similarProvince = analysis.provinces[currentProvince.nearestProvince];
  const oppositeProvince = analysis.provinces[currentProvince.oppositeProvince];

  // Historical values across 2020, 2022, 2024 for selected province
  const historicalValues = useMemo(() => {
    const vals: { 2020: number; 2022: number; 2024: number } = {
      2020: 0,
      2022: 0,
      2024: 0,
    };
    [2020, 2022, 2024].forEach((yr) => {
      const ds = rawDatasets[yr];
      if (ds) {
        const idx = ds.provinces.indexOf(selectedProvince);
        if (idx !== -1) {
          vals[yr as 2020 | 2022 | 2024] = ds.y[idx];
        }
      }
    });
    return vals;
  }, [selectedProvince]);

  const currentProjection = projections[selectedProvince];

  const comparisonData = [
    {
      role: 'Seçilen' as const,
      name: currentProvince.name,
      wastePerCapita: currentProvince.wastePerCapita,
      diffFromNationalAvg: currentProvince.wastePerCapita - analysis.nationalAverage,
    },
    {
      role: 'Benzer' as const,
      name: similarProvince.name,
      wastePerCapita: similarProvince.wastePerCapita,
      diffFromNationalAvg: similarProvince.wastePerCapita - analysis.nationalAverage,
      distance: currentProvince.nearestDistance,
    },
    {
      role: 'Zıt' as const,
      name: oppositeProvince.name,
      wastePerCapita: oppositeProvince.wastePerCapita,
      diffFromNationalAvg: oppositeProvince.wastePerCapita - analysis.nationalAverage,
      distance: currentProvince.oppositeDistance,
    },
  ];

  return (
    <div className="min-h-screen flex flex-col lg:flex-row bg-[#fbfdfc]">
      {/* Sidebar Controls */}
      <Sidebar
        provinces={analysis.provinceList}
        selectedProvince={selectedProvince}
        onSelectProvince={setSelectedProvince}
        selectedYear={selectedYear}
        onSelectYear={setSelectedYear}
        options={options}
        onOptionsChange={setOptions}
        metrics={analysis.metrics}
      />

      {/* Main Content Area */}
      <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-[1200px] mx-auto w-full">
        {/* Top Header */}
        <header className="mb-6 pb-4 border-b border-slate-200">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2">
                <span className="text-2xl" role="img" aria-label="recycle">
                  ♻️
                </span>
                <h1 className="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight">
                  İl Atık Profili ve Öneri Sistemi
                </h1>
                <span className="bg-emerald-100 text-emerald-800 text-xs font-bold px-2 py-0.5 rounded-full">
                  {selectedYear}
                </span>
              </div>
              <p className="text-sm text-slate-600 mt-1">
                Katkı analizi gerçek {selectedYear} açıklayıcı verisiyle hesaplanır.
                Geçmiş kişi başı atık değerleri ve senaryo projeksiyonları ayrıca sunulur.
              </p>
            </div>

            {/* Navigation Tabs */}
            <div className="flex items-center bg-slate-100 p-1 rounded-xl self-start sm:self-auto border border-slate-200">
              <button
                type="button"
                onClick={() => setActiveTab('profile')}
                className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all ${
                  activeTab === 'profile'
                    ? 'bg-white text-slate-900 shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                <Map className="w-3.5 h-3.5 text-emerald-600" />
                İl Profili: {selectedProvince}
              </button>
              <button
                type="button"
                onClick={() => setActiveTab('national')}
                className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all ${
                  activeTab === 'national'
                    ? 'bg-white text-slate-900 shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                <BarChart2 className="w-3.5 h-3.5 text-emerald-600" />
                Türkiye Geneli & Model Özeti
              </button>
            </div>
          </div>
        </header>

        {activeTab === 'profile' ? (
          <div className="space-y-6">
            {/* 3 Top Cards: Seçilen İl, Benzer İl, Zıt İl */}
            <section aria-label="İl Karşılaştırma Kartları">
              <ProvinceCards
                currentProvince={currentProvince}
                similarProvince={similarProvince}
                oppositeProvince={oppositeProvince}
                nationalAverage={analysis.nationalAverage}
                selectedYear={selectedYear}
                onSelectProvince={setSelectedProvince}
              />
            </section>

            {/* Dominant Factors Callout with exact template */}
            <section aria-label="Baskın Faktörler">
              <DominantFactorsCallout
                provinceName={currentProvince.name}
                waste={currentProvince.wastePerCapita}
                nationalAvg={analysis.nationalAverage}
                dominantFactors={currentProvince.dominantFactors}
                weightsClose={currentProvince.weightsClose}
              />
            </section>

            {/* Past Values (2020, 2022, 2024) and 2027 Projections */}
            <section aria-label="Geçmiş Değerler ve 2027 Projeksiyonu">
              <ProjectionsSection
                provinceName={currentProvince.name}
                historicalValues={historicalValues}
                projection={currentProjection}
              />
            </section>

            {/* Related Application Examples / Interventions (Öneri Sistemi) */}
            <section aria-label="İlişkili Uygulama Örnekleri">
              <RecommendationsSection
                dominantFactors={currentProvince.dominantFactors}
                recommendations={recommendations}
              />
            </section>

            {/* Two Column Grid: Horizontal Bar Chart & Comparison Table */}
            <section
              aria-label="İlişkili Faktörler ve Karşılaştırma Tablosu"
              className="grid grid-cols-1 lg:grid-cols-12 gap-6"
            >
              <div className="lg:col-span-7">
                <ContributionChart contributions={currentProvince.contributions} />
              </div>
              <div className="lg:col-span-5">
                <ComparisonTable
                  data={comparisonData}
                  onSelectProvince={setSelectedProvince}
                />
              </div>
            </section>

            {/* Detailed Table */}
            <section aria-label="Katkı Ayrıntısı">
              <ContributionDetailTable
                provinceName={currentProvince.name}
                contributions={currentProvince.contributions}
              />
            </section>
          </div>
        ) : (
          <section aria-label="Türkiye Geneli ve Model Özeti">
            <NationalOverview
              analysis={analysis}
              onSelectProvince={(il) => {
                setSelectedProvince(il);
                setActiveTab('profile');
              }}
              selectedProvince={selectedProvince}
            />
          </section>
        )}

        {/* Footer */}
        <footer className="mt-12 pt-6 border-t border-slate-200 text-xs text-slate-400 flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
            <span>T.C. Çevre, Şehircilik ve İklim Değişikliği & TÜİK Resmi İstatistikleri</span>
          </div>
          <div className="flex items-center gap-4">
            <span className="flex items-center gap-1">
              <Database className="w-3.5 h-3.5" />
              81 İl & 8 Açıklayıcı Değişken
            </span>
            <span>&bull;</span>
            <span>Atık Yönetimi Öneri Sistemi</span>
          </div>
        </footer>
      </main>
    </div>
  );
};
