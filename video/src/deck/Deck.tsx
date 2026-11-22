// The RISK MINER presentation as a video: the ten slides of "RISK MINER – prezentacja.pdf", in the app's look,
// with pieces of the real recordings in place of screenshots.
// Motion follows prompt_prezentacja_przejscia.md: every slide leaves by cross-fade; the slide header does not
// move; content blocks rise 28 px while fading in (520 ms, 110 ms apart, in reading order).
import React from 'react';
import {AbsoluteFill, Easing, interpolate, Sequence, useCurrentFrame} from 'remotion';
import analizaJson from '../../public/captures/analiza.json';
import bazaJson from '../../public/captures/baza.json';
import ekspertJson from '../../public/captures/ekspert.json';
import podobneJson from '../../public/captures/podobne.json';
import {at, part, rectOf, union, type Capture} from '../capture';
import {Stage} from '../chrome';
import {C, DISPLAY, FPS, MONO, PIXEL} from '../theme';
import {Clip} from './Clip';
import {D} from './copy';

const baza = bazaJson as unknown as Capture, ekspert = ekspertJson as unknown as Capture;
const analiza = analizaJson as unknown as Capture, podobne = podobneJson as unknown as Capture;

const FADE = Math.round(0.5 * FPS);          // cross-fade between slides
const RISE = Math.round(0.52 * FPS), STEP = 0.11 * FPS;
const X = 150, TOP = 112, CONTENT = 318, RIGHT = 1770;

/** A content block that rises into place; `i` is its position in reading order. */
const Rise: React.FC<{i: number; children: React.ReactNode; style?: React.CSSProperties}> = ({i, children, style}) => {
  const f = useCurrentFrame() - i * STEP;
  const p = interpolate(f, [0, RISE], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.quad)});
  return <div style={{opacity: p, transform: `translateY(${(1 - p) * 28}px)`, ...style}}>{children}</div>;
};

const Blocks: React.FC<{on?: string}> = ({on}) => (
  <div style={{display: 'flex', gap: 4, marginTop: 16}}>
    <i style={{display: 'block', height: 8, width: 52, background: on ?? C.accent}} />
    <i style={{display: 'block', height: 8, width: 16, background: on ? '#fff' : C.ink}} />
    <i style={{display: 'block', height: 8, width: 8, background: C.amber}} />
  </div>
);

/** The slide header: never animated, same place on every slide, so the cross-fade does not make it jump. */
const Header: React.FC<{kicker: string; title: string; no: number}> = ({kicker, title, no}) => (
  <>
    <div style={{position: 'absolute', left: X, top: TOP}}>
      <div style={{font: `600 22px ${MONO}`, color: C.accent, letterSpacing: '0.08em', textTransform: 'uppercase'}}>{kicker}</div>
      <div style={{font: `700 66px/1.1 ${DISPLAY}`, letterSpacing: '-0.025em', marginTop: 10, whiteSpace: 'nowrap'}}>{title}</div>
      <Blocks />
    </div>
    <PageNo no={no} />
  </>
);
const PageNo: React.FC<{no: number; color?: string}> = ({no, color = C.muted}) => (
  <div style={{position: 'absolute', right: 150, bottom: 56, font: `500 20px ${MONO}`, color}}>{String(no).padStart(2, '0')} / 10</div>
);
const Footer: React.FC = () => (
  <div style={{position: 'absolute', left: X, bottom: 56, font: `500 20px ${MONO}`, color: C.muted}}>{D.repo}</div>
);

