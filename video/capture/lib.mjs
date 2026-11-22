// Screen capture for a demo video: a real browser driving the real application.
//
// A recording is two files on one clock:
//   public/captures/<name>.mp4   the Chromium screencast (device-pixel frames, constant frame rate)
//   public/captures/<name>.json  what happened in it: cursor samples, clicks, and named marks, each with
//                                the rectangle of the element it refers to
// The composition (src/) draws the cursor and aims the camera from that log, so nothing in the video is
// positioned by hand-measured pixels or hand-typed timestamps.
//
// Chromium cannot deliver 2560x1440 frames in real time (roughly 8-11 per second), so the browser is driven
// in slow motion: our own input, our pauses and the page's CSS animations run SLOW times slower, and the
// recording is retimed by the same factor ("scene time"). Waiting for a server is the exception — it cannot
// be slowed down, so those stretches are recorded at factor 1 (see `realtime`) and keep their true length.
import {chromium} from 'playwright-core';
import {spawnSync} from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

export const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
export const OUT = path.join(ROOT, 'public', 'captures');
/** The application to record; empty means "the scene decides" (the bundled example starts its own server). */
export const BASE = (process.env.DEMO_BASE || '').replace(/\/$/, '');
export const VIEW = {width: 1280, height: 720};
export const SCALE = 2;
export const FPS = 30;
export const SLOW = Number(process.env.DEMO_CAPTURE_SLOW || 5);

export function chromePath() {
  if (process.env.CHROME_PATH) return process.env.CHROME_PATH;
  try {
    const own = chromium.executablePath();  // the build this playwright-core version expects
    if (own && fs.existsSync(own)) return own;
  } catch {}
  // Any other Playwright Chromium already on the machine (newest first).
  const caches = [process.env.PLAYWRIGHT_BROWSERS_PATH, path.join(os.homedir(), '.cache', 'ms-playwright'),
    path.join(os.homedir(), 'Library', 'Caches', 'ms-playwright'),
    process.env.LOCALAPPDATA && path.join(process.env.LOCALAPPDATA, 'ms-playwright')].filter(Boolean);
  const exes = ['chrome-linux64/chrome', 'chrome-linux/chrome', 'chrome-win64/chrome.exe', 'chrome-win/chrome.exe',
    'chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing',
    'chrome-mac/Chromium.app/Contents/MacOS/Chromium'];
  for (const cache of caches) {
    if (!fs.existsSync(cache)) continue;
    const builds = fs.readdirSync(cache).filter(d => /^chromium-\d+$/.test(d)).sort((a, b) => Number(b.split('-')[1]) - Number(a.split('-')[1]));
    for (const b of builds) for (const e of exes) {
      const exe = path.join(cache, b, e);
      if (fs.existsSync(exe)) return exe;
    }
  }
  throw new Error('No Chromium found for capture. Run `npx playwright-core install chromium`, or set CHROME_PATH to a Chrome/Chromium binary.');
}

/** Set to a directory to get a screenshot at every mark — the way to check a run without watching it. */
const DEBUG = process.env.DEMO_CAPTURE_DEBUG || '';
if (DEBUG) fs.mkdirSync(DEBUG, {recursive: true});

export const sleep = ms => new Promise(r => setTimeout(r, ms));
const ease = t => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);

const GPU = process.env.DEMO_CAPTURE_GPU === '0' ? []
  : ['--enable-gpu', '--ignore-gpu-blocklist', '--use-gl=angle', '--use-angle=gl-egl'];

/**
 * Starts the browser with a REAL device scale factor. (An emulated `deviceScaleFactor` renders sharp
 * screenshots but the screencast still arrives at 1x.)
 *   extension  path of an unpacked browser extension to load
 *   profile    directory of a browser profile to keep between runs (a signed-in session); default: throwaway
 *   headless   false to watch, or to let a person sign in
 */
export async function launch({extension = null, profile = null, headless = true, view = VIEW, scale = SCALE,
  locale = process.env.DEMO_LOCALE || 'en-US', timezoneId = process.env.DEMO_TIMEZONE || undefined, colorScheme = 'light'} = {}) {
  const args = ['--hide-scrollbars', '--force-color-profile=srgb', `--force-device-scale-factor=${scale}`,
    `--window-size=${view.width},${view.height + 87}`, ...GPU];
  if (extension) args.push(`--disable-extensions-except=${extension}`, `--load-extension=${extension}`);
  const dir = profile || fs.mkdtempSync(path.join(os.tmpdir(), 'demo-video-profile-'));
  const ctx = await chromium.launchPersistentContext(dir, {
    executablePath: chromePath(), headless, args, viewport: null, locale, timezoneId, colorScheme,
    // Playwright switches extensions off by default.
    ignoreDefaultArgs: extension ? ['--disable-extensions'] : [],
  });
  const page = ctx.pages()[0] || await ctx.newPage();
  await fitViewport(page, view);
  return {ctx, page, dir};
}

