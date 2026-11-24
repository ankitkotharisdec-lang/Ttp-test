const $=s=>document.querySelector(s);
let data,section=0,mode='map',requestId=0;
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
async function read(url){const r=await fetch(url,{credentials:'same-origin'});if(!r.ok)throw Error('Request failed');return r.json()}
const done=c=>c.lessons_done||0,started=c=>c.lessons_started||0;
const pct=c=>c.lesson_count?Math.round(100*done(c)/c.lesson_count):0;
const plural=(n,w)=>`${n} ${w}${n===1?'':'s'}`;
const allChapters=()=>data.sections.flatMap(s=>s.chapters);
const state=c=>pct(c)===100&&c.lesson_count?'complete':(done(c)||started(c))?'mid':'none';
const badge=c=>({complete:'<i class="st ok" title="Complete">✓</i>',mid:'<i class="st mid" title="In progress">!</i>',none:'<i class="st none" title="Not started">✓</i>'}[state(c)]);
async function load(){$('#retry').hidden=true;try{data=await read($('main').dataset.outlineUrl);section=0;render()}catch(e){$('#count').textContent='Could not load chapters';$('#retry').hidden=false}}
function renderChips(){
  const me=data.me;
  if(!me){$('#chips').innerHTML=`<span class="chip"><a href="/login/?next=/">Log in</a> or <a href="/signup/">sign up</a> to save your progress</span>`;return}
  const g=Math.min(100,Math.round(100*me.today_done/me.daily_goal));
  $('#chips').innerHTML=`<span class="chip">Overall Mastery: <b>${me.lessons_done} / ${me.lessons_total} lessons read</b></span><span class="chip" title="Days in a row with a completed lesson">🔥 <b>${me.streak}</b> day streak</span><span class="chip">⚡ <b>${me.xp}</b> XP</span><span class="chip goal" title="${me.goal_met?'Daily goal complete':'Finish '+(me.daily_goal-me.today_done)+' more lesson(s) today'}">Today <b>${Math.min(me.today_done,me.daily_goal)}/${me.daily_goal}</b><span class="bar ${me.goal_met?'done':''}"><i style="width:${g}%"></i></span></span>`}
function lastReadChapterId(){return data.me&&data.me.last_read?data.me.last_read.chapter_id:null}
function renderResume(){
  const me=data.me,btn=$('#resume-btn'),all=allChapters();
  if(me&&me.last_read){const l=me.last_read;$('#resume-label').textContent='LAST READ:';$('#resume-text').innerHTML=`${esc(l.lesson_title)}<br><small>${esc(l.chapter_title)} · ${l.status==='completed'?'completed':'in progress'}</small>`;btn.textContent=l.status==='completed'?'Review lesson':'Read lesson';btn.href=l.url;btn.removeAttribute('data-id');return}
  const first=all.find(c=>pct(c)<100)||all[0];
  $('#resume-label').textContent='UP NEXT:';$('#resume-text').textContent=first?first.title:'No chapters published yet';btn.textContent='Open chapter';btn.href='#';btn.dataset.id=first?first.id:''}
function node(c,i,x,y,cls,lw,cur){const p=pct(c),n=allChapters().indexOf(c)+1;
  return `<button class="node ${state(c)==='complete'?'complete':''} ${cur?'current':''}" data-id="${c.id}" style="left:${x}px;top:${y}px;--p:${p};--lw:${lw}px" aria-label="${esc(c.title)}, ${done(c)} of ${c.lesson_count} lessons read"><span class="n">${n}</span>${badge(c)}<span class="label ${cls}">${esc(c.title)}<small>${done(c)} / ${c.lesson_count} lessons read</small><span class="bar sm" aria-hidden="true"><i style="width:${p}%"></i></span></span></button>`}
