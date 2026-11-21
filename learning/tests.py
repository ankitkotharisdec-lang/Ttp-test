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
from unittest import mock
from django.test import override_settings
from . import supabase_auth as sb
SESSION={'user':{'id':'11111111-1111-1111-1111-111111111111','email':'a@b.com'},'access_token':'tok','refresh_token':'ref'}
@override_settings(SUPABASE_URL='https://x.supabase.co',SUPABASE_PUBLISHABLE_KEY='k')
class AuthTests(TestCase):
    def test_account_requires_login(self):
        r=self.client.get('/account/')
        self.assertEqual(r.status_code,302);self.assertTrue(r['Location'].startswith('/login/'))
    @mock.patch('learning.views.sb.get_profile',return_value={'plan':'paid','email':'a@b.com'})
    @mock.patch('learning.views.sb.sign_in',return_value=SESSION)
    def test_login_stores_plan_and_opens_account(self,si,gp):
        r=self.client.post('/login/',{'email':'A@B.com','password':'secret123'})
        self.assertRedirects(r,'/account/',fetch_redirect_response=False)
        si.assert_called_once_with('a@b.com','secret123')
        self.assertEqual(self.client.session['sb_plan'],'paid')
        self.assertContains(self.client.get('/account/'),'PAID')
    @mock.patch('learning.views.sb.sign_in',side_effect=sb.SupabaseError('Invalid login credentials',400))
    def test_bad_login_shows_error(self,si):
        r=self.client.post('/login/',{'email':'a@b.com','password':'x'})
        self.assertContains(r,'Incorrect email or password.');self.assertNotIn('sb_user_id',self.client.session)
    @mock.patch('learning.views.sb.sign_up',return_value={'user':{'id':'u','email':'a@b.com'}})
    def test_signup_without_session_asks_to_confirm_email(self,su):
        r=self.client.post('/signup/',{'full_name':'Ankit','email':'a@b.com','password':'longenough1'})
        self.assertContains(r,'Check your email');su.assert_called_once_with('a@b.com','longenough1','Ankit')
    def test_signup_rejects_short_password(self):
        self.assertContains(self.client.post('/signup/',{'full_name':'A','email':'a@b.com','password':'short'}),'at least 8')
    def test_login_ignores_offsite_next(self):
        with mock.patch('learning.views.sb.sign_in',return_value=SESSION),mock.patch('learning.views.sb.get_profile',return_value={}):
            r=self.client.post('/login/',{'email':'a@b.com','password':'p','next':'https://evil.example/'})
        self.assertRedirects(r,'/account/',fetch_redirect_response=False)
    def test_logout_requires_post(self):
        self.assertEqual(self.client.get('/logout/').status_code,405)
