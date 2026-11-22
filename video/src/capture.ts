// Reads a recording made by capture/lib.mjs: the footage plus the log of what happened in it.
// Scenes are written against named marks and element rectangles from that log, so a re-recording with
// different timing or layout needs no changes here.
//
// Two clocks are in play. FOOTAGE TIME is seconds into a recording (what marks carry). COMPOSITION FRAMES are
// frames of the scene after cutting. `timeline()` converts between them: `tl.frameOf(seconds)`.
import {spring} from 'remotion';
import {FPS, ZOOM_SPRING} from './theme';

export type Rect = {x: number; y: number; w: number; h: number};
export type Ev = {type: string; t: number; x?: number; y?: number; name?: string; rect?: Rect | null; text?: string};
export type Capture = {
  name: string; video: string; fps: number; duration: number; view: {width: number; height: number};
  scale: number; base?: string; events: Ev[];
};

export function mark(c: Capture, name: string, nth = 0): Ev {
  const m = c.events.filter(e => e.type === 'mark' && e.name === name)[nth];
  if (!m) throw new Error(`Recording "${c.name}" has no mark "${name}" #${nth}. Re-record it or update the scene.`);
  return m;
}
export const at = (c: Capture, name: string, nth = 0) => mark(c, name, nth).t;
/** Whether the recording has this mark — for marks added to a capture script after the footage was made. */
export const has = (c: Capture, name: string, nth = 0) => c.events.filter(e => e.type === 'mark' && e.name === name).length > nth;
export function rectOf(c: Capture, name: string, nth = 0): Rect {
  const r = mark(c, name, nth).rect;
  if (!r) throw new Error(`Mark "${name}" in "${c.name}" has no rectangle.`);
  return r;
}
export function clickAt(c: Capture, nth: number): number {
  const k = c.events.filter(e => e.type === 'click')[nth];
  if (!k) throw new Error(`Recording "${c.name}" has no click #${nth}.`);
  return k.t;
}
/** Part of a rectangle, in fractions of its size. */
export const part = (r: Rect, x0: number, y0: number, x1: number, y1: number): Rect =>
  ({x: r.x + r.w * x0, y: r.y + r.h * y0, w: r.w * (x1 - x0), h: r.h * (y1 - y0)});
export function union(...rs: Rect[]): Rect {
  const x = Math.min(...rs.map(r => r.x)), y = Math.min(...rs.map(r => r.y));
  return {x, y, w: Math.max(...rs.map(r => r.x + r.w)) - x, h: Math.max(...rs.map(r => r.y + r.h)) - y};
}

// ---------------------------------------------------------------- timeline: which part of the footage plays when
export type Clip = {from: number; to: number; speed?: number; afterWait?: boolean};
export type Timeline = {
  /** `skipped`: seconds of waiting cut out before this clip. `soft`: the cut into this clip is a change of subject, shown with a short dip. */
  clips: {from: number; to: number; speed: number; start: number; frames: number; skipped: number; soft: boolean}[];
  frames: number;
  /** Footage time shown at a composition frame. */
  srcAt: (frame: number) => number;
  /** Composition frame at which a footage time is on screen (the next clip's start if it was cut out). */
  frameOf: (t: number) => number;
  /** Whether the video cuts (rather than plays on) at this composition frame. */
  cutsAt: (frame: number) => boolean;
};

export type Gap = {from: number; to: number; wait?: boolean};

/**
 * Footage from `from` to `to` without the `gaps`. A gap marked `wait` is time spent waiting for the server:
 * the clip after it reports the seconds skipped, so the video can say so. Gaps too short to be worth a cut
 * (a fast answer) are left in — the same scene works whether the server took one second or fifteen.
 * A gap that is not a wait is a change of subject: the footage dips to the stage colour across it, so the
 * picture never jumps between two unrelated screens.
 */
export function cutting(from: number, to: number, gaps: Gap[], minGap = 1): Clip[] {
  const clips: Clip[] = [];
  let at = from, afterWait = false;
  for (const g of [...gaps].sort((a, b) => a.from - b.from)) {
    if (g.to - g.from < minGap || g.from <= at || g.to >= to) continue;
    clips.push({from: at, to: g.from, afterWait});
    at = g.to; afterWait = !!g.wait;
  }
  clips.push({from: at, to, afterWait});
  return clips;
}

