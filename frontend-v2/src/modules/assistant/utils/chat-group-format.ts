import { TONE_CLASS } from '@/shared/ui/status-tone'
import { formatDate } from '@/shared/utils/format-date'

import type { ChatGroupItem, ChatGroupMessage, ZaloAccountStatus } from '../api/chat-group-api'

/** Tông màu từng kênh — ba kênh nằm cạnh nhau trong cùng một bảng nên phải khác màu hẳn. */
const CHANNEL_TONE: Record<string, string> = {
  telegram: TONE_CLASS.progress,
  zalo_account: TONE_CLASS.handoff,
  zalo_bot: TONE_CLASS.partial,
}

export function getChannelTone(channel: string): string {
  return CHANNEL_TONE[channel] ?? TONE_CLASS.neutral
}

export interface GroupStateView {
  label: string
  tone: string
}

/**
 * Tình trạng ghi của một nhóm. Thứ tự xét quan trọng: nhóm bot đã RỜI thì có bị tắt ghi hay không cũng không còn
 * nghĩa — người đọc cần biết trước hết là bot không còn ở đó.
 */
export function describeGroupState(item: Pick<ChatGroupItem, 'active' | 'paused'>): GroupStateView {
  if (!item.active) return { label: 'Bot đã rời nhóm', tone: TONE_CLASS.neutral }
  if (item.paused) return { label: 'Ngừng ghi', tone: TONE_CLASS.returned }
  return { label: 'Đang ghi', tone: TONE_CLASS.done }
}

const ZALO_STATE_LABEL: Record<string, string> = {
  off: 'Chưa bật',
  unreachable: 'Không gọi được tiến trình Zalo',
  idle: 'Chưa đăng nhập',
  qr: 'Đang chờ quét mã QR',
  connected: 'Đang kết nối',
  down: 'Mất kết nối',
}

export function describeZaloState(status: ZaloAccountStatus | undefined): GroupStateView {
  const state = status?.state ?? 'off'
  const label = ZALO_STATE_LABEL[state] ?? state
  if (state === 'connected') return { label, tone: TONE_CLASS.done }
  if (state === 'qr') return { label, tone: TONE_CLASS.pending }
  if (state === 'down' || state === 'unreachable') return { label, tone: TONE_CLASS.danger }
  return { label, tone: TONE_CLASS.neutral }
}

/** Dung lượng tệp dễ đọc. 0 / âm / không phải số = không rõ (Telegram, Zalo đôi khi không báo cỡ tệp). */
export function formatFileSize(bytes: number | null | undefined): string {
  if (typeof bytes !== 'number' || !Number.isFinite(bytes) || bytes <= 0) return ''
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

/** Ảnh QR mà tiến trình Zalo trả (base64 thuần, có khi đã kèm tiền tố) → giá trị dùng được cho `<img src>`. */
export function toQrImageSrc(raw: string | null | undefined): string {
  const value = (raw ?? '').trim()
  if (!value) return ''
  if (value.startsWith('data:image/')) return value
  //  Chỉ nhận đúng ký tự base64 — chuỗi lạ không được lọt vào thuộc tính src.
  if (!/^[A-Za-z0-9+/=\s]+$/.test(value)) return ''
  return `data:image/png;base64,${value.replace(/\s+/g, '')}`
}

// ---------------------------------------------------------------------------
// Khung chat của nhóm (dựng theo khung hội thoại của Trợ lý AI)
// ---------------------------------------------------------------------------
/** Hai tin cùng người gửi cách nhau quá chừng này thì vẽ lại tên + giờ. */
const SAME_RUN_MS = 5 * 60 * 1000

export type GroupThreadItem =
  | { kind: 'day'; key: string; label: string }
  | { kind: 'message'; key: string; message: ChatGroupMessage; showHeader: boolean }

function toMillis(value: string | null): number {
  if (!value) return Number.NaN
  //  Máy chủ trả giờ UTC trần (không `Z`) — cùng quy ước `shared/utils/format-date.ts`.
  const hasZone = /[zZ]$|[+-]\d{2}:?\d{2}$/.test(value)
  return new Date(hasZone ? value : `${value}Z`).getTime()
}

function dayLabel(day: string, now: Date): string {
  if (day === formatDate(now)) return 'Hôm nay'
  if (day === formatDate(new Date(now.getTime() - 24 * 60 * 60 * 1000))) return 'Hôm qua'
  return day
}

/**
 * Tin nhóm (máy chủ trả mới nhất trước, nhiều trang) → dòng hiển thị theo thứ tự đọc: cũ trên, mới dưới, có vạch ngày
 * và gộp các tin liên tiếp của cùng một người (chỉ tin đầu cụm có tên + giờ, như Zalo / Telegram).
 */
export function buildGroupThread(messages: ChatGroupMessage[], now: Date = new Date()): GroupThreadItem[] {
  const ordered = [...new Map(messages.map((m) => [m.id, m])).values()].sort((a, b) => a.id - b.id)
  const out: GroupThreadItem[] = []
  let lastDay = ''
  let lastSender = ''
  let lastAt = Number.NaN
  for (const m of ordered) {
    const day = m.sent_at ? formatDate(m.sent_at) : ''
    const at = toMillis(m.sent_at)
    if (day && day !== lastDay) {
      out.push({ kind: 'day', key: `day-${day}`, label: dayLabel(day, now) })
      lastDay = day
      lastSender = ''
    }
    const sameRun =
      m.from_name === lastSender && Number.isFinite(at) && Number.isFinite(lastAt) && at - lastAt <= SAME_RUN_MS
    out.push({ kind: 'message', key: `m-${m.id}`, message: m, showHeader: !sameRun })
    lastSender = m.from_name
    lastAt = at
  }
  return out
}

/** Chữ trên ô ảnh đại diện: chữ đầu của hai từ cuối («Trần Được» → «TĐ», «Pltgiang» → «P»). */
export function getInitials(name: string | null | undefined): string {
  const words = (name ?? '').trim().split(/\s+/).filter(Boolean)
  if (!words.length) return '?'
  return words
    .slice(-2)
    .map((w) => w[0]?.toLocaleUpperCase('vi-VN') ?? '')
    .join('')
}

const AVATAR_TONES = [
  TONE_CLASS.progress,
  TONE_CLASS.done,
  TONE_CLASS.handoff,
  TONE_CLASS.active,
  TONE_CLASS.partial,
  TONE_CLASS.returned,
]

/** Màu ô ảnh đại diện cố định theo tên — cùng một người luôn cùng một màu. */
export function getAvatarTone(name: string | null | undefined): string {
  let h = 0
  for (const ch of name ?? '') h = (h * 31 + ch.charCodeAt(0)) >>> 0
  return AVATAR_TONES[h % AVATAR_TONES.length] ?? TONE_CLASS.neutral
}

