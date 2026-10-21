"""81 il verisini klasördeki CSV/Excel dosyalarından birleştirir.

Örnek:
    python3 birlesik_il_verileri.py --veri-klasoru veri --yil 2022

Gerekli paketler:
    python3 -m pip install pandas openpyxl numpy
"""

from __future__ import annotations

import argparse
import csv
import re
import unicodedata
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


# Ana tabloyu her zaman 81 il ile üretmek için resmî il listesi.
ILLER = [
    "Adana", "Adıyaman", "Afyonkarahisar", "Ağrı", "Amasya", "Ankara",
    "Antalya", "Artvin", "Aydın", "Balıkesir", "Bilecik", "Bingöl",
    "Bitlis", "Bolu", "Burdur", "Bursa", "Çanakkale", "Çankırı",
    "Çorum", "Denizli", "Diyarbakır", "Edirne", "Elazığ", "Erzincan",
    "Erzurum", "Eskişehir", "Gaziantep", "Giresun", "Gümüşhane",
    "Hakkâri", "Hatay", "Isparta", "Mersin", "İstanbul", "İzmir",
    "Kars", "Kastamonu", "Kayseri", "Kırklareli", "Kırşehir", "Kocaeli",
    "Konya", "Kütahya", "Malatya", "Manisa", "Kahramanmaraş", "Mardin",
    "Muğla", "Muş", "Nevşehir", "Niğde", "Ordu", "Rize", "Sakarya",
    "Samsun", "Siirt", "Sinop", "Sivas", "Tekirdağ", "Tokat", "Trabzon",
    "Tunceli", "Şanlıurfa", "Uşak", "Van", "Yozgat", "Zonguldak",
    "Aksaray", "Bayburt", "Karaman", "Kırıkkale", "Batman", "Şırnak",
    "Bartın", "Ardahan", "Iğdır", "Yalova", "Karabük", "Kilis", "Osmaniye",
    "Düzce",
]


def il_anahtari(deger: object) -> str:
    """İl adlarını Türkçe karakter/büyük harf/boşluk farkından bağımsız eşleştirir."""
    metin = unicodedata.normalize("NFKD", str(deger)).strip()
    metin = "".join(harf for harf in metin if not unicodedata.combining(harf))
    metin = re.sub(r"\s+", " ", metin)
    ceviri = str.maketrans({
        "Ç": "c", "ç": "c", "Ğ": "g", "ğ": "g", "İ": "i", "I": "i", "ı": "i",
        "Ö": "o", "ö": "o", "Ş": "s", "ş": "s", "Ü": "u", "ü": "u",
    })
    return metin.translate(ceviri).lower()


# Sık karşılaşılan eski/kısa il adları.
IL_ESANLAMLARI = {
    "afyon": "afyonkarahisar", "afyon karahisar": "afyonkarahisar",
    "icel": "mersin", "maras": "kahramanmaras", "kahraman maras": "kahramanmaras",
    "urfa": "sanliurfa", "sanli urfa": "sanliurfa",
}
IL_SOZLUGU = {il_anahtari(il): il for il in ILLER}
IL_SOZLUGU.update({takma: IL_SOZLUGU[hedef] for takma, hedef in IL_ESANLAMLARI.items()})


def standart_il(deger: object) -> str | None:
    """Bir değeri resmî yazımlı il adına çevirir; il değilse None döner."""
    return IL_SOZLUGU.get(il_anahtari(deger))


def temiz_kolon_adi(ad: object) -> str:
    return re.sub(r"\s+", " ", str(ad).replace("\n", " ")).strip()


def sayiya_cevir(seri: pd.Series) -> pd.Series:
    """1.234,56 ve 1234.56 gibi Türkçe/uluslararası sayıları güvenle sayıya çevirir."""
    if pd.api.types.is_numeric_dtype(seri):
        return pd.to_numeric(seri, errors="coerce")
    metin = seri.astype("string").str.strip().str.replace("\u00a0", "", regex=False)
    hem_nokta_hem_virgul = metin.str.contains(".", regex=False, na=False) & metin.str.contains(",", regex=False, na=False)
    metin.loc[hem_nokta_hem_virgul] = (
        metin.loc[hem_nokta_hem_virgul].str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
    )
    metin.loc[~hem_nokta_hem_virgul] = metin.loc[~hem_nokta_hem_virgul].str.replace(",", ".", regex=False)
    return pd.to_numeric(metin, errors="coerce")


