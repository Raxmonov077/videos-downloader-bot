import os
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryContext, ContextTypes
import yt_dlp

# Bot tokenini shu yerga qo'yamiz
TOKEN = "8957100892:AAHSW62og9MIE_kqOXmoX8m6o4UT2os9voc"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Salom! Men orqali YouTube va Instagram-dan videolarni yuklab olishingiz mumkin.\n"
        "Menga shunchaki video havolasini (linkini) yuboring!"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not re.match(r'https?://(www\.)?(youtube\.com|youtu\.be|instagram\.com)', url):
        await update.message.reply_text("❌ Iltimos, faqat YouTube yoki Instagram havolasini yuboring!")
        return

    msg = await update.message.reply_text("🔍 Video ma'lumotlari tekshirilmoqda, iltimos kuting...")

    try:
        ydl_opts = {'noplaylist': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])
            
            keyboard = []
            # Sifatlarni saralash (144p dan 4K gacha)
            available_resolutions = ["144p", "240p", "360p", "480p", "720p", "1080p", "1440p", "2160p"]
            seen_res = set()

            for f in formats:
                res = f.get('format_note') or f.get('resolution')
                if res in available_resolutions and res not in seen_res:
                    if f.get('url'):
                        seen_res.add(res)
                        keyboard.append([InlineKeyboardButton(text=f"🎬 {res}", url=f.get('url'))])

            if not keyboard:
                best_url = info.get('url') or (formats[-1].get('url') if formats else None)
                if best_url:
                    keyboard.append([InlineKeyboardButton(text="🎬 Yuklab olish (Eng yaxshi sifat)", url=best_url)])

            if keyboard:
                reply_markup = InlineKeyboardMarkup(keyboard)
                await msg.edit_text("✨ Video topildi! Quyidagi tugma orqali o'zingizga ma'qul sifatda yuklab oling:", reply_markup=reply_markup)
            else:
                await msg.edit_text("❌ Videoni yuklab olish uchun havola topilmadi.")

    except Exception as e:
        await msg.edit_text(f"❌ Xatolik yuz berdi: {str(e)}")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == '__main__':
    main()
