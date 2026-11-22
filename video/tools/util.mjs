// Shared by the tools: running ffmpeg/ffprobe, grabbing frames, tiling images into contact sheets.
import {spawnSync} from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

export const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');

export function run(cmd, args, {allowFail = false} = {}) {
  const r = spawnSync(cmd, args, {encoding: 'utf8', maxBuffer: 256 * 1024 * 1024});
  if (r.error) throw new Error(`${cmd} could not be started (${r.error.code}). Is it installed and on PATH?`);
  if (r.status !== 0 && !allowFail) throw new Error(`${cmd} ${args.join(' ')}\n${r.stderr.slice(-2000)}`);
  return r;
}

/** Arguments of the form `--name value` and bare words. */
export function parseArgs(argv = process.argv.slice(2)) {
  const opts = {}, rest = [];
  for (let i = 0; i < argv.length; i++) {
    if (argv[i].startsWith('--')) { const k = argv[i].slice(2); opts[k] = argv[i + 1] && !argv[i + 1].startsWith('--') ? argv[++i] : true; }
    else rest.push(argv[i]);
  }
  return {opts, rest};
}

export function probe(video) {
  const r = run('ffprobe', ['-v', 'error', '-show_streams', '-show_format', '-of', 'json', video]);
  const j = JSON.parse(r.stdout), v = j.streams.find(s => s.codec_type === 'video');
  const [n, d] = v.r_frame_rate.split('/').map(Number);
  return {
    width: v.width, height: v.height, fps: n / d, codec: v.codec_name, pixFmt: v.pix_fmt, frames: Number(v.nb_frames),
    duration: Number(j.format.duration), bytes: Number(j.format.size), audio: j.streams.some(s => s.codec_type === 'audio'),
  };
}

/** One frame of a video at `t` seconds, scaled to `width`. */
export function grab(video, t, out, width = 960) {
  run('ffmpeg', ['-y', '-loglevel', 'error', '-ss', String(Math.max(0, t)), '-i', video, '-frames:v', '1', '-update', '1',
    '-vf', `scale=${width}:-2`, out]);
}

/** `count` consecutive frames starting at `t`, tiled in one image: the way to look at motion without a player. */
export function burst(video, t, out, {count = 12, cols = 6, width = 480} = {}) {
  run('ffmpeg', ['-y', '-loglevel', 'error', '-ss', String(Math.max(0, t)), '-i', video, '-frames:v', '1', '-update', '1',
    '-vf', `scale=${width}:-2,tile=${cols}x${Math.ceil(count / cols)}`, '-q:v', '3', out]);
}

/** Tiles image files (same size, any names) into one contact sheet, reading order left to right, top to bottom. */
export function tile(files, out, {cols = 2, width = 960} = {}) {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'sheet-'));
  const ext = path.extname(files[0]);
  files.forEach((f, i) => fs.copyFileSync(f, path.join(tmp, `i-${String(i).padStart(3, '0')}${ext}`)));
  fs.mkdirSync(path.dirname(out), {recursive: true});
  run('ffmpeg', ['-y', '-loglevel', 'error', '-start_number', '0', '-i', path.join(tmp, `i-%03d${ext}`), '-frames:v', '1', '-update', '1',
    '-vf', `scale=${width}:-2,tile=${cols}x${Math.ceil(files.length / cols)}`, '-q:v', '3', out]);
  fs.rmSync(tmp, {recursive: true, force: true});
}

/** Splits `items` into sheets of `per`, tiles each, and returns [{file, items}] so the caller can say what is where. */
export function sheets(items, dir, prefix, {per = 6, cols = 2, width = 960} = {}) {
  const out = [];
  for (let i = 0; i < items.length; i += per) {
    const part = items.slice(i, i + per), file = path.join(dir, `${prefix}-${String(i / per + 1).padStart(2, '0')}.jpg`);
    tile(part.map(p => p.file), file, {cols, width});
    out.push({file, items: part});
  }
  return out;
}

export const rel = p => path.relative(process.cwd(), p) || '.';
export const clock = s => `${Math.floor(s / 60)}:${(s % 60).toFixed(1).padStart(4, '0')}`;