export function timeline(clips: Clip[]): Timeline {
  let start = 0;
  const out = clips.map((c, i) => {
    const speed = c.speed ?? 1, frames = Math.max(1, Math.round((c.to - c.from) / speed * FPS));
    const clip = {from: c.from, to: c.to, speed, start, frames, skipped: i && c.afterWait ? Math.max(0, c.from - clips[i - 1].to) : 0, soft: i > 0 && !c.afterWait};
    start += frames;
    return clip;
  });
  const srcAt = (frame: number) => {
    const c = out.find(k => frame < k.start + k.frames) ?? out[out.length - 1];
    return Math.min(c.to, c.from + Math.max(0, frame - c.start) / FPS * c.speed);
  };
  const frameOf = (t: number) => {
    for (const c of out) {
      if (t < c.from) return c.start;
      if (t <= c.to) return c.start + Math.round((t - c.from) / c.speed * FPS);
    }
    return start;
  };
  const cutsAt = (frame: number) => out.some((c, i) => i > 0 && c.start === frame);
  return {clips: out, frames: start, srcAt, frameOf, cutsAt};
}

// ---------------------------------------------------------------- camera
/**
 * Look at `rect` (page coordinates of the recording) from footage time `t` on; no rect = the whole page.
 * `maxZoom` caps how far in the camera goes (default 2), `pad` is the margin kept around the rect (default 0.16).
 * `cut`: if the video cuts at that moment, the camera is already there instead of travelling.
 */
export type Shot = {t: number; rect?: Rect | null; maxZoom?: number; pad?: number; cut?: boolean};
export type View = {cx: number; cy: number; z: number};

const clamp = (v: number, lo: number, hi: number) => Math.min(hi, Math.max(lo, v));

export function frame(shot: Shot, vw: number, vh: number): View {
  if (!shot.rect) return {cx: vw / 2, cy: vh / 2, z: 1};
  const pad = shot.pad ?? 0.16, r = shot.rect;
  const z = clamp(Math.min(vw / (r.w * (1 + pad)), vh / (r.h * (1 + pad))), 1, shot.maxZoom ?? 2);
  return {
    z,
    cx: clamp(r.x + r.w / 2, vw / 2 / z, vw - vw / 2 / z),
    cy: clamp(r.y + r.h / 2, vh / 2 / z, vh - vh / 2 / z),
  };
}

export function cameraAt(f: number, shots: Shot[], tl: Timeline, vw: number, vh: number): View {
  let v = frame(shots[0], vw, vh);
  for (const s of shots.slice(1)) {
    const f0 = tl.frameOf(s.t);
    if (f < f0) break;
    const target = frame(s, vw, vh);
    const p = s.cut && tl.cutsAt(f0) ? 1 : spring({frame: f - f0, fps: FPS, config: ZOOM_SPRING});
    v = {cx: v.cx + (target.cx - v.cx) * p, cy: v.cy + (target.cy - v.cy) * p, z: v.z + (target.z - v.z) * p};
  }
  return v;
}

// ---------------------------------------------------------------- cursor
export function cursorTrack(c: Capture) {
  const pts = c.events.filter(e => e.type === 'cursor' || e.type === 'click') as Required<Pick<Ev, 't' | 'x' | 'y'>>[];
  const clicks = c.events.filter(e => e.type === 'click').map(e => e.t);
  const posAt = (t: number) => {
    if (!pts.length) return null;
    let lo = 0, hi = pts.length - 1;
    if (t <= pts[0].t) return {x: pts[0].x, y: pts[0].y};
    if (t >= pts[hi].t) return {x: pts[hi].x, y: pts[hi].y};
    while (hi - lo > 1) { const mid = (lo + hi) >> 1; if (pts[mid].t <= t) lo = mid; else hi = mid; }
    const a = pts[lo], b = pts[hi], p = b.t > a.t ? (t - a.t) / (b.t - a.t) : 0;
    return {x: a.x + (b.x - a.x) * p, y: a.y + (b.y - a.y) * p};
  };
  /** Seconds since the most recent click at footage time `t` (Infinity if none yet). */
  const sinceClick = (t: number) => {
    let last = -Infinity;
    for (const k of clicks) if (k <= t) last = k;
    return t - last;
  };
  return {posAt, sinceClick};
}