const TROPHY='<svg width="54" height="54" viewBox="0 0 54 54" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M17 8h20v12a10 10 0 0 1-20 0V8z"/><path d="M17 12H9v4a8 8 0 0 0 8 8M37 12h8v4a8 8 0 0 1-8 8"/><path d="M27 30v8M19 46h16M22 38h10v8H22z"/><path d="M27 13l1.8 3.7 4 .6-2.9 2.8.7 4-3.6-1.9-3.6 1.9.7-4-2.9-2.8 4-.6z" fill="currentColor" stroke="none"/></svg>';
function snake(chapters){
  const W=Math.max(300,$('#content').clientWidth),cur=lastReadChapterId();
  const k=W>=900?3:1,top=k===1?60:130;let html='',path='',h;
  if(k===1){
    const rowH=W<500?150:176,R=Math.min(46,rowH/2-34),xL=Math.max(48,Math.round(W*(W<500?.13:.13))),xR=W-xL,lw=Math.max(110,Math.min(W<500?W-2*xL-30:330,xR-xL-80));
    const pos=chapters.map((c,i)=>({x:i%2?xR:xL,y:top+i*rowH}));
    pos.forEach((p,i)=>{html+=node(chapters[i],i,p.x,p.y,i%2?'l':'r',lw,chapters[i].id===cur)});
    const r=33;
    pos.slice(0,-1).forEach((p,i)=>{const q=pos[i+1],mid=p.y+rowH/2;
      path+=i%2===0?`M ${p.x} ${p.y+r+3} V ${mid-R} A ${R} ${R} 0 0 0 ${p.x+R} ${mid} H ${q.x-R} A ${R} ${R} 0 0 1 ${q.x} ${mid+R} V ${q.y-r-3} `
                   :`M ${p.x} ${p.y+r+3} V ${mid-R} A ${R} ${R} 0 0 1 ${p.x-R} ${mid} H ${q.x+R} A ${R} ${R} 0 0 0 ${q.x} ${mid+R} V ${q.y-r-3} `});
    const last=pos.at(-1),fy=last.y+rowH*0.78;
    path+=`M ${last.x} ${last.y+r+3} V ${fy-16}`;
    html+=`<div class="finish" style="left:${last.x}px;top:${fy+18}px">${TROPHY}</div>`;
    h=fy+90;
  }else{
    const rowHeight=274, radius=104, left=W*.225, right=W*.775;
    const slots=[[left,0,'l'],[W*.475,0,'t'],[right,rowHeight/2,'r'],
                 [W*.635,rowHeight,'t'],[W*.36,rowHeight,'t'],[left,rowHeight*1.5,'l']];
    const points=chapters.map((chapter,i)=>{
      const [x,offset,label]=slots[i%slots.length];
      const y=top+offset+Math.floor(i/slots.length)*2*rowHeight;
      html+=node(chapter,i,x,y,label,label==='t'?W*.22:W*.17,chapter.id===cur);
      return {x,y};
    });
    path=`M ${left} ${top}`;
    points.slice(1).forEach((point,index)=>{
      const {x,y}=point, prior=points[index], slot=(index+1)%6;
      if(slot===2)path+=` H ${right-radius} Q ${right} ${prior.y} ${right} ${prior.y+radius} V ${y}`;
      else if(slot===3)path+=` V ${y-radius} Q ${right} ${y} ${right-radius} ${y} H ${x}`;
      else if(slot===5)path+=` H ${left+radius} Q ${left} ${prior.y} ${left} ${prior.y+radius} V ${y}`;
      else if(slot===0)path+=` V ${y}`;
      else path+=` H ${x}`;
    });
    h=points.at(-1).y+105;
  }
  return `<div class="roadmap" style="height:${h}px"><svg width="${W}" height="${h}" viewBox="0 0 ${W} ${h}" aria-hidden="true"><path d="${path}" stroke="#cfe3f0" stroke-width="2" fill="none" stroke-linecap="round"/></svg>${html}</div>`}
