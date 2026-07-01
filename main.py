import os
import re
import telebot
import yt_dlp
from threading import Thread
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer

# --- RENDER UCHUN MAJBURIY SOXTA PORT ---
def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    handler = SimpleHTTPRequestHandler
    TCPServer.allow_reuse_address = True
    try:
        with TCPServer(("", port), handler) as httpd:
            print(f"Soxta server {port}-portda faol.")
            httpd.serve_forever()
    except Exception as e:
        print(f"Server xatosi: {e}")

Thread(target=run_dummy_server, daemon=True).start()
# ---------------------------------------

BOT_TOKEN = os.environ.get("BOT_TOKEN")
# Ziddiyatlarni (Conflict) oldini olish uchun eski webhooklarni tozalab ulanamiz
bot = telebot.TeleBot(BOT_TOKEN, threaded=False)
bot.remove_webhook()

# Barcha platformalar uchun eng universal va barqaror yuklash sozlamalari
ydl_opts = {
    'noplaylist': True,
    'cookiefile': 'cookies.txt',
    'format': 'best',  # Sifat muammolarini chetlab o'tish uchun
    'outtmpl': 'downloads/%(id)s.%(ext)s',
    'quiet': True,
    'no_warnings': True
}

# Uzun matn (ichida heshteg, emoji bo'lsa ham) ichidan toza havolani ajratib olish
def extract_url(text):
    urls = re.findall(r'(https?://[^\s]+)', text)
    return urls[0] if urls else None

@bot.message_handler(commands=['start'])
def welcome(message):
    bot.reply_to(
        message, 
        "👋 Salom! Men orqali YouTube, Instagram va TikTok-dan videolarni muammosiz yuklab olasiz.\n"
        "Menga video havolasi (linki) bor istalgan matnni yuboring, heshteglar xalaqit bermaydi!"
    )

@bot.message_handler(func=lambda message: True)
def handle_link(message):
    url = extract_url(message.text)
    
    if not url:
        bot.reply_to(message, "⚠️ Kechirasiz, bu matn ichida hech qanday video havola topilmadi.")
        return

    msg = bot.reply_to(message, "📥 Video aniqlanmoqda va yuklanmoqda... Iltimos kuting...")
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # Fayl kengaytmasini aniqlashtiramiz
            if not os.path.exists(filename):
                base, _ = os.path.splitext(filename)
                for ext in ['mp4', 'mkv', 'webm', '3gp', 'm4a']:
                    if os.path.exists(f"{base}.{ext}"):
                        filename = f"{base}.{ext}"
                        break
            
            bot.edit_message_text("🚀 Video tayyor! Telegram'ga yuborilmoqda...", chat_id=message.chat.id, message_id=msg.message_id)
            
            with open(filename, 'rb') as video:
                bot.send_video(message.chat.id, video, caption="✨ Videongiz muvaffaqiyatli yuklab olindi!")
            
            if os.path.exists(filename):
                os.remove(filename)
            
            bot.delete_message(message.chat.id, msg.message_id)
                
    except Exception as e:
        bot.edit_message_text(f"❌ Yuklashda xatolik: Video juda katta bo'lishi mumkin yoki platforma blokladi.", chat_id=message.chat.id, message_id=msg.message_id)
        print(f"Xatolik tafsiloti: {str(e)}")

if __name__ == "__main__":
    print("Bot muvaffaqiyatli ishga tushdi...")
    bot.infinity_polling(skip_pending=True) # Eski kelib qolib ketgan xabarlarni tashlab yuboradi