const Card: React.FC<{no?: string; title: string; children?: React.ReactNode; w: number; h: number}> = ({no, title, children, w, h}) => (
  <div style={{width: w, height: h, boxSizing: 'border-box', padding: '26px 28px', background: C.panel, border: `2px solid ${C.ink}`,
    boxShadow: '8px 8px 0 0 #121212'}}>
    {no ? <div style={{font: `400 30px ${PIXEL}`, color: C.accent, marginBottom: 14}}>{no}</div> : null}
    <div style={{font: `700 33px/1.2 ${DISPLAY}`, letterSpacing: '-0.01em'}}>{title}</div>
    <div style={{fontSize: 25, lineHeight: 1.42, color: '#3b3933', marginTop: 14}}>{children}</div>
  </div>
);
const Big: React.FC<{n: string; label: string; size?: number}> = ({n, label, size = 92}) => (
  <div>
    <div style={{font: `700 ${size}px/1 ${DISPLAY}`, color: C.accent, letterSpacing: '-0.03em'}}>{n}</div>
    <div style={{fontSize: 25, lineHeight: 1.35, marginTop: 10, color: C.ink}}>{label}</div>
  </div>
);
const P: React.FC<{children: React.ReactNode; size?: number; muted?: boolean; w?: number}> = ({children, size = 30, muted, w}) => (
  <div style={{fontSize: size, lineHeight: 1.42, color: muted ? C.muted : C.ink, width: w}}>{children}</div>
);
const Tag: React.FC<{color: string; children: React.ReactNode}> = ({color, children}) => (
  <span style={{display: 'inline-block', font: `500 22px ${MONO}`, color, border: `2px solid ${color}`, padding: '4px 12px',
    background: `${color}12`}}>{children}</span>
);

// ------------------------------------------------------------------ the slides
const S = D.slides;

const Title: React.FC = () => {
  const m = rectOf(analiza, 'mining');
  return (
    <Stage>
      <div style={{position: 'absolute', left: X, top: 210, width: 860}}>
        <div style={{font: `600 22px ${MONO}`, color: C.accent, letterSpacing: '0.08em', textTransform: 'uppercase'}}>{S.title.kicker}</div>
        <div style={{font: `700 150px/1.02 ${PIXEL}`, color: C.accent, marginTop: 22}}>RISK<br />MINER</div>
        <Blocks />
        <Rise i={0}><div style={{font: `600 40px/1.3 ${DISPLAY}`, marginTop: 40, letterSpacing: '-0.015em'}}>{S.title.lead}</div></Rise>
        <Rise i={1}><div style={{font: `500 22px ${MONO}`, color: C.muted, marginTop: 26}}>{S.title.pilot}</div></Rise>
      </div>
      <Rise i={0} style={{position: 'absolute', left: 1070, top: 230}}>
        <Clip cap={analiza} from={at(analiza, 'mining')} to={at(analiza, 'result') - 1.2} rect={part(m, 0, 0.1, 1, 1)}
          w={700} cursor={false} />
      </Rise>
      <Footer />
    </Stage>
  );
};

const Problem: React.FC = () => (
  <AbsoluteFill style={{background: C.accent, color: '#fff', fontFamily: DISPLAY}}>
    <div style={{position: 'absolute', left: X, top: TOP}}>
      <div style={{font: `600 22px ${MONO}`, letterSpacing: '0.08em', textTransform: 'uppercase', opacity: 0.85}}>{S.problem.kicker}</div>
    </div>
    <div style={{position: 'absolute', left: X, top: 300, width: 1300}}>
      <Rise i={0}><div style={{font: `700 120px/1.02 ${DISPLAY}`, letterSpacing: '-0.035em'}}>{S.problem.head}</div></Rise>
      <Rise i={2}><div style={{fontSize: 34, lineHeight: 1.45, marginTop: 44, width: 1180}}>{S.problem.body}</div></Rise>
    </div>
    <div style={{position: 'absolute', left: X, bottom: 56, font: `500 20px ${MONO}`, opacity: 0.8}}>{S.problem.source}</div>
    <PageNo no={2} color="rgba(255,255,255,.8)" />
  </AbsoluteFill>
);

const Solution: React.FC = () => (
  <Stage>
    <Header kicker={S.solution.kicker} title={S.solution.title} no={3} />
    <div style={{position: 'absolute', left: X, top: CONTENT + 20, display: 'flex', gap: 46}}>
      {S.solution.cards.map(([t, b], i) => <Rise key={t} i={i}><Card no={String(i + 1)} title={t} w={510} h={470}>{b}</Card></Rise>)}
    </div>
  </Stage>
);

