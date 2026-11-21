"""Per-user learning progress, XP and streaks. Users are identified by their Supabase auth UUID."""
from datetime import timedelta
from django.db import transaction
from django.db.models import F, Sum
from django.utils import timezone
from .models import DailyActivity, Lesson, LessonProgress

XP_PER_LESSON = 20
DAILY_GOAL = 2  # lessons per day


def mark_started(uid, lesson):
    obj, created = LessonProgress.objects.get_or_create(user_id=uid, lesson=lesson, defaults={'status': 'in_progress'})
    if not created:
        obj.last_read_at = timezone.now()
        obj.save(update_fields=['last_read_at'])
    return obj


@transaction.atomic
def mark_completed(uid, lesson, rating=None):
    """Returns (progress, xp_gained). XP is awarded once per lesson."""
    obj, _ = LessonProgress.objects.select_for_update().get_or_create(user_id=uid, lesson=lesson)
    first_time = obj.status != 'completed'
    now = timezone.now()
    obj.status = 'completed'
    obj.last_read_at = now
    if first_time:
        obj.completed_at = now
    if rating in (1, 2, 3, 4, 5):
        obj.rating = rating
    obj.save()
    xp = 0
    if first_time:
        xp = XP_PER_LESSON
        day, _ = DailyActivity.objects.get_or_create(user_id=uid, day=timezone.localdate())
        DailyActivity.objects.filter(pk=day.pk).update(lessons_completed=F('lessons_completed') + 1, xp=F('xp') + xp)
    return obj, xp


def streak(uid):
    days = set(DailyActivity.objects.filter(user_id=uid, lessons_completed__gt=0).values_list('day', flat=True))
    today = timezone.localdate()
    cur = today if today in days else today - timedelta(days=1)
    n = 0
    while cur in days:
        n += 1
        cur -= timedelta(days=1)
    return n


def stats(uid):
    today = DailyActivity.objects.filter(user_id=uid, day=timezone.localdate()).first()
    total = DailyActivity.objects.filter(user_id=uid).aggregate(x=Sum('xp'))['x'] or 0
    done_today = today.lessons_completed if today else 0
    return {'streak': streak(uid), 'xp': total, 'today_done': done_today, 'daily_goal': DAILY_GOAL,
            'goal_met': done_today >= DAILY_GOAL, 'xp_today': today.xp if today else 0}


def status_map(uid):
    return {p.lesson_id: p.status for p in LessonProgress.objects.filter(user_id=uid)}


def last_read(uid):
    p = (LessonProgress.objects.filter(user_id=uid).select_related('lesson__chapter')
         .order_by('-last_read_at').first())
    if not p:
        return None
    l = p.lesson
    return {'lesson_id': str(l.id), 'lesson_title': l.title, 'chapter_id': str(l.chapter_id),
            'chapter_title': l.chapter.title, 'status': p.status, 'url': l.get_absolute_url()}


def ordered_lessons(course):
    return list(Lesson.objects.filter(is_published=True, chapter__is_published=True, chapter__section__is_published=True,
                                      chapter__section__course=course)
                .order_by('chapter__section__position', 'chapter__position', 'position', 'id'))
