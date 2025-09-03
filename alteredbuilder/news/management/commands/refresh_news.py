from argparse import ArgumentParser
from datetime import datetime
import json
import requests
import time
from typing import Any

from bs4 import BeautifulSoup
from django.utils import timezone
import feedparser

from config.commands import BaseCommand
from config.utils import get_user_agent
from news.models import NewsItem

RSS_FEEDS = [
    ("Altered TCG Blog", "https://alteredtcg.blog/feed/"),
]
HEADERS = {"User-Agent": get_user_agent("FeedParser")}


class Command(BaseCommand):
    help = "Refresh the news"
    version = "1.0.0"

    def add_arguments(self, parser: ArgumentParser):
        parser.add_argument(
            "source",
            type=str,
            choices=NewsItem.Sources.as_list(),
            help="The source to update",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """The command's entrypoint. Queries the API for each language."""

        self.stdout.write(f"{options=}")

        match options["source"]:
            case NewsItem.Sources.RSS:
                self.official_news()
            case NewsItem.Sources.YOUTUBE:
                print("qwer")
            case NewsItem.Sources.TWITCH:
                print("asdf")
            case _:
                pass

    def official_news(self):
        feed = feedparser.parse("https://www.altered.gg/api/rss/news")
        count = 0
        try:
            for entry in feed.entries:
                print(json.dumps(entry, indent=4))
                created = self.parse_equinox_entry(entry)
                if not created:
                    break
                count += 1
        except Exception as e:
            print(json.dumps(entry, indent=4))
            raise e
        finally:
            self.stdout.write(f"Found {count} new articles")

    def parse_equinox_entry(self, entry):

        # Parse publishing date
        published_at = None
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            published_at = timezone.make_aware(
                datetime.fromtimestamp(time.mktime(entry.published_parsed))
            )

        if NewsItem.objects.filter(
            source=NewsItem.Sources.RSS, link=entry.link
        ).exists():
            return False

        article = {
            "source": NewsItem.Sources.RSS,
            "link": entry.link,
            "site": "Equinox",
            "title": entry.title,
            "author": (entry.author if hasattr(entry, "author") else None),
            "description": getattr(entry, "summary", ""),
            "published_at": published_at or timezone.now(),
        }

        article.update(self.fetch_extra_attrs(entry.link))

        self.stdout.write(f'Added RSS item: "{entry.title}"')
        self.stdout.write(f"{article}")
        NewsItem.objects.create(**article)
        return True

    def fetch_extra_attrs(self, link):
        res = requests.get(link, headers=HEADERS)
        soup = BeautifulSoup(res.content, "html.parser")

        img = soup.find("img", attrs={"class": "object-cover"})
        img_src = img.get("src").split("&image=")[-1]

        div = soup.find("div", attrs={"id": "widget0"})
        first_text = None
        for p in div.find_all("p"):
            text = p.get_text(strip=True)
            if text:
                first_text = text
                break
        return {"thumbnail": img_src, "description": first_text}

    def update_rss(self):
        for blog, feed in RSS_FEEDS:
            self.stdout.write(f"Fetching RSS feed: {feed}")

            feed = feedparser.parse(feed)

            for entry in feed.entries:
                print(json.dumps(entry, indent=4))
                try:
                    published_at = None
                    if hasattr(entry, "published_parsed") and entry.published_parsed:
                        published_at = timezone.make_aware(
                            datetime.fromtimestamp(time.mktime(entry.published_parsed))
                        )
                    _, created = NewsItem.objects.get_or_create(
                        source=NewsItem.Sources.RSS,
                        link=entry.link,
                        site=blog,
                        defaults={
                            "title": entry.title,
                            "author": (
                                entry.author if hasattr(entry, "author") else None
                            ),
                            "description": getattr(entry, "summary", ""),
                            "published_at": published_at or timezone.now(),
                        },
                    )
                    if created:
                        self.stdout.write(f'Added RSS item: "{entry.title}"')
                except Exception as e:
                    print(json.dumps(entry, indent=4))
                    raise e
