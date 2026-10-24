# Veri Kartı — İstanbul su güvenliği karar destek prototipi

Bu kart yalnızca `veri/` altındaki mevcut kaynakların envanteridir. Kaynak URL'si,
indirme zamanı veya ölçü birimi dosyada ya da proje içindeki alma betiklerinde
kanıtlanamıyorsa **BILINMIYOR** olarak bırakılmıştır. Hiçbir dosya sentetik olarak
etiketlenmemiştir; bunun gerçek veri olduğu sonucuna varılamaz.

## Ortak sınırlar

- İncelenen an: 24 Ekim 2026. Veri son dönemi dosyaya göre 2024 veya 2025'tir.
- Tüm dosyalarda `is_synthetic` sütunu eksik. Bu nedenle sentetik ve gerçek
  kayıtların ayrımı **BILINMIYOR**; bu veri, tahmin doğruluk metriği için
  kullanılmadan önce düzeltilmelidir.
- Tarih alanlarının tamamı yıllık ya da yıl-başlıklı. Günlük seri bulunmadığından
  “eksik gün” ölçüsü **BILINMIYOR**; yıllık dönem boşlukları sözleşmede ayrıca
  belirtilir.
- Aykırı değer sayısı, sayısal hücrelerde sütun bazında IQR (Q1−1,5×IQR,
  Q3+1,5×IQR) kuralıyla üretilmiş bir uyarıdır. Aykırı değer hata veya sentetik
  veri kanıtı değildir.

## Kaynak setleri

| Dosya | Kaynak | Tanım | Son yayın/güncelleme | Bilinen sorunlar |
|---|---|---|---|---|
| `belediye_atik_yillara_gore.csv` | Projedeki `veri_cekme/il_kirilimli_atık.py`, TÜİK NSI web hizmeti ve `TR,DF_ATIK_BELEDIYE_HIZMET_V1,1` akışını işaret ediyor; özgün indirme tarihi/URL'si **BILINMIYOR**. | İl bazında belediye atığı ve hizmet kapsamı göstergeleri; 2020, 2022, 2024. | **BILINMIYOR** | 2021 ve 2023 dönemleri yok; birim alanı yok; 82 satır (81 il beklentisine göre fazladan satırın kimliği doğrulanmalı); `is_synthetic` yok. |
| `belediye_belgeli_konaklama_2020.xlsx` | Dosya başlığı dışında kaynak **BILINMIYOR**. | İl/ilçe düzeyinde belediye belgeli konaklama tesise geliş, geceleme, kalış süresi ve doluluk oranı; 2020. | **BILINMIYOR** | Birimler yalnızca doluluk başlığında `%` olarak açık; il hücreleri birleştirilmiş; `is_synthetic` yok. |
| `belediye_belgeli_konaklama_2022.xlsx` | Dosya başlığı dışında kaynak **BILINMIYOR**. | İl/ilçe düzeyinde belediye belgeli konaklama göstergeleri; 2022. | **BILINMIYOR** | Birimler yalnızca doluluk başlığında `%` olarak açık; il hücreleri birleştirilmiş; `is_synthetic` yok. |
| `kentsel_kirsal_nufus_temiz.csv` | Projedeki TÜİK NSI alma betikleri kaynak işaretidir; bu dosyanın özgün akış kimliği/indirme kaydı **BILINMIYOR**. | Kentsel ve kırsal nüfus kırılımları; 2022–2025. | Dosya içeriğinde yayın tarihi yok: **BILINMIYOR**. | Birim alanı yok; 2020 için kaynak yok; `is_synthetic` yok. |
| `kisi_basi_gshy_temiz.csv` | Dosya alanlarında `YAYIN_TUIK` bulunuyor; özgün veri akışı/URL **BILINMIYOR**. | Cari fiyatlarla kişi başı GSYH kırılımları; 2000–2024. | İçerikte `YAYIM_DONEMI = January 2026` görülüyor; dosyanın indirme tarihi **BILINMIYOR**. | Değerin birimi satır bazında `Turkish lira` veya `US dollar`; tek bir birim yok. `is_synthetic` yok. |
| `nufus_2020.csv` | TÜİK NSI alma betikleri kaynak işaretidir; özgün indirme kaydı **BILINMIYOR**. | ADNKS nüfus gözlemleri, 2020. | **BILINMIYOR** | `UNIT_MEASURE` ve ilgili açıklama alanları boş; dosya başlığı noktalı virgülle ayrılmış; `is_synthetic` yok. |
| `nufus_2022.csv` | TÜİK NSI alma betikleri kaynak işaretidir; özgün indirme kaydı **BILINMIYOR**. | ADNKS nüfus gözlemleri, 2022. | **BILINMIYOR** | Birim alanları boş; noktalı virgül ayracı; `is_synthetic` yok. |
| `nufus_2024.csv` | TÜİK NSI alma betikleri kaynak işaretidir; özgün indirme kaydı **BILINMIYOR**. | ADNKS nüfus gözlemleri, 2024. | **BILINMIYOR** | Birim alanları boş; noktalı virgül ayracı; `is_synthetic` yok. |
| `yabanci_nufus.csv` | `veri_cekme/veri_cek.py` TÜİK NSI `TR,DF_ADNKS_T12,1.1` akışını işaret ediyor. Özgün indirme zamanı **BILINMIYOR**. | ADNKS yabancı nüfus kırılımları; 2007–2025. | Dosya içinde yayın tarihi yok: **BILINMIYOR**. | Birim alanı yok; `is_synthetic` yok. |
| `İllere Göre Ortalama Hanehalkı Büyüklüğü (TR,DF_ADNKS_T25,1.1).csv` | Dosya adındaki akış kimliği ve TÜİK NSI alma betikleri TÜİK kaynağını işaret ediyor; özgün indirme kaydı **BILINMIYOR**. | İl düzeyinde ortalama hanehalkı büyüklüğü; 2008–2025. | **BILINMIYOR** | Birim alanları boş; noktalı virgül ayracı ve virgüllü ondalıklar; `is_synthetic` yok. |

## Modelleme için kullanım kararı

Bu envanterin mevcut hâliyle sentetik/gerçek ayrımı kanıtlanmadığından doğruluk
metriği hesaplanmamalıdır. Her kaynak sahibinden birim, özgün kaynak URL'si,
indirme tarihi ve `is_synthetic=false` beyanı doğrulanmadan 2027 tahmininin
başarı ölçümü yapılmamalıdır.

Birleştirme betiği çalıştırıldığında üretilen yıl dosyalarında satır düzeyinde
etiket uygulanır: `il_verileri_2022.csv` içindeki 81 satır `false` olarak
kalır; 2024'te belediye belgeli konaklama 2020–2022 eğiliminden üretildiği için
81 satır `true` olur. Ayrıca betikte 2020 kentsel/kırsal nüfus da 2022–2024
eğiliminden geriye üretildiğinden 2020'nin 81 satırı `true` olur. Bu ikinci
sentetik seri, kullanıcı tarafından ayrıca belirtilmemiş olsa da betikteki
üretim kuralı nedeniyle gerçek olarak işaretlenemez.
