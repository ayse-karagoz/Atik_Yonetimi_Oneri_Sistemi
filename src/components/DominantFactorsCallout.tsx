import React from 'react';
import { Info, AlertTriangle } from 'lucide-react';

interface DominantFactorsCalloutProps {
  provinceName: string;
  waste: number;
  nationalAvg: number;
  dominantFactors: [string, string, string];
  weightsClose?: boolean;
}

export const DominantFactorsCallout: React.FC<DominantFactorsCalloutProps> = ({
  provinceName,
  waste,
  nationalAvg,
  dominantFactors,
  weightsClose,
}) => {
  const diff = waste - nationalAvg;
  const [v1, v2, v3] = dominantFactors;

  return (
    <div className="space-y-2">
      <div className="bg-sky-50/90 border border-sky-200 text-sky-950 p-4 rounded-xl flex items-start gap-3 shadow-xs">
        <div className="p-1 rounded-md bg-sky-100 text-sky-700 shrink-0 mt-0.5">
          <Info className="w-5 h-5" />
        </div>
        <div className="text-sm leading-relaxed">
          <p className="font-medium text-slate-800">
            <strong>{provinceName}</strong> için kişi başı atık{' '}
            <span className="font-mono font-bold text-sky-900">{waste.toFixed(2)}</span> kg/kişi-gün;{' '}
            ulusal ortalamadan{' '}
            <span className="font-mono font-bold text-sky-900">
              {diff >= 0 ? `+${diff.toFixed(2)}` : diff.toFixed(2)}
            </span>{' '}
            kg/kişi-gün. Farkla en ilişkili değişkenler:{' '}
            <strong className="text-sky-900 bg-sky-100/80 px-1 py-0.5 rounded">{v1}</strong>,{' '}
            <strong className="text-sky-900 bg-sky-100/80 px-1 py-0.5 rounded">{v2}</strong>,{' '}
            <strong className="text-sky-900 bg-sky-100/80 px-1 py-0.5 rounded">{v3}</strong>.
            {weightsClose && (
              <span className="ml-2 font-semibold text-sky-800">
                (Birkaç değişken benzer ağırlıkta.)
              </span>
            )}
          </p>

          <div className="mt-2 pt-2 border-t border-sky-200/60 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-500">
            <span>&bull; Bu bir ilişkidir. Bir değişkenin diğerini oluşturduğunu göstermez.</span>
            <span>&bull; {provinceName}, modelin eğitim verisindedir (sonuç eğitim verilerinden hesaplandı).</span>
            <span>&bull; Yalnızca belediye belgeli tesisler; turizm yoğun illerde kapsam eksik olabilir.</span>
          </div>
        </div>
      </div>
    </div>
  );
};
