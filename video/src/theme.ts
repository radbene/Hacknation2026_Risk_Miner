// The look of everything that is NOT footage. Take these values from the application being shown
// (its CSS variables, fonts, border and shadow style) so the video reads as part of the product.
// RISK MINER's "terminal on paper" look (frontend/src/index.css): paper, black ink, one electric-blue accent,
// square corners, 2-px ink borders with hard offset shadows, Silkscreen pixel display, JetBrains Mono labels.
export const C = {
  bg: '#f2f1ea',        // --color-paper
  dot: '#dcdad1',       // the app's drifting dot grid (ink at ~10%)
  panel: '#f8f7f2',     // --color-surface
  bar: '#f8f7f2',
  ink: '#121212',
  muted: '#6f6b60',     // slate-500
  line: '#121212',      // borders are ink
  accent: '#3d33f2',    // --color-brand
  accentSoft: '#e7e5ff',
  amber: '#f2a516',     // third block of the title accent
  onAccent: '#ffffff',
};
export const DISPLAY = '"Archivo", system-ui, sans-serif';
export const BODY = '"Archivo", system-ui, sans-serif';
export const PIXEL = '"Silkscreen", "JetBrains Mono", monospace';
export const MONO = '"JetBrains Mono", ui-monospace, monospace';

/** Shape language of windows and captions. */
export const LOOK = {
  border: 2,
  radius: 0,
  shadow: '6px 6px 0 0 #121212',
  stepped: false,
};

export const FPS = 60;
export const W = 1920;
export const H = 1080;

/**
 * Where recorded footage sits on the stage. The content area keeps the recording's 16:9 shape:
 * 1536x864 shows a 1280x720 page at 1.2x, and the recording is 2560x1440, so the camera can zoom to
 * 1.67x before a single pixel is upscaled.
 */
export const WIN = {x: 190, y: 34, bar: 46, border: LOOK.border, contentW: 1536, contentH: 864};
export const CAPTION = {x: 190, y: 968, w: 1536 + LOOK.border * 2, h: 80};

/** Screen-recording zoom: reaches 90% in about 0.3 s and settles without overshoot. */
export const ZOOM_SPRING = {stiffness: 205, damping: 33.3, mass: 1.5};

/** Frame used by stage furniture; footage, camera and cursor always stay smooth. */
export const tick = (frame: number) => (LOOK.stepped ? Math.floor(frame / 2) * 2 : frame);
