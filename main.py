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

# Luxury visual prompts for search
LUXURY_KEYWORDS = [
    "luxury villa golden hour",
    "modern estate private pool",
    "penthouse city view night",
    "mansion driveway sunset",
    "luxury real estate aerial"
]

# Step 1: Get idea
def get_random_idea():
    try:
        with open("ideas.csv", "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            ideas = list(reader)
        if not ideas:
            return None
        idea = random.choice(ideas)
        print(f"✅ Idea: {idea}")
        return idea
    except Exception as e:
        print(f"❌ Ideas failed: {e}")
        return None

# Step 2: Generate caption with Gemini
def generate_caption(idea):
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        prompt = f"""You are a luxury real estate content creator.
Write a short Instagram caption (max 150 chars) for:
Title: {idea['title']}
Category: {idea['category']}
Language: {idea['language']}
Hashtags: {idea['hashtags']}

Rules:
- Start with the title in original language
- Add one elegant English tagline
- End with: Book now via link in bio!
- Add hashtags on new line
- Keep it aspirational and minimal"""

        response = requests.post(url, json={
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": 300}
        }, timeout=30)

        data = response.json()
        caption = data["candidates"][0]["content"]["parts"][0]["text"]
        return caption.strip()
    except Exception as e:
        print(f"⚠️ Gemini failed: {e}")
        # Fallback caption
        return f"✨ {idea['title']} — Where silence is the ultimate luxury.\n\nBook now via link in bio!\n\n#QuietLuxury #LuxuryRealEstate {idea['hashtags']}"

# Step 3: Get video from Pexels
def get_pexels_video(category):
    try:
        keyword = random.choice(LUXURY_KEYWORDS)
        print(f"🎬 Searching Pexels for: {keyword}")

        headers = {"Authorization": PEXELS_API_KEY}
        response = requests.get(
            "https://api.pexels.com/videos/search",
            headers=headers,
            params={"query": keyword, "per_page": 10, "orientation": "portrait"},
            timeout=30
        )

        data = response.json()
        videos = data.get("videos", [])
        if not videos:
            print("❌ No videos found")
            return None

        video = random.choice(videos)
        video_files = video["video_files"]
        best = max(video_files, key=lambda x: x.get("width", 0))
        video_url = best["link"]
        print(f"✅ Pexels video found: {video_url}")
        return video_url
    except Exception as e:
        print(f"❌ Pexels failed: {e}")
        return None

# Step 4: Send to Telegram (upload as file, not URL)
def send_to_telegram(video_url, caption):
    try:
        print("⬇️ Downloading video...")
        video_data = requests.get(video_url, timeout=60)
        if video_data.status_code != 200:
            print("❌ Failed to download video")
            return False

        print("📤 Uploading to Telegram...")
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo"
        response = requests.post(
            url,
            data={
                "chat_id": TELEGRAM_CHAT_ID,
                "caption": caption[:1024],
            },
            files={
                "video": ("video.mp4", video_data.content, "video/mp4")
            },
            timeout=120
        )

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

video_url = get_pexels_video(idea["category"])
if not video_url:
    print("❌ No video found. Exiting.")
    exit(1)

send_to_telegram(video_url, caption)
