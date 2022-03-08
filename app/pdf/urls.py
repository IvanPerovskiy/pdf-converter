from django.urls import path, include
from rest_framework import routers

from pdf import views


router = routers.SimpleRouter(trailing_slash=False)
router.register('', views.PDFViewSet)


urlpatterns = [
    path('', include(router.urls)),
]
