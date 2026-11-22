// Checks a rendered video and lays it out for inspection.
//   node tools/qa.mjs [out/demo.mp4] [--expect 1920x1080@60] [--every 5]
// Automatic: container and stream properties, blank frames, where the cuts are, long motionless stretches.
// For your eyes (out/qa/): overview sheets every few seconds and a strip of consecutive frames across every cut.
// Exit code 1 if an automatic check fails. Passing them does not mean the video is good — look at the images.
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {ROOT, burst, clock, grab, parseArgs, probe, rel, run, sheets} from './util.mjs';

const {opts, rest} = parseArgs();
const video = path.resolve(rest[0] || path.join(ROOT, 'out', 'demo.mp4'));
if (!fs.existsSync(video)) { console.error(`No video at ${video}. Run \`npm run render\` first.`); process.exit(1); }
const outDir = path.resolve(opts.out || path.join(ROOT, 'out', 'qa'));
fs.rmSync(outDir, {recursive: true, force: true});
fs.mkdirSync(outDir, {recursive: true});

let failed = 0;
const pass = msg => console.log(`  ok    ${msg}`);
const fail = msg => { failed++; console.log(`  FAIL  ${msg}`); };
const note = msg => console.log(`  note  ${msg}`);

// 1. The file is what was asked for.
const v = probe(video);
const [, ew, eh, efps] = /^(\d+)x(\d+)@(\d+(?:\.\d+)?)$/.exec(String(opts.expect || '1920x1080@60')) || [];
console.log(`${rel(video)}: ${v.width}x${v.height}, ${v.fps} fps, ${clock(v.duration)} (${v.frames} frames), ${v.codec}/${v.pixFmt}, ${(v.bytes / 2 ** 20).toFixed(1)} MB`);
v.width === Number(ew) && v.height === Number(eh) ? pass(`size ${ew}x${eh}`) : fail(`size is ${v.width}x${v.height}, expected ${ew}x${eh}`);
Math.abs(v.fps - Number(efps)) < 0.01 ? pass(`${efps} fps`) : fail(`frame rate is ${v.fps}, expected ${efps}`);
v.codec === 'h264' && v.pixFmt === 'yuv420p' ? pass('H.264 / yuv420p (plays everywhere)') : fail(`codec ${v.codec}/${v.pixFmt}: use H.264 yuv420p for players and chat apps`);
Math.abs(v.frames / v.fps - v.duration) < 0.1 ? pass('frame count matches duration') : fail(`${v.frames} frames at ${v.fps} fps is not ${v.duration}s — the render was interrupted?`);
note(v.audio ? 'has an audio track' : 'no audio track');

// 2. One decode pass: blank frames, cuts, motionless stretches.
const r = run('ffmpeg', ['-hide_banner', '-nostats', '-i', video, '-an', '-filter_complex',
  `[0:v]split=3[a][b][c];[a]blackdetect=d=0.03:pix_th=0.08[a1];[b]freezedetect=n=0.001:d=4[b1];[c]scale=320:-2,select='gt(scene,${opts.scene || 0.2})',showinfo[c1]`,
  '-map', '[a1]', '-f', 'null', '-', '-map', '[b1]', '-f', 'null', '-', '-map', '[c1]', '-f', 'null', '-'], {allowFail: true});
const log = r.stderr;
const black = [...log.matchAll(/black_start:([\d.]+) black_end:([\d.]+)/g)].map(m => [Number(m[1]), Number(m[2])]);
black.length ? fail(`blank frames at ${black.map(b => `${clock(b[0])}–${clock(b[1])}`).join(', ')} — footage missing or not loaded at a clip boundary`) : pass('no blank frames');
const cuts = [...log.matchAll(/pts_time:([\d.]+)/g)].map(m => Number(m[1])).filter((t, i, a) => i === 0 || t - a[i - 1] > 0.25);
const freezes = [...log.matchAll(/freeze_start: ([\d.]+)[\s\S]*?freeze_duration: ([\d.]+)/g)].map(m => [Number(m[1]), Number(m[2])]);
for (const [t, d] of freezes) note(`nothing moves for ${d.toFixed(1)} s from ${clock(t)} — fine if a caption is typing or the viewer is meant to read; otherwise footage has stalled`);

// 3. For your eyes.
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'qa-'));
const every = Number(opts.every || 5);
const times = Array.from({length: Math.ceil(v.duration / every)}, (_, i) => (i + 0.5) * every).filter(t => t < v.duration);
const items = times.map((t, i) => { const file = path.join(tmp, `g${i}.png`); grab(video, t, file); return {file, label: clock(t)}; });
console.log('\nOverview (reading order):');
for (const s of sheets(items, outDir, 'overview')) console.log(`  ${rel(s.file)}: ${s.items.map(i => i.label).join(' | ')}`);
console.log(`\n${cuts.length} abrupt picture change(s) (cuts between parts or clips, or content that changes all at once):`);
for (const t of cuts.slice(0, Number(opts.cuts || 24))) {
  const file = path.join(outDir, `cut-${t.toFixed(2).padStart(7, '0')}.jpg`);
  burst(video, t - 6 / v.fps, file, {count: 12, cols: 6});
  console.log(`  ${rel(file)}: 6 frames before and after ${clock(t)}`);
}
fs.rmSync(tmp, {recursive: true, force: true});

console.log(failed ? `\n${failed} automatic check(s) FAILED.` : '\nAutomatic checks passed. Now open the images above and go through docs/QA.md — these checks cannot see a wrong zoom target, a clipped caption or a cursor in the wrong place.');
process.exit(failed ? 1 : 0);
