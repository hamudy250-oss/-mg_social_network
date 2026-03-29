from django.contrib import admin
from .models import Comment, DirectMessage, DirectMessageThread, Notification, Post, PostImage, Profile, Report


class PostImageInline(admin.TabularInline):
    model = PostImage
    extra = 1


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    inlines = [PostImageInline]
    list_display = ('title', 'author', 'created_at')
    search_fields = ('title', 'content', 'author__username')
    list_filter = ('created_at', 'author')
    ordering = ('-created_at',)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'post', 'parent', 'created_at')
    search_fields = ('author__username', 'post__title', 'content')
    list_filter = ('created_at',)
    ordering = ('-created_at',)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_verified', 'location', 'website', 'created_at')
    list_filter = ('is_verified',)
    search_fields = ('user__username', 'user__email', 'bio', 'location')
    ordering = ('-created_at',)
    filter_horizontal = ('following',)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('actor', 'recipient', 'notification_type', 'post', 'comment', 'read', 'created_at')
    list_filter = ('notification_type', 'read', 'created_at')
    search_fields = ('actor__username', 'recipient__username', 'post__title', 'comment__content')
    ordering = ('-created_at',)


@admin.register(DirectMessageThread)
class DirectMessageThreadAdmin(admin.ModelAdmin):
    list_display = ('id', 'created_at')
    filter_horizontal = ('participants',)
    ordering = ('-created_at',)


@admin.register(DirectMessage)
class DirectMessageAdmin(admin.ModelAdmin):
    list_display = ('thread', 'sender', 'created_at', 'read')
    list_filter = ('read', 'created_at')
    search_fields = ('sender__username', 'content')
    ordering = ('-created_at',)


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('reporter', 'post', 'reason', 'status', 'created_at')
    list_filter = ('reason', 'status', 'created_at')
    search_fields = ('reporter__username', 'post__title', 'post__content')
    ordering = ('-created_at',)
