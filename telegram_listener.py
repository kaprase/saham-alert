"""
telegram_listener.py
Bot Telegram yang mendengarkan perintah dari Kandip secara real-time.

Perintah yang tersedia:
  /portfolio          — lihat semua saham + profit/loss
  /beli BRIS 1500 10  — catat beli BRIS harga 1500, 10 lot
  /jual BRIS 1700 5   — catat jual BRIS harga 1700, 5 lot
  /hapus BRIS         — hapus BRIS dari portfolio
  /analisis BRIS      — analisis teknikal + fundamental BRIS sekarang
  /help               — tampilkan semua perintah

Jalankan dengan: python telegram_listener.py
"""

import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

from portfolio import (
    catat_beli,
    catat_jual,
    hapus_saham,
    hitung_portfolio_lengkap,
    format_pesan_portfolio,
    format_rupiah,
)

load_dotenv()
logging.basicConfig(level=logging.INFO)


# ── Helper ─────────────────────────────────────────────────

def cek_user(update: Update) -> bool:
    """Pastikan hanya Kandip yang bisa pakai bot ini."""
    chat_id = str(update.effective_chat.id)
    allowed = os.getenv("TELEGRAM_CHAT_ID", "")
    return chat_id == allowed


async def tolak(update: Update):
    await update.message.reply_text("⛔ Maaf, bot ini khusus untuk Kandip saja!")


# ── Command Handlers ───────────────────────────────────────

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not cek_user(update):
        return await tolak(update)

    pesan = (
        "🤖 *Clau — Portfolio Commands*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "📊 `/portfolio`\n"
        "   Lihat semua saham + profit/loss\n\n"
        "🟢 `/beli BRIS 1500 10`\n"
        "   Catat beli BRIS harga 1500, 10 lot\n\n"
        "🔴 `/jual BRIS 1700 5`\n"
        "   Catat jual BRIS harga 1700, 5 lot\n\n"
        "🗑 `/hapus BRIS`\n"
        "   Hapus BRIS dari portfolio\n\n"
        "🔬 `/analisis BRIS`\n"
        "   Analisis BRIS sekarang\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🤖 Powered by Clau - Kandip's smartest assistant 😎"
    )
    await update.message.reply_text(pesan, parse_mode="Markdown")


async def cmd_portfolio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not cek_user(update):
        return await tolak(update)

    await update.message.reply_text("⏳ Mengambil harga terkini...")
    data = hitung_portfolio_lengkap()
    pesan = format_pesan_portfolio(data)
    await update.message.reply_text(pesan, parse_mode="Markdown")


