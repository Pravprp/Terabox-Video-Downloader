import os
import time
import telebot
import re
import threading
from collections import defaultdict
from urllib.parse import urlparse
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from keep_alive import keep_alive

# Fetch the token from Render's environment variables
BOT_TOKEN = os.environ.get('BOT_TOKEN')

if not BOT_TOKEN:
    raise ValueError("No BOT_TOKEN found. Please set it in your environment variables.")

bot = telebot.TeleBot(BOT_TOKEN)

# Create a queue/lock system for each user so rapid forwarded messages process sequentially
user_locks = defaultdict(threading.Lock)

def is_valid_terabox_url(url):
    """Safely validates if the URL is a real Terabox link."""
    try:
        parsed = urlparse(url)
        if parsed.scheme in ['http', 'https'] and 'terabox' in parsed.netloc.lower():
            return True
        return False
    except Exception:
        return False

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    if message.chat.type != 'private':
        return
        
    bot.reply_to(message, "Send or forward me any Terabox video link, and I will generate watch/download buttons for you! You can even forward multiple messages at once.")

# Added content_types to catch forwarded videos/photos that have links in their captions
@bot.message_handler(content_types=['text', 'photo', 'video', 'document'])
def handle_message(message):
    if message.chat.type != 'private':
        return

    chat_id = message.chat.id
    
    # Extract text from a normal message OR a media caption
    text_content = message.text or message.caption or ""
    
    # Find all URLs in the message using regex
    all_urls = re.findall(r'(https?://[^\s]+)', text_content)
    
    # Filter out anything that isn't a Terabox link
    valid_urls = [url for url in all_urls if is_valid_terabox_url(url)]
    
    # Check if the message was forwarded
    is_forwarded = bool(message.forward_date)

    if not valid_urls:
        # If it's a forwarded message without links, ignore it silently so we don't spam the user.
        # Only scold them if they manually typed an invalid link.
        if not is_forwarded and text_content.strip():
            bot.reply_to(message, "❌ Invalid Link. Please send a valid Terabox link starting with http:// or https://")
        return

    # Acquire the lock for this specific user. 
    # If 5 messages are forwarded at once, they will line up here and process one by one.
    with user_locks[chat_id]:
        for url in valid_urls:
            process_single_link(message, url)

def process_single_link(message, url):
    """Handles the UI animation and button generation for a single link."""
    try:
        # 1. Initial Status (Shows a snippet of the URL so they know which one is processing)
        short_url = url[:30] + "..." if len(url) > 30 else url
        status_message = bot.reply_to(message, f"⏳ Analysing Link...\n{short_url}")
        time.sleep(1.5)
        
        # 2. Processing
        bot.edit_message_text(
            chat_id=status_message.chat.id, 
            message_id=status_message.message_id, 
            text=f"🔄 Processing...\n{short_url}"
        )
        time.sleep(1.5)

        # 3. Generating Buttons
        final_url_1 = f"https://www.teraboxdownloader.pro/p/fs.html?q={url}"
        final_url_2 = f"https://teradownloader.com/download?l={url}"

        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton(text="Watch / Download Server 1", web_app=WebAppInfo(url=final_url_1)))
        markup.add(InlineKeyboardButton(text="Watch / Download Server 2", web_app=WebAppInfo(url=final_url_2)))

        # Final Update
        bot.edit_message_text(
            chat_id=status_message.chat.id, 
            message_id=status_message.message_id, 
            text="✅ Choose a server below:", 
            reply_markup=markup
        )
        
        # Small delay at the end of each link to protect against Telegram rate limits
        time.sleep(0.5)
        
    except Exception as e:
        print(f"Error handling message: {e}")
        bot.send_message(message.chat.id, "⚠️ An error occurred while processing this link. Please try again.")

# 1. Start the web server for UptimeRobot
keep_alive()

# 2. Start the Telegram bot
print("Bot is running...")
bot.infinity_polling()
