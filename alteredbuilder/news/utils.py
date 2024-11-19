import requests


def fetch_youtube_videos(api_key, channel_id):
    url = f"https://www.googleapis.com/youtube/v3/search?key={api_key}&channelId={channel_id}&part=snippet&type=video&order=date"
    response = requests.get(url)
    return response.json().get("items", [])


def fetch_twitch_streams(client_id, access_token, category_id):
    headers = {
        "Client-ID": client_id,
        "Authorization": f"Bearer {access_token}",
    }
    url = f"https://api.twitch.tv/helix/streams?game_id={category_id}"
    response = requests.get(url, headers=headers)
    return response.json().get("data", [])
