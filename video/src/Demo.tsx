// The running order. Add a [node, frames] pair per part; the total length follows.
import React from 'react';
import {Series} from 'remotion';
import {COPY} from './copy';
import {Analiza, ANALIZA_FRAMES} from './scenes/Analiza';
import {Baza, BAZA_FRAMES} from './scenes/Baza';
import {Card, CARD_FRAMES, Intro, INTRO_FRAMES, Outro, OUTRO_FRAMES} from './scenes/Cards';
import {Ekspert, EKSPERT_FRAMES} from './scenes/Ekspert';

const PARTS: [name: string, node: React.ReactNode, frames: number][] = [
  ['intro', <Intro />, INTRO_FRAMES],
  ['card 01', <Card {...COPY.baza.card} />, CARD_FRAMES],
  ['baza', <Baza />, BAZA_FRAMES],
  ['card 02', <Card {...COPY.ekspert.card} />, CARD_FRAMES],
  ['ekspert', <Ekspert />, EKSPERT_FRAMES],
  ['card 03', <Card {...COPY.analiza.card} />, CARD_FRAMES],
  ['analiza', <Analiza />, ANALIZA_FRAMES],
  ['outro', <Outro />, OUTRO_FRAMES],
];
export const DEMO_FRAMES = PARTS.reduce((n, p) => n + p[2], 0);
/** Name, first frame and length of each part. Passed as a prop only so the tools can print a map of the video. */
export const PART_MAP = PARTS.map((p, i) => ({name: p[0], start: PARTS.slice(0, i).reduce((n, q) => n + q[2], 0), frames: p[2]}));

export const Demo: React.FC<{parts?: typeof PART_MAP}> = () => (
  <Series>
    {PARTS.map(([name, node, frames]) => (
      <Series.Sequence key={name} durationInFrames={frames}>{node}</Series.Sequence>
    ))}
  </Series>
);
