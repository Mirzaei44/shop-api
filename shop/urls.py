from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token

from .views import ProductViewSet, OrderViewSet


# DRF router automatically generates RESTful routes
# for our ViewSets (list, retrieve, create, update, etc.)
router = DefaultRouter()
router.register("products", ProductViewSet, basename="products")
router.register("orders", OrderViewSet, basename="orders")


urlpatterns = [
    # Includes all automatically generated routes:
    # /products/, /orders/, /orders/{id}/items/, etc.
    path("", include(router.urls)),

    # Token authentication endpoint:
    # POST /api/token/  -> returns auth token
    path("token/", obtain_auth_token),
]