const PathA: React.FC = () => (
  <Stage>
    <Header kicker={S.pathA.kicker} title={S.pathA.title} no={4} />
    <Rise i={0} style={{position: 'absolute', left: X, top: CONTENT + 10, display: 'flex', alignItems: 'center', gap: 18}}>
      {S.pathA.steps.map(([t, b], i) => (
        <React.Fragment key={t}>
          {i ? <span style={{font: `700 34px ${DISPLAY}`, color: C.accent}}>→</span> : null}
          <div style={{width: 268, height: 230, boxSizing: 'border-box', padding: '20px 20px', background: C.panel, border: `2px solid ${C.ink}`,
            boxShadow: '6px 6px 0 0 #121212'}}>
            <div style={{font: `700 28px/1.2 ${DISPLAY}`}}>{t}</div>
            <div style={{fontSize: 22, lineHeight: 1.4, color: '#3b3933', marginTop: 10}}>{b}</div>
          </div>
        </React.Fragment>
      ))}
    </Rise>
    <div style={{position: 'absolute', left: X, top: CONTENT + 300, display: 'flex', gap: 120}}>
      {S.pathA.numbers.map(([n, l], i) => <Rise key={l} i={i + 1}><Big n={n} label={l} size={84} /></Rise>)}
    </div>
    <Rise i={5} style={{position: 'absolute', left: X, top: CONTENT + 470, width: 1500}}><P size={24} muted>{S.pathA.note}</P></Rise>
  </Stage>
);

const Linking: React.FC = () => (
  <Stage>
    <Header kicker={S.linking.kicker} title={S.linking.title} no={5} />
    <div style={{position: 'absolute', left: X, top: CONTENT + 10, width: 560}}>
      <Rise i={1}><Big n="22/22" label={S.linking.n1} /></Rise>
      <Rise i={2} style={{marginTop: 40}}><Big n="1,0" label={S.linking.n2} /></Rise>
      <Rise i={3} style={{marginTop: 40}}><P size={25} muted>{S.linking.note}</P></Rise>
    </div>
    <Rise i={0} style={{position: 'absolute', left: 790, top: CONTENT + 20}}>
      <Clip cap={baza} from={at(baza, 'link') - 0.1} to={at(baza, 'up') - 0.6} rect={rectOf(baza, 'link')} w={980} />
    </Rise>
  </Stage>
);

const Source: React.FC = () => {
  const quote = union(rectOf(baza, 'highlight'), part(rectOf(baza, 'source'), 0.27, 0.42, 0.75, 0.9));
  return (
    <Stage>
      <Header kicker={S.source.kicker} title={S.source.title} no={6} />
      <div style={{position: 'absolute', left: X, top: CONTENT + 20, width: 640}}>
        <Rise i={1}><P>{S.source.p1}</P></Rise>
        <Rise i={2} style={{marginTop: 26}}><P>{S.source.p2}</P></Rise>
        <Rise i={3} style={{marginTop: 26}}><P size={24} muted>{S.source.p3}</P></Rise>
      </div>
      <Rise i={0} style={{position: 'absolute', left: 870, top: CONTENT + 20}}>
        <Clip cap={baza} from={at(baza, 'source')} to={baza.duration - 0.3} rect={quote} w={900} />
      </Rise>
    </Stage>
  );
};

const Expert: React.FC = () => (
  <Stage>
    <Header kicker={S.expert.kicker} title={S.expert.title} no={7} />
    <Rise i={0} style={{position: 'absolute', left: X, top: CONTENT + 20}}>
      <Clip cap={ekspert} from={at(ekspert, 'event') - 0.2} to={at(ekspert, 'accepted') + 3.6} rect={rectOf(ekspert, 'event')}
        w={1000} />
    </Rise>
    <Rise i={1} style={{position: 'absolute', left: 1220, top: CONTENT + 20, width: 550}}>
      <ul style={{margin: 0, paddingLeft: 26, fontSize: 26, lineHeight: 1.42}}>
        {S.expert.points.map(p => <li key={p} style={{marginBottom: 16}}>{p}</li>)}
      </ul>
    </Rise>
    <Rise i={2} style={{position: 'absolute', left: X, top: CONTENT + 380, width: 1000}}><P size={24} muted>{S.expert.note}</P></Rise>
  </Stage>
);

