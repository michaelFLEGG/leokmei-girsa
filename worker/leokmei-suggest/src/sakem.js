/* ===== סכם: פרק שלם על המנוי, בלי API (פרומפט 15, 28.10.2026) =====
   בקובץ הזה אין קריאה למודל. "סכם" על קטע מסומן - מיד, דרך ה-API (sakem_now.js, הוחזר 29.10),
   ונופל לתור כשאין קרדיט. "סכם פרק" - תמיד תור:
   הדף בונה "חבילה" (יחידות הפרק או הקטע בפורמט הדף, לשון הגמרא ופירוש הגמרא של דפיו)
   ושולח אותה לכאן. פעולת גיטהאב (sakem-sync.yml) מורידה את החבילות לריפו
   (data/sakem/queue/<jid>.json), משימה מתוזמנת של קלוד בענן כותבת הצעות לריפו
   (data/sakem/out/<jid>.json) לפי docs/sakem-runner.md, והפעולה מעלה אותן חזרה לכאן.
   המנהל סוקר בדף קטע-קטע, וכל הכרעה נרשמת כאן ויורדת לריפו ללמידה (data/sakem/decisions/).

   POST /sakem/job        {slug, kind:'perek'|'seg', perek, title, packet}   הכנסה לתור
   POST /sakem/cancel     {jid}                                              הוצאה מן התור
   GET  /sakem/jobs       ?slug                                              התור ומצבו (ממתין / בעבודה N מתוך M / מוכן לסקירה)
   GET  /sakem/out        ?jid                                               ההצעות וההכרעות של עבודה אחת
   POST /sakem/dec        {jid, iid, act, layers, final, prop, orig, slug}   הכרעה על פריט (accept/reject/edit/undo)
   GET  /sakem/export                                                        (פעולת הסנכרון) חבילות שטרם ירדו לריפו
   POST /sakem/exported   {jids}
   POST /sakem/import     {jid, out}                                         (פעולת הסנכרון) הצעות מן הריפו
   GET  /sakem/decisions                                                     (פעולת הסנכרון) הכרעות של פרקים שנסקרו
   POST /sakem/committed  {jids}
   POST /sakem/done, /sakem/later, GET /sakem/stat, /sakem/queue - כמו קודם (יומן הלמידה ותור הסולמיות הישן). */
import SKC from '../../../tools/sakem_core.js';
import { sakemNow, nowStat, nowDone, NOW_PATHS } from './sakem_now.js';

const norm = (t) => SKC.bare(t).replace(/[֑-ׇ]/g, '').replace(/[\s ]+/g, ' ').trim();
const JOBS = 'skm:jobs';
const jidOk = (j) => /^[a-z-]{2,30}-(p\d{1,2}|s\d{1,9}-[a-z0-9]{1,12})$/.test(j || '');
const HVG = { 'א': 1, 'ב': 2, 'ג': 3, 'ד': 4, 'ה': 5, 'ו': 6, 'ז': 7, 'ח': 8, 'ט': 9, 'י': 10, 'כ': 20, 'ל': 30, 'מ': 40, 'נ': 50, 'ס': 60, 'ע': 70, 'פ': 80, 'צ': 90, 'ק': 100, 'ר': 200, 'ש': 300, 'ת': 400 };
function dafNum(d) {
  d = String(d || '').trim();
  let n = 0;
  for (const c of d.replace(/[^א-ת]/g, '')) n += HVG[c] || 0;
  return n ? n * 2 + (/:$/.test(d) ? 1 : 0) : null;
}
async function jobs(env) { return (await env.STORE.get(JOBS, 'json')) || { items: [] }; }
async function putJobs(env, j) { j.items = j.items.slice(-200); await env.STORE.put(JOBS, JSON.stringify(j)); }
/* מה שמוצג לדף: בלי החבילה עצמה */
const pub = (x) => ({ jid: x.jid, slug: x.slug, kind: x.kind, perek: x.perek, title: x.title, t: x.t, st: x.st, n: x.n || 0, total: x.total || 0, shown: x.shown || 0, dec: x.dec || 0 });

