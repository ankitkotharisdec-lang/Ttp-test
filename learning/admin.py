from django.contrib import admin
from .models import Course,Section,Chapter,Lesson
admin.site.site_header='Step2Success Content Admin'
class SectionInline(admin.TabularInline):
    model=Section
    extra=0
    show_change_link=True
class ChapterInline(admin.TabularInline):
    model=Chapter
    extra=0
    show_change_link=True
class LessonInline(admin.TabularInline):
    model=Lesson
    fields=['title','position','is_published']
    extra=0
    show_change_link=True
@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display=['title','slug','is_published']
    prepopulated_fields={'slug':('title',)}
    inlines=[SectionInline]
@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display=['title','course','position','is_published']
    list_filter=['course','is_published']
    inlines=[ChapterInline]
@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    list_display=['title','section','position','is_published']
    list_filter=['section','is_published']
    search_fields=['title']
    inlines=[LessonInline]
@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display=['title','chapter','position','is_published']
    list_filter=['chapter','is_published']
    search_fields=['title','explanation']
