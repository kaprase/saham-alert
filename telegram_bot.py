"""
telegram_bot.py
Modul untuk mengirim notifikasi via Telegram Bot
"""

import os
import asyncio
import requests
from datetime import datetime


def kirim_pesan(teks: str, parse_mode: str = "Markdown") -> bool:
    """
    Kirim pesan ke Telegram menggunakan HTTP API (sinkron).
    """
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token or token == "isi_token_bot_kamu_disini":
        print("  [!] Token Telegram belum diisi di file .env")
        return False
    if not chat_id or chat_id == "isi_chat_id_kamu_disini":
        print("  [!] Chat ID Telegram belum diisi di file .env")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": teks,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True,
    }

    try:
        resp = requests.post(url, json=payload, timeout=15)
        if resp.status_code == 200:
            return True
        else:
            print(f"  [!] Telegram error {resp.status_code}: {resp.text[:200]}")
            return False
    except Exception as e:
        print(f"  [!] Gagal kirim Telegram: {e}")
        return False


def kirim_sinyal(laporan: dict, pesan: str) -> bool:
    """
    Kirim sinyal trading ke Telegram.
    """
    return kirim_pesan(pesan)


def kirim_ringkasan_harian(semua_laporan: list) -> bool:
    """
    Kirim ringkasan semua saham yang dianalisis hari ini.
    """
    now = datetime.now().strftime("%d %b %Y %H:%M WIB")
    baris = [
        f"📋 *RINGKASAN ANALISIS SAHAM*",
        f"🕐 {now}",
        f"━━━━━━━━━━━━━━━━━━━━",
    ]

    beli = [r for r in semua_laporan if r["keputusan"] == "BUY"]
    jual = [r for r in semua_laporan if r["keputusan"] == "SELL"]
    tahan = [r for r in semua_laporan if r["keputusan"] == "HOLD"]

    if beli:
        baris.append(f"\n🟢 *SINYAL BUY ({len(beli)} saham)*")
        for r in sorted(beli, key=lambda x: x["skor_gabungan"], reverse=True):
            baris.append(
                f"  • *{r['kode']}* — Skor {r['skor_gabungan']}/100"
            )

    if jual:
        baris.append(f"\n🔴 *SINYAL SELL ({len(jual)} saham)*")
        for r in sorted(jual, key=lambda x: x["skor_gabungan"]):
            baris.append(
                f"  • *{r['kode']}* — Skor {r['skor_gabungan']}/100"
            )

    if tahan:
        baris.append(f"\n⚪ *HOLD ({len(tahan)} saham)*")
        for r in tahan:
            baris.append(f"  • {r['kode']} ({r['skor_gabungan']}/100)")

    baris += [
        f"\n━━━━━━━━━━━━━━━━━━━━",
        f"⚠️ _Ini bukan rekomendasi investasi. Lakukan riset sendiri._",
    ]

    return kirim_pesan("\n".join(baris))


def uji_koneksi_telegram() -> bool:
    """
    Uji apakah koneksi Telegram berhasil.
    """
    pesan = (
        "✅ *Sistem Analisis Saham IDX aktif!*\n"
        "Bot berhasil terhubung dan siap mengirim sinyal.\n"
        "_Notifikasi akan dikirim sesuai jadwal yang dikonfigurasi._"
    )
    hasil = kirim_pesan(pesan)
    if hasil:
        print("  ✅ Telegram berhasil terhubung!")
    else:
        print("  ❌ Koneksi Telegram gagal. Cek token dan chat ID di file .env")
    return hasil
