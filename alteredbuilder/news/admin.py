from django.contrib import admin

from news.models import NewsItem


@admin.register(NewsItem)
class NewsItemAdmin(admin.ModelAdmin):
    list_display = ["site", "author", "title", "description", "published_at"]
