from django.contrib.auth.models import User
from django.db.models import Count

from rest_framework import generics, permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Application
from .serializers import ApplicationSerializer, RegisterSerializer


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class ApplicationViewSet(viewsets.ModelViewSet):
    serializer_class = ApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    filterset_fields = ["status", "job_type"]
    search_fields = ["company", "position"]
    ordering_fields = ["created_at", "applied_on", "expected_salary"]

    def get_queryset(self):
        return Application.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class StatisticsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        status_counts = (
            Application.objects
            .filter(owner=request.user)
            .values("status")
            .annotate(count=Count("id"))
        )

        stats = {
            "total": 0,
            "wishlist": 0,
            "applied": 0,
            "interview": 0,
            "offer": 0,
            "rejected": 0,
        }

        for item in status_counts:
            status = item["status"].lower()
            stats[status] = item["count"]

        stats["total"] = sum(
            stats[key]
            for key in [
                "wishlist",
                "applied",
                "interview",
                "offer",
                "rejected",
            ]
        )

        return Response(stats)