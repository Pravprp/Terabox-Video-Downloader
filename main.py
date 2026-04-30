import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from keep_alive import keep_alive

# We fetch the token from Render's environment variables for security
BOT_TOKEN = os.environ.get('BOT_TOKEN')

if not BOT_TOKEN:
    raise ValueError("No BOT_TOKEN found. Please set it in your environment variables.")

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Send me any video link, and I will generate watch/download buttons for you!")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    text = message.text.strip()
    
    # Check if the user sent a valid URL
    if text.startswith('http://') or text.startswith('https://'):
        
        # Generate the two different server URLs
        final_url_1 = "https://www.teraboxdownloader.pro/p/fs.html?q=" + text
        final_url_2 = "https://teradownloader.com/download?l=" + text

        markup = InlineKeyboardMarkup()
        
        # Create Button 1 (Server 1)
        button1 = InlineKeyboardButton(
            text="Watch / Download Server 1", 
            web_app=WebAppInfo(url=final_url_1)
        )
        
        # Create Button 2 (Server 2)
        button2 = InlineKeyboardButton(
            text="Watch / Download Server 2", 
            web_app=WebAppInfo(url=final_url_2)
        )
        
        # Adding them one by one stacks them vertically, which looks cleaner for long button names
        markup.add(button1)
        markup.add(button2)

        bot.reply_to(message, "Choose a server below:", reply_markup=markup)
    else:
        bot.reply_to(message, "Please send a valid link starting with http:// or https://")

# 1. Start the web server for UptimeRobot
keep_alive()

# 2. Start the Telegram bot
print("Bot is running...")
bot.infinity_polling()
