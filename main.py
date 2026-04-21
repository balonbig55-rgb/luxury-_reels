import os
import random
import csv
import requests
import time
from datetime import datetime

# GitHub Secrets
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
FAL_API_KEY = os.environ.get("FAL_API_KEY")
PIXABAY_API_KEY = os.environ.get("PIXABAY_API_KEY")  # ✅ NEW: Pixabay API Key

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

# Step 3a: Get video from Pexels
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
            print("❌ No videos found on Pexels")
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

# Step 3b: ✅ NEW — Get video from Pixabay as second source
def get_pixabay_video(idea):
    if not PIXABAY_API_KEY:
        print("⚠️ PIXABAY_API_KEY not set, skipping Pixabay")
        return None

    try:
        keyword = idea.get("pexels_query", idea["title"])
        print(f"🎬 Searching Pixabay for: {keyword}")

        response = requests.get(
            "https://pixabay.com/api/videos/",
            params={
                "key": PIXABAY_API_KEY,
                "q": keyword,
                "per_page": 10,
                "safesearch": "true",
                "order": "popular"
            },
            timeout=30
        )

        data = response.json()
        videos = data.get("hits", [])
        if not videos:
            print("❌ No videos found on Pixabay")
            return None

        video = random.choice(videos)
        # Get the best quality portrait video available
        sizes = video.get("videos", {})
        for quality in ["large", "medium", "small", "tiny"]:
            if quality in sizes and sizes[quality].get("url"):
                video_url = sizes[quality]["url"]
                print(f"✅ Pixabay video found ({quality}): {video_url}")
                return video_url

        print("❌ No usable video file on Pixabay")
        return None
    except Exception as e:
        print(f"❌ Pixabay failed: {e}")
        return None

# Step 3c: ✅ — Generate video with FAL.ai as fallback
def generate_fal_video(idea):
    if not FAL_API_KEY:
        print("⚠️ FAL_API_KEY not set, skipping AI generation")
        return None

    try:
        keyword = idea.get("pexels_query", idea["title"])
        prompt = f"Cinematic luxury travel video, {keyword}, aerial view, golden hour, 4K, ultra realistic, smooth camera movement, no text"
        print(f"🤖 Generating AI video with FAL.ai for: {keyword}")

        # Submit the generation job
        headers = {
            "Authorization": f"Key {FAL_API_KEY}",
            "Content-Type": "application/json"
        }

        submit_response = requests.post(
            "https://queue.fal.run/fal-ai/kling-video/v1.6/standard/text-to-video",
            headers=headers,
            json={
                "prompt": prompt,
                "duration": "5",
                "aspect_ratio": "9:16"  # Portrait for Reels/Telegram
            },
            timeout=30
        )

        if submit_response.status_code != 200:
            print(f"❌ FAL.ai submit failed: {submit_response.text}")
            return None

        job = submit_response.json()
        request_id = job.get("request_id")
        if not request_id:
            print("❌ No request_id from FAL.ai")
            return None

        print(f"⏳ FAL.ai job submitted: {request_id}, waiting for result...")

        # Poll for result (max 3 minutes)
        status_url = f"https://queue.fal.run/fal-ai/kling-video/v1.6/standard/text-to-video/requests/{request_id}/status"
        result_url = f"https://queue.fal.run/fal-ai/kling-video/v1.6/standard/text-to-video/requests/{request_id}"

        for attempt in range(18):  # 18 × 10s = 3 minutes
            time.sleep(10)
            status_response = requests.get(status_url, headers=headers, timeout=15)
            status_data = status_response.json()
            status = status_data.get("status", "")
            print(f"⏳ Status ({attempt+1}/18): {status}")

            if status == "COMPLETED":
                result_response = requests.get(result_url, headers=headers, timeout=15)
                result_data = result_response.json()
                video_url = result_data.get("video", {}).get("url")
                if video_url:
                    print(f"✅ FAL.ai video generated: {video_url}")
                    return video_url
                else:
                    print("❌ FAL.ai result has no video URL")
                    return None

            elif status in ["FAILED", "CANCELLED"]:
                print(f"❌ FAL.ai job {status}")
                return None

        print("❌ FAL.ai timed out after 3 minutes")
        return None

    except Exception as e:
        print(f"❌ FAL.ai failed: {e}")
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

# ─── Main ───────────────────────────────────────────────
trend = get_trending_topic()

idea = get_random_idea()
if not idea:
    print("❌ No idea found. Exiting.")
    exit(1)

caption = generate_caption(idea, trend)
print(f"📝 Caption:\n{caption}")

# ✅ Try Pexels → Pixabay → FAL.ai
video_url = get_pexels_video(idea)

if not video_url:
    print("⚠️ Pexels failed — trying Pixabay...")
    video_url = get_pixabay_video(idea)

if not video_url:
    print("⚠️ Pixabay failed — trying FAL.ai AI video generation...")
    video_url = generate_fal_video(idea)

if not video_url:
    print("❌ No video available from any source. Exiting.")
    exit(1)

send_to_telegram(video_url, caption)
