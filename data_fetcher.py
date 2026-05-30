"""
data_fetcher.py
Modul untuk mengambil data saham dari Yahoo Finance
"""

import yfinance as yf
import pandas as pd
from datetime import datetime
import time


def ambil_data_saham(kode_saham: str, periode: str = "6mo") -> pd.DataFrame | None:
    """
    Ambil data historis harga saham.
    
    kode_saham : contoh "BBCA.JK"
    periode    : "1mo", "3mo", "6mo", "1y"
    """
    try:
        ticker = yf.Ticker(kode_saham)
        df = ticker.history(period=periode)
        if df.empty:
            print(f"  [!] Data kosong untuk {kode_saham}")
            return None
        df.index = pd.to_datetime(df.index)
        return df
    except Exception as e:
        print(f"  [!] Gagal ambil data {kode_saham}: {e}")
        return None


def ambil_info_saham(kode_saham: str) -> dict:
    """
    Ambil informasi fundamental saham.
    """
    info_default = {
        "nama": kode_saham,
        "sektor": "N/A",
        "pe_ratio": None,
        "eps": None,
        "roe": None,
        "der": None,
        "book_value": None,
        "market_cap": None,
        "harga_sekarang": None,
        "volume": None,
    }
    try:
        ticker = yf.Ticker(kode_saham)
        info = ticker.info

        info_default.update({
            "nama": info.get("longName", kode_saham),
            "sektor": info.get("sector", "N/A"),
            "pe_ratio": info.get("trailingPE"),
            "eps": info.get("trailingEps"),
            "roe": info.get("returnOnEquity"),
            "der": info.get("debtToEquity"),
            "book_value": info.get("bookValue"),
            "market_cap": info.get("marketCap"),
            "harga_sekarang": info.get("currentPrice") or info.get("regularMarketPrice"),
            "volume": info.get("regularMarketVolume"),
        })
        return info_default
    except Exception as e:
        print(f"  [!] Gagal ambil info {kode_saham}: {e}")
        return info_default


def ambil_semua_data(daftar_saham: list) -> dict:
    """
    Ambil data untuk semua saham dalam daftar.
    """
    hasil = {}
    print(f"\n📥 Mengambil data untuk {len(daftar_saham)} saham...")
    
    for kode in daftar_saham:
        print(f"  → {kode} ...", end=" ", flush=True)
        df = ambil_data_saham(kode)
        info = ambil_info_saham(kode)
        
        if df is not None:
            hasil[kode] = {"harga": df, "info": info}
            print("✓")
        else:
            print("✗ (dilewati)")
        
        time.sleep(0.5)  # jeda agar tidak kena rate limit
    
    print(f"✅ Berhasil ambil data: {len(hasil)}/{len(daftar_saham)} saham\n")
    return hasil
