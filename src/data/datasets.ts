import rawDataJson from './raw_data.json';
import recommendationsJson from './recommendations.json';
import projectionsJson from './projections.json';
import { RawDatasetYear, RecommendationRecord, ProvinceProjection } from '../types';

export const rawDatasets: Record<number, RawDatasetYear> = rawDataJson as unknown as Record<
  number,
  RawDatasetYear
>;

export const recommendations: RecommendationRecord[] = recommendationsJson as unknown as RecommendationRecord[];

export const projections: Record<string, ProvinceProjection> = projectionsJson as unknown as Record<
  string,
  ProvinceProjection
>;

export const AVAILABLE_YEARS: number[] = [2022, 2024, 2020];

export const ONERI_ATAMALARI: Record<string, string> = {
  'Konaklama doluluk oranı': 'Yüksek konaklama doluluk oranı',
  'Konaklama tesise geliş sayısı': 'Yüksek konaklama tesise geliş sayısı',
  'Toplam nüfus': 'Yüksek toplam nüfus / yoğun kent bağlamı',
  'Konaklama ortalama kalış süresi': 'Yüksek ortalama kalış süresi',
  'Ortalama hanehalkı büyüklüğü': 'Küçük hane büyüklüğü',
};
