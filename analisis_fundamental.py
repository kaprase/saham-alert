"""
analisis_fundamental.py
Modul untuk analisis fundamental saham IDX
"""


def analisis_fundamental(info: dict) -> dict:
    """
    Analisis kondisi fundamental saham.
    Mengembalikan skor 0-100 dan detail penilaian.
    """
    sinyal = []
    skor_total = 0
    bobot_total = 0

    # ── P/E Ratio ─────────────────────────────────────
    pe = info.get("pe_ratio")
    if pe and pe > 0:
        bobot = 30
        if pe < 10:
            skor_pe = 85
            label_pe = f"P/E {pe:.1f} — Sangat murah (undervalued) 🟢"
        elif pe < 15:
            skor_pe = 75
            label_pe = f"P/E {pe:.1f} — Murah 🟢"
        elif pe < 25:
            skor_pe = 55
            label_pe = f"P/E {pe:.1f} — Wajar ⚪"
        elif pe < 40:
            skor_pe = 35
            label_pe = f"P/E {pe:.1f} — Agak mahal 🟡"
        else:
            skor_pe = 15
            label_pe = f"P/E {pe:.1f} — Terlalu mahal 🔴"
        sinyal.append(("P/E Ratio", skor_pe, label_pe, bobot))
        skor_total += skor_pe * bobot
        bobot_total += bobot

    # ── ROE ───────────────────────────────────────────
    roe = info.get("roe")
    if roe:
        roe_pct = roe * 100
        bobot = 30
        if roe_pct > 20:
            skor_roe = 90
            label_roe = f"ROE {roe_pct:.1f}% — Sangat baik 🟢"
        elif roe_pct > 15:
            skor_roe = 75
            label_roe = f"ROE {roe_pct:.1f}% — Baik 🟢"
        elif roe_pct > 10:
            skor_roe = 55
            label_roe = f"ROE {roe_pct:.1f}% — Cukup ⚪"
        elif roe_pct > 5:
            skor_roe = 35
            label_roe = f"ROE {roe_pct:.1f}% — Rendah 🟡"
        else:
            skor_roe = 15
            label_roe = f"ROE {roe_pct:.1f}% — Sangat rendah 🔴"
        sinyal.append(("ROE", skor_roe, label_roe, bobot))
        skor_total += skor_roe * bobot
        bobot_total += bobot

    # ── Debt to Equity ────────────────────────────────
    der = info.get("der")
    if der and der >= 0:
        bobot = 20
        if der < 0.5:
            skor_der = 85
            label_der = f"DER {der:.2f} — Hutang sangat rendah 🟢"
        elif der < 1.0:
            skor_der = 70
            label_der = f"DER {der:.2f} — Hutang rendah 🟢"
        elif der < 2.0:
            skor_der = 45
            label_der = f"DER {der:.2f} — Hutang sedang ⚪"
        elif der < 3.0:
            skor_der = 25
            label_der = f"DER {der:.2f} — Hutang tinggi 🟡"
        else:
            skor_der = 10
            label_der = f"DER {der:.2f} — Hutang sangat tinggi 🔴"
        sinyal.append(("Debt/Equity", skor_der, label_der, bobot))
        skor_total += skor_der * bobot
        bobot_total += bobot

    # ── EPS ───────────────────────────────────────────
    eps = info.get("eps")
    if eps:
        bobot = 20
        if eps > 500:
            skor_eps = 90
            label_eps = f"EPS Rp{eps:.0f} — Laba sangat besar 🟢"
        elif eps > 200:
            skor_eps = 75
            label_eps = f"EPS Rp{eps:.0f} — Laba besar 🟢"
        elif eps > 50:
            skor_eps = 55
            label_eps = f"EPS Rp{eps:.0f} — Laba cukup ⚪"
        elif eps > 0:
            skor_eps = 35
            label_eps = f"EPS Rp{eps:.0f} — Laba kecil 🟡"
        else:
            skor_eps = 5
            label_eps = f"EPS Rp{eps:.0f} — RUGI 🔴"
        sinyal.append(("EPS", skor_eps, label_eps, bobot))
        skor_total += skor_eps * bobot
        bobot_total += bobot

    if bobot_total == 0:
        return {"skor": 50, "detail": {}, "catatan": "Data fundamental tidak tersedia"}

    skor_akhir = int(skor_total / bobot_total)

    return {
        "skor": skor_akhir,
        "detail": {nama: {"skor": s, "label": l} for nama, s, l, _ in sinyal},
        "nama": info.get("nama", "N/A"),
        "sektor": info.get("sektor", "N/A"),
    }
