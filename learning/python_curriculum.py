"""Install the first full Python curriculum over the original sample course."""

import json
from importlib import import_module
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from .sample_content import SAMPLE_BLOCKS


LEGACY_SECTIONS = import_module('learning.migrations.0002_sample_python_course').DATA
LEGACY_LESSON_CHAPTER = {
    lesson: chapter
    for section in LEGACY_SECTIONS.values()
    for chapter, lessons in section
    for lesson in lessons
}
SECTIONS = (
    ('core', 'Python Core', ('introduction', 'types-operators')),
    ('structures', 'Data Structures', ('lists', 'tuples-sets', 'dictionaries')),
    ('control', 'Control Flow and Functions', ('conditionals', 'loops', 'exceptions', 'functions')),
    ('engineering', 'Data Engineering', ('files-and-formats', 'sqlite-crud')),
    ('projects', 'Projects', ('optional-record-classes', 'pipeline-project')),
)
BLOCK_DEFAULTS = {
    'block_type': 'text',
    'title': '',
    'body': '',
    'code': '',
    'video_url': '',
    'options': '',
    'correct_option': 0,
    'explanation': '',
    'is_published': True,
}
LEGACY_FIELD_DEFAULTS = {
    'explanation': ('', 'Sample lesson. Replace this text through the Django admin.'),
    'code_example': ('', 'message = "Hello, Python!"\nprint(message)'),
    'expected_output': ('', 'Hello, Python!'),
    'video_url': ('',),
    'summary': ('', 'Practice the example, then add your own content.'),
}


def _curriculum_id(kind, key):
    return uuid5(NAMESPACE_URL, f'https://ttp-test.onrender.com/courses/python/{kind}/{key}')


def _read_catalog():
    return json.loads(Path(__file__).with_name('python_curriculum.json').read_text(encoding='utf-8'))


def _find_existing(query, key, titles):
    item = query.filter(pk=key).first()
    for title in titles:
        if item is not None:
            break
        if title:
            matches = list(query.filter(title=title)[:2])
            if len(matches) == 1:
                item = matches[0]
    return item


def _update_fields(item, alias, **changes):
    changed = []
    for field, value in changes.items():
        if getattr(item, field) != value:
            setattr(item, field, value)
            changed.append(field)
    if changed:
        item.save(using=alias, update_fields=changed)


def _stock_lessons(chapters, Lesson):
    """Find old sample lessons in their original chapters before any moves."""
    original_chapters = {}
    for section_name, section_data in LEGACY_SECTIONS.items():
        for title, _ in section_data:
            matches = [chapter for chapter in chapters if chapter.title == title]
            original = next((chapter for chapter in matches if chapter.section.title == section_name), None)
            if original is None and len(matches) == 1:
                original = matches[0]
            if original is not None:
                original_chapters[title] = original

    old_lessons = {}
    for title, chapter_name in LEGACY_LESSON_CHAPTER.items():
        chapter = original_chapters.get(chapter_name)
        if chapter is None:
            continue
        matches = list(Lesson.filter(chapter_id=chapter.id, title=title)[:2])
        if len(matches) == 1:
            old_lessons[title] = (matches[0], chapter.is_published and chapter.section.is_published)
    return original_chapters, old_lessons


def _matches_sample_blocks(existing, title):
    stock = SAMPLE_BLOCKS.get(title, [])
    return len(existing) == len(stock) and all(
        block.position == position
        and all(getattr(block, name) == value for name, value in (BLOCK_DEFAULTS | definition).items())
        for position, (block, definition) in enumerate(zip(existing, stock), 1)
    )


def _legacy_blocks(lesson):
    """Materialize edited fallback fields before new blocks supersede the fallback reader."""
    def custom(name):
        value = getattr(lesson, name)
        return value if value not in LEGACY_FIELD_DEFAULTS[name] else ''

    if explanation := custom('explanation'):
        yield {'body': explanation}
    if code := custom('code_example'):
        yield {'block_type': 'code', 'title': 'Example', 'code': code}
    if output := custom('expected_output'):
        yield {'block_type': 'code', 'title': 'Output', 'code': output}
    if video_url := custom('video_url'):
        yield {'block_type': 'video', 'video_url': video_url}
    if summary := custom('summary'):
        yield {'block_type': 'summary', 'title': 'Key takeaways', 'body': summary}


def _catalog_blocks(definition, image_url):
    for paragraph in definition['explanation']:
        yield {'body': paragraph}
    if definition['id'] == 'append-extend-insert':
        yield {
            'block_type': 'image',
            'title': 'See what append changes',
            'video_url': image_url,
            'body': 'Watch the new value join the end of the list while the existing items keep their positions.',
            'explanation': 'Two existing file names stay at positions 0 and 1 as append adds a third at position 2.',
        }
    if labels := definition.get('diagram'):
        yield {'block_type': 'diagram', 'title': 'How it fits together', 'options': json.dumps(labels)}

    # Keep the original concept check in this lesson alongside the new coding exercise.
    if definition['title'] == 'Understanding variables':
        yield from (
            block for block in SAMPLE_BLOCKS['Understanding variables']
            if block['block_type'] in ('must_know', 'example')
        )

    example = definition['example']
    yield {
        'block_type': 'trace',
        'title': example.get('title', 'Step through the code'),
        'body': example.get('body', ''),
        'code': example['code'],
        'explanation': example['output'],
        'options': json.dumps(example['steps'], ensure_ascii=False),
    }
    practice = definition['practice']
    yield {
        'block_type': 'practice',
        'title': practice.get('title', 'Practice in Python'),
        'body': practice['prompt'],
        'code': practice['starter'],
        'explanation': practice['expected'],
        'options': practice.get('solution', ''),
    }
    if summary := definition.get('summary'):
        yield {'block_type': 'summary', 'title': 'Key takeaways', 'body': summary}


