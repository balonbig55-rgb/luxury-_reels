import os
import random
import csv
import requests
from datetime import datetime

# GitHub Secrets
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

print("🚀 Luxury Reel Generator Started!")
print(f"📅 {datetime.now()}")

# Step 1: Get idea
def get_random_idea():
    try:
        with open("ideas.csv", "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            ideas = list(reader)
            idea = random.choice(ideas)
            print(f"✅ Idea: {idea}")
            return idea
    except Exception as e:
        print(f"⚠️ Could not read ideas.csv: {e}")
        return {"title": "Luxury Villa", "category": "Villa", "hashtags": "#luxury", "language": "en"}

# Step 2: Generate caption with Gemini
def generate_caption(idea):
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"
        payload = {"contents": [{"parts": [{"text": f"Write a short Instagram caption for: {idea['title']}"}]}]}
        response = requests.post(url, json=payload)
        data = response.json()
        caption = data["candidates"][0]["content"]["parts"][0]["text"]
        print(f"✅ Gemini caption: {caption}")
        return caption + f"\n\n{idea.get('hashtags', '')}"
    except Exception as e:
        print(f"⚠️ Gemini failed: {e}, using default caption")
        return f"✨ {idea['title']} in Paradise 🏡\n\nYour luxury escape awaits. Book now via link in bio!\n\n#LuxuryRealEstate #LuxuryTravel\n{idea.get('hashtags', '')}"

# Step 3: Get video from Pexels
def get_pexels_video(query):
    try:
        headers = {"Authorization": PEXELS_API_KEY}
        url = f"https://api.pexels.com/videos/search?query={query}&per_page=10"
        response = requests.get(url, headers=headers)
        data = response.json()
        videos = data["videos"]
        video = random.choice(videos)
        video_url = video["video_files"][0]["link"]
        print(f"✅ Pexels video found: {video_url}")
        return video_url
    except Exception as e:
        print(f"❌ Pexels failed: {e}")
        return None

# Step 4: Send to Telegram (URL only - no download)
def send_to_telegram(video_url, caption):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo"
        response = requests.post(url, data={
            "chat_id": TELEGRAM_CHAT_ID,
            "video": video_url,
            "caption": caption[:1024],
        }, timeout=60)
        if response.status_code == 200:
            print("✅ Sent to Telegram!")
            return True
        else:
            print(f"❌ Telegram error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Telegram failed: {e}")
        return False

# Main
idea = get_random_idea()
caption = generate_caption(idea)
print(f"📝 Caption:\n{caption}")

video_url = get_pexels_video(idea["title"])
if not video_url:
    print("❌ No video found. Exiting.")
    exit(1)

send_to_telegram(video_url, caption)
