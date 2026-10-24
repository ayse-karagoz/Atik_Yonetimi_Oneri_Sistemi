import {
  RawDatasetYear,
  ModelOptions,
  FullAnalysisResult,
  ProvinceAnalysis,
  VariableContribution,
  GlobalFeatureSummary,
  ModelMetrics,
} from '../types';

/**
 * Solves the linear system A * x = b using Gaussian elimination with partial pivoting.
 */
function solveLinearSystem(A: number[][], b: number[]): number[] {
  const n = A.length;
  const M: number[][] = A.map((row, i) => [...row, b[i]]);

  for (let i = 0; i < n; i++) {
    // Find pivot row
    let maxRow = i;
    for (let k = i + 1; k < n; k++) {
      if (Math.abs(M[k][i]) > Math.abs(M[maxRow][i])) {
        maxRow = k;
      }
    }

    // Swap pivot row
    const temp = M[i];
    M[i] = M[maxRow];
    M[maxRow] = temp;

    const pivot = M[i][i];
    if (Math.abs(pivot) < 1e-12) {
      continue;
    }

    // Normalize pivot row
    for (let c = i; c <= n; c++) {
      M[i][c] /= pivot;
    }

    // Eliminate other rows
    for (let k = 0; k < n; k++) {
      if (k !== i) {
        const factor = M[k][i];
        for (let c = i; c <= n; c++) {
          M[k][c] -= factor * M[i][c];
        }
      }
    }
  }

  return M.map((row) => row[n]);
}

