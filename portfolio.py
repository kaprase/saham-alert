"""
portfolio.py
Modul portfolio tracking — simpan & baca data dari file JSON di repository
"""

import json
import os
from datetime import datetime, timezone, timedelta

WIB = timezone(timedelta(hours=7))
PORTFOLIO_FILE = "portfolio_data.json"


def baca_portfolio() -> dict:
    """Baca data portfolio dari file JSON."""
    if not os.path.exists(PORTFOLIO_FILE):
        return {}
    try:
        with open(PORTFOLIO_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def simpan_portfolio(data: dict):
    """Simpan data portfolio ke file JSON."""
    with open(PORTFOLIO_FILE, "w") as f:
        json.dump(data, f, indent=2)


def catat_beli(kode: str, harga_beli: float, lot: int) -> dict:
    """
    Catat pembelian saham.
    1 lot = 100 lembar saham
    """
    kode = kode.upper()
    if not kode.endswith(".JK"):
        kode += ".JK"

    portfolio = baca_portfolio()

    if kode in portfolio:
        # Rata-rata harga jika beli lagi (average down/up)
        existing = portfolio[kode]
        total_lot_lama = existing["lot"]
        harga_lama = existing["harga_beli"]
        total_lot_baru = total_lot_lama + lot
        harga_rata = ((harga_lama * total_lot_lama) + (harga_beli * lot)) / total_lot_baru
        portfolio[kode]["harga_beli"] = round(harga_rata, 2)
        portfolio[kode]["lot"] = total_lot_baru
        portfolio[kode]["tanggal_update"] = datetime.now(WIB).strftime("%d/%m/%Y %H:%M WIB")
        aksi = "update"
    else:
        portfolio[kode] = {
            "harga_beli": harga_beli,
            "lot": lot,
            "tanggal_beli": datetime.now(WIB).strftime("%d/%m/%Y %H:%M WIB"),
            "tanggal_update": datetime.now(WIB).strftime("%d/%m/%Y %H:%M WIB"),
        }
        aksi = "baru"

    simpan_portfolio(portfolio)
    return {"kode": kode, "aksi": aksi, "data": portfolio[kode]}


def catat_jual(kode: str, harga_jual: float, lot: int) -> dict:
    """Catat penjualan saham."""
    kode = kode.upper()
    if not kode.endswith(".JK"):
        kode += ".JK"

    portfolio = baca_portfolio()

    if kode not in portfolio:
        return {"error": f"{kode} tidak ada di portfolio kamu."}

    existing = portfolio[kode]
    lot_tersisa = existing["lot"] - lot

    profit_per_lembar = harga_jual - existing["harga_beli"]
    profit_total = profit_per_lembar * lot * 100  # 1 lot = 100 lembar
    pct = (profit_per_lembar / existing["harga_beli"]) * 100

    if lot_tersisa <= 0:
        del portfolio[kode]
        status = "habis terjual"
    else:
        portfolio[kode]["lot"] = lot_tersisa
        portfolio[kode]["tanggal_update"] = datetime.now(WIB).strftime("%d/%m/%Y %H:%M WIB")
        status = f"sisa {lot_tersisa} lot"

    simpan_portfolio(portfolio)

    return {
        "kode": kode,
        "harga_beli": existing["harga_beli"],
        "harga_jual": harga_jual,
        "lot_dijual": lot,
        "profit_total": profit_total,
        "pct": pct,
        "status": status,
    }


def hapus_saham(kode: str) -> dict:
    """Hapus saham dari portfolio."""
    kode = kode.upper()
    if not kode.endswith(".JK"):
        kode += ".JK"

    portfolio = baca_portfolio()
    if kode not in portfolio:
        return {"error": f"{kode} tidak ada di portfolio."}

    del portfolio[kode]
    simpan_portfolio(portfolio)
    return {"kode": kode, "status": "dihapus"}


def hitung_portfolio_lengkap() -> dict:
    """
    Hitung nilai portfolio saat ini dengan harga terkini dari Yahoo Finance.
    """
    import yfinance as yf
    import time

    portfolio = baca_portfolio()
    if not portfolio:
        return {"kosong": True}

    hasil = []
    total_modal = 0
    total_nilai_sekarang = 0

    for kode, data in portfolio.items():
        try:
            ticker = yf.Ticker(kode)
            info = ticker.fast_info
            harga_sekarang = info.last_price or info.regular_market_price
            time.sleep(0.3)
        except Exception:
            harga_sekarang = None

        harga_beli = data["harga_beli"]
        lot = data["lot"]
        lembar = lot * 100

        modal = harga_beli * lembar
        total_modal += modal

        if harga_sekarang:
            nilai_sekarang = harga_sekarang * lembar
            total_nilai_sekarang += nilai_sekarang
            profit = nilai_sekarang - modal
            pct = (profit / modal) * 100
        else:
            nilai_sekarang = None
            profit = None
            pct = None

        hasil.append({
            "kode": kode,
            "harga_beli": harga_beli,
            "harga_sekarang": harga_sekarang,
            "lot": lot,
            "lembar": lembar,
            "modal": modal,
            "nilai_sekarang": nilai_sekarang,
            "profit": profit,
            "pct": pct,
        })

    # Urutkan: profit terbesar di atas
    hasil.sort(key=lambda x: x["pct"] if x["pct"] is not None else -999, reverse=True)

    total_profit = total_nilai_sekarang - total_modal if total_nilai_sekarang else None
    total_pct = (total_profit / total_modal * 100) if total_profit and total_modal else None

    return {
        "kosong": False,
        "saham": hasil,
        "total_modal": total_modal,
        "total_nilai_sekarang": total_nilai_sekarang,
        "total_profit": total_profit,
        "total_pct": total_pct,
    }


def format_rupiah(angka) -> str:
    if angka is None:
        return "N/A"
    try:
        return f"Rp{int(angka):,}".replace(",", ".")
    except Exception:
        return str(angka)


def format_pesan_portfolio(data: dict) -> str:
    """Format data portfolio menjadi pesan Telegram."""
    if data.get("kosong"):
        return (
            "📂 *Portfolio kamu masih kosong, Kandip!*\n\n"
            "Gunakan perintah berikut untuk mulai:\n"
            "`/beli BRIS 1500 10` — beli BRIS harga 1500, 10 lot\n\n"
            "🤖 Powered by Clau - Kandip's smartest assistant 😎"
        )

    baris = [
        "📊 *PORTFOLIO KANDIP*",
        f"🕐 {datetime.now(WIB).strftime('%d %b %Y %H:%M WIB')}",
        "━━━━━━━━━━━━━━━━━━━━",
    ]

    for s in data["saham"]:
        if s["pct"] is not None:
            emoji = "🟢" if s["pct"] >= 0 else "🔴"
            tanda = "+" if s["pct"] >= 0 else ""
            baris += [
                f"\n{emoji} *{s['kode'].replace('.JK', '')}* — {s['lot']} lot",
                f"  Beli: {format_rupiah(s['harga_beli'])} → Kini: {format_rupiah(s['harga_sekarang'])}",
                f"  P/L: {format_rupiah(s['profit'])} ({tanda}{s['pct']:.1f}%)",
            ]
        else:
            baris += [
                f"\n⚪ *{s['kode'].replace('.JK', '')}* — {s['lot']} lot",
                f"  Beli: {format_rupiah(s['harga_beli'])} → Kini: N/A",
            ]

    baris.append("\n━━━━━━━━━━━━━━━━━━━━")

    if data["total_profit"] is not None:
        emoji_total = "🟢" if data["total_profit"] >= 0 else "🔴"
        tanda = "+" if data["total_profit"] >= 0 else ""
        baris += [
            f"💼 Modal: *{format_rupiah(data['total_modal'])}*",
            f"💰 Nilai kini: *{format_rupiah(data['total_nilai_sekarang'])}*",
            f"{emoji_total} Total P/L: *{format_rupiah(data['total_profit'])}* ({tanda}{data['total_pct']:.1f}%)",
        ]

    baris.append("\n🤖 Powered by Clau - Kandip's smartest assistant 😎")
    return "\n".join(baris)
