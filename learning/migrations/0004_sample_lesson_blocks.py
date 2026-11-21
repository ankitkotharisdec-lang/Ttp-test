from django.db import migrations
from learning.sample_content import seed_blocks


def seed(apps, schema_editor):
    """Fills empty lessons only, so it does nothing on Supabase where the blocks are already loaded."""
    db = schema_editor.connection.alias
    Lesson = apps.get_model('learning', 'Lesson')
    Block = apps.get_model('learning', 'LessonBlock')

    class _Mgr:  # lets seed_blocks use historical models with the right database alias
        def __init__(self, model):
            self.objects = model.objects.using(db)
    seed_blocks(_Mgr(Lesson), _Mgr(Block))


class Migration(migrations.Migration):
    dependencies = [('learning', '0003_blocks_progress_activity')]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
