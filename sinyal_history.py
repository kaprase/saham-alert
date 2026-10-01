"""
sinyal_history.py
Modul untuk melacak riwayat sinyal BUY/SELL/HOLD per saham.
Data disimpan di signal_history.json dan di-commit ke GitHub.
"""

import json
import os
import subprocess
from datetime import datetime, timezone, timedelta

WIB = timezone(timedelta(hours=7))
HISTORY_FILE = "signal_history.json"


def baca_history() -> dict:
    """Baca riwayat sinyal dari file JSON."""
    if not os.path.exists(HISTORY_FILE):
        return {}
    try:
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def simpan_history(data: dict):
    """Simpan riwayat sinyal ke file JSON."""
    with open(HISTORY_FILE, "w") as f:
        json.dump(data, f, indent=2)


def update_sinyal(kode: str, sinyal_baru: str) -> dict:
    """
    Update riwayat sinyal untuk satu saham.
    Kembalikan info berapa hari sinyal ini sudah berlangsung.
    """
    history = baca_history()
    today = datetime.now(WIB).strftime("%Y-%m-%d")

    if kode not in history:
        # Pertama kali muncul
        history[kode] = {
            "sinyal": sinyal_baru,
            "tanggal_mulai": today,
            "hari": 1,
            "terakhir_update": today,
        }
    else:
        existing = history[kode]
        if existing["sinyal"] == sinyal_baru:
            # Sinyal sama — hitung hari berturut-turut
            # Hitung selisih hari dari tanggal mulai
            tanggal_mulai = datetime.strptime(existing["tanggal_mulai"], "%Y-%m-%d")
            tanggal_sekarang = datetime.strptime(today, "%Y-%m-%d")
            selisih = (tanggal_sekarang - tanggal_mulai).days + 1
            history[kode]["hari"] = selisih
            history[kode]["terakhir_update"] = today
        else:
            # Sinyal berubah — reset hitungan
            history[kode] = {
                "sinyal": sinyal_baru,
                "tanggal_mulai": today,
                "hari": 1,
                "terakhir_update": today,
            }

    simpan_history(history)
    return history[kode]


def update_semua_sinyal(semua_laporan: list) -> dict:
    """Update riwayat sinyal untuk semua saham sekaligus."""
    hasil = {}
    for laporan in semua_laporan:
        kode = laporan["kode"]
        sinyal = laporan["keputusan"]
        hasil[kode] = update_sinyal(kode, sinyal)
    return hasil


def ambil_info_sinyal(kode: str) -> dict | None:
    """Ambil info riwayat sinyal untuk satu saham."""
    history = baca_history()
    return history.get(kode)


def format_durasi_sinyal(kode: str) -> str:
    """Format info durasi sinyal untuk ditampilkan di Telegram."""
    info = ambil_info_sinyal(kode)
    if not info:
        return ""

    hari = info["hari"]
    tanggal = datetime.strptime(info["tanggal_mulai"], "%Y-%m-%d")
    tanggal_str = tanggal.strftime("%d %b %Y")
    sinyal = info["sinyal"]

    if sinyal == "BUY":
        emoji = "🟢"
    elif sinyal == "SELL":
        emoji = "🔴"
    else:
        emoji = "⚪"

    if hari == 1:
        return f"📅 {emoji} Sinyal {sinyal} hari ini ({tanggal_str})"
    else:
        return f"📅 {emoji} Sinyal {sinyal} selama *{hari} hari* (sejak {tanggal_str})"


def commit_history_ke_github():
    """
    Commit file signal_history.json ke GitHub agar tersimpan permanen.
    Hanya berjalan di environment GitHub Actions.
    """
    # Cek apakah sedang di GitHub Actions
    if not os.getenv("GITHUB_ACTIONS"):
        print("  [i] Bukan di GitHub Actions, skip commit")
        return

    try:
        # Setup git identity
        subprocess.run(
            ["git", "config", "user.email", "clau-bot@saham-alert.com"],
            check=True, capture_output=True
        )
        subprocess.run(
            ["git", "config", "user.name", "Clau Bot"],
            check=True, capture_output=True
        )

        # Add file
        subprocess.run(
            ["git", "add", HISTORY_FILE],
            check=True, capture_output=True
        )

        # Cek apakah ada perubahan
        result = subprocess.run(
            ["git", "diff", "--cached", "--quiet"],
            capture_output=True
        )

        if result.returncode == 0:
            print("  [i] Tidak ada perubahan sinyal, skip commit")
            return

        # Commit
        today = datetime.now(WIB).strftime("%d %b %Y %H:%M WIB")
        subprocess.run(
            ["git", "commit", "-m", f"📊 Update signal history — {today}"],
            check=True, capture_output=True
        )

        # Push
        subprocess.run(
            ["git", "push"],
            check=True, capture_output=True
        )

        print("  ✅ Signal history berhasil disimpan ke GitHub")

    except subprocess.CalledProcessError as e:
        print(f"  [!] Gagal commit history: {e}")
    except Exception as e:
        print(f"  [!] Error: {e}")
