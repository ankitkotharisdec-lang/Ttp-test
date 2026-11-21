import uuid
from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
# On Supabase/Postgres the tables are owned by Supabase (see README), so Django must not create or alter them.
# On local SQLite there is no Supabase, so Django creates them (python manage.py migrate --run-syncdb).
MANAGED=settings.DATABASES['default']['ENGINE'].endswith('sqlite3')
class OrderedContent(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    title=models.CharField(max_length=200)
    position=models.PositiveIntegerField(default=1)
    is_published=models.BooleanField(default=False)
    class Meta:
        abstract=True
        ordering=['position','id']
    def __str__(self): return self.title
class Course(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    title=models.CharField(max_length=200)
    slug=models.SlugField(unique=True)
    is_published=models.BooleanField(default=False)
    class Meta:
        db_table='courses'
        managed=MANAGED
    def __str__(self): return self.title
class Section(OrderedContent):
    course=models.ForeignKey(Course,on_delete=models.PROTECT,related_name='sections')
    class Meta(OrderedContent.Meta):
        db_table='sections'
        managed=MANAGED
        indexes=[models.Index(fields=['course','position'])]
class Chapter(OrderedContent):
    section=models.ForeignKey(Section,on_delete=models.PROTECT,related_name='chapters')
    class Meta(OrderedContent.Meta):
        db_table='chapters'
        managed=MANAGED
        indexes=[models.Index(fields=['section','position'])]
class Lesson(OrderedContent):
    chapter=models.ForeignKey(Chapter,on_delete=models.PROTECT,related_name='lessons')
    explanation=models.TextField(blank=True)
    code_example=models.TextField(blank=True)
    expected_output=models.TextField(blank=True)
    video_url=models.URLField(blank=True)
    summary=models.TextField(blank=True)
    class Meta(OrderedContent.Meta):
        db_table='lessons'
        managed=MANAGED
        indexes=[models.Index(fields=['chapter','position'])]
    def get_absolute_url(self): return reverse('lesson-detail',args=[self.id])

class LessonBlock(models.Model):
    """One piece of lesson content. Admins stack blocks to build a lesson: text, Must Know box, highlight, example, code, video."""
    TEXT,MUST_KNOW,HIGHLIGHT,EXAMPLE,CODE,VIDEO,SUMMARY='text','must_know','highlight','example','code','video','summary'
    TYPES=[(TEXT,'Text paragraph'),(MUST_KNOW,'Must Know box'),(HIGHLIGHT,'Highlighted text'),(EXAMPLE,'Example (practice question)'),(CODE,'Code example'),(VIDEO,'Video'),(SUMMARY,'Summary / key takeaways')]
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    lesson=models.ForeignKey(Lesson,on_delete=models.CASCADE,related_name='blocks')
    position=models.PositiveIntegerField(default=1)
    block_type=models.CharField(max_length=20,choices=TYPES,default=TEXT)
    title=models.CharField(max_length=200,blank=True,help_text='Optional heading. For Example blocks this is the label, e.g. "Example 1".')
    body=models.TextField(blank=True,help_text='The text. Blank lines make new paragraphs. For Example blocks this is the question.')
    code=models.TextField(blank=True,help_text='Python code shown in a code box.')
    video_url=models.URLField(blank=True,help_text='YouTube or other video link.')
    options=models.TextField(blank=True,help_text='Example blocks only: one answer choice per line.')
    correct_option=models.PositiveIntegerField(default=0,help_text='Example blocks only: number of the correct choice (1 = first line).')
    explanation=models.TextField(blank=True,help_text='Example blocks only: shown after the student answers.')
    is_published=models.BooleanField(default=True)
    class Meta:
        db_table='lesson_blocks'
        managed=MANAGED
        ordering=['position','id']
        indexes=[models.Index(fields=['lesson','position'])]
    def __str__(self): return f'{self.get_block_type_display()}: {self.title or self.body[:40]}'
    @property
    def option_list(self): return [o.strip() for o in self.options.splitlines() if o.strip()]
class LessonProgress(models.Model):
    IN_PROGRESS,COMPLETED='in_progress','completed'
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    user_id=models.UUIDField(db_index=True)  # Supabase auth user id
    lesson=models.ForeignKey(Lesson,on_delete=models.CASCADE,related_name='progress')
    status=models.CharField(max_length=20,choices=[(IN_PROGRESS,'In progress'),(COMPLETED,'Completed')],default=IN_PROGRESS)
    started_at=models.DateTimeField(default=timezone.now)
    last_read_at=models.DateTimeField(default=timezone.now)
    completed_at=models.DateTimeField(null=True,blank=True)
    rating=models.PositiveSmallIntegerField(null=True,blank=True)
    class Meta:
        db_table='lesson_progress'
        managed=MANAGED
        constraints=[models.UniqueConstraint(fields=['user_id','lesson'],name='lesson_progress_user_lesson_uniq')]
        indexes=[models.Index(fields=['user_id','-last_read_at'],name='lesson_progress_user_read_idx')]
class DailyActivity(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    user_id=models.UUIDField(db_index=True)
    day=models.DateField()
    lessons_completed=models.PositiveIntegerField(default=0)
    xp=models.PositiveIntegerField(default=0)
    class Meta:
        db_table='daily_activity'
        managed=MANAGED
        constraints=[models.UniqueConstraint(fields=['user_id','day'],name='daily_activity_user_day_uniq')]
