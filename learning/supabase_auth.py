"""Thin client for Supabase Auth (GoTrue) and the profile table, using only the stdlib.

Only the publishable key is used. Profile reads/updates run with the signed-in user's own access
token, so Postgres row level security decides what they can see."""
import json
import urllib.error
import urllib.request

from django.conf import settings


class SupabaseError(Exception):
    def __init__(self, message, status=None):
        super().__init__(message)
        self.message = message
        self.status = status


def _request(method, path, body=None, token=None, headers=None):
    if not settings.SUPABASE_URL or not settings.SUPABASE_PUBLISHABLE_KEY:
        raise SupabaseError('Sign-in is not configured yet.')
    req = urllib.request.Request(
        settings.SUPABASE_URL + path,
        data=json.dumps(body).encode() if body is not None else None,
        method=method,
    )
    req.add_header('apikey', settings.SUPABASE_PUBLISHABLE_KEY)
    req.add_header('Authorization', f'Bearer {token or settings.SUPABASE_PUBLISHABLE_KEY}')
    req.add_header('Content-Type', 'application/json')
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read()
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        try:
            data = json.loads(e.read())
            msg = data.get('msg') or data.get('error_description') or data.get('message') or 'Request failed.'
        except Exception:
            msg = 'Request failed.'
        raise SupabaseError(msg, e.code)
    except (urllib.error.URLError, TimeoutError):
        raise SupabaseError('Could not reach the sign-in service. Try again.')


def sign_up(email, password, full_name):
    return _request('POST', '/auth/v1/signup', {'email': email, 'password': password, 'data': {'full_name': full_name}})


def sign_in(email, password):
    return _request('POST', '/auth/v1/token?grant_type=password', {'email': email, 'password': password})


def refresh(refresh_token):
    return _request('POST', '/auth/v1/token?grant_type=refresh_token', {'refresh_token': refresh_token})


def sign_out(token):
    try:
        _request('POST', '/auth/v1/logout', token=token)
    except SupabaseError:
        pass


def get_profile(user_id, token):
    rows = _request('GET', f'/rest/v1/profiles?id=eq.{user_id}&select=*', token=token)
    return rows[0] if rows else None


def update_profile(user_id, token, **fields):
    rows = _request('PATCH', f'/rest/v1/profiles?id=eq.{user_id}', fields, token=token,
                    headers={'Prefer': 'return=representation'})
    return rows[0] if rows else None


# ---- Google (OAuth, PKCE) ----
import base64
import hashlib
import secrets
import urllib.parse


def new_pkce():
    verifier = secrets.token_urlsafe(64)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b'=').decode()
    return verifier, challenge


def google_authorize_url(redirect_to, challenge):
    if not settings.SUPABASE_URL:
        raise SupabaseError('Sign-in is not configured yet.')
    q = urllib.parse.urlencode({'provider': 'google', 'redirect_to': redirect_to,
                                'code_challenge': challenge, 'code_challenge_method': 's256'})
    return f'{settings.SUPABASE_URL}/auth/v1/authorize?{q}'


def exchange_code(code, verifier):
    return _request('POST', '/auth/v1/token?grant_type=pkce', {'auth_code': code, 'code_verifier': verifier})
