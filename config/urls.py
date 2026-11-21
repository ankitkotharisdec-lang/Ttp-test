from django.contrib import admin
from django.urls import path
from learning import views
urlpatterns = [
 path('admin/',admin.site.urls),
 path('',views.roadmap,name='home'),
 path('courses/<slug:slug>/',views.roadmap,name='roadmap'),
 path('api/courses/<slug:slug>/outline/',views.outline,name='outline'),
 path('api/chapters/<uuid:chapter_id>/lessons/',views.chapter_lessons,name='chapter-lessons'),
 path('login/',views.login_view,name='login'),
 path('signup/',views.signup_view,name='signup'),
 path('logout/',views.logout_view,name='logout'),
 path('account/',views.account,name='account'),
 path('lessons/<uuid:lesson_id>/',views.lesson_detail,name='lesson-detail'),
]
