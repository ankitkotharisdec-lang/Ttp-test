from uuid import uuid4

from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import Chapter, Course, Lesson, LessonProgress, Section


class ReaderSidebarTests(TestCase):
    def setUp(self):
        course = Course.objects.create(slug='reader-sidebar', title='Sidebar course', is_published=True)
        section = Section.objects.create(course=course, title='Test section', is_published=True)
        self.chapter = Chapter.objects.create(section=section, title='Test chapter', is_published=True)

    def create_lesson(self, title, position, published=True):
        return Lesson.objects.create(
            chapter=self.chapter,
            title=title,
            position=position,
            is_published=published,
        )

    def test_sidebar_status_and_next_incomplete_follow_chapter_order(self):
        first = self.create_lesson('First', 2)
        current = self.create_lesson('Current', 10)
        done = self.create_lesson('Already done', 30)
        later = self.create_lesson('Later', 40)
        user_id = uuid4()
        session = self.client.session
        session['sb_user_id'] = str(user_id)
        session.save()
        LessonProgress.objects.create(user_id=user_id, lesson=done, status=LessonProgress.COMPLETED)

        context = self.client.get(current.get_absolute_url()).context
        self.assertEqual(context['sidebar_lessons'], [
            {'id': first.id, 'number': 1, 'title': first.title, 'url': first.get_absolute_url(), 'status': 'new'},
            {'id': current.id, 'number': 2, 'title': current.title, 'url': current.get_absolute_url(), 'status': 'in_progress'},
            {'id': done.id, 'number': 3, 'title': done.title, 'url': done.get_absolute_url(), 'status': 'completed'},
            {'id': later.id, 'number': 4, 'title': later.title, 'url': later.get_absolute_url(), 'status': 'new'},
        ])
        self.assertEqual(context['next_incomplete'], later)

        LessonProgress.objects.create(user_id=user_id, lesson=later, status=LessonProgress.COMPLETED)
        self.assertEqual(self.client.get(current.get_absolute_url()).context['next_incomplete'], first)

        LessonProgress.objects.create(user_id=user_id, lesson=first, status=LessonProgress.COMPLETED)
        self.assertIsNone(self.client.get(current.get_absolute_url()).context['next_incomplete'])

    def test_only_staff_preview_includes_current_draft(self):
        first = self.create_lesson('First', 2)
        draft = self.create_lesson('Draft', 3, published=False)
        last = self.create_lesson('Last', 4)

        public_context = self.client.get(first.get_absolute_url()).context
        self.assertEqual([item['id'] for item in public_context['sidebar_lessons']], [first.id, last.id])
        self.assertEqual(self.client.get(draft.get_absolute_url()).status_code, 404)

        staff = get_user_model().objects.create_user(username='editor', is_staff=True)
        self.client.force_login(staff)
        preview = self.client.get(draft.get_absolute_url()).context
        self.assertEqual([item['id'] for item in preview['sidebar_lessons']], [first.id, draft.id, last.id])
        self.assertEqual(preview['lesson_no'], 2)
        self.assertEqual(preview['chapter_lessons'], [first, last])
