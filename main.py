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
    bot.reply_to(message, "Send me any video link, and I will generate a watch online button for you!")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    text = message.text.strip()
    
    # Check if the user sent a valid URL
    if text.startswith('http://') or text.startswith('https://'):
        base_url = "https://www.teraboxdownloader.pro/p/fs.html?q="
        final_url = base_url + text

        # Create the inline button using WebAppInfo to skip the popup
        markup = InlineKeyboardMarkup()
        button = InlineKeyboardButton(
            text="Watch Video Online 🎬", 
            web_app=WebAppInfo(url=final_url)
        )
        markup.add(button)

        bot.reply_to(message, "Here is your generated link:", reply_markup=markup)
    else:
        bot.reply_to(message, "Please send a valid link starting with http:// or https://")

# 1. Start the web server for UptimeRobot
keep_alive()

# 2. Start the Telegram bot
print("Bot is running...")
bot.infinity_polling()
