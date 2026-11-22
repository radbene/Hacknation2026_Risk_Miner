// Stage furniture: background, window frame, captions. None of it is footage.
// This is the neutral version — restyle it to the product being shown (see docs/STYLE.md and
// examples/prawdowid/ for a strongly themed variant).
import React from 'react';
import {AbsoluteFill, spring, useCurrentFrame} from 'remotion';
import {BODY, C, CAPTION, DISPLAY, FPS, LOOK, MONO, PIXEL, tick} from './theme';
import type {Rect} from './capture';

export const Stage: React.FC<{children?: React.ReactNode}> = ({children}) => (
  <AbsoluteFill style={{
    backgroundColor: C.bg, backgroundImage: `radial-gradient(${C.dot} 1.4px, transparent 1.7px)`, backgroundSize: '22px 22px',
    fontFamily: BODY, color: C.ink,
  }}>{children}</AbsoluteFill>
);

/** Title bar of the app's own dialogs: a square box, the title, ink stripes, a square close box. */
export const TitleBar: React.FC<{title: string; right?: string; height?: number}> = ({title, right, height = 46}) => (
  <div style={{
    height, display: 'flex', alignItems: 'center', gap: 14, padding: '0 16px', boxSizing: 'border-box', flexShrink: 0,
    background: C.bar, borderBottom: `${LOOK.border}px solid ${C.ink}`, font: `700 19px ${MONO}`, color: C.ink,
  }}>
    <span style={{width: 16, height: 16, border: `2px solid ${C.ink}`, boxSizing: 'border-box', flexShrink: 0}} />
    <span style={{whiteSpace: 'nowrap'}}>{title}</span>
    <span style={{flex: 1, height: 14, background: `repeating-linear-gradient(to bottom, ${C.ink} 0 2px, transparent 2px 5px)`}} />
    {right ? <span style={{whiteSpace: 'nowrap', font: `500 16px ${MONO}`, color: C.ink, padding: '3px 10px', background: C.panel,
      border: `1.5px solid ${C.ink}`, textTransform: 'uppercase', letterSpacing: '0.04em'}}>{right}</span> : null}
    <span style={{width: 22, height: 22, border: `2px solid ${C.ink}`, boxSizing: 'border-box', flexShrink: 0, display: 'grid', placeItems: 'center',
      font: `700 15px ${MONO}`}}>×</span>
  </div>
);

export const Window: React.FC<{
  rect: Rect; title: string; right?: string; children?: React.ReactNode; bar?: number; body?: React.CSSProperties;
}> = ({rect, title, right, children, bar = 46, body}) => (
  <div style={{
    position: 'absolute', left: rect.x, top: rect.y, width: rect.w, height: rect.h, boxSizing: 'border-box', overflow: 'hidden',
    background: C.panel, border: `${LOOK.border}px solid ${C.line}`, borderRadius: LOOK.radius, boxShadow: LOOK.shadow,
    display: 'flex', flexDirection: 'column',
  }}>
    <TitleBar title={title} right={right} height={bar} />
    <div style={{flex: 1, position: 'relative', overflow: 'hidden', ...body}}>{children}</div>
  </div>
);

/** A scene's entrance: a short settle from slightly smaller and transparent. */
export const Appear: React.FC<{children: React.ReactNode; delay?: number}> = ({children, delay = 0}) => {
  const p = spring({frame: tick(useCurrentFrame()) - delay, fps: FPS, config: {damping: 200, stiffness: 180}});
  return <AbsoluteFill style={{opacity: p, transform: `scale(${0.965 + 0.035 * p})`}}>{children}</AbsoluteFill>;
};

/** Shows its children from a frame on (relative to the enclosing scene), fading in over a few frames. */
export const After: React.FC<{frame: number; children: React.ReactNode}> = ({frame, children}) => {
  const f = tick(useCurrentFrame()) - frame;
  if (f < 0) return null;
  const p = LOOK.stepped ? 1 : Math.min(1, f / 10);
  return <div style={{opacity: p, transform: `translateY(${(1 - p) * 10}px)`}}>{children}</div>;
};

/** Text that types itself. */
export const Typed: React.FC<{text: string; start?: number; cps?: number; caret?: boolean}> =
  ({text, start = 0, cps = 38, caret = true}) => {
    const f = useCurrentFrame() - start;
    const n = Math.max(0, Math.min(text.length, Math.floor((f / FPS) * cps)));
    const blink = Math.floor(f / (FPS / 2)) % 2 === 0;
    return (
      <span>
        {text.slice(0, n)}
        {caret ? <span style={{display: 'inline-block', width: '0.09em', height: '1em', marginLeft: '0.06em', verticalAlign: '-0.12em',
          background: n < text.length || blink ? 'currentColor' : 'transparent'}} /> : null}
      </span>
    );
  };

export type Line = {from: number; to: number; text: string};

/**
 * One caption at a time under the window; `from`/`to` are composition frames of the scene.
 * A caption must fit on one line: keep it under about 60 characters.
 */
export const Captions: React.FC<{lines: Line[]; tag: string}> = ({lines, tag}) => {
  const f = useCurrentFrame();
  const line = lines.find(l => f >= l.from && f < l.to);
  return (
    <div style={{
      position: 'absolute', left: CAPTION.x, top: CAPTION.y, width: CAPTION.w, height: CAPTION.h, boxSizing: 'border-box', overflow: 'hidden',
      background: C.panel, border: `${LOOK.border}px solid ${C.line}`, borderRadius: LOOK.radius, boxShadow: LOOK.shadow, display: 'flex', alignItems: 'center',
    }}>
      <div style={{alignSelf: 'stretch', display: 'flex', alignItems: 'center', padding: '0 24px', background: C.accent, color: C.onAccent,
        font: `400 21px ${PIXEL}`, whiteSpace: 'nowrap', letterSpacing: '0.02em', borderRight: `${LOOK.border}px solid ${C.ink}`}}>{tag}</div>
      <div style={{flex: 1, padding: '0 28px', font: `500 31px ${DISPLAY}`, letterSpacing: '-0.01em', whiteSpace: 'nowrap', overflow: 'hidden'}}>
        {line ? <Typed key={line.from} text={line.text} start={line.from} cps={46} /> : null}
      </div>
    </div>
  );
};
