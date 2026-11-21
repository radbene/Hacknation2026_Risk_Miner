/** Waiting screen for the risk calculation: a pickaxe strikes a rock every moment, the rock cracks a little more with
 * every hit, and the moment the server answers it shatters, uncovers the gem and hands over to the result.
 * The cracks are not a fake progress bar: they slow down and never finish until the calculation really is done. */
import { useEffect, useMemo, useRef, useState } from 'react'
import { GEM, GEM_COL, INK, Pixels, ground, sceneRock, type Px } from '@/components/PixelMine'
import { cn } from '@/lib/utils'

const key = (x: number, y: number) => `${x},${y}`
const xy = (k: string) => k.split(',').map(Number) as [number, number]

const STRIKE_EVERY = 1500 // ms between hits
const IMPACT_AT = 380 // ms into the swing when the pick touches the rock
const SHATTER_MS = 1100 // how long the pieces fly before the result shows
const MAX_WAITING_DAMAGE = 0.9 // the rock never breaks by itself

// The same rock as on the start page (mound with crystals, 64×40 scene); a little extra room on the right for the swing.
const BASE = sceneRock()
const CX = 30, CY = 24
const IMPACT: [number, number] = [47, 26]
const STEPS = [
  'Szukamy podobnych zakończonych inwestycji',
  'Liczymy opóźnienia i zmiany umów w podobnych',
  'Oceniamy budżet i harmonogram',
  'Sprawdzamy czerwone flagi i zapisy umowne',
  'Model językowy pisze podsumowanie',
]

function rng(seed: number) {
  return () => { seed |= 0; seed = (seed + 0x6d2b79f5) | 0; let t = Math.imul(seed ^ (seed >>> 15), 1 | seed); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296 }
}

const inRock = (x: number, y: number) => BASE.has(key(x, y))

/** Crack pixels, interleaved so that all cracks grow together. */
const CRACKS: string[] = (() => {
  const rand = rng(7), lines: string[][] = []
  for (const base of [Math.PI * 0.85, Math.PI * 1.05, Math.PI * 1.25, Math.PI * 0.6, Math.PI * 1.45]) {
    let [x, y] = IMPACT, a = base
    const line: string[] = []
    for (let i = 0; i < 22; i++) {
      x += Math.round(Math.cos(a)); y += Math.round(Math.sin(a)); a += (rand() - 0.5) * 0.9
      if (!inRock(x, y)) break
      line.push(key(x, y))
    }
    lines.push(line)
  }
  const out: string[] = [], seen = new Set<string>()
  for (let i = 0; i < 22; i++) for (const l of lines) if (l[i] && !seen.has(l[i])) { seen.add(l[i]); out.push(l[i]) }
  return out
})()

/** Rock pixels for a given damage (0..1): crater at the impact point, cracks, ink edge around the crater. */
function rock(damage: number): Px {
  const m: Px = new Map(BASE)
  const crater = damage < 0.12 ? 0 : 1.5 + damage * 5
  const removed: string[] = []
  for (const k of BASE.keys()) { const [x, y] = xy(k); if (Math.hypot(x - IMPACT[0], y - IMPACT[1]) < crater) { m.delete(k); removed.push(k) } }
  for (const k of removed) {
    const [x, y] = xy(k)
    for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) { const n = key(x + dx, y + dy); if (m.has(n)) m.set(n, INK) }
  }
  CRACKS.slice(0, Math.floor(CRACKS.length * Math.min(1, damage / MAX_WAITING_DAMAGE))).forEach((k) => { if (m.has(k)) m.set(k, INK) })
  return m
}

/** Split the rock into pieces by angle around its centre; each piece flies its own way when it shatters. */
const PIECES = 7
function split(m: Px): Px[] {
  const parts: Px[] = Array.from({ length: PIECES }, () => new Map())
  for (const [k, c] of m) {
    const [x, y] = xy(k)
    const a = Math.atan2(y - CY, x - CX) + Math.PI
    parts[Math.min(PIECES - 1, Math.floor((a / (2 * Math.PI)) * PIECES))].set(k, c)
  }
  return parts
}

function outlined(fill: Px): Px {
  const m: Px = new Map(fill)
  for (const k of fill.keys()) {
    const [x, y] = xy(k)
    for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) if (!fill.has(key(x + dx, y + dy))) m.set(key(x + dx, y + dy), INK)
  }
  for (const [k, c] of fill) m.set(k, c)
  return m
}

