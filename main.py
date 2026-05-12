import os
import time
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from keep_alive import keep_alive

# Fetch the token from Render's environment variables
BOT_TOKEN = os.environ.get('BOT_TOKEN')

if not BOT_TOKEN:
    raise ValueError("No BOT_TOKEN found. Please set it in your environment variables.")

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    # Ignore commands sent in groups/channels
    if message.chat.type != 'private':
        return
        
    bot.reply_to(message, "Send me any Terabox video link, and I will generate watch/download buttons for you!")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    # 1. STRICTLY PRIVATE DMs ONLY
    if message.chat.type != 'private':
        return

    text = message.text.strip()
    
    # 2. Basic check: Is it a URL at all?
    if not (text.startswith('http://') or text.startswith('https://')):
        bot.reply_to(message, "Please send a valid link starting with http:// or https://")
        return

    # 3. Send the first "loading" frame
    status_message = bot.reply_to(message, "⏳ Analysing Link...")
    
    # Wait for 2 seconds to simulate processing
    time.sleep(2)
    
    # 4. Validation check: Does it contain "terabox"? 
    if 'terabox' not in text.lower():
        bot.edit_message_text(
            chat_id=status_message.chat.id, 
            message_id=status_message.message_id, 
            text="Link Creation failed Due to Invalid Link. Please Provide a Valid link to Proceed 😔"
        )
        return

    # 5. If the link is valid, continue the animation
    bot.edit_message_text(
        chat_id=status_message.chat.id, 
        message_id=status_message.message_id, 
        text="🔄 Processing..."
    )
    time.sleep(2)

    bot.edit_message_text(
        chat_id=status_message.chat.id, 
        message_id=status_message.message_id, 
        text="⚙️ Creating Link..."
    )
    time.sleep(2)

    # 6. Generate the final URLs and Buttons
    final_url_1 = "https://www.teraboxdownloader.pro/p/fs.html?q=" + text
    final_url_2 = "https://teradownloader.com/download?l=" + text

    markup = InlineKeyboardMarkup()
    
    button1 = InlineKeyboardButton(
        text="Watch / Download Server 1", 
        web_app=WebAppInfo(url=final_url_1)
    )
    button2 = InlineKeyboardButton(
        text="Watch / Download Server 2", 
        web_app=WebAppInfo(url=final_url_2)
    )
    
    markup.add(button1)
    markup.add(button2)

    # 7. Edit the message one last time to show the final buttons
    bot.edit_message_text(
        chat_id=status_message.chat.id, 
        message_id=status_message.message_id, 
        text="✅ Choose a server below:", 
        reply_markup=markup
    )

# 1. Start the web server for UptimeRobot
keep_alive()

# 2. Start the Telegram bot
print("Bot is running...")
bot.infinity_polling()
