import uuid
from django.conf import settings
from django.db import models
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
