from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import PostForm
# Импортируем модель, чтобы обратиться к ней
from .models import Group, Post, User


def get_page_context(post_list, request):
    # Показывать по 10 записей на странице.
    paginator = Paginator(post_list, 10)
    # Из URL извлекаем номер запрошенной страницы - это значение параметра page
    page_number = request.GET.get('page')
    # Получаем набор записей для страницы с запрошенным номером
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
    # Функция get_object_or_404 получает по заданным критериям объект
    # из базы данных или возвращает сообщение об ошибке, если объект не найден.
    # В нашем случае в переменную group будут переданы объекты модели Group,
    # поле slug у которых соответствует значению slug в запросе
    group = get_object_or_404(Group, slug=slug)
    # Благодаря ранее описанным related_name в models.py
    # напрямую берём посты из группы
    post_list = group.posts.all()
    context = {
        'group': group,
        'post_list': post_list,
    }
    context.update(get_page_context(group.posts.all(), request))
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    """Выводит шаблон профайла пользователя"""
    # Здесь код запроса к модели и создание словаря контекста
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
    # Здесь код запроса к модели и создание словаря контекста
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
