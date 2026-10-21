import json
import os
import pandas as pd


def tuik_json_to_pivot_with_years(veri_klasoru="veri"):
  json_dosyasi = None
  if os.path.exists(veri_klasoru):
    for dosya in os.listdir(veri_klasoru):
      if dosya.endswith(".json"):
        json_dosyasi = os.path.join(veri_klasoru, dosya)
        break

  if not json_dosyasi:
    print(f"❌ '{veri_klasoru}' klasöründe hiç JSON dosyası bulunamadı!")
    return None

  print(f"📁 Okunan Dosya: {json_dosyasi}")

  with open(json_dosyasi, "r", encoding="utf-8") as f:
    raw_data = json.load(f)

  try:
    struct_sec = raw_data.get("structure")
    if not struct_sec and "data" in raw_data:
      s_list = raw_data["data"].get("structures", [])
      if s_list:
        struct_sec = s_list[0]

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

    ds = datasets.get(0) if isinstance(datasets, dict) else datasets[0]
    parsed_rows = []

    # Verileri Çöz
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

    if df.empty:
      print("⚠️ Çözülen veri tablosu boş.")
      return None

    print(f"✅ Ham veriden {len(df)} satır çözüldü.")

    # Sütun isimlerini kontrol edelim
    print(f"Mevcut Sütunlar: {df.columns.tolist()}")

    # İlgili kolon isimlerini dinamik bulalım
    il_kolonu = next(
        (
            c
            for c in df.columns
            if any(k in c.upper() for k in ["REF_AREA", "IL", "PROVINCE"])
        ),
        df.columns[0],
    )
    gosterge_kolonu = next(
        (
            c
            for c in df.columns
            if any(k in c.upper() for k in ["GOSTERGE", "INDICATOR", "MEASURE"])
        ),
        None,
    )
    yil_kolonu = next(
        (
            c
            for c in df.columns
            if any(k in c.upper() for k in ["TIME_PERIOD", "YIL", "YEAR"])
        ),
        None,
    )

    print(
        f"Seçilen -> İl: {il_kolonu}, Gösterge: {gosterge_kolonu}, Yıl:"
        f" {yil_kolonu}"
    )

    # Değerleri sayısal yap
    df["Deger"] = pd.to_numeric(
        df["Deger"].astype(str).str.replace(",", "."), errors="coerce"
    )

    # Eğer yıl kolonu varsa, pivot işleminde sütunlara hem göstergeyi hem yılı yansıtalım
    if yil_kolonu and gosterge_kolonu:
      # Gösterge ve Yılı birleştirerek benzersiz sütun isimleri elde edelim
      df["Kriter_Yil"] = (
          df[gosterge_kolonu].astype(str) + " (" + df[yil_kolonu].astype(str) + ")"
      )

      pivot_df = df.pivot_table(
          index=il_kolonu, columns="Kriter_Yil", values="Deger", aggfunc="sum"
      )
    elif gosterge_kolonu:
      pivot_df = df.pivot_table(
          index=il_kolonu,
          columns=gosterge_kolonu,
          values="Deger",
          aggfunc="sum",
      )
    else:
      pivot_df = df

    # Düzleştir
    if isinstance(pivot_df, pd.DataFrame):
      pivot_df.columns = [str(col) for col in pivot_df.columns]
      pivot_df = pivot_df.reset_index()

    return pivot_df

  except Exception as e:
    print(f"❌ Hata: {e}")
    import traceback

    traceback.print_exc()
    return None


# Çalıştır ve Kaydet
df_final = tuik_json_to_pivot_with_years()

if df_final is not None and not df_final.empty:
  print("\n--- Oluşan Final Tablo İlk Görünüm ---")
  print(df_final.head())

  os.makedirs("veri", exist_ok=True)
  output_excel = "veri/belediye_atik_yillara_gore.xlsx"
  output_csv = "veri/belediye_atik_yillara_gore.csv"

  try:
    df_final.to_excel(output_excel, index=False)
    print(f"\n💾 Excel olarak kaydedildi: {output_excel}")
  except:
    df_final.to_csv(output_csv, index=False, encoding="utf-8-sig")
    print(f"\n💾 CSV olarak kaydedildi: {output_csv}")
else:
  print("❌ Tablo oluşturulamadı.")