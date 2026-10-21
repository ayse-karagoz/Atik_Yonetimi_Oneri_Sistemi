import requests

# ==========================================
# AYARLAR (Kendi API Key'inizi buraya yazın)
# ==========================================
API_KEY = "BURAYA_TÜİK_PORTALINDAN_ALDIĞINIZ_API_KEY_YAZIN"
BASE_URL = "https://nsiws.tuik.gov.tr/rest"
TOKEN_URL = "https://giris.tuik.gov.tr/realms/web/protocol/openid-connect/token"

print("🔑 Token alınıyor...")
token_res = requests.post(
    TOKEN_URL,
    data={
        "grant_type": "password",
        "client_id": "nsi-ws-consumer",
        "api_key": API_KEY,
    },
)

if token_res.status_code != 200:
  print(f"❌ Kimlik doğrulama başarısız! Hata Kodu: {token_res.status_code}")
  print(f"Detay: {token_res.text}")
  exit()

access_token = token_res.json().get("access_token")
print("✅ Token başarıyla alındı!")

headers = {
    "Authorization": f"Bearer {access_token}",
    "Accept": "application/json",
}

# Doğrudan dataflow servisini sorgulayalım
response = requests.get(f"{BASE_URL}/dataflow/TR/all/latest", headers=headers)

if response.status_code == 200:
  data = response.json()

  # Farklı JSON yapılarına karşı esnek arama
  dataflows = []
  if isinstance(data, list):
    dataflows = data
  elif isinstance(data, dict):
    # SDMX yapısına göre olası anahtarları kontrol et
    for key in ["dataflows", "dataflow", "resources"]:
      if key in data:
        val = data[key]
        if isinstance(val, list):
          dataflows = val
          break
        elif isinstance(val, dict) and "dataflows" in val:
          dataflows = val["dataflows"]
          break

  print(f"📊 Toplam {len(dataflows)} veri akışı bulundu. Taranıyor...\n")

  bulunan_sayisi = 0
  for df in dataflows:
    if not isinstance(df, dict):
      continue

    df_id = df.get("id", "")
    agency = df.get("agencyID", "TR")
    version = df.get("version", "1.0")

    # İsim alanını güvenli alalım
    names = df.get("names", df.get("name", {}))
    if isinstance(names, dict):
      name_str = " | ".join(str(v) for v in names.values())
    else:
      name_str = str(names)

    # Nüfus, adnks veya bölgesel kelimelerini filtrele
    if any(
        k in name_str.lower()
        for k in ["nüfus", "nufus", "population", "adnks", "ilçe", "gdp", "hasıla"]
    ):
      bulunan_sayisi += 1
      print(f"🎯 ID: {agency},{df_id},{version}")
      print(f"   Açıklama: {name_str}")
      print("-" * 60)

  if bulunan_sayisi == 0:
    print(
        "⚠️ Filtreye uygun akış bulunamadı. İlk 5 ham akış başlığı yazdırılıyor:"
    )
    for df in dataflows[:5]:
      print(df.get("id"), "->", df.get("names", df.get("name")))
else:
  print(f"❌ Veri akışları çekilemedi. Hata Kodu: {response.status_code}")