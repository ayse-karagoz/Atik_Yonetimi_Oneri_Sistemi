import pandas as pd

# Kaydettiğimiz temiz CSV'yi okuyalım
df = pd.read_csv("veri/belediye_atik_yillara_gore.csv")

# Tabloda hangi sütunlar ve kategoriler var bakalım
print("Tablodaki Sütunlar:", df.columns.tolist())

# Eğer veri setinde gösterge/ölçüt belirten bir sütun varsa benzersiz değerleri görelim:
# (Genellikle Indicator, Measure veya benzeri bir sütun adıyla geçer)
for col in df.columns:
  if df[col].dtype == "object":
    print(f"\nSütun '{col}' içindeki bazı benzersiz değerler:")
    print(df[col].unique()[:10])