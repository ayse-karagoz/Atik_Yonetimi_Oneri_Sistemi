#!/usr/bin/env python3
"""`veri/` altındaki kaynak dosyalarını değiştirmeden doğrular.

Kullanım:
    .venv/bin/python validate_data.py
    .venv/bin/python validate_data.py --data-dir veri

Betik sentetik sütunu eksikse eklemez. Bu durum, modelleme öncesinde
giderilmesi gereken bir hata olarak raporlanır.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


UNKNOWN = "BILINMIYOR"
SUPPORTED_SUFFIXES = {".csv", ".xls", ".xlsx"}
YEAR_RE = re.compile(r"(?<!\d)((?:19|20)\d{2})(?!\d)")
DATE_COLUMN_TOKENS = ("time_period", "time period", "zaman", "date", "tarih")
UNIT_COLUMN_TOKENS = ("unit_measure", "ölçü birimi", "olcu birimi", "unit")
EXCLUDED_NUMERIC_TOKENS = ("year", "yıl", "yil", "decimal", "ondalık", "unit_mult", "birim çarpanı")


@dataclass
class Finding:
    level: str
    code: str
    message: str


def normalise(value: object) -> str:
    value = unicodedata.normalize("NFKD", str(value)).strip().lower()
    value = "".join(char for char in value if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", value)


def sniff_delimiter(path: Path, encoding: str = "utf-8-sig") -> str:
    with path.open("r", encoding=encoding, errors="replace", newline="") as source:
        sample = source.read(16_384)
    try:
        return csv.Sniffer().sniff(sample, delimiters=";,\t|").delimiter
    except csv.Error:
        return ";" if sample.count(";") > sample.count(",") else ","


def read_csv(path: Path) -> pd.DataFrame:
    last_error: Exception | None = None
    for encoding in ("utf-8-sig", "utf-8", "cp1254", "latin1"):
        try:
            return pd.read_csv(path, sep=sniff_delimiter(path, encoding), encoding=encoding, dtype="string")
        except (UnicodeDecodeError, pd.errors.ParserError) as error:
            last_error = error
    raise ValueError(f"CSV okunamadı: {last_error}")


def unique_names(values: list[str]) -> list[str]:
    seen: dict[str, int] = {}
    result: list[str] = []
    for value in values:
        value = value or "BOS"
        seen[value] = seen.get(value, 0) + 1
        result.append(value if seen[value] == 1 else f"{value}_{seen[value]}")
    return result


def read_excel(path: Path) -> pd.DataFrame:
    """İki satırlı turizm başlıklarını tek satıra indirger."""
    raw = pd.read_excel(path, sheet_name=0, header=None, dtype="string")
    header_row = next(
        (
            index
            for index, row in raw.iterrows()
            if {"iller", "il"}.intersection({normalise(value) for value in row.dropna()})
        ),
        None,
    )
    if header_row is None:
        raise ValueError("Excel dosyasında il/iller başlık satırı bulunamadı.")

    first = raw.iloc[header_row].fillna("").astype(str).str.strip()
    second = raw.iloc[header_row + 1].fillna("").astype(str).str.strip()
    # İkinci satırda il adı bulunması onun veri satırı olduğunu gösterir.
    province_examples = {"adana", "adiyaman", "afyonkarahisar"}
    is_two_row_header = not any(normalise(value) in province_examples for value in second)
    if is_two_row_header:
        first = first.replace("", pd.NA).ffill().fillna("")
        columns = ["_".join(part for part in (top, bottom) if part) for top, bottom in zip(first, second)]
        frame = raw.iloc[header_row + 2 :].copy()
    else:
        columns = first.tolist()
        frame = raw.iloc[header_row + 1 :].copy()
    frame.columns = unique_names([str(value) for value in columns])
    return frame.reset_index(drop=True)


def read_file(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".csv":
        return read_csv(path)
    return read_excel(path)


def to_number(values: pd.Series) -> pd.Series:
    if pd.api.types.is_numeric_dtype(values):
        return pd.to_numeric(values, errors="coerce")
    text = values.astype("string").str.strip().str.replace("\u00a0", "", regex=False)
    both_separators = text.str.contains(".", regex=False, na=False) & text.str.contains(",", regex=False, na=False)
    text.loc[both_separators] = (
        text.loc[both_separators].str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
    )
    text.loc[~both_separators] = text.loc[~both_separators].str.replace(",", ".", regex=False)
    return pd.to_numeric(text, errors="coerce")


def numeric_measure_columns(frame: pd.DataFrame) -> list[str]:
    columns: list[str] = []
    for column in frame.columns:
        name = normalise(column)
        if any(token in name for token in EXCLUDED_NUMERIC_TOKENS):
            continue
        non_null = frame[column].dropna()
        if len(non_null) and to_number(frame[column]).notna().sum() / len(non_null) >= 0.99:
            columns.append(str(column))
    return columns


def find_years(frame: pd.DataFrame, path: Path) -> list[int]:
    years = {int(value) for value in YEAR_RE.findall(path.stem)}
    for column in frame.columns:
        name = normalise(column)
        if any(token in name for token in DATE_COLUMN_TOKENS) and not any(
            token in name for token in ("dogum", "doğum", "baz")
        ):
            values = to_number(frame[column]).dropna()
            years.update(int(value) for value in values if 1900 <= value <= 2100 and float(value).is_integer())
        years.update(int(value) for value in YEAR_RE.findall(str(column)))
    return sorted(years)


def has_daily_dates(frame: pd.DataFrame) -> bool:
    for column in frame.columns:
        if any(token in normalise(column) for token in ("date", "tarih")):
            parsed = pd.to_datetime(frame[column], errors="coerce")
            if parsed.notna().any():
                return True
    return False


def validate_units(frame: pd.DataFrame, measures: list[str], file_name: str) -> list[Finding]:
    if not measures:
        return []
    unit_columns = [
        str(column)
        for column in frame.columns
        if any(token in normalise(column) for token in UNIT_COLUMN_TOKENS)
        and "mult" not in normalise(column)
        and "carpan" not in normalise(column)
    ]
    populated = [column for column in unit_columns if frame[column].astype("string").str.strip().notna().any()]
    percent_in_headers = any("%" in column or "oran" in normalise(column) for column in measures)
    if populated or percent_in_headers:
        return []
    return [Finding(
        "HATA", "BIRIM_BILINMIYOR",
        f"{file_name}: sayısal ölçüler var ancak kaynakta dolu bir birim alanı veya açık yüzde işareti yok. "
        f"Sözleşmede birim {UNKNOWN} olarak kalmalıdır.",
    )]


def validate_dates(frame: pd.DataFrame, path: Path) -> list[Finding]:
    years = find_years(frame, path)
    if not years:
        return [Finding("HATA", "TARIH_BULUNAMADI", f"{path.name}: dönem/tarih alanı tespit edilemedi.")]
    findings: list[Finding] = []
    if has_daily_dates(frame):
        # Günlük seri varsa ardışık takvim günleri üzerinden boşluk aranır.
        for column in frame.columns:
            if not any(token in normalise(column) for token in ("date", "tarih")):
                continue
            dates = pd.to_datetime(frame[column], errors="coerce").dropna().dt.normalize().drop_duplicates().sort_values()
            if len(dates) > 1:
                missing = len(pd.date_range(dates.iloc[0], dates.iloc[-1], freq="D")) - len(dates)
                if missing:
                    findings.append(Finding("HATA", "TARIH_BOSLUGU", f"{path.name}: {missing} eksik takvim günü bulundu."))
        return findings

    expected = set(range(years[0], years[-1] + 1))
    missing = sorted(expected.difference(years))
    if missing:
        findings.append(Finding(
            "HATA", "YILLIK_DONEM_BOSLUGU",
            f"{path.name}: yıllık dönemlerde boşluk var: {', '.join(map(str, missing))}. Günlük eksik sayısı hesaplanamaz.",
        ))
    else:
        findings.append(Finding(
            "BILGI", "GUNLUK_SERI_YOK",
            f"{path.name}: yıllık dönem tespit edildi ({years[0]}–{years[-1]}); günlük eksik sayısı {UNKNOWN}.",
        ))
    return findings


def validate_values(frame: pd.DataFrame, measures: list[str], file_name: str) -> list[Finding]:
    findings: list[Finding] = []
    for column in measures:
        numbers = to_number(frame[column])
        negatives = int((numbers < 0).sum())
        if negatives:
            findings.append(Finding("HATA", "NEGATIF_DEGER", f"{file_name}: '{column}' içinde {negatives} negatif değer var."))
        name = normalise(column)
        if "%" in column or "oran" in name or "rate" in name or "doluluk" in name:
            impossible = int(((numbers < 0) | (numbers > 100)).sum())
            if impossible:
                findings.append(Finding(
                    "HATA", "IMKANSIZ_ORAN",
                    f"{file_name}: '{column}' içinde 0–100 aralığı dışında {impossible} oran değeri var.",
                ))
    return findings


def validate_synthetic_marker(frame: pd.DataFrame, file_name: str) -> list[Finding]:
    matches = [column for column in frame.columns if normalise(column) == "is_synthetic"]
    if not matches:
        return [Finding(
            "HATA", "IS_SYNTHETIC_EKSIK",
            f"{file_name}: 'is_synthetic' sütunu yok. Dosya değiştirilmedi; sentetik/gerçek ayrımı BILINMIYOR.",
        )]
    column = matches[0]
    values = frame[column].astype("string").str.strip().str.lower()
    valid = {"true", "false", "1", "0"}
    invalid = values.notna() & ~values.isin(valid)
    if invalid.any():
        return [Finding(
            "HATA", "IS_SYNTHETIC_GECERSIZ",
            f"{file_name}: 'is_synthetic' sütununda {int(invalid.sum())} geçersiz değer var; yalnızca true/false kabul edilir.",
        )]
    has_synthetic = values.isin({"true", "1"}).any()
    has_real = values.isin({"false", "0"}).any()
    if has_synthetic and has_real:
        return [Finding(
            "HATA", "SENTETIK_GERCEK_KARISIMI",
            f"{file_name}: sentetik ve gerçek satırlar aynı dosyada karışık. Modelleme öncesinde ayrı veri kümelerine bölün.",
        )]
    return []


def validate_file(path: Path) -> list[Finding]:
    try:
        frame = read_file(path)
    except Exception as error:  # Kullanıcıya dosya bazında açık hata verilir.
        return [Finding("HATA", "OKUMA_HATASI", f"{path.name}: okunamadı ({type(error).__name__}: {error}).")]
    measures = numeric_measure_columns(frame)
    findings = validate_units(frame, measures, path.name)
    findings.extend(validate_dates(frame, path))
    findings.extend(validate_values(frame, measures, path.name))
    findings.extend(validate_synthetic_marker(frame, path.name))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Veri sözleşmesi öncesi kaynak veri denetimi")
    parser.add_argument("--data-dir", type=Path, default=Path("veri"), help="CSV/XLS/XLSX kaynaklarının klasörü")
    args = parser.parse_args()
    if not args.data_dir.is_dir():
        print(f"HATA [VERI_KLASORU_YOK] {args.data_dir} klasörü bulunamadı.")
        return 2

    files = sorted(path for path in args.data_dir.iterdir() if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES)
    if not files:
        print(f"HATA [VERI_DOSYASI_YOK] {args.data_dir} içinde desteklenen veri dosyası yok.")
        return 2

    all_findings: list[Finding] = []
    for path in files:
        print(f"\n--- {path.name} ---")
        findings = validate_file(path)
        all_findings.extend(findings)
        for finding in findings:
            print(f"{finding.level} [{finding.code}] {finding.message}")

    errors = sum(finding.level == "HATA" for finding in all_findings)
    print(f"\nÖzet: {len(files)} dosya tarandı, {errors} hata bulundu.")
    if errors:
        print("Doğrulama başarısız. Dosyalar değiştirilmedi.")
        return 1
    print("Doğrulama başarılı.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
