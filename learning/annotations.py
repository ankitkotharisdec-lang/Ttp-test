import hashlib
import json
import re
from uuid import UUID

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_http_methods

from .models import Lesson, LessonAnnotation

BLOCK_KEY = re.compile(r'[a-zA-Z0-9_-]{1,100}')
MAX_QUOTE = 3000
MAX_SELECTIONS = 16


def _published_lessons():
    return Lesson.objects.filter(
        is_published=True,
        chapter__is_published=True,
        chapter__section__is_published=True,
        chapter__section__course__is_published=True,
    )


def _user_id(request):
    try:
        return UUID(request.session.get('sb_user_id', ''))
    except (ValueError, AttributeError, TypeError):
        return None


def _invalid():
    return JsonResponse({'error': 'invalid_annotation'}, status=400)


def _highlight_entries(payload, user_id, lesson):
    selections = payload.get('selections')
    if not isinstance(selections, list) or not 1 <= len(selections) <= MAX_SELECTIONS:
        raise ValueError
    entries = []
    for selection in selections:
        if not isinstance(selection, dict):
            raise ValueError
        block = selection.get('block')
        start = selection.get('start')
        end = selection.get('end')
        quote = selection.get('quote')
        if not isinstance(block, str) or not BLOCK_KEY.fullmatch(block):
            raise ValueError
        if type(start) is not int or type(end) is not int or not 0 <= start < end <= 100_000:
            raise ValueError
        if not isinstance(quote, str) or not quote.strip() or '\0' in quote or len(quote) > MAX_QUOTE:
            raise ValueError
        # Browser Range offsets are UTF-16 code units.
        if len(quote.encode('utf-16-le')) // 2 != end - start:
            raise ValueError
        encoded = json.dumps([block, start, end, quote], ensure_ascii=True).encode()
        entries.append(LessonAnnotation(
            user_id=user_id,
            lesson=lesson,
            signature=hashlib.sha256(encoded).hexdigest(),
            block_key=block,
            start=start,
            end=end,
            quote=quote,
        ))
    return entries


@never_cache
@require_http_methods(['GET', 'POST'])
def lesson_annotations(request, lesson_id):
    user_id = _user_id(request)
    if user_id is None:
        return JsonResponse({'error': 'login_required'}, status=401)
    lesson = get_object_or_404(_published_lessons(), pk=lesson_id)
    entries = LessonAnnotation.objects.filter(user_id=user_id, lesson=lesson)
    if request.method == 'POST':
        try:
            if len(request.body) > 80_000:
                return _invalid()
            payload = json.loads(request.body)
            if not isinstance(payload, dict):
                return _invalid()
            action = payload.get('action')
            if action == 'bookmark' and type(payload.get('saved')) is bool:
                if payload['saved']:
                    LessonAnnotation.objects.get_or_create(
                        user_id=user_id, lesson=lesson, signature=LessonAnnotation.BOOKMARK
                    )
                else:
                    entries.filter(signature=LessonAnnotation.BOOKMARK).delete()
            elif action == 'highlight':
                LessonAnnotation.objects.bulk_create(
                    _highlight_entries(payload, user_id, lesson), ignore_conflicts=True
                )
            elif action == 'remove':
                highlight_id = UUID(payload.get('id', ''))
                entries.exclude(signature=LessonAnnotation.BOOKMARK).filter(pk=highlight_id).delete()
            else:
                return _invalid()
        except (ValueError, AttributeError, TypeError):
            return _invalid()
    records = list(entries)
    return JsonResponse({
        'saved': any(record.signature == LessonAnnotation.BOOKMARK for record in records),
        'highlights': [
            {'id': str(record.id), 'block': record.block_key, 'start': record.start,
             'end': record.end, 'quote': record.quote}
            for record in records if record.signature != LessonAnnotation.BOOKMARK
        ],
    })


@never_cache
@require_GET
def course_bookmarks(request, slug):
    user_id = _user_id(request)
    if user_id is None:
        return JsonResponse({'error': 'login_required'}, status=401)
    lessons = _published_lessons().filter(chapter__section__course__slug=slug)
    bookmarks = LessonAnnotation.objects.filter(
        user_id=user_id, lesson__in=lessons, signature=LessonAnnotation.BOOKMARK,
    ).select_related('lesson__chapter')
    return JsonResponse({
        'bookmarks': [
            {'id': str(row.lesson_id), 'title': row.lesson.title, 'chapter': row.lesson.chapter.title,
             'url': row.lesson.get_absolute_url()}
            for row in bookmarks
        ],
    })