function render(){
  if(!data)return;renderChips();renderResume();
  const showSections = data.slug !== 'python';
  const tabs = $('#tabs');
  tabs.hidden = !showSections;
  if (showSections) {
    tabs.innerHTML = data.sections.map((s, i) => `<button data-section="${i}" class="${i === section ? 'active' : ''}" aria-pressed="${i === section}">${esc(s.title)}</button>`).join('');
  }
  const selectedSection = data.sections[section];
  const availableChapters = showSections ? selectedSection?.chapters || [] : allChapters();
  const sectionTitle = showSections ? selectedSection?.title : data.title;
  $('#section-title').textContent = sectionTitle || 'No published sections yet';
  const query = $('#search').value.trim().toLowerCase();
  const chapters = availableChapters.filter(chapter => chapter.title.toLowerCase().includes(query));
  const d=chapters.reduce((n,c)=>n+done(c),0),t=chapters.reduce((n,c)=>n+c.lesson_count,0);
  $('#count').textContent=`${sectionTitle ? sectionTitle + ' · ' : ''}${plural(chapters.length,'chapter')} · ${d} of ${t} lessons covered`;
  $('#map').setAttribute('aria-pressed',mode==='map');$('#list').setAttribute('aria-pressed',mode==='list');
  if(!chapters.length){$('#content').textContent='No published chapters match this view.';return}
  if(mode==='list'||query){$('#content').innerHTML=chapters.map(c=>`<button class="row" data-id="${c.id}"><b class="num ${state(c)==='complete'?'ok':''}">${state(c)==='complete'?'✓':allChapters().indexOf(c)+1}</b><span class="rt"><span>${esc(c.title)}</span><span class="bar sm"><i style="width:${pct(c)}%"></i></span></span><small>${done(c)} / ${c.lesson_count} lessons read</small></button>`).join('');return}
  $('#content').innerHTML=snake(chapters)}
$('#tabs').onclick=e=>{const b=e.target.closest('[data-section]');if(b){section=Number(b.dataset.section);$('#search').value='';render()}};
$('#map').onclick=()=>{mode='map';render()};$('#list').onclick=()=>{mode='list';render()};$('#search').oninput=render;$('#retry').onclick=load;
$('#resume-btn').onclick=e=>{const b=e.currentTarget;if(b.getAttribute('href')==='#'){e.preventDefault();if(b.dataset.id)openChapter(b.dataset.id)}};
async function openChapter(chapterId){
  const id=++requestId,ch=allChapters().find(c=>c.id===chapterId),no=allChapters().indexOf(ch)+1;
  $('#dnode').innerHTML=`${no}${ch?badge(ch):''}`;$('#dnode').style.borderColor=ch&&state(ch)==='complete'?'var(--ok)':'';
  $('#dialog-title').textContent=ch?ch.title:'Loading lessons…';$('#dialog-sub').textContent=ch?`${done(ch)} / ${ch.lesson_count} lessons read`:'';$('#dnode').style.setProperty('--filled', '0%');$('#lesson-list').textContent='';$('#chapter-dialog').showModal();
  try{const c=await read(`/api/chapters/${chapterId}/lessons/`);if(id!==requestId)return;
    $('#dialog-title').textContent=c.title;
    const dn=c.lessons.filter(l=>l.status==='completed').length;$('#dialog-sub').textContent=`${dn} / ${c.lessons.length} lessons read`;
    $('#dnode').style.setProperty('--filled', (c.lessons.length ? 100*dn/c.lessons.length : 0)+'%');
    $('#lesson-list').innerHTML=c.lessons.length?c.lessons.map((l,i)=>{const prev=c.lessons[i-1]&&c.lessons[i-1].status==='completed';
      return `<a href="${l.url}" class="lrow ${l.status} ${prev?'prev-done':''}"><span class="tm"><span class="dot" title="${l.status==='completed'?'Complete':l.status==='in_progress'?'In progress':'Not started'}">${l.status==='completed'?'✓':l.status==='in_progress'?'!':''}</span></span><span class="lt"><b>${no}.${i+1}</b>${esc(l.title)}</span></a>`}).join(''):'<p class="dsum">No published lessons yet.</p>'}
  catch(e){if(id===requestId)$('#dialog-title').textContent='Could not load lessons. Close and try again.'}}
$('#content').onclick=e=>{const b=e.target.closest('[data-id]');if(b)openChapter(b.dataset.id)};
$('#close').onclick=()=>$('#chapter-dialog').close();
$('#chapter-dialog').addEventListener('click',e=>{if(e.target===e.currentTarget)e.currentTarget.close()});
let timer;window.addEventListener('resize',()=>{clearTimeout(timer);timer=setTimeout(render,120)});load();
