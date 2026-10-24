import React, { useState } from 'react';
import { RecommendationRecord } from '../types';
import { ONERI_ATAMALARI } from '../data/datasets';
import { ChevronDown, ChevronUp, ExternalLink, Lightbulb, ShieldAlert, CheckCircle } from 'lucide-react';

interface RecommendationsSectionProps {
  dominantFactors: [string, string, string];
  recommendations: RecommendationRecord[];
}

export const RecommendationsSection: React.FC<RecommendationsSectionProps> = ({
  dominantFactors,
  recommendations,
}) => {
  const [openItems, setOpenItems] = useState<Record<string, boolean>>({
    'item-0': true, // open first item by default
  });

  const toggleItem = (id: string) => {
    setOpenItems((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  // Find recommendations matching dominant factors
  const matchedItems: {
    factor: string;
    key: string;
    rec: RecommendationRecord;
  }[] = [];

  dominantFactors.forEach((factor, fIdx) => {
    const targetYon = ONERI_ATAMALARI[factor];
    if (!targetYon) return;

    const matchedRecs = recommendations.filter((r) =>
      r.yön.toLowerCase().startsWith(targetYon.toLowerCase())
    );

    matchedRecs.forEach((rec, rIdx) => {
      matchedItems.push({
        factor,
        key: `${factor}-${rIdx}`,
        rec,
      });
    });
  });

  return (
    <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-4">
      <div>
        <div className="flex items-center gap-2">
          <Lightbulb className="w-5 h-5 text-emerald-700" />
          <h3 className="text-base font-bold text-slate-800">
            İlişkili Uygulama Örnekleri (Öneri Sistemi)
          </h3>
        </div>
        <p className="text-xs text-slate-500 mt-1">
          Örnekler, seçili ilde en yüksek katkıya sahip değişkenlerle eşleştirilir. Bu eşleştirme etki kanıtı değildir.
        </p>
      </div>

      {matchedItems.length === 0 ? (
        <div className="p-4 bg-slate-50 text-slate-500 text-xs rounded-lg border border-slate-200">
          Bu değişkenler için taranan literatürde doğrudan uygulama örneği bulunamadı.
        </div>
      ) : (
        <div className="space-y-3">
          {matchedItems.map(({ factor, key, rec }, idx) => {
            const isOpen = !!openItems[key];
            const hasEvidence = rec['örnek yer ve yıl'] !== 'kanıt bulunamadı';

            return (
              <div
                key={key}
                className="border border-slate-200 rounded-lg overflow-hidden transition-all"
              >
                <button
                  type="button"
                  onClick={() => toggleItem(key)}
                  className="w-full text-left p-3.5 bg-slate-50/80 hover:bg-slate-100 flex items-center justify-between gap-3 transition-colors"
                >
                  <div className="flex items-center gap-2.5">
                    <span className="text-xs font-semibold px-2 py-0.5 rounded bg-emerald-100 text-emerald-800">
                      {factor}
                    </span>
                    <span className="text-xs sm:text-sm font-bold text-slate-800">
                      {rec['örnek yer ve yıl']}
                    </span>
                  </div>
                  <div className="text-slate-400">
                    {isOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                  </div>
                </button>

                {isOpen && (
                  <div className="p-4 bg-white space-y-3 text-xs leading-relaxed border-t border-slate-100">
                    {!hasEvidence ? (
                      <p className="text-slate-500 italic">Kanıt bulunamadı.</p>
                    ) : (
                      <>
                        <div>
                          <strong className="text-slate-800 block mb-0.5">Ne yapıldı:</strong>
                          <p className="text-slate-600 bg-slate-50 p-2.5 rounded border border-slate-100">
                            {rec['ne yapıldı']}
                          </p>
                        </div>

                        <div>
                          <strong className="text-slate-800 block mb-0.5">Raporlanan sonuç:</strong>
                          <p className="text-emerald-900 bg-emerald-50/60 p-2.5 rounded border border-emerald-100 font-medium">
                            {rec['raporlanan sonuç']}
                          </p>
                        </div>

                        {rec['kaynak bağlantısı'] && (
                          <div className="flex items-center gap-1.5 pt-1">
                            <span className="text-slate-500">Kaynak:</span>
                            <a
                              href={rec['kaynak bağlantısı']}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-emerald-700 hover:text-emerald-900 font-medium underline inline-flex items-center gap-1"
                            >
                              {rec['kaynak türü']}
                              <ExternalLink className="w-3 h-3" />
                            </a>
                          </div>
                        )}

                        <div className="bg-amber-50/70 border border-amber-200/80 p-2.5 rounded text-amber-900 text-[11px] space-y-1">
                          <div className="flex items-start gap-1.5">
                            <ShieldAlert className="w-3.5 h-3.5 text-amber-700 shrink-0 mt-0.5" />
                            <p>{rec['öneri uyarısı']}</p>
                          </div>
                          {rec['Türkiye için bilinen engeller'] && (
                            <p className="pt-1 border-t border-amber-200/60 text-slate-600">
                              <strong className="text-amber-950">Türkiye için bilinen engeller: </strong>
                              {rec['Türkiye için bilinen engeller']}
                            </p>
                          )}
                        </div>
                      </>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
