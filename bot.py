import os
import asyncio
import tempfile
from pathlib import Path
from urllib.parse import urlparse

import yt_dlp
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
Application,
CommandHandler,
MessageHandler,
ContextTypes,
filters,
)

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

def is_facebook_url(url):
try:
parsed = urlparse(url)
host = (parsed.hostname or "").lower()

    allowed = (
        host == "facebook.com"
        or host.endswith(".facebook.com")
        or host == "fb.watch"
    )

    return parsed.scheme == "https" and allowed
except ValueError:
    return False

def download_video(url, folder):
output = str(Path(folder) / "video.%(ext)s")

options = {
    "format": "best[ext=mp4]/best",
    "outtmpl": output,
    "noplaylist": True,
    "socket_timeout": 20,
    "retries": 1,
    "quiet": True,
}

with yt_dlp.YoutubeDL(options) as downloader:
    downloader.download([url])

files = list(Path(folder).glob("video.*"))

if not files:
    raise RuntimeError("Video not found")

video = files[0]

if video.stat().st_size > 45 * 1024 * 1024:
    raise RuntimeError("Video is too large for this bot")

return video

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
await update.message.reply_text(
"👋 Welcome to Reel Saver!\n\n"
"Send me a Facebook Reel link to download."
)

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
url = (update.message.text or "").strip()

if not is_facebook_url(url):
    await update.message.reply_text(
        "❌ Please send a valid Facebook video link."
    )
    return

status = await update.message.reply_text(
    "⏳ Processing your video..."
)

try:
    with tempfile.TemporaryDirectory() as folder:
        video = await asyncio.to_thread(
            download_video, url, folder
        )

        with video.open("rb") as file:
            await update.message.reply_video(
                video=file,
                caption="✅ Your video is ready!"
            )

    await status.delete()

except Exception:
    await status.edit_text(
        "❌ Download failed. The video may be "
        "unavailable or unsupported."
    )

def main():
if not TOKEN:
raise RuntimeError(
"Bot token missing. Check your .env file."
)

app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(
    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link)
)

print("Bot is running!")

app.run_polling()

if name == "main":
main()