"""
email_alert.py
Modul untuk mengirim email alert sinyal SELL via Gmail SMTP
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone, timedelta

WIB = timezone(timedelta(hours=7))


def format_rupiah(angka) -> str:
    if angka is None:
        return "N/A"
    try:
        return f"Rp{int(angka):,}".replace(",", ".")
    except Exception:
        return str(angka)


def buat_html_sell_alert(laporan: dict) -> str:
    """Buat isi email HTML untuk sinyal SELL."""
    kode = laporan["kode"].replace(".JK", "")
    nama = laporan.get("nama", kode)
    harga = format_rupiah(laporan.get("harga"))
    skor = laporan.get("skor_gabungan", 0)
    skor_t = laporan.get("skor_teknikal", 0)
    skor_f = laporan.get("skor_fundamental", 0)
    skor_a = laporan.get("skor_ai", 0)
    deskripsi = laporan.get("deskripsi", "")
    waktu = datetime.now(WIB).strftime("%d %b %Y %H:%M WIB")

    # Detail teknikal
    detail_t = laporan.get("detail_teknikal", {})
    baris_teknikal = ""
    for nama_ind, d in detail_t.items():
        baris_teknikal += f"<tr><td style='padding:6px 12px;'>{nama_ind}</td><td style='padding:6px 12px;'>{d['label']}</td></tr>"

    # Detail fundamental
    detail_f = laporan.get("detail_fundamental", {})
    baris_fundamental = ""
    for nama_ind, d in detail_f.items():
        baris_fundamental += f"<tr><td style='padding:6px 12px;'>{nama_ind}</td><td style='padding:6px 12px;'>{d['label']}</td></tr>"

    html = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    body {{ font-family: Arial, sans-serif; background: #f5f5f5; margin: 0; padding: 20px; }}
    .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
    .header {{ background: #c0392b; color: white; padding: 24px; text-align: center; }}
    .header h1 {{ margin: 0; font-size: 28px; }}
    .header p {{ margin: 8px 0 0; opacity: 0.9; font-size: 14px; }}
    .badge {{ display: inline-block; background: white; color: #c0392b; padding: 4px 16px; border-radius: 20px; font-weight: bold; font-size: 18px; margin-top: 10px; }}
    .content {{ padding: 24px; }}
    .info-box {{ background: #fdf2f2; border-left: 4px solid #c0392b; padding: 16px; border-radius: 4px; margin-bottom: 20px; }}
    .info-box h2 {{ margin: 0 0 8px; color: #c0392b; font-size: 20px; }}
    .info-box p {{ margin: 4px 0; color: #555; font-size: 14px; }}
    .skor-box {{ display: flex; gap: 12px; margin-bottom: 20px; }}
    .skor-item {{ flex: 1; text-align: center; padding: 12px; border-radius: 8px; background: #f9f9f9; border: 1px solid #eee; }}
    .skor-item .angka {{ font-size: 24px; font-weight: bold; color: #c0392b; }}
    .skor-item .label {{ font-size: 11px; color: #888; margin-top: 4px; }}
    table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 13px; }}
    th {{ background: #f0f0f0; padding: 8px 12px; text-align: left; font-size: 12px; color: #666; }}
    tr:nth-child(even) {{ background: #fafafa; }}
    .footer {{ background: #f9f9f9; padding: 16px 24px; text-align: center; font-size: 12px; color: #999; border-top: 1px solid #eee; }}
    .disclaimer {{ background: #fff8e1; border: 1px solid #ffe082; border-radius: 6px; padding: 12px; margin-top: 16px; font-size: 12px; color: #795548; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>🔴 SELL ALERT</h1>
      <p>{waktu}</p>
      <div class="badge">⚠️ Sinyal Jual Terdeteksi</div>
    </div>
    <div class="content">
      <div class="info-box">
        <h2>{kode} — {nama}</h2>
        <p>💰 Harga Sekarang: <strong>{harga}</strong></p>
        <p>📊 Skor Gabungan: <strong>{skor}/100</strong></p>
        <p>💡 {deskripsi}</p>
      </div>

      <div class="skor-box">
        <div class="skor-item">
          <div class="angka">{skor_t}</div>
          <div class="label">Teknikal</div>
        </div>
        <div class="skor-item">
          <div class="angka">{skor_f}</div>
          <div class="label">Fundamental</div>
        </div>
        <div class="skor-item">
          <div class="angka">{skor_a}</div>
          <div class="label">AI Score</div>
        </div>
        <div class="skor-item">
          <div class="angka" style="color:#c0392b">{skor}</div>
          <div class="label">Total</div>
        </div>
      </div>

      <table>
        <tr><th colspan="2">📈 Analisis Teknikal</th></tr>
        {baris_teknikal}
      </table>

      <table>
        <tr><th colspan="2">🏦 Analisis Fundamental</th></tr>
        {baris_fundamental}
      </table>

      <div class="disclaimer">
        ⚠️ <strong>Disclaimer:</strong> Email ini hanya informasi analisis otomatis, bukan rekomendasi investasi. Selalu lakukan riset sendiri sebelum mengambil keputusan.
      </div>
    </div>
    <div class="footer">
      🤖 Powered by Clau - Kandip's smartest assistant 😎
    </div>
  </div>
</body>
</html>
"""
    return html


