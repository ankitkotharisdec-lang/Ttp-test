import json
import re

from django import forms
from django.contrib import admin
from django.core.validators import URLValidator
from django.urls import reverse
from django.utils.html import format_html

from .models import Chapter, Course, Lesson, LessonBlock, LessonProgress, Section


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
    verbose_name_plural = 'Lessons · use Change to edit text, media, and exercises'
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
    fieldsets = [('Chapter settings', {'fields': ['title', 'section', 'position', 'is_published']})]


BLOCK_FIELDS = {
    'text': {'title': [], 'body': []},
    'must_know': {'title': [], 'body': []},
    'highlight': {'body': []},
    'example': {'title': [], 'body': [], 'options': [], 'correct_option': [], 'explanation': []},
    'code': {'title': [], 'body': [], 'code': []},
    'video': {'title': [], 'video_url': [], 'body': []},
    'summary': {'title': [], 'body': []},
    'image': {
        'title': [],
        'video_url': ['Image URL', 'Use a direct HTTPS image or GIF link, or a bundled /static/learning/ image path.'],
        'body': ['Caption', 'Optional text below the image.'],
        'explanation': ['Alternative text', 'Describe what the image shows for readers who cannot see it.'],
    },
    'diagram': {
        'title': [],
        'body': ['Caption', 'Optional text explaining how the stages connect.'],
        'options': ['Flow stages', 'Enter a JSON array of two to six short labels, for example ["Read CSV", "Validate rows", "Write results"].'],
    },
    'trace': {
        'title': [],
        'body': ['Introduction', 'Explain what the learner should look for as the example runs.'],
        'code': ['Python code', 'Use the exact code shown in the worked example.'],
        'options': ['Animation steps', 'Enter a JSON array of steps. Each step has line (starting at 1) and caption. Optional state and output are text.'],
        'explanation': ['Final output', 'Enter the final terminal output. Leave it blank when the code has no output.'],
    },
    'practice': {
        'title': [],
        'body': ['Practice prompt', 'Tell the learner what their code should do or print.'],
        'code': ['Starter code', 'Python code prefilled in the learner’s editor.'],
        'explanation': ['Expected output', 'The output the learner should produce.'],
        'options': ['Reference solution', 'Optional Python solution for the learner to reveal.'],
    },
}


class LessonBlockForm(forms.ModelForm):
    image_path = re.compile(r'/static/learning/[\w-]+\.(?:gif|webp|png|jpe?g|avif)', re.ASCII | re.IGNORECASE)

    class Meta:
        model = LessonBlock
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ('code', 'options', 'explanation'):
            self.fields[name].strip = False
        self.fields['block_type'].widget.attrs['data-block-fields'] = json.dumps(BLOCK_FIELDS)
        selected_type = self['block_type'].value()
        for name, labels in BLOCK_FIELDS.get(selected_type, {}).items():
            if labels:
                field = self.fields[name]
                field.widget.attrs['data-default-label'] = field.label
                field.widget.attrs['data-default-help'] = field.help_text
                field.label, field.help_text = labels

    def clean(self):
        cleaned = super().clean()
        block_type = cleaned.get('block_type')
        media_url = cleaned.get('video_url', '')
        if block_type == 'image':
            if not self.image_path.fullmatch(media_url):
                self.clean_media_url(media_url, 'Enter an HTTP or HTTPS image URL, or a bundled image path.')
            if not cleaned.get('explanation', '').strip():
                self.add_error('explanation', 'Describe the image in alternative text.')
        elif block_type == 'video' and media_url:
            self.clean_media_url(media_url, 'Enter an HTTP or HTTPS video URL.')
        elif block_type == 'trace':
            self.clean_trace(cleaned)
        elif block_type == 'diagram':
            labels = self.read_options(cleaned)
            if not isinstance(labels, list) or not 2 <= len(labels) <= 6 or any(
                not isinstance(label, str) or not 1 <= len(label.strip()) <= 80 for label in labels
            ):
                self.add_error('options', 'Enter a JSON array of two to six labels, up to 80 characters each.')
        elif block_type == 'practice' and not cleaned.get('body'):
            self.add_error('body', 'Enter a practice prompt.')
        return cleaned

    def clean_media_url(self, url, error):
        try:
            URLValidator(schemes=['http', 'https'])(url)
        except forms.ValidationError:
            self.add_error('video_url', error)

    @staticmethod
    def read_options(cleaned):
        try:
            return json.loads(cleaned.get('options', ''))
        except (ValueError, RecursionError):
            return None

    def clean_trace(self, cleaned):
        code = cleaned.get('code', '')
        if not code.strip():
            self.add_error('code', 'Enter the Python code for this worked example.')
        line_count = len(code.splitlines())
        steps = self.read_options(cleaned)
        if not isinstance(steps, list) or not steps:
            self.add_error('options', 'Enter at least one animation step in a JSON array.')
            return
        for index, step in enumerate(steps, 1):
            if not isinstance(step, dict):
                self.add_error('options', f'Step {index} must be a JSON object.')
                continue
            line = step.get('line')
            if type(line) is not int or not 1 <= line <= line_count:
                self.add_error('options', f'Step {index} must refer to a line in the code.')
            caption = step.get('caption')
            if not isinstance(caption, str) or not caption.strip():
                self.add_error('options', f'Step {index} must include a caption.')
            if any(not isinstance(step.get(key, ''), str) for key in ('state', 'output')):
                self.add_error('options', f'Step {index} must use text for state and output.')


class LessonBlockInline(admin.StackedInline):
    model=LessonBlock
    form = LessonBlockForm
    extra=0
    ordering=['position']
    fieldsets=[(None,{'fields':[('block_type','position','is_published')]}),('Content',{'fields':['title','body','code','video_url','options','correct_option','explanation']})]
    verbose_name_plural = 'Lesson content blocks'


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    inlines=[LessonBlockInline]
    class Media:
        js=('learning/admin_blocks.js',)
    list_display=['title','chapter','position','is_published']
    list_filter=['chapter','is_published']
    search_fields=['title','explanation']
    readonly_fields = ['chapter_settings']
    fieldsets = [
        ('Lesson settings', {'fields': ['title', 'chapter', 'chapter_settings', 'position', 'is_published']}),
        ('Fallback content', {
            'classes': ['collapse'],
            'description': 'These fields are shown in the reader when there are no visible content blocks.',
            'fields': ['explanation', 'code_example', 'expected_output', 'video_url', 'summary'],
        }),
    ]

    @admin.display(description='Chapter editor')
    def chapter_settings(self, obj):
        if obj is None or not obj.chapter_id:
            return '—'
        url = reverse('admin:learning_chapter_change', args=[obj.chapter_id])
        return format_html('<a href="{}">Open chapter settings</a>', url)

@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display=['user_id','lesson','status','last_read_at','completed_at','rating']
    list_filter=['status']
    readonly_fields=['user_id','lesson','started_at','last_read_at','completed_at','rating']
    def has_add_permission(self,request): return False
