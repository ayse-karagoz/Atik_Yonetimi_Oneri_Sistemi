export interface RawDatasetYear {
  year: number;
  provinces: string[];
  featureLabels: string[];
  X: number[][];
  y: number[];
}

export type ModelType = 'ridge' | 'linear';

export interface ModelOptions {
  modelType: ModelType;
  ridgeAlpha: number;
}

export interface VariableContribution {
  variable: string;
  rawValue: number;
  standardizedValue: number;
  coefficient: number;
  contribution: number; // standardized units: X_z * coef
  relativeSharePct: number; // |katki| / sum(|katki|) * 100
  direction: 'Pozitif' | 'Negatif';
}

export interface ProvinceComparison {
  role: 'Seçilen' | 'Benzer' | 'Zıt';
  name: string;
  wastePerCapita: number;
  diffFromNationalAvg: number;
  distance?: number;
}

export interface ProvinceAnalysis {
  name: string;
  wastePerCapita: number;
  predictedWaste: number;
  residual: number;
  totalAbsContribution: number;
  nearestProvince: string;
  nearestDistance: number;
  oppositeProvince: string;
  oppositeDistance: number;
  contributions: VariableContribution[];
  dominantFactors: [string, string, string]; // Top 3 dominant factors as updated
  weightsClose: boolean; // whether top 2 relative shares differ by < 5%
}

export interface GlobalFeatureSummary {
  variable: string;
  standardizedCoef: number;
  meanAbsContribution: number;
  globalImportancePct: number;
}

export interface ModelMetrics {
  modelType: ModelType;
  ridgeAlpha: number;
  observationCount: number;
  featureCount: number;
  trainR2: number;
  nationalAverage: number;
  note: string;
}

export interface FullAnalysisResult {
  year: number;
  metrics: ModelMetrics;
  provinces: Record<string, ProvinceAnalysis>;
  provinceList: string[];
  globalFeatures: GlobalFeatureSummary[];
  nationalAverage: number;
}

export interface RecommendationRecord {
  yön: string;
  'örnek yer ve yıl': string;
  'ne yapıldı': string;
  'raporlanan sonuç': string;
  'kaynak bağlantısı': string;
  'kaynak türü': string;
  'kanıt düzeyi': string;
  'aktarılabilirlik koşulları (hukuki yetki, altyapı, gelir)': string;
  'Türkiye için bilinen engeller': string;
  'öneri uyarısı': string;
}

export interface ProvinceProjection {
  il: string;
  hedef_yil: number;
  cikti_etiketi: string;
  guvenilirlik: string;
  yontem: string;
  ufuk_yil: number;
  dusuk_senaryo: number;
  baz_senaryo: number;
  yuksek_senaryo: number;
  aralik_80_alt: number;
  aralik_80_ust: number;
  aralik_95_alt: number;
  aralik_95_ust: number;
  is_synthetic: boolean;
  neden: string;
}
