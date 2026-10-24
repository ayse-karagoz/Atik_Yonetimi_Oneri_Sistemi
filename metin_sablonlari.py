"""Kullanıcıya gösterilen, sabit Türkçe metin şablonları.

Bu modül üretken metin kullanmaz. Yalnızca önceden tanımlı kalıplara yer
tutucu değerler yerleştirir.
"""

from __future__ import annotations


IL_SONUC_SABLONU = (
    "{il} için kişi başı atık {atik:.2f} kg/kişi-gün; ulusal ortalamadan {fark:+.2f} kg/kişi-gün. "
    "Farkla en ilişkili değişkenler: {v1}, {v2}, {v3}."
)
YAKIN_KATKI_NOTU = "Birkaç değişken benzer ağırlıkta."
ILISKI_UYARISI = "Bu bir ilişkidir. Bir değişkenin diğerini oluşturduğunu göstermez."
PROJEKSIYON_UYARISI = (
    "Bu aralık yalnızca 3 veri noktasına dayanır. {alt:.2f}–{ust:.2f} kg/kişi-gün aralığı gösterilir; tahmin değildir."
)
ONERI_UYARISI_SABLONU = (
    "Bu uygulama başka yerlerde denenmiştir; bu ilde etkisi kesin değildir. "
    "Kanıt düzeyi: {kanit_duzeyi}. Karar kullanıcıya aittir."
)
KONAKLAMA_NOTU = "Yalnızca belediye belgeli tesisler; turizm yoğun illerde kapsam eksik olabilir."
EGITIM_VERISI_NOTU_SABLONU = "{il}, modelin eğitim verisindedir. Bu il için sonuç, eğitimdeki verilerden hesaplandı."


def il_sonuc_cumlesi(
    il: str,
    atik: float,
    ulusal_ortalama: float,
    degiskenler: list[str],
    katkilar_yakin: bool = False,
) -> str:
    """İl sonucu için sabit metni, en fazla üç değişkenle döndürür."""
    if len(degiskenler) < 3:
        raise ValueError("İl sonuç cümlesi için en az üç değişken gerekir.")
    metin = IL_SONUC_SABLONU.format(
        il=il,
        atik=atik,
        fark=atik - ulusal_ortalama,
        v1=degiskenler[0],
        v2=degiskenler[1],
        v3=degiskenler[2],
    )
    return f"{metin} {YAKIN_KATKI_NOTU}" if katkilar_yakin else metin


def projeksiyon_uyarisi(alt: float, ust: float) -> str:
    """Tek nokta içermeyen, sabit projeksiyon uyarısını döndürür."""
    return PROJEKSIYON_UYARISI.format(alt=alt, ust=ust)


def oneri_uyarisi(kanit_duzeyi: str) -> str:
    """Her öneri kaydında kullanılacak sabit uyarıyı döndürür."""
    return ONERI_UYARISI_SABLONU.format(kanit_duzeyi=kanit_duzeyi)


def egitim_verisi_notu(il: str) -> str:
    """Seçili ilin eğitim verisinde bulunduğunu açıkça belirtir."""
    return EGITIM_VERISI_NOTU_SABLONU.format(il=il)
