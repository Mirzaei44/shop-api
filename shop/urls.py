from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token

from .views import ProductViewSet, OrderViewSet

router = DefaultRouter()
router.register("products", ProductViewSet, basename="products")
router.register("orders", OrderViewSet, basename="orders")

urlpatterns = [
    path("", include(router.urls)),
    path("token/", obtain_auth_token),
]