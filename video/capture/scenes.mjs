// The scenes of the RISK MINER demo. One function per scene; each writes public/captures/<name>.mp4 + .json.
//   DEMO_BASE=http://localhost:5180 node capture/scenes.mjs            → every scene
//   DEMO_BASE=http://localhost:5180 node capture/scenes.mjs ekspert    → one scene
// Everything runs against the real app (API :8040, worker, local Bielik via Ollama). Side effects:
//   ekspert  – accepts ONE proposed event (RM-2026-004, "Zmiana umowy nr 2"); run `node capture/undo.mjs` to reopen it
//   analiza  – creates one new analysis "Przykład: kanalizacja sanitarna" in "Moje analizy"
import {launch, Recorder, BASE, settle} from './lib.mjs';

if (!BASE) { console.error('Set DEMO_BASE, e.g. DEMO_BASE=http://localhost:5180'); process.exit(1); }

const NOWOGARD = '1af41c13-14b5-5838-952b-cb0eb360ceba';   // RM-2026-020, Nowogard – Konarzewo
const CZERNIKOWO = 'c5d55863-81b8-552e-bad0-4f44d2f8d513'; // RM-2026-004, SUW Czernikowo
const SCROLLER = 'main > div.overflow-auto';                // the app scrolls inside this div, not the window
const opts = {locale: 'pl-PL', timezoneId: 'Europe/Warsaw'};

/** Scroll the app's content so that `loc`'s top lands `top` px below the viewport's top. */
async function scrollTo(rec, loc, top = 130, ms = 900) {
  const r = await rec.rect(loc);
  const dy = Math.round(r.y - top);
  if (Math.abs(dy) > 4) await rec.scrollBy(dy, ms, SCROLLER);
}
/** The innermost ink-bordered card containing `text`. */
const card = (page, text) => page.locator('div.border-2.border-ink.shadow-md', {hasText: text}).last();
/** Union of all elements matching a selector, as a rectangle (viewport coordinates now). */
const unionOf = (page, sel) => () => page.evaluate(s => {
  const rs = [...document.querySelectorAll(s)].map(e => e.getBoundingClientRect()).filter(r => r.width > 0);
  if (!rs.length) return null;
  const x = Math.min(...rs.map(r => r.x)), y = Math.min(...rs.map(r => r.y));
  return {x, y, w: Math.max(...rs.map(r => r.right)) - x, h: Math.max(...rs.map(r => r.bottom)) - y};
}, sel);

async function open(page, path) {
  await page.goto(BASE + path);
  await settle(page);
  await page.waitForSelector('h1');
  await page.waitForTimeout(800);   // page entrance animation
}

