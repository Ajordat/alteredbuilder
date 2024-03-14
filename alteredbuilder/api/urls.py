from django.urls import include, path
from rest_framework import routers

from . import views

router = routers.DefaultRouter()
router.register(r"users", views.UserViewSet)
router.register(r"groups", views.GroupViewSet)
router.register(r"cards", views.CardViewSet)
router.register(r"characters", views.CharacterViewSet)
router.register(r"heroes", views.HeroViewSet)
router.register(r"landmarks", views.LandmarkViewSet)
router.register(r"spells", views.SpellViewSet)

# Wire up our API using automatic URL routing.
urlpatterns = router.urls
