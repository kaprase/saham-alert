"""
saham_syariah.py
Modul filter saham syariah IDX.

Sumber resmi: Pengumuman BEI No. Peng-00089/BEI.POP/05-2026
Periode efektif: 2 Juni 2026 s.d. 30 November 2026
"""

import os
import requests

# ─────────────────────────────────────────────────────────────
# DAFTAR JII70 — PERIODE JUNI s.d. NOVEMBER 2026
# Sumber: Lampiran Pengumuman BEI No. Peng-00089/BEI.POP/05-2026
# ─────────────────────────────────────────────────────────────
DAFTAR_JII70 = [
    "AADI.JK",   # Adaro Andalan Indonesia
    "ACES.JK",   # Ace Hardware Indonesia
    "ADMR.JK",   # Adaro Minerals Indonesia
    "ADRO.JK",   # Adaro Energy Indonesia
    "AKRA.JK",   # AKR Corporindo
    "ANTM.JK",   # Aneka Tambang
    "ARCI.JK",   # Archi Indonesia (BARU)
    "AVIA.JK",   # Aviasi Pariwisata Indonesia
    "BKSL.JK",   # Sentul City (BARU)
    "BRIS.JK",   # Bank Syariah Indonesia
    "BRMS.JK",   # Bumi Resources Minerals
    "BSDE.JK",   # Bumi Serpong Damai
    "BTPS.JK",   # Bank BTPN Syariah
    "BUMI.JK",   # Bumi Resources
    "CMRY.JK",   # Cisarua Mountain Dairy
    "CPIN.JK",   # Charoen Pokphand Indonesia
    "CTRA.JK",   # Ciputra Development
    "DEWA.JK",   # Darma Henwa (BARU)
    "DKFT.JK",   # Central Omega Resources (BARU)
    "DSNG.JK",   # Dharma Satya Nusantara
    "ELSA.JK",   # Elnusa
    "ENRG.JK",   # Energi Mega Persada
    "ERAA.JK",   # Erajaya Swasembada
    "ESSA.JK",   # Essa Industries Indonesia
    "EXCL.JK",   # XL Axiata
    "HEAL.JK",   # Medikaloka Hermina
    "HRTA.JK",   # Hartadinata Abadi (BARU)
    "HRUM.JK",   # Harum Energy
    "ICBP.JK",   # Indofood CBP
    "IMPC.JK",   # Impack Pratama Industri (BARU)
    "INDF.JK",   # Indofood Sukses Makmur
    "INDY.JK",   # Indika Energy
    "INKP.JK",   # Indah Kiat Pulp & Paper
    "INTP.JK",   # Indocement Tunggal Prakarsa
    "ISAT.JK",   # Indosat Ooredoo Hutchison
    "ITMG.JK",   # Indo Tambangraya Megah
    "JPFA.JK",   # Japfa Comfeed Indonesia
    "JSMR.JK",   # Jasa Marga
    "KIJA.JK",   # Kawasan Industri Jababeka
    "KLBF.JK",   # Kalbe Farma
    "KPIG.JK",   # MNC Land
    "LSIP.JK",   # PP London Sumatra
    "MAPA.JK",   # Map Aktif Adiperkasa
    "MAPI.JK",   # Mitra Adiperkasa
    "MARK.JK",   # Mark Dynamics Indonesia
    "MBMA.JK",   # Merdeka Battery Materials
    "MDKA.JK",   # Merdeka Copper Gold
    "MEDC.JK",   # Medco Energi Internasional
    "MIKA.JK",   # Mitra Keluarga Karyasehat
    "MTEL.JK",   # Dayamitra Telekomunikasi
    "MYOR.JK",   # Mayora Indah
    "PGAS.JK",   # Perusahaan Gas Negara
    "PTBA.JK",   # Bukit Asam
    "RAJA.JK",   # Rukun Raharja (BARU)
    "RATU.JK",   # Raharja Energi Cepu
    "SIDO.JK",   # Industri Jamu Sido Muncul
    "SMGR.JK",   # Semen Indonesia
    "SMRA.JK",   # Summarecon Agung
    "SRTG.JK",   # Saratoga Investama Sedaya
    "SSIA.JK",   # Surya Semesta Internusa
    "TAPG.JK",   # Triputra Agro Persada
    "TCPI.JK",   # Transcoal Pacific
    "TINS.JK",   # Timah (BARU)
    "TKIM.JK",   # Tjiwi Kimia
    "TLKM.JK",   # Telkom Indonesia
    "TOBA.JK",   # TBS Energi Utama (BARU)
    "TPIA.JK",   # Chandra Asri Pacific
    "UNTR.JK",   # United Tractors
    "UNVR.JK",   # Unilever Indonesia
    "WIFI.JK",   # Solusi Sinergi Digital (BARU)
]

# Saham yang keluar dari JII70 periode ini
KELUAR_JII70 = ["ASII", "BRPT", "DSSA", "INCO", "NCKL", "PANI", "PGEO", "PTPP", "PWON"]


def coba_ambil_dari_github(github_user: str, repo: str = "saham-alert") -> list | None:
    """Coba baca file saham_syariah.txt dari repository GitHub."""
    url = f"https://raw.githubusercontent.com/{github_user}/{repo}/main/saham_syariah.txt"
    try:
        r = requests.get(url, timeout=8)
        if r.status_code == 200:
            saham = [
                baris.strip().upper()
                for baris in r.text.splitlines()
                if baris.strip() and not baris.startswith("#")
            ]
            if saham:
                print(f"  ✅ Berhasil ambil {len(saham)} saham dari GitHub")
                return saham
    except Exception as e:
        print(f"  [!] Gagal ambil dari GitHub: {e}")
    return None


def ambil_daftar_syariah(
    indeks: str = "JII70",
    github_user: str | None = None,
) -> list:
    """Ambil daftar saham syariah."""
    print(f"\n📋 Mengambil daftar saham syariah ({indeks})...")

    if github_user:
        dari_github = coba_ambil_dari_github(github_user)
        if dari_github:
            return dari_github

    print(f"  ✅ Menggunakan daftar {indeks}: {len(DAFTAR_JII70)} saham")
    print(f"  📅 Periode: 2 Juni 2026 s.d. 30 November 2026")
    return DAFTAR_JII70


def filter_saham_syariah(daftar_saham: list, indeks: str = "JII70") -> list:
    """Filter daftar saham, hanya kembalikan yang masuk indeks syariah."""
    referensi = set(DAFTAR_JII70)
    hasil = [s for s in daftar_saham if s.upper() in referensi]
    tidak_syariah = [s for s in daftar_saham if s.upper() not in referensi]
    if tidak_syariah:
        print(f"  ⚠️  Dikeluarkan (bukan syariah/tidak di JII70): {', '.join(tidak_syariah)}")
    return hasil


def cetak_info_indeks():
    print("""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📌 INFO INDEKS SAHAM SYARIAH IDX
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Indeks  : JII70 (Jakarta Islamic Index 70)
Sumber  : Peng-00089/BEI.POP/05-2026
Periode : 2 Juni 2026 s.d. 30 November 2026
Total   : 70 saham syariah
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")


if __name__ == "__main__":
    cetak_info_indeks()
    daftar = ambil_daftar_syariah("JII70")
    print(f"Total: {len(daftar)} saham")
