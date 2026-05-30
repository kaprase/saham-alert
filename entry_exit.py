"""
entry_exit.py
Modul perhitungan otomatis Entry, Exit (Target), dan Stop Loss
berdasarkan analisis teknikal Support & Resistance + ATR
"""

import numpy as np
import pandas as pd
import pandas_ta as ta


def hitung_support_resistance(df: pd.DataFrame, periode: int = 20) -> dict:
    """
    Hitung level support dan resistance dari data historis.
    Metode: pivot points + swing high/low
    """
    close = df["Close"]
    high = df["High"]
    low = df["Low"]

    # ── Pivot Points (Classic) ─────────────────────────────
    # Ambil data kemarin sebagai referensi
    pivot = (high.iloc[-2] + low.iloc[-2] + close.iloc[-2]) / 3
    r1 = (2 * pivot) - low.iloc[-2]
    r2 = pivot + (high.iloc[-2] - low.iloc[-2])
    s1 = (2 * pivot) - high.iloc[-2]
    s2 = pivot - (high.iloc[-2] - low.iloc[-2])

    # ── Swing High / Low (last N candles) ─────────────────
    recent = df.tail(periode)
    swing_high = recent["High"].max()
    swing_low = recent["Low"].min()

    # ── Support & Resistance dari Volume Profile ──────────
    # Cari harga dengan volume tertinggi (area konsolidasi)
    bins = pd.cut(close.tail(60), bins=10)
    vol_profile = df["Volume"].tail(60).groupby(bins).sum()
    if not vol_profile.empty:
        top_area = vol_profile.idxmax()
        area_tengah = (top_area.left + top_area.right) / 2
    else:
        area_tengah = close.mean()

    # ── Moving Average sebagai dynamic support ────────────
    ma20 = ta.sma(close, length=20).iloc[-1]
    ma50 = ta.sma(close, length=50).iloc[-1]

    harga_sekarang = close.iloc[-1]

    # Kumpulkan semua level support (di bawah harga sekarang)
    kandidat_support = [s1, s2, swing_low, ma20, ma50, area_tengah]
    support_levels = sorted(
        [s for s in kandidat_support if pd.notna(s) and s < harga_sekarang],
        reverse=True  # support terdekat di atas
    )

    # Kumpulkan semua level resistance (di atas harga sekarang)
    kandidat_resistance = [r1, r2, swing_high, area_tengah]
    resistance_levels = sorted(
        [r for r in kandidat_resistance if pd.notna(r) and r > harga_sekarang]
    )

    return {
        "harga_sekarang": harga_sekarang,
        "pivot": pivot,
        "support_levels": support_levels[:3],   # 3 support terdekat
        "resistance_levels": resistance_levels[:3],  # 3 resistance terdekat
        "swing_high": swing_high,
        "swing_low": swing_low,
        "ma20": ma20,
        "ma50": ma50,
    }


def hitung_atr(df: pd.DataFrame, periode: int = 14) -> float:
    """
    Hitung Average True Range — ukuran volatilitas harga.
    Digunakan untuk menentukan jarak stop loss yang wajar.
    """
    atr = ta.atr(df["High"], df["Low"], df["Close"], length=periode)
    if atr is not None and not atr.empty:
        return float(atr.iloc[-1])
    return float((df["High"] - df["Low"]).tail(14).mean())


