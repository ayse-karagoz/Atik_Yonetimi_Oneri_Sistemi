import json
import requests

# ==========================================
# AYARLAR
# ==========================================
API_KEY = "01a148d4-f8b9-7bba-8b0a-0c4d95da4a0b"
BASE_URL = "https://nsiws.tuik.gov.tr/rest"
TOKEN_URL = "https://giris.tuik.gov.tr/realms/web/protocol/openid-connect/token"

# 1. Otomatik Token Al
print("Token alınıyor...")
token_res = requests.post(
    TOKEN_URL,
    data={
        "grant_type": "password",
        "client_id": "nsi-ws-consumer",
        "api_key": API_KEY,
    },
)
token_data = token_res.json()
access_token = token_data.get("access_token")

if not access_token:
  print("❌ Token alınamadı, API Key'inizi kontrol edin:", token_data)
  exit()
print("✅ Token başarıyla alındı!\n")

# 2. Doğru Formatlı ID ile Veri Çekme
# Sizin bulduğunuz ID'yi API formatına (sonda virgül ve versiyon) uyarladık:
DATAFLOW_ID = "TR,DF_ATIK_BELEDIYE_HIZMET_V1,1"
data_url = f"{BASE_URL}/data/{DATAFLOW_ID}"

headers = {
    "Authorization": f"Bearer {access_token}",
    "Accept": "application/json",  # JSON formatında almak için
}

print(f"'{DATAFLOW_ID}' veri setinden il kırılımlı atık verileri çekiliyor...")
response = requests.get(data_url, headers=headers)

if response.status_code == 200:
  data = response.json()
  print("✅ Veri başarıyla çekildi!")

  # Dosyaya kaydetme
  with open("belediye_atik_verileri.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)
  print(
      "📁 Veriler başarıyla 'belediye_atik_verileri.json' dosyasına kaydedildi!"
  )
else:
  print(f"❌ Veri çekilemedi. Hata kodu: {response.status_code}")
  print(response.text)