def csv_ayracini_bul(dosya: Path, encoding: str) -> str:
    with dosya.open("r", encoding=encoding, errors="replace", newline="") as dosya_nesnesi:
        ornek = dosya_nesnesi.read(16_384)
    try:
        return csv.Sniffer().sniff(ornek, delimiters=";,\t|").delimiter
    except csv.Error:
        return ";" if ornek.count(";") > ornek.count(",") else ","


def csv_oku(dosya: Path) -> pd.DataFrame:
    son_hata: Exception | None = None
    for encoding in ("utf-8-sig", "utf-8", "cp1254", "latin1"):
        try:
            return pd.read_csv(dosya, sep=csv_ayracini_bul(dosya, encoding), encoding=encoding, dtype="string")
        except (UnicodeDecodeError, pd.errors.ParserError) as hata:
            son_hata = hata
    raise RuntimeError(f"CSV okunamadı: {son_hata}")


def dosya_oku(dosya: Path) -> pd.DataFrame:
    if dosya.suffix.lower() == ".csv":
        return csv_oku(dosya)
    # Bazı turizm tablolarında iki satırlı, birleştirilmiş başlık bulunur
    # (ör. "GECELEME" > "YABANCI / YERLİ / TOPLAM"). Önce ham sayfayı okuyup
    # bu başlığı tek satıra indirgeriz.
    ham = pd.read_excel(dosya, sheet_name=0, header=None, dtype="string")
    baslik_satiri = next(
        (
            i for i, satir in ham.iterrows()
            if satir.astype("string").map(il_anahtari).isin({"il", "iller", "il adi", "il adı"}).any()
        ),
        None,
    )
    if baslik_satiri is None:
        return pd.read_excel(dosya, sheet_name=0, dtype="string")

    ilk_baslik = ham.iloc[baslik_satiri].fillna("").astype(str).map(temiz_kolon_adi)
    sonraki_satir = ham.iloc[baslik_satiri + 1] if baslik_satiri + 1 < len(ham) else pd.Series("", index=ham.columns)
    # Sonraki satırda il adı varsa bu satır veri satırıdır, ikinci başlık değildir.
    iki_satirli = sonraki_satir.map(standart_il).notna().sum() == 0
    if iki_satirli:
        # Birleştirilmiş hücrelerde üst başlık yalnızca ilk alt sütunda görünür.
        ilk_baslik = ilk_baslik.replace("", pd.NA).ffill().fillna("")
        ikinci_baslik = sonraki_satir.fillna("").astype(str).map(temiz_kolon_adi)
        basliklar = ["_".join(parca for parca in (a, b) if parca) or f"Kolon_{j}" for j, (a, b) in enumerate(zip(ilk_baslik, ikinci_baslik))]
        veri = ham.iloc[baslik_satiri + 2 :].copy()
    else:
        basliklar = [ad or f"Kolon_{j}" for j, ad in enumerate(ilk_baslik)]
        veri = ham.iloc[baslik_satiri + 1 :].copy()
    # Aynı alt başlık (ör. üç farklı "TOPLAM") pandas'ta yinelenen kolon
    # üretmesin; üst başlık boşsa bile benzersiz bir son ek verilir.
    gorulen: dict[str, int] = {}
    benzersiz_basliklar: list[str] = []
    for baslik in basliklar:
        gorulen[baslik] = gorulen.get(baslik, 0) + 1
        benzersiz_basliklar.append(baslik if gorulen[baslik] == 1 else f"{baslik}_{gorulen[baslik]}")
    veri.columns = benzersiz_basliklar
    veri.attrs["il_hucreleri_birlestirilmis"] = True
    return veri.reset_index(drop=True)


