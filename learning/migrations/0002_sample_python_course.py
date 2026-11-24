from uuid import NAMESPACE_URL, uuid5

from django.db import migrations

DATA = {
    'Python Core': [('Introduction to Python', ['What is Python?', 'Installing Python', 'Your first program']), ('Variables and Data Types', ['Understanding variables', 'Numbers and strings', 'Type conversion']), ('Control Flow', ['If statements', 'Else and elif', 'Nested conditions']), ('Strings', ['Indexing', 'Slicing', 'String methods']), ('Loops and Iteration', ['For loops', 'While loops', 'Break and continue'])],
    'Data Structures': [('Lists and Tuples', ['Creating lists', 'List methods', 'Tuples']), ('Dictionaries and Sets', ['Key-value pairs', 'Dictionary methods', 'Sets'])],
    'OOP and Modules': [('Functions', ['Defining functions', 'Arguments', 'Return values']), ('Classes and Objects', ['Classes', 'Objects', 'Methods'])],
    'Projects': [('Expense Tracker', ['Project requirements', 'Build the tracker', 'Test your solution'])],
}


# Keep the published UUIDs when this migration seeds a fresh database.
# Databases with an existing course skip the seed and retain their own IDs.
COURSE_ID = 'aa44f58d-5cb9-4b0d-a311-4a458aa19ae1'
SECTION_IDS = {
    'Data Structures': '34435d9f-9735-4ed7-9417-9eed69db25d3',
    'Projects': '3eab7fbd-2cdb-4b21-b761-9882113735df',
    'Python Core': '9b6f347a-d93d-4798-8400-b76e37a23860',
}

CHAPTER_IDS = {
    'Classes and Objects': '6b22da67-0c33-4dcc-b0fb-d146773ad10d',
    'Control Flow': '79f1068d-2ea6-4588-bbfc-8ad7dbf4dd9a',
    'Dictionaries and Sets': 'e4f31587-6e97-46ae-a47f-f09d54bab190',
    'Expense Tracker': '437a4385-1af6-4a86-b28f-6de0f4855db8',
    'Functions': 'acf3c6bb-0660-4c26-afec-332e515a454c',
    'Introduction to Python': 'c978a186-fa24-4380-996c-b81c86ec144e',
    'Lists and Tuples': 'cbf62508-2e00-4a51-8c8e-e918865e37ba',
    'Loops and Iteration': '5ee64610-8b03-41cd-a1ae-09dce71cb76c',
    'Variables and Data Types': '67d7efc7-dfe6-4072-9a5b-852b5cea9826',
}

LESSON_IDS = {
    'Arguments': '93e2d9fe-5986-4931-9bed-af45589111de',
    'Break and continue': 'ab7272ce-3eab-47b0-bf37-3a6d593db499',
    'Build the tracker': '89ec1463-0135-4fcd-813b-65e80a92abe5',
    'Classes': 'ea1150a8-beab-4218-8b6f-e8decba3f9cd',
    'Creating lists': 'd55f5bf7-e1ac-43b7-8318-6352a077b49b',
    'Defining functions': '54726bde-08cb-4e67-ae0f-7bc6b5781ad5',
    'Dictionary methods': 'b796dca3-4817-45af-84f1-0b62ff265170',
    'Else and elif': '0994402b-dc9e-432c-b660-e9db8bc7e9c1',
    'For loops': 'c053b2e0-3a6a-4734-bbaa-853b1c11387e',
    'If statements': '1cb87147-c170-4bdb-a8fe-ecde6157dcfc',
    'Indexing': 'c7216694-c301-42d4-88a3-a998fc1ca628',
    'Installing Python': '880306e4-1c7e-4d26-a48a-5be825749a83',
    'Key-value pairs': '734c5c4e-2217-46a1-af65-6a6fd970a4b0',
    'List methods': '82a7c0a5-d280-477b-b9dd-7f663983cf72',
    'Methods': '4dc48562-657f-4022-a426-6b3cd22d3439',
    'Nested conditions': '2137468b-8988-454c-b0ce-b83176c3b065',
    'Numbers and strings': '0fc8f4a1-5222-4732-92c8-edbf26687b58',
    'Objects': '6a273f7c-ae9e-4733-a2c1-3434d47cc66a',
    'Project requirements': 'ef6ad507-3c1e-4c83-ab28-b70aae1a00a9',
    'Return values': 'cd1ee305-3acb-479c-9f9f-155e8dfb575f',
    'Sets': '120a8071-85fa-4c18-ae9d-583db4a4dad4',
    'Slicing': '4974a505-41f1-4e0a-8824-85cb2b977591',
    'String methods': '3a180c95-eba3-46cc-9d90-0e16bb055204',
    'Test your solution': 'e212a089-d80d-48c7-96b9-7031d0362662',
    'Tuples': '4cc1791f-8d8c-4bf3-b503-f8f020599189',
    'Type conversion': '5a9ed5bc-db9b-44b7-8228-cef56a7aac91',
    'Understanding variables': 'de8d259c-7e46-4995-9f5e-e52a75323415',
    'What is Python?': '934baf6d-a533-4122-a009-953af8465e27',
    'While loops': '693cf34a-e5df-4809-b958-e6fa52481b9f',
    'Your first program': 'e38ea7ae-bfed-48ea-8830-e223f65b7f45',
}


def _seed_id(published_ids, kind, title):
    return published_ids.get(title) or uuid5(NAMESPACE_URL, f"step2success/python/sample/{kind}/{title}")


def seed(apps, schema_editor):
    """Only seeds an empty database (local SQLite). Supabase already has the sample course, so this is skipped there."""
    db = schema_editor.connection.alias
    Course, Section, Chapter, Lesson = [apps.get_model('learning', n).objects.using(db) for n in ('Course', 'Section', 'Chapter', 'Lesson')]
    if Course.filter(slug='python').exists():
        return
    course = Course.create(id=COURSE_ID, slug='python', title='Python', is_published=True)
    for si, (name, chapters) in enumerate(DATA.items(), 1):
        section = Section.create(id=_seed_id(SECTION_IDS, 'section', name), course=course, title=name, position=si, is_published=True)
        for ci, (title, lessons) in enumerate(chapters, 1):
            chapter = Chapter.create(id=_seed_id(CHAPTER_IDS, 'chapter', title), section=section, title=title, position=ci, is_published=True)
            for li, ltitle in enumerate(lessons, 1):
                Lesson.create(id=LESSON_IDS[ltitle], chapter=chapter, title=ltitle, position=li, is_published=True,
                              explanation='Sample lesson. Replace this text through the Django admin.')


class Migration(migrations.Migration):
    dependencies = [('learning', '0001_supabase_content_tables')]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
