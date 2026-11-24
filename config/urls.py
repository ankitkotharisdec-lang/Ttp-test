from django.contrib import admin
from django.urls import path
from learning import annotations, views
urlpatterns = [
 path('admin/',admin.site.urls),
 path('',views.roadmap,name='home'),
 path('courses/<slug:slug>/',views.roadmap,name='roadmap'),
 path('api/courses/<slug:slug>/outline/',views.outline,name='outline'),
 path('api/chapters/<uuid:chapter_id>/lessons/',views.chapter_lessons,name='chapter-lessons'),
 path('login/',views.login_view,name='login'),
 path('signup/',views.signup_view,name='signup'),
 path('auth/google/',views.google_start,name='google-start'),
 path('auth/callback/',views.auth_callback,name='auth-callback'),
 path('logout/',views.logout_view,name='logout'),
 path('account/',views.account,name='account'),
 path('api/lessons/<uuid:lesson_id>/complete/',views.complete_lesson,name='lesson-complete'),
 path('api/lessons/<uuid:lesson_id>/annotations/',annotations.lesson_annotations,name='lesson-annotations'),
 path('api/courses/<slug:slug>/bookmarks/',annotations.course_bookmarks,name='course-bookmarks'),
 path('lessons/<uuid:lesson_id>/',views.lesson_detail,name='lesson-detail'),
]
