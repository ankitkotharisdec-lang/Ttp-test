(()=>{
const lp=document.querySelector('.lp');
const bar=document.getElementById('readbar');
const upd=()=>{const h=document.documentElement;const m=h.scrollHeight-h.clientHeight;bar.style.width=(m>0?Math.min(100,100*h.scrollTop/m):100)+'%'};
addEventListener('scroll',upd,{passive:true});upd();
document.querySelectorAll('.copy').forEach(b=>b.onclick=async()=>{try{await navigator.clipboard.writeText(b.nextElementSibling.innerText);b.textContent='Copied';setTimeout(()=>b.textContent='Copy',1500)}catch(e){b.textContent='Press Ctrl+C'}});
// interactive examples: pick an option, then confirm
document.querySelectorAll('.blk-ex').forEach(ex=>{
  const right=Number(ex.dataset.correct),box=ex.querySelector('.explain'),opts=[...ex.querySelectorAll('.opt')],ok=ex.querySelector('.confirm'),again=ex.querySelector('.again');
  let sel=0,locked=false;
  const reset=()=>{sel=0;locked=false;opts.forEach(o=>{o.disabled=false;o.className='opt';o.setAttribute('aria-checked','false')});if(ok)ok.disabled=true;box.hidden=true};
  opts.forEach(o=>o.onclick=()=>{if(locked)return;opts.forEach(x=>{x.classList.remove('sel','wrong');x.setAttribute('aria-checked','false')});sel=Number(o.dataset.n);o.classList.add('sel');o.setAttribute('aria-checked','true');ok.disabled=false;box.hidden=true});
  if(ok)ok.onclick=()=>{if(!sel)return;const o=opts[sel-1];
    if(sel===right){locked=true;opts.forEach(x=>x.disabled=true);o.className='opt right';box.className='explain';box.textContent='Correct! '+box.dataset.text;ok.disabled=true}
    else{o.className='opt wrong';box.className='explain no';box.textContent='Not quite. Pick another option and confirm again.';ok.disabled=true;sel=0}
    box.hidden=false};
  if(again)again.onclick=reset;
  if(!opts.length){box.textContent=box.dataset.text;box.hidden=!box.dataset.text}
});
const done=document.getElementById('done');if(!done)return;
let rating=0;
const post=async data=>{const r=await fetch(lp.dataset.completeUrl,{method:'POST',credentials:'same-origin',headers:{'X-CSRFToken':lp.dataset.csrf,'Content-Type':'application/x-www-form-urlencoded'},body:new URLSearchParams(data)});if(r.status===401){location.href='/login/?next='+encodeURIComponent(location.pathname);return null}if(!r.ok)throw Error();return r.json()};
const rate=document.getElementById('rate');
rate.onclick=async e=>{const b=e.target.closest('[data-r]');if(!b)return;rating=Number(b.dataset.r);rate.querySelectorAll('.face').forEach(f=>f.classList.toggle('on',f===b));if(lp.dataset.status==='completed'){try{await post({rating})}catch(_){}}};
done.onclick=async()=>{
  done.disabled=true;done.textContent='Saving…';
  try{
    const d=await post(rating?{rating}:{});if(!d)return;
    if(lp.dataset.status!=='completed'){
      const chapter=document.getElementById('chapter-meter');
      chapter.value=Math.min(chapter.max,chapter.value+1);
      document.getElementById('read-count').textContent=chapter.value;
      document.getElementById('chapter-value').textContent=Math.round(100*chapter.value/chapter.max)+'%';
    }
    done.hidden=true;lp.dataset.status='completed';
    document.getElementById('fh').textContent=d.xp_gained?'Lesson complete! 🎉':'Already complete';
    document.getElementById('fp').textContent='';
    const s=d.stats,cel=document.getElementById('cel');
    document.getElementById('xpg').textContent=d.xp_gained?`+${d.xp_gained} XP`:'No new XP';
    document.getElementById('celmsg').textContent=(s.goal_met?`Daily goal reached (${s.today_done}/${s.daily_goal}). `:`${s.today_done}/${s.daily_goal} lessons today. `)+`🔥 ${s.streak}-day streak · ⚡ ${s.xp} XP total.`;
    cel.classList.add('show');
    const pill=document.getElementById('statuspill');if(pill){pill.className='pill ok';pill.textContent='✓ Completed'}
    const dc=document.getElementById('donecount');if(dc&&d.xp_gained){const [a,b]=dc.textContent.split('/').map(Number);dc.textContent=(a+1)+'/'+b;
      const meter=document.getElementById('course-progress');
      if(meter){meter.value=a+1;document.getElementById('course-percent').textContent=Math.round(100*meter.value/meter.max)+'%'}}
  }catch(e){done.disabled=false;done.textContent='Mark complete';document.getElementById('fp').textContent='Could not save. Check your connection and try again.'}
};
})();
