/**
 * Bắt lỗi giao diện chưa xử lý của cả trang → CLIENT_ERROR (chép từ ERP v2 `install-global-error-capture.ts`,
 * bao-CR-649). App cũ không có `logger` / ErrorBoundary nên chỉ có hai trình nghe `error` + `unhandledrejection`.
 */
import { getCurrentRoute, telemetry } from './telemetry-queue'
import { UI_EVENT } from './ui-event-codes'

const MAX_ERRORS_PER_LOAD = 20
const seen = new Set<string>()
let reported = 0
let reporting = false

/** Cắt 200 ký tự và thay chuỗi số ≥ 6 chữ số bằng `#` (tránh lọt số điện thoại/CCCD). */
export function sanitizeErrorMessage(message: string): string {
  return message.replace(/\d{6,}/g, '#').slice(0, 200)
}

/**
 * Đẩy một CLIENT_ERROR vào hàng đợi: tối đa 20/lần nạp trang, trùng thông điệp thì bỏ, có cờ chống đệ quy.
 * Chỉ gửi tên + thông điệp đã làm sạch — không stack, không dữ liệu form.
 */
export function reportClientError(name: string, message: string) {
  if (reporting || reported >= MAX_ERRORS_PER_LOAD) return
  const clean = sanitizeErrorMessage(message)
  const key = `${name}|${clean}`
  if (seen.has(key)) return
  reporting = true
  try {
    seen.add(key)
    reported += 1
    telemetry.enqueue({
      type: UI_EVENT.CLIENT_ERROR,
      route: getCurrentRoute(),
      error: { name: name.slice(0, 60), message: clean },
    })
  } finally {
    reporting = false
  }
}

let installed = false
/** Gọi một lần. */
export function installGlobalErrorCapture() {
  if (installed || typeof window === 'undefined') return
  installed = true
  window.addEventListener('error', (event) => {
    reportClientError(event.error instanceof Error ? event.error.name : 'Error', event.message || 'Error')
  })
  window.addEventListener('unhandledrejection', (event) => {
    const reason: unknown = event.reason
    if (reason instanceof Error) reportClientError(reason.name, reason.message)
    else reportClientError('UnhandledRejection', typeof reason === 'string' ? reason : 'Unhandled rejection')
  })
}
