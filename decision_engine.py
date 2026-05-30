"""
decision_engine.py
Mesin pengambil keputusan BUY / HOLD / SELL berdasarkan gabungan analisis
"""

import os


def format_rupiah(angka) -> str:
    if angka is None:
        return "N/A"
    try:
        return f"Rp{int(angka):,}".replace(",", ".")
    except Exception:
        return str(angka)


def format_market_cap(mc) -> str:
    if mc is None:
        return "N/A"
    try:
        t = mc / 1_000_000_000_000
        return f"Rp{t:.1f}T"
    except Exception:
        return "N/A"


def hitung_skor_gabungan(
    hasil_teknikal: dict,
    hasil_fundamental: dict,
    hasil_ai: dict,
    bobot: dict | None = None,
) -> dict:
    """
    Gabungkan skor dari tiga mesin analisis.
    Bobot default: Teknikal 40%, Fundamental 35%, AI 25%
    """
    if bobot is None:
        bobot = {"teknikal": 0.40, "fundamental": 0.35, "ai": 0.25}

    skor_t = hasil_teknikal.get("skor", 50)
    skor_f = hasil_fundamental.get("skor", 50)
    skor_a = hasil_ai.get("skor", 50)

    skor_gabungan = (
        skor_t * bobot["teknikal"]
        + skor_f * bobot["fundamental"]
        + skor_a * bobot["ai"]
    )

    return {
        "skor_gabungan": int(skor_gabungan),
        "skor_teknikal": skor_t,
        "skor_fundamental": skor_f,
        "skor_ai": skor_a,
    }


def tentukan_keputusan(skor_gabungan: int) -> dict:
    """
    Tentukan keputusan BUY / HOLD / SELL berdasarkan skor.
    """
    skor_beli = int(os.getenv("SKOR_BUY", 65))
    skor_jual = int(os.getenv("SKOR_SELL", 35))

    if skor_gabungan >= skor_beli:
        return {
            "keputusan": "BUY",
            "emoji": "🟢",
            "kekuatan": "KUAT" if skor_gabungan >= 75 else "MODERAT",
            "deskripsi": "Kondisi teknikal dan fundamental mendukung pembelian",
        }
    elif skor_gabungan <= skor_jual:
        return {
            "keputusan": "SELL",
            "emoji": "🔴",
            "kekuatan": "KUAT" if skor_gabungan <= 25 else "MODERAT",
            "deskripsi": "Kondisi menunjukkan tekanan jual / valuasi terlalu mahal",
        }
    else:
        return {
            "keputusan": "HOLD",
            "emoji": "⚪",
            "kekuatan": "NETRAL",
            "deskripsi": "Belum ada sinyal yang jelas — lebih baik tunggu",
        }


def buat_laporan_lengkap(
    kode: str,
    info: dict,
    hasil_teknikal: dict,
    hasil_fundamental: dict,
    hasil_ai: dict,
) -> dict:
    """
    Gabungkan semua hasil menjadi laporan lengkap.
    """
    skor = hitung_skor_gabungan(hasil_teknikal, hasil_fundamental, hasil_ai)
    keputusan = tentukan_keputusan(skor["skor_gabungan"])

    return {
        "kode": kode,
        "nama": info.get("nama", kode),
        "sektor": info.get("sektor", "N/A"),
        "harga": info.get("harga_sekarang"),
        "market_cap": info.get("market_cap"),
        "pe_ratio": info.get("pe_ratio"),
        "volume": info.get("volume"),
        **skor,
        **keputusan,
        "detail_teknikal": hasil_teknikal.get("detail", {}),
        "detail_fundamental": hasil_fundamental.get("detail", {}),
        "label_ai": hasil_ai.get("label", "N/A"),
        "prob_naik": hasil_ai.get("probabilitas_naik", 0.5),
    }


def format_pesan_telegram(laporan: dict) -> str:
    """
    Format laporan menjadi pesan Telegram yang rapi.
    """
    k = laporan
    skor = k["skor_gabungan"]

    # Bar progress skor
    kotak_penuh = int(skor / 10)
    bar = "█" * kotak_penuh + "░" * (10 - kotak_penuh)

    baris = [
        f"{k['emoji']} *{k['keputusan']} — {k['kode']}*",
        f"_{k['nama']}_",
        f"━━━━━━━━━━━━━━━━━━━━",
        f"💰 Harga: *{format_rupiah(k['harga'])}*",
        f"📊 Skor: *{skor}/100* `[{bar}]`",
        f"🏢 Sektor: {k['sektor']}",
        f"💼 Kap. Pasar: {format_market_cap(k['market_cap'])}",
        f"",
        f"📈 *Analisis Teknikal* ({k['skor_teknikal']}/100)",
    ]

    for nama, d in k["detail_teknikal"].items():
        baris.append(f"  • {nama}: {d['label']}")

    baris += [
        f"",
        f"🏦 *Analisis Fundamental* ({k['skor_fundamental']}/100)",
    ]

    for nama, d in k["detail_fundamental"].items():
        baris.append(f"  • {nama}: {d['label']}")

    baris += [
        f"",
        f"🤖 *AI/Machine Learning* ({k['skor_ai']}/100)",
        f"  • {k['label_ai']}",
        f"  • Probabilitas naik: *{k['prob_naik']*100:.0f}%*",
        f"",
        f"━━━━━━━━━━━━━━━━━━━━",
        f"💡 *{k['deskripsi']}*",
        f"⚠️ _Bukan rekomendasi investasi. DYOR!_",
    ]

    return "\n".join(baris)