def il_kolonunu_bul(df: pd.DataFrame) -> str | None:
    """İl adı içeren kolonu, 81 il ile gerçek eşleşme sayısına göre seçer."""
    en_iyi_kolon: str | None = None
    en_iyi_skor = 0
    for kolon in df.columns:
        skor = df[kolon].map(standart_il).notna().sum()
        if skor > en_iyi_skor:
            en_iyi_kolon, en_iyi_skor = str(kolon), int(skor)
    return en_iyi_kolon if en_iyi_skor else None


def yil_kolonunu_bul(df: pd.DataFrame) -> str | None:
    # DOGUM_YIL ve BAZ_YILI bir gözlem dönemi değildir. Yalnızca dönem/yıl
    # anlamını açıkça taşıyan kolonlar seçilir.
    anahtarlar = ("time_period", "time period", "zaman", "observation year")
    for kolon in df.columns:
        ad = il_anahtari(kolon)
        if any(anahtar in ad for anahtar in anahtarlar) or ad in {"yil", "year"}:
            return str(kolon)
    return None


def toplam_filtrele(df: pd.DataFrame, il_kolonu: str) -> pd.DataFrame:
    """Cinsiyet/yerleşim kırılımlarında varsa Toplam satırını seçer.

    Böylece kadın + erkek gibi alt kırılımlar yanlışlıkla tekrar toplanmaz.
    """
    # IKAMET_YERI bazı TÜİK dosyalarında ilin kodunu taşır; onu "Toplam"a
    # filtrelemek il kayıtlarını siler. Bu nedenle yalnızca gerçek alt
    # kırılımları (cinsiyet ve yerleşim türü) daraltılır.
    boyut_kolonlari = {"sex", "yerlesim_yeri_tur"}
    toplam_degerler = {"toplam", "total", "_t"}
    sonuc = df.copy()
    for kolon in sonuc.columns:
        if kolon == il_kolonu or il_anahtari(kolon) not in boyut_kolonlari:
            continue
        degerler = sonuc[kolon].astype("string").map(il_anahtari)
        if degerler.isin(toplam_degerler).any():
            sonuc = sonuc[degerler.isin(toplam_degerler)].copy()
    return sonuc


def deger_kolonunu_bul(df: pd.DataFrame) -> str | None:
    oncelikler = ("deger", "değer", "gozlem degeri", "gözlem değeri", "value", "obs value")
    for oncelik in oncelikler:
        for kolon in df.columns:
            if il_anahtari(kolon) == il_anahtari(oncelik):
                return str(kolon)
    return None


def guvenli_etiket(metin: object) -> str:
    return re.sub(r"\s+", "_", temiz_kolon_adi(metin)).strip("_")


def kaynak_adi(dosya: Path) -> str:
    """Dosya adındaki yılı kaldırır; yıllar arası aynı özellik adını korur."""
    adsiz = re.sub(r"(?<!\d)(?:19|20)\d{2}(?!\d)", "", dosya.stem)
    adsiz = re.sub(r"[_\- ]+", "_", adsiz).strip("_")
    return guvenli_etiket(adsiz)


def ozellik_adi(ad: object) -> str:
    """Yıl zaten dosya adıyla belirtildiği için özellik başlığından kaldırılır."""
    adsiz = re.sub(r"(?<!\d)(?:19|20)\d{2}(?!\d)", "", str(ad))
    return guvenli_etiket(re.sub(r"[()]+", "", adsiz))


