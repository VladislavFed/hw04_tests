from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import PostForm
from .models import Group, Post, User

MAX_NUM_OF_POSTS = 10  # Максимальное количество постов на странице


def get_page_context(post_list, request):
    paginator = Paginator(post_list, MAX_NUM_OF_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return {
        'paginator': paginator,
        'page_number': page_number,
        'page_obj': page_obj,
    }


def index(request):
    """Выводит шаблон главной страницы"""
    context = get_page_context(Post.objects.all(), request)
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    """Выводит шаблон с группами постов"""
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    context = {
        'group': group,
        'post_list': post_list,
    }
    context.update(get_page_context(group.posts.all(), request))
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    """Выводит шаблон профайла пользователя"""
    template_name = 'posts/profile.html'
    user = User.objects.get(username=username)
    posts = user.posts.select_related("group")
    post_count = posts.count()
    context = {
        'post_count': post_count,
        'author': user,
    }
    context.update(get_page_context(user.posts.all(), request))
    return render(request, template_name, context)


def post_detail(request, post_id):
    template_name = 'posts/post_detail.html'
    post = get_object_or_404(Post, id=post_id)
    context = {
        'post': post,
    }
    return render(request, template_name, context)


@login_required
def post_create(request):
    post = Post(author=request.user)
    form = PostForm(request.POST or None, instance=post)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            return redirect("posts:profile", request.user.username)
    context = {
        "form": form,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def post_edit(request, post_id):
    is_edit = True
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id)
    form = PostForm(request.POST or None, instance=post)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return redirect('posts:post_detail', post_id)
    return render(
        request, 'posts/create_post.html', {'form': form, 'is_edit': is_edit})
