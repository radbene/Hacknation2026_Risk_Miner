// Prints what a recording contains — its marks and clicks on the footage clock — and flags the usual problems.
//   node tools/events.mjs            → every recording in public/captures
//   node tools/events.mjs example    → one
// With DEMO_CAPTURE_DEBUG screenshots present (npm run capture:debug → out/debug), also tiles them into
// contact sheets, in the order the marks were made.
import fs from 'node:fs';
import path from 'node:path';
import {ROOT, parseArgs, rel, sheets} from './util.mjs';

const dir = path.join(ROOT, 'public', 'captures');
const {rest} = parseArgs();
const names = rest.length ? rest : (fs.existsSync(dir) ? fs.readdirSync(dir).filter(f => f.endsWith('.json')).map(f => f.slice(0, -5)) : []);
if (!names.length) { console.error('No recordings in public/captures. Run `npm run capture` first.'); process.exit(1); }

let warnings = 0;
const warn = msg => { warnings++; console.log(`  WARN  ${msg}`); };

for (const name of names) {
  const c = JSON.parse(fs.readFileSync(path.join(dir, `${name}.json`), 'utf8'));
  const density = c.frames / c.duration;
  console.log(`\n${name}: ${c.duration}s of footage, ${c.view.width}x${c.view.height} at ${c.scale}x, ${c.frames} captured frames (${density.toFixed(1)} per second), recorded ${c.capturedAt}`);
  let clicks = 0;
  const seen = new Map();
  for (const e of c.events) {
    if (e.type === 'cursor') continue;
    if (e.type === 'click') { console.log(`  ${e.t.toFixed(2).padStart(7)}  click #${clicks++}  at ${Math.round(e.x)},${Math.round(e.y)}`); continue; }
    const nth = seen.get(e.name) ?? 0; seen.set(e.name, nth + 1);
    const r = e.rect ? `rect ${Math.round(e.rect.x)},${Math.round(e.rect.y)} ${Math.round(e.rect.w)}x${Math.round(e.rect.h)}` : '';
    console.log(`  ${e.t.toFixed(2).padStart(7)}  ${(e.name + (nth ? ` #${nth}` : '')).padEnd(22)} ${r}`);
    if (e.rect && (e.rect.w < 4 || e.rect.h < 4)) warn(`mark "${e.name}" has a ${Math.round(e.rect.w)}x${Math.round(e.rect.h)} rectangle — is the element visible at that moment?`);
    if (e.rect && (e.rect.x + e.rect.w < 0 || e.rect.y + e.rect.h < 0 || e.rect.x > c.view.width || e.rect.y > c.view.height))
      warn(`mark "${e.name}" is outside the viewport — scroll to it before marking, or the camera will aim at nothing`);
    else if (e.rect && e.rect.y + e.rect.h > c.view.height + 1) console.log(`           note: "${e.name}" extends below the viewport by ${Math.round(e.rect.y + e.rect.h - c.view.height)}px`);
  }
  if (density < 4) warn(`only ${density.toFixed(1)} captured frames per footage second — motion will look choppy. Raise DEMO_CAPTURE_SLOW (now ${c.slow}).`);
  if (c.scale < 2) warn(`recorded at ${c.scale}x — zooms will be soft`);

  const debug = process.env.DEMO_CAPTURE_DEBUG || path.join(ROOT, 'out', 'debug');
  const shots = fs.existsSync(debug) ? fs.readdirSync(debug).filter(f => f.startsWith(`${name}-`) && f.endsWith('.jpg')).sort() : [];
  if (shots.length) {
    const made = sheets(shots.map(f => ({file: path.join(debug, f), label: f.slice(name.length + 4, -4)})), debug, `sheet-${name}`, {per: 6, cols: 3, width: 640});
    for (const s of made) console.log(`  screenshots at marks → ${rel(s.file)}: ${s.items.map(i => i.label).join(' | ')}`);
  }
}
console.log(warnings ? `\n${warnings} warning(s).` : '\nNo problems found in the logs. Look at the screenshot sheets as well: a log cannot tell whether the page looked right.');
