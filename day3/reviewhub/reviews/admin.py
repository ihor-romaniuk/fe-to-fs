from django.contrib import admin

from .models import Comment, ReviewRequest


@admin.register(ReviewRequest)
class ReviewRequestAdmin(admin.ModelAdmin):
    list_display = ["title", "author", "reviewer", "status", "created_at"]
    list_filter = ["status"]
    search_fields = ["title"]


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ["review_request", "author", "created_at"]
