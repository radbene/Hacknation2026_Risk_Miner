// The parts of the video that are not footage: opening, section cards, closing.
import React from 'react';
import {After, Appear, Stage, Typed, Window} from '../chrome';
import {COPY} from '../copy';
import {C, DISPLAY, FPS, H, LOOK, MONO, PIXEL, W} from '../theme';

/** The app's accent under page titles: three stepped blocks (brand, ink, amber). */
const TitleBlocks: React.FC<{scale?: number}> = ({scale = 1}) => (
  <div style={{display: 'flex', gap: 3 * scale, marginTop: 14 * scale}}>
    <i style={{display: 'block', height: 6 * scale, width: 40 * scale, background: C.accent}} />
    <i style={{display: 'block', height: 6 * scale, width: 12 * scale, background: C.ink}} />
    <i style={{display: 'block', height: 6 * scale, width: 6 * scale, background: C.amber}} />
  </div>
);

export const INTRO_FRAMES = Math.round(5.4 * FPS);
export const CARD_FRAMES = Math.round(3.2 * FPS);
export const OUTRO_FRAMES = Math.round(6.5 * FPS);

export const Intro: React.FC = () => (
  <Stage>
    <div style={{position: 'absolute', left: 170, top: 300, width: 1500}}>
      <After frame={4}><div style={{font: `500 24px ${MONO}`, color: C.muted, letterSpacing: '0.06em', textTransform: 'uppercase'}}>{COPY.intro.kicker}</div></After>
      <div style={{font: `700 150px/1.05 ${PIXEL}`, color: C.accent, letterSpacing: '0.01em', whiteSpace: 'nowrap', marginTop: 10}}>
        <Typed text={COPY.brand} start={10} cps={16} />&nbsp;
      </div>
      <After frame={44}><TitleBlocks scale={2} /></After>
      <After frame={56}><div style={{font: `700 52px ${DISPLAY}`, letterSpacing: '-0.02em', marginTop: 30}}>{COPY.intro.lead}</div></After>
      <After frame={84}><div style={{fontSize: 30, color: C.muted, marginTop: 14}}>{COPY.intro.sub}</div></After>
      <div style={{display: 'flex', gap: 18, marginTop: 50}}>
        {COPY.intro.chips.map((name, i) => (
          <After key={name} frame={108 + i * 12}>
            <div style={{display: 'flex', alignItems: 'center', gap: 14, padding: '14px 24px', background: C.panel, color: C.ink,
              border: `${LOOK.border}px solid ${C.ink}`, boxShadow: LOOK.shadow, font: `600 27px ${DISPLAY}`}}>
              <span style={{font: `400 20px ${PIXEL}`, color: C.accent}}>0{i + 1}</span>{name}
            </div>
          </After>
        ))}
      </div>
    </div>
  </Stage>
);

export const Card: React.FC<{no: string; title: string; sub: string}> = ({no, title, sub}) => {
  const rect = {x: (W - 1180) / 2, y: (H - 440) / 2, w: 1180, h: 440};
  return (
    <Stage>
      <Appear>
        <Window rect={rect} title={COPY.brand}>
          <div style={{display: 'flex', alignItems: 'center', gap: 48, padding: '0 64px', height: '100%'}}>
            <div style={{width: 180, height: 180, borderRadius: LOOK.radius * 1.5, background: C.accent, color: C.onAccent, display: 'grid', placeItems: 'center',
              font: `700 92px/1 ${PIXEL}`, flexShrink: 0, border: `${LOOK.border}px solid ${C.ink}`, boxShadow: LOOK.shadow}}>{no}</div>
            <div>
              <div style={{font: `700 92px/1.05 ${DISPLAY}`, letterSpacing: '-0.03em'}}><Typed text={title} start={20} cps={18} caret={false} />&nbsp;</div>
              <TitleBlocks scale={1.6} />
              <After frame={70}><div style={{fontSize: 34, marginTop: 18, color: C.muted, letterSpacing: '-0.015em'}}>{sub}</div></After>
            </div>
          </div>
        </Window>
      </Appear>
    </Stage>
  );
};

export const Outro: React.FC = () => {
  const O = COPY.outro;
  const rect = {x: 1010, y: 290, w: 760, h: 110 * O.rows.length + 46 + LOOK.border * 2};
  return (
    <Stage>
      <div style={{position: 'absolute', left: 150, top: 290, width: 800}}>
        <div style={{font: `400 34px ${PIXEL}`, color: C.accent, marginBottom: 22}}>{COPY.brand}</div>
        <div style={{font: `700 74px/1.12 ${DISPLAY}`, color: C.accent, letterSpacing: '-0.035em', whiteSpace: 'nowrap'}}>
          <Typed text={O.title} start={8} cps={22} caret={false} /><br />
          <Typed text={O.title2} start={8 + Math.round((O.title.length / 22) * FPS)} cps={22} caret={false} />&nbsp;
        </div>
        <After frame={140}>
          <div style={{background: C.panel, border: `${LOOK.border}px solid ${C.line}`, borderRadius: LOOK.radius, padding: '16px 22px', marginTop: 40,
            fontSize: 24, lineHeight: 1.4, color: C.muted}}>{O.note}</div>
        </After>
      </div>
      <Appear delay={30}>
        <Window rect={rect} title={COPY.brand}>
          {O.rows.map(([name, what], i) => (
            <After key={name} frame={60 + i * 20}>
              <div style={{display: 'flex', alignItems: 'center', gap: 26, padding: '0 32px', height: 110, boxSizing: 'border-box',
                borderBottom: i < O.rows.length - 1 ? `1px solid ${C.line}` : 'none'}}>
                <span style={{font: `400 36px ${PIXEL}`, color: C.accent, width: 64}}>0{i + 1}</span>
                <span>
                  <span style={{display: 'block', font: `600 36px ${DISPLAY}`}}>{name}</span>
                  <span style={{display: 'block', fontSize: 23, color: C.muted, marginTop: 4}}>{what}</span>
                </span>
              </div>
            </After>
          ))}
        </Window>
      </Appear>
    </Stage>
  );
};