const PathB: React.FC = () => (
  <Stage>
    <Header kicker={S.pathB.kicker} title={S.pathB.title} no={8} />
    <Rise i={0} style={{position: 'absolute', left: X, top: CONTENT + 10}}>
      <Clip cap={analiza} from={at(analiza, 'result') - 0.1} to={at(analiza, 'flags') + 3.5} rect={{x: 0, y: 84, w: 1280, h: 636}}
        w={960} />
    </Rise>
    <div style={{position: 'absolute', left: 1200, top: CONTENT + 20, width: 570}}>
      {S.pathB.steps.map((s, i) => (
        <Rise key={s} i={i + 1} style={{display: 'flex', gap: 20, marginBottom: 34}}>
          <span style={{font: `400 34px ${PIXEL}`, color: C.accent, flexShrink: 0}}>{i + 1}</span>
          <P size={27}>{s}</P>
        </Rise>
      ))}
    </div>
  </Stage>
);

const Similar: React.FC = () => (
  <Stage>
    <Header kicker={S.similar.kicker} title={S.similar.title} no={9} />
    <Rise i={0} style={{position: 'absolute', left: X, top: CONTENT + 10}}>
      <Clip cap={podobne} from={at(podobne, 'grid')} to={podobne.duration - 0.3} rect={rectOf(podobne, 'grid')} w={1000} />
    </Rise>
    <div style={{position: 'absolute', left: 1230, top: CONTENT + 20, width: 540}}>
      {S.similar.labels.map(([tag, color, text], i) => (
        <Rise key={tag} i={i + 1} style={{marginBottom: 26}}>
          <Tag color={color}>{tag}</Tag>
          <P size={24}>{text}</P>
        </Rise>
      ))}
    </div>
  </Stage>
);

const Rollout: React.FC = () => (
  <Stage>
    <Header kicker={S.rollout.kicker} title={S.rollout.title} no={10} />
    <div style={{position: 'absolute', left: X, top: CONTENT + 20, display: 'flex', gap: 46}}>
      {S.rollout.cards.map(([t, items], i) => (
        <Rise key={t} i={i}>
          <Card title={t} w={510} h={440}>
            {items.map(x => <div key={x} style={{marginBottom: 14}}>{x}</div>)}
          </Card>
        </Rise>
      ))}
    </div>
    <Footer />
  </Stage>
);

// ------------------------------------------------------------------ running order, with cross-fades
const SLIDES: [string, React.FC, number][] = [
  ['01 tytuł', Title, 7], ['02 problem', Problem, 7], ['03 rozwiązanie', Solution, 7.5], ['04 ścieżka A', PathA, 8.5],
  ['05 łączenie', Linking, 8], ['06 źródło', Source, 9], ['07 ekspert', Expert, 10], ['08 ścieżka B', PathB, 11],
  ['09 podobieństwo', Similar, 10], ['10 wdrożenie', Rollout, 9],
];
const frames = SLIDES.map(s => Math.round(s[2] * FPS));
const starts = frames.map((_, i) => frames.slice(0, i).reduce((n, d) => n + d - FADE, 0));
export const DECK_FRAMES = starts[starts.length - 1] + frames[frames.length - 1];
export const DECK_MAP = SLIDES.map((s, i) => ({name: s[0], start: starts[i], frames: frames[i]}));

const FadeIn: React.FC<{first: boolean; children: React.ReactNode}> = ({first, children}) => {
  const f = useCurrentFrame();
  const o = first ? 1 : interpolate(f, [0, FADE], [0, 1], {extrapolateRight: 'clamp'});
  return <AbsoluteFill style={{opacity: o}}>{children}</AbsoluteFill>;
};

export const Deck: React.FC<{parts?: typeof DECK_MAP}> = () => (
  <AbsoluteFill style={{background: C.bg}}>
    {SLIDES.map(([name, Slide], i) => (
      <Sequence key={name} from={starts[i]} durationInFrames={frames[i]} premountFor={FPS}>
        <FadeIn first={i === 0}><Slide /></FadeIn>
      </Sequence>
    ))}
  </AbsoluteFill>
);
