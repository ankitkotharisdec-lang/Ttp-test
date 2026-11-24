import re
from urllib.parse import parse_qs, urlparse
from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe

register = template.Library()
_INLINE_CODE = re.compile(r'`([^`]+)`')
_BOLD = re.compile(r'\*\*([^*]+)\*\*')


def _inline(t):
    t = escape(t)
    t = _INLINE_CODE.sub(r'<code>\1</code>', t)
    return _BOLD.sub(r'<strong>\1</strong>', t)


@register.filter
def rich(text):
    """Escapes everything, then supports paragraphs, '- ' bullet lists, **bold** and `code`."""
    out = []
    for para in re.split(r'\n\s*\n', (text or '').strip()):
        lines = [l for l in para.split('\n') if l.strip()]
        if not lines:
            continue
        if all(l.lstrip().startswith('- ') for l in lines):
            out.append('<ul>' + ''.join(f'<li>{_inline(l.lstrip()[2:])}</li>' for l in lines) + '</ul>')
        else:
            out.append('<p>' + '<br>'.join(_inline(l) for l in lines) + '</p>')
    return mark_safe(''.join(out))


@register.filter
def embed_url(url):
    """Returns an embeddable URL for YouTube/Vimeo links, else ''."""
    try:
        u = urlparse(url or '')
    except ValueError:
        return ''
    host = (u.hostname or '').lower().removeprefix('www.')
    if u.scheme not in ('http', 'https'):
        return ''
    if host == 'youtu.be' and u.path.strip('/'):
        return f'https://www.youtube.com/embed/{u.path.strip("/")}'
    if host in ('youtube.com', 'm.youtube.com'):
        v = parse_qs(u.query).get('v', [''])[0]
        if v:
            return f'https://www.youtube.com/embed/{v}'
        if u.path.startswith('/embed/'):
            return url
    if host == 'vimeo.com' and u.path.strip('/').isdigit():
        return f'https://player.vimeo.com/video/{u.path.strip("/")}'
    return ''


@register.filter
def http_only(url):
    return url if (url or '').lower().startswith(('http://', 'https://')) else ''


@register.filter
def lesson_image_url(url):
    url = url or ''
    if re.fullmatch(r'/static/learning/[\w-]+\.(?:gif|png|jpe?g|webp|avif)', url, re.IGNORECASE):
        return url
    return http_only(url)
