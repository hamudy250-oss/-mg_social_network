import re
from collections import Counter

from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import ProfileForm
from .models import Comment, DirectMessage, DirectMessageThread, Like, Notification, Post, Profile, Report

User = get_user_model()


def get_notifications_context(request):
    unread_notifications = 0
    unread_messages = 0
    if request.user.is_authenticated:
        unread_notifications = request.user.notifications.filter(read=False).count()
        unread_messages = DirectMessage.objects.filter(
            thread__participants=request.user
        ).exclude(sender=request.user).filter(read=False).count()
    return {
        'unread_notifications_count': unread_notifications,
        'unread_messages_count': unread_messages,
    }


def build_feed_queryset(request, search_query=''):
    if request.user.is_authenticated:
        Profile.objects.get_or_create(user=request.user)
        profile = Profile.objects.get(user=request.user)
        following_ids = profile.following.values_list('user_id', flat=True)
        feed_posts = Post.objects.filter(
            Q(author=request.user) | Q(author_id__in=following_ids)
        )
    else:
        feed_posts = Post.objects.all()

    if search_query:
        feed_posts = feed_posts.filter(
            Q(title__icontains=search_query) |
            Q(content__icontains=search_query) |
            Q(author__username__icontains=search_query)
        )

    return feed_posts


def get_trending_tags():
    recent_posts = Post.objects.order_by('-created_at')[:50]
    word_counter = Counter()
    stopwords = {
        'و', 'في', 'على', 'من', 'عن', 'مع', 'ما', 'لا', 'هل', 'أن', 'إن',
        'كل', 'هذا', 'هذه', 'ذلك', 'هناك', 'لقد', 'كما', 'أو', 'إلى', 'عن',
        'هو', 'هي', 'كان', 'كانت', 'يكون', 'يتم'
    }

    for post in recent_posts:
        text = f"{post.title} {post.content}"
        for tag in re.findall(r'#(\w+)', text):
            word_counter[f'#{tag.lower()}'] += 1
        for token in re.findall(r"[\w\u0600-\u06FF]{3,}", text.lower()):
            if token in stopwords or token.startswith('http'):
                continue
            word_counter[token] += 1

    trending_tags = [word for word, _ in word_counter.most_common(8)]
    return trending_tags


def get_or_create_dm_thread(user1, user2):
    if user1 == user2:
        return None
    thread = DirectMessageThread.objects.filter(participants=user1).filter(participants=user2).distinct().first()
    if not thread:
        thread = DirectMessageThread.objects.create()
        thread.participants.add(user1, user2)
    return thread


def is_admin_user(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser or user.username == 'muhammed250')


@user_passes_test(is_admin_user, login_url='login')
def admin_dashboard(request):
    total_users = User.objects.count()
    total_posts = Post.objects.count()
    total_likes = Like.objects.count()

    top_followed_profiles = Profile.objects.annotate(
        followers_count=Count('followers')
    ).order_by('-followers_count')[:5]

    latest_users = User.objects.order_by('-date_joined')[:5]

    user_growth = []
    for days in range(6, -1, -1):
        day = timezone.now().date() - timezone.timedelta(days=days)
        count = User.objects.filter(date_joined__date=day).count()
        user_growth.append({
            'date': day.strftime('%d %b'),
            'count': count,
        })

    pending_reports = Report.objects.filter(status='pending').select_related('reporter', 'post', 'post__author')[:10]

    context = {
        'total_users': total_users,
        'total_posts': total_posts,
        'total_likes': total_likes,
        'top_followed_profiles': top_followed_profiles,
        'latest_users': latest_users,
        'user_growth': user_growth,
        'pending_reports': pending_reports,
    }
    context.update(get_notifications_context(request))
    return render(request, 'base/dashboard.html', context)


@login_required(login_url='login')
@require_POST
def submit_report(request):

    post_id = request.POST.get('post_id')
    reason = request.POST.get('reason')
    if not post_id or not reason:
        return JsonResponse({'error': 'Missing data.'}, status=400)

    post = get_object_or_404(Post, pk=post_id)
    report, created = Report.objects.get_or_create(
        reporter=request.user,
        post=post,
        defaults={'reason': reason},
    )
    if not created:
        if report.status == 'dismissed':
            report.reason = reason
            report.status = 'pending'
            report.save()
        else:
            return JsonResponse({'error': 'لقد أبلغت عن هذا المنشور بالفعل.'}, status=400)

    return JsonResponse({'success': True, 'message': 'شكراً لتقاريرك. سنراجع المنشور قريبًا.'})


@user_passes_test(is_admin_user, login_url='login')
@require_POST
def delete_report_post(request, report_id):

    report = get_object_or_404(Report, pk=report_id)
    post = report.post
    post.delete()
    report.status = 'reviewed'
    report.save()
    return JsonResponse({'success': True})


@user_passes_test(is_admin_user, login_url='login')
@require_POST
def dismiss_report(request, report_id):

    report = get_object_or_404(Report, pk=report_id)
    report.status = 'dismissed'
    report.save()
    return JsonResponse({'success': True})