/** The window is sized from outside, so correct it until the page itself measures exactly `view`. */
export async function fitViewport(page, view = VIEW) {
  const cdp = await page.context().newCDPSession(page);
  for (let i = 0; i < 4; i++) {
    const inner = await page.evaluate(() => ({w: innerWidth, h: innerHeight}));
    if (inner.w === view.width && inner.h === view.height) break;
    const {windowId, bounds} = await cdp.send('Browser.getWindowForTarget');
    await cdp.send('Browser.setWindowBounds', {windowId, bounds: {
      width: bounds.width + view.width - inner.w, height: bounds.height + view.height - inner.h}});
    await sleep(250);
  }
  const inner = await page.evaluate(() => ({w: innerWidth, h: innerHeight, dpr: devicePixelRatio}));
  if (inner.w !== view.width || inner.h !== view.height) throw new Error(`Viewport is ${inner.w}x${inner.h}, wanted ${view.width}x${view.height}`);
  await cdp.detach().catch(() => {});
  return inner;
}

/** Call after navigation, before recording: network quiet, fonts loaded, no spell-check squiggles. */
export async function settle(page) {
  await page.waitForLoadState('networkidle').catch(() => {});
  await page.evaluate(() => document.fonts.ready);
  await page.evaluate(() => document.querySelectorAll('textarea, input, [contenteditable]').forEach(e => { e.spellcheck = false; }));
}

export class Recorder {
  /** `base` is only written to the log (shown as the address in the window's title bar). */
  constructor(page, name, {view = VIEW, scale = SCALE, slow = SLOW, base = BASE} = {}) {
    this.page = page; this.name = name; this.view = view; this.scale = scale; this.baseSlow = slow; this.base = base;
    this.segs = [{r: Date.now() / 1000, v: 0, slow}];
    this.frames = []; this.events = []; this.shots = 0; this.locked = null; this.onFrame = null;
    this.pos = {x: view.width / 2, y: view.height / 2};
    this.dir = fs.mkdtempSync(path.join(os.tmpdir(), `frames-${name}-`));
  }

  get slow() { return this.segs.at(-1).slow; }

  /** Scene time (seconds) of a wall-clock instant: wall time divided by the slow-motion factor then in force. */
  now(r = Date.now() / 1000) {
    let seg = this.segs[0];
    for (const s of this.segs) if (s.r <= r) seg = s;
    return seg.v + Math.max(0, r - seg.r) / seg.slow;
  }

  async setSlow(slow) {
    const r = Date.now() / 1000;
    this.segs.push({r, v: this.now(r), slow});
    await this.cdp.send('Animation.setPlaybackRate', {playbackRate: 1 / slow}).catch(() => {});
  }

  /** Run `fn` at true speed — for anything whose duration is the server's, not ours. */
  async realtime(fn) {
    await this.setSlow(1);
    try { return await fn(); } finally { await this.setSlow(this.baseSlow); }
  }

  /** Pause for `ms` of scene time. */
  wait(ms) { return sleep(ms * this.slow); }

  async start() {
    this.cdp = await this.page.context().newCDPSession(this.page);
    this.cdp.on('Page.screencastFrame', f => {
      // An app that animates continuously (a drifting background) repaints all the time: during a real-time
      // wait that is ~200 frames per second of footage, gigabytes per minute. The footage is 30 fps, so keep
      // at most one frame per output frame (frame-locked scroll steps are always kept).
      const v = this.locked ?? this.now(f.metadata.timestamp);
      if (this.locked == null && this.lastV != null && v - this.lastV < 1 / FPS) {
        this.onFrame?.();
        this.cdp.send('Page.screencastFrameAck', {sessionId: f.sessionId}).catch(() => {});
        return;
      }
      this.lastV = v;
      const file = path.join(this.dir, `f${String(this.frames.length).padStart(6, '0')}.jpg`);
      fs.writeFileSync(file, Buffer.from(f.data, 'base64'));
      this.frames.push({file, t: f.metadata.timestamp, v: this.locked});
      this.onFrame?.();
      this.cdp.send('Page.screencastFrameAck', {sessionId: f.sessionId}).catch(() => {});
    });
    await this.cdp.send('Animation.enable');
    await this.cdp.send('Animation.setPlaybackRate', {playbackRate: 1 / this.slow});
    await this.cdp.send('Page.startScreencast', {
      format: 'jpeg', quality: 94, everyNthFrame: 1, maxWidth: this.view.width * this.scale, maxHeight: this.view.height * this.scale,
    });
    await this.page.mouse.move(this.pos.x, this.pos.y);
    this.log('cursor', {...this.pos});
    await this.wait(300);
  }

