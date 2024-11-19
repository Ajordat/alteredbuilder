from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import render
from .utils import fetch_youtube_videos, fetch_twitch_streams


def updates_view(request):
    youtube_videos = fetch_youtube_videos(
        api_key="YOUR_YOUTUBE_API_KEY", channel_id="CHANNEL_ID"
    )
    twitch_streams = fetch_twitch_streams(
        client_id="YOUR_CLIENT_ID",
        access_token="YOUR_ACCESS_TOKEN",
        category_id="CATEGORY_ID",
    )

    context = {"youtube_videos": youtube_videos, "twitch_streams": twitch_streams}
    return render(request, "news/updates.html", context)
