import uuid
import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models

# As in 0001: on Supabase/Postgres these tables already exist (owned by Supabase); on local SQLite they are created here.


def create_tables_on_sqlite(apps, schema_editor):
    if schema_editor.connection.vendor != 'sqlite':
        return
    for name in ('LessonBlock', 'LessonProgress', 'DailyActivity'):
        schema_editor.create_model(apps.get_model('learning', name))


def _id():
    return ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False))


class Migration(migrations.Migration):
    dependencies = [('learning', '0002_sample_python_course')]
    operations = [
        migrations.SeparateDatabaseAndState(state_operations=[
            migrations.CreateModel(name='LessonBlock', fields=[
                _id(),
                ('position', models.PositiveIntegerField(default=1)),
                ('block_type', models.CharField(default='text', max_length=20)),
                ('title', models.CharField(blank=True, max_length=200)),
                ('body', models.TextField(blank=True)),
                ('code', models.TextField(blank=True)),
                ('video_url', models.URLField(blank=True)),
                ('options', models.TextField(blank=True)),
                ('correct_option', models.PositiveIntegerField(default=0)),
                ('explanation', models.TextField(blank=True)),
                ('is_published', models.BooleanField(default=True)),
                ('lesson', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='blocks', to='learning.lesson')),
            ], options={'db_table': 'lesson_blocks', 'ordering': ['position', 'id'], 'indexes': [models.Index(fields=['lesson', 'position'], name='lesson_bloc_lesson__6c1f0b_idx')]}),
            migrations.CreateModel(name='LessonProgress', fields=[
                _id(),
                ('user_id', models.UUIDField(db_index=True)),
                ('status', models.CharField(default='in_progress', max_length=20)),
                ('started_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('last_read_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('rating', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('lesson', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='progress', to='learning.lesson')),
            ], options={'db_table': 'lesson_progress', 'indexes': [models.Index(fields=['user_id', '-last_read_at'], name='lesson_progress_user_read_idx')], 'constraints': [models.UniqueConstraint(fields=['user_id', 'lesson'], name='lesson_progress_user_lesson_uniq')]}),
            migrations.CreateModel(name='DailyActivity', fields=[
                _id(),
                ('user_id', models.UUIDField(db_index=True)),
                ('day', models.DateField()),
                ('lessons_completed', models.PositiveIntegerField(default=0)),
                ('xp', models.PositiveIntegerField(default=0)),
            ], options={'db_table': 'daily_activity', 'constraints': [models.UniqueConstraint(fields=['user_id', 'day'], name='daily_activity_user_day_uniq')]}),
        ]),
        migrations.RunPython(create_tables_on_sqlite, migrations.RunPython.noop),
    ]
