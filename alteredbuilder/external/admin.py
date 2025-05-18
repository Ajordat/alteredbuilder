from django.contrib import admin

from external.models import AccessToken, Cookie


@admin.register(AccessToken)
class AccessTokenAdmin(admin.ModelAdmin):
    list_display = ["service", "expires_at"]


@admin.register(Cookie)
class CookieAdmin(admin.ModelAdmin):
    list_display = ["service", "name", "expires"]
