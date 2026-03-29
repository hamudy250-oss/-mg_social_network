from django.contrib import admin
from .models import Post, Profile


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'created_at')
    search_fields = ('title', 'content', 'author__username')
    list_filter = ('created_at', 'author')
    ordering = ('-created_at',)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_verified', 'created_at')
    list_filter = ('is_verified',)
    search_fields = ('user__username', 'user__email')
    ordering = ('-created_at',)
