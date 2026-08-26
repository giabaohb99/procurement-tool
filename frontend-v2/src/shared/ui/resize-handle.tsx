import type { PointerEvent as ReactPointerEvent } from 'react'

import { cn } from '@/shared/utils/cn'

/** Mỗi lần bấm mũi tên đổi bao nhiêu px. */
const KEY_STEP_PX = 16

interface ResizeHandleProps {
  label: string
  width: number
  min: number
  max: number
  onPointerDown: (event: ReactPointerEvent) => void
  onKeyResize: (buoc: number) => void
  className?: string
}

/**
 * Vạch kéo giãn ở mép một cột.
 *
 * Vạch **rộng 8px đè lên viền 1px**: viền một pixel thì phải căn tay mới bắt
 * trúng con trỏ. Chỉ tô màu khi rê chuột vào nên bình thường không ai thấy nó.
 *
 * Có `tabIndex` và nghe phím mũi tên: chỉnh được bằng bàn phím chứ không bắt
 * buộc phải có chuột. `aria-valuenow/min/max` để trình đọc màn hình đọc ra
 * đang rộng bao nhiêu.
 */
export function ResizeHandle({
  label,
  width,
  min,
  max,
  onPointerDown,
  onKeyResize,
  className,
}: ResizeHandleProps) {
  return (
    <div
      role="separator"
      aria-orientation="vertical"
      aria-label={label}
      aria-valuenow={width}
      aria-valuemin={min}
      aria-valuemax={max}
      tabIndex={0}
      title={label}
      onPointerDown={onPointerDown}
      onKeyDown={(e) => {
        if (e.key === 'ArrowLeft') {
          e.preventDefault()
          onKeyResize(-KEY_STEP_PX)
        }
        if (e.key === 'ArrowRight') {
          e.preventDefault()
          onKeyResize(KEY_STEP_PX)
        }
      }}
      className={cn(
        'absolute inset-y-0 -right-1 z-10 w-2 cursor-col-resize touch-none',
        'transition-colors hover:bg-primary/20 focus-visible:bg-primary/30 focus-visible:outline-none',
        className,
      )}
    />
  )
}