def _add_lesson_blocks(Block, lesson, definition, image_url):
    existing = list(Block.filter(lesson_id=lesson.id).order_by('position', 'id'))
    legacy_title = definition.get('legacy_title') or definition['title']
    start = existing[-1].position if existing else 0
    new_blocks = []
    if _matches_sample_blocks(existing, legacy_title):
        Block.filter(lesson_id=lesson.id).delete()
        existing = []
        start = 0
    if not any(block.is_published for block in existing):
        new_blocks.extend(_legacy_blocks(lesson))
    new_blocks.extend(_catalog_blocks(definition, image_url))
    Block.bulk_create([
        Block.model(
            id=_curriculum_id('block', f"{definition['id']}/{offset}"),
            lesson_id=lesson.id,
            position=start + offset,
            **(BLOCK_DEFAULTS | block),
        )
        for offset, block in enumerate(new_blocks, 1)
    ])


def install_python_curriculum(apps, alias, *, image_url='/static/learning/list-append.gif'):
    """Seed the course once, preserving lesson UUIDs and existing author content."""
    Course, Section, Chapter, Lesson, Block = (
        apps.get_model('learning', name).objects.using(alias)
        for name in ('Course', 'Section', 'Chapter', 'Lesson', 'LessonBlock')
    )
    catalog = {chapter['id']: chapter for chapter in _read_catalog()}
    if set(catalog) != {key for _, _, chapter_ids in SECTIONS for key in chapter_ids}:
        raise ValueError('Python curriculum chapters and section assignments must match.')
    all_lesson_ids = [lesson['id'] for chapter in catalog.values() for lesson in chapter['lessons']]
    if len(all_lesson_ids) != len(set(all_lesson_ids)):
        raise ValueError('Python curriculum lesson IDs must be unique.')

    course, _ = Course.select_for_update().get_or_create(
        slug='python', defaults={'title': 'Python', 'is_published': True}
    )
    blocks = Block.filter(lesson__chapter__section__course=course)
    if blocks.filter(pk__in=[_curriculum_id('block', f'{key}/1') for key in all_lesson_ids]).exists():
        return False

    course_sections = Section.filter(course=course)
    course_chapters = Chapter.filter(section__course=course)
    initial_sections = list(course_sections)
    initial_chapters = list(course_chapters.select_related('section'))
    original_chapters, old_lessons = _stock_lessons(initial_chapters, Lesson)
    used_sections, used_chapters, used_lessons = set(), set(), set()

    for section_position, (section_key, title, chapter_keys) in enumerate(SECTIONS, 1):
        section_id = _curriculum_id('section', section_key)
        section = _find_existing(course_sections, section_id, (title,))
        if section is None:
            section = Section.create(
                id=section_id, course=course, title=title, position=section_position, is_published=True
            )
        else:
            _update_fields(section, alias, title=title, position=section_position)
        used_sections.add(section.id)

        for chapter_position, chapter_key in enumerate(chapter_keys, 1):
            chapter_definition = catalog[chapter_key]
            chapter_id = _curriculum_id('chapter', chapter_key)
            chapter_title = chapter_definition['title']
            legacy_title = chapter_definition.get('legacy_title') or chapter_title
            chapter = (
                _find_existing(course_chapters.filter(section=section), chapter_id, (chapter_title,))
                or original_chapters.get(legacy_title)
            )
            if chapter is None or chapter.id in used_chapters:
                chapter = Chapter.create(
                    id=chapter_id, section=section, title=chapter_title, position=chapter_position,
                    is_published=True,
                )
            else:
                publish = chapter.is_published
                if chapter.section_id != section.id:
                    publish = publish and chapter.section.is_published
                _update_fields(
                    chapter, alias, section_id=section.id, title=chapter_title, position=chapter_position,
                    is_published=publish,
                )
            used_chapters.add(chapter.id)

            for lesson_position, definition in enumerate(chapter_definition['lessons'], 1):
                lesson_key = _curriculum_id('lesson', definition['id'])
                lesson_title = definition['title']
                old_name = definition.get('legacy_title') or lesson_title
                lesson = _find_existing(Lesson.filter(chapter_id=chapter.id), lesson_key, (lesson_title, old_name))
                prior_lesson, was_visible = old_lessons.get(old_name, (None, True))
                if lesson is None:
                    lesson = prior_lesson
                if lesson is None or lesson.id in used_lessons:
                    lesson = Lesson.create(
                        id=lesson_key, chapter=chapter, title=lesson_title, position=lesson_position,
                        is_published=True,
                    )
                else:
                    publish = lesson.is_published
                    if lesson.chapter_id != chapter.id and prior_lesson is not None:
                        publish = publish and was_visible
                    _update_fields(
                        lesson, alias, chapter_id=chapter.id, title=lesson_title, position=lesson_position,
                        is_published=publish,
                    )
                used_lessons.add(lesson.id)
                _add_lesson_blocks(Block, lesson, definition, image_url)

    # Preserve legacy IDs and any authored material in retired sample containers.
    for chapter in original_chapters.values():
        if chapter.id not in used_chapters and not Lesson.filter(chapter_id=chapter.id).exists():
            _update_fields(chapter, alias, is_published=False)
    for section in initial_sections:
        if (
            section.id not in used_sections and section.title in LEGACY_SECTIONS
            and not Chapter.filter(section_id=section.id, is_published=True).exists()
        ):
            _update_fields(section, alias, is_published=False)
    return True
