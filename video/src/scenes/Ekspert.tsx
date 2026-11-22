// Scene 2 – the expert: demo login → the review queue → one model proposal on a project card → accepted.
import React from 'react';
import json from '../../public/captures/ekspert.json';
import {at, clickAt, cutting, part, rectOf, timeline, union, type Capture, type Shot} from '../capture';
import {Appear, Captions, Stage} from '../chrome';
import {COPY} from '../copy';
import {Footage} from '../Footage';

const cap = json as unknown as Capture;
const T = COPY.ekspert;

const panel = clickAt(cap, 0), enter = clickAt(cap, 1), accept = clickAt(cap, 2);
const queue = at(cap, 'queue'), leave = at(cap, 'leave'), card = at(cap, 'card');
const event = at(cap, 'event'), accepted = at(cap, 'accepted');

// Leaving the queue for the project card is a change of subject (a page load): cut it, with a dip.
const tl = timeline(cutting(0.2, cap.duration - 0.3, [{from: leave + 0.1, to: card + 0.05}]));
export const EKSPERT_FRAMES = tl.frames;

const shots: Shot[] = [
  {t: 0},
  {t: panel + 0.25, rect: rectOf(cap, 'login'), maxZoom: 1.5},
  {t: enter + 0.3},
  {t: queue + 0.2, rect: union(rectOf(cap, 'queue'), rectOf(cap, 'queue-intro')), maxZoom: 1.5, pad: 0.04},
  {t: card + 0.05, cut: true},
  {t: event + 0.1, rect: rectOf(cap, 'event'), maxZoom: 1.6, pad: 0.04},
  {t: accepted + 0.15, rect: rectOf(cap, 'accepted'), maxZoom: 1.6, pad: 0.04},
];

const f = tl.frameOf;
const lines = [
  {from: f(panel - 0.2), to: f(enter + 0.4), text: T.login},
  {from: f(queue), to: f(leave), text: T.queue},
  {from: f(event), to: f(accept), text: T.proposal},
  {from: f(accepted), to: tl.frames, text: T.accepted},
];

const outlines = [
  {from: event + 0.6, to: accept, rect: part(rectOf(cap, 'actions'), 0, 0, 0.3, 1)},  // the buttons, not the whole row
  {from: accepted + 0.5, to: cap.duration, rect: rectOf(cap, 'accepted-status')},
];

export const Ekspert: React.FC = () => (
  <Stage>
    <Appear>
      <Footage capture={cap} tl={tl} shots={shots} outlines={outlines} title={T.window}
        right={cap.base ? new URL(cap.base).host : undefined} skipLabel={COPY.skipped} />
      <Captions lines={lines} tag={T.tag} />
    </Appear>
  </Stage>
);
