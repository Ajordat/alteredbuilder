from django.shortcuts import render

from .utils import fetch_youtube_videos, fetch_twitch_streams


async def updates_view(request):
    youtube_videos = await fetch_youtube_videos()
    twitch_streams = await fetch_twitch_streams()

    context = {"youtube_videos": youtube_videos, "twitch_streams": twitch_streams}
    return render(request, "news/updates.html", context)
