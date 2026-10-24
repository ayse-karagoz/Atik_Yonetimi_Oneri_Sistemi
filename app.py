"""İl bazlı atık profili için Streamlit arayüzü.

Çalıştırma:
    .venv/bin/streamlit run app.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
from sklearn.preprocessing import StandardScaler

from metin_sablonlari import (
    EGITIM_VERISI_NOTU_SABLONU,
    ILISKI_UYARISI,
    KONAKLAMA_NOTU,
    il_sonuc_cumlesi,
)
from model_katki_analizi import modeli_calistir, veriyi_hazirla
from veri_cekme.birlesik_il_verileri import standart_il


GIRDI = Path("il_verileri_2022.csv")
ATIK_KAYNAGI = Path("veri/belediye_atik_yillara_gore.csv")
PROJEKSIYON_DOSYASI = Path("projeksiyon.csv")
ONERI_DOSYASI = Path("oneri_tablosu.csv")
HEDEF_SUTUNU = "Amount of Waste Per Capita ({yil})"
YILLAR = (2020, 2022, 2024)

# Bu eşleştirme sabittir; seçili ildeki en yüksek katkı değişkeni, yalnızca
# aynı bağlam için araştırılmış uygulama örnekleriyle gösterilir.
ONERI_ATAMALARI = {
    "Konaklama doluluk oranı": "Yüksek konaklama doluluk oranı",
    "Konaklama tesise geliş sayısı": "Yüksek konaklama tesise geliş sayısı",
    "Toplam nüfus": "Yüksek toplam nüfus / yoğun kent bağlamı",
    "Konaklama ortalama kalış süresi": "Yüksek ortalama kalış süresi",
    "Ortalama hanehalkı büyüklüğü": "Küçük hane büyüklüğü",
}


@st.cache_data(show_spinner="Veri ve açıklama modeli hazırlanıyor...")
def analizi_yukle(girdi_yolu: str) -> dict[str, object]:
    """Ön işleme, Ridge katkıları ve standartlaştırılmış il mesafelerini üretir."""
    _, hedef_sutunu, secilenler, sayisal = veriyi_hazirla(Path(girdi_yolu))
    model_ozeti, katkilar, sonuc = modeli_calistir(
        sayisal=sayisal,
        hedef_sutunu=hedef_sutunu,
        secilenler=secilenler,
        model_turu="ridge",
        ridge_alpha=1.0,
    )
    ozellik_sutunlari = list(secilenler.values())
    standardize = StandardScaler()
    profil_vektorleri = standardize.fit_transform(sayisal[ozellik_sutunlari])
    iller = sayisal["İl"].to_numpy()
    farklar = profil_vektorleri[:, None, :] - profil_vektorleri[None, :, :]
    mesafeler = np.sqrt(np.sum(farklar**2, axis=2))
    return {
        "sayisal": sayisal,
        "hedef_sutunu": hedef_sutunu,
        "katkilar": katkilar,
        "model_ozeti": model_ozeti,
        "il_model_ozeti": sonuc["il_ozeti"],
        "metrikler": sonuc["metrikler"],
        "iller": iller,
        "mesafeler": mesafeler,
    }


@st.cache_data(show_spinner="Geçmiş gözlemler ve projeksiyon durumu yükleniyor...")
def atik_serisini_yukle(kaynak_yolu: str, projeksiyon_yolu: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """2020, 2022 ve 2024 gerçek hedef gözlemlerini ve 2027 durumunu okur."""
    kaynak = pd.read_csv(kaynak_yolu)
    if "REF_AREA" not in kaynak.columns:
        raise KeyError("Atık kaynağında REF_AREA sütunu bulunamadı.")
    kaynak["İl"] = kaynak["REF_AREA"].map(standart_il)
    records: list[dict[str, object]] = []
    for yil in YILLAR:
        sutun = HEDEF_SUTUNU.format(yil=yil)
        if sutun not in kaynak.columns:
            raise KeyError(f"Atık kaynağında '{sutun}' sütunu bulunamadı.")
        for _, satir in kaynak.dropna(subset=["İl"]).iterrows():
            records.append({"İl": satir["İl"], "Yıl": yil, "Kişi başı atık": float(satir[sutun])})
    gecmis = pd.DataFrame(records)

    if not Path(projeksiyon_yolu).exists():
        raise FileNotFoundError(f"Projeksiyon durumu bulunamadı: {projeksiyon_yolu}")
    projeksiyon = pd.read_csv(projeksiyon_yolu).rename(columns={"il": "İl"})
    gerekli = {
        "İl", "hedef_yil", "cikti_etiketi", "guvenilirlik", "yontem", "ufuk_yil",
        "dusuk_senaryo", "baz_senaryo", "yuksek_senaryo", "aralik_80_alt",
        "aralik_80_ust", "aralik_95_alt", "aralik_95_ust", "is_synthetic", "neden",
    }
    eksik = gerekli.difference(projeksiyon.columns)
    if eksik:
        raise KeyError(f"Projeksiyon dosyasında eksik sütunlar var: {sorted(eksik)}")
    return gecmis, projeksiyon


@st.cache_data(show_spinner="Uygulama örnekleri yükleniyor...")
def onerileri_yukle(dosya_yolu: str) -> pd.DataFrame:
    """Kaynaklı öneri tablosunu okur; metin üretmez veya değiştirmez."""
    oneriler = pd.read_csv(dosya_yolu)
    gerekli = {"yön", "örnek yer ve yıl", "ne yapıldı", "raporlanan sonuç", "kaynak bağlantısı", "kanıt düzeyi", "öneri uyarısı"}
    eksik = gerekli.difference(oneriler.columns)
    if eksik:
        raise KeyError(f"Öneri dosyasında eksik sütunlar var: {sorted(eksik)}")
    return oneriler


def karsilastirma_illerini_bul(iller: np.ndarray, mesafeler: np.ndarray, secili_il: str) -> tuple[str, str, float, float]:
    """Seçili ilin kendisi hariç en yakın ve en uzak ili döndürür."""
    secili_indeks = int(np.where(iller == secili_il)[0][0])
    uzakliklar = mesafeler[secili_indeks].copy()
    uzakliklar[secili_indeks] = np.nan
    yakin_indeks = int(np.nanargmin(uzakliklar))
    zit_indeks = int(np.nanargmax(uzakliklar))
    return iller[yakin_indeks], iller[zit_indeks], float(uzakliklar[yakin_indeks]), float(uzakliklar[zit_indeks])


def il_atik_degeri(il_model_ozeti: pd.DataFrame, il: str) -> float:
    return float(il_model_ozeti.loc[il_model_ozeti["İl"] == il, "Gerçek kişi başı atık"].iloc[0])


def il_karti(baslik: str, il: str, atik: float, ulusal_ortalama: float, uzaklik: float | None = None) -> None:
    st.subheader(baslik)
    st.markdown(f"### {il}")
    st.metric("Kişi başı toplanan atık", f"{atik:.2f}", f"Ulusal ortalamadan {atik - ulusal_ortalama:+.2f}")
    if uzaklik is None:
        st.caption("Seçilen ilin gerçek 2022 değeri")
    else:
        st.caption(f"Standartlaştırılmış Öklid mesafesi: {uzaklik:.2f}")


def main() -> None:
    st.set_page_config(page_title="İl Atık Profili", page_icon="♻️", layout="wide")
    st.markdown(
        """<style>
        .block-container {max-width: 1160px; padding-top: 2.3rem;}
        div[data-testid="stMetric"] {background: #f4f8f6; border-radius: 12px; padding: 14px;}
        </style>""",
        unsafe_allow_html=True,
    )
    st.title("İl Atık Profili")
    st.write(
        "Katkı analizi yalnızca gerçek 2022 açıklayıcı verisiyle hesaplanır. "
        "Geçmiş kişi başı atık değerleri 2020, 2022 ve 2024 için ayrıca gösterilir."
    )

    if not GIRDI.exists():
        st.error(f"Girdi dosyası bulunamadı: {GIRDI}")
        st.stop()
    analiz = analizi_yukle(str(GIRDI.resolve()))
    iller = sorted(analiz["iller"].tolist())
    varsayilan = iller.index("Sivas") if "Sivas" in iller else 0

    with st.sidebar:
        st.header("Seçim")
        secili_il = st.selectbox("İl", iller, index=varsayilan)
        st.caption("Mesafeler, modelde kullanılan sekiz açıklayıcı değişken standartlaştırıldıktan sonra hesaplanır.")
        st.caption(f"Ridge eğitim R²: {analiz['metrikler']['eğitim_R_kare']:.3f}. Bu değer tahmin performansı iddiası değildir.")

    if not ATIK_KAYNAGI.exists() or not PROJEKSIYON_DOSYASI.exists() or not ONERI_DOSYASI.exists():
        st.error("Geçmiş değer, projeksiyon durumu veya öneri dosyası bulunamadı.")
        st.stop()
    gecmis, projeksiyonlar = atik_serisini_yukle(str(ATIK_KAYNAGI.resolve()), str(PROJEKSIYON_DOSYASI.resolve()))
    oneriler = onerileri_yukle(str(ONERI_DOSYASI.resolve()))

    yakin_il, zit_il, yakin_mesafe, zit_mesafe = karsilastirma_illerini_bul(
        analiz["iller"], analiz["mesafeler"], secili_il
    )
    il_ozeti = analiz["il_model_ozeti"]
    ulusal_ortalama = float(il_ozeti["Gerçek kişi başı atık"].mean())
    secili_atik = il_atik_degeri(il_ozeti, secili_il)
    yakin_atik = il_atik_degeri(il_ozeti, yakin_il)
    zit_atik = il_atik_degeri(il_ozeti, zit_il)

    secili, yakin, zit = st.columns(3)
    with secili:
        il_karti("Seçilen il", secili_il, secili_atik, ulusal_ortalama)
    with yakin:
        il_karti("Benzer il", yakin_il, yakin_atik, ulusal_ortalama, yakin_mesafe)
    with zit:
        il_karti("Zıt il", zit_il, zit_atik, ulusal_ortalama, zit_mesafe)

    st.subheader(f"{secili_il} için geçmiş değerler ve 2027 projeksiyonu")
    secili_gecmis = gecmis[gecmis["İl"] == secili_il].sort_values("Yıl")
    gecmis_sutunlari = st.columns(4)
    for sutun, yil in zip(gecmis_sutunlari[:3], YILLAR):
        deger = float(secili_gecmis.loc[secili_gecmis["Yıl"] == yil, "Kişi başı atık"].iloc[0])
        with sutun:
            st.metric(f"{yil} gözlenen", f"{deger:.2f} kg/kişi-gün")
    durum = projeksiyonlar.loc[projeksiyonlar["İl"] == secili_il].iloc[0]
    with gecmis_sutunlari[3]:
        st.metric("2027 baz senaryo", f"{float(durum['baz_senaryo']):.2f} kg/kişi-gün")
    st.warning(
        "2027 sayıları güvenilmez göstergedir. Geriye dönük sınamada yöntem, "
        "son bilinen il değeri bazını geçemedi. Bu değer gerçek gözlem değildir."
    )
    senaryolar = pd.DataFrame({
        "Senaryo": ["Düşük", "Baz", "Yüksek"],
        "2027 kişi başı atık (kg/kişi-gün)": [
            float(durum["dusuk_senaryo"]),
            float(durum["baz_senaryo"]),
            float(durum["yuksek_senaryo"]),
        ],
        "%80 aralık": [
            f"{float(durum['aralik_80_alt']):.2f}–{float(durum['aralik_80_ust']):.2f}"
            for _ in range(3)
        ],
        "%95 aralık": [
            f"{float(durum['aralik_95_alt']):.2f}–{float(durum['aralik_95_ust']):.2f}"
            for _ in range(3)
        ],
    })
    st.dataframe(senaryolar, hide_index=True, width="stretch", column_config={
        "2027 kişi başı atık (kg/kişi-gün)": st.column_config.NumberColumn(format="%.2f"),
    })
    st.caption(
        f"Yöntem: {durum['yontem']}. Ufuk: {int(durum['ufuk_yil'])} yıl. "
        f"Çıktı is_synthetic={bool(durum['is_synthetic'])}."
    )
    st.caption(f"Gerekçe: {durum['neden']}")
    st.caption("Yalnızca 3 veri noktası kullanıldı. Aralıklar gösterilir; bu bir tahmin değildir.")

    katkilar = analiz["katkilar"]
    secili_katki = katkilar[katkilar["İl"] == secili_il].copy()
    secili_katki["Mutlak katkı"] = secili_katki["Katkı (standartlaştırılmış birim)"].abs()
    secili_katki = secili_katki.sort_values("Mutlak katkı", ascending=False)
    baskin_uc = secili_katki.head(3)["Değişken"].tolist()
    # İlk iki göreli katkı arasındaki fark %5 puandan küçükse ağırlıklar yakın sayılır.
    yakin_katki = (
        len(secili_katki) >= 2
        and abs(float(secili_katki.iloc[0]["Göreli katkı payı (%)"]) - float(secili_katki.iloc[1]["Göreli katkı payı (%)"])) < 5
    )
    st.info(il_sonuc_cumlesi(secili_il, secili_atik, ulusal_ortalama, baskin_uc, yakin_katki))
    st.caption(ILISKI_UYARISI)
    st.caption(EGITIM_VERISI_NOTU_SABLONU.format(il=secili_il))
    st.caption(KONAKLAMA_NOTU)

    st.subheader("İlişkili uygulama örnekleri")
    st.caption("Örnekler, seçili ilde en yüksek katkıya sahip değişkenlerle eşleştirilir. Bu eşleştirme etki kanıtı değildir.")
    for degisken in baskin_uc:
        yon_basligi = ONERI_ATAMALARI.get(degisken)
        if yon_basligi is None:
            continue
        eslesenler = oneriler[oneriler["yön"].astype(str).str.startswith(yon_basligi, na=False)]
        for _, oneri in eslesenler.iterrows():
            with st.expander(f"{degisken}: {oneri['örnek yer ve yıl']}", expanded=False):
                if oneri["örnek yer ve yıl"] == "kanıt bulunamadı":
                    st.write("Kanıt bulunamadı.")
                    continue
                st.write(f"Ne yapıldı: {oneri['ne yapıldı']}")
                st.write(f"Raporlanan sonuç: {oneri['raporlanan sonuç']}")
                st.markdown(f"Kaynak: [{oneri['kaynak türü']}]({oneri['kaynak bağlantısı']})")
                st.caption(str(oneri["öneri uyarısı"]))
                st.caption(f"Türkiye için bilinen engeller: {oneri['Türkiye için bilinen engeller']}")

    sol, sag = st.columns((1.15, 0.85))
    with sol:
        st.subheader("İlişkili faktörler")
        st.bar_chart(secili_katki.set_index("Değişken")["Katkı (standartlaştırılmış birim)"], horizontal=True)
        st.caption("Pozitif değerler model tahminini yükseltir, negatif değerler düşürür.")
    with sag:
        st.subheader("İl karşılaştırması")
        tablo = pd.DataFrame({
            "Rol": ["Seçilen", "Benzer", "Zıt"],
            "İl": [secili_il, yakin_il, zit_il],
            "Kişi başı atık": [secili_atik, yakin_atik, zit_atik],
            "Ulusal ortalamadan fark": [
                secili_atik - ulusal_ortalama,
                yakin_atik - ulusal_ortalama,
                zit_atik - ulusal_ortalama,
            ],
        })
        st.dataframe(tablo, hide_index=True, width="stretch", column_config={
            "Kişi başı atık": st.column_config.NumberColumn(format="%.2f"),
            "Ulusal ortalamadan fark": st.column_config.NumberColumn(format="%+.2f"),
        })

    st.subheader(f"{secili_il} için katkı ayrıntısı")
    st.dataframe(
        secili_katki[["Değişken", "Etki yönü", "Katkı (standartlaştırılmış birim)", "Göreli katkı payı (%)"]],
        hide_index=True,
        width="stretch",
        column_config={
            "Katkı (standartlaştırılmış birim)": st.column_config.NumberColumn(format="%+.3f"),
            "Göreli katkı payı (%)": st.column_config.NumberColumn(format="%.1f%%"),
        },
    )
    st.caption("Model, atık değeriyle hangi değişkenlerin ilişkili olduğunu görünür kılmak için kullanılır.")


if __name__ == "__main__":
    main()
