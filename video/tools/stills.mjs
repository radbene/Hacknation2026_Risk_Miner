// Renders single frames of the composition and tiles them into contact sheets — the check before a full render.
//   node tools/stills.mjs                    → one frame every 4 seconds
//   node tools/stills.mjs --every 2          → one frame every 2 seconds
//   node tools/stills.mjs 150 320 900        → these composition frames
//   node tools/stills.mjs --part example --every 1.5   → only inside one part of the video
// Output: out/stills/fNNNNN.png and out/stills/sheet-NN.jpg (six frames per sheet, reading order).
import {bundle} from '@remotion/bundler';
import {renderStill, selectComposition} from '@remotion/renderer';
import fs from 'node:fs';
import path from 'node:path';
import {ROOT, clock, parseArgs, rel, sheets} from './util.mjs';

const {opts, rest} = parseArgs();
const outDir = path.resolve(opts.out || path.join(ROOT, 'out', 'stills'));
fs.rmSync(outDir, {recursive: true, force: true});
fs.mkdirSync(outDir, {recursive: true});

const serveUrl = await bundle({entryPoint: path.join(ROOT, 'src', 'index.ts')});
const composition = await selectComposition({serveUrl, id: opts.id || 'Demo'});
const {fps, durationInFrames: total} = composition;
const parts = composition.props?.parts ?? [];
console.log(`${composition.id}: ${composition.width}x${composition.height}, ${fps} fps, ${total} frames (${clock(total / fps)})`);
for (const p of parts) console.log(`  ${String(p.start).padStart(6)} – ${String(p.start + p.frames - 1).padEnd(6)} ${p.name}  (${(p.frames / fps).toFixed(1)} s)`);

let frames = rest.map(Number).filter(Number.isFinite);
if (!frames.length) {
  const step = Math.max(1, Math.round(Number(opts.every || 4) * fps));
  let from = 0, to = total;
  if (opts.part) {
    const p = parts.find(q => q.name === opts.part);
    if (!p) { console.error(`No part "${opts.part}". Parts: ${parts.map(q => q.name).join(', ')}`); process.exit(1); }
    from = p.start; to = p.start + p.frames;
  }
  for (let f = from + Math.round(step / 2); f < to; f += step) frames.push(f);
}
frames = frames.filter(f => f >= 0 && f < total);

const partOf = f => parts.find(p => f >= p.start && f < p.start + p.frames)?.name ?? '';
const items = [];
for (const f of frames) {
  const file = path.join(outDir, `f${String(f).padStart(5, '0')}.png`);
  await renderStill({composition, serveUrl, frame: f, output: file, imageFormat: 'png'});
  items.push({file, label: `f${f} ${clock(f / fps)} ${partOf(f)}`});
}
for (const s of sheets(items, outDir, 'sheet')) console.log(`${rel(s.file)}: ${s.items.map(i => i.label).join(' | ')}`);
console.log('Open the sheets and go through the checklist in docs/QA.md. Full-size frames are next to them.');
process.exit(0);
