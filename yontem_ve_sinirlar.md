# Yöntem ve sınırlılıklar

## Sonuç

Geriye dönük sınama **geçmedi**. Kullanıcı isteğiyle 2027 için sayısal
senaryolar yayımlandı; durum: **güvenilmez**.

Gerekçe: İl bazlı doğrusal trend, 2024 holdout'unda son bilinen il değeri bazından daha düşük MAE üretmedi; bu baza göre bootstrap güven aralığı bütünüyle negatiftir.

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

| holdout_yili | yontem | MAE | RMSE |
| --- | --- | --- | --- |
| 2022 | son bilinen il değeri | 0.117607 | 0.157075 |
| 2022 | ulusal ortalama | 0.253606 | 0.309248 |
| 2024 | son bilinen il değeri | 0.094368 | 0.137313 |
| 2024 | ulusal ortalama | 0.194826 | 0.271945 |
| 2024 | il bazlı doğrusal trend | 0.196300 | 0.253728 |

## Aday yöntemin hata iyileşmesi

İyileşme = bazın mutlak hatası − aday yöntemin mutlak hatası. Pozitif değer
aday yöntemi destekler. Aralıklar, 81 il üzerinden sabit tohumlu 500
tekrarlı bootstrap ile %95 düzeyindedir.

| holdout_yili | aday_yontem | karsilastirma_bazi | MAE_iyilesmesi | bootstrap_%95_alt | bootstrap_%95_ust |
| --- | --- | --- | --- | --- | --- |
| 2024 | il bazlı doğrusal trend | son bilinen il değeri | -0.101932 | -0.130649 | -0.076027 |
| 2024 | il bazlı doğrusal trend | ulusal ortalama | -0.001474 | -0.057634 | 0.058276 |

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