def kirim_email_sell(laporan: dict) -> bool:
    """
    Kirim email alert untuk sinyal SELL.
    Membutuhkan variabel environment:
      GMAIL_ADDRESS     : alamat Gmail pengirim
      GMAIL_APP_PASSWORD: App Password Gmail (bukan password biasa)
    """
    gmail = os.getenv("GMAIL_ADDRESS", "").strip()
    app_password = os.getenv("GMAIL_APP_PASSWORD", "").strip()

    if not gmail or not app_password:
        print("  [!] GMAIL_ADDRESS atau GMAIL_APP_PASSWORD belum diisi di Secrets")
        return False

    kode = laporan["kode"].replace(".JK", "")
    harga = format_rupiah(laporan.get("harga"))
    skor = laporan.get("skor_gabungan", 0)
    waktu = datetime.now(WIB).strftime("%d %b %Y %H:%M WIB")

    subject = f"🔴 SELL Alert: {kode} — Skor {skor}/100 | {waktu}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"Clau Alert <{gmail}>"
    msg["To"] = gmail  # kirim ke diri sendiri

    # Versi teks biasa (fallback)
    teks = (
        f"SELL ALERT — {kode}\n"
        f"Harga: {harga}\n"
        f"Skor: {skor}/100\n"
        f"Waktu: {waktu}\n\n"
        f"🤖 Powered by Clau - Kandip's smartest assistant 😎"
    )

    # Versi HTML
    html = buat_html_sell_alert(laporan)

    msg.attach(MIMEText(teks, "plain"))
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(gmail, app_password)
            server.sendmail(gmail, gmail, msg.as_string())
        print(f"  ✅ Email SELL alert terkirim untuk {kode}")
        return True
    except smtplib.SMTPAuthenticationError:
        print("  [!] Gmail authentication gagal — cek App Password kamu")
        return False
    except Exception as e:
        print(f"  [!] Gagal kirim email: {e}")
        return False


