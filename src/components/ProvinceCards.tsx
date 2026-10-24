import React from 'react';
import { ProvinceAnalysis } from '../types';
import { ArrowUpRight, ArrowDownRight, Compass, Sparkles, AlertCircle } from 'lucide-react';

interface ProvinceCardsProps {
  currentProvince: ProvinceAnalysis;
  similarProvince: ProvinceAnalysis;
  oppositeProvince: ProvinceAnalysis;
  nationalAverage: number;
  selectedYear: number;
  onSelectProvince: (name: string) => void;
}

interface SingleCardProps {
  title: string;
  roleType: 'selected' | 'similar' | 'opposite';
  provinceName: string;
  waste: number;
  nationalAvg: number;
  distance?: number;
  selectedYear: number;
  onClickProvince?: () => void;
}

const SingleCard: React.FC<SingleCardProps> = ({
  title,
  roleType,
  provinceName,
  waste,
  nationalAvg,
  distance,
  selectedYear,
  onClickProvince,
}) => {
  const diff = waste - nationalAvg;
  const isPositive = diff >= 0;

  const roleStyles = {
    selected: {
      badge: 'bg-emerald-600 text-white',
      border: 'border-emerald-200 ring-1 ring-emerald-500/20',
      icon: <Sparkles className="w-3.5 h-3.5" />,
    },
    similar: {
      badge: 'bg-teal-600 text-white',
      border: 'border-teal-200',
      icon: <Compass className="w-3.5 h-3.5" />,
    },
    opposite: {
      badge: 'bg-amber-600 text-white',
      border: 'border-amber-200',
      icon: <AlertCircle className="w-3.5 h-3.5" />,
    },
  }[roleType];

  return (
    <div
      className={`metric-card flex flex-col justify-between transition-all relative overflow-hidden ${roleStyles.border}`}
    >
      <div>
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
            {title}
          </span>
          <span
            className={`text-[11px] font-semibold px-2 py-0.5 rounded-full flex items-center gap-1 ${roleStyles.badge}`}
          >
            {roleStyles.icon}
            {roleType === 'selected' ? 'Mevcut' : roleType === 'similar' ? 'En Benzer' : 'En Farklı'}
          </span>
        </div>

        <div className="flex items-baseline justify-between mt-1">
          <h3
            onClick={onClickProvince}
            className={`text-2xl font-black text-slate-800 ${
              onClickProvince ? 'cursor-pointer hover:text-emerald-700 hover:underline' : ''
            }`}
            title={onClickProvince ? `${provinceName} profilini görüntüle` : undefined}
          >
            {provinceName}
          </h3>
          {onClickProvince && (
            <button
              type="button"
              onClick={onClickProvince}
              className="text-xs text-emerald-700 hover:text-emerald-900 font-semibold"
            >
              Görüntüle &rarr;
            </button>
          )}
        </div>

        <div className="mt-4 pt-3 border-t border-slate-200/80">
          <span className="text-xs text-slate-500 block">Kişi başı toplanan atık</span>
          <div className="flex items-baseline gap-2 mt-0.5">
            <span className="text-3xl font-extrabold text-slate-900 font-mono tracking-tight">
              {waste.toFixed(2)}
            </span>
            <span className="text-xs font-semibold text-slate-500">kg/gün</span>
          </div>

          <div className="flex items-center gap-1.5 mt-2">
            <span
              className={`inline-flex items-center text-xs font-bold px-2 py-0.5 rounded ${
                isPositive
                  ? 'bg-rose-100 text-rose-800'
                  : 'bg-emerald-100 text-emerald-800'
              }`}
            >
              {isPositive ? (
                <ArrowUpRight className="w-3.5 h-3.5 mr-0.5" />
              ) : (
                <ArrowDownRight className="w-3.5 h-3.5 mr-0.5" />
              )}
              Ulusal ortalamadan {diff >= 0 ? `+${diff.toFixed(2)}` : diff.toFixed(2)}
            </span>
          </div>
        </div>
      </div>

      <div className="mt-4 pt-2 border-t border-slate-200/60 text-xs text-slate-500">
        {distance === undefined ? (
          <span>Seçilen ilin gerçek {selectedYear} değeri</span>
        ) : (
          <span>
            Standartlaştırılmış Öklid mesafesi:{' '}
            <strong className="font-mono text-slate-700">{distance.toFixed(2)}</strong>
          </span>
        )}
      </div>
    </div>
  );
};

export const ProvinceCards: React.FC<ProvinceCardsProps> = ({
  currentProvince,
  similarProvince,
  oppositeProvince,
  nationalAverage,
  selectedYear,
  onSelectProvince,
}) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      <SingleCard
        title="Seçilen il"
        roleType="selected"
        provinceName={currentProvince.name}
        waste={currentProvince.wastePerCapita}
        nationalAvg={nationalAverage}
        selectedYear={selectedYear}
      />
      <SingleCard
        title="Benzer il"
        roleType="similar"
        provinceName={similarProvince.name}
        waste={similarProvince.wastePerCapita}
        nationalAvg={nationalAverage}
        distance={currentProvince.nearestDistance}
        selectedYear={selectedYear}
        onClickProvince={() => onSelectProvince(similarProvince.name)}
      />
      <SingleCard
        title="Zıt il"
        roleType="opposite"
        provinceName={oppositeProvince.name}
        waste={oppositeProvince.wastePerCapita}
        nationalAvg={nationalAverage}
        distance={currentProvince.oppositeDistance}
        selectedYear={selectedYear}
        onClickProvince={() => onSelectProvince(oppositeProvince.name)}
      />
    </div>
  );
};
