from django.contrib import admin

from .models import Application


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "company",
        "position",
        "owner",
        "status",
        "job_type",
        "applied_on",
        "expected_salary",
        "created_at",
    )

    list_filter = (
        "status",
        "job_type",
    )

    search_fields = (
        "company",
        "position",
        "owner__username",
    )