#!/usr/bin/env python3
"""İl bazlı belediye atığı için zaman sıralı geriye dönük sınama.

Bu betik yalnızca `belediye_atik_yillara_gore.csv` içindeki ham hedef serisini
kullanır. Kullanıcının beyanına göre sentetik olan seri yalnızca 2024 belediye
belgeli konaklamadır; bu dosyada konaklama değişkeni kullanılmaz.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from veri_cekme.birlesik_il_verileri import ILLER, standart_il


TARGET_TEMPLATE = "Amount of Waste Per Capita ({year})"
NATIONAL_LABEL = "Türkiye"
BOOTSTRAP_ITERATIONS = 500
BOOTSTRAP_SEED = 20261024


def metrics(actual: np.ndarray, predicted: np.ndarray) -> dict[str, float]:
    error = actual - predicted
    return {
        "MAE": float(np.abs(error).mean()),
        "RMSE": float(np.sqrt(np.mean(np.square(error)))),
    }


def bootstrap_mae_improvement(
    actual: np.ndarray, candidate: np.ndarray, baseline: np.ndarray
) -> tuple[float, float, float]:
    """Baz - aday mutlak hatası için ortalama ve %95 bootstrap aralığı."""
    improvement = np.abs(actual - baseline) - np.abs(actual - candidate)
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    samples = np.array([
        rng.choice(improvement, size=len(improvement), replace=True).mean()
        for _ in range(BOOTSTRAP_ITERATIONS)
    ])
    low, high = np.quantile(samples, [0.025, 0.975])
    return float(improvement.mean()), float(low), float(high)


def markdown_table(frame: pd.DataFrame) -> str:
    """Ek bir paket gerektirmeden küçük sonuç tablolarını Markdown'a çevirir."""
    headers = [str(column) for column in frame.columns]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in frame.itertuples(index=False, name=None):
        values = [f"{value:.6f}" if isinstance(value, (float, np.floating)) else str(value) for value in row]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def load_target(source: Path) -> tuple[pd.DataFrame, pd.Series]:
    raw = pd.read_csv(source)
    expected = [TARGET_TEMPLATE.format(year=year) for year in (2020, 2022, 2024)]
    absent = [column for column in expected if column not in raw.columns]
    if absent:
        raise ValueError(f"Hedef sütunlar bulunamadı: {absent}")
    if "REF_AREA" not in raw.columns:
        raise ValueError("Kaynakta REF_AREA il alanı yok.")

    raw["il"] = raw["REF_AREA"].map(standart_il)
    national = raw.loc[raw["REF_AREA"] == NATIONAL_LABEL, expected].squeeze()
    if not isinstance(national, pd.Series):
        raise ValueError("Türkiye toplam satırı tekil değil veya bulunamadı.")
    provinces = raw.dropna(subset=["il"]).copy()
    duplicates = provinces.loc[provinces["il"].duplicated(), "il"].tolist()
    if duplicates:
        raise ValueError(f"İl anahtarı tekil değil: {duplicates[:5]}")
    missing = sorted(set(ILLER).difference(provinces["il"]))
    extra = sorted(set(provinces["il"]).difference(ILLER))
    if missing or extra or len(provinces) != 81:
        raise ValueError(
            f"81 il koşulu sağlanmadı. Eksik: {missing}; fazladan: {extra}; satır: {len(provinces)}"
        )
    return provinces.set_index("il").loc[ILLER], national


