import os
import re
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

BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

# Barqaror yuklash sozlamalari
ydl_opts = {
    'noplaylist': True,
    'cookiefile': 'cookies.txt',
    'format': 'best',  # Format xatoliklari chiqmasligi uchun eng universal rejim
    'outtmpl': 'downloads/%(id)s.%(ext)s',
}

# Matn ichidan linkni ajratib olish funksiyasi
def extract_url(text):
    urls = re.findall(r'(https?://[^\s]+)', text)
    return urls[0] if urls else None

@bot.message_handler(commands=['start'])
def welcome(message):
    bot.reply_to(
        message, 
        "👋 Salom! Men orqali YouTube va Instagram-dan videolarni muammosiz yuklab olishingiz mumkin.\n"
        "Menga video havolasi bor istalgan matnni yuborishingiz mumkin!"
    )

@bot.message_handler(func=lambda message: True)
def handle_link(message):
    # Matn ichidan havolani qidirib topamiz
    url = extract_url(message.text)
    
    if not url:
        bot.reply_to(message, "⚠️ Iltimos, xabarda to'g'ri havola (link) borligini tekshiring.")
        return

    if "youtube.com" in url or "youtu.be" in url or "instagram.com" in url:
        msg = bot.reply_to(message, "📥 Video aniqlanmoqda va serverga yuklanmoqda... Iltimos kuting...")
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                
                # Agar kengaytma o'zgargan bo'lsa tekshiramiz
                if not os.path.exists(filename):
                    base, _ = os.path.splitext(filename)
                    for ext in ['mp4', 'mkv', 'webm', '3gp']:
                        if os.path.exists(f"{base}.{ext}"):
                            filename = f"{base}.{ext}"
                            break
                
                bot.edit_message_text("🚀 Server videoni tayyorladi! Telegram'ga yuborilmoqda...", chat_id=message.chat.id, message_id=msg.message_id)
                
                with open(filename, 'rb') as video:
                    bot.send_video(message.chat.id, video, caption="✨ Botingiz orqali muvaffaqiyatli yuklab olindi!")
                
                if os.path.exists(filename):
                    os.remove(filename)
                
                bot.delete_message(message.chat.id, msg.message_id)
                    
        except Exception as e:
            bot.edit_message_text(f"❌ Xatolik yuz berdi: {str(e)}", chat_id=message.chat.id, message_id=msg.message_id)
    else:
        bot.reply_to(message, "⚠️ Kechirasiz, hozircha faqat YouTube va Instagram havolalarini qo'llab-quvvatlayman.")

if __name__ == "__main__":
    print("Bot muvaffaqiyatli ishga tushdi...")
    bot.infinity_polling()