// Pickaxe in the impact pose: the tip touches IMPACT, the handle goes down-right to the pivot.
const PERP: [number, number] = [-0.83, 0.55] // along the head, towards the tip
const DIR: [number, number] = [-0.55, -0.83] // along the handle, from pivot to head
const TOP: [number, number] = [IMPACT[0] - PERP[0] * 7, IMPACT[1] - PERP[1] * 7]
const HANDLE = 15
const PIVOT: [number, number] = [TOP[0] - DIR[0] * HANDLE, TOP[1] - DIR[1] * HANDLE]
const PICK: Px = (() => {
  const f: Px = new Map()
  for (let i = 0; i <= HANDLE; i++) {
    const x = Math.round(PIVOT[0] + DIR[0] * i), y = Math.round(PIVOT[1] + DIR[1] * i)
    f.set(key(x, y), '#8a5a2b'); f.set(key(x + 1, y), '#5e3b17')
  }
  for (let s = -6; s <= 7; s++) {
    const bend = -0.07 * s * s
    const x = TOP[0] + PERP[0] * s + DIR[0] * bend, y = TOP[1] + PERP[1] * s + DIR[1] * bend
    f.set(key(Math.round(x), Math.round(y)), s === 7 || s === -6 ? '#ffffff' : '#c9c9d4')
    f.set(key(Math.round(x - DIR[0]), Math.round(y - DIR[1])), '#8b8b99')
  }
  return outlined(f)
})()

interface Chip { id: number; dx: number; dy: number; c: string }

const reducedMotion = () => typeof window !== 'undefined' && window.matchMedia?.('(prefers-reduced-motion: reduce)').matches