  log(type, data = {}) { this.events.push({type, t: this.now(), ...data}); }

  /**
   * Named moment, optionally with the rectangle of what the camera should look at (selector, locator,
   * rectangle or function). The rectangle is in viewport coordinates AT THIS MOMENT: mark again after
   * the page scrolls or re-lays out.
   */
  async mark(name, target = null, extra = {}) {
    let rect = null;
    if (target) rect = await this.rect(target);
    this.log('mark', {name, rect, ...extra});
    if (DEBUG) await this.page.screenshot({path: path.join(DEBUG, `${this.name}-${String(this.shots++).padStart(2, '0')}-${name}.jpg`), type: 'jpeg', quality: 70, scale: 'css'}).catch(() => {});
    return rect;
  }

  async rect(target) {
    if (typeof target === 'function') return target();
    if (target && typeof target.x === 'number') return target;
    const loc = typeof target === 'string' ? this.page.locator(target).first() : target;
    const b = await loc.boundingBox();
    return b ? {x: b.x, y: b.y, w: b.width, h: b.height} : null;
  }

  /** Hand-like move: eased, slightly arced, sampled continuously so hover states are real. */
  async moveTo(x, y, ms = null) {
    const from = {...this.pos}, dist = Math.hypot(x - from.x, y - from.y);
    if (dist < 1) return;
    const dur = (ms ?? Math.min(1100, 320 + dist * 0.9)) * this.slow;
    const bow = Math.min(40, dist * 0.08) * (x > from.x ? -1 : 1);
    const nx = -(y - from.y) / dist, ny = (x - from.x) / dist;
    const t0 = Date.now();
    for (;;) {
      const p = Math.min(1, (Date.now() - t0) / dur), e = ease(p), arc = Math.sin(Math.PI * e) * bow;
      this.pos = {x: from.x + (x - from.x) * e + nx * arc, y: from.y + (y - from.y) * e + ny * arc};
      await this.page.mouse.move(this.pos.x, this.pos.y);
      this.log('cursor', {...this.pos});
      if (p >= 1) break;
      await sleep(12);
    }
  }

  /** `fx`, `fy`: where inside the rectangle to aim, as fractions (0.5, 0.5 = centre). */
  async moveToRect(r, {fx = 0.5, fy = 0.5, ms = null} = {}) {
    await this.moveTo(r.x + r.w * fx, r.y + r.h * fy, ms);
  }

  async click({pause = 140} = {}) {
    await this.wait(pause);
    this.log('click', {...this.pos});
    await this.page.mouse.down(); await this.wait(70); await this.page.mouse.up();
  }

  async clickOn(target, opts = {}) {
    const r = await this.rect(target);
    if (!r) throw new Error(`Nothing to click: ${target}`);
    await this.moveToRect(r, opts);
    await this.click(opts);
    return r;
  }

  /** Typing with uneven key timing; the text really goes through the keyboard. Logs `type-start` / `type-end`. */
  async type(text, {cps = 26} = {}) {
    this.log('mark', {name: 'type-start', text});
    for (const ch of text) {
      await this.page.keyboard.type(ch);
      const base = 1000 / cps;
      await this.wait(base * (ch === ' ' ? 1.5 : 0.55 + Math.random() * 0.9));
    }
    this.log('mark', {name: 'type-end'});
  }

  /** Resolves when the next screencast frame arrives (or after `timeout` ms if the page did not repaint). */
  nextFrame(timeout = 800) {
    return new Promise(resolve => {
      const timer = setTimeout(resolve, timeout);
      this.onFrame = () => { clearTimeout(timer); this.onFrame = null; resolve(); };
    });
  }

