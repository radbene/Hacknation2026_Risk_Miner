import React from 'react';
import {Composition, staticFile} from 'remotion';
import {loadFont} from '@remotion/fonts';
import {Demo, DEMO_FRAMES, PART_MAP} from './Demo';
import {Deck, DECK_FRAMES, DECK_MAP} from './deck/Deck';
import {FPS, H, W} from './theme';

// The application's own fonts (OFL-1.1, copied from frontend/node_modules/@fontsource*): latin + latin-ext,
// so Polish diacritics render in the real face rather than a fallback.
const LATIN = 'U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD';
const LATIN_EXT = 'U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,U+0329,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF';
for (const [sub, range] of [['latin', LATIN], ['latin-ext', LATIN_EXT]] as const) {
  loadFont({family: 'Archivo', url: staticFile(`fonts/archivo-${sub}-wght-normal.woff2`), weight: '100 900', unicodeRange: range});
  loadFont({family: 'JetBrains Mono', url: staticFile(`fonts/jetbrains-mono-${sub}-wght-normal.woff2`), weight: '100 800', unicodeRange: range});
  for (const w of ['400', '700']) loadFont({family: 'Silkscreen', url: staticFile(`fonts/silkscreen-${sub}-${w}-normal.woff2`), weight: w, unicodeRange: range});
}

export const Root: React.FC = () => (
  <>
    <Composition id="Demo" component={Demo} durationInFrames={DEMO_FRAMES} fps={FPS} width={W} height={H}
      defaultProps={{parts: PART_MAP}} />
    <Composition id="Prezentacja" component={Deck} durationInFrames={DECK_FRAMES} fps={FPS} width={W} height={H}
      defaultProps={{parts: DECK_MAP}} />
  </>
);
