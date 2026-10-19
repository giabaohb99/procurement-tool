import { env } from '@/core/config/env'
import { tokenStorage } from '@/core/api/token-storage'

import { UI_FORM_NONE, type UiEventCode, type UiFormCode } from './ui-event-codes'

/** Sự kiện một giao diện đẩy vào hàng đợi (hợp đồng `POST /api/telemetry/ui-events`). */
export interface UiEventInput {
  type: UiEventCode
  route: string
  form?: UiFormCode
  duration_ms?: number
  /** Chỉ SEARCH — số kết quả. TỪ KHÓA không bao giờ đi qua đây. */
  result_count?: number | null
  /** Chỉ CLIENT_ERROR. */
  error?: { name: string; message: string } | null
}

interface QueuedEvent extends UiEventInput {
  at: number
}

/** Một lô sẵn sàng gửi: sự kiện gốc (để trả lại bộ đệm khi 401) + JSON đã dựng. */
interface Batch {
  events: QueuedEvent[]
  json: string[]
  bytes: number
}

export interface TelemetryQueueDeps {
  fetchImpl: typeof fetch
  now: () => number
  getToken: () => string | null
  url: string
  tabKey: number
}

export const MAX_QUEUE = 300
export const MAX_BATCH_EVENTS = 100
/** Trần thân của `fetch keepalive` là 64 KB — chừa lề. */
export const MAX_BATCH_BYTES = 60 * 1024
/** Tổng thân của mọi `fetch keepalive` cùng lúc: trần của trình duyệt là 64 KB — chừa lề. */
export const MAX_KEEPALIVE_TOTAL_BYTES = 60 * 1024
export const FLUSH_INTERVAL_MS = 30_000
/** Khớp `MAX_AGE_MS` của backend (24 giờ): lô giữ lại qua đêm do 401 vẫn rơi đúng ngày phát sinh. */
const MAX_AGE_MS = 86_400_000

const encoder = new TextEncoder()
const bytesOf = (text: string) => encoder.encode(text).length

function toWire(event: QueuedEvent, now: number, tabKey: number) {
  return {
    type: event.type,
    route: event.route,
    form: event.form ?? UI_FORM_NONE,
    duration_ms: Math.max(0, Math.min(86_400_000, Math.round(event.duration_ms ?? 0))),
    result_count: event.result_count ?? null,
    age_ms: Math.max(0, Math.min(MAX_AGE_MS, now - event.at)),
    tab_key: tabKey,
    error: event.error ?? null,
  }
}

/**
 * Hàng đợi sự kiện giao diện. KHÔNG phải state React: chỉ đẩy vào mảng, nên
 * không làm giao diện render lại. Mọi lỗi mạng/HTTP đều nuốt im lặng — thu thập
 * hành vi không bao giờ được hiện toast hay chặn người dùng.
 *
 * Gửi bằng `fetch(..., { keepalive: true })` kèm `Authorization: Bearer` (không
 * dùng `sendBeacon` vì token không nằm trong cookie).
 */
