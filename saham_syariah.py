# HM Sampoerna
    "HEAL.JK",   # Medikaloka Hermina
    "MIKA.JK",   # Mitra Keluarga Karyasehat
    "RAJA.JK",   # Rukun Raharja
    "PGAS.JK",   # Perusahaan Gas Negara
    "ESSA.JK",   # Essa Industries Indonesia
]

# JII (Jakarta Islamic Index) — 30 saham terbaik dari JII70
DAFTAR_JII30 = [
    "ADRO.JK", "AKRA.JK", "AMRT.JK", "ANTM.JK", "ASII.JK",
    "BRIS.JK", "BSDE.JK", "CTRA.JK", "EMTK.JK", "EXCL.JK",
    "ICBP.JK", "INCO.JK", "INDF.JK", "ISAT.JK", "ITMG.JK",
    "JSMR.JK", "KLBF.JK", "MDKA.JK", "MEDC.JK", "MYOR.JK",
    "PGAS.JK", "PTBA.JK", "SMGR.JK", "TLKM.JK", "TPIA.JK",
    "UNVR.JK", "AALI.JK", "SIDO.JK", "MIKA.JK", "BTPS.JK",
]


def coba_ambil_dari_github(github_user: str, repo: str = "saham-alert") -> list | None:
    """
    Coba baca file saham_syariah.txt dari repository GitHub kamu.
    Format file: satu kode saham per baris, contoh:
        BRIS.JK
        TLKM.JK
        ADRO.JK
    """
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
    """
    Ambil daftar saham syariah.

    indeks      : "JII70" (default, 70 saham) atau "JII30" (30 saham terbaik)
    github_user : username GitHub kamu (opsional, untuk ambil custom list)
    """
    print(f"\n📋 Mengambil daftar saham syariah ({indeks})...")

    # Prioritas 1: custom list dari GitHub repo kamu
    if github_user:
        dari_github = coba_ambil_dari_github(github_user)
        if dari_github:
            return dari_github

    # Prioritas 2: daftar yang sudah dikurasi
    if indeks == "JII30":
        daftar = DAFTAR_JII30
    else:
        daftar = DAFTAR_JII70

    print(f"  ✅ Menggunakan daftar {indeks}: {len(daftar)} saham")
    return daftar


def filter_saham_syariah(daftar_saham: list, indeks: str = "JII70") -> list:
    """
    Filter daftar saham, hanya kembalikan yang masuk indeks syariah.
    """
    if indeks == "JII30":
        referensi = set(DAFTAR_JII30)
    else:
        referensi = set(DAFTAR_JII70)

    hasil = [s for s in daftar_saham if s.upper() in referensi]
    tidak_syariah = [s for s in daftar_saham if s.upper() not in referensi]

    if tidak_syariah:
        print(f"  ⚠️  Dikeluarkan (bukan syariah): {', '.join(tidak_syariah)}")

    return hasil


def cetak_info_indeks():
    """Tampilkan info ringkas tentang indeks syariah."""
    print("""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📌 INFO INDEKS SAHAM SYARIAH IDX
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
JII70  : 70 saham syariah paling likuid
JII30  : 30 saham terbaik dari JII70
ISSI   : Semua saham syariah di BEI

Daftar diperbarui BEI setiap 6 bulan
(Mei & November).

Update terakhir file ini: Mei 2025
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")


if __name__ == "__main__":
    cetak_info_indeks()
    daftar = ambil_daftar_syariah("JII70")
    print(f"Total saham: {len(daftar)}")
    print(", ".join(daftar[:10]), "...")
