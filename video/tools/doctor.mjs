// Checks that this machine can capture and render, and says what to do about anything missing.
//   node tools/doctor.mjs
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {spawnSync} from 'node:child_process';
import {ROOT} from './util.mjs';

let failed = false;
const ok = (what, detail = '') => console.log(`  ok    ${what}${detail ? ` — ${detail}` : ''}`);
const bad = (what, fix) => { failed = true; console.log(`  FAIL  ${what}\n        → ${fix}`); };
const note = (what, detail) => console.log(`  note  ${what} — ${detail}`);

const major = Number(process.versions.node.split('.')[0]);
major >= 20 ? ok('Node.js', process.versions.node) : bad(`Node.js ${process.versions.node}`, 'Install Node.js 20 or newer.');

for (const tool of ['ffmpeg', 'ffprobe']) {
  const r = spawnSync(tool, ['-version'], {encoding: 'utf8'});
  r.status === 0 ? ok(tool, r.stdout.split('\n')[0].split(' ').slice(0, 3).join(' '))
    : bad(`${tool} not found`, 'Install FFmpeg (apt install ffmpeg / brew install ffmpeg) and make sure it is on PATH.');
}

if (!fs.existsSync(path.join(ROOT, 'node_modules', 'remotion'))) bad('Dependencies are not installed', 'Run `npm install` in this directory.');
else {
  ok('Dependencies', 'node_modules present');
  try {
    const {chromePath} = await import('../capture/lib.mjs');
    ok('Chromium for capture', chromePath());
  } catch (e) { bad('Chromium for capture', e.message); }
  const shell = path.join(ROOT, 'node_modules', '.remotion');
  fs.existsSync(shell) && fs.readdirSync(shell).length ? ok('Browser for rendering', 'node_modules/.remotion')
    : note('Browser for rendering', 'not downloaded yet; the first render fetches it (about 100 MB), or run `npx remotion browser ensure` now');
}

// Rendering memory: each render tab took 0.5-0.9 GB in practice, plus about 1 GB for the encoder and the rest.
let avail = os.freemem();
try { avail = Number(/MemAvailable:\s+(\d+)/.exec(fs.readFileSync('/proc/meminfo', 'utf8'))[1]) * 1024; } catch {}
const gb = avail / 2 ** 30, conc = Math.max(1, Math.min(Math.floor(os.cpus().length / 2), Math.floor((gb - 1) / 0.8)));
(gb >= 3 ? ok : note)('Memory', `${gb.toFixed(1)} GB available → \`npm run render\` will use ${conc} render tab${conc > 1 ? 's' : ''}`);

if (process.env.DEMO_BASE) {
  try { const r = await fetch(process.env.DEMO_BASE, {signal: AbortSignal.timeout(5000)}); ok('Application', `${process.env.DEMO_BASE} answered ${r.status}`); }
  catch (e) { bad(`Application at ${process.env.DEMO_BASE} does not answer`, 'Start the application, or correct DEMO_BASE.'); }
} else note('Application', 'DEMO_BASE is not set; only the bundled example can be recorded');

console.log(failed ? '\nNot ready: fix the FAIL lines above.' : '\nReady.');
process.exit(failed ? 1 : 0);
