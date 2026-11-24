from io import StringIO
from uuid import uuid4

from django.core.management import call_command
from django.test import TestCase

from .models import Chapter, Course, Lesson, LessonBlock, LessonProgress, Section


class CurriculumUpgradeTests(TestCase):
    def test_fresh_database_keeps_published_lesson_address(self):
        response = self.client.get('/lessons/82a7c0a5-d280-477b-b9dd-7f663983cf72/')
        self.assertEqual(response.context['lesson'].title, 'List methods')
        self.assertContains(response, 'id="lesson-index"')
        self.assertContains(response, 'id="lesson-progress"')
        self.assertRedirects(
            self.client.get('/lessons/87641624-e73c-4185-a7ec-a9d83ada9d5d/'),
            '/lessons/82a7c0a5-d280-477b-b9dd-7f663983cf72/',
            status_code=301,
        )

    def test_upgrade_preserves_lesson_identity_and_author_edits(self):
        course = Course.objects.get(slug='python')
        Lesson.objects.filter(chapter__section__course=course).delete()
        Chapter.objects.filter(section__course=course).delete()
        Section.objects.filter(course=course).delete()

        structures = Section.objects.create(course=course, title='Data Structures', is_published=True)
        lists = Chapter.objects.create(section=structures, title='Lists and Tuples', is_published=True)
        tuple_lesson = Lesson.objects.create(
            chapter=lists,
            title='Tuples',
            is_published=True,
            explanation='Our warehouse groups records by customer and date.',
        )
        list_lesson = Lesson.objects.create(chapter=lists, title='List methods', is_published=True)
        edited = LessonBlock.objects.create(lesson=list_lesson, body='An example written by our team.')
        progress = LessonProgress.objects.create(lesson=tuple_lesson, user_id=uuid4(), status='completed')

        call_command('seed_python', stdout=StringIO())

        tuple_lesson.refresh_from_db()
        list_lesson.refresh_from_db()
        self.assertNotEqual(tuple_lesson.chapter_id, lists.id)
        self.assertIn('tuple', tuple_lesson.chapter.title.lower())
        self.assertEqual(
            LessonProgress.objects.get(pk=progress.id).lesson_id,
            tuple_lesson.id,
        )
        self.assertTrue(tuple_lesson.blocks.filter(body=tuple_lesson.explanation).exists())
        self.assertTrue(list_lesson.blocks.filter(pk=edited.id, body=edited.body).exists())
        self.assertTrue(list_lesson.blocks.filter(block_type='image').exists())
        self.assertTrue(list_lesson.blocks.filter(block_type='trace').exists())
        lesson_count = Lesson.objects.count()
        block_count = LessonBlock.objects.count()

        edited.body = 'The editor updated this after launch.'
        edited.save(update_fields=['body'])
        call_command('seed_python', stdout=StringIO())

        self.assertEqual(Lesson.objects.count(), lesson_count)
        self.assertEqual(LessonBlock.objects.count(), block_count)
        self.assertEqual(LessonBlock.objects.get(pk=edited.id).body, edited.body)
