from http import HTTPStatus
import sys

from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.contrib.sitemaps import views as sitemap_views
from django.shortcuts import render
from django.urls import include, path, reverse_lazy
from django.views.debug import technical_404_response, technical_500_response
from django.views.decorators.cache import cache_page
from django.views.generic import RedirectView, TemplateView
from django.views.i18n import JavaScriptCatalog

from config.sitemaps import (
    DeckSitemap,
    DailyLocalizedStaticViewSitemap,
    MonthlyLocalizedStaticViewSitemap,
    StaticViewSitemap,
)


sitemaps = {
    "static": StaticViewSitemap,
    "daily-localized-static": DailyLocalizedStaticViewSitemap,
    "monthly-localized-static": MonthlyLocalizedStaticViewSitemap,
    "decks": DeckSitemap,
}

urlpatterns = [
    path("admin/", admin.site.urls),
    path("admin_tools_stats/", include("admin_tools_stats.urls")),
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
    # path("api/", include("api.urls")),
    path("accounts/", include("allauth.socialaccount.providers.github.urls")),
    path("accounts/", include("allauth.socialaccount.providers.discord.urls")),
    path(
        "",
        RedirectView.as_view(url=reverse_lazy("home"), permanent=True),
        name="index",
    ),
    path(
        "robots.txt",
        TemplateView.as_view(template_name="robots.txt", content_type="text/plain"),
        name="robots.txt",
    ),
    path(
        "sitemap.xml",
        sitemap_views.sitemap,
        {"sitemaps": sitemaps},
        name="django.contrib.sitemaps.views.sitemap",
    ),
]

urlpatterns += i18n_patterns(
    path("decks/", include("decks.urls")),
    path("trends/", include("trends.urls")),
    path(
        "jsi18n/",
        cache_page(3600, key_prefix="jsi18n-%s" % settings.VERSION)(
            JavaScriptCatalog.as_view()
        ),
        name="javascript-catalog",
    ),
    path("accounts/", include("allauth.account.urls")),
    path("accounts/", include("allauth.socialaccount.urls")),
    path("profiles/", include("profiles.urls")),
    path("notifications/", include("notifications.urls")),
    path("about/", TemplateView.as_view(template_name="about.html"), name="about"),
    path(
        "contribute/",
        TemplateView.as_view(template_name="contribute.html"),
        name="contribute",
    ),
    path(
        "collaborators/",
        TemplateView.as_view(template_name="collaborators.html"),
        name="collaborators",
    ),
    path(
        "privacy-policy/",
        TemplateView.as_view(template_name="privacy_policy.html"),
        name="privacy-policy",
    ),
    path(
        "terms-and-conditions/",
        TemplateView.as_view(template_name="terms_and_conditions.html"),
        name="terms-and-conditions",
    ),
    path(
        "markdown/",
        TemplateView.as_view(template_name="markdown.html"),
        name="markdown",
    ),
    path("troubleshoot/", include("troubleshoot.urls")),
    path(
        "",
        RedirectView.as_view(url=reverse_lazy("home"), permanent=False),
        name="i18n_index",
    ),
)

if settings.DEBUG:  # pragma: no cover
    # Only include django-debug-toolbar in debug mode
    urlpatterns += [path("__debug__/", include("debug_toolbar.urls"))]


# Error files definitions
def handler403(request, exception):
    return render(request, "errors/403.html", status=HTTPStatus.FORBIDDEN)


def handler404(request, exception):
    if hasattr(request, "user") and request.user.is_superuser:
        return technical_404_response(request, exception)
    else:
        return render(request, "errors/404.html", status=HTTPStatus.NOT_FOUND)


def handler500(request):
    if hasattr(request, "user") and request.user.is_superuser:
        return technical_500_response(request, *sys.exc_info())
    else:
        return render(
            request, "errors/500.html", status=HTTPStatus.INTERNAL_SERVER_ERROR
        )
