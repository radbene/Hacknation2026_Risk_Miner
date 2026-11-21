/** Quiet animated background behind every page: a slowly drifting dot grid and a few small pixel gems and sparkles
 * floating up. Fixed, behind the content, ignores the mouse; switched off for prefers-reduced-motion (see index.css). */
import { Gem } from './PixelMine'

// x position (vw), size (px), float duration (s), start delay (s), kind
const BITS: [number, number, number, number, 'gem' | 'spark'][] = [
  [4, 14, 38, 0, 'gem'], [11, 7, 29, 9, 'spark'], [19, 10, 44, 18, 'gem'], [27, 6, 33, 4, 'spark'],
  [36, 12, 41, 26, 'gem'], [45, 7, 31, 13, 'spark'], [53, 9, 47, 6, 'gem'], [61, 6, 35, 21, 'spark'],
  [69, 13, 40, 11, 'gem'], [77, 7, 30, 28, 'spark'], [85, 10, 45, 2, 'gem'], [93, 6, 34, 16, 'spark'],
]

export function MineBackdrop() {
  return (
    <div aria-hidden className="pointer-events-none fixed inset-0 z-0 overflow-hidden">
      <div className="backdrop-grid absolute -inset-16" />
      {BITS.map(([x, size, dur, delay, kind], i) => (
        <span key={i} className="float-bit absolute bottom-0" style={{ left: `${x}vw`, animationDuration: `${dur}s`, animationDelay: `-${delay}s` }}>
          {kind === 'gem'
            ? <Gem size={size} className="opacity-30" />
            : <svg width={size} height={size} viewBox="0 0 3 3" shapeRendering="crispEdges" className="opacity-40"><rect x={1} y={0} width={1} height={3} fill="#3d33f2" /><rect x={0} y={1} width={3} height={1} fill="#3d33f2" /></svg>}
        </span>))}
    </div>
  )
}