def hitung_entry_exit(df: pd.DataFrame, info: dict = None) -> dict:
    """
    Hitung rekomendasi entry, target profit, dan stop loss secara otomatis.

    Return dict berisi:
    - entry       : harga entry yang disarankan
    - target1     : target profit konservatif
    - target2     : target profit optimis
    - stop_loss   : batas rugi maksimal
    - rr_ratio    : risk/reward ratio
    - penjelasan  : alasan di balik setiap level
    """
    if df is None or len(df) < 50:
        return {"error": "Data tidak cukup untuk analisis"}

    sr = hitung_support_resistance(df)
    atr = hitung_atr(df)
    harga = sr["harga_sekarang"]

    # ── Entry Price ────────────────────────────────────────
    # Ideal: beli di dekat support terdekat
    if sr["support_levels"]:
        support_terdekat = sr["support_levels"][0]
        # Entry sedikit di atas support (konfirmasi)
        entry = round(support_terdekat * 1.005, 0)  # +0.5% dari support
        alasan_entry = f"Dekat support Rp{support_terdekat:,.0f}".replace(",", ".")
    else:
        # Tidak ada support jelas → entry di harga sekarang
        entry = round(harga, 0)
        alasan_entry = "Harga sekarang (support tidak teridentifikasi)"

    # ── Stop Loss ─────────────────────────────────────────
    # Metode ATR: stop loss = entry - (1.5 × ATR)
    stop_atr = entry - (1.5 * atr)

    # Metode Support: stop loss = support terkuat - sedikit buffer
    if sr["support_levels"]:
        support_kuat = sr["support_levels"][-1] if len(sr["support_levels"]) > 1 else sr["support_levels"][0]
        stop_support = round(support_kuat * 0.98, 0)  # 2% di bawah support
    else:
        stop_support = entry * 0.93  # default 7%

    # Ambil yang lebih tinggi (lebih konservatif)
    stop_loss = round(max(stop_atr, stop_support), 0)

    # Pastikan stop loss tidak lebih dari 10% di bawah entry
    if (entry - stop_loss) / entry > 0.10:
        stop_loss = round(entry * 0.92, 0)

    alasan_stop = f"1.5× ATR (Rp{atr:,.0f}) dari entry".replace(",", ".")

    # ── Target Profit ──────────────────────────────────────
    risiko = entry - stop_loss

    # Target 1 (konservatif): Risk/Reward = 1:1.5
    if sr["resistance_levels"]:
        target1_sr = sr["resistance_levels"][0]
        target1_rr = entry + (risiko * 1.5)
        target1 = round(min(target1_sr, target1_rr) if target1_sr > entry else target1_rr, 0)
        alasan_t1 = f"Resistance terdekat / RR 1:1.5"
    else:
        target1 = round(entry + (risiko * 1.5), 0)
        alasan_t1 = "Risk/Reward 1:1.5"

    # Target 2 (optimis): Risk/Reward = 1:3
    if len(sr["resistance_levels"]) > 1:
        target2_sr = sr["resistance_levels"][1]
        target2_rr = entry + (risiko * 3)
        target2 = round(max(target2_sr, target2_rr) if target2_sr > target1 else target2_rr, 0)
        alasan_t2 = f"Resistance kuat / RR 1:3"
    else:
        target2 = round(entry + (risiko * 3), 0)
        alasan_t2 = "Risk/Reward 1:3"

    # ── Risk/Reward Ratio ──────────────────────────────────
    rr1 = round((target1 - entry) / risiko, 1) if risiko > 0 else 0
    rr2 = round((target2 - entry) / risiko, 1) if risiko > 0 else 0

    # ── Persen perubahan ───────────────────────────────────
    pct_entry = ((entry - harga) / harga) * 100
    pct_t1 = ((target1 - entry) / entry) * 100
    pct_t2 = ((target2 - entry) / entry) * 100
    pct_sl = ((stop_loss - entry) / entry) * 100

    return {
        "harga_sekarang": harga,
        "entry": entry,
        "target1": target1,
        "target2": target2,
        "stop_loss": stop_loss,
        "rr1": rr1,
        "rr2": rr2,
        "atr": atr,
        "pct_entry": pct_entry,
        "pct_t1": pct_t1,
        "pct_t2": pct_t2,
        "pct_sl": pct_sl,
        "alasan_entry": alasan_entry,
        "alasan_stop": alasan_stop,
        "alasan_t1": alasan_t1,
        "alasan_t2": alasan_t2,
        "support_levels": sr["support_levels"],
        "resistance_levels": sr["resistance_levels"],
        "ma20": sr["ma20"],
        "ma50": sr["ma50"],
    }


def format_rupiah(angka) -> str:
    if angka is None:
        return "N/A"
    try:
        return f"Rp{int(angka):,}".replace(",", ".")
    except Exception:
        return str(angka)


def format_pesan_entry_exit(kode: str, hasil: dict, nama: str = "") -> str:
    """Format hasil analisis entry/exit menjadi pesan Telegram."""
    if "error" in hasil:
        return f"⚠️ {hasil['error']}"

    kode_bersih = kode.replace(".JK", "")
    nama_tampil = f"_{nama}_\n" if nama else ""

    tanda_entry = "🔽" if hasil["pct_entry"] < 0 else "➡️"

    pesan = [
        f"🎯 *ENTRY & EXIT — {kode_bersih}*",
        nama_tampil,
        f"━━━━━━━━━━━━━━━━━━━━",
        f"💰 Harga sekarang: *{format_rupiah(hasil['harga_sekarang'])}*",
        f"",
        f"📍 *ENTRY (Harga Beli)*",
        f"  {tanda_entry} *{format_rupiah(hasil['entry'])}*",
        f"  _{hasil['alasan_entry']}_",
        f"",
        f"🎯 *TARGET PROFIT*",
        f"  T1: *{format_rupiah(hasil['target1'])}* (+{hasil['pct_t1']:.1f}%) — RR 1:{hasil['rr1']}",
        f"  _{hasil['alasan_t1']}_",
        f"  T2: *{format_rupiah(hasil['target2'])}* (+{hasil['pct_t2']:.1f}%) — RR 1:{hasil['rr2']}",
        f"  _{hasil['alasan_t2']}_",
        f"",
        f"🛑 *STOP LOSS*",
        f"  *{format_rupiah(hasil['stop_loss'])}* ({hasil['pct_sl']:.1f}%)",
        f"  _{hasil['alasan_stop']}_",
        f"",
        f"━━━━━━━━━━━━━━━━━━━━",
        f"📊 *Level Teknikal*",
        f"  MA20: {format_rupiah(hasil['ma20'])} | MA50: {format_rupiah(hasil['ma50'])}",
    ]

    if hasil["support_levels"]:
        supports = " · ".join([format_rupiah(s) for s in hasil["support_levels"]])
        pesan.append(f"  Support: {supports}")

    if hasil["resistance_levels"]:
        resistances = " · ".join([format_rupiah(r) for r in hasil["resistance_levels"]])
        pesan.append(f"  Resistance: {resistances}")

    pesan += [
        f"",
        f"⚠️ _Selalu pasang stop loss! Disiplin adalah kuncinya._",
        f"🤖 Powered by Clau - Kandip's smartest assistant 😎",
    ]

    return "\n".join(pesan)
