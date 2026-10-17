import { MousePointer2 } from 'lucide-react'
import { motion } from 'motion/react'

import type { CursorState } from './chapter-timeline'

/** Con trỏ giả đi trên khung demo; tọa độ là % khung, `motion` nội suy giữa hai nhịp đếm cho mượt. */
export function DemoCursor({ state }: { state: CursorState }) {
  return (
    <motion.div
      aria-hidden
      className="pointer-events-none absolute z-30 -translate-x-1 -translate-y-1"
      animate={{ left: `${state.x}%`, top: `${state.y}%` }}
      transition={{ type: 'tween', ease: 'linear', duration: 0.05 }}
    >
      {state.clicking && (
        <motion.span
          className="absolute -top-2 -left-2 size-6 rounded-full border-2 border-primary"
          initial={{ scale: 0.4, opacity: 0.9 }}
          animate={{ scale: 1.4, opacity: 0 }}
          transition={{ duration: 0.4 }}
        />
      )}
      <MousePointer2 className="size-5 fill-foreground text-background drop-shadow" />
    </motion.div>
  )
}
