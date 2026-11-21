/** Original pixel-art for the "miner" theme: a gem icon and a rock mound with crystals and a pickaxe.
 * Drawn procedurally on a pixel grid (crisp SVG rects), so it scales without blur. */
import { useMemo } from 'react'
import { cn } from '@/lib/utils'

export const INK = '#121212'
export type Px = Map<string, string>
const k = (x: number, y: number) => `${x},${y}`

export function Pixels({ px, className }: { px: Px; className?: string }) {
  return <g className={className}>{[...px].map(([key, fill]) => { const [x, y] = key.split(',').map(Number); return <rect key={key} x={x} y={y} width={1.02} height={1.02} fill={fill} /> })}</g>
}

export const GEM = [
  '..KKKKK..',
  '.KLLHLLK.',
  'KLLHHHLLK',
  'KKKKKKKKK',
  '.KDLLLDK.',
  '..KDLDK..',
  '...KDK...',
  '....K....',
]
export const GEM_COL: Record<string, string> = { K: INK, L: '#7d75ff', H: '#e7e5ff', D: '#3d33f2' }

export function Gem({ size = 20, className }: { size?: number; className?: string }) {
  const px = useMemo(() => {
    const m: Px = new Map()
    GEM.forEach((row, y) => [...row].forEach((c, x) => { if (GEM_COL[c]) m.set(k(x, y), GEM_COL[c]) }))
    return m
  }, [])
  return <svg viewBox="0 0 9 8" width={size} height={size * 8 / 9} shapeRendering="crispEdges" className={className} aria-hidden><Pixels px={px} /></svg>
}

/** Fill a shape, then outline its edge pixels in ink. */
function shape(test: (x: number, y: number) => string | null, box: [number, number, number, number]): Px {
  const m: Px = new Map()
  const [x0, y0, x1, y1] = box
  for (let y = y0; y <= y1; y++) for (let x = x0; x <= x1; x++) { const c = test(x, y); if (c) m.set(k(x, y), c) }
  for (const key of [...m.keys()]) {
    const [x, y] = key.split(',').map(Number)
    if (![[1, 0], [-1, 0], [0, 1], [0, -1]].every(([dx, dy]) => m.has(k(x + dx, y + dy)))) m.set(key, INK)
  }
  return m
}

interface Crystal { cx: number; base: number; hw: number; h: number; tip: number; shear: number; light: string; mid: string; dark: string }
const CRYSTALS: Crystal[] = [
  { cx: 24, base: 22, hw: 3, h: 15, tip: 4, shear: -0.18, light: '#a7a1ff', mid: '#5b52ff', dark: '#3d33f2' },
  { cx: 31, base: 21, hw: 4, h: 19, tip: 5, shear: 0.02, light: '#c4bfff', mid: '#6f67ff', dark: '#3d33f2' },
  { cx: 38, base: 23, hw: 2, h: 11, tip: 3, shear: 0.25, light: '#9ff0d0', mid: '#2fbf8c', dark: '#11795a' },
  { cx: 18, base: 25, hw: 2, h: 8, tip: 3, shear: -0.3, light: '#ffd98a', mid: '#f2a516', dark: '#a86a00' },
]

function crystal(c: Crystal): Px {
  const top = c.base - c.h
  return shape((x, y) => {
    if (y < top || y > c.base) return null
    const ox = Math.round(c.shear * (c.base - y))
    const dx = x - (c.cx + ox)
    const w = y < top + c.tip ? Math.round(c.hw * (y - top + 1) / c.tip) : c.hw
    if (Math.abs(dx) > w) return null
    if (dx === -w + 1 && y > top + 1) return '#ffffff'
    return dx < 0 ? c.light : dx === 0 ? c.mid : c.dark
  }, [c.cx - c.hw - 6, top, c.cx + c.hw + 6, c.base])
}

function mound(): Px {
  const cx = 30, cy = 37, rx = 26, ry = 17
  return shape((x, y) => {
    if (y > 36) return null
    const d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
    if (d > 1) return null
    const depth = (y - (cy - ry)) / ry // 0 top → 1 bottom
    if ((x + y) % 2 === 0 && depth > 0.55) return '#a9a698'
    if ((x * 3 + y * 5) % 7 === 0 && depth > 0.3) return '#bfbcaf'
    return '#dcdacf'
  }, [cx - rx, cy - ry, cx + rx, 36])
}

export function ground(width = 64): Px {
  const m: Px = new Map()
  for (let x = 0; x < width; x++) {
    m.set(k(x, 37), INK)
    for (let y = 38; y < 40; y++) if ((x + y) % 3 === 0) m.set(k(x, y), '#7d7a6e')
  }
  return m
}

function pickaxe(): Px {
  const m: Px = new Map()
  // handle: from (49,36) up-right to (58,20)
  for (let i = 0; i <= 16; i++) {
    const x = Math.round(49 + i * 9 / 16), y = 36 - i
    m.set(k(x, y), '#8a5a2b'); m.set(k(x + 1, y), '#5e3b17')
    m.set(k(x - 1, y), INK); m.set(k(x + 2, y), INK)
  }
  // head: an arc through the top of the handle
  const head: [number, number][] = [[50, 22], [51, 21], [52, 20], [53, 19], [54, 19], [55, 18], [56, 18], [57, 18], [58, 18], [59, 18], [60, 18], [61, 19], [62, 19], [63, 20]]
  head.forEach(([x, y], i) => {
    m.set(k(x, y - 1), INK); m.set(k(x, y + 2), INK)
    m.set(k(x, y), i % 4 === 0 ? '#ffffff' : '#c9c9d4'); m.set(k(x, y + 1), '#8b8b99')
  })
  m.set(k(49, 22), INK); m.set(k(49, 23), INK)
  return m
}

const SPARKS: [number, number, number][] = [[14, 9, 0], [44, 6, 0.6], [36, 14, 1.2], [10, 20, 1.8], [47, 26, 0.9], [27, 3, 1.5]]

/** The mound with its crystals as one pixel map (the "rock" the loader breaks). */
export function sceneRock(): Px {
  const m: Px = new Map(mound())
  for (const c of CRYSTALS) for (const [key, fill] of crystal(c)) m.set(key, fill)
  return m
}

/** Static start-page illustration: rock mound with crystals, a pickaxe leaning on it, a few sparkles. */
export function PixelMine({ className }: { className?: string }) {
  const layers = useMemo(() => ({ ground: ground(), rock: sceneRock(), pick: pickaxe() }), [])
  return (
    <svg viewBox="0 0 64 40" shapeRendering="crispEdges" className={cn('block h-auto w-full', className)} role="img" aria-label="Ilustracja: skała z kryształami i kilof">
      <Pixels px={layers.ground} />
      <Pixels px={layers.rock} />
      <Pixels px={layers.pick} />
      {SPARKS.map(([x, y, d]) => (
        <g key={`${x},${y}`} className="twinkle" style={{ animationDelay: `${d}s` }} fill={INK}>
          <rect x={x} y={y - 1} width={1} height={3} /><rect x={x - 1} y={y} width={3} height={1} />
        </g>))}
    </svg>
  )
}
