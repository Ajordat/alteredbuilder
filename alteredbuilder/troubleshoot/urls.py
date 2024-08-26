from django.urls import path

from troubleshoot import views

# Endpoints for this app

app_name = "troubleshoot"
urlpatterns = [
    path("session", views.SubmitSessionFormView.as_view(), name="session"),
    path(
        "descriptions",
        views.DeckDescriptionsListView.as_view(),
        name="deck_descriptions",
    ),
]
