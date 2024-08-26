from rest_framework import routers

from api import views

# Register the available views

router = routers.DefaultRouter()
router.register(r"users", views.UserViewSet)
router.register(r"groups", views.GroupViewSet)
router.register(r"cards", views.CardViewSet)

# Wire up our API using automatic URL routing.
urlpatterns = router.urls