def kaynak_tablosuna_donustur(df: pd.DataFrame, kaynak: str, yil: int) -> pd.DataFrame | None:
    """Tek bir dosyayı bir satır/il olacak biçimde geniş tabloya dönüştürür."""
    df = df.copy()
    df.columns = [temiz_kolon_adi(k) for k in df.columns]
    il_kolonu = il_kolonunu_bul(df)
    if il_kolonu is None:
        print(f"  UYARI: İl adı içeren kolon bulunamadı; atlandı.")
        return None

    # Excel'de il adı ilk satırda, ilçeler ise alt satırlarda boş bırakılmış
    # olabiliyor. İl bilgisi aşağı doğru taşınır ve il toplamı hesaplanır.
    if df.attrs.get("il_hucreleri_birlestirilmis"):
        df[il_kolonu] = df[il_kolonu].ffill()

    yil_kolonu = yil_kolonunu_bul(df)
    if yil_kolonu is not None:
        yil_degerleri = pd.to_numeric(df[yil_kolonu], errors="coerce")
        if (yil_degerleri == yil).any():
            df = df.loc[yil_degerleri == yil].copy()
            print(f"  {yil_kolonu} = {yil} filtresi uygulandı.")
        else:
            print(f"  UYARI: {yil_kolonu} içinde {yil} yok; kaynak atlandı (farklı yıllar karıştırılmadı).")
            return None

    df = toplam_filtrele(df, il_kolonu)
    df["İl"] = df[il_kolonu].map(standart_il)
    il_olmayanlar = df.loc[df["İl"].isna(), il_kolonu].dropna().astype(str).unique().tolist()
    df = df.dropna(subset=["İl"]).copy()
    if il_olmayanlar:
        print(f"  Eşleşmeyen coğrafi değerler (ilk 8): {il_olmayanlar[:8]}")
    if df.empty:
        print("  UYARI: Filtrelerden sonra il kaydı kalmadı; atlandı.")
        return None

    deger_kolonu = deger_kolonunu_bul(df)
    if deger_kolonu is not None:
        # Uzun format: gösterge varsa her gösterge ayrı sütuna pivotlanır.
        df[deger_kolonu] = sayiya_cevir(df[deger_kolonu])
        gosterge = next((str(k) for k in df.columns if il_anahtari(k) in {"indicator", "istatistiksel gosterge"}), None)
        if gosterge is not None and df[gosterge].nunique(dropna=True) > 1:
            sonuc = df.pivot_table(index="İl", columns=gosterge, values=deger_kolonu, aggfunc="mean").reset_index()
            sonuc.columns = ["İl"] + [f"{kaynak}__{guvenli_etiket(k)}" for k in sonuc.columns[1:]]
        else:
            sonuc = df.groupby("İl", as_index=False)[deger_kolonu].mean()
            sonuc = sonuc.rename(columns={deger_kolonu: f"{kaynak}__{guvenli_etiket(df[gosterge].dropna().iloc[0]) if gosterge and df[gosterge].notna().any() else 'Deger'}"})
    else:
        # Geniş format: sayısal olabilen veri sütunlarını koru. Başlığında yıl
        # bulunan sütunlardan yalnızca istenen yılı alır.
        adaylar: dict[str, pd.Series] = {}
        for kolon in df.columns:
            if kolon in {il_kolonu, "İl"}:
                continue
            if re.search(r"\b(19|20)\d{2}\b", str(kolon)) and str(yil) not in str(kolon):
                continue
            sayilar = sayiya_cevir(df[kolon])
            if sayilar.notna().sum() > 0:
                adaylar[f"{kaynak}__{ozellik_adi(kolon)}"] = sayilar
        if not adaylar:
            print("  UYARI: Sayısal veri sütunu bulunamadı; atlandı.")
            return None
        genis = pd.DataFrame({"İl": df["İl"], **adaylar})
        if df.attrs.get("il_hucreleri_birlestirilmis"):
            # İlçe bazındaki sayılar toplanır; oran ve ortalamalar ilçe
            # değerlerinin ortalamasıyla temsil edilir.
            fonksiyonlar = {
                kolon: ("mean" if any(ipucu in il_anahtari(kolon) for ipucu in ("oran", "doluluk", "ortalama", "yogunluk", "sure")) else "sum")
                for kolon in genis.columns if kolon != "İl"
            }
            sonuc = genis.groupby("İl", as_index=False).agg(fonksiyonlar)
        else:
            sonuc = genis.groupby("İl", as_index=False).mean(numeric_only=True)

    tekrar = int(df["İl"].duplicated().sum())
    if tekrar:
        if df.attrs.get("il_hucreleri_birlestirilmis"):
            print(f"  {tekrar} ilçe satırı il bazında toplulaştırıldı (sayılar toplam, oran/ortalamalar ortalama).")
        else:
            print(f"  {tekrar} tekrar eden il satırı bulundu; aynı il için ortalama alındı.")
    return sonuc


