import os
import telebot
import yt_dlp
from threading import Thread
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer

# --- RENDER TEKIN TARIFI UCHUN SOXTA PORT OCHISH ---
def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    handler = SimpleHTTPRequestHandler
    TCPServer.allow_reuse_address = True
    with TCPServer(("", port), handler) as httpd:
        print(f"Soxta server {port}-portda ishlamoqda...")
        httpd.serve_forever()

Thread(target=run_dummy_server, daemon=True).start()
# --------------------------------------------------------

# Telegram bot tokenini o'rnatamiz
BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

# Yuklash sozlamalari (Cookies ulangan va format eng yaxshisiga sozlangan)
ydl_opts = {
    'noplaylist': True,
    'cookiefile': 'cookies.txt',
    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',  # Eng yaxshi sifatni avtomatik birlashtiradi
    'outtmpl': 'downloads/%(id)s.%(ext)s',
    'merge_output_format': 'mp4'  # Yakuniy format har doim MP4 bo'ladi
}

@bot.message_handler(commands=['start'])
def welcome(message):
    bot.reply_to(
        message, 
        "👋 Salom! Men orqali YouTube va Instagram-dan videolarni daxshatli tez yuklab olishingiz mumkin.\n"
        "Menga shunchaki video havolasini (linkini) yuboring!"
    )

@bot.message_handler(func=lambda message: True)
def handle_link(message):
    url = message.text
    if "youtube.com" in url or "youtu.be" in url or "instagram.com" in url:
        msg = bot.reply_to(message, "📥 Video aniqlanmoqda va serverga yuklanmoqda... Iltimos kuting...")
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                
                # Agar fayl formati o'zgargan bo'lsa (mkv o'rniga mp4 qilingan bo'lsa), haqiqiy nomini tekshiramiz
                if not os.path.exists(filename):
                    base, _ = os.path.splitext(filename)
                    filename = base + ".mp4"
                
                bot.edit_message_text("🚀 Server videoni tayyorladi! Telegram'ga yuborilmoqda...", chat_id=message.chat.id, message_id=msg.message_id)
                
                # Videoni Telegram'ga yuboramiz
                with open(filename, 'rb') as video:
                    bot.send_video(message.chat.id, video, caption="✨ Botingiz orqali daxshatli tezlikda yuklab olindi!")
                
                # Serverda joy qolishi uchun faylni o'chiramiz
                if os.path.exists(filename):
                    os.remove(filename)
                
                bot.delete_message(message.chat.id, msg.message_id)
                    
        except Exception as e:
            bot.edit_message_text(f"❌ Xatolik yuz berdi: {str(e)}", chat_id=message.chat.id, message_id=msg.message_id)
    else:
        bot.reply_to(message, "⚠️ Iltimos, faqat to'g'ri YouTube yoki Instagram havolasini yuboring.")

if __name__ == "__main__":
    print("Bot muvaffaqiyatli ishga tushdi...")
    bot.infinity_polling()
