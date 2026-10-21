import json
import os
import requests
import pandas as pd


def tuik_api_to_dataframe(dataflow_id, api_key):
  """TÜİK API altyapısından belirtilen Dataflow ID'sine ait verileri çeker

  ve pandas DataFrame'e dönüştürür.
  """
  base_url = "https://nsiws.tuik.gov.tr/rest"
  token_url = "https://giris.tuik.gov.tr/realms/web/protocol/openid-connect/token"

  print(f"🔑 Token alınıyor...")
  token_res = requests.post(
      token_url,
      data={
          "grant_type": "password",
          "client_id": "nsi-ws-consumer",
          "api_key": api_key,
      },
  )

  if token_res.status_code != 200:
    print(
        f"❌ Token alınamadı! Hata Kodu: {token_res.status_code} -"
        f" {token_res.text}"
    )
    return None

  access_token = token_res.json().get("access_token")
  if not access_token:
    print("❌ Token üretilemedi!")
    return None

  print(f"✅ Token alındı. '{dataflow_id}' veri akışı indiriliyor...")

  # Veri akışını API'den çek (En güncel veriler)
  headers = {
      "Authorization": f"Bearer {access_token}",
      "Accept": "application/json",
  }
  url = f"{base_url}/data/{dataflow_id}/all?detail=full"
  response = requests.get(url, headers=headers)

  if response.status_code != 200:
    print(
        f"❌ Veri indirilemedi! Hata Kodu: {response.status_code} -"
        f" {response.text}"
    )
    return None

  raw_data = response.json()
  print("✅ Veri başarıyla indirildi, işleniyor...")

  try:
    # SDMX-JSON yapı ve boyutlarını çözme
    struct_sec = raw_data.get("structure")
    if not struct_sec and "data" in raw_data:
      s_list = raw_data["data"].get("structures", [])
      if s_list:
        struct_sec = s_list[0]

    if not struct_sec:
      print("⚠️ Yapı (Structure) alanı bulunamadı.")
      return None

    dims = struct_sec.get("dimensions", {})
    series_dims = dims.get("series", [])
    obs_dims = dims.get("observation", [])

    s_names = [d.get("id") for d in series_dims]
    s_vals = [
        [v.get("name", v.get("id")) for v in d.get("values", [])]
        for d in series_dims
    ]

    o_names = [d.get("id") for d in obs_dims]
    o_vals = [
        [v.get("name", v.get("id")) for v in d.get("values", [])]
        for d in obs_dims
    ]

    datasets = raw_data.get("dataSets", [])
    if not datasets and "data" in raw_data:
      datasets = raw_data["data"].get("dataSets", [])

    if not datasets:
      print("⚠️ 'dataSets' bulunamadı.")
      return None

    ds = datasets.get(0) if isinstance(datasets, dict) else datasets[0]
    parsed_rows = []

    # Seri bazlı yapıyı çöz
    if "series" in ds:
      for s_key, s_content in ds["series"].items():
        s_indices = [int(i) for i in s_key.split(":")]
        row_info = {}
        for idx, val_idx in enumerate(s_indices):
          if idx < len(s_names):
            row_info[s_names[idx]] = s_vals[idx][val_idx]

        obs_dict = s_content.get("observations", {})
        for o_key, val_list in obs_dict.items():
          o_indices = [int(i) for i in o_key.split(":")]
          row_data = row_info.copy()
          for idx, val_idx in enumerate(o_indices):
            if idx < len(o_names):
              row_data[o_names[idx]] = o_vals[idx][val_idx]

          row_data["Deger"] = val_list[0] if isinstance(val_list, list) else val_list
          parsed_rows.append(row_data)

    df = pd.DataFrame(parsed_rows)
    print(f"✅ İşlem tamamlandı! Toplam Satır Sayısı: {len(df)}")
    return df

  except Exception as e:
    print(f"❌ Veri işlenirken hata oluştu: {e}")
    import traceback

    traceback.print_exc()
    return None


# ==========================================
# KULLANIM ÖRNEĞİ:
# ==========================================
if __name__ == "__main__":
  API_KEY = "01a148d4-f8b9-7bba-8b0a-0c4d95da4a0b"
  HEDEF_DATAFLOW = "TR,DF_ADNKS_T12,1.1"

  # Fonksiyonu çağırarak veriyi çekiyoruz
  df_nufus = tuik_api_to_dataframe(HEDEF_DATAFLOW, API_KEY)

if df_nufus is not None and not df_nufus.empty:
  print("\n--- Çekilen Nüfus Verisi İlk 5 Satır ---")
  print(df_nufus.head())
  
  # Temizlenmiş CSV olarak kaydet
  df_nufus.to_csv("veri/yabanci_nufus.csv", index=False, encoding="utf-8-sig")
  print("\n💾 Dosya 'veri/kentsel_kirsal_nufus_temiz.csv' olarak kaydedildi.")