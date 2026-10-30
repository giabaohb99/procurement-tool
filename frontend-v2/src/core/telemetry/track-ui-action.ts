import { getCurrentRoute, telemetry } from './telemetry-queue'
import { UI_ACTION_CODE, UI_EVENT, type UiActionCode } from './ui-event-codes'

/**
 * Ghi một lần "bấm chức năng" (duoc-CR-654, D0a). Chỉ mang MÃ NÚT cố định + route mẫu — không chữ gõ, không id.
 *
 * Chống spam ở máy khách (xem phase-01):
 *  1. bỏ trùng: cùng (mã, route) trong 2 giây → bỏ (bấm đúp);
 *  2. mã "lắm lời" (sắp xếp, chuyển trang, đổi cỡ trang, ẩn/hiện cột, tô màu) gộp cửa sổ 10 giây theo (mã, route);
 *  3. trần 30 UI_ACTION/phút/tab (cửa sổ trượt), vượt thì bỏ im lặng.
 * Trần phía máy chủ là 60/lô, nên đây là lớp đầu, không phải lớp duy nhất.
 */
export const DEDUPE_MS = 2_000
export const NOISY_WINDOW_MS = 10_000
export const MAX_ACTIONS_PER_MINUTE = 30
const MINUTE_MS = 60_000

const NOISY: ReadonlySet<UiActionCode> = new Set<UiActionCode>([
  UI_ACTION_CODE.SORT_CHANGE,
  UI_ACTION_CODE.PAGE_CHANGE,
  UI_ACTION_CODE.PAGE_SIZE_CHANGE,
  UI_ACTION_CODE.COLUMN_TOGGLE,
  UI_ACTION_CODE.COLUMN_COLOR,
])

export interface UiActionTrackerDeps {
  now: () => number
  getRoute: () => string
  enqueue: (action: UiActionCode, route: string) => void
}

export function createUiActionTracker(deps: UiActionTrackerDeps) {
  const lastSeen = new Map<string, number>()
  let sent: number[] = []

  return function track(code: UiActionCode): void {
    const now = deps.now()
    const route = deps.getRoute()
    const key = `${code}|${route}`
    const window = NOISY.has(code) ? NOISY_WINDOW_MS : DEDUPE_MS
    const prev = lastSeen.get(key)
    if (prev !== undefined && now - prev < window) return
    sent = sent.filter((t) => now - t < MINUTE_MS)
    if (sent.length >= MAX_ACTIONS_PER_MINUTE) return
    lastSeen.set(key, now)
    sent.push(now)
    deps.enqueue(code, route)
  }
}

const track = createUiActionTracker({
  now: () => Date.now(),
  getRoute: getCurrentRoute,
  enqueue: (action, route) => telemetry.enqueue({ type: UI_EVENT.UI_ACTION, route, action }),
})

/** Gọi trong handler NGƯỜI BẤM (không gọi trong hàm đồng bộ URL/effect). Nuốt mọi lỗi: đo đạc không được làm hỏng nút. */
export function trackUiAction(code: UiActionCode): void {
  try {
    track(code)
  } catch {
    /* im lặng */
  }
}
