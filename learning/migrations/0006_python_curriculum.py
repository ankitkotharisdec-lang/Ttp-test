import re

from django.db import IntegrityError, migrations, models

from learning.python_curriculum import install_python_curriculum


BLOCK_TYPES = [
    ('text', 'Text paragraph'),
    ('must_know', 'Must Know box'),
    ('highlight', 'Highlighted text'),
    ('example', 'Example (practice question)'),
    ('code', 'Code example'),
    ('video', 'Video'),
    ('summary', 'Summary / key takeaways'),
    ('trace', 'Code walkthrough'),
    ('practice', 'Python exercise'),
    ('image', 'Image or GIF'),
    ('diagram', 'Flow diagram'),
]
NEW_BLOCK_TYPES = {value for value, _ in BLOCK_TYPES[7:]}


def _allowlist(expression):
    """Recognize PostgreSQL's deparsed single-column IN expression."""
    expression = re.sub(r'::(?:character varying|varchar|text)(?:\[\])?', '', expression)
    expression = re.sub(r'[()\s"]', '', expression)
    match = re.fullmatch(r"block_type=ANYARRAY\[('[a-z_]+(?:','[a-z_]+)*')\]", expression)
    return set(re.findall(r"'([a-z_]+)'", match[1])) if match else None


def extend_block_type_allowlist(apps, schema_editor):
    """Some Supabase schemas restrict the block types through a CHECK."""
    connection = schema_editor.connection
    if connection.vendor != 'postgresql':
        return
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT c.conname, pg_get_expr(c.conbin, c.conrelid), c.convalidated,
                   c.connoinherit, cardinality(c.conkey)
            FROM pg_constraint c
            JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = ANY(c.conkey)
            WHERE c.conrelid = 'lesson_blocks'::regclass AND c.contype = 'c'
              AND a.attname = 'block_type'
            """
        )
        constraints = cursor.fetchall()
    for name, expression, validated, no_inherit, columns in constraints:
        allowed = _allowlist(expression) if columns == 1 else None
        if allowed is None:
            # This may be an unrelated validation, such as a non-empty value check.
            # Keep its semantics and let PostgreSQL enforce it for seeded rows.
            continue
        if NEW_BLOCK_TYPES <= allowed:
            continue
        quote = schema_editor.quote_name
        values = ', '.join(f"'{value}'" for value in sorted(allowed | NEW_BLOCK_TYPES))
        suffix = (' NO INHERIT' if no_inherit else '') + ('' if validated else ' NOT VALID')
        schema_editor.execute(
            f'ALTER TABLE {quote("lesson_blocks")} DROP CONSTRAINT {quote(name)}, '
            f'ADD CONSTRAINT {quote(name)} CHECK (block_type IN ({values})){suffix}'
        )


def seed(apps, schema_editor):
    try:
        install_python_curriculum(apps, schema_editor.connection.alias)
    except IntegrityError as exc:
        postgres_error = exc.__cause__
        details = getattr(postgres_error, 'diag', None)
        if getattr(postgres_error, 'sqlstate', None) == '23514' and details.table_name == 'lesson_blocks':
            raise RuntimeError(
                f'The Supabase lesson_blocks check {details.constraint_name!r} rejected curriculum data. '
                'Review the constraint for the trace, practice, image, and diagram block types before retrying.'
            ) from exc
        raise


class Migration(migrations.Migration):
    dependencies = [('learning', '0005_annotations')]
    operations = [
        migrations.SeparateDatabaseAndState(state_operations=[
            migrations.AlterField(
                model_name='lessonblock',
                name='video_url',
                field=models.CharField(max_length=200, blank=True, help_text='Video or image URL.'),
            ),
            migrations.AlterField(
                model_name='lessonblock',
                name='block_type',
                field=models.CharField(max_length=20, choices=BLOCK_TYPES, default='text'),
            ),
        ]),
        migrations.RunPython(extend_block_type_allowlist, migrations.RunPython.noop),
        migrations.RunPython(seed, migrations.RunPython.noop),
    ]
