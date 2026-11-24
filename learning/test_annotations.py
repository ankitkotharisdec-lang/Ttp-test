import uuid

from django.test import Client, TestCase
from django.urls import reverse

from .models import Chapter, Course, Lesson, LessonAnnotation, Section


class AnnotationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        course = Course.objects.create(title='Reading test', slug='reading-test', is_published=True)
        section = Section.objects.create(course=course, title='Section', is_published=True)
        chapter = Chapter.objects.create(section=section, title='Chapter', is_published=True)
        cls.lesson = Lesson.objects.create(chapter=chapter, title='Passage', is_published=True)

    def setUp(self):
        self.annotation_url = reverse('lesson-annotations', args=[self.lesson.id])
        self.bookmarks_url = reverse('course-bookmarks', args=[self.lesson.chapter.section.course.slug])
        self.user_id = uuid.uuid4()
        self.login(self.client, self.user_id)

    def login(self, client, user_id):
        session = client.session
        session['sb_user_id'] = str(user_id)
        session.save()

    def write(self, action, client=None):
        return (client or self.client).post(self.annotation_url, action, content_type='application/json')

    def test_bookmark_is_idempotent_and_can_be_revisited(self):
        save = {'action': 'bookmark', 'saved': True}
        for _ in range(2):
            self.assertTrue(self.write(save).json()['saved'])
        self.assertEqual(LessonAnnotation.objects.count(), 1)
        bookmark, = self.client.get(self.bookmarks_url).json()['bookmarks']
        self.assertEqual(bookmark['url'], self.lesson.get_absolute_url())
        self.assertEqual(bookmark['title'], self.lesson.title)
        self.assertFalse(self.write({'action': 'bookmark', 'saved': False}).json()['saved'])
        self.assertEqual(self.client.get(self.bookmarks_url).json()['bookmarks'], [])

    def test_highlight_is_deduplicated_and_private(self):
        save = {'action': 'highlight', 'selections': [
            {'block': 'intro', 'start': 7, 'end': 13, 'quote': 'Use 🐍'},
        ]}
        for _ in range(2):
            response = self.write(save)
            self.assertEqual(response.status_code, 200)
        highlight, = response.json()['highlights']
        other = Client()
        self.login(other, uuid.uuid4())
        self.assertEqual(other.get(self.annotation_url).json()['highlights'], [])
        self.write({'action': 'remove', 'id': highlight['id']}, other)
        self.assertEqual(self.client.get(self.annotation_url).json()['highlights'], [highlight])
        self.assertEqual(self.write({'action': 'remove', 'id': highlight['id']}).json()['highlights'], [])

    def test_unpublished_lesson_is_hidden_and_anonymous_writes_are_blocked(self):
        self.assertEqual(Client().get(self.annotation_url).status_code, 401)
        self.assertEqual(self.write({'action': 'bookmark', 'saved': True}, Client()).status_code, 401)
        self.write({'action': 'bookmark', 'saved': True})
        self.lesson.is_published = False
        self.lesson.save()
        self.assertEqual(self.client.get(self.annotation_url).status_code, 404)
        self.assertEqual(self.client.get(self.bookmarks_url).json()['bookmarks'], [])

    def test_invalid_selection_and_csrf_are_rejected(self):
        response = self.write({'action': 'highlight', 'selections': [
            {'block': 'intro', 'start': 9, 'end': 2, 'quote': 'invalid'},
        ]})
        self.assertEqual(response.status_code, 400)
        csrf_client = Client(enforce_csrf_checks=True)
        self.login(csrf_client, self.user_id)
        response = self.write({'action': 'bookmark', 'saved': True}, csrf_client)
        self.assertEqual(response.status_code, 403)
