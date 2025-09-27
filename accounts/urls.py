from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from accounts.views import RegisterAPIView, CustomTokenObtainPairView, MeAPIView

urlpatterns = [
    path("register/", RegisterAPIView.as_view(), name="register"),
    path("token/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("me/", MeAPIView.as_view(), name="me"),
]
