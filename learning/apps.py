from django.apps import AppConfig
from django.db.models.signals import post_migrate


def lock_down_public_tables(sender, using='default', **kwargs):
    """Supabase exposes the public schema through its REST API. Django connects as the table owner
    (which bypasses row level security), so enabling RLS with no policies hides every Django-managed
    table from the public API without affecting the app."""
    from django.db import connections
    conn = connections[using]
    if conn.vendor != 'postgresql':
        return
    with conn.cursor() as cur:
        cur.execute("""DO $$ DECLARE r record; BEGIN
            FOR r IN SELECT tablename FROM pg_tables WHERE schemaname = 'public' LOOP
                EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', r.tablename);
            END LOOP; END $$;""")


class LearningConfig(AppConfig):
    name = 'learning'
    default_auto_field = 'django.db.models.BigAutoField'

    def ready(self):
        post_migrate.connect(lock_down_public_tables, dispatch_uid='learning_lock_down_public_tables')
