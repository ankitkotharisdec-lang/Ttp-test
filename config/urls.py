from django.contrib import admin
from django.urls import path
from django.views.generic import RedirectView
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
 # Previously shared List methods link from the initial course release.
 path('lessons/87641624-e73c-4185-a7ec-a9d83ada9d5d/', RedirectView.as_view(
     url='/lessons/82a7c0a5-d280-477b-b9dd-7f663983cf72/', permanent=True)),
 path('lessons/<uuid:lesson_id>/',views.lesson_detail,name='lesson-detail'),
]
