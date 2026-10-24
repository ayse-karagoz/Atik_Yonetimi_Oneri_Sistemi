"""2022 il verisi için açıklanabilir atık modeli prototipi.

Amaç tahmin performansından çok, seçilen açıklayıcı değişkenlerin kişi başı
toplanan atık miktarına il bazındaki göreli katkısını görünür kılmaktır.

Örnek kullanım:
    .venv/bin/python model_katki_analizi.py
    .venv/bin/python model_katki_analizi.py --model linear
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.metrics import r2_score
from sklearn.preprocessing import StandardScaler


# Her etikete karşılık gelen anahtar, birleşik CSV'deki sütun adında aranır.
# Veri setine yeni bir açıklayıcı değişken eklemek için listeye bir satır eklemek
# yeterlidir; anahtar, ilgili sütun adının bir parçası olmalıdır.
OZELLIKLER = [
    ("Kişi başı GSYH", "kisi_basi_gshy"),
    ("Ortalama hanehalkı büyüklüğü", "ortalama_hanehalki_buyuklugu"),
    ("Toplam nüfus", "nufus__ng_adnks"),
    ("Yabancı nüfus", "yabanci_nufus"),
    ("Konaklama tesise geliş sayısı", "tesise_gelis_sayisi_toplam"),
    ("Konaklama geceleme", "geceleme_toplam"),
    ("Konaklama doluluk oranı", "doluluk_orani_toplam"),
    ("Konaklama ortalama kalış süresi", "ortalama_kalis_suresi_toplam"),
]
HEDEF_ANAHTARI = "amount_of_waste_per_capita"


def anahtar(metin: object) -> str:
    """Sütun aramasını Türkçe karakter ve yazım farkından bağımsızlaştırır."""
    metin = unicodedata.normalize("NFKD", str(metin))
    metin = "".join(harf for harf in metin if not unicodedata.combining(harf))
    metin = metin.translate(str.maketrans("ÇçĞğİIıÖöŞşÜü", "ccggiiioossuu"))
    return re.sub(r"[^a-z0-9]+", "_", metin.lower()).strip("_")


def sutun_bul(df: pd.DataFrame, aranan: str) -> str:
    aranan = anahtar(aranan)
    eslesenler = [kolon for kolon in df.columns if aranan in anahtar(kolon)]
    if len(eslesenler) == 1:
        return eslesenler[0]
    if not eslesenler:
        raise KeyError(f"'{aranan}' anahtarına karşılık gelen sütun bulunamadı.")
    raise KeyError(f"'{aranan}' için birden fazla sütun bulundu: {eslesenler}")


def veriyi_hazirla(girdi: Path) -> tuple[pd.DataFrame, str, dict[str, str], pd.DataFrame]:
    """Yalnızca gerçek satırları kullanır, sayısallaştırır ve eksikleri doldurur."""
    df = pd.read_csv(girdi)
    if "İl" not in df.columns:
        raise KeyError("Girdide 'İl' sütunu bulunamadı.")
    if "is_synthetic" not in df.columns:
        raise KeyError("Girdide 'is_synthetic' sütunu yok; gerçek ve sentetik kayıtlar ayrıştırılamaz.")

    sentetik = df["is_synthetic"].astype("string").str.strip().str.lower()
    gecerli_degerler = {"true", "false", "1", "0"}
    gecersiz = sentetik.notna() & ~sentetik.isin(gecerli_degerler)
    if gecersiz.any() or sentetik.isna().any():
        raise ValueError("'is_synthetic' yalnızca true/false değerlerini içermeli ve boş olmamalı.")
    sentetik_maske = sentetik.isin({"true", "1"})
    if sentetik_maske.any():
        print(f"{int(sentetik_maske.sum())} sentetik satır eğitim ve metriklerden çıkarıldı.")
    df = df.loc[~sentetik_maske].copy()
    if df.empty:
        raise ValueError("is_synthetic=False olan gerçek satır kalmadı.")

    hedef_sutunu = sutun_bul(df, HEDEF_ANAHTARI)
    secilenler = {etiket: sutun_bul(df, aranan) for etiket, aranan in OZELLIKLER}
    kullanilacak = [hedef_sutunu, *secilenler.values()]
    sayisal = df[["İl", *kullanilacak]].copy()
    for kolon in kullanilacak:
        sayisal[kolon] = pd.to_numeric(sayisal[kolon], errors="coerce")
        if sayisal[kolon].notna().sum() == 0:
            raise ValueError(f"'{kolon}' tamamen boş olduğu için modelde kullanılamaz.")
        eksik = int(sayisal[kolon].isna().sum())
        if eksik:
            ortanca = float(sayisal[kolon].median())
            sayisal[kolon] = sayisal[kolon].fillna(ortanca)
            print(f"{kolon}: {eksik} eksik değer ortanca ({ortanca:.4g}) ile dolduruldu.")

    if sayisal["İl"].duplicated().any():
        tekrarlar = sayisal.loc[sayisal["İl"].duplicated(), "İl"].tolist()
        raise ValueError(f"İl anahtarı tekil değil: {tekrarlar[:5]}")
    return df, hedef_sutunu, secilenler, sayisal


def modeli_calistir(
    sayisal: pd.DataFrame,
    hedef_sutunu: str,
    secilenler: dict[str, str],
    model_turu: str,
    ridge_alpha: float,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, object]]:
    """Standartlaştırılmış modeli ve il bazlı katkı tablolarını oluşturur."""
    etiketler = list(secilenler)
    ozellik_sutunlari = list(secilenler.values())
    X = sayisal[ozellik_sutunlari].to_numpy(dtype=float)
    y = sayisal[hedef_sutunu].to_numpy(dtype=float)

    x_olcekle = StandardScaler()
    y_olcekle = StandardScaler()
    X_z = x_olcekle.fit_transform(X)
    y_z = y_olcekle.fit_transform(y.reshape(-1, 1)).ravel()
    model = Ridge(alpha=ridge_alpha) if model_turu == "ridge" else LinearRegression()
    model.fit(X_z, y_z)

    tahmin_z = model.predict(X_z)
    tahmin = y_olcekle.inverse_transform(tahmin_z.reshape(-1, 1)).ravel()
    katkilar = X_z * model.coef_
    mutlak_toplam = np.abs(katkilar).sum(axis=1)
    paylar = np.divide(
        np.abs(katkilar), mutlak_toplam[:, None],
        out=np.zeros_like(katkilar), where=mutlak_toplam[:, None] != 0,
    ) * 100

    # Etki işareti: pozitif katkı, ilin model tahminini yükseltir; negatif katkı düşürür.
    detay = pd.DataFrame({
        "İl": np.repeat(sayisal["İl"].to_numpy(), len(etiketler)),
        "Değişken": np.tile(etiketler, len(sayisal)),
        "Standartlaştırılmış değer": X_z.ravel(),
        "Standartlaştırılmış katsayı": np.tile(model.coef_, len(sayisal)),
        "Katkı (standartlaştırılmış birim)": katkilar.ravel(),
        "Göreli katkı payı (%)": paylar.ravel(),
    })
    detay["Etki yönü"] = np.where(detay["Katkı (standartlaştırılmış birim)"] >= 0, "Pozitif", "Negatif")
    detay = detay.sort_values(["İl", "Göreli katkı payı (%)"], ascending=[True, False])

    ozet = pd.DataFrame({
        "Değişken": etiketler,
        "Kaynak sütun": ozellik_sutunlari,
        "Standartlaştırılmış katsayı": model.coef_,
        "Ortalama mutlak katkı": np.abs(katkilar).mean(axis=0),
    })
    ozet["Küresel göreli önem (%)"] = (
        ozet["Ortalama mutlak katkı"] / ozet["Ortalama mutlak katkı"].sum() * 100
    )
    ozet = ozet.sort_values("Küresel göreli önem (%)", ascending=False)

    il_ozeti = sayisal[["İl"]].copy()
    il_ozeti["Gerçek kişi başı atık"] = y
    il_ozeti["Model tahmini"] = tahmin
    il_ozeti["Artık (gerçek - tahmin)"] = y - tahmin
    il_ozeti["Toplam mutlak katkı"] = mutlak_toplam
    metrikler = {
        "model": model_turu,
        "ridge_alpha": ridge_alpha if model_turu == "ridge" else None,
        "gözlem_sayısı": int(len(sayisal)),
        "özellik_sayısı": int(len(etiketler)),
        "eğitim_R_kare": float(r2_score(y, tahmin)),
        "hedef_sütunu": hedef_sutunu,
        "not": "R-kare eğitim verisindedir; prototipte açıklama amacıyla raporlanır, tahmin başarısı iddiası değildir.",
    }
    return ozet, detay, {"metrikler": metrikler, "il_ozeti": il_ozeti}


def main() -> None:
    parser = argparse.ArgumentParser(description="2022 il verisiyle açıklanabilir atık katkı modeli")
    parser.add_argument("--girdi", type=Path, default=Path("il_verileri_2022.csv"))
    parser.add_argument("--cikti-klasoru", type=Path, default=Path("model_ciktilari"))
    parser.add_argument("--model", choices=("ridge", "linear"), default="ridge")
    parser.add_argument("--ridge-alpha", type=float, default=1.0)
    args = parser.parse_args()
    if args.ridge_alpha < 0:
        parser.error("--ridge-alpha negatif olamaz.")

    _, hedef, secilenler, sayisal = veriyi_hazirla(args.girdi)
    ozet, detay, sonuc = modeli_calistir(sayisal, hedef, secilenler, args.model, args.ridge_alpha)
    args.cikti_klasoru.mkdir(parents=True, exist_ok=True)
    ozet.to_csv(args.cikti_klasoru / "model_ozeti_2022.csv", index=False, encoding="utf-8-sig")
    detay.to_csv(args.cikti_klasoru / "il_bazli_katki_paylari_2022.csv", index=False, encoding="utf-8-sig")
    sonuc["il_ozeti"].to_csv(args.cikti_klasoru / "il_model_ozeti_2022.csv", index=False, encoding="utf-8-sig")
    with (args.cikti_klasoru / "model_metrikleri_2022.json").open("w", encoding="utf-8") as dosya:
        json.dump(sonuc["metrikler"], dosya, ensure_ascii=False, indent=2)

    print(f"Model: {sonuc['metrikler']['model']}")
    print(f"Eğitim R²: {sonuc['metrikler']['eğitim_R_kare']:.3f}")
    print(f"Çıktı klasörü: {args.cikti_klasoru.resolve()}")


if __name__ == "__main__":
    main()