def konaklama_kolonu(kolon: str) -> bool:
    ad = il_anahtari(kolon)
    return "konaklama" in ad and "yogunluk" in ad


def eksikleri_doldur(df: pd.DataFrame, tohum: int = 42) -> pd.DataFrame:
    """Sayısal boşlukları doldürür ve uygulanan yöntemi konsola bildirir."""
    uretec = np.random.default_rng(tohum)
    for kolon in [k for k in df.columns if k != "İl"]:
        eksik = int(df[kolon].isna().sum())
        if not eksik:
            continue
        gozlem = pd.to_numeric(df[kolon], errors="coerce").dropna()
        if konaklama_kolonu(kolon):
            if len(gozlem) >= 2:
                alt, ust = np.quantile(gozlem, [0.05, 0.95])
                if alt == ust:
                    alt, ust = max(0, alt * 0.8), ust * 1.2 if ust else 1.0
                df.loc[df[kolon].isna(), kolon] = uretec.uniform(alt, ust, eksik)
                print(f"  {kolon}: {eksik} eksik değer, gözlenen %5-%95 aralığında ({alt:.3g}-{ust:.3g}) rastgele mock veri ile dolduruldu.")
            else:
                # Hiç gözlem yoksa biriminizi biliyorsanız bu aralığı aşağıda değiştirin.
                df.loc[df[kolon].isna(), kolon] = uretec.uniform(0, 100, eksik)
                print(f"  {kolon}: {eksik} eksik değer, gözlem olmadığı için varsayılan 0-100 mock aralığıyla dolduruldu.")
        elif len(gozlem):
            ortanca = float(gozlem.median())
            df[kolon] = df[kolon].fillna(ortanca)
            print(f"  {kolon}: {eksik} eksik değer, sütun ortancasıyla ({ortanca:.3g}) dolduruldu.")
        else:
            print(f"  {kolon}: tamamı boş olduğu için uydurma değer üretilmedi (sütun korunuyor).")
    return df


def konaklama_sentetik_2024(veri_klasoru: Path) -> pd.DataFrame | None:
    """2024 konaklama verisini 2020-2022 il bazlı eğilimini uzatarak üretir.

    Sayı göstergeleri için ``2024 = 2022 + (2022 - 2020)`` uygulanır. Oran ve
    ortalamalar 0-100 (oran) sınırına çekilir. 2020 değeri olmayan bir ilde
    2022 değeri korunur; son aşamadaki eksikler genel eksik-değer kuralıyla
    doldurulur. Böylece sentetik değerler tekrar üretilebilir ve denetlenebilir.
    """
    adaylar = [
        p for p in veri_klasoru.iterdir()
        if p.suffix.lower() in {".xlsx", ".xls", ".csv"}
        and "belediye" in il_anahtari(p.stem) and "konaklama" in il_anahtari(p.stem)
    ]
    onceki = next((p for p in adaylar if "2020" in p.stem), None)
    guncel = next((p for p in adaylar if "2022" in p.stem), None)
    if guncel is None:
        print("  UYARI: 2024 sentetik konaklama verisi için 2022 referans dosyası bulunamadı.")
        return None

    kaynak = kaynak_adi(guncel)
    try:
        tablo_2022 = kaynak_tablosuna_donustur(dosya_oku(guncel), kaynak, 2022)
        tablo_2020 = kaynak_tablosuna_donustur(dosya_oku(onceki), kaynak, 2020) if onceki else None
    except Exception as hata:
        print(f"  UYARI: Sentetik konaklama referansı okunamadı: {hata}")
        return None
    if tablo_2022 is None:
        return None
    if tablo_2020 is None:
        print("  UYARI: 2020 konaklama referansı yok; 2024 için 2022 seviyesi kullanılacak.")
        return tablo_2022

    eski = tablo_2020.set_index("İl")
    sentetik = tablo_2022.set_index("İl").copy()
    ortak_sutunlar = [k for k in sentetik.columns if k in eski.columns]
    for kolon in ortak_sutunlar:
        simdiki = pd.to_numeric(sentetik[kolon], errors="coerce")
        onceki_deger = pd.to_numeric(eski[kolon], errors="coerce").reindex(sentetik.index)
        tahmin = simdiki + (simdiki - onceki_deger)
        # Önceki yıl eksikse 2022 seviyesi en savunulabilir geri dönüştür.
        tahmin = tahmin.where(onceki_deger.notna(), simdiki).clip(lower=0)
        ad = il_anahtari(kolon)
        if "oran" in ad or "doluluk" in ad or "%" in kolon:
            tahmin = tahmin.clip(upper=100)
        sentetik[kolon] = tahmin
    print(f"  2024 belediye konaklama: {guncel.name} ve {onceki.name} eğiliminden sentetik olarak üretildi.")
    return sentetik.reset_index()


