from django.test import TestCase
from django.core.management import call_command
from django.contrib.auth import get_user_model
from .models import Course,Section,Chapter,Lesson
class CourseTests(TestCase):
    def setUp(self):
        call_command('seed_python',verbosity=0)
        self.course=Course.objects.get(slug='python')
        self.chapter=Chapter.objects.filter(section__course=self.course).first()
    def test_outline_counts_published_lessons_only(self):
        Lesson.objects.create(chapter=self.chapter,title='Hidden draft',is_published=False)
        response=self.client.get('/api/courses/python/outline/')
        self.assertEqual(response.status_code,200)
        chapters=[c for s in response.json()['sections'] for c in s['chapters']]
        row=next(c for c in chapters if c['id']==str(self.chapter.id))
        self.assertEqual(row['lesson_count'],self.chapter.lessons.filter(is_published=True).count())
    def test_unpublished_ancestors_hide_lesson(self):
        lesson=self.chapter.lessons.first()
        for obj in [self.chapter,self.chapter.section,self.course]:
            obj.is_published=False;obj.save()
            self.assertEqual(self.client.get(f'/lessons/{lesson.id}/').status_code,404)
            self.assertEqual(self.client.get(f'/api/chapters/{self.chapter.id}/lessons/').status_code,404)
            obj.is_published=True;obj.save()
    def test_read_api_cannot_write(self):
        self.assertEqual(self.client.post('/api/courses/python/outline/',{}).status_code,405)
    def test_public_cannot_edit_admin(self):
        self.assertEqual(self.client.get('/admin/learning/chapter/add/').status_code,302)
    def test_admin_creates_visible_chapter(self):
        user=get_user_model().objects.create_superuser('tester','test@example.com','test-only-password')
        self.client.force_login(user)
        section=self.chapter.section
        r=self.client.post('/admin/learning/chapter/add/',{'title':'Admin created','section':section.id,'position':99,'is_published':'on','lessons-TOTAL_FORMS':0,'lessons-INITIAL_FORMS':0,'lessons-MIN_NUM_FORMS':0,'lessons-MAX_NUM_FORMS':1000,'_save':'Save'})
        self.assertEqual(r.status_code,302)
        self.assertContains(self.client.get('/api/courses/python/outline/'),'Admin created')
    def test_seed_is_repeatable(self):
        before=(Course.objects.count(),Chapter.objects.count(),Lesson.objects.count())
        call_command('seed_python',verbosity=0)
        self.assertEqual(before,(Course.objects.count(),Chapter.objects.count(),Lesson.objects.count()))
    def test_safe_text_and_working_lesson(self):
        lesson=self.chapter.lessons.first();lesson.explanation='<script>alert(1)</script>';lesson.save()
        r=self.client.get(f'/lessons/{lesson.id}/')
        self.assertContains(r,'&lt;script&gt;')
        self.assertNotContains(r,'<script>alert(1)</script>')
    def test_order_and_query_count(self):
        with self.assertNumQueries(3):
            r=self.client.get('/api/courses/python/outline/')
        for s in r.json()['sections']:
            positions=[c['position'] for c in s['chapters']]
            self.assertEqual(positions,sorted(positions))
    def test_roadmap_page(self):
        self.assertContains(self.client.get('/'),'data-outline-url="/api/courses/python/outline/"')
