from flask import Flask
from threading import Thread
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive and running!"

def run():
    # Render assigns a dynamic PORT, so it's best practice to fetch it dynamically.
    # It will fall back to 8080 if not found.
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()
