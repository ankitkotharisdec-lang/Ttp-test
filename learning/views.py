from django.db.models import Count,Prefetch,Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404,render
from django.views.decorators.http import require_GET
from functools import wraps
from django.shortcuts import redirect
from django.views.decorators.http import require_http_methods
from django.utils.http import url_has_allowed_host_and_scheme
from . import supabase_auth as sb
from . import progress
from .models import Course,Section,Chapter,Lesson,LessonBlock,LessonProgress
@require_GET
def roadmap(request,slug='python'):
    course=get_object_or_404(Course,slug=slug,is_published=True)
    return render(request,'learning/roadmap.html',{'course':course})
def _uid(request):
    return request.session.get('sb_user_id')
@require_GET
def outline(request,slug):
    chapters=Chapter.objects.filter(is_published=True).annotate(lesson_count=Count('lessons',filter=Q(lessons__is_published=True))).order_by('position','id')
    sections=Section.objects.filter(is_published=True).prefetch_related(Prefetch('chapters',queryset=chapters,to_attr='published_chapters'))
    course=get_object_or_404(Course.objects.prefetch_related(Prefetch('sections',queryset=sections,to_attr='published_sections')),slug=slug,is_published=True)
    uid=_uid(request)
    done={};started={}
    if uid:
        rows=LessonProgress.objects.filter(user_id=uid,lesson__is_published=True).values('lesson__chapter_id','status')
        for r in rows:
            d=done if r['status']=='completed' else started
            d[r['lesson__chapter_id']]=d.get(r['lesson__chapter_id'],0)+1
    def chap(c):
        row={'id':str(c.id),'title':c.title,'position':c.position,'lesson_count':c.lesson_count}
        if uid: row.update(lessons_done=done.get(c.id,0),lessons_started=started.get(c.id,0))
        return row
    data={'id':str(course.id),'title':course.title,'slug':course.slug,'sections':[{'id':str(s.id),'title':s.title,'position':s.position,'chapters':[chap(c) for c in s.published_chapters]} for s in course.published_sections],'logged_in':bool(uid)}
    if uid:
        total=sum(c['lesson_count'] for s in data['sections'] for c in s['chapters'])
        got=sum(c['lessons_done'] for s in data['sections'] for c in s['chapters'])
        data['me']=dict(progress.stats(uid),last_read=progress.last_read(uid),lessons_total=total,lessons_done=got,mastery=round(100*got/total) if total else 0,plan=request.session.get('sb_plan','free'))
    return JsonResponse(data)
@require_GET
def chapter_lessons(request,chapter_id):
    chapter=get_object_or_404(Chapter,id=chapter_id,is_published=True,section__is_published=True,section__course__is_published=True)
    smap=progress.status_map(_uid(request)) if _uid(request) else {}
    rows=[{'id':l['id'],'title':l['title'],'position':l['position'],'status':smap.get(l['id'],'new') if smap or _uid(request) else 'new'} for l in chapter.lessons.filter(is_published=True).values('id','title','position')]
    for r in rows: r['id']=str(r['id']);r['url']=f"/lessons/{r['id']}/"
    return JsonResponse({'id':str(chapter.id),'title':chapter.title,'lessons':rows})
def _published_lesson(request,lesson_id):
    qs=Lesson.objects.select_related('chapter__section__course')
    if request.user.is_authenticated and request.user.is_staff:
        return get_object_or_404(qs,id=lesson_id),True  # staff can preview drafts
    return get_object_or_404(qs,id=lesson_id,is_published=True,chapter__is_published=True,chapter__section__is_published=True,chapter__section__course__is_published=True),False
@require_GET
def lesson_detail(request,lesson_id):
    lesson,preview=_published_lesson(request,lesson_id)
    uid=_uid(request)
    status='new'
    if uid and not preview:
        status=progress.mark_started(uid,lesson).status
    blocks=lesson.blocks.all() if preview else lesson.blocks.filter(is_published=True)
    order=progress.ordered_lessons(lesson.chapter.section.course)
    ids=[l.id for l in order]
    i=ids.index(lesson.id) if lesson.id in ids else -1
    chap_ids=[]
    for l in order:
        if l.chapter_id not in chap_ids: chap_ids.append(l.chapter_id)
    chapter_no=chap_ids.index(lesson.chapter_id)+1 if lesson.chapter_id in chap_ids else lesson.chapter.position
    lesson_no=sum(1 for l in order[:max(i,0)] if l.chapter_id==lesson.chapter_id)+1 if i>=0 else lesson.position
    statuses = progress.status_map(uid) if uid else {}
    done_total = sum(statuses.get(item.id) == 'completed' for item in order)
    chapter_lessons = [item for item in order if item.chapter_id == lesson.chapter_id]
    ctx={'lesson':lesson,'blocks':list(blocks),'preview':preview,'status':status,'logged_in':bool(uid),
         'prev':order[i-1] if i>0 else None,'next':order[i+1] if 0<=i<len(order)-1 else None,
         'position':i+1 if i>=0 else None,'total':len(order),'me':progress.stats(uid) if uid else None,
         'chapter_no':chapter_no,'lesson_no':lesson_no,'done_total':done_total,
         'chapter_lessons':chapter_lessons,
         'chapter_done':sum(statuses.get(item.id) == 'completed' for item in chapter_lessons),
         'faces':[(1,'😞','Very unhelpful'),(2,'😕','Unhelpful'),(3,'😐','Neutral'),(4,'🙂','Helpful'),(5,'😄','Very helpful')]}
    return render(request,'learning/lesson.html',ctx)
@require_http_methods(['POST'])
def complete_lesson(request,lesson_id):
    uid=_uid(request)
    if not uid: return JsonResponse({'error':'login_required'},status=401)
    lesson,preview=_published_lesson(request,lesson_id)
    if preview: return JsonResponse({'error':'preview'},status=400)
    try: rating=int(request.POST.get('rating',''))
    except ValueError: rating=None
    _,xp=progress.mark_completed(uid,lesson,rating)
    order=progress.ordered_lessons(lesson.chapter.section.course)
    ids=[l.id for l in order];i=ids.index(lesson.id) if lesson.id in ids else -1
    nxt=order[i+1] if 0<=i<len(order)-1 else None
    return JsonResponse({'xp_gained':xp,'stats':progress.stats(uid),'next_url':nxt.get_absolute_url() if nxt else None,'next_title':nxt.title if nxt else None})

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

@require_GET
def google_start(request):
    verifier,challenge=sb.new_pkce()
    request.session['sb_pkce']=verifier
    request.session['sb_next']=_safe_next(request)
    try:
        url=sb.google_authorize_url(request.build_absolute_uri('/auth/callback/'),challenge)
    except sb.SupabaseError as e:
        return render(request,'learning/auth.html',{'mode':'login','error':e.message})
    return redirect(url)
@require_GET
def auth_callback(request):
    verifier=request.session.pop('sb_pkce',None)
    nxt=request.session.pop('sb_next','/account/')
    code=request.GET.get('code')
    if not code or not verifier:
        msg=request.GET.get('error_description') or 'Google sign-in did not complete. Please try again.'
        return render(request,'learning/auth.html',{'mode':'login','error':msg})
    try:
        data=sb.exchange_code(code,verifier)
        try: profile=sb.get_profile(data['user']['id'],data['access_token'])
        except sb.SupabaseError: profile=None
    except sb.SupabaseError as e:
        return render(request,'learning/auth.html',{'mode':'login','error':e.message})
    _start_session(request,data,profile)
    return redirect(nxt if url_has_allowed_host_and_scheme(nxt,allowed_hosts={request.get_host()}) else '/account/')