export function createTelemetryQueue(deps: TelemetryQueueDeps) {
  let buffer: QueuedEvent[] = []
  let enabled = false
  /** Máy chủ báo đã tắt thu thập (204 / accepted 0): dừng tới khi nạp lại trang. */
  let serverOff = false
  let inFlight = false
  let timer: ReturnType<typeof setInterval> | null = null
  const flushHooks = new Set<() => void>()

  const trim = () => {
    if (buffer.length > MAX_QUEUE) buffer = buffer.slice(buffer.length - MAX_QUEUE)
  }

  /**
   * Chia lô ≤ 100 sự kiện và ≤ 60 KB (đo theo byte của thân JSON). Mỗi sự kiện được
   * dựng JSON ĐÚNG MỘT LẦN ở đây (lúc gửi), không phải lúc `enqueue`.
   */
  function takeBatches(): Batch[] {
    const now = deps.now()
    const empty = bytesOf('{"events":[]}')
    const batches: Batch[] = []
    let current: Batch = { events: [], json: [], bytes: empty }
    for (const event of buffer) {
      const json = JSON.stringify(toWire(event, now, deps.tabKey))
      const eventBytes = bytesOf(json) + 1
      if (
        current.events.length > 0 &&
        (current.events.length >= MAX_BATCH_EVENTS || current.bytes + eventBytes > MAX_BATCH_BYTES)
      ) {
        batches.push(current)
        current = { events: [], json: [], bytes: empty }
      }
      current.events.push(event)
      current.json.push(json)
      current.bytes += eventBytes
    }
    if (current.events.length > 0) batches.push(current)
    buffer = []
    return batches
  }

  /** Gửi một lô. Trả `true` nếu phải GIỮ LẠI lô (401: token hết hạn, thử nhịp sau). */
  async function sendBatch(batch: Batch, keepalive: boolean, token: string): Promise<boolean> {
    try {
      const res = await deps.fetchImpl(deps.url, {
        method: 'POST',
        keepalive,
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: `{"events":[${batch.json.join(',')}]}`,
      })
      if (res.status === 401) return true
      if (res.status === 204) serverOff = true
      else if (res.ok) {
        const body = (await res.json().catch(() => null)) as { data?: { accepted?: number } } | null
        if (body?.data?.accepted === 0) serverOff = true
      }
      // 413 / 4xx / 5xx khác: bỏ lô — thử lại cũng không khá hơn.
      return false
    } catch {
      return false // lỗi mạng: bỏ lô, không báo gì
    }
  }

  async function flush(keepalive = false): Promise<void> {
    if (!enabled || serverOff || buffer.length === 0) return
    if (!keepalive && inFlight) return
    const token = deps.getToken()
    if (!token) return // chưa đăng nhập / vừa đăng xuất: giữ nguyên bộ đệm
    const batches = takeBatches()
    if (!keepalive) inFlight = true
    try {
      const kept: Batch[] = []
      if (keepalive) {
        // Trình duyệt giới hạn TỔNG thân của mọi `fetch keepalive` đang bay ở 64 KB: vượt là
        // `TypeError` và lô đó mất im lặng. Nên chỉ bắn các lô vừa trong ~60 KB cộng dồn (lô
        // đầu luôn được bắn — nó đã ≤ 60 KB); phần còn lại GIỮ trong bộ đệm cho lần gửi sau
        // (tab chỉ bị ẩn) hoặc mất theo trang (đang đóng) — cố ý, không ép thêm.
        let used = 0
        const now: Batch[] = []
        for (const batch of batches) {
          if (now.length > 0 && used + batch.bytes > MAX_KEEPALIVE_TOTAL_BYTES) kept.push(batch)
          else {
            now.push(batch)
            used += batch.bytes
          }
        }
        const results = await Promise.all(now.map((b) => sendBatch(b, true, token)))
        results.forEach((keep, i) => keep && kept.push(now[i]))
      } else {
        for (const batch of batches) {
          if (await sendBatch(batch, false, token)) kept.push(batch)
        }
      }
      if (kept.length > 0) {
        buffer = [...kept.flatMap((b) => b.events), ...buffer]
        trim()
      }
    } finally {
      // Chỉ đường gửi THƯỜNG được đặt/xóa cờ: keepalive không đặt nên cũng không được xóa, nếu không một lần
      // gửi thường đang bay sẽ bị coi như đã xong và nhịp 30 giây kế tiếp chạy chồng lên nó.
      if (!keepalive) inFlight = false
    }
  }

  function stopTimer() {
    if (timer !== null) clearInterval(timer)
    timer = null
  }

  return {
    enqueue(event: UiEventInput) {
      if (!enabled || serverOff) return
      buffer.push({ ...event, at: deps.now() })
      trim()
    },
    flush,
    /** Bật/tắt thu thập. Tắt = xóa bộ đệm và dừng nhịp gửi. */
    setEnabled(next: boolean) {
      if (next === enabled) return
      enabled = next
      if (next) {
        timer = setInterval(() => void flush(false), FLUSH_INTERVAL_MS)
      } else {
        stopTimer()
        buffer = []
      }
    },
    /** Việc chạy ĐỒNG BỘ ngay trước lần gửi cuối khi rời trang (phát PAGE_LEAVE/FORM_ABANDON). */
    onPageHide(hook: () => void) {
      flushHooks.add(hook)
      return () => flushHooks.delete(hook)
    },
    /** Gọi bởi trình nghe `pagehide`: chạy các hook rồi đẩy hết bằng keepalive. */
    handlePageHide() {
      flushHooks.forEach((hook) => hook())
      void flush(true)
    },
    handleHidden() {
      void flush(true)
    },
    size: () => buffer.length,
  }
}

export type TelemetryQueue = ReturnType<typeof createTelemetryQueue>

/** Một số ngẫu nhiên mỗi lần nạp trang — tách đường đi khi mở nhiều tab. */
const tabKey = Math.floor(Math.random() * 2_000_000_000)

export const telemetry = createTelemetryQueue({
  fetchImpl: (...args) => fetch(...args),
  now: () => Date.now(),
  getToken: () => tokenStorage.getAccessToken(),
  url: `${env.apiUrl}/api/telemetry/ui-events`,
  tabKey,
})

/** Route mẫu của màn đang mở — để gắn vào sự kiện không tự biết route (lỗi JS). */
let currentRoute = '/'
export const setCurrentRoute = (route: string) => {
  currentRoute = route
}
export const getCurrentRoute = () => currentRoute

let lifecycleInstalled = false
/** Gắn trình nghe `visibilitychange`/`pagehide` đúng một lần cho cả trang. */
export function installTelemetryLifecycle() {
  if (lifecycleInstalled || typeof window === 'undefined') return
  lifecycleInstalled = true
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'hidden') telemetry.handleHidden()
  })
  window.addEventListener('pagehide', () => telemetry.handlePageHide())
}