  /**
   * Scroll the page in exact steps, one captured frame per step. A full-page repaint at this resolution
   * takes far longer than a frame, so scene time is assigned per step instead of being measured.
   * Logs `scroll-start` and `scrolled`.
   */
  async scrollBy(dy, ms = 700, el = null) {
    const steps = Math.max(2, Math.round(ms / 1000 * FPS)), v0 = this.now();
    this.log('mark', {name: 'scroll-start', dy});
    // `el`: selector of an inner scroll container (apps whose page scrolls inside a div, not the window)
    const y0 = await this.page.evaluate(sel => (sel ? document.querySelector(sel).scrollTop : window.scrollY), el);
    for (let i = 1; i <= steps; i++) {
      const got = this.nextFrame();
      this.locked = v0 + (i / steps) * ms / 1000;
      await this.page.evaluate(([sel, y]) => (sel ? document.querySelector(sel) : window).scrollTo({top: y, behavior: 'instant'}), [el, y0 + dy * ease(i / steps)]);
      await got;
    }
    await sleep(120);
    this.locked = null;
    this.segs.push({r: Date.now() / 1000, v: v0 + ms / 1000, slow: this.slow});
    await this.page.mouse.move(this.pos.x, this.pos.y);  // hover state for the content now under the cursor
    this.log('mark', {name: 'scrolled', dy});
  }

  /** Wheel over whatever is under the cursor (an inner scroll area); small repaints keep up in slow motion. Logs `wheeled`. */
  async wheel(dy, ms = 600) {
    const t0 = Date.now(), dur = ms * this.slow;
    let done = 0;
    for (;;) {
      const p = Math.min(1, (Date.now() - t0) / dur), target = dy * ease(p), d = target - done;
      done = target;
      await this.page.mouse.wheel(0, d);
      if (p >= 1) break;
      await sleep(30);
    }
    this.log('mark', {name: 'wheeled', dy});
  }

  async stop() {
    await this.wait(400);
    await this.cdp.send('Page.stopScreencast').catch(() => {});
    await sleep(300);
    if (this.frames.length < 2) throw new Error(`${this.name}: only ${this.frames.length} frames captured`);
    fs.mkdirSync(OUT, {recursive: true});
    for (const f of this.frames) f.t = f.v ?? this.now(f.t);
    this.frames.sort((a, b) => a.t - b.t);
    const t0 = this.frames[0].t, end = Math.max(this.frames.at(-1).t, this.now());
    // One still per screencast frame, held until the next one: the page only repaints when it changes.
    const list = this.frames.map((f, i) => {
      const next = i + 1 < this.frames.length ? this.frames[i + 1].t : end + 1 / FPS;
      return `file '${f.file.replace(/\\/g, '/')}'\nduration ${Math.max(0.001, next - f.t).toFixed(4)}`;
    }).join('\n') + `\nfile '${this.frames.at(-1).file.replace(/\\/g, '/')}'\n`;
    const listFile = path.join(this.dir, 'frames.txt');
    fs.writeFileSync(listFile, list);
    const mp4 = path.join(OUT, `${this.name}.mp4`);
    // -g FPS: a keyframe every second, so the composition can seek into any clip cheaply.
    const r = spawnSync('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', listFile,
      '-vf', `fps=${FPS},scale=trunc(iw/2)*2:trunc(ih/2)*2:flags=lanczos`, '-c:v', 'libx264', '-preset', 'slow', '-crf', '15',
      '-g', String(FPS), '-pix_fmt', 'yuv420p', '-movflags', '+faststart', mp4], {encoding: 'utf8'});
    if (r.error) throw new Error(`ffmpeg could not be started: ${r.error.message}`);
    if (r.status !== 0) throw new Error(`ffmpeg failed: ${r.stderr}`);
    const meta = {
      name: this.name, video: `captures/${this.name}.mp4`, fps: FPS, duration: +(end - t0).toFixed(3),
      view: this.view, scale: this.scale, slow: this.baseSlow, frames: this.frames.length, capturedAt: new Date().toISOString(), base: this.base,
      events: this.events.map(e => ({...e, t: +(e.t - t0).toFixed(3)})),
    };
    fs.writeFileSync(path.join(OUT, `${this.name}.json`), JSON.stringify(meta, null, 1));
    fs.rmSync(this.dir, {recursive: true, force: true});
    const density = (this.frames.length / meta.duration).toFixed(1);
    console.log(`${this.name}: ${meta.duration}s of scene time, ${this.frames.length} frames (~${density} per scene second) → ${path.relative(ROOT, mp4)}`);
    return meta;
  }
}
