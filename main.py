"""
main.py
Program utama sistem analisis saham IDX
Jalankan dengan: python main.py
"""

import os
import sys
import time
import schedule
from datetime import datetime, timezone, timedelta

WIB = timezone(timedelta(hours=7))
from dotenv import load_dotenv
from colorama import init, Fore, Style

# Inisialisasi warna terminal
init(autoreset=True)

# Load konfigurasi dari .env
load_dotenv()

# Import modul lokal
from data_fetcher import ambil_semua_data
from analisis_teknikal import analisis_sinyal_teknikal
from analisis_fundamental import analisis_fundamental
from analisis_ai import prediksi_ai
from decision_engine import buat_laporan_lengkap, format_pesan_telegram
from telegram_bot import kirim_sinyal, kirim_ringkasan_harian, uji_koneksi_telegram


def cetak_banner():
    print(Fore.CYAN + """
╔══════════════════════════════════════════════════════╗
║         SISTEM ANALISIS SAHAM IDX / BEI             ║
║     Teknikal + Fundamental + AI  →  Telegram        ║
╚══════════════════════════════════════════════════════╝
""" + Style.RESET_ALL)


def ambil_daftar_saham() -> list:
    from saham_syariah import ambil_daftar_syariah, filter_saham_syariah

    raw = os.getenv("DAFTAR_SAHAM", "").strip()
    indeks = os.getenv("INDEKS_SYARIAH", "JII70").upper()
    github_user = os.getenv("GITHUB_USER", "").strip() or None

    if raw:
        daftar = [s.strip().upper() for s in raw.split(",") if s.strip()]
        print(f"📋 Mode: filter manual → hanya syariah {indeks}")
        return filter_saham_syariah(daftar, indeks)
    else:
        print(f"📋 Mode: otomatis daftar {indeks}")
        return ambil_daftar_syariah(indeks, github_user)


def jalankan_analisis(kirim_semua: bool = False):
    """
    Jalankan analisis lengkap untuk semua saham.
    kirim_semua=True → kirim ringkasan ke Telegram
    kirim_semua=False → hanya kirim sinyal BUY/SELL
    """
    waktu = datetime.now(WIB).strftime("%d/%m/%Y %H:%M WIB")
    print(f"\n{Fore.YELLOW}⏰ Analisis dimulai: {waktu}{Style.RESET_ALL}")

    daftar = ambil_daftar_saham()
    data = ambil_semua_data(daftar)

    semua_laporan = []
    sinyal_penting = []

    print(f"{Fore.CYAN}🔬 Menganalisis {len(data)} saham...{Style.RESET_ALL}\n")

    for kode, konten in data.items():
        print(f"  📊 {kode}", end=" ... ", flush=True)

        df_harga = konten["harga"]
        info = konten["info"]

        # Jalankan tiga mesin analisis
        hasil_t = analisis_sinyal_teknikal(df_harga)
        hasil_f = analisis_fundamental(info)
        hasil_a = prediksi_ai(df_harga)

        # Gabungkan menjadi laporan
        laporan = buat_laporan_lengkap(kode, info, hasil_t, hasil_f, hasil_a)
        semua_laporan.append(laporan)

        keputusan = laporan["keputusan"]
        skor = laporan["skor_gabungan"]

        # Warnai output berdasarkan keputusan
        if keputusan == "BUY":
            warna = Fore.GREEN
        elif keputusan == "SELL":
            warna = Fore.RED
        else:
            warna = Fore.WHITE

        print(warna + f"{keputusan} (Skor: {skor}/100)" + Style.RESET_ALL)

        # Tandai sinyal BUY/SELL untuk dikirim ke Telegram
        if keputusan in ("BUY", "SELL"):
            sinyal_penting.append(laporan)

    print()

    # Kirim notifikasi ke Telegram
    if sinyal_penting:
        print(f"{Fore.YELLOW}📤 Mengirim {len(sinyal_penting)} sinyal ke Telegram...{Style.RESET_ALL}")
        for laporan in sinyal_penting:
            pesan = format_pesan_telegram(laporan)
            berhasil = kirim_sinyal(laporan, pesan)
            status = "✅" if berhasil else "❌"
            print(f"  {status} {laporan['kode']} ({laporan['keputusan']})")
            time.sleep(1)

    if kirim_semua and semua_laporan:
        print(f"\n{Fore.YELLOW}📋 Mengirim ringkasan harian...{Style.RESET_ALL}")
        kirim_ringkasan_harian(semua_laporan)

    print(f"\n{Fore.GREEN}✅ Analisis selesai!{Style.RESET_ALL}")
    cetak_tabel(semua_laporan)


