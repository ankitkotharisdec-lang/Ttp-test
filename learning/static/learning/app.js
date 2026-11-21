const $=s=>document.querySelector(s);
let data,section=0,mode='map',requestId=0;
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
async function read(url){const r=await fetch(url,{credentials:'same-origin'});if(!r.ok)throw Error('Request failed');return r.json()}
const pct=c=>c.lesson_count?Math.round(100*(c.lessons_done||0)/c.lesson_count):0;
const plural=(n,w)=>`${n} ${w}${n===1?'':'s'}`;
async function load(){$('#retry').hidden=true;try{data=await read($('main').dataset.outlineUrl);section=0;render()}catch(e){$('#section-title').textContent='Could not load chapters';$('#retry').hidden=false}}
function renderStats(){
  const box=$('#stats'),me=data.me;
  if(!me){box.hidden=false;box.innerHTML=`<p class="stat-login"><b>Track your progress.</b> <a href="/login/?next=/">Log in</a> or <a href="/signup/">create a free account</a> to save lessons, build streaks and earn XP.</p>`;return}
  const g=Math.min(100,Math.round(100*me.today_done/me.daily_goal));
  box.hidden=false;
  box.innerHTML=`<div class="stat"><span class="ico" aria-hidden="true">🔥</span><b>${me.streak}</b><small>day streak</small></div>
  <div class="stat"><span class="ico" aria-hidden="true">⚡</span><b>${me.xp}</b><small>XP earned</small></div>
  <div class="stat goal"><div class="goal-top"><small>Today's goal</small><b>${Math.min(me.today_done,me.daily_goal)}/${me.daily_goal} lessons</b></div><div class="bar ${me.goal_met?'done':''}" role="progressbar" aria-valuenow="${g}" aria-valuemin="0" aria-valuemax="100"><i style="width:${g}%"></i></div><small>${me.goal_met?'Goal complete. Great work!':'Finish '+(me.daily_goal-me.today_done)+' more to keep your streak alive.'}</small></div>
  <div class="stat"><span class="ico" aria-hidden="true">🎯</span><b>${me.mastery}%</b><small>${me.lessons_done}/${me.lessons_total} lessons</small></div>`}
function renderResume(){
  const me=data.me,btn=$('#resume-btn'),all=data.sections.flatMap(x=>x.chapters);
  if(me&&me.last_read){const l=me.last_read;$('#resume-label').textContent='LAST READ';$('#resume-text').innerHTML=`${esc(l.chapter_title)}<br><small>${esc(l.lesson_title)}${l.status==='completed'?' · completed':' · in progress'}</small>`;btn.textContent=l.status==='completed'?'REVIEW LESSON':'CONTINUE';btn.href=l.url;return}
  const first=all.find(c=>!c.lessons_done)||all[0];
  $('#resume-label').textContent='UP NEXT';$('#resume-text').textContent=first?first.title:'No chapters published yet';btn.textContent='OPEN CHAPTER';btn.href='#';btn.dataset.id=first?first.id:''}
