import uuid
import django.db.models.deletion
from django.db import migrations, models

# On Supabase/Postgres these tables already exist and are owned by Supabase, so this migration only
# records the models. On local SQLite it creates the tables so the app works without Supabase.


def create_tables_on_sqlite(apps, schema_editor):
    if schema_editor.connection.vendor != 'sqlite':
        return
    for name in ('Course', 'Section', 'Chapter', 'Lesson'):
        schema_editor.create_model(apps.get_model('learning', name))


def _base():
    return [
        ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
        ('title', models.CharField(max_length=200)),
    ]


def _ordered():
    return [
        ('position', models.PositiveIntegerField(default=1)),
        ('is_published', models.BooleanField(default=False)),
    ]


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.SeparateDatabaseAndState(state_operations=[
            migrations.CreateModel(name='Course', fields=_base() + [
                ('slug', models.SlugField(unique=True)),
                ('is_published', models.BooleanField(default=False)),
            ], options={'db_table': 'courses'}),
            migrations.CreateModel(name='Section', fields=_base() + _ordered() + [
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='sections', to='learning.course')),
            ], options={'db_table': 'sections', 'ordering': ['position', 'id'], 'indexes': [models.Index(fields=['course', 'position'], name='sections_course_position_idx')]}),
            migrations.CreateModel(name='Chapter', fields=_base() + _ordered() + [
                ('section', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='chapters', to='learning.section')),
            ], options={'db_table': 'chapters', 'ordering': ['position', 'id'], 'indexes': [models.Index(fields=['section', 'position'], name='chapters_section_position_idx')]}),
            migrations.CreateModel(name='Lesson', fields=_base() + _ordered() + [
                ('explanation', models.TextField(blank=True)),
                ('code_example', models.TextField(blank=True)),
                ('expected_output', models.TextField(blank=True)),
                ('video_url', models.URLField(blank=True)),
                ('summary', models.TextField(blank=True)),
                ('chapter', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='lessons', to='learning.chapter')),
            ], options={'db_table': 'lessons', 'ordering': ['position', 'id'], 'indexes': [models.Index(fields=['chapter', 'position'], name='lessons_chapter_position_idx')]}),
        ]),
        migrations.RunPython(create_tables_on_sqlite, migrations.RunPython.noop),
    ]