/** Full-screen overlay while `pending`; when it turns false (and not `failed`) the rock shatters, then `onFinished`. */
export function MiningLoader({ pending, failed, onFinished, title = 'Liczymy ryzyko' }: { pending: boolean; failed?: boolean; onFinished?: () => void; title?: string }) {
  const [phase, setPhase] = useState<'idle' | 'mining' | 'breaking' | 'broken'>('idle')
  const [damage, setDamage] = useState(0)
  const [hits, setHits] = useState(0) // remount key: shakes the rock on every hit
  const [swing, setSwing] = useState(0)
  const [chips, setChips] = useState<Chip[]>([])
  const [started, setStarted] = useState(0)
  const [now, setNow] = useState(0)
  const finished = useRef(onFinished)
  finished.current = onFinished

  // Start / stop following the request.
  useEffect(() => {
    if (pending && (phase === 'idle' || phase === 'broken')) {
      setPhase('mining'); setDamage(0); setHits(0); setChips([]); setStarted(Date.now()); setNow(Date.now())
    } else if (!pending && phase === 'mining') {
      if (failed) { setPhase('idle'); return }
      if (reducedMotion()) { setPhase('idle'); finished.current?.(); return }
      setPhase('breaking')
    }
  }, [pending, failed, phase])

  // One hit: swing, and at the moment of impact crack the rock a bit more (slower and slower).
  const strike = (final: boolean) => {
    setSwing((s) => s + 1)
    return window.setTimeout(() => {
      setHits((h) => h + 1)
      setDamage((d) => (final ? 1 : Math.min(MAX_WAITING_DAMAGE, d + Math.max(0.015, (MAX_WAITING_DAMAGE - d) * 0.14))))
      const id = Date.now()
      setChips((c) => [...c.slice(-12), ...Array.from({ length: final ? 0 : 4 }, (_, i) => ({ id: id + i, dx: 3 + Math.random() * 8, dy: -4 - Math.random() * 6, c: i % 2 ? '#a9a698' : '#cfccbf' }))])
      if (final) setPhase('broken')
    }, IMPACT_AT)
  }

  useEffect(() => {
    if (phase !== 'mining' || reducedMotion()) return
    const timers: number[] = [strike(false)]
    const iv = window.setInterval(() => timers.push(strike(false)), STRIKE_EVERY)
    const clock = window.setInterval(() => setNow(Date.now()), 1000)
    return () => { clearInterval(iv); clearInterval(clock); timers.forEach(clearTimeout) }
  }, [phase])

  useEffect(() => {
    if (phase !== 'breaking') return
    const t = strike(true)
    return () => clearTimeout(t)
  }, [phase])

  useEffect(() => {
    if (phase !== 'broken') return
    const t = window.setTimeout(() => { setPhase('idle'); finished.current?.() }, SHATTER_MS)
    return () => clearTimeout(t)
  }, [phase])

  const step = Math.round(damage * 20) / 20
  const pieces = useMemo(() => split(rock(step)), [step])
  const groundPx = useMemo(() => ground(70), [])
  const gem = useMemo(() => {
    const m: Px = new Map()
    GEM.forEach((row, y) => [...row].forEach((c, x) => { if (GEM_COL[c]) m.set(key(x, y), GEM_COL[c]) }))
    return m
  }, [])

  if (phase === 'idle') return null
  const broken = phase === 'broken'
  const secs = Math.max(0, Math.round((now - started) / 1000))
  const message = broken ? 'Gotowe: ryzyko wydobyte' : STEPS[Math.min(STEPS.length - 1, Math.floor(secs / 6))]

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-paper/85 p-4 backdrop-blur-[2px]">
      <div className="w-[min(560px,100%)] border-2 border-ink bg-surface shadow-lg" role="dialog" aria-modal="true" aria-label={title}>
        <div className="flex items-center gap-3 border-b-2 border-ink px-3 py-1.5">
          <span className="h-3 w-3 border-2 border-ink" aria-hidden />
          <span className="font-mono text-xs font-semibold">kopalnia_ryzyka.exe</span>
          <span className="stripes h-3 flex-1" aria-hidden />
        </div>
        <div className="px-4 pt-4 sm:px-6">
          <svg viewBox="0 0 70 40" shapeRendering="crispEdges" className="h-auto w-full" aria-hidden>
            <Pixels px={groundPx} />
            {/* the gem waiting inside */}
            <g className={cn(broken ? 'gem-reveal' : 'opacity-0')} style={{ transformOrigin: `${CX}px ${CY}px`, transformBox: 'view-box' }}>
              <g transform={`translate(${CX - 9} ${CY - 6}) scale(2)`}><Pixels px={gem} /></g>
            </g>
            {/* the rock, shaking on every hit, flying apart at the end */}
            <g key={hits} className={broken ? undefined : 'rock-shake'}>
              {pieces.map((p, i) => {
                const a = ((i + 0.5) / PIECES) * 2 * Math.PI - Math.PI
                const fly = { ['--tx' as string]: `${Math.cos(a) * 30}px`, ['--ty' as string]: `${Math.sin(a) * 22 - 4}px`, ['--rot' as string]: `${(i % 2 ? 1 : -1) * 50}deg` }
                return <g key={i} className={broken ? 'rock-fly' : undefined} style={{ transformBox: 'fill-box', transformOrigin: 'center', ...(broken ? fly : {}) }}><Pixels px={p} /></g>
              })}
            </g>
            {/* chips flying off at the impact point */}
            {chips.map((c) => (
              <rect key={c.id} x={IMPACT[0]} y={IMPACT[1]} width={1} height={1} fill={c.c} className="rock-chip"
                style={{ ['--dx' as string]: `${c.dx}px`, ['--dy' as string]: `${c.dy}px` }} />))}
            {/* the pickaxe, resting raised between hits */}
            {!broken && (
              <g key={swing} className="pick-strike" style={{ transformOrigin: `${PIVOT[0]}px ${PIVOT[1]}px`, transformBox: 'view-box' }}>
                <Pixels px={PICK} />
              </g>)}
            {broken && [[16, 12], [44, 10], [20, 32], [42, 33], [31, 6]].map(([x, y], i) => (
              <g key={i} className="twinkle" style={{ animationDelay: `${i * 0.15}s` }} fill="#3d33f2">
                <rect x={x} y={y - 1} width={1} height={3} /><rect x={x - 1} y={y} width={3} height={1} />
              </g>))}
          </svg>
        </div>
        <div className="border-t-2 border-ink px-4 py-3 sm:px-6">
          <p role="status" aria-live="polite" className={cn('font-semibold', broken && 'text-brand')}>{message}{broken ? '' : '…'}</p>
          <p className="mt-1 font-mono text-[11px] text-slate-600">
            {broken ? 'Pokazujemy wynik.' : <>czas: {secs} s · zwykle do 2 minut, bo podsumowanie pisze model językowy</>}
          </p>
        </div>
      </div>
    </div>
  )
}
