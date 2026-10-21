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

from model_katki_analizi import modeli_calistir, veriyi_hazirla


GIRDI = Path("il_verileri_2022.csv")


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
    st.write("2022 il verisindeki ilişkileri, standartlaştırılmış özellikler ve Ridge regresyon katkılarıyla inceler.")

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

    katkilar = analiz["katkilar"]
    secili_katki = katkilar[katkilar["İl"] == secili_il].copy()
    secili_katki["Mutlak katkı"] = secili_katki["Katkı (standartlaştırılmış birim)"].abs()
    secili_katki = secili_katki.sort_values("Mutlak katkı", ascending=False)
    baskin_iki = secili_katki.head(2)["Değişken"].tolist()
    cümle = (
        f"Bu ilde kişi başı atık miktarının ulusal ortalamadan farklı olmasında en yüksek katkıya sahip "
        f"değişkenler sırasıyla {baskin_iki[0]} ve {baskin_iki[1]}'dir. "
        "Not: Bu bir ilişkidir, neden olduğu kanıtlanmamıştır."
    )
    st.info(cümle)

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
    st.caption("Model, tahmin yapmak için değil, gerçek atık değerinin hangi değişkenlerle ilişkili olduğunu görünür kılmak için kullanılır.")


if __name__ == "__main__":
    main()