def kentsel_kirsal_sentetik_2020(veri_klasoru: Path) -> pd.DataFrame | None:
    """2020 kentsel/kırsal nüfusu, 2022 ve 2024'ten geriye eğilimle tahmin eder."""
    dosya = next((p for p in veri_klasoru.iterdir() if "kentsel" in il_anahtari(p.stem) and "kirsal" in il_anahtari(p.stem)), None)
    if dosya is None:
        return None
    kaynak = kaynak_adi(dosya)
    try:
        veri_2022 = kaynak_tablosuna_donustur(dosya_oku(dosya), kaynak, 2022)
        veri_2024 = kaynak_tablosuna_donustur(dosya_oku(dosya), kaynak, 2024)
    except Exception as hata:
        print(f"  UYARI: 2020 kentsel/kırsal sentetik referansı okunamadı: {hata}")
        return None
    if veri_2022 is None or veri_2024 is None:
        return None
    eski = veri_2022.set_index("İl")
    yeni = veri_2024.set_index("İl")
    sentetik = eski.copy()
    for kolon in sentetik.columns:
        if kolon not in yeni.columns:
            continue
        tahmin = 2 * pd.to_numeric(eski[kolon], errors="coerce") - pd.to_numeric(yeni[kolon], errors="coerce").reindex(eski.index)
        # Nüfus negatif olamaz; 2024 değeri eksikse 2022 seviyesi korunur.
        sentetik[kolon] = tahmin.where(tahmin.notna(), pd.to_numeric(eski[kolon], errors="coerce")).clip(lower=0)
    print(f"  2020 kentsel/kırsal nüfus: {dosya.name} içindeki 2022-2024 eğiliminden geriye sentetik olarak üretildi.")
    return sentetik.reset_index()


