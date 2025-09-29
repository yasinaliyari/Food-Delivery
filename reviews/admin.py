from django.contrib import admin
from reviews.models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "product", "rating", "created_at")
    list_filter = ("rating", "created_at")
    search_fields = ("user__username ", "product__name", "comment")