def home(request):
    search_query = request.GET.get('q', '').strip()
    page_number = request.GET.get('page', 1)
    trending_posts = Post.objects.annotate(like_count=Count('likes')).order_by('-like_count', '-created_at')[:5]

    feed_posts = build_feed_queryset(request, search_query)
    feed_posts = feed_posts.select_related('author', 'author__profile').prefetch_related(
        'likes',
        'comments__author',
        'comments__author__profile',
        'comments__replies__author',
        'comments__replies__author__profile',
    )

    author_ids = {post.author_id for post in feed_posts if post.author_id}
    for author_id in author_ids:
        Profile.objects.get_or_create(user_id=author_id)

    paginator = Paginator(feed_posts, 5)
    page_obj = paginator.get_page(page_number)

    liked_post_ids = []
    if request.user.is_authenticated:
        liked_post_ids = list(request.user.liked_posts.values_list('pk', flat=True))

    context = {
        'page_obj': page_obj,
        'feed_posts': page_obj.object_list,
        'trending_posts': trending_posts,
        'liked_post_ids': liked_post_ids,
        'search_query': search_query,
        'has_next': page_obj.has_next(),
        'next_page': page_obj.next_page_number() if page_obj.has_next() else None,
    }
    context.update(get_notifications_context(request))
    return render(request, 'base/home.html', context)


def load_more_posts(request):
    if request.headers.get('x-requested-with') != 'XMLHttpRequest':
        return HttpResponseBadRequest('Invalid request')

    search_query = request.GET.get('q', '').strip()
    page_number = request.GET.get('page', 1)

    feed_posts = build_feed_queryset(request, search_query)
    feed_posts = feed_posts.select_related('author', 'author__profile').prefetch_related(
        'likes',
        'comments__author',
        'comments__author__profile',
        'comments__replies__author',
        'comments__replies__author__profile',
    )

    paginator = Paginator(feed_posts, 5)
    page_obj = paginator.get_page(page_number)

    liked_post_ids = []
    if request.user.is_authenticated:
        liked_post_ids = list(request.user.liked_posts.values_list('pk', flat=True))

    html = render_to_string(
        'base/partials/post_cards.html',
        {
            'posts': page_obj.object_list,
            'liked_post_ids': liked_post_ids,
            'request': request,
        },
        request=request,
    )

    return JsonResponse({
        'html': html,
        'has_next': page_obj.has_next(),
        'next_page': page_obj.next_page_number() if page_obj.has_next() else None,
    })


def post_detail(request, pk):
    post = get_object_or_404(
        Post.objects.select_related('author', 'author__profile').prefetch_related(
            'likes',
            'images',
            'comments__author',
            'comments__author__profile',
            'comments__replies__author',
            'comments__replies__author__profile',
        ),
        pk=pk,
    )

    if request.method == 'POST':
        return create_comment(request, pk)

    liked = post.is_liked_by(request.user) if request.user.is_authenticated else False

    context = {
        'post': post,
        'liked': liked,
    }
    context.update(get_notifications_context(request))
    return render(request, 'base/post_detail.html', context)


def search(request):
    query = request.GET.get('q', '').strip()
    posts = Post.objects.none()
    users = User.objects.none()

    if query:
        posts = Post.objects.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(author__username__icontains=query)
        ).select_related('author', 'author__profile').prefetch_related('likes')
        users = User.objects.filter(username__icontains=query).select_related('profile')

    context = {
        'query': query,
        'posts': posts,
        'users': users,
    }
    context.update(get_notifications_context(request))
    return render(request, 'base/search_results.html', context)


def profile_detail(request, username):
    target_user = get_object_or_404(User, username=username)
    target_profile, _ = Profile.objects.get_or_create(user=target_user)
    posts = target_user.posts.select_related('author', 'author__profile').prefetch_related(
        'likes',
        'comments__author',
        'comments__author__profile',
        'comments__replies__author',
        'comments__replies__author__profile',
    )

    is_following = False
    if request.user.is_authenticated and request.user != target_user:
        current_profile, _ = Profile.objects.get_or_create(user=request.user)
        is_following = current_profile.following.filter(pk=target_profile.pk).exists()

    context = {
        'profile_owner': target_user,
        'target_profile': target_profile,
        'posts': posts,
        'is_following': is_following,
    }
    context.update(get_notifications_context(request))
    return render(request, 'base/profile_detail.html', context)


def conversations(request):
    if not request.user.is_authenticated:
        return redirect('login')

    threads = request.user.dm_threads.prefetch_related('participants', 'messages__sender').order_by('-created_at')
    thread_list = []
    for thread in threads:
        partner = thread.get_other_user(request.user)
        last_message = thread.messages.order_by('-created_at').select_related('sender').first()
        unread_count = thread.messages.exclude(sender=request.user).filter(read=False).count()
        thread_list.append({
            'thread': thread,
            'partner': partner,
            'last_message': last_message,
            'unread_count': unread_count,
        })

    context = {
        'threads': thread_list,
    }
    context.update(get_notifications_context(request))
    return render(request, 'base/conversations.html', context)


