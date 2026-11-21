from django.db.models import Count,Prefetch,Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404,render
from django.views.decorators.http import require_GET
from functools import wraps
from django.shortcuts import redirect
from django.views.decorators.http import require_http_methods
from django.utils.http import url_has_allowed_host_and_scheme
from . import supabase_auth as sb
from .models import Course,Section,Chapter,Lesson
@require_GET
def roadmap(request,slug='python'):
    course=get_object_or_404(Course,slug=slug,is_published=True)
    return render(request,'learning/roadmap.html',{'course':course})
@require_GET
def outline(request,slug):
    chapters=Chapter.objects.filter(is_published=True).annotate(lesson_count=Count('lessons',filter=Q(lessons__is_published=True))).order_by('position','id')
    sections=Section.objects.filter(is_published=True).prefetch_related(Prefetch('chapters',queryset=chapters,to_attr='published_chapters'))
    course=get_object_or_404(Course.objects.prefetch_related(Prefetch('sections',queryset=sections,to_attr='published_sections')),slug=slug,is_published=True)
    return JsonResponse({'id':str(course.id),'title':course.title,'slug':course.slug,'sections':[{'id':str(s.id),'title':s.title,'position':s.position,'chapters':[{'id':str(c.id),'title':c.title,'position':c.position,'lesson_count':c.lesson_count} for c in s.published_chapters]} for s in course.published_sections]})
@require_GET
def chapter_lessons(request,chapter_id):
    chapter=get_object_or_404(Chapter,id=chapter_id,is_published=True,section__is_published=True,section__course__is_published=True)
    return JsonResponse({'id':str(chapter.id),'title':chapter.title,'lessons':list(chapter.lessons.filter(is_published=True).values('id','title','position'))})
@require_GET
def lesson_detail(request,lesson_id):
    lesson=get_object_or_404(Lesson,id=lesson_id,is_published=True,chapter__is_published=True,chapter__section__is_published=True,chapter__section__course__is_published=True)
    return render(request,'learning/lesson.html',{'lesson':lesson})

def _start_session(request,data,profile=None):
    user=data['user']
    request.session.cycle_key()
    request.session['sb_access']=data['access_token']
    request.session['sb_refresh']=data.get('refresh_token','')
    request.session['sb_user_id']=user['id']
    request.session['sb_email']=user.get('email','')
    request.session['sb_plan']=(profile or {}).get('plan','free')
def _safe_next(request):
    nxt=request.POST.get('next') or request.GET.get('next') or ''
    return nxt if url_has_allowed_host_and_scheme(nxt,allowed_hosts={request.get_host()}) else '/account/'
def sb_login_required(view):
    @wraps(view)
    def inner(request,*a,**kw):
        if not request.session.get('sb_user_id'):
            return redirect(f"/login/?next={request.path}")
        return view(request,*a,**kw)
    return inner
@require_http_methods(['GET','POST'])
def login_view(request):
    ctx={'mode':'login','next':request.GET.get('next','')}
    if request.method=='POST':
        email=request.POST.get('email','').strip().lower()
        password=request.POST.get('password','')
        ctx['email']=email
        if not email or not password:
            ctx['error']='Enter your email and password.'
        else:
            try:
                data=sb.sign_in(email,password)
                try: profile=sb.get_profile(data['user']['id'],data['access_token'])
                except sb.SupabaseError: profile=None
                _start_session(request,data,profile)
                return redirect(_safe_next(request))
            except sb.SupabaseError as e:
                ctx['error']='Incorrect email or password.' if e.status==400 and 'confirm' not in e.message.lower() else e.message
    return render(request,'learning/auth.html',ctx)
@require_http_methods(['GET','POST'])
def signup_view(request):
    ctx={'mode':'signup'}
    if request.method=='POST':
        name=request.POST.get('full_name','').strip()
        email=request.POST.get('email','').strip().lower()
        password=request.POST.get('password','')
        ctx.update(full_name=name,email=email)
        if not name or not email:
            ctx['error']='Enter your name and email.'
        elif len(password)<8:
            ctx['error']='Password must be at least 8 characters.'
        else:
            try:
                data=sb.sign_up(email,password,name)
                if data and data.get('access_token'):
                    _start_session(request,data,{'plan':'free'})
                    return redirect('/account/')
                ctx['notice']='Account created. Check your email and click the confirmation link, then log in.'
                ctx['mode']='login'
            except sb.SupabaseError as e:
                ctx['error']=e.message
    return render(request,'learning/auth.html',ctx)
@require_http_methods(['POST'])
def logout_view(request):
    sb.sign_out(request.session.get('sb_access'))
    request.session.flush()
    return redirect('/')
@sb_login_required
@require_http_methods(['GET','POST'])
def account(request):
    uid=request.session['sb_user_id']
    def call(fn,*a,**kw):
        try:
            return fn(uid,request.session['sb_access'],*a,**kw)
        except sb.SupabaseError as e:
            if e.status not in (401,403): raise
            data=sb.refresh(request.session.get('sb_refresh',''))
            request.session['sb_access']=data['access_token']
            request.session['sb_refresh']=data.get('refresh_token',request.session.get('sb_refresh',''))
            return fn(uid,request.session['sb_access'],*a,**kw)
    ctx={}
    try:
        if request.method=='POST':
            call(sb.update_profile,full_name=request.POST.get('full_name','').strip() or None,phone=request.POST.get('phone','').strip() or None)
            ctx['notice']='Profile saved.'
        profile=call(sb.get_profile)
    except sb.SupabaseError:
        request.session.flush()
        return redirect('/login/')
    request.session['sb_plan']=(profile or {}).get('plan','free')
    ctx['profile']=profile or {}
    return render(request,'learning/account.html',ctx)
