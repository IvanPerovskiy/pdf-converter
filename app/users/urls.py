from django.urls import path, include
from rest_framework import routers

from users import views


router = routers.SimpleRouter(trailing_slash=False)
router.register('', views.UserViewSet)


urlpatterns = [
    path('', include(router.urls)),
]