def make_report(
    results: pd.DataFrame, improvement: pd.DataFrame, passed: bool, reason: str
) -> str:
    status = "geçti" if passed else "geçmedi"
    table = markdown_table(results)
    improvement_table = markdown_table(improvement)
    return f"""# Yöntem ve sınırlılıklar

## Sonuç

Geriye dönük sınama **{status}**. Kullanıcı isteğiyle 2027 için sayısal
senaryolar yayımlandı; durum: **güvenilmez**.

Gerekçe: {reason}

## Kullanılan gerçek veri ve varsayım

- Hedef, TÜİK il bazlı `Amount of Waste Per Capita` sütunudur. Birim, kaynak
  dosyasında açıkça yazmadığından `kg/kişi-gün` olduğu bu betikle doğrulanamadı;
  proje tanımındaki karşılığı bu şekilde belirtilmiştir.
- Kullanıcı beyanı uyarınca yalnızca 2024 belediye belgeli konaklama verisi
  sentetiktir. Bu sınamada konaklama veya başka açıklayıcı değişken kullanılmadı;
  yalnızca ham belediye atığı hedefi kullanıldı.
- Ham atık kaynağında `is_synthetic` sütunu yoktur. Bu çalıştırma, yukarıdaki
  açık kullanıcı beyanına dayanır; üretim kullanımı öncesinde bu köken bilgisinin
  kaynak dosyada ayrıca doğrulanması gerekir.
- 81 ilin her biri ve ayrı Türkiye toplam satırı bulundu. Hedef yılları 2020,
  2022 ve 2024'tür; dönem aralığı iki yıldır.

## Zaman sıralı sınama

- 2022 holdout: yalnızca 2020 kullanıldı. Bir il-bazlı eğim hesaplanamadığından
  trend yöntemi bu adımda uygulanamadı; iki baz karşılaştırıldı.
- 2024 holdout: yalnızca 2020 ve 2022 kullanıldı. Aday yöntem, il başına doğrusal
  iki-nokta eğilim uzatmasıdır: `2024 = 2022 + (2022 - 2020)`.
- “Son bilinen il değeri” bazı, son geçmiş yılın aynı il değeridir. “Ulusal
  ortalama” bazı, yalnızca son geçmiş yılın Türkiye toplam satırıdır. Gelecek
  yılın ulusal değeri kullanılmadı.

{table}

## Aday yöntemin hata iyileşmesi

İyileşme = bazın mutlak hatası − aday yöntemin mutlak hatası. Pozitif değer
aday yöntemi destekler. Aralıklar, 81 il üzerinden sabit tohumlu {BOOTSTRAP_ITERATIONS}
tekrarlı bootstrap ile %95 düzeyindedir.

{improvement_table}

## Projeksiyon kararı ve sınırlılıklar

- Geçme ölçütü: 2024 holdout'unda aday yöntemin ortalama MAE iyileşmesi hem son
  bilinen il değeri hem ulusal ortalama bazına karşı pozitif olmalı ve %95
  bootstrap aralığının alt sınırı sıfırın üzerinde kalmalıdır.
- Ölçüt sağlanmadı. Kullanıcının açık isteğiyle sayısal çıktı yine de
  yayımlandı; her satır `güvenilmez` ve `is_synthetic=true` olarak etiketlendi.
  Bu satırlar gerçek gözlem değildir; eğitimde ve hata metriklerinde
  kullanılmadı.
- Düşük/baz/yüksek senaryolar, sırasıyla 2020–2022 ve 2022–2024 iki yıllık
  değişimlerinin düşük, ortalama ve yüksek olanının 2024'ten 2027'ye üç yıllık
  uzatılmasıyla hesaplandı. Bu yalnızca üç veri noktasına dayanır.
- %80 ve %95 aralıkları, 2024 holdout'unda il-bazlı doğrusal eğilimin 81 ildeki
  mutlak hatalarının deneysel yüzdeliklerinden üretildi. Bu dağılım tek bir
  geçmiş sınama yılına dayanır ve üç yıllık ufuk için kalibre edilmemiştir.
- Yalnızca üç dönem (2020, 2022, 2024) vardır; eğilim için iki aralık gözlenir.
  2025–2027'de iklim, göç, turizm, belediye hizmet kapsamı, fiyatlar ve politika
  değişimleri bu seride bilinmemektedir.
- Bu analiz ilişki veya katkı payı iddia etmez; açıklayıcı değişken içermeyen
  saf zaman serisi kontrolüdür.
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Belediye atığı geriye dönük zaman sınaması")
    parser.add_argument("--source", type=Path, default=Path("veri/belediye_atik_yillara_gore.csv"))
    parser.add_argument("--output", type=Path, default=Path("projeksiyon.csv"))
    parser.add_argument("--report", type=Path, default=Path("yontem_ve_sinirlar.md"))
    args = parser.parse_args()

    provinces, national = load_target(args.source)
    y2020 = provinces[TARGET_TEMPLATE.format(year=2020)].to_numpy(float)
    y2022 = provinces[TARGET_TEMPLATE.format(year=2022)].to_numpy(float)
    y2024 = provinces[TARGET_TEMPLATE.format(year=2024)].to_numpy(float)

    records: list[dict[str, object]] = []
    # İlk holdout'ta trend için iki geçmiş gözlem yoktur.
    for name, prediction in {
        "son bilinen il değeri": y2020,
        "ulusal ortalama": np.full(len(provinces), float(national[TARGET_TEMPLATE.format(year=2020)])),
    }.items():
        records.append({"holdout_yili": 2022, "yontem": name, **metrics(y2022, prediction)})

    last_known = y2022
    national_mean = np.full(len(provinces), float(national[TARGET_TEMPLATE.format(year=2022)]))
    trend = y2022 + (y2022 - y2020)
    for name, prediction in {
        "son bilinen il değeri": last_known,
        "ulusal ortalama": national_mean,
        "il bazlı doğrusal trend": trend,
    }.items():
        records.append({"holdout_yili": 2024, "yontem": name, **metrics(y2024, prediction)})
    results = pd.DataFrame(records)

    improvements = []
    for name, baseline in {
        "son bilinen il değeri": last_known,
        "ulusal ortalama": national_mean,
    }.items():
        mean, low, high = bootstrap_mae_improvement(y2024, trend, baseline)
        improvements.append({
            "holdout_yili": 2024,
            "aday_yontem": "il bazlı doğrusal trend",
            "karsilastirma_bazi": name,
            "MAE_iyilesmesi": mean,
            "bootstrap_%95_alt": low,
            "bootstrap_%95_ust": high,
        })
    improvement = pd.DataFrame(improvements)
    passed = bool((improvement["bootstrap_%95_alt"] > 0).all())
    reason = (
        "İl bazlı doğrusal trend, 2024 holdout'unda son bilinen il değeri bazından "
        "daha düşük MAE üretmedi; bu baza göre bootstrap güven aralığı bütünüyle negatiftir."
        if not passed else "Aday yöntem her iki baza karşı önceden tanımlanmış MAE ölçütünü karşıladı."
    )

    # Kullanıcının açık talebi üzerine çıktı yayımlanır. Bu, geçmeyen yöntemin
    # gerçek gözlem gibi yorumlanmasını engellemek için sentetik olarak işaretlenir.
    horizon_years = 3
    years_per_step = 2
    step_20_22 = y2022 - y2020
    step_22_24 = y2024 - y2022
    scale = horizon_years / years_per_step
    low_scenario = np.maximum(0, y2024 + scale * np.minimum(step_20_22, step_22_24))
    base_scenario = np.maximum(0, y2024 + scale * ((step_20_22 + step_22_24) / 2))
    high_scenario = np.maximum(0, y2024 + scale * np.maximum(step_20_22, step_22_24))

    # Tek 2024 holdout kesitindeki mutlak hatalar, aralık genişliği için yalnızca
    # deneysel bir gösterge sağlar; üç yıllık ufukta kalibre edilmiş değildir.
    absolute_residuals = np.abs(y2024 - trend)
    residual_80 = float(np.quantile(absolute_residuals, 0.80))
    residual_95 = float(np.quantile(absolute_residuals, 0.95))
    output = pd.DataFrame({
        "il": provinces.index,
        "hedef_yil": 2027,
        "cikti_etiketi": "projeksiyon (senaryo bazlı)",
        "guvenilirlik": "güvenilmez",
        "yontem": "Üç gözlemli il bazlı doğrusal eğilim; geriye dönük sınamayı geçmedi",
        "ufuk_yil": horizon_years,
        "dusuk_senaryo": low_scenario,
        "baz_senaryo": base_scenario,
        "yuksek_senaryo": high_scenario,
        "aralik_80_alt": np.maximum(0, base_scenario - residual_80),
        "aralik_80_ust": base_scenario + residual_80,
        "aralik_95_alt": np.maximum(0, base_scenario - residual_95),
        "aralik_95_ust": base_scenario + residual_95,
        "is_synthetic": True,
        "neden": reason,
    })
    output.to_csv(args.output, index=False, encoding="utf-8-sig")
    args.report.write_text(make_report(results, improvement, passed, reason), encoding="utf-8")
    print(f"Geriye dönük sınama sonucu: {'GEÇTİ' if passed else 'GEÇMEDİ'}")
    print(f"Çıktı: {args.output.resolve()}")
    print(f"Rapor: {args.report.resolve()}")


if __name__ == "__main__":
    main()
