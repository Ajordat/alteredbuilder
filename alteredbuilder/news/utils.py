import json
import requests

from django.conf import settings
from django.utils.translation import get_language
from twitchAPI.twitch import Twitch

TWITCH_ALTERED_TCG_CATEGORY_ID = "717164103"

async def fetch_youtube_videos():
    url = f"https://www.googleapis.com/youtube/v3/search"
    response = requests.get(
        url,
        params={
            "q": "alteredtcg",
            "key": settings.YOUTUBE_API_KEY,
            "part": "snippet",
            "type": "video",
            "order": "date",
            "relevanceLanguage": get_language(),
            "safeSearch": "none",
            "maxResults": 10
        }
    )
    videos = []
    for video in response.json().get("items", []):
        snippet = video["snippet"]
        videos.append({
            "title": snippet["title"],
            "video_id": video["id"]["videoId"],
            "thumbnail": snippet["thumbnails"]["medium"]["url"],
            "published_at": snippet["publishedAt"]
        })
    return videos

async def fetch_twitch_streams():
    twitch = await Twitch(settings.TWITCH_CLIENT_ID, settings.TWITCH_SECRET_KEY)
    streams = []
    async for stream in twitch.get_streams(game_id=TWITCH_ALTERED_TCG_CATEGORY_ID, stream_type="live"):
        streams.append({
            "title": stream.title,
            "user_name": stream.user_login,
            "viewer_count": stream.viewer_count,
            "thumbnail_url": stream.thumbnail_url,
            "language": stream.language
        })
    return streams
