import uuid

import django.db.models.deletion
from django.db import migrations, models


def protect_from_public_api(apps, schema_editor):
    if schema_editor.connection.vendor == 'postgresql':
        schema_editor.execute('ALTER TABLE learning_lesson_annotations ENABLE ROW LEVEL SECURITY')


class Migration(migrations.Migration):
    dependencies = [('learning', '0004_sample_lesson_blocks')]
    operations = [
        migrations.CreateModel(
            name='LessonAnnotation',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('user_id', models.UUIDField()),
                ('signature', models.CharField(max_length=64)),
                ('block_key', models.CharField(blank=True, max_length=100)),
                ('start', models.PositiveIntegerField(default=0)),
                ('end', models.PositiveIntegerField(default=0)),
                ('quote', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('lesson', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE, related_name='annotations', to='learning.lesson'
                )),
            ],
            options={
                'db_table': 'learning_lesson_annotations',
                'constraints': [
                    models.UniqueConstraint(
                        fields=['user_id', 'lesson', 'signature'], name='lesson_annotation_user_key_uniq'
                    ),
                ],
                'ordering': ['-created_at', 'id'],
            },
        ),
        migrations.RunPython(protect_from_public_api, migrations.RunPython.noop),
    ]