def conversation_detail(request, thread_id):
    if not request.user.is_authenticated:
        return redirect('login')

    thread = get_object_or_404(DirectMessageThread, pk=thread_id, participants=request.user)
    partner = thread.get_other_user(request.user)

    if request.method == 'POST':
        content = request.POST.get('message', '').strip()
        if content:
            DirectMessage.objects.create(
                thread=thread,
                sender=request.user,
                content=content,
            )
        return redirect('conversation_detail', thread_id=thread.pk)

    thread.messages.exclude(sender=request.user).filter(read=False).update(read=True)
    messages = thread.messages.select_related('sender').all()
    context = {
        'thread': thread,
        'partner': partner,
        'messages': messages,
    }
    context.update(get_notifications_context(request))
    return render(request, 'base/conversation_detail.html', context)


@login_required(login_url='login')
def create_post(request):
    errors = []
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()
        if not title:
            errors.append('العنوان مطلوب.')
        if not content:
            errors.append('المحتوى مطلوب.')
        if not errors:
            Post.objects.create(author=request.user, title=title, content=content)
            return redirect('home')

    context = {
        'errors': errors,
    }
    context.update(get_notifications_context(request))
    return render(request, 'base/post_create.html', context)


def start_conversation(request, username):
    if not request.user.is_authenticated:
        return redirect('login')

    target_user = get_object_or_404(User, username=username)
    if request.user == target_user:
        return redirect('profile_detail', username=request.user.username)

    thread = get_or_create_dm_thread(request.user, target_user)
    return redirect('conversation_detail', thread_id=thread.pk)


@login_required(login_url='login')
def edit_profile(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('profile_detail', username=request.user.username)
    else:
        form = ProfileForm(instance=profile)

    context = {
        'form': form,
    }
    context.update(get_notifications_context(request))
    return render(request, 'base/edit_profile.html', context)


@login_required(login_url='login')
def notifications_view(request):
    if request.method == 'POST':
        request.user.notifications.filter(read=False).update(read=True)
        return redirect('notifications')

    notifications = request.user.notifications.select_related('actor', 'post', 'comment').all()
    context = {
        'notifications': notifications,
    }
    context.update(get_notifications_context(request))
    return render(request, 'base/notifications.html', context)


@login_required(login_url='login')
@require_POST
def create_comment(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.method != 'POST':
        return HttpResponseBadRequest('Invalid method')

    content = request.POST.get('comment_content', '').strip()
    parent_id = request.POST.get('parent_id')
    parent_comment = None
    if parent_id:
        parent_comment = Comment.objects.filter(pk=parent_id, post=post).first()

    if not content:
        return JsonResponse({'error': 'Comment cannot be empty.'}, status=400)

    comment = Comment.objects.create(
        author=request.user,
        post=post,
        content=content,
        parent=parent_comment,
    )

    if post.author and post.author != request.user:
        Notification.objects.create(
            recipient=post.author,
            actor=request.user,
            notification_type='comment',
            post=post,
            comment=comment,
        )

    if parent_comment and parent_comment.author and parent_comment.author != request.user and parent_comment.author != post.author:
        Notification.objects.create(
            recipient=parent_comment.author,
            actor=request.user,
            notification_type='comment',
            post=post,
            comment=comment,
        )

    comments_count = post.comments_count()
    response_data = {
        'comment': {
            'id': comment.pk,
            'author': comment.author.username,
            'verified': bool(comment.author and getattr(comment.author, 'profile', None) and comment.author.profile.is_verified),
            'content': comment.content,
            'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M'),
            'parent_id': parent_comment.pk if parent_comment else None,
        },
        'comments_count': comments_count,
    }

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse(response_data)

    return redirect('post_detail', pk=pk)


@login_required(login_url='login')
@require_POST
def toggle_follow(request, username):
    target_user = get_object_or_404(User, username=username)
    if request.user == target_user:
        return redirect('home')

    profile, _ = Profile.objects.get_or_create(user=request.user)
    target_profile, _ = Profile.objects.get_or_create(user=target_user)

    if profile.following.filter(pk=target_profile.pk).exists():
        profile.following.remove(target_profile)
        following = False
    else:
        profile.following.add(target_profile)
        following = True
        if target_user != request.user:
            Notification.objects.create(
                recipient=target_user,
                actor=request.user,
                notification_type='follow',
            )

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'following': following})
    return redirect('profile_detail', username=target_user.username)


@login_required(login_url='login')
@require_POST
def toggle_like(request, pk):
    post = get_object_or_404(Post, pk=pk)
    like, created = Like.objects.get_or_create(user=request.user, post=post)
    if not created:
        like.delete()
        liked = False
        Notification.objects.filter(
            recipient=post.author,
            actor=request.user,
            notification_type='like',
            post=post,
        ).delete()
    else:
        liked = True
        if post.author and post.author != request.user:
            Notification.objects.create(
                recipient=post.author,
                actor=request.user,
                notification_type='like',
                post=post,
            )

    likes_count = post.likes.count()
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'liked': liked, 'likes_count': likes_count})

    return redirect('home')


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect('home')
    else:
        form = AuthenticationForm()

    return render(request, 'base/login.html', {
        'form': form,
    })


def logout_view(request):
    logout(request)
    return redirect('home')
