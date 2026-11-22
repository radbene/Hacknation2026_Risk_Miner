// Undo the side effect of the `ekspert` scene: reopen the event it accepted (back to "Czeka na eksperta").
// Uses the app's demo expert account (README: ekspert / demo-riskminer).
const API = (process.env.DEMO_API || 'http://localhost:8040').replace(/\/$/, '');
const PROJECT = 'c5d55863-81b8-552e-bad0-4f44d2f8d513', TITLE = 'Zmiana umowy nr 2 – termin, zakres';
const login = await fetch(`${API}/api/auth/login`, {method: 'POST', headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({username: 'ekspert', password: 'demo-riskminer'})}).then(r => r.json());
const auth = {Authorization: `Bearer ${login.token}`, 'Content-Type': 'application/json'};
const evs = await fetch(`${API}/api/events?project_id=${PROJECT}&limit=200`, {headers: auth}).then(r => r.json());
const list = Array.isArray(evs) ? evs : evs.items;
const ev = list.find(e => (e.title || '').startsWith(TITLE));
if (!ev) { console.error('event not found'); process.exit(1); }
console.log('status before:', ev.review_status ?? ev.status);
const r = await fetch(`${API}/api/review/event/${ev.id}`, {method: 'POST', headers: auth,
  body: JSON.stringify({action: 'reopen', comment: 'Cofnięcie zatwierdzenia z nagrania filmu demo'})});
console.log('reopen:', r.status, (await r.text()).slice(0, 200));
