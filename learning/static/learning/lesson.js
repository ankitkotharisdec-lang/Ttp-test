(()=>{
const lp=document.querySelector('.lp');
// reading progress bar
const bar=document.getElementById('readbar');
const upd=()=>{const h=document.documentElement;const m=h.scrollHeight-h.clientHeight;bar.style.width=(m>0?Math.min(100,100*h.scrollTop/m):100)+'%'};
addEventListener('scroll',upd,{passive:true});upd();
// copy buttons
document.querySelectorAll('.copy').forEach(b=>b.onclick=async()=>{try{await navigator.clipboard.writeText(b.nextElementSibling.innerText);b.textContent='Copied';setTimeout(()=>b.textContent='Copy',1500)}catch(e){b.textContent='Press Ctrl+C'}});
// interactive examples
document.querySelectorAll('.blk-ex').forEach(ex=>{
  const right=Number(ex.dataset.correct),box=ex.querySelector('.explain'),opts=[...ex.querySelectorAll('.opt')];
  opts.forEach(o=>o.onclick=()=>{
    const n=Number(o.dataset.n);
    if(n===right){opts.forEach(x=>x.disabled=true);o.classList.add('right');box.className='explain';box.textContent='Correct! '+box.dataset.text}
    else{o.classList.add('wrong');o.disabled=true;box.className='explain no';box.textContent='Not quite. Try another option.'}
    box.hidden=false;
  });
  if(!right){box.textContent=box.dataset.text;box.hidden=!box.dataset.text}
});
// complete + rate
const done=document.getElementById('done');if(!done)return;
let rating=0;
const post=async data=>{const r=await fetch(lp.dataset.completeUrl,{method:'POST',credentials:'same-origin',headers:{'X-CSRFToken':lp.dataset.csrf,'Content-Type':'application/x-www-form-urlencoded'},body:new URLSearchParams(data)});if(r.status===401){location.href='/login/?next='+encodeURIComponent(location.pathname);return null}if(!r.ok)throw Error();return r.json()};
const rate=document.getElementById('rate');
const paint=()=>rate.querySelectorAll('button').forEach(b=>b.classList.toggle('on',Number(b.dataset.r)<=rating));
rate.onclick=async e=>{const b=e.target.closest('[data-r]');if(!b)return;rating=Number(b.dataset.r);paint();if(lp.dataset.status==='completed'||done.hidden){try{await post({rating})}catch(_){}}};
done.onclick=async()=>{
  done.disabled=true;done.textContent='Saving…';
  try{
    const d=await post(rating?{rating}:{});if(!d)return;
    done.hidden=true;lp.dataset.status='completed';
    document.getElementById('fh').textContent=d.xp_gained?'Lesson complete! 🎉':'Already complete';
    document.getElementById('fp').textContent='';
    const s=d.stats,cel=document.getElementById('cel');
    document.getElementById('xpg').textContent=d.xp_gained?`+${d.xp_gained} XP`:'No new XP';
    document.getElementById('celmsg').textContent=(s.goal_met?`Daily goal reached (${s.today_done}/${s.daily_goal}). `:`${s.today_done}/${s.daily_goal} lessons today. `)+`🔥 ${s.streak}-day streak · ⚡ ${s.xp} XP total.`;
    cel.classList.add('show');
    const pill=document.getElementById('statuspill');if(pill){pill.className='pill ok';pill.textContent='✓ Completed'}
    const nx=document.getElementById('nextlink');if(nx)nx.classList.add('hl');
  }catch(e){done.disabled=false;done.textContent='MARK COMPLETE';document.getElementById('fp').textContent='Could not save. Check your connection and try again.'}
};
})();
