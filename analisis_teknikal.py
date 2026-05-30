"""
analisis_teknikal.py
Modul untuk menghitung indikator teknikal saham
"""

import pandas as pd
import pandas_ta as ta
import numpy as np


def hitung_indikator(df: pd.DataFrame) -> pd.DataFrame:
    """
    Hitung semua indikator teknikal.
    """
    df = df.copy()
    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    volume = df["Volume"]

    # Moving Average
    df["MA20"] = ta.sma(close, length=20)
    df["MA50"] = ta.sma(close, length=50)
    df["EMA12"] = ta.ema(close, length=12)
    df["EMA26"] = ta.ema(close, length=26)

    # RSI
    df["RSI"] = ta.rsi(close, length=14)

    # MACD
    macd = ta.macd(close, fast=12, slow=26, signal=9)
    if macd is not None:
        df["MACD"] = macd.get("MACD_12_26_9", np.nan)
        df["MACD_Signal"] = macd.get("MACDs_12_26_9", np.nan)
        df["MACD_Hist"] = macd.get("MACDh_12_26_9", np.nan)

    # Bollinger Bands
    bb = ta.bbands(close, length=20)
    if bb is not None:
        df["BB_Upper"] = bb.get("BBU_20_2.0", np.nan)
        df["BB_Middle"] = bb.get("BBM_20_2.0", np.nan)
        df["BB_Lower"] = bb.get("BBL_20_2.0", np.nan)

    # Stochastic
    stoch = ta.stoch(high, low, close)
    if stoch is not None:
        df["Stoch_K"] = stoch.get("STOCHk_14_3_3", np.nan)
        df["Stoch_D"] = stoch.get("STOCHd_14_3_3", np.nan)

    # Volume MA
    df["Volume_MA20"] = ta.sma(volume, length=20)

    return df


def analisis_sinyal_teknikal(df: pd.DataFrame) -> dict:
    """
    Analisis sinyal dari indikator teknikal.
    Mengembalikan skor 0-100 beserta detail sinyal.
    """
    if df is None or len(df) < 50:
        return {"skor": 50, "detail": {}, "ringkasan": "Data tidak cukup"}

    df = hitung_indikator(df)
    df_valid = df.dropna(subset=["RSI", "MA20", "MA50"])
    if df_valid.empty:
        df_valid = df.dropna(subset=["RSI"])
    if df_valid.empty:
        return {"skor": 50, "detail": {}, "ringkasan": "Indikator belum bisa dihitung"}
    baris = df_valid.iloc[-1]  # data terbaru

    sinyal = []
    skor_total = 0
    bobot_total = 0

    # ── RSI ────────────────────────────────────────────
    rsi = baris.get("RSI", 50)
    if pd.notna(rsi):
        bobot = 25
        if rsi < 30:
            skor_rsi = 90
            label_rsi = f"Oversold ({rsi:.1f}) → Potensi naik 🟢"
        elif rsi < 40:
            skor_rsi = 70
            label_rsi = f"Mendekati oversold ({rsi:.1f}) 🟡"
        elif rsi > 70:
            skor_rsi = 15
            label_rsi = f"Overbought ({rsi:.1f}) → Potensi turun 🔴"
        elif rsi > 60:
            skor_rsi = 35
            label_rsi = f"Mendekati overbought ({rsi:.1f}) 🟡"
        else:
            skor_rsi = 50
            label_rsi = f"Netral ({rsi:.1f}) ⚪"
        sinyal.append(("RSI", skor_rsi, label_rsi, bobot))
        skor_total += skor_rsi * bobot
        bobot_total += bobot

    # ── MACD ───────────────────────────────────────────
    macd_val = baris.get("MACD", np.nan)
    macd_sig = baris.get("MACD_Signal", np.nan)
    macd_hist = baris.get("MACD_Hist", np.nan)

    if pd.notna(macd_val) and pd.notna(macd_sig):
        bobot = 25
        if macd_val > macd_sig and macd_hist > 0:
            skor_macd = 80
            label_macd = "Golden cross → Momentum naik 🟢"
        elif macd_val < macd_sig and macd_hist < 0:
            skor_macd = 20
            label_macd = "Death cross → Momentum turun 🔴"
        else:
            skor_macd = 50
            label_macd = "Netral ⚪"
        sinyal.append(("MACD", skor_macd, label_macd, bobot))
        skor_total += skor_macd * bobot
        bobot_total += bobot

    # ── Moving Average ─────────────────────────────────
    harga = baris.get("Close", np.nan)
    ma20 = baris.get("MA20", np.nan)
    ma50 = baris.get("MA50", np.nan)

    if pd.notna(harga) and pd.notna(ma20) and pd.notna(ma50):
        bobot = 25
        if harga > ma20 > ma50:
            skor_ma = 85
            label_ma = "Harga di atas MA20 & MA50 (uptrend) 🟢"
        elif harga < ma20 < ma50:
            skor_ma = 15
            label_ma = "Harga di bawah MA20 & MA50 (downtrend) 🔴"
        elif harga > ma20:
            skor_ma = 60
            label_ma = "Harga di atas MA20 🟡"
        else:
            skor_ma = 40
            label_ma = "Harga di bawah MA20 🟡"
        sinyal.append(("Moving Average", skor_ma, label_ma, bobot))
        skor_total += skor_ma * bobot
        bobot_total += bobot

    # ── Bollinger Bands ────────────────────────────────
    bb_upper = baris.get("BB_Upper", np.nan)
    bb_lower = baris.get("BB_Lower", np.nan)

    if pd.notna(harga) and pd.notna(bb_upper) and pd.notna(bb_lower):
        bobot = 25
        if harga <= bb_lower:
            skor_bb = 85
            label_bb = "Harga menyentuh lower band → Potensi rebound 🟢"
        elif harga >= bb_upper:
            skor_bb = 15
            label_bb = "Harga menyentuh upper band → Potensi koreksi 🔴"
        else:
            posisi = (harga - bb_lower) / (bb_upper - bb_lower)
            if posisi < 0.35:
                skor_bb = 65
                label_bb = "Harga dekat lower band 🟡"
            elif posisi > 0.65:
                skor_bb = 35
                label_bb = "Harga dekat upper band 🟡"
            else:
                skor_bb = 50
                label_bb = "Harga di tengah bollinger band ⚪"
        sinyal.append(("Bollinger Bands", skor_bb, label_bb, bobot))
        skor_total += skor_bb * bobot
        bobot_total += bobot

    skor_akhir = int(skor_total / bobot_total) if bobot_total > 0 else 50

    return {
        "skor": skor_akhir,
        "detail": {nama: {"skor": s, "label": l} for nama, s, l, _ in sinyal},
        "harga_terakhir": float(harga) if pd.notna(harga) else None,
        "rsi": float(rsi) if pd.notna(rsi) else None,
    }
