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

# Affiliate Link
AFFILIATE_LINK = "https://bit.ly/4sWmPWB"

# ✅ System Prompt للكابشنات الفاخرة
CAPTION_SYSTEM_PROMPT = """You are a luxury travel content writer for an exclusive Telegram channel.
Your job is to write captions for short luxury travel videos.

STYLE RULES:
- Language: English only
- Tone: Luxurious, elegant, aspirational — like a high-end travel magazine
- Length: 3 to 5 lines maximum before hashtags
- Use 4 to 6 relevant emojis naturally within the text

STRUCTURE:
Line 1: One poetic evocative opening line that makes the viewer feel the place ✨
Line 2: (empty)
Line 3: Describe the experience, not just the location — make it aspirational 🌊
Line 4: (empty)
Line 5: Call to action ending with the affiliate link 👇
Line 6: (empty)
Line 7: 5 to 8 hashtags

AFFILIATE LINK FORMAT (always last before hashtags):
🔗 Book your escape → {affiliate_link}

HASHTAGS (always use these):
#LuxuryTravel #FiveStarLife #TravelInStyle #ExclusiveResorts #DreamVacation #LuxuryLife #Wanderlust

AVOID:
- Generic phrases like "beautiful place" or "amazing view"
- Casual or informal language
- Overly promotional tone
- More than 5 lines before hashtags
- Repeating the destination name more than once"""

print("🚀 Luxury Reel Generator Started!")
print(f"📅 {datetime.now()}")

# Step 0: Fetch trending luxury topic from Robb Report RSS
def get_trending_topic():
    try:
        rss_url = "https://robbreport.com/feed/"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(rss_url, headers=headers, timeout=15)
        content = response.text

        titles = []
        parts = content.split("<title>")
        for part in parts[2:7]:
            title = part.split("</title>")[0]
            title = title.replace("<![CDATA[", "").replace("]]>", "").strip()
            if title:
                titles.append(title)

        if titles:
            trend = titles[0]
            print(f"🔥 Trending topic: {trend}")
            return trend
        return None
    except Exception as e:
        print(f"⚠️ Trend fetch failed: {e}")
        return None

# Step 1: Get random idea from CSV
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

# Step 2: Generate caption with Gemini (trend-aware)
def generate_caption(idea, trend=None):
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

        trend_context = ""
        if trend:
            trend_context = f"\nCurrently trending in luxury world: {trend}\nUse this as subtle inspiration if relevant."

        # ✅ استخدام الـ System Prompt الجديد
        system = CAPTION_SYSTEM_PROMPT.replace("{affiliate_link}", AFFILIATE_LINK)

        prompt = f"""{system}

Now write a caption for a video about: {idea['title']}
{trend_context}"""

        response = requests.post(url, json={
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": 350}
        }, timeout=30)

        data = response.json()
        caption = data["candidates"][0]["content"]["parts"][0]["text"]
        return caption.strip()
    except Exception as e:
        print(f"⚠️ Gemini failed: {e}")
        fallback = idea.get("caption", idea["title"])
        return f"✨ {fallback}\n\n🔗 Book your escape → {AFFILIATE_LINK}\n\n#LuxuryTravel #FiveStarLife #TravelInStyle #ExclusiveResorts #DreamVacation #LuxuryLife #Wanderlust"

# Step 3: Get video from Pexels
def get_pexels_video(idea):
    try:
        keyword = idea.get("pexels_query", idea["title"])
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

# Step 4: Send to Telegram
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
trend = get_trending_topic()

idea = get_random_idea()
if not idea:
    print("❌ No idea found. Exiting.")
    exit(1)

caption = generate_caption(idea, trend)
print(f"📝 Caption:\n{caption}")

video_url = get_pexels_video(idea)
if not video_url:
    print("❌ No video found. Exiting.")
    exit(1)

send_to_telegram(video_url, caption)
