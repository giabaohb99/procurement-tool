import type { ReactNode } from 'react'

import type { CursorPoint } from './chapter-timeline'

/** Trạng thái cảnh nhận được mỗi khung hình: tiến độ chương (0 → 1) và cờ giảm chuyển động. */
export interface DemoSceneState {
  progress: number
  reduced: boolean
}

/** Một chương của demo: cảnh dựng bằng component v2 thật với dữ liệu giả, không video. */
export interface DemoChapter {
  id: string
  title: string
  /** Một câu giải thích hiện dưới khung. */
  caption: string
  durationMs: number
  /** Đường đi con trỏ giả (tọa độ % khung). Bỏ trống = không có con trỏ. */
  cursor?: CursorPoint[]
  render: (state: DemoSceneState) => ReactNode
}
