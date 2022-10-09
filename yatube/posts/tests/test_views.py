from django import forms
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post, User
from ..views import MAX_NUM_OF_POSTS

NUMBER_OF_POSTS = 13  # Количество переданных постов
POSTS_ON_THE_SEC_PAGE = 3  # Количество ожидаемых постов на второй странице


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username="NoName")
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test-slug",
            description="Тестовое описание",
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text="Тестовый пост",
            group=cls.group,
        )

    def setUp(self):
        self.user = User.objects.get(username="NoName")
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем второй клиент
        self.authorized_client = Client()
        # Авторизуем пользователя
        self.authorized_client.force_login(PostURLTests.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            (reverse('posts:group_list', kwargs={'slug': 'test-slug'})):
            'posts/group_list.html',
            (reverse('posts:profile', kwargs={'username': 'NoName'})):
            'posts/profile.html',
            (reverse('posts:post_detail', kwargs={'post_id': self.post.id})):
            'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            (reverse('posts:post_edit', kwargs={'post_id': self.post.id})):
            'posts/create_post.html',
        }
        for reverse_name, template in templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        context_objects = {
            self.user.id: first_object.author.id,
            self.post.text: first_object.text,
            self.group.slug: first_object.group.slug,
            self.post.id: first_object.id,
        }
        for value, expected in context_objects.items():
            with self.subTest(expected=expected):
                self.assertEqual(value, expected)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={"slug": self.group.slug})
        )
        first_object = response.context['page_obj'][0]
        task_author_0 = first_object.author
        task_text_0 = first_object.text
        task_group_0 = first_object.group
        self.assertEqual(task_author_0, self.user)
        self.assertEqual(task_text_0, 'Тестовый пост')
        self.assertEqual(task_group_0, self.group)

    def test_post_profile_page_show_correct_context(self):
        """Шаблон post_profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={
                'username': self.user.username}))
        first_object = response.context['page_obj'][0]
        context_objects = {
            self.user.id: first_object.author.id,
            self.post.text: first_object.text,
            self.group.slug: first_object.group.slug,
            self.post.id: first_object.id,
        }
        for value, expected in context_objects.items():
            with self.subTest(expected=expected):
                self.assertEqual(value, expected)

    def test_post_detail_pages_show_correct_context(self):
        '''Шаблон post_detail сформирован с правильным контекстом.'''
        response = self.client.get(reverse(
            'posts:post_detail', kwargs={'post_id': 1}))
        test_post = {
            response.context.get('post').author: self.user,
            response.context.get('post').group: self.group,
            response.context.get('post').text: 'Тестовый пост',
        }
        for value, expected in test_post.items():
            with self.subTest(value=value):
                self.assertEqual(value, expected)

    def test_post_create_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_check_post_with_group_in_pages(self):
        """Проверяем создание поста на страницах с выбранной группой."""
        form_fields = {
            reverse("posts:index"): Post.objects.get(group=self.post.group),
            reverse("posts:group_list", kwargs={"slug": self.group.slug}
                    ): Post.objects.get(group=self.post.group),
            reverse("posts:profile", kwargs={"username": self.post.author}
                    ): Post.objects.get(group=self.post.group),
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                response = self.authorized_client.get(value)
                form_field = response.context["page_obj"]
                self.assertIn(expected, form_field)

    def test_check_post_with_group_not_be_other_group_page(self):
        """Проверяем чтобы созданный пост не попал в другую группу."""
        form_fields = {
            reverse("posts:group_list", kwargs={"slug": self.group.slug}
                    ): Post.objects.exclude(group=self.post.group),
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                response = self.authorized_client.get(value)
                form_field = response.context["page_obj"]
                self.assertNotIn(expected, form_field)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.authorized_author = Client()
        cls.user = User.objects.create(username="NoName")
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test-slug",
            description="Тестовое описание",
        )

    def setUp(self):
        for post_temp in range(NUMBER_OF_POSTS):
            Post.objects.create(
                text=f'text{post_temp}', author=self.user, group=self.group
            )

    def test_first_page_contains_ten_records(self):
        """Проверяет что на первой странице отображается десять постов"""
        templates_pages_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/group_list.html':
                reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            'posts/profile.html':
                reverse('posts:profile', kwargs={'username': self.user}),
        }
        for _, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.client.get(reverse_name)
                self.assertEqual(
                    len(response.context['page_obj']), MAX_NUM_OF_POSTS
                )

    def test_second_page_contains_three_records(self):
        """Проверяет что на первой странице отображается три поста"""
        templates_pages_names = {
            'posts/index.html': reverse('posts:index') + '?page=2',
            'posts/group_list.html':
                reverse('posts:group_list',
                        kwargs={'slug': self.group.slug}) + '?page=2',
            'posts/profile.html':
                reverse('posts:profile',
                        kwargs={'username': self.user}) + '?page=2',
        }
        for _, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.client.get(reverse_name)
                self.assertEqual(len(
                    response.context['page_obj']), POSTS_ON_THE_SEC_PAGE
                )
