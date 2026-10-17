(() => {
const D = window.ATT, P = 'Present', A = 'Absent', V = 'Pending Verification';
const CSRF = document.querySelector('meta[name=csrf]').content;
const $ = id => document.getElementById(id);
const R = D.roster, byId = {}, rows = {}, retry = [];
R.forEach(s => byId[s.id] = s);
const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
const post = (url, body) => fetch(url, {method: 'POST', keepalive: true,
  headers: {'Content-Type': 'application/json', 'X-CSRFToken': CSRF}, body: JSON.stringify(body)});
const msg = t => $('msg').textContent = t;
const mic = (t, c) => { $('mic').textContent = t; $('mic').className = 'px-2 py-1 rounded text-sm ' + (c || 'bg-slate-200'); };
const COL = {[P]: 'text-green-700', [A]: 'text-red-700', [V]: 'text-amber-600'};

// ---------- table ----------
let sel = -1;
function rowHtml(s) {
  const b = (st, l, c) => `<button data-id="${s.id}" data-st="${st}" class="m px-2 py-1 rounded text-white ${c} ${s.status === st ? 'ring-2 ring-black' : ''}">${l}</button>`;
  return `<td class="p-2 font-mono">${s.roll}</td><td>${s.name}</td>
  <td class="font-semibold ${COL[s.status] || 'text-slate-400'}">${s.status || 'Not reviewed'}</td>
  <td class="space-x-1 whitespace-nowrap">${b(P, 'P', 'bg-green-600')}${b(A, 'A', 'bg-red-600')}${b(V, '?', 'bg-amber-500')}</td>`;
}
function build() {
  $('tb').innerHTML = '';
  R.forEach(s => { const tr = document.createElement('tr'); tr.className = 'border-t'; tr.tabIndex = 0;
    tr.innerHTML = rowHtml(s); tr.onclick = () => select(tr); $('tb').appendChild(tr); rows[s.id] = tr; });
  counts();
}
function upd(s) { const tr = rows[s.id]; tr.innerHTML = rowHtml(s);
  tr.className = 'border-t ' + (s.status ? '' : 'bg-yellow-50'); }
function counts() {
  const c = {[P]: 0, [A]: 0, [V]: 0, u: 0};
  R.forEach(s => s.status ? c[s.status]++ : c.u++);
  $('cP').textContent = c[P]; $('cA').textContent = c[A]; $('cV').textContent = c[V]; $('cU').textContent = c.u;
  return c;
}
function mark(s, status) {
  if (!D.canEdit) { msg('Session is locked for editing.'); return; }
  s.status = status; upd(s); counts();
  const body = {student_id: s.id, status};
  post(`/api/session/${D.sid}/mark`, body).then(r => { if (!r.ok) throw 0; }).catch(() => retry.push(body));
}
setInterval(() => { const b = retry.shift(); if (b) post(`/api/session/${D.sid}/mark`, b).then(r => { if (!r.ok) throw 0; }).catch(() => retry.push(b)); }, 3000);
$('tb').addEventListener('click', e => { const b = e.target.closest('.m'); if (b) mark(byId[b.dataset.id], b.dataset.st); });
function select(tr) { [...$('tb').children].forEach(t => t.classList.remove('outline')); tr.classList.add('outline'); sel = [...$('tb').children].indexOf(tr); }
$('q').oninput = e => { const q = e.target.value.toLowerCase();
  R.forEach(s => rows[s.id].style.display = (s.roll + ' ' + s.name).toLowerCase().includes(q) ? '' : 'none'); };
document.addEventListener('keydown', e => {
  if (e.target.tagName === 'INPUT') return;
  const vis = [...$('tb').children].filter(t => t.style.display !== 'none');
  if (e.key === 'ArrowDown' || e.key === 'ArrowUp') { e.preventDefault();
    const cur = vis.findIndex(t => t.classList.contains('outline'));
    const n = Math.max(0, Math.min(vis.length - 1, cur + (e.key === 'ArrowDown' ? 1 : -1)));
    if (vis[n]) { select(vis[n]); vis[n].scrollIntoView({block: 'nearest'}); } }
  const k = e.key.toLowerCase(), m = {p: P, a: A, v: V}[k];
  if (m && sel >= 0) mark(R[sel], m);
});
async function bulk(action, text) {
  if (!confirm(text)) return;
  const r = await post(`/api/session/${D.sid}/bulk`, {action});
  if (r.ok) location.reload(); else msg('Bulk action not allowed.');
}
$('bAll').onclick = () => bulk('all_present', 'Mark ALL students Present?');
$('bRest').onclick = () => bulk('rest_absent', 'Mark all unreviewed students Absent?');
document.querySelectorAll('.act').forEach(b => b.onclick = async () => {
  const action = b.dataset.act, body = {action};
  if (action === 'reopen') { const r = prompt('Reason for reopening (required):'); if (!r) return; body.reason = r; }
  if (action === 'finalize' && !confirm('Permanently finalize this attendance?')) return;
  const r = await post(`/api/session/${D.sid}/state`, body), j = await r.json().catch(() => ({}));
  if (!r.ok) { msg(j.error || 'Action not allowed.'); return; }
  msg('Done: ' + action); location.reload();
});

// ---------- voice helpers ----------
const ONES = {zero:0,oh:0,o:0,one:1,won:1,wan:1,two:2,to:2,too:2,tu:2,three:3,tree:3,four:4,for:4,fore:4,five:5,six:6,sex:6,seven:7,eight:8,ate:8,nine:9,nein:9,
  ten:10,eleven:11,twelve:12,thirteen:13,fourteen:14,fifteen:15,sixteen:16,seventeen:17,eighteen:18,nineteen:19};
const TENS = {twenty:20,thirty:30,forty:40,fifty:50,sixty:60,seventy:70,eighty:80,ninety:90};
function parse(t) {
  t = t.toLowerCase().replace(/[^a-z0-9 ]/g, ' ').replace(/\band\b/g, ' ').trim();
  if (/\d/.test(t)) return t.replace(/\D/g, '').replace(/^0+(?=\d)/, '');
  const w = t.split(/\s+/);
  if (w.includes('hundred')) { let n = 0;
    for (const x of w) { if (x === 'hundred') n = (n || 1) * 100; else if (x in TENS) n += TENS[x]; else if (x in ONES) n += ONES[x]; }
    return String(n); }
  let out = '';
  for (let i = 0; i < w.length; i++) {
    if (w[i] in TENS) { const nx = ONES[w[i + 1]]; if (nx > 0 && nx < 10) { out += TENS[w[i]] + nx; i++; } else out += TENS[w[i]]; }
    else if (w[i] in ONES) out += ONES[w[i]];
  }
  return out.replace(/^0+(?=\d)/, '');
}
const byRoll = {};
R.forEach(s => { const k = s.roll.replace(/\D/g, '').replace(/^0+(?=\d)/, ''); (byRoll[k] = byRoll[k] || []).push(s); });
let speaking = false;
const say = t => new Promise(r => { speaking = true; const u = new SpeechSynthesisUtterance(t);
  u.onend = u.onerror = () => { speaking = false; r(); }; speechSynthesis.speak(u); });
const noSR = () => { if (!SR) { mic('Voice unsupported – use Chrome/Edge or manual mode', 'bg-red-200'); return true; } };
function recog(cont, interim) { const r = new SR(); r.lang = 'en-IN'; r.continuous = cont; r.interimResults = !!interim; r.maxAlternatives = 5;
  r.onerror = e => { if (/not-allowed|service-not-allowed/.test(e.error)) { running = false; paused = true;
    mic('Microphone blocked – allow it in the address bar or use manual mode', 'bg-red-200'); } }; return r; }
let running = false, paused = false, rec = null, timer = null;
function autosave() { return post(`/api/session/${D.sid}/state`, {action: 'autosave'}); }
async function finish(text) {
  running = false; paused = true; try { rec && rec.stop(); } catch (_) {}
  mic('Mic off', 'bg-slate-200'); await autosave().catch(() => {});
  const c = counts(); msg(`${text} Present ${c[P]}, Absent ${c[A]}, Pending ${c[V]}, Unreviewed ${c.u}. Review the list, then submit.`);
}

// ---------- mode 1: voice by roll number ----------
const keyOf = s => s.roll.replace(/\D/g, '').replace(/^0+(?=\d)/, '');
const isPrefix = k => R.some(s => { const x = keyOf(s); return x !== k && x.startsWith(k); });
let lastKey = '', lastAt = 0;
function startRoll() {
  if (noSR() || running) return;
  running = true; paused = false; rec = recog(true, true);
  rec.onresult = e => {
    for (let i = e.resultIndex; i < e.results.length; i++) {
      const res = e.results[i];
      if (res.isFinal) { handle(res); continue; }
      reset();                                   // speech is happening: keep the 6 s timer alive
      const k = parse(res[0].transcript), m = byRoll[k];
      if (m && m.length === 1 && !isPrefix(k)) accept(m[0], k);   // exact, unambiguous: mark without waiting for "final"
    }
  };
  rec.onspeechstart = () => { if (running) reset(); };
  rec.onend = () => { if (running) try { rec.start(); } catch (_) {} };
  say('Please say your roll number for attendance.').then(() => { if (!running) return;
    try { rec.start(); } catch (_) {} mic('🎤 Listening', 'bg-green-200'); reset(); });
}
const reset = () => { clearTimeout(timer); timer = setTimeout(() => finish('Voice attendance completed and saved.'), 6000); };
function accept(s, k) {
  const now = Date.now();
  if (k === lastKey && now - lastAt < 3500) return;       // same utterance already handled
  lastKey = k; lastAt = now; reset();
  if (s.status === P) { msg(`${s.roll} already marked.`); say('Already'); return; }
  mark(s, P); msg(`✔ ${s.roll} ${s.name}`); say('Next.');
}
function handle(res) {
  reset(); let hit = null, hk = '', amb = false, seen = '';
  for (let i = 0; i < res.length && !hit; i++) {
    const k = parse(res[i].transcript); if (k) seen = seen || k;
    const m = byRoll[k]; if (m && m.length === 1) { hit = m[0]; hk = k; } else if (m) amb = true;
  }
  if (hit) return accept(hit, hk);
  if (!seen && !amb) { msg(`Heard: "${res[0].transcript}" – no number`); return; }
  msg(amb ? 'Ambiguous roll number.' : `Not recognized: "${res[0].transcript}"`); say('Repeat');
}

// ---------- mode 2: call and confirm ----------
const YES = /pres+[ae]?nt|prasent|prazent|parsent|presen|\b(yes|yeah|yep|yea|here|haan|han|ha|haazir|hazir|hajir|sir|madam|mam|jee?|okay|ok)\b/i;
let idx = 0, skip = false, repeat = false;
async function callLoop() {
  if (noSR() || running) return; running = true; paused = false;
  while (running && idx < R.length) {
    const s = R[idx]; if (s.status === P || s.status === A) { idx++; continue; }
    msg(`Calling ${s.roll} ${s.name}`); mic('🔊 Speaking', 'bg-blue-200');
    await say(`Roll number ${s.roll}, ${s.name}. Please say Present.`);
    let heard = false, unclear = false, over = false; skip = repeat = false;
    const r = recog(true, true); rec = r;
    r.onresult = e => { for (let i = e.resultIndex; i < e.results.length; i++) for (let j = 0; j < e.results[i].length; j++) {
      const t = e.results[i][j].transcript; if (YES.test(t) || parse(t) === keyOf(s)) heard = true; else if (t.trim()) unclear = true; } };
    r.onend = () => { if (!over && !heard && running) try { r.start(); } catch (_) {} };   // keep listening for the whole window
    try { r.start(); } catch (_) {} mic('🎤 Listening', 'bg-green-200');
    const end = Date.now() + 3000;
    while (running && !heard && !skip && !repeat && Date.now() < end) {
      if (paused) { while (paused && running) await new Promise(k => setTimeout(k, 200)); break; }
      await new Promise(k => setTimeout(k, 60));
    }
    over = true; try { r.abort(); } catch (_) {}
    if (!running) return;
    if (paused || repeat) continue;
    if (heard) { mark(s, P); msg(`✔ ${s.roll} ${s.name}`); }
    else if (!skip && !s.status) { mark(s, V); msg(unclear ? `Unclear from ${s.roll} – set Pending.` : `No response from ${s.roll} – set Pending.`); }
    idx++;
  }
  if (running) { idx = 0; await finish('Call-and-confirm completed and saved.'); }
}

// ---------- controls ----------
if ($('bStart')) {
  $('bStart').onclick = () => { if (D.mode === 'voice_roll') { paused = false; startRoll(); } else { paused = false; callLoop(); } };
  $('bPause').onclick = () => { paused = true; if (D.mode === 'voice_roll') { running = false; clearTimeout(timer); try { rec.stop(); } catch (_) {} }
    mic('Paused', 'bg-amber-200'); };
  $('bStop').onclick = () => { speechSynthesis.cancel(); finish('Stopped and saved.'); };
  if ($('bSkip')) { $('bSkip').onclick = () => skip = true; $('bRep').onclick = () => repeat = true; }
}
window.addEventListener('beforeunload', () => { if (retry.length) return 'Unsaved changes pending'; });
build();
if (!D.canEdit) msg('This session is locked (finalized or submitted).');
})();