const scenes = {
  /** Path A: a finished investment, its link to BZP with reasons, an event with its cause, the source. */
  async baza() {
    const {ctx, page} = await launch(opts);
    try {
      await open(page, `/projekty/${NOWOGARD}`);
      const rec = new Recorder(page, 'baza'); await rec.start();
      await rec.mark('header', page.locator('h1').locator('..'));
      await rec.mark('tabs', page.getByRole('tablist'));
      await rec.wait(1600);

      // 1. the BZP procedure this project was linked to, with the conditions checked
      const tabLinks = page.getByRole('tab', {name: /Ogłoszenia BZP tej inwestycji/});
      await rec.clickOn(tabLinks, {fx: 0.4});                                      // click 0
      await page.getByText('Dopasowano po podobieństwie').waitFor();
      await rec.wait(500);
      await scrollTo(rec, card(page, 'Dopasowano po podobieństwie'), 96);
      await rec.mark('link', card(page, 'Dopasowano po podobieństwie'));
      await rec.mark('link-head', page.getByText('Dopasowano po podobieństwie'));
      await rec.mark('reasons', page.locator('ul', {hasText: 'Nazwa zamówienia podobna'}).last());
      await rec.moveToRect(await rec.rect(page.locator('ul', {hasText: 'Nazwa zamówienia podobna'}).last().getByText('Źródło', {exact: true}).nth(1)), {fx: 0.5});
      await rec.wait(4200);

      // 2. back up to the tabs: events and causes
      await rec.mark('up');
      await rec.scrollBy(-2000, 700, SCROLLER);
      const tabEvents = page.getByRole('tab', {name: /Zdarzenia i przyczyny/});
      await rec.clickOn(tabEvents, {fx: 0.4});                                     // click 1
      await page.getByText('Zmiana umowy nr 1 – termin').first().waitFor();
      await rec.wait(500);
      const ev = card(page, 'Zmiana umowy nr 1 – termin');
      await scrollTo(rec, ev, 96);
      await rec.mark('event', ev);
      await rec.mark('event-head', ev.locator('> div').first());
      await rec.mark('cause', ev.getByText('Przyczyna', {exact: true}).locator('..').locator('..'));
      const show = ev.getByText(/Pokaż w źródle/).first();
      await rec.moveToRect(await rec.rect(ev.getByText('+37 dni')), {fx: 0.5});
      await rec.wait(3600);

      // 3. the source: the original notice PDF with the quoted point highlighted
      await rec.clickOn(show);                                                     // click 2
      await rec.realtime(async () => {
        await page.locator('dialog[open]').waitFor();
        await rec.mark('dialog-open', 'dialog[open]');
        await page.locator('div.bg-yellow-300\\/50').first().waitFor({timeout: 30000});
        await page.waitForTimeout(1800);   // the viewer scrolls the quote into view after rendering
      });
      await rec.mark('source', 'dialog[open]');
      await rec.mark('highlight', unionOf(page, 'div.bg-yellow-300\\/50'));
      await rec.moveTo(900, 640);
      await rec.wait(4400);
      await rec.stop();
    } finally { await ctx.close(); }
  },

  /** The expert: one-click demo login, the review queue, accepting one model proposal. */
  async ekspert() {
    const {ctx, page} = await launch(opts);
    try {
      await open(page, `/projekty/${CZERNIKOWO}?tab=zdarzenia`);
      const rec = new Recorder(page, 'ekspert'); await rec.start();
      await rec.wait(700);
      await rec.clickOn(page.getByRole('button', {name: 'Panel eksperta'}));       // click 0
      await page.getByRole('button', {name: 'Wejdź jako ekspert (demo)'}).waitFor();
      await rec.wait(300);
      await rec.mark('login', page.locator('dialog[open]'));
      await rec.wait(900);
      await rec.clickOn(page.getByRole('button', {name: 'Wejdź jako ekspert (demo)'})); // click 1
      await rec.realtime(async () => {
        await page.waitForURL(/\/kolejka/);
        await page.getByText('Zdarzenia i przyczyny').first().waitFor();
        await page.waitForTimeout(700);
      });
      await rec.mark('queue', page.locator('h1').locator('../..'));
      await rec.mark('queue-intro', page.getByText('Wszystko, co system zbudował').locator('..'));
      await rec.mark('queue-counts', page.getByRole('button', {name: /Zdarzenia i przyczyny/}).locator('..'));
      await rec.moveToRect(await rec.rect(page.getByRole('button', {name: /Zdarzenia i przyczyny/})), {fx: 0.7});
      await rec.wait(4200);

      // the project card again, now with the expert's buttons
      await rec.mark('leave');
      await page.goto(`${BASE}/projekty/${CZERNIKOWO}?tab=zdarzenia`);
      await settle(page);
      const ev = card(page, 'Zmiana umowy nr 2 – termin, zakres');
      await ev.waitFor();
      await page.waitForTimeout(900);
      await rec.mark('card');
      await rec.wait(500);
      await scrollTo(rec, ev, 96);
      await rec.mark('event', ev);
      await rec.mark('status', ev.getByText('Czeka na eksperta'));
      const accept = ev.getByRole('button', {name: 'Akceptuj'});
      await rec.mark('actions', accept.locator('..'));
      await rec.moveToRect(await rec.rect(ev.getByText('[Wniosek modelu]')), {fx: 0.5});
      await rec.wait(3000);
      await rec.clickOn(accept);                                                   // click 2
      await rec.realtime(async () => {
        await ev.getByText(/Zatwierdzone przez eksperta/i).waitFor({timeout: 15000});
        await page.waitForTimeout(300);
      });
      await rec.mark('accepted', ev);
      await rec.mark('accepted-status', ev.getByText(/Zatwierdzone przez eksperta/i));
      await rec.moveTo(1100, 600);
      await rec.wait(3800);
      await rec.stop();
    } finally { await ctx.close(); }
  },

  /** Path B: a new investment described in text → features read by the local model → risk analysis. */
  async analiza() {
    const {ctx, page} = await launch(opts);
    try {
      await open(page, '/nowa-inwestycja');
      const rec = new Recorder(page, 'analiza'); await rec.start();
      await rec.mark('page', page.locator('h1').locator('..').locator('..'));
      await rec.wait(1400);
      await scrollTo(rec, page.getByText('1. Opis inwestycji'), 110);
      await rec.mark('form');
      await rec.wait(300);
      await rec.clickOn(page.getByText('Wstaw przykładowy opis'));                 // click 0
      await page.locator('#ni-x').evaluate(e => { if (!e.value) throw new Error('example text not inserted'); });
      await rec.wait(400);
      await rec.mark('filled', page.locator('#ni-x').locator('..').locator('..').locator('..'));
      await rec.mark('text', '#ni-x');
      await rec.moveToRect(await rec.rect('#ni-x'), {fx: 0.75, fy: 0.55});
      await rec.wait(3600);

      const extract = page.getByRole('button', {name: 'Odczytaj cechy'});
      await scrollTo(rec, extract, 520, 700);
      await rec.clickOn(extract);                                                  // click 1
      await rec.realtime(async () => {
        await page.getByText(/model czyta opis/).waitFor({timeout: 10000}).catch(() => {});
        await rec.mark('reading', extract.locator('..'));
        await page.getByRole('button', {name: 'Analizuj ryzyko'}).waitFor({timeout: 150000});
        await rec.mark('read');
        await page.waitForTimeout(600);
      });
      const right = card(page, '2. Sprawdź odczytane cechy');
      await scrollTo(rec, right, 96);
      await rec.mark('features', right);
      await rec.mark('model-badge', right.getByText(/uzupełnił:/));
      if (await page.locator('div.bg-amber-50').count()) await rec.mark('questions', page.locator('div.bg-amber-50').first());
      await rec.moveToRect(await rec.rect(right), {fx: 0.8, fy: 0.3});
      await rec.wait(4200);

      const analyse = page.getByRole('button', {name: 'Analizuj ryzyko'});
      await scrollTo(rec, analyse, 520);
      await rec.clickOn(analyse);                                                  // click 2
      await rec.realtime(async () => {
        await page.getByRole('dialog', {name: /kopalnia|ryzyk/i}).first().waitFor({timeout: 15000}).catch(() => {});
        // The loader is positioned within the scrolled page, so at this scroll position it sits partly above
        // the viewport (a real quirk of the app). Scroll it into view while waiting, as a user would.
        const dlg = page.locator('[role=dialog][aria-modal=true]').first();
        const r = await rec.rect(dlg);
        if (r && (r.y < 60 || r.y + r.h > 720)) await rec.scrollBy(Math.round(r.y - (84 + (720 - 84 - r.h) / 2)), 600, SCROLLER);
        await rec.mark('mining', dlg);
        await page.waitForURL(/\/analizy\//, {timeout: 400000});
        await page.getByText('W skrócie').first().waitFor({timeout: 60000});
        await page.waitForTimeout(1000);
      });
      await rec.mark('result', page.locator('h1').locator('..'));
      const summary = card(page, 'W skrócie');
      await rec.mark('summary', summary);
      await rec.mark('summary-left', summary.getByText('Czy zdąży na czas?').locator('..'));
      await rec.mark('exports', page.getByRole('button', {name: /Pobierz kartę/}).locator('..'));
      await rec.moveToRect(await rec.rect(summary.getByText('Czy zdąży na czas?').locator('..')), {fx: 0.85, fy: 0.85});
      await rec.wait(4600);

      // the flags
      const tablist = page.getByRole('tablist');
      await scrollTo(rec, tablist, 70);
      await rec.mark('flags-tab', page.getByRole('tab', {name: /Na co uważać/}));
      await rec.mark('flags', page.locator('[role=tabpanel]'));
      await rec.moveTo(1150, 420);
      await rec.wait(4600);

      // export
      await rec.mark('up');
      await rec.scrollBy(-2000, 700, SCROLLER);
      await rec.mark('exports-top', page.getByRole('button', {name: /Pobierz kartę/}).locator('..'));
      await rec.moveToRect(await rec.rect(page.getByRole('button', {name: /Pobierz kartę/})), {fx: 0.5});
      await rec.wait(3800);
      await rec.stop();
    } catch (e) {
      await page.screenshot({path: 'out/analiza-fail.png'}).catch(() => {});
      throw e;
    } finally { await ctx.close(); }
  },

  /** Read-only: the similar investments of an existing analysis, one tile opened (no recompute, nothing saved). */
  async podobne() {
    const {ctx, page} = await launch(opts);
    try {
      await open(page, '/analizy/1f4372f8-0579-466c-9bf2-c6e311ae0341?tab=sasiedzi');
      await page.locator('[role=tabpanel] button[aria-expanded]').first().waitFor();
      const rec = new Recorder(page, 'podobne'); await rec.start();
      await rec.wait(500);
      await scrollTo(rec, page.locator('[role=tabpanel]'), 90);
      await rec.mark('grid', page.locator('[role=tabpanel]'));
      await rec.wait(1500);
      const tile = page.locator('[role=tabpanel] button[aria-expanded]').first();
      await rec.clickOn(tile, {fx: 0.3});                                          // click 0
      await page.locator('[role=tabpanel] button[aria-expanded=true]').first().waitFor();
      await rec.wait(400);
      await rec.mark('open', tile.locator('..'));
      await rec.moveTo(900, 500);
      await rec.wait(5000);
      await rec.stop();
    } finally { await ctx.close(); }
  },
};

const wanted = process.argv.slice(2);
for (const name of wanted.length ? wanted : Object.keys(scenes)) {
  if (!scenes[name]) { console.error(`No scene "${name}". Scenes: ${Object.keys(scenes).join(', ')}`); process.exit(1); }
  console.log(`— ${name}`);
  await scenes[name]();
}
