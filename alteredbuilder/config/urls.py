"""
URL configuration for alteredbuilder project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.urls import include, path, reverse_lazy
from django.views.generic import RedirectView, TemplateView
from django.views.i18n import JavaScriptCatalog


# Error files definitions
handler403 = TemplateView.as_view(template_name="errors/403.html")
handler404 = TemplateView.as_view(template_name="errors/404.html")
handler500 = TemplateView.as_view(template_name="errors/500.html")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
    path("api/", include("api.urls")),
    path("accounts/", include("allauth.socialaccount.providers.github.urls")),
    path("accounts/", include("allauth.socialaccount.providers.discord.urls")),
    path(
        "",
        RedirectView.as_view(url=reverse_lazy("deck-list"), permanent=True),
        name="index",
    ),
    path(
        "robots.txt",
        TemplateView.as_view(template_name="robots.txt", content_type="text/plain"),
    ),
]

urlpatterns += i18n_patterns(
    path("jsi18n/", JavaScriptCatalog.as_view(), name="javascript-catalog"),
    path("accounts/", include("allauth.account.urls")),
    path("accounts/", include("allauth.socialaccount.urls")),
    path("decks/", include("decks.urls")),
    path("about/", TemplateView.as_view(template_name="about.html"), name="about"),
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
        RedirectView.as_view(url=reverse_lazy("deck-list"), permanent=True),
        name="i18n_index",
    ),
)

if settings.DEBUG:
    # Only include django-debug-toolbar in debug mode
    urlpatterns += [path("__debug__/", include("debug_toolbar.urls"))]
