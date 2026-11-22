// Renders the video with settings chosen for screen content, and progress an agent can read.
//   node tools/render.mjs [out/demo.mp4] [--concurrency N] [--id Demo]
import {bundle} from '@remotion/bundler';
import {renderMedia, selectComposition} from '@remotion/renderer';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {ROOT, clock, parseArgs, rel} from './util.mjs';

const {opts, rest} = parseArgs();
const output = path.resolve(rest[0] || path.join(ROOT, 'out', 'demo.mp4'));
fs.mkdirSync(path.dirname(output), {recursive: true});

// Each render tab took 0.5-0.9 GB in practice; running out of memory kills the render late, so start modest.
let avail = os.freemem();
try { avail = Number(/MemAvailable:\s+(\d+)/.exec(fs.readFileSync('/proc/meminfo', 'utf8'))[1]) * 1024; } catch {}
const auto = Math.max(1, Math.min(Math.floor(os.cpus().length / 2), Math.floor((avail / 2 ** 30 - 1) / 0.8)));
const concurrency = Number(opts.concurrency) || auto;

console.log('Bundling…');
const serveUrl = await bundle({entryPoint: path.join(ROOT, 'src', 'index.ts')});
const composition = await selectComposition({serveUrl, id: opts.id || 'Demo'});
const total = composition.durationInFrames;
console.log(`Rendering ${total} frames (${clock(total / composition.fps)}) with ${concurrency} tab(s) → ${rel(output)}`);

const t0 = Date.now();
let last = -1;
await renderMedia({
  composition, serveUrl, codec: 'h264', outputLocation: output, concurrency, overwrite: true,
  imageFormat: 'png',          // JPEG frames smear thin borders and fine textures
  crf: 16, pixelFormat: 'yuv420p', colorSpace: 'bt709', x264Preset: 'slow',
  onProgress: ({renderedFrames, encodedFrames}) => {
    const step = Math.floor((renderedFrames / total) * 20);
    if (step === last) return;
    last = step;
    const el = (Date.now() - t0) / 1000, eta = renderedFrames ? el * (total - renderedFrames) / renderedFrames : 0;
    console.log(`  ${String(step * 5).padStart(3)}%  rendered ${renderedFrames}/${total}, encoded ${encodedFrames}, ${Math.round(el)} s elapsed, about ${Math.round(eta)} s left`);
  },
});
console.log(`Done in ${Math.round((Date.now() - t0) / 1000)} s: ${rel(output)} (${(fs.statSync(output).size / 2 ** 20).toFixed(1)} MB). Now run \`npm run qa\`.`);
process.exit(0);
