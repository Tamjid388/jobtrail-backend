from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import ApplicationViewSet, RegisterView, StatisticsView


router = DefaultRouter()
router.register("applications", ApplicationViewSet, basename="application")


urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", TokenObtainPairView.as_view(), name="login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("stats/", StatisticsView.as_view(), name="statistics"),
    path("", include(router.urls)),
]