def cetak_tabel(laporan_list: list):
    """
    Tampilkan ringkasan tabel di terminal.
    """
    print(f"\n{'═'*65}")
    print(f"{'KODE':<12} {'NAMA':<22} {'HARGA':>10} {'SKOR':>6} {'SINYAL':<8}")
    print(f"{'─'*65}")

    for r in sorted(laporan_list, key=lambda x: x["skor_gabungan"], reverse=True):
        harga = f"Rp{int(r['harga']):,}".replace(",", ".") if r["harga"] else "N/A"
        nama = (r["nama"] or r["kode"])[:20]

        if r["keputusan"] == "BUY":
            warna = Fore.GREEN
        elif r["keputusan"] == "SELL":
            warna = Fore.RED
        else:
            warna = Fore.WHITE

        print(
            warna
            + f"{r['kode']:<12} {nama:<22} {harga:>10} {r['skor_gabungan']:>5}%  "
            + f"{r['emoji']} {r['keputusan']}"
            + Style.RESET_ALL
        )
    print(f"{'═'*65}\n")


def setup_jadwal():
    """
    Atur jadwal analisis otomatis.
    """
    jam_pagi = os.getenv("JAM_ANALISIS_PAGI", "09:30")
    jam_siang = os.getenv("JAM_ANALISIS_SIANG", "12:00")
    jam_sore = os.getenv("JAM_ANALISIS_SORE", "15:30")

    # Analisis pagi — kirim sinyal saja
    schedule.every().monday.at(jam_pagi).do(jalankan_analisis)
    schedule.every().tuesday.at(jam_pagi).do(jalankan_analisis)
    schedule.every().wednesday.at(jam_pagi).do(jalankan_analisis)
    schedule.every().thursday.at(jam_pagi).do(jalankan_analisis)
    schedule.every().friday.at(jam_pagi).do(jalankan_analisis)

    # Analisis siang
    schedule.every().monday.at(jam_siang).do(jalankan_analisis)
    schedule.every().tuesday.at(jam_siang).do(jalankan_analisis)
    schedule.every().wednesday.at(jam_siang).do(jalankan_analisis)
    schedule.every().thursday.at(jam_siang).do(jalankan_analisis)
    schedule.every().friday.at(jam_siang).do(jalankan_analisis)

    # Analisis sore — kirim ringkasan harian
    schedule.every().monday.at(jam_sore).do(jalankan_analisis, kirim_semua=True)
    schedule.every().tuesday.at(jam_sore).do(jalankan_analisis, kirim_semua=True)
    schedule.every().wednesday.at(jam_sore).do(jalankan_analisis, kirim_semua=True)
    schedule.every().thursday.at(jam_sore).do(jalankan_analisis, kirim_semua=True)
    schedule.every().friday.at(jam_sore).do(jalankan_analisis, kirim_semua=True)

    print(f"{Fore.CYAN}📅 Jadwal analisis diatur:")
    print(f"   Pagi  : {jam_pagi} WIB (Senin–Jumat)")
    print(f"   Siang : {jam_siang} WIB (Senin–Jumat)")
    print(f"   Sore  : {jam_sore} WIB + ringkasan harian (Senin–Jumat)")
    print(Style.RESET_ALL)


def main():
    cetak_banner()

    # Mode: langsung analisis atau jadwal
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()

        if arg == "analisis":
            print(f"{Fore.YELLOW}▶ Mode: Analisis langsung{Style.RESET_ALL}")
            jalankan_analisis(kirim_semua=True)

        elif arg == "uji-telegram":
            print(f"{Fore.YELLOW}▶ Mode: Uji koneksi Telegram{Style.RESET_ALL}")
            load_dotenv()
            uji_koneksi_telegram()

        elif arg == "jadwal":
            print(f"{Fore.YELLOW}▶ Mode: Jadwal otomatis aktif{Style.RESET_ALL}")
            uji_koneksi_telegram()
            setup_jadwal()
            print(f"{Fore.GREEN}✅ Sistem berjalan. Tekan Ctrl+C untuk berhenti.{Style.RESET_ALL}\n")
            while True:
                schedule.run_pending()
                time.sleep(30)
        else:
            print(f"Perintah tidak dikenal: {arg}")
            print("Gunakan: python main.py [analisis | uji-telegram | jadwal]")
    else:
        print("Cara penggunaan:")
        print(f"  {Fore.CYAN}python main.py analisis{Style.RESET_ALL}      → Analisis sekarang")
        print(f"  {Fore.CYAN}python main.py uji-telegram{Style.RESET_ALL}  → Uji koneksi bot")
        print(f"  {Fore.CYAN}python main.py jadwal{Style.RESET_ALL}        → Jalankan terjadwal")


if __name__ == "__main__":
    main()
