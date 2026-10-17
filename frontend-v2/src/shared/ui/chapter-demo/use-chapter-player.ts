import { useCallback, useEffect, useReducer, useRef } from 'react'

/** Nhịp đếm của bộ chạy — đủ mượt cho thanh tiến độ, chuyển động thật do `motion` nội suy. */
export const PLAYER_TICK_MS = 50

export interface PlayerState {
  index: number
  elapsed: number
  playing: boolean
}

export type PlayerAction =
  | { type: 'tick'; ms: number }
  | { type: 'goTo'; index: number }
  | { type: 'toggle' }

function durationOf(durations: readonly number[], index: number): number {
  const value = durations[index]
  return typeof value === 'number' && Number.isFinite(value) && value > 0 ? value : 1
}

/**
 * Bước chạy THUẦN: hết giờ chương này thì sang chương kế (dư thời gian không dồn sang
 * chương sau), hết chương cuối thì dừng ở trạng thái cuối; bấm chạy tiếp khi đã hết thì
 * chạy lại từ chương đầu. `goTo` nhảy về đầu chương được chọn, giữ nguyên đang chạy / dừng.
 */
export function stepPlayer(
  state: PlayerState,
  action: PlayerAction,
  durations: readonly number[],
): PlayerState {
  const count = durations.length
  if (count === 0) return { index: 0, elapsed: 0, playing: false }
  const index = Math.min(count - 1, Math.max(0, state.index))
  const duration = durationOf(durations, index)
  switch (action.type) {
    case 'tick': {
      if (!state.playing) return state
      const elapsed = state.elapsed + Math.max(0, action.ms)
      if (elapsed < duration) return { ...state, index, elapsed }
      if (index < count - 1) return { ...state, index: index + 1, elapsed: 0 }
      return { index, elapsed: duration, playing: false }
    }
    case 'goTo': {
      const target = Number.isFinite(action.index) ? Math.trunc(action.index) : 0
      return { ...state, index: Math.min(count - 1, Math.max(0, target)), elapsed: 0 }
    }
    case 'toggle': {
      const finished = !state.playing && index === count - 1 && state.elapsed >= duration
      if (finished) return { index: 0, elapsed: 0, playing: true }
      return { ...state, index, playing: !state.playing }
    }
  }
}

export interface ChapterPlayerOptions {
  /** Thời lượng từng chương (ms), theo thứ tự chương. */
  durations: readonly number[]
  autoplay?: boolean
  /** Giảm chuyển động: không tự chạy, mỗi chương đứng ở trạng thái cuối (`progress = 1`). */
  reduced?: boolean
  onChapterChange?: (index: number) => void
}

export interface ChapterPlayer {
  index: number
  progress: number
  playing: boolean
  goTo: (index: number) => void
  toggle: () => void
}

export function useChapterPlayer({
  durations,
  autoplay = true,
  reduced = false,
  onChapterChange,
}: ChapterPlayerOptions): ChapterPlayer {
  const [state, dispatch] = useReducer(
    (s: PlayerState, a: PlayerAction) => stepPlayer(s, a, durations),
    { index: 0, elapsed: 0, playing: autoplay && !reduced && durations.length > 0 },
  )
  const playing = state.playing && !reduced

  useEffect(() => {
    if (!playing) return undefined
    const timer = window.setInterval(() => dispatch({ type: 'tick', ms: PLAYER_TICK_MS }), PLAYER_TICK_MS)
    return () => window.clearInterval(timer)
  }, [playing])

  //  Báo đổi chương cho bên ngoài — bỏ lần dựng đầu (chưa có gì «đổi»).
  const onChange = useRef(onChapterChange)
  const lastIndex = useRef(state.index)
  useEffect(() => {
    onChange.current = onChapterChange
  }, [onChapterChange])
  useEffect(() => {
    if (lastIndex.current === state.index) return
    lastIndex.current = state.index
    onChange.current?.(state.index)
  }, [state.index])

  const goTo = useCallback((index: number) => dispatch({ type: 'goTo', index }), [])
  const toggle = useCallback(() => {
    if (!reduced) dispatch({ type: 'toggle' })
  }, [reduced])

  const duration = durationOf(durations, state.index)
  return {
    index: state.index,
    progress: reduced ? 1 : Math.min(1, state.elapsed / duration),
    playing,
    goTo,
    toggle,
  }
}
