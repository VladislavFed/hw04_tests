from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post, User


class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='NoName')
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.author,
        )
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test-slug",
            description="Тестовое описание",
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def post_create_form(self):
        """Валидная форма создает запись в БД."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Текстовый текст',
            'group': self.group.slug
        }
        post_latest = Post.objects.latest('id')
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse(
                "posts:profile",
                kwargs={"username": self.user.username}
            )
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(Post.objects.filter(
                        text=form_data['text'],
                        group=self.group.id,
                        author=self.user
                        ).exists())
        self.assertEqual(post_latest.text, form_data['text'])
        self.assertEqual(post_latest.group.id, form_data['group'])
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def post_edit_form(self):
        """Валидная форма редактирует запись в БД."""
        posts_count = Post.objects.count()
        form_data = {'text': 'Тестовый текст'}
        edit_post = Post.objects.get(id=self.post.id)
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id}
            )
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(edit_post.text, form_data['text'])
        self.assertEqual(edit_post.author, self.post.author)
        self.assertEqual(response.status_code, HTTPStatus.OK)
