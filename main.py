import os
import re
import asyncio
from urllib.parse import urlparse
from collections import defaultdict

from aiogram import Bot, Dispatcher, F, types, Router
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.enums import ParseMode

from keep_alive import keep_alive

# Fetch token
BOT_TOKEN = os.environ.get('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("No BOT_TOKEN found. Please set it in your environment variables.")

# Initialize Bot, Dispatcher, and Router
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()
dp.include_router(router)

# --- STATS & QUEUE SETUP ---
active_tasks_count = 0
stats_lock = asyncio.Lock()

# This acts as our "Celery + Redis" replacement. 
# It holds links in a queue until a worker is ready.
task_queue = asyncio.Queue()

def is_valid_terabox_url(url):
    try:
        parsed = urlparse(url)
        if parsed.scheme in ['http', 'https'] and 'terabox' in parsed.netloc.lower():
            return True
        return False
    except Exception:
        return False

# --- COMMANDS ---

@router.message(Command("start", "help"))
async def send_welcome(message: types.Message):
    if message.chat.type != 'private':
        return
    await message.reply("Send or forward me any Terabox video link, and I will generate watch/download buttons for you!")

@router.message(Command("stats"))
async def send_stats(message: types.Message):
    if message.chat.type != 'private':
        return
    
    # Safely read the current active count
    async with stats_lock:
        current_count = active_tasks_count
        
    # Check how many items are waiting in the queue
    queue_size = task_queue.qsize()
    
    stats_text = (
        f"📊 **Bot Statistics**\n\n"
        f"🟢 Active Processing Tasks: `{current_count}`\n"
        f"⏳ Links Waiting in Queue: `{queue_size}`"
    )
    await message.reply(stats_text, parse_mode="Markdown")

# --- MESSAGE HANDLER ---

@router.message(F.text | F.caption)
async def handle_message(message: types.Message):
    if message.chat.type != 'private':
        return

    text_content = message.text or message.caption or ""
    all_urls = re.findall(r'(https?://[^\s]+)', text_content)
    valid_urls = [url for url in all_urls if is_valid_terabox_url(url)]
    
    is_forwarded = message.forward_date is not None

    if not valid_urls:
        if not is_forwarded and text_content.strip() and not text_content.startswith('/'):
            await message.reply("❌ Invalid Link. Please send a valid Terabox link starting with http:// or https://")
        return

    # Instead of processing immediately, put them in our Task Queue
    for url in valid_urls:
        await task_queue.put({"message": message, "url": url})
        
    # Optional: Tell the user their links are queued if they sent multiple
    if len(valid_urls) > 1:
        await message.reply(f"✅ Added {len(valid_urls)} links to the processing queue!")

# --- WORKER & PROCESSING LOGIC ---

async def process_single_link(message: types.Message, url: str):
    """The actual processing logic that updates the UI."""
    global active_tasks_count
    
    # Increment counter
    async with stats_lock:
        active_tasks_count += 1
        
    try:
        short_url = url[:30] + "..." if len(url) > 30 else url
        
        # 1. Initial Status
        status_message = await message.reply(f"⏳ Analysing Link...\n{short_url}")
        await asyncio.sleep(1.0) # Non-blocking sleep!
        
        # 2. Processing
        await status_message.edit_text(f"🔄 Processing...\n{short_url}")
        await asyncio.sleep(1.0) # Non-blocking sleep!

        # 3. Generating Buttons
        final_url_1 = f"https://www.teraboxdownloader.pro/p/fs.html?q={url}"
        final_url_2 = f"https://teradownloader.com/download?l={url}"

        # aiogram v3 UI generation
        markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Watch / Download Server 1", web_app=WebAppInfo(url=final_url_1))],
            [InlineKeyboardButton(text="Watch / Download Server 2", web_app=WebAppInfo(url=final_url_2))]
        ])

        # Final Update
        await status_message.edit_text("✅ Choose a server below:", reply_markup=markup)
        
        # Tiny delay to respect Telegram's rate limits
        await asyncio.sleep(0.5)

    except Exception as e:
        print(f"Error handling message: {e}")
        await message.answer("⚠️ An error occurred while processing this link. Please try again.")
        
    finally:
        # Decrement counter safely
        async with stats_lock:
            active_tasks_count -= 1

async def worker_loop():
    """Continuously pulls tasks from the queue and processes them."""
    while True:
        task = await task_queue.get()
        await process_single_link(task["message"], task["url"])
        task_queue.task_done()

# --- MAIN RUNNER ---

async def main():
    # 1. Start the keep_alive server (Flask runs in its own thread)
    keep_alive()
    
    # 2. Start our background workers. 
    # Creating 3 workers means the bot can process 3 links at the EXACT same time globally.
    # The rest wait gracefully in the queue.
    for _ in range(3):
        asyncio.create_task(worker_loop())
    
    # 3. Start the bot
    print("Async Bot is running...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
