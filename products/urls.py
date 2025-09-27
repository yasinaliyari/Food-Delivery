from django.urls import path, include
from rest_framework.routers import DefaultRouter
from products.views import ProductViewSet, CategoryListAPIView

router = DefaultRouter()
router.register(r"products", ProductViewSet, basename="product")

urlpatterns = [
    path("categories/", CategoryListAPIView.as_view(), name="category-list"),
    path("", include(router.urls)),
]
