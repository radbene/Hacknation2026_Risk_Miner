// Scene 1 – the case base: Nowogard's project card → its BZP procedure with the conditions checked →
// an event with its cause → the original notice with the quoted point highlighted.
import React from 'react';
import json from '../../public/captures/baza.json';
import {at, clickAt, cutting, part, rectOf, timeline, union, type Capture, type Shot} from '../capture';
import {Appear, Captions, Stage} from '../chrome';
import {COPY} from '../copy';
import {Footage} from '../Footage';

const cap = json as unknown as Capture;
const T = COPY.baza;

const tabLinks = clickAt(cap, 0), tabEvents = clickAt(cap, 1), show = clickAt(cap, 2);
const link = at(cap, 'link'), up = at(cap, 'up'), event = at(cap, 'event');
const dialogOpen = at(cap, 'dialog-open'), source = at(cap, 'source');

// The only wait is the PDF loading in the source dialog: cut it if it took more than a second.
const tl = timeline(cutting(0.2, cap.duration - 0.3, [{from: dialogOpen + 0.5, to: source - 0.3, wait: true}]));
export const BAZA_FRAMES = tl.frames;

const reasons = union(rectOf(cap, 'link-head'), rectOf(cap, 'reasons'));
const ev = rectOf(cap, 'event');
// the highlighted point plus the section above it, so the camera stays clear of the dialog's bottom edge
const quote = union(rectOf(cap, 'highlight'), part(rectOf(cap, 'source'), 0.2, 0.45, 0.75, 0.8));
const shots: Shot[] = [
  {t: 0},
  {t: 0.5, rect: union(rectOf(cap, 'header'), part(rectOf(cap, 'tabs'), 0, 0, 0.6, 1)), maxZoom: 1.4},
  {t: tabLinks - 0.5},
  {t: link + 0.1, rect: reasons, maxZoom: 1.6, pad: 0.05},
  {t: up - 0.2},
  {t: event + 0.1, rect: ev, maxZoom: 1.6, pad: 0.04},
  {t: show - 0.4},
  {t: source - 0.3, cut: true},
  {t: source + 0.3, rect: quote, maxZoom: 1.7},
];

const f = tl.frameOf;
const lines = [
  {from: f(0.4), to: f(tabLinks), text: T.open},
  {from: f(tabLinks + 0.1), to: f(link + 0.6), text: T.link},
  {from: f(link + 0.6), to: f(up), text: T.reasons},
  {from: f(event), to: f(show), text: T.event},
  {from: f(show + 0.1), to: tl.frames, text: T.source},
];

const outlines = [
  {from: source + 0.8, to: cap.duration, rect: rectOf(cap, 'highlight')},
];

export const Baza: React.FC = () => (
  <Stage>
    <Appear>
      <Footage capture={cap} tl={tl} shots={shots} outlines={outlines} title={T.window}
        right={cap.base ? new URL(cap.base).host : undefined} skipLabel={COPY.skipped} />
      <Captions lines={lines} tag={T.tag} />
    </Appear>
  </Stage>
);
