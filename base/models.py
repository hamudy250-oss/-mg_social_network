from django.contrib.auth import get_user_model
from django.db import models


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
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Post'
        verbose_name_plural = 'Posts'

    def __str__(self):
        return self.title


class Profile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='المستخدم'
    )
    is_verified = models.BooleanField(default=False, verbose_name='موثق')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')

    class Meta:
        verbose_name = 'Profile'
        verbose_name_plural = 'Profiles'

    def __str__(self):
        return f'{self.user.username} Profile'
