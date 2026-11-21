from django.db import migrations

DATA = {
    'Python Core': [('Introduction to Python', ['What is Python?', 'Installing Python', 'Your first program']), ('Variables and Data Types', ['Understanding variables', 'Numbers and strings', 'Type conversion']), ('Control Flow', ['If statements', 'Else and elif', 'Nested conditions']), ('Strings', ['Indexing', 'Slicing', 'String methods']), ('Loops and Iteration', ['For loops', 'While loops', 'Break and continue'])],
    'Data Structures': [('Lists and Tuples', ['Creating lists', 'List methods', 'Tuples']), ('Dictionaries and Sets', ['Key-value pairs', 'Dictionary methods', 'Sets'])],
    'OOP and Modules': [('Functions', ['Defining functions', 'Arguments', 'Return values']), ('Classes and Objects', ['Classes', 'Objects', 'Methods'])],
    'Projects': [('Expense Tracker', ['Project requirements', 'Build the tracker', 'Test your solution'])],
}


def seed(apps, schema_editor):
    """Only seeds an empty database (local SQLite). Supabase already has the sample course, so this is skipped there."""
    db = schema_editor.connection.alias
    Course, Section, Chapter, Lesson = [apps.get_model('learning', n).objects.using(db) for n in ('Course', 'Section', 'Chapter', 'Lesson')]
    if Course.filter(slug='python').exists():
        return
    course = Course.create(slug='python', title='Python', is_published=True)
    for si, (name, chapters) in enumerate(DATA.items(), 1):
        section = Section.create(course=course, title=name, position=si, is_published=True)
        for ci, (title, lessons) in enumerate(chapters, 1):
            chapter = Chapter.create(section=section, title=title, position=ci, is_published=True)
            for li, ltitle in enumerate(lessons, 1):
                Lesson.create(chapter=chapter, title=ltitle, position=li, is_published=True,
                              explanation='Sample lesson. Replace this text through the Django admin.')


class Migration(migrations.Migration):
    dependencies = [('learning', '0001_supabase_content_tables')]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
