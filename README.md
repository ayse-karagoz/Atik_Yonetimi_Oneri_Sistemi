# İl Atık Profili ve Öneri Sistemi (Waste Management Recommendation System)

Bu uygulama, Türkiye genelindeki 81 ilin kişi başı belediye atık miktarlarını, sosyoekonomik, demografik ve turizm göstergeleriyle (standartlaştırılmış özellikler ve Ridge / Doğrusal regresyon katkıları) açıklayan ve karşılaştıran modern bir React SPA uygulamasıdır.

## Temel Özellikler

- **İl Bazlı Atık Analizi:** 81 il için kişi başı toplanan atık miktarı, ulusal ortalamadan fark ve model kestirimleri.
- **Benzer ve Zıt İl Eşleşmesi:** 8 açıklayıcı değişkenin standartlaştırılmış Öklid mesafesi üzerinden her il için en benzer ve en farklı (zıt) profil illeri.
- **İlişkili Faktörler & Katkı Ayrıştırması:** Değişkenlerin il bazındaki pozitif / negatif katkıları ve göreli katkı payları (%).
- **Baskın Faktör Uyarısı:** Her il için atık miktarındaki sapmayı en çok açıklayan ilk iki faktörün net caveats ile sunumu.
- **Çoklu Yıl Desteği:** 2020, 2022 ve 2024 resmi TÜİK ve Bakanlık verileri arasında anında geçiş.
- **Dinamik Model Parametreleri:** Ridge Regresyon (ayarlanabilir &alpha; parametresi) ve Standart Doğrusal Regresyon modelleri.
- **Türkiye Geneli ve Küresel Önem:** Küresel değişken ağırlıkları ve 81 ilin filtrelenebilir, sıralanabilir karşılaştırma matrisi.

## Kullanılan Açıklayıcı Değişkenler

1. Kişi başı GSYH
2. Ortalama hanehalkı büyüklüğü
3. Toplam nüfus
4. Yabancı nüfus
5. Konaklama tesise geliş sayısı
6. Konaklama geceleme sayısı
7. Konaklama doluluk oranı
8. Konaklama ortalama kalış süresi

## Geliştirme

```bash
npm install
npm run dev
```

Uygulama `http://0.0.0.0:3000` adresinde çalışır.
