// Scene 3 – a new investment: example description → features read by the local model (Bielik) →
// risk analysis against completed contracts → summary, flags, exports.
import React from 'react';
import json from '../../public/captures/analiza.json';
import {at, clickAt, cutting, has, part, rectOf, timeline, union, type Capture, type Shot} from '../capture';
import {Appear, Captions, Stage} from '../chrome';
import {COPY} from '../copy';
import {Footage} from '../Footage';

const cap = json as unknown as Capture;
const T = COPY.analiza;

const insert = clickAt(cap, 0), extract = clickAt(cap, 1), analyse = clickAt(cap, 2);
const reading = at(cap, 'reading'), read = at(cap, 'read'), features = at(cap, 'features');
const mining = at(cap, 'mining'), result = at(cap, 'result');
const flagsAt = at(cap, 'flags'), up = at(cap, 'up'), exportsTop = at(cap, 'exports-top');

// Two real waits: the model reading the text and the calculation. Each is cut (and labelled) only if it
// lasted long enough; in the recording used, both were short and are shown in full.
const tl = timeline(cutting(0.2, cap.duration - 0.3, [
  {from: reading + 2.2, to: read - 0.2, wait: true},
  {from: mining + 3.2, to: result - 1.6, wait: true},
]));
export const ANALIZA_FRAMES = tl.frames;

const featRect = has(cap, 'questions')
  ? union(rectOf(cap, 'model-badge'), rectOf(cap, 'questions'))
  : part(rectOf(cap, 'features'), 0, 0, 1, 0.5);
const shots: Shot[] = [
  {t: 0},
  {t: insert - 0.4, rect: rectOf(cap, 'filled'), maxZoom: 1.5},
  {t: extract - 0.3, rect: union(rectOf(cap, 'reading'), part(rectOf(cap, 'filled'), 0, 0.6, 1, 1)), maxZoom: 1.6},
  {t: read - 0.2, cut: true},
  {t: features + 0.1, rect: featRect, maxZoom: 1.6},
  {t: analyse - 0.6},
  {t: mining + 0.1, rect: rectOf(cap, 'mining'), maxZoom: 1.5},
  {t: result - 0.3},
  {t: result + 0.4, rect: union(rectOf(cap, 'result'), rectOf(cap, 'summary')), maxZoom: 1.6, pad: 0.04},
  {t: flagsAt - 1.2},
  {t: flagsAt + 0.1, rect: union(rectOf(cap, 'flags-tab'), rectOf(cap, 'flags')), maxZoom: 1.6, pad: 0.04},
  {t: up - 0.2},
  {t: exportsTop + 0.1, rect: rectOf(cap, 'exports-top'), maxZoom: 1.5, pad: 0.25},
];

const f = tl.frameOf;
const lines = [
  {from: f(insert - 0.3), to: f(extract - 0.2), text: T.paste},
  {from: f(extract - 0.1), to: f(features + 1.6), text: T.reading},
  {from: f(features + 1.6), to: f(analyse), text: T.features},
  {from: f(analyse + 0.1), to: f(result), text: T.mining},
  {from: f(result + 0.2), to: f(flagsAt - 1.2), text: T.summary},
  {from: f(flagsAt - 0.2), to: f(up), text: T.flags},
  {from: f(exportsTop), to: tl.frames, text: T.exports},
];

const outlines = [
  {from: exportsTop + 0.6, to: cap.duration, rect: rectOf(cap, 'exports-top')},
];

export const Analiza: React.FC = () => (
  <Stage>
    <Appear>
      <Footage capture={cap} tl={tl} shots={shots} outlines={outlines} title={T.window}
        right={cap.base ? new URL(cap.base).host : undefined} skipLabel={COPY.skipped} />
      <Captions lines={lines} tag={T.tag} />
    </Appear>
  </Stage>
);
