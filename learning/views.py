from django.db.models import Count,Prefetch,Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404,render
from django.views.decorators.http import require_GET
from .models import Course,Section,Chapter,Lesson
@require_GET
def roadmap(request,slug='python'):
    course=get_object_or_404(Course,slug=slug,is_published=True)
    return render(request,'learning/roadmap.html',{'course':course})
@require_GET
def outline(request,slug):
    chapters=Chapter.objects.filter(is_published=True).annotate(lesson_count=Count('lessons',filter=Q(lessons__is_published=True))).order_by('position','id')
    sections=Section.objects.filter(is_published=True).prefetch_related(Prefetch('chapters',queryset=chapters,to_attr='published_chapters'))
    course=get_object_or_404(Course.objects.prefetch_related(Prefetch('sections',queryset=sections,to_attr='published_sections')),slug=slug,is_published=True)
    return JsonResponse({'id':str(course.id),'title':course.title,'slug':course.slug,'sections':[{'id':str(s.id),'title':s.title,'position':s.position,'chapters':[{'id':str(c.id),'title':c.title,'position':c.position,'lesson_count':c.lesson_count} for c in s.published_chapters]} for s in course.published_sections]})
@require_GET
def chapter_lessons(request,chapter_id):
    chapter=get_object_or_404(Chapter,id=chapter_id,is_published=True,section__is_published=True,section__course__is_published=True)
    return JsonResponse({'id':str(chapter.id),'title':chapter.title,'lessons':list(chapter.lessons.filter(is_published=True).values('id','title','position'))})
@require_GET
def lesson_detail(request,lesson_id):
    lesson=get_object_or_404(Lesson,id=lesson_id,is_published=True,chapter__is_published=True,chapter__section__is_published=True,chapter__section__course__is_published=True)
    return render(request,'learning/lesson.html',{'lesson':lesson})