def calistir(veri_klasoru: Path, yil: int, cikti: Path) -> None:
    if not veri_klasoru.is_dir():
        raise FileNotFoundError(f"Veri klasörü bulunamadı: {veri_klasoru}")
    dosyalar = sorted(p for p in veri_klasoru.iterdir() if p.suffix.lower() in {".csv", ".xlsx", ".xls"})
    if not dosyalar:
        raise FileNotFoundError(f"{veri_klasoru} içinde CSV/XLS/XLSX bulunamadı.")

    birlesik = pd.DataFrame({"İl": ILLER})
    konaklama_yuklendi = False
    kentsel_kirsal_yuklendi = False
    for dosya in dosyalar:
        # Önceki çalıştırmanın çıktısını tekrar girdi kabul etme.
        if dosya.resolve() == cikti.resolve():
            continue
        dosya_yillari = set(re.findall(r"(?<!\d)(?:19|20)\d{2}(?!\d)", dosya.stem))
        if dosya_yillari and str(yil) not in dosya_yillari:
            print(f"\nAtlandı: {dosya.name} (dosya adındaki dönem {sorted(dosya_yillari)}, istenen dönem {yil})")
            continue
        print(f"\nOkunuyor: {dosya.name}")
        try:
            kaynak_df = kaynak_tablosuna_donustur(dosya_oku(dosya), kaynak_adi(dosya), yil)
            if kaynak_df is None:
                continue
            birlesik = birlesik.merge(kaynak_df, on="İl", how="left", validate="one_to_one")
            if "belediye" in il_anahtari(dosya.stem) and "konaklama" in il_anahtari(dosya.stem):
                konaklama_yuklendi = True
            if "kentsel" in il_anahtari(dosya.stem) and "kirsal" in il_anahtari(dosya.stem):
                kentsel_kirsal_yuklendi = True
            print(f"  Başarılı: {len(kaynak_df)} il ve {len(kaynak_df.columns) - 1} veri sütunu eklendi.")
        except Exception as hata:
            print(f"  HATA: Dosya atlandı -> {type(hata).__name__}: {hata}")

    if yil == 2024 and not konaklama_yuklendi:
        print("\n2024 belediye konaklama dosyası bulunamadı; sentetik seri hazırlanıyor.")
        sentetik_konaklama = konaklama_sentetik_2024(veri_klasoru)
        if sentetik_konaklama is not None:
            birlesik = birlesik.merge(sentetik_konaklama, on="İl", how="left", validate="one_to_one")
            print(f"  Başarılı: {len(sentetik_konaklama)} il ve {len(sentetik_konaklama.columns) - 1} sentetik konaklama sütunu eklendi.")

    if yil == 2020 and not kentsel_kirsal_yuklendi:
        print("\n2020 kentsel/kırsal nüfus kaydı yok; şema uyumu için sentetik seri hazırlanıyor.")
        sentetik_kentsel_kirsal = kentsel_kirsal_sentetik_2020(veri_klasoru)
        if sentetik_kentsel_kirsal is not None:
            birlesik = birlesik.merge(sentetik_kentsel_kirsal, on="İl", how="left", validate="one_to_one")
            print(f"  Başarılı: {len(sentetik_kentsel_kirsal)} il ve {len(sentetik_kentsel_kirsal.columns) - 1} sentetik kentsel/kırsal sütunu eklendi.")

    birlesik = eksikleri_doldur(birlesik)
    # Kaynakların okunma sırası değişse bile bütün yıl dosyalarında özellik
    # dizilimi sabit kalsın; yıl bilgisi yalnızca dosya adında yer alır.
    birlesik = birlesik[["İl"] + sorted(k for k in birlesik.columns if k != "İl")]
    birlesik.to_csv(cikti, index=False, encoding="utf-8-sig")
    print(f"\nTamamlandı: {len(birlesik)} il, {len(birlesik.columns) - 1} veri sütunu")
    print(f"Çıktı: {cikti.resolve()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="81 ilin dağınık CSV/Excel verilerini birleştirir.")
    parser.add_argument("--veri-klasoru", default="veri", type=Path, help="CSV ve Excel dosyalarının bulunduğu klasör")
    parser.add_argument("--yil", default=2022, type=int, help="Seçilecek dönem")
    parser.add_argument("--cikti", type=Path, help="Çıktı CSV dosyası (varsayılan: il_verileri_<yıl>.csv)")
    parser.add_argument("--tum-yillar", action="store_true", help="2020, 2022 ve 2024 için ayrı CSV üret")
    args = parser.parse_args()
    if args.tum_yillar:
        if args.cikti:
            parser.error("--tum-yillar ile --cikti birlikte kullanılamaz.")
        for secili_yil in (2020, 2022, 2024):
            print(f"\n{'=' * 16} {secili_yil} {'=' * 16}")
            calistir(args.veri_klasoru, secili_yil, Path(f"il_verileri_{secili_yil}.csv"))
    else:
        calistir(args.veri_klasoru, args.yil, args.cikti or Path(f"il_verileri_{args.yil}.csv"))
