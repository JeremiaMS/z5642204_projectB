"""Risk-free benchmark for Part B: Kenneth French daily RF and the cash series.

The daily RF comes from the Kenneth French data library (Week 5 approach):
download the factors zip, keep only RF, scale percent to decimal. The raw zip
is written to a system temp path only and never enters the repo.
"""
from __future__ import annotations

import csv
import io
import os
import tempfile
import zipfile
from pathlib import Path

import pandas as pd
import requests

FRENCH_FACTORS_URL = (
    "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
    "F-F_Research_Data_Factors_daily_CSV.zip"
)


def fetch_french_factors_zip(url: str = FRENCH_FACTORS_URL,
                             timeout_seconds: int = 60) -> bytes:
    """Download the zipped Kenneth French daily factors file."""
    response = requests.get(url, timeout=timeout_seconds)
    response.raise_for_status()
    return response.content


def extract_first_csv_text(zip_path: Path) -> str:
    """Read the first CSV member from the zip at zip_path."""
    with zipfile.ZipFile(zip_path) as archive:
        csv_members = [name for name in archive.namelist()
                       if name.lower().endswith(".csv")]
        if not csv_members:
            raise ValueError("Kenneth French zip file did not contain a CSV member.")
        with archive.open(csv_members[0]) as handle:
            return handle.read().decode("utf-8-sig")


def parse_french_daily_rfr(csv_text: str) -> pd.DataFrame:
    """Keep only the daily RF series, scaled from percent to decimal.

    Returns a DataFrame with columns date and rf_daily, sorted by date.
    """
    rows: list[tuple[pd.Timestamp, float]] = []
    reader = csv.reader(io.StringIO(csv_text))
    for row in reader:
        if not row:
            continue
        date_token = row[0].strip()
        if len(date_token) != 8 or not date_token.isdigit():
            continue
        if len(row) < 5:
            continue
        rf_text = row[-1].strip()
        if not rf_text:
            continue
        rows.append((pd.to_datetime(date_token, format="%Y%m%d"),
                     float(rf_text) / 100.0))
    if not rows:
        raise ValueError("No daily Kenneth French RF rows were found.")

    frame = pd.DataFrame(rows, columns=["date", "rf_daily"])
    frame["date"] = pd.to_datetime(frame["date"])
    frame["rf_daily"] = frame["rf_daily"].astype(float)
    return frame.sort_values("date").reset_index(drop=True)


def download_risk_free(url: str = FRENCH_FACTORS_URL,
                       timeout_seconds: int = 60) -> pd.DataFrame:
    """Download the daily RF and parse it, keeping the raw zip out of the repo.

    The raw zip is written to a system temp path, read once for parsing, then
    deleted. It never enters the repo, so it cannot be committed.
    """
    zip_bytes = fetch_french_factors_zip(url, timeout_seconds)
    fd, raw_path = tempfile.mkstemp(suffix=".zip", prefix="french_factors_")
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(zip_bytes)
        return parse_french_daily_rfr(extract_first_csv_text(Path(raw_path)))
    finally:
        Path(raw_path).unlink(missing_ok=True)


def cash_benchmark(rf: pd.DataFrame, start, end) -> pd.DataFrame:
    """Growth of one dollar in cash over [start, end].

    Only dates that actually have a French RF reading are kept (business
    days), so no weekend rate is ever invented. Row one is 1 plus the first
    daily rate; each later row multiplies the running value by 1 plus rf.
    """
    daily = rf.set_index("date")["rf_daily"].loc[start:end].dropna()
    if len(daily) == 0:
        raise ValueError("No risk free readings inside the requested range.")
    growth = (1.0 + daily).cumprod()
    return pd.DataFrame({"date": growth.index, "cash_growth": growth.values})


def annualised_cash_return(cash: pd.DataFrame,
                           periods_per_year: int = 252) -> float:
    """Annualised return of cash over the aligned window (252 business days)."""
    n = len(cash)
    return float(cash["cash_growth"].iloc[-1] ** (periods_per_year / n) - 1.0)