export function runModelAnalysis(
  dataset: RawDatasetYear,
  options: ModelOptions = { modelType: 'ridge', ridgeAlpha: 1.0 }
): FullAnalysisResult {
  const { provinces: iller, featureLabels, X, y } = dataset;
  const N = iller.length;
  const K = featureLabels.length;

  // 1. Mean and Std of X (ddof = 0)
  const meanX: number[] = new Array(K).fill(0);
  const stdX: number[] = new Array(K).fill(0);

  for (let j = 0; j < K; j++) {
    let sum = 0;
    for (let i = 0; i < N; i++) {
      sum += X[i][j];
    }
    const m = sum / N;
    meanX[j] = m;

    let sq = 0;
    for (let i = 0; i < N; i++) {
      sq += (X[i][j] - m) ** 2;
    }
    stdX[j] = Math.sqrt(sq / N);
  }

  const X_z: number[][] = X.map((row) =>
    row.map((val, j) => (stdX[j] === 0 ? 0 : (val - meanX[j]) / stdX[j]))
  );

  // 2. Mean and Std of y (ddof = 0)
  let sumY = 0;
  for (let i = 0; i < N; i++) {
    sumY += y[i];
  }
  const meanY = sumY / N;

  let sqY = 0;
  for (let i = 0; i < N; i++) {
    sqY += (y[i] - meanY) ** 2;
  }
  const stdY = Math.sqrt(sqY / N);
  const y_z: number[] = y.map((val) => (stdY === 0 ? 0 : (val - meanY) / stdY));

  // 3. Compute (X_z^T * X_z + alpha * I) beta = X_z^T * y_z
  const alpha = options.modelType === 'ridge' ? Math.max(0, options.ridgeAlpha) : 0;
  const XtX: number[][] = Array.from({ length: K }, () => Array(K).fill(0));
  const Xty: number[] = Array(K).fill(0);

  for (let j = 0; j < K; j++) {
    for (let l = 0; l < K; l++) {
      let s = 0;
      for (let i = 0; i < N; i++) {
        s += X_z[i][j] * X_z[i][l];
      }
      XtX[j][l] = s;
    }
    XtX[j][j] += alpha;

    let sy = 0;
    for (let i = 0; i < N; i++) {
      sy += X_z[i][j] * y_z[i];
    }
    Xty[j] = sy;
  }

  const beta = solveLinearSystem(XtX, Xty);

  // 4. Predictions and R^2
  const pred_z: number[] = X_z.map((row) =>
    row.reduce((acc, val, j) => acc + val * beta[j], 0)
  );
  const pred_y: number[] = pred_z.map((pz) => pz * stdY + meanY);

  let ssTot = 0;
  let ssRes = 0;
  for (let i = 0; i < N; i++) {
    ssTot += (y[i] - meanY) ** 2;
    ssRes += (y[i] - pred_y[i]) ** 2;
  }
  const r2 = ssTot === 0 ? 0 : 1 - ssRes / ssTot;

  // 5. Distance Matrix (Euclidean on standardized X_z)
  const distMatrix: number[][] = Array.from({ length: N }, () => Array(N).fill(0));
  for (let i = 0; i < N; i++) {
    for (let k = i + 1; k < N; k++) {
      let d2 = 0;
      for (let j = 0; j < K; j++) {
        d2 += (X_z[i][j] - X_z[k][j]) ** 2;
      }
      const d = Math.sqrt(d2);
      distMatrix[i][k] = d;
      distMatrix[k][i] = d;
    }
  }

  // 6. Contributions and Province details
  // katkilar[i][j] = X_z[i][j] * beta[j]
  const katkilar: number[][] = X_z.map((row) =>
    row.map((val, j) => val * beta[j])
  );

  const absSums: number[] = katkilar.map((row) =>
    row.reduce((acc, val) => acc + Math.abs(val), 0)
  );

  const provincesMap: Record<string, ProvinceAnalysis> = {};

  for (let i = 0; i < N; i++) {
    const il = iller[i];

    // Find nearest and furthest
    let minDist = Infinity;
    let maxDist = -Infinity;
    let nearIdx = 0;
    let farIdx = 0;

    for (let k = 0; k < N; k++) {
      if (k === i) continue;
      const d = distMatrix[i][k];
      if (d < minDist) {
        minDist = d;
        nearIdx = k;
      }
      if (d > maxDist) {
        maxDist = d;
        farIdx = k;
      }
    }

    const totalAbs = absSums[i];
    const contribList: VariableContribution[] = [];

    for (let j = 0; j < K; j++) {
      const contrib = katkilar[i][j];
      const relShare = totalAbs > 0 ? (Math.abs(contrib) / totalAbs) * 100 : 0;
      contribList.push({
        variable: featureLabels[j],
        rawValue: X[i][j],
        standardizedValue: X_z[i][j],
        coefficient: beta[j],
        contribution: contrib,
        relativeSharePct: relShare,
        direction: contrib >= 0 ? 'Pozitif' : 'Negatif',
      });
    }

    // Sort by relative share descending
    contribList.sort((a, b) => b.relativeSharePct - a.relativeSharePct);

    // Check if first two relative shares differ by less than 5%
    const weightsClose =
      contribList.length >= 2 &&
      Math.abs(contribList[0].relativeSharePct - contribList[1].relativeSharePct) < 5;

    provincesMap[il] = {
      name: il,
      wastePerCapita: y[i],
      predictedWaste: pred_y[i],
      residual: y[i] - pred_y[i],
      totalAbsContribution: totalAbs,
      nearestProvince: iller[nearIdx],
      nearestDistance: minDist,
      oppositeProvince: iller[farIdx],
      oppositeDistance: maxDist,
      contributions: contribList,
      dominantFactors: [
        contribList[0]?.variable || '',
        contribList[1]?.variable || '',
        contribList[2]?.variable || '',
      ],
      weightsClose,
    };
  }

  // 7. Global Feature Importance
  const meanAbsContrib: number[] = new Array(K).fill(0);
  for (let j = 0; j < K; j++) {
    let s = 0;
    for (let i = 0; i < N; i++) {
      s += Math.abs(katkilar[i][j]);
    }
    meanAbsContrib[j] = s / N;
  }
  const sumMeanAbs = meanAbsContrib.reduce((acc, val) => acc + val, 0);

  const globalFeatures: GlobalFeatureSummary[] = featureLabels.map((flab, j) => ({
    variable: flab,
    standardizedCoef: beta[j],
    meanAbsContribution: meanAbsContrib[j],
    globalImportancePct: sumMeanAbs > 0 ? (meanAbsContrib[j] / sumMeanAbs) * 100 : 0,
  }));
  globalFeatures.sort((a, b) => b.globalImportancePct - a.globalImportancePct);

  const metrics: ModelMetrics = {
    modelType: options.modelType,
    ridgeAlpha: options.ridgeAlpha,
    observationCount: N,
    featureCount: K,
    trainR2: r2,
    nationalAverage: meanY,
    note: 'R-kare eğitim verisindedir; prototipte açıklama amacıyla raporlanır, tahmin başarısı iddiası değildir.',
  };

  return {
    year: dataset.year,
    metrics,
    provinces: provincesMap,
    provinceList: [...iller].sort((a, b) => a.localeCompare('tr')),
    globalFeatures,
    nationalAverage: meanY,
  };
}
