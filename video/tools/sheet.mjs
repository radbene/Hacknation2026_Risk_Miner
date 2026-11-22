// Contact sheets for looking at a video, or a folder of images, without a player.
//   node tools/sheet.mjs out/demo.mp4 --every 5         → a frame every 5 s, six per sheet
//   node tools/sheet.mjs out/demo.mp4 --at 12,19.5,33   → frames at these seconds
//   node tools/sheet.mjs out/demo.mp4 --burst 13.25     → 12 consecutive frames from 13.25 s (motion, cuts)
//   node tools/sheet.mjs --dir out/debug                → every .jpg/.png in a folder
// Options: --out <dir> (default out/sheets), --count N and --cols N for --burst.
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {ROOT, burst, clock, grab, parseArgs, probe, rel, sheets} from './util.mjs';

const {opts, rest} = parseArgs();
const outDir = path.resolve(opts.out || path.join(ROOT, 'out', 'sheets'));
fs.mkdirSync(outDir, {recursive: true});

if (opts.dir) {
  const files = fs.readdirSync(opts.dir).filter(f => /\.(jpe?g|png)$/i.test(f) && !f.startsWith('sheet-')).sort();
  const made = sheets(files.map(f => ({file: path.join(opts.dir, f), label: f})), outDir, 'sheet-dir', {cols: 3, width: 640});
  for (const s of made) console.log(`${rel(s.file)}: ${s.items.map(i => i.label).join(' | ')}`);
  process.exit(0);
}

const video = rest[0];
if (!video || !fs.existsSync(video)) { console.error('Usage: node tools/sheet.mjs <video> --every S | --at t1,t2 | --burst t   (or --dir <folder>)'); process.exit(1); }
const info = probe(video);

if (opts.burst !== undefined) {
  const t = Number(opts.burst), file = path.join(outDir, `burst-${t.toFixed(2)}.jpg`);
  const count = Number(opts.count || 12), cols = Number(opts.cols || 6);
  burst(video, t, file, {count, cols});
  console.log(`${rel(file)}: ${count} consecutive frames from ${clock(t)} (${(1000 / info.fps).toFixed(1)} ms apart), reading order`);
  process.exit(0);
}

const times = opts.at ? String(opts.at).split(',').map(Number)
  : Array.from({length: Math.ceil(info.duration / Number(opts.every || 5))}, (_, i) => (i + 0.5) * Number(opts.every || 5)).filter(t => t < info.duration);
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'grab-'));
const items = times.map((t, i) => { const file = path.join(tmp, `g${i}.png`); grab(video, t, file); return {file, label: clock(t)}; });
for (const s of sheets(items, outDir, 'sheet')) console.log(`${rel(s.file)}: ${s.items.map(i => i.label).join(' | ')}`);
fs.rmSync(tmp, {recursive: true, force: true});
