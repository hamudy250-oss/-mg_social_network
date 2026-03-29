from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import redirect, render

from .models import Post, Profile


def home(request):
    if request.method == 'POST' and request.user.is_authenticated:
        title = request.POST.get('title')
        content = request.POST.get('content')
        if title and content:
            Post.objects.create(title=title, content=content, author=request.user)
            return redirect('home')

    posts = Post.objects.select_related('author', 'author__profile').all()
    author_ids = {post.author_id for post in posts if post.author_id}
    for author_id in author_ids:
        Profile.objects.get_or_create(user_id=author_id)

    return render(request, 'base/home.html', {
        'posts': posts,
    })


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
