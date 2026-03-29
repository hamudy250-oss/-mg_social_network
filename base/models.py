from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse


User = get_user_model()


class Post(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='posts',
        verbose_name='المؤلف'
    )
    title = models.CharField(max_length=200, verbose_name='العنوان')
    content = models.TextField(verbose_name='المحتوى')
    image = models.ImageField(upload_to='post_images/', null=True, blank=True, verbose_name='صورة')
    video = models.FileField(upload_to='post_videos/', null=True, blank=True, verbose_name='فيديو')
    created_at = models.DateTimeField(auto_now_add=True)
    likes = models.ManyToManyField(
        User,
        through='Like',
        related_name='liked_posts',
        blank=True,
        verbose_name='إعجابات'
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Post'
        verbose_name_plural = 'Posts'

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('post_detail', args=[self.pk])

    def likes_count(self):
        return self.likes.count()

    def is_liked_by(self, user):
        if not user.is_authenticated:
            return False
        return self.likes.filter(pk=user.pk).exists()

    def comments_count(self):
        return self.comments.count()

    @property
    def media_type(self):
        if self.video:
            return 'video'
        if self.image:
            return 'image'
        if self.images.exists():
            return 'gallery'
        return None


class PostImage(models.Model):
    post = models.ForeignKey(
        'Post',
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name='صور المنشور'
    )
    image = models.ImageField(upload_to='post_images/', verbose_name='صورة')
    order = models.PositiveIntegerField(default=0, verbose_name='ترتيب')

    class Meta:
        ordering = ['order']
        verbose_name = 'Post Image'
        verbose_name_plural = 'Post Images'

    def __str__(self):
        return f'Image for {self.post.title}'


class Comment(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='comments',
        verbose_name='المؤلف'
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='المنشور'
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies',
        verbose_name='رد على'
    )
    content = models.TextField(verbose_name='المحتوى')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Comment'
        verbose_name_plural = 'Comments'

    def __str__(self):
        author_name = self.author.username if self.author else 'Unknown'
        target = f'{self.parent.author.username} reply' if self.parent else self.post.title
        return f'{author_name} on {target}'

    def is_reply(self):
        return self.parent is not None


class Profile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='المستخدم'
    )
    avatar = models.ImageField(upload_to='profile_avatars/', null=True, blank=True, verbose_name='الصورة الشخصية')
    cover_photo = models.ImageField(upload_to='profile_covers/', null=True, blank=True, verbose_name='صورة الغلاف')
    bio = models.CharField(max_length=260, blank=True, verbose_name='نبذة')
    location = models.CharField(max_length=120, blank=True, verbose_name='الموقع')
    website = models.URLField(blank=True, null=True, verbose_name='الموقع الإلكتروني')
    social_links = models.JSONField(default=dict, blank=True, verbose_name='روابط اجتماعية')
    is_verified = models.BooleanField(default=False, verbose_name='موثق')
    following = models.ManyToManyField(
        'self',
        symmetrical=False,
        related_name='followers',
        blank=True,
        verbose_name='يتابع'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')

    class Meta:
        verbose_name = 'Profile'
        verbose_name_plural = 'Profiles'

    def __str__(self):
        return f'{self.user.username} Profile'

    def get_absolute_url(self):
        return reverse('profile_detail', args=[self.user.username])

    def avatar_url(self):
        if self.avatar:
            return self.avatar.url
        return '/static/default-avatar.png'

    def followers_count(self):
        return self.followers.count()

    def following_count(self):
        return self.following.count()


class Like(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='likes',
        verbose_name='المستخدم'
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='like_records',
        verbose_name='المنشور'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإعجاب')

    class Meta:
        unique_together = ('user', 'post')
        verbose_name = 'Like'
        verbose_name_plural = 'Likes'

    def __str__(self):
        return f'{self.user.username} likes {self.post.title}'


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('like', 'إعجاب'),
        ('comment', 'تعليق'),
        ('follow', 'متابعة'),
    ]

    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='المستلم'
    )
    actor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='actor_notifications',
        verbose_name='الفاعل'
    )
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, verbose_name='نوع الإشعار')
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications',
        verbose_name='منشور'
    )
    comment = models.ForeignKey(
        Comment,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications',
        verbose_name='تعليق'
    )
    read = models.BooleanField(default=False, verbose_name='مقروء')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'

    def __str__(self):
        return f'{self.actor.username} -> {self.recipient.username} ({self.notification_type})'

    def label(self):
        if self.notification_type == 'like':
            return f'أعجب {self.actor.username} بمنشورك «{self.post.title if self.post else "…"}»'
        if self.notification_type == 'comment':
            if self.comment and self.comment.parent:
                return f'رد {self.actor.username} على تعليقك في منشور «{self.post.title if self.post else "…"}»'
            return f'علق {self.actor.username} على منشورك «{self.post.title if self.post else "…"}»'
        if self.notification_type == 'follow':
            return f'بدأ {self.actor.username} بمتابعتك'
        return 'إشعار جديد'


class Report(models.Model):
    REASON_CHOICES = [
        ('spam', 'Spam'),
        ('harassment', 'Harassment'),
        ('inappropriate', 'Inappropriate Content'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('reviewed', 'Reviewed'),
        ('dismissed', 'Dismissed'),
    ]

    reporter = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reports_made',
        verbose_name='المبلغ'
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='reports',
        verbose_name='المنشور'
    )
    reason = models.CharField(max_length=32, choices=REASON_CHOICES, verbose_name='السبب')
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='pending', verbose_name='الحالة')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')

    class Meta:
        unique_together = ('reporter', 'post')
        ordering = ['-created_at']
        verbose_name = 'Report'
        verbose_name_plural = 'Reports'

    def __str__(self):
        return f'{self.reporter.username} reported {self.post.title} ({self.get_status_display()})'


class DirectMessageThread(models.Model):
    participants = models.ManyToManyField(
        User,
        related_name='dm_threads',
        verbose_name='المشاركون'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')

    class Meta:
        verbose_name = 'Direct Message Thread'
        verbose_name_plural = 'Direct Message Threads'

    def __str__(self):
        return f'Thread ({self.pk})'

    def get_other_user(self, user):
        return self.participants.exclude(pk=user.pk).first()


class DirectMessage(models.Model):
    thread = models.ForeignKey(
        DirectMessageThread,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name='المحادثة'
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_messages',
        verbose_name='المرسل'
    )
    content = models.TextField(verbose_name='المحتوى')
    attachment = models.FileField(upload_to='dm_attachments/', null=True, blank=True, verbose_name='مرفق')
    read = models.BooleanField(default=False, verbose_name='مقروء')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Direct Message'
        verbose_name_plural = 'Direct Messages'

    def __str__(self):
        return f'Message from {self.sender.username} in thread {self.thread.pk}'

    @property
    def receiver(self):
        return self.thread.participants.exclude(pk=self.sender.pk).first()

    @property
    def body(self):
        return self.content

    @property
    def is_read(self):
        return self.read