async def cmd_beli(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not cek_user(update):
        return await tolak(update)

    args = context.args
    if len(args) < 3:
        await update.message.reply_text(
            "⚠️ Format salah!\nGunakan: `/beli BRIS 1500 10`\n"
            "_(kode saham, harga beli, jumlah lot)_",
            parse_mode="Markdown"
        )
        return

    try:
        kode = args[0].upper()
        harga = float(args[1].replace(",", "."))
        lot = int(args[2])
    except ValueError:
        await update.message.reply_text("⚠️ Harga dan lot harus berupa angka!")
        return

    hasil = catat_beli(kode, harga, lot)
    kode_bersih = hasil["kode"].replace(".JK", "")
    modal = harga * lot * 100

    if hasil["aksi"] == "baru":
        pesan = (
            f"✅ *Berhasil dicatat!*\n\n"
            f"📌 Saham: *{kode_bersih}*\n"
            f"💰 Harga beli: *{format_rupiah(harga)}*\n"
            f"📦 Jumlah: *{lot} lot* ({lot*100:,} lembar)\n"
            f"💼 Total modal: *{format_rupiah(modal)}*\n\n"
            f"🤖 Powered by Clau - Kandip's smartest assistant 😎"
        )
    else:
        data = hasil["data"]
        pesan = (
            f"🔄 *Portfolio diperbarui!*\n\n"
            f"📌 Saham: *{kode_bersih}*\n"
            f"💰 Harga rata-rata baru: *{format_rupiah(data['harga_beli'])}*\n"
            f"📦 Total lot: *{data['lot']} lot*\n\n"
            f"🤖 Powered by Clau - Kandip's smartest assistant 😎"
        )

    await update.message.reply_text(pesan, parse_mode="Markdown")


async def cmd_jual(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not cek_user(update):
        return await tolak(update)

    args = context.args
    if len(args) < 3:
        await update.message.reply_text(
            "⚠️ Format salah!\nGunakan: `/jual BRIS 1700 5`",
            parse_mode="Markdown"
        )
        return

    try:
        kode = args[0].upper()
        harga_jual = float(args[1].replace(",", "."))
        lot = int(args[2])
    except ValueError:
        await update.message.reply_text("⚠️ Harga dan lot harus berupa angka!")
        return

    hasil = catat_jual(kode, harga_jual, lot)

    if "error" in hasil:
        await update.message.reply_text(f"⚠️ {hasil['error']}")
        return

    emoji = "🟢" if hasil["profit_total"] >= 0 else "🔴"
    tanda = "+" if hasil["profit_total"] >= 0 else ""
    kode_bersih = hasil["kode"].replace(".JK", "")

    pesan = (
        f"{emoji} *Penjualan dicatat!*\n\n"
        f"📌 Saham: *{kode_bersih}*\n"
        f"💰 Harga beli: *{format_rupiah(hasil['harga_beli'])}*\n"
        f"💸 Harga jual: *{format_rupiah(harga_jual)}*\n"
        f"📦 Lot dijual: *{lot} lot*\n"
        f"{'━'*20}\n"
        f"{emoji} Profit/Loss: *{format_rupiah(hasil['profit_total'])}* ({tanda}{hasil['pct']:.1f}%)\n"
        f"📋 Status: _{hasil['status']}_\n\n"
        f"🤖 Powered by Clau - Kandip's smartest assistant 😎"
    )
    await update.message.reply_text(pesan, parse_mode="Markdown")


async def cmd_hapus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not cek_user(update):
        return await tolak(update)

    if not context.args:
        await update.message.reply_text("⚠️ Gunakan: `/hapus BRIS`", parse_mode="Markdown")
        return

    kode = context.args[0].upper()
    hasil = hapus_saham(kode)

    if "error" in hasil:
        await update.message.reply_text(f"⚠️ {hasil['error']}")
    else:
        await update.message.reply_text(
            f"🗑 *{hasil['kode'].replace('.JK','')} berhasil dihapus* dari portfolio.\n\n"
            f"🤖 Powered by Clau - Kandip's smartest assistant 😎",
            parse_mode="Markdown"
        )


async def cmd_analisis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not cek_user(update):
        return await tolak(update)

    if not context.args:
        await update.message.reply_text("⚠️ Gunakan: `/analisis BRIS`", parse_mode="Markdown")
        return

    kode = context.args[0].upper()
    if not kode.endswith(".JK"):
        kode += ".JK"

    await update.message.reply_text(f"⏳ Menganalisis *{kode.replace('.JK','')}*...", parse_mode="Markdown")

    try:
        from data_fetcher import ambil_data_saham, ambil_info_saham
        from analisis_teknikal import analisis_sinyal_teknikal
        from analisis_fundamental import analisis_fundamental
        from analisis_ai import prediksi_ai
        from decision_engine import buat_laporan_lengkap, format_pesan_telegram

        df = ambil_data_saham(kode)
        info = ambil_info_saham(kode)

        if df is None or df.empty:
            await update.message.reply_text(f"⚠️ Data {kode} tidak tersedia.")
            return

        t = analisis_sinyal_teknikal(df)
        f = analisis_fundamental(info)
        a = prediksi_ai(df)
        laporan = buat_laporan_lengkap(kode, info, t, f, a)
        pesan = format_pesan_telegram(laporan)
        await update.message.reply_text(pesan, parse_mode="Markdown")

    except Exception as e:
        await update.message.reply_text(f"⚠️ Gagal analisis: {e}")


# ── Main ───────────────────────────────────────────────────

def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token or token == "isi_token_bot_kamu_disini":
        print("❌ Token Telegram belum diisi di file .env")
        return

    print("🤖 Clau Bot aktif — menunggu perintah dari Kandip...")
    print("   Tekan Ctrl+C untuk berhenti\n")

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("start", cmd_help))
    app.add_handler(CommandHandler("portfolio", cmd_portfolio))
    app.add_handler(CommandHandler("beli", cmd_beli))
    app.add_handler(CommandHandler("jual", cmd_jual))
    app.add_handler(CommandHandler("hapus", cmd_hapus))
    app.add_handler(CommandHandler("analisis", cmd_analisis))

    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
