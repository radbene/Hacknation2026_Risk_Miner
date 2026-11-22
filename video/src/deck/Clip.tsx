// A piece of a real recording placed on a slide: footage seconds `from`–`to`, cropped to `rect` (page
// coordinates of the recording, taken from its marks), in an ink-bordered box like the app's panels.
// When the slide outlasts the piece, the last frame is held.
import React from 'react';
import {Freeze, Sequence, staticFile, useCurrentFrame} from 'remotion';
import {Video} from '@remotion/media';
import {cursorTrack, type Capture, type Rect} from '../capture';
import {C, FPS, LOOK} from '../theme';

export const Clip: React.FC<{
  /** `h` defaults to the rectangle's own proportions, so nothing is cropped away. */
  cap: Capture; from: number; to: number; rect: Rect; w: number; h?: number; cursor?: boolean; start?: number;
}> = ({cap, from, to, rect, w, h: hh, cursor = true, start = 0}) => {
  const h = hh ?? Math.round(w * rect.h / rect.w);
  const f = useCurrentFrame() - start;
  const {width: vw, height: vh} = cap.view;
  const s = Math.max(w / rect.w, h / rect.h);
  const clamp = (v: number, lo: number, hi: number) => Math.min(hi, Math.max(lo, v));
  const left = clamp(w / 2 - (rect.x + rect.w / 2) * s, w - vw * s, 0);
  const top = clamp(h / 2 - (rect.y + rect.h / 2) * s, h - vh * s, 0);
  const len = Math.max(1, Math.round((to - from) * FPS));
  const track = React.useMemo(() => cursorTrack(cap), [cap]);
  const t = from + clamp(f, 0, len - 1) / FPS;
  const pos = cursor ? track.posAt(t) : null;
  const video = (
    <Video src={staticFile(cap.video)} muted trimBefore={Math.round(from * FPS)}
      style={{position: 'absolute', left, top, width: vw * s, height: vh * s}} />
  );
  return (
    <div style={{position: 'relative', width: w, height: h, overflow: 'hidden', background: C.panel,
      border: `${LOOK.border}px solid ${C.ink}`, boxShadow: '8px 8px 0 0 #121212'}}>
      {f < len ? <Sequence from={start} durationInFrames={len} premountFor={FPS}>{video}</Sequence>
        : <Freeze frame={len - 1}>{video}</Freeze>}
      {pos ? (
        <svg width={20} height={30} viewBox="0 0 13 20" style={{position: 'absolute', left: left + pos.x * s, top: top + pos.y * s,
          overflow: 'visible', transform: `scale(${Math.min(1.6, 0.9 * s)})`, transformOrigin: '0 0'}}>
          <path d="M1 1 L1 15 L4.5 11.8 L7 17.6 L9.4 16.6 L6.9 10.9 L11.6 10.9 Z" fill={C.ink} stroke="#fff" strokeWidth={1.3} strokeLinejoin="round" />
        </svg>
      ) : null}
    </div>
  );
};