def kirim_ringkasan_email(semua_laporan: list) -> bool:
    """
    Kirim ringkasan harian semua sinyal via email.
    """
    gmail = os.getenv("GMAIL_ADDRESS", "").strip()
    app_password = os.getenv("GMAIL_APP_PASSWORD", "").strip()

    if not gmail or not app_password:
        return False

    waktu = datetime.now(WIB).strftime("%d %b %Y %H:%M WIB")
    beli = [r for r in semua_laporan if r["keputusan"] == "BUY"]
    jual = [r for r in semua_laporan if r["keputusan"] == "SELL"]
    tahan = [r for r in semua_laporan if r["keputusan"] == "HOLD"]

    subject = f"📊 Ringkasan Analisis Saham Syariah — {waktu}"

    def baris_saham(r, warna):
        return f"""
        <tr>
          <td style='padding:8px 12px;font-weight:bold;color:{warna}'>{r['kode'].replace('.JK','')}</td>
          <td style='padding:8px 12px;'>{r.get('nama','')[:25]}</td>
          <td style='padding:8px 12px;'>{format_rupiah(r.get('harga'))}</td>
          <td style='padding:8px 12px;font-weight:bold;color:{warna}'>{r['skor_gabungan']}/100</td>
          <td style='padding:8px 12px;font-weight:bold;color:{warna}'>{r['keputusan']}</td>
        </tr>"""

    baris_html = ""
    for r in sorted(beli, key=lambda x: x["skor_gabungan"], reverse=True):
        baris_html += baris_saham(r, "#27ae60")
    for r in sorted(jual, key=lambda x: x["skor_gabungan"]):
        baris_html += baris_saham(r, "#c0392b")
    for r in tahan:
        baris_html += baris_saham(r, "#888")

    html = f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;background:#f5f5f5;padding:20px;">
  <div style="max-width:700px;margin:0 auto;background:white;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.1);">
    <div style="background:#1a237e;color:white;padding:24px;text-align:center;">
      <h1 style="margin:0;">📊 Ringkasan Analisis Saham Syariah</h1>
      <p style="margin:8px 0 0;opacity:0.9;">{waktu}</p>
    </div>
    <div style="padding:24px;">
      <div style="display:flex;gap:12px;margin-bottom:24px;text-align:center;">
        <div style="flex:1;padding:16px;background:#e8f5e9;border-radius:8px;">
          <div style="font-size:32px;font-weight:bold;color:#27ae60;">{len(beli)}</div>
          <div style="color:#888;font-size:13px;">BUY</div>
        </div>
        <div style="flex:1;padding:16px;background:#fde8e8;border-radius:8px;">
          <div style="font-size:32px;font-weight:bold;color:#c0392b;">{len(jual)}</div>
          <div style="color:#888;font-size:13px;">SELL</div>
        </div>
        <div style="flex:1;padding:16px;background:#f5f5f5;border-radius:8px;">
          <div style="font-size:32px;font-weight:bold;color:#888;">{len(tahan)}</div>
          <div style="color:#888;font-size:13px;">HOLD</div>
        </div>
      </div>
      <table style="width:100%;border-collapse:collapse;font-size:13px;">
        <tr style="background:#f0f0f0;">
          <th style="padding:8px 12px;text-align:left;">Kode</th>
          <th style="padding:8px 12px;text-align:left;">Nama</th>
          <th style="padding:8px 12px;text-align:left;">Harga</th>
          <th style="padding:8px 12px;text-align:left;">Skor</th>
          <th style="padding:8px 12px;text-align:left;">Sinyal</th>
        </tr>
        {baris_html}
      </table>
      <div style="background:#fff8e1;border:1px solid #ffe082;border-radius:6px;padding:12px;margin-top:16px;font-size:12px;color:#795548;">
        ⚠️ Ini bukan rekomendasi investasi. Selalu lakukan riset sendiri.
      </div>
    </div>
    <div style="background:#f9f9f9;padding:16px;text-align:center;font-size:12px;color:#999;border-top:1px solid #eee;">
      🤖 Powered by Clau - Kandip's smartest assistant 😎
    </div>
  </div>
</body>
</html>"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"Clau Alert <{gmail}>"
    msg["To"] = gmail
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(gmail, app_password)
            server.sendmail(gmail, gmail, msg.as_string())
        print("  ✅ Ringkasan email terkirim!")
        return True
    except Exception as e:
        print(f"  [!] Gagal kirim ringkasan email: {e}")
        return False