function ringNode(c,i,pos){const p=pct(c),done=p===100;return `<button class="node ${done?'complete':''} ${c.lessons_done||c.lessons_started?'started':''}" data-id="${c.id}" style="left:${pos.x}%;top:${pos.y}px;--p:${p}" aria-label="${esc(c.title)}, ${c.lessons_done||0} of ${c.lesson_count} lessons done"><span>${done?'✓':i+1}</span><span class="label">${esc(c.title)}<small>${c.lessons_done!==undefined?`${c.lessons_done} of ${c.lesson_count} lessons`:plural(c.lesson_count,'lesson')}</small></span></button>`}
function render(){
  if(!data)return;renderStats();renderResume();
  $('#tabs').innerHTML=data.sections.map((s,i)=>{const t=s.chapters.reduce((n,c)=>n+c.lesson_count,0),d=s.chapters.reduce((n,c)=>n+(c.lessons_done||0),0);return `<button data-section="${i}" class="${i===section?'active':''}" aria-pressed="${i===section}">${esc(s.title)}${data.logged_in?`<em>${d}/${t}</em>`:''}</button>`}).join('');
  const s=data.sections[section];$('#section-title').textContent=s?s.title:'No published sections yet';
  const q=$('#search').value.toLowerCase(),chapters=(s?.chapters||[]).filter(c=>c.title.toLowerCase().includes(q));
  const done=chapters.reduce((n,c)=>n+(c.lessons_done||0),0),total=chapters.reduce((n,c)=>n+c.lesson_count,0);
  $('#count').textContent=`${plural(chapters.length,'chapter')} · ${data.logged_in?`${done} of ${total} lessons covered`:plural(total,'lesson')}`;
  $('#map').setAttribute('aria-pressed',mode==='map');$('#list').setAttribute('aria-pressed',mode==='list');
  if(!chapters.length){$('#content').textContent='No published chapters match this view.';return}
  if(mode==='list'||q){$('#content').innerHTML=chapters.map((c,i)=>`<button class="row" data-id="${c.id}"><b class="num ${pct(c)===100?'ok':''}">${pct(c)===100?'✓':i+1}</b><span class="rt"><span>${esc(c.title)}</span>${data.logged_in?`<span class="bar sm"><i style="width:${pct(c)}%"></i></span>`:''}</span><small>${data.logged_in?`${c.lessons_done} / ${c.lesson_count} lessons`:plural(c.lesson_count,'lesson')}</small></button>`).join('');return}
  const mobile=innerWidth<=600,step=mobile?150:240,top=mobile?75:185,pos=chapters.map((c,i)=>({x:mobile?16:[28,72,72,28][i%4],y:top+(mobile?i:Math.floor(i/2))*step}));
  let path=`M ${pos[0].x*10} ${pos[0].y}`;pos.slice(1).forEach((p,i)=>{const prev=pos[i];path+=p.y===prev.y?` L ${p.x*10} ${p.y}`:` C ${prev.x*10+(mobile?0:prev.x>50?170:-170)} ${prev.y} ${p.x*10+(mobile?0:p.x>50?170:-170)} ${p.y} ${p.x*10} ${p.y}`});
  const height=pos.at(-1).y+170;
  $('#content').innerHTML=`<div class="roadmap" style="height:${height}px"><svg viewBox="0 0 1000 ${height}" preserveAspectRatio="none" aria-hidden="true"><path d="${path}" stroke="#c7dae3" stroke-width="2" fill="none"/></svg>${chapters.map((c,i)=>ringNode(c,i,pos[i])).join('')}<div class="finish">Your next step starts here.</div></div>`}
$('#tabs').onclick=e=>{const b=e.target.closest('[data-section]');if(b){section=Number(b.dataset.section);$('#search').value='';render()}};
$('#map').onclick=()=>{mode='map';render()};$('#list').onclick=()=>{mode='list';render()};$('#search').oninput=render;$('#retry').onclick=load;
$('#resume-btn').onclick=e=>{const b=e.currentTarget;if(b.getAttribute('href')==='#'){e.preventDefault();if(b.dataset.id)openChapter(b.dataset.id)}};
const ICON={completed:'<span class="st ok" title="Completed">✓</span>',in_progress:'<span class="st mid" title="In progress">●</span>',new:'<span class="st" title="Not started">○</span>'};
async function openChapter(chapterId){const id=++requestId;$('#dialog-title').textContent='Loading lessons…';$('#lesson-list').textContent='';$('#chapter-dialog').showModal();
  try{const c=await read(`/api/chapters/${chapterId}/lessons/`);if(id!==requestId)return;$('#dialog-title').textContent=c.title;
    const done=c.lessons.filter(l=>l.status==='completed').length;
    $('#lesson-list').innerHTML=c.lessons.length?(data.logged_in?`<p class="dlg-sum">${done} of ${c.lessons.length} lessons complete</p><div class="bar"><i style="width:${Math.round(100*done/c.lessons.length)}%"></i></div>`:'')+c.lessons.map((l,i)=>`<a href="${l.url}" class="lrow ${l.status}">${ICON[l.status]||ICON.new}<span>${i+1}. ${esc(l.title)}</span><em>${l.status==='completed'?'Complete':l.status==='in_progress'?'In progress':''}</em></a>`).join(''):'No published lessons yet.'}
  catch(e){if(id===requestId)$('#dialog-title').textContent='Could not load lessons. Close and try again.'}}
$('#content').onclick=e=>{const b=e.target.closest('[data-id]');if(b)openChapter(b.dataset.id)};
$('#close').onclick=()=>$('#chapter-dialog').close();
let timer;window.addEventListener('resize',()=>{clearTimeout(timer);timer=setTimeout(render,100)});load();