export async function sakemApi(req, env, url, p, h) {
  const { isAdmin, json, bad, slugOk } = h;
  if (!(await isAdmin(req, env))) return bad('אין הרשאה', 401);
  let b = {};
  if (req.method === 'POST') { try { b = await req.json(); } catch (e) { return bad('גוף הבקשה אינו JSON'); } }

  /* ---- קטע מסומן: מיד, דרך ה-API (הכרעת המנהל 29.10.2026) ---- */
  if (NOW_PATHS.has(p)) return sakemNow(env, p, b, h);

  /* ---- התור ---- */
  if (p === '/sakem/job') {
    const slug = String(b.slug || ''), kind = b.kind === 'seg' ? 'seg' : 'perek';
    if (!slugOk(slug)) return bad('מסכת לא תקינה');
    const pk = b.packet;
    if (!pk || !Array.isArray(pk.units) || !pk.units.length) return bad('החבילה ריקה');
    const body = JSON.stringify(pk);
    if (body.length > 4e6) return bad('החבילה גדולה מדי');
    const perek = Math.max(0, Math.min(99, +b.perek || 0));
    const jid = kind === 'perek' ? slug + '-p' + perek : slug + '-s' + (+pk.units[0].id || 0) + '-' + Date.now().toString(36);
    if (!jidOk(jid)) return bad('מזהה עבודה לא תקין');
    const J = await jobs(env);
    const old = J.items.find((x) => x.jid === jid && x.st !== 'done');
    if (old) return json({ ok: true, jid, job: pub(old), again: true });
    J.items = J.items.filter((x) => x.jid !== jid);
    pk.jid = jid;
    await env.STORE.put('skm:job:' + jid, JSON.stringify(pk));
    await env.STORE.delete('skm:out:' + jid);
    await env.STORE.delete('skm:dec:' + jid);
    const it = { jid, slug, kind, perek, title: String(b.title || '').slice(0, 120), t: Date.now(), st: 'wait' };
    J.items.push(it);
    await putJobs(env, J);
    return json({ ok: true, jid, job: pub(it) });
  }
  if (p === '/sakem/cancel') {
    const jid = String(b.jid || '');
    const J = await jobs(env);
    J.items = J.items.filter((x) => x.jid !== jid);
    await putJobs(env, J);
    return json({ ok: true });
  }
  if (p === '/sakem/jobs') {
    const slug = url.searchParams.get('slug') || '';
    const J = await jobs(env);
    return json({ ok: true, items: J.items.filter((x) => !slug || x.slug === slug).map(pub) });
  }
  if (p === '/sakem/out') {
    const jid = url.searchParams.get('jid') || '';
    if (!jidOk(jid)) return bad('מזהה עבודה לא תקין');
    const out = await env.STORE.get('skm:out:' + jid, 'json');
    if (!out) return bad('ההצעות לפרק הזה טרם הגיעו', 404);
    const dec = (await env.STORE.get('skm:dec:' + jid, 'json')) || { dec: {}, log: [] };
    const J = await jobs(env), it = J.items.find((x) => x.jid === jid);
    return json({ ok: true, out, dec: dec.dec, job: it ? pub(it) : null });
  }
  if (p === '/sakem/dec') {
    const jid = String(b.jid || ''), iid = String(b.iid || '').slice(0, 24), act = String(b.act || '');
    if (!jidOk(jid) || !iid || !/^(accept|reject|edit|undo|stale|keep)$/.test(act)) return bad('הכרעה לא תקינה');
    const dk = 'skm:dec:' + jid;
    const D = (await env.STORE.get(dk, 'json')) || { dec: {}, log: [] };
    const layers = (Array.isArray(b.layers) ? b.layers : []).map(String).slice(0, 4);
    if (act === 'undo') delete D.dec[iid];
    else D.dec[iid] = { act, layers, t: Date.now() };
    const cut = (s, n) => String(s || '').slice(0, n);
    D.log.push({ iid, act, layers, t: Date.now(), orig: cut(b.orig, 6000), prop: cut(b.prop, 6000), final: act === 'edit' ? cut(b.final, 6000) : '', gem: cut(b.gem, 1500) });
    D.log = D.log.slice(-600);
    await env.STORE.put(dk, JSON.stringify(D));
    /* גם ליומן הלמידה הכללי של סכם (כמו /sakem/done), כשהנוסח הסופי שונה מן ההצעה */
    if (act === 'edit' && b.final && norm(b.final) !== norm(b.prop || '')) {
      const lg = (await env.STORE.get('skm:lg', 'json')) || { pairs: [], rejects: 0, applied: 0, rj: [] };
      lg.pairs.push({ id: jid + ':' + iid, slug: String(b.slug || ''), t: Date.now(), orig: cut(b.orig, 6000), prop: cut(b.prop, 6000), final: cut(b.final, 6000), kinds: SKC.diffKinds(String(b.prop || ''), String(b.final)), layers });
      lg.pairs = lg.pairs.slice(-300);
      await env.STORE.put('skm:lg', JSON.stringify(lg));
    }
    const J = await jobs(env), it = J.items.find((x) => x.jid === jid);
    if (it) {
      it.dec = Object.keys(D.dec).length;
      if (it.shown && it.dec >= it.shown && it.st === 'ready') it.st = 'done';
      else if (it.st === 'done' && it.dec < it.shown) it.st = 'ready';
      await putJobs(env, J);
    }
    return json({ ok: true, job: it ? pub(it) : null });
  }

  /* ---- פעולת הסנכרון (גיטהאב, עם מפתח המנהל כסוד בריפו) ---- */
  if (p === '/sakem/export') {
    /* again: עבודות שסומנו "נשלח" אך אינן בריפו (הדחיפה של הסנכרון נכשלה אחרי הסימון) - נשלחות שוב */
    const again = new Set(String(url.searchParams.get('again') || '').split(',').filter(Boolean));
    const J = await jobs(env), out = [];
    for (const it of J.items.filter((x) => x.st === 'wait' || (x.st === 'sent' && again.has(x.jid))).slice(0, 6)) {
      const pk = await env.STORE.get('skm:job:' + it.jid, 'json');
      if (!pk) continue;
      /* ביאור חברותא לדפי החבילה, מן המחסן */
      pk.hv = {};
      for (const pg of pk.pages || []) {
        const n = dafNum(pg.daf);
        if (n === null) continue;
        try {
          const ch = await env.STORE.get('hv:' + it.slug + ':' + Math.floor(n / 12), 'json');
          const hp = ch && ch[pg.daf];
          if (hp && hp.segs) pk.hv[pg.daf] = hp.segs.map((s) => ({ p: s.p, g: s.g || '', e: String(s.e || '').replace(/\[\[הערה:\d+\]\]/g, '') }));
        } catch (e) { /* בלי חברותא */ }
      }
      out.push({ job: pub(it), packet: pk });
    }
    return json({ ok: true, items: out });
  }
  if (p === '/sakem/exported') {
    const ids = new Set((b.jids || []).map(String));
    const J = await jobs(env);
    J.items.forEach((x) => { if (ids.has(x.jid) && x.st === 'wait') x.st = 'sent'; });
    await putJobs(env, J);
    return json({ ok: true });
  }
  if (p === '/sakem/import') {
    const jid = String(b.jid || ''), o = b.out;
    if (!jidOk(jid) || !o || !Array.isArray(o.items)) return bad('תוצאה לא תקינה');
    const J = await jobs(env), it = J.items.find((x) => x.jid === jid);
    if (!it) return json({ ok: true, skipped: 'no-job' });
    await env.STORE.put('skm:out:' + jid, JSON.stringify(o));
    it.total = +o.total || 0;
    it.n = +o.done || 0;
    it.shown = o.items.filter((x) => !x.nochange).length;
    if (o.status === 'ready') { if (it.st !== 'done') it.st = (it.dec || 0) >= it.shown && it.shown ? 'done' : 'ready'; }
    else if (it.st === 'wait' || it.st === 'sent') it.st = 'work';
    await putJobs(env, J);
    return json({ ok: true, job: pub(it) });
  }
  if (p === '/sakem/decisions') {
    const J = await jobs(env), out = [];
    for (const it of J.items.filter((x) => x.st === 'done' && !x.dc)) {
      const D = await env.STORE.get('skm:dec:' + it.jid, 'json');
      if (D) out.push({ job: pub(it), dec: D.dec, log: D.log });
    }
    return json({ ok: true, items: out });
  }
  if (p === '/sakem/committed') {
    const ids = new Set((b.jids || []).map(String));
    const J = await jobs(env);
    J.items.forEach((x) => { if (ids.has(x.jid)) x.dc = 1; });
    await putJobs(env, J);
    return json({ ok: true });
  }

  /* ---- יומן הלמידה (כמו קודם) ---- */
  if (p === '/sakem/stat') {
    const lg = (await env.STORE.get('skm:lg', 'json')) || { pairs: [], rejects: 0 };
    const slug = url.searchParams.get('slug') || '';
    const J = await jobs(env);
    return json({ ok: true, ...(await nowStat(env)), pairs: lg.pairs.length, rejects: lg.rejects || 0,
                  later: lg.pairs.reduce((n, x) => n + ((x.later || []).length), 0),
                  jobs: J.items.filter((x) => !slug || x.slug === slug).map(pub) });
  }
  if (p === '/sakem/queue') {
    const slug = url.searchParams.get('slug') || '';
    if (!slugOk(slug)) return bad('מסכת לא תקינה');
    const q = (await env.STORE.get('skm:hq:' + slug, 'json')) || { items: [] };
    return json({ ok: true, items: q.items.filter((x) => !x.d) });
  }
  if (p === '/sakem/done') {
    const slug = String(b.slug || ''), id = String(b.id || '').slice(0, 40), act = String(b.act || '');
    await nowDone(env, b);
    if (slugOk(slug)) {
      const qk = 'skm:hq:' + slug, q = await env.STORE.get(qk, 'json');
      if (q && q.items.some((x) => x.id === id && !x.d)) { q.items.forEach((x) => { if (x.id === id) x.d = act || 'done'; }); await env.STORE.put(qk, JSON.stringify(q)); }
    }
    return json({ ok: true });
  }
  /* עריכה מאוחרת: המנהל תיקן בעורך שורה שנכתבה ב"סכם", אחרי שקיבל. נצמדת לאותה הצעה ביומן הלמידה. */
  if (p === '/sakem/later') {
    const id = String(b.id || '').slice(0, 60), was = String(b.was || '').slice(0, 4000), now = String(b.now || '').slice(0, 4000);
    const KINDS = ['מספור', 'דובר', 'הסבר'];
    const wasI = String(b.wasI || '').slice(0, 4000), nowI = String(b.nowI || '').slice(0, 4000);
    const kinds = [...new Set((Array.isArray(b.kinds) ? b.kinds.map(String) : []).concat(wasI && nowI ? SKC.diffKinds(wasI, nowI) : []))].filter((k) => KINDS.includes(k));
    if (!id || !now || norm(was) === norm(now)) return json({ ok: true, skipped: true });
    const lg = (await env.STORE.get('skm:lg', 'json')) || { pairs: [], rejects: 0, applied: 0, rj: [] };
    let pair = lg.pairs.find((x) => x.id === id);
    if (!pair) { pair = { id, slug: String(b.slug || ''), t: Date.now(), orig: '', prop: was, final: was }; lg.pairs.push(pair); }
    pair.later = (pair.later || []).filter((x) => norm(x.was) !== norm(was));
    pair.later.push({ was, now, daf: String(b.daf || '').slice(0, 12), t: Date.now(), kinds });
    pair.later = pair.later.slice(-20);
    pair.t = Date.now();
    lg.pairs = lg.pairs.slice(-300);
    await env.STORE.put('skm:lg', JSON.stringify(lg));
    return json({ ok: true, n: pair.later.length });
  }
  return bad('נתיב לא מוכר', 404);
}
