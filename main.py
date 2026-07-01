import os
import telebot
import yt_dlp
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from threading import Thread
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer

# --- RENDER TEKIN TARIFI UCHUN SOXTA PORT OCHISH (ALDASh) ---
def run_dummy_server():
    # Render avtomatik beradigan PORT yoki 10000-portni oladi
    port = int(os.environ.get("PORT", 10000))
    handler = SimpleHTTPRequestHandler
    # Port band bo'lib qolmasligi uchun sharoit yaratamiz
    TCPServer.allow_reuse_address = True
    with TCPServer(("", port), handler) as httpd:
        print(f"Soxta server {port}-portda ishlamoqda...")
        httpd.serve_forever()

# Serverni alohida fonda ishga tushiramiz
Thread(target=run_dummy_server, daemon=True).start()
# --------------------------------------------------------

# Telegram bot tokenini o'rnatamiz
BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

# Yuklash sozlamalari (Cookies ulangan holatda)
ydl_opts = {
    'noplaylist': True,
    'cookiefile': 'cookies.txt'
}

@bot.message_handler(commands=['start'])
def welcome(message):
    bot.reply_to(
        message, 
        "👋 Salom! Men orqali YouTube va Instagram-dan videolarni yuklab olishingiz mumkin.\n"
        "Menga shunchaki video havolasini (linkini) yuboring!"
    )

@bot.message_handler(func=lambda message: True)
def handle_link(message):
    url = message.text
    if "youtube.com" in url or "youtu.be" in url or "instagram.com" in url:
        msg = bot.reply_to(message, "🔍 Video ma'lumotlari yuklanmoqda, iltimos kuting...")
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                formats = info.get('formats', [])
                video_title = info.get('title', 'Video')
                
                markup = InlineKeyboardMarkup()
                seen_resolutions = set()
                
                for f in formats:
                    if f.get('vcodec') != 'none' and f.get('acodec') != 'none' and f.get('resolution'):
                        res = f.get('resolution')
                        if res not in seen_resolutions:
                            seen_resolutions.add(res)
                            callback_data = f"dl|{f.get('format_id')}|{url}"
                            if len(callback_data) <= 64:
                                markup.add(InlineKeyboardButton(text=f"🎬 Yuklash ({res})", callback_data=callback_data))
                
                if seen_resolutions:
                    bot.edit_message_text(
                        chat_id=message.chat.id,
                        message_id=msg.message_id,
                        text=f"🎥 **{video_title}**\n\nYuklash uchun quyidagi sifatlardan birini tanlang:",
                        reply_markup=markup,
                        parse_mode="Markdown"
                    )
                else:
                    bot.edit_message_text("📥 Video yuklanmoqda...", chat_id=message.chat.id, message_id=msg.message_id)
                    download_and_send(message.chat.id, url, 'best')
                    bot.delete_message(message.chat.id, msg.message_id)
                    
        except Exception as e:
            bot.edit_message_text(f"❌ Xatolik yuz berdi: {str(e)}", chat_id=message.chat.id, message_id=msg.message_id)
    else:
        bot.reply_to(message, "⚠️ Iltimos, faqat to'g'ri YouTube yoki Instagram havolasini yuboring.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('dl|'))
def handle_download_callback(call):
    bot.answer_callback_query(call.id, "Yuklash boshlandi...")
    _, format_id, url = call.data.split('|')
    
    msg = bot.send_message(call.message.chat.id, "📥 Server videoni tayyorlamoqda, hozir yuboraman...")
    
    try:
        download_and_send(call.message.chat.id, url, format_id)
        bot.delete_message(call.message.chat.id, msg.message_id)
    except Exception as e:
        bot.edit_message_text(f"❌ Yuklashda xatolik: {str(e)}", call.message.chat.id, msg.message_id)

def download_and_send(chat_id, url, format_id):
    custom_opts = dict(ydl_opts)
    custom_opts['format'] = format_id
    custom_opts['outtmpl'] = f'downloads/%(id)s_{format_id}.%(ext)s'
    
    with yt_dlp.YoutubeDL(custom_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        
        with open(filename, 'rb') as video:
            bot.send_video(chat_id, video, caption="✨ Botingiz orqali daxshatli tezlikda yuklab olindi!")
        
        if os.path.exists(filename):
            os.remove(filename)

if __name__ == "__main__":
    print("Bot muvaffaqiyatli ishga tushdi...")
    bot.infinity_polling()
