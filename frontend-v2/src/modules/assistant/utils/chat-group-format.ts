import { TONE_CLASS } from '@/shared/ui/status-tone'

import type { ChatGroupItem, ZaloAccountStatus } from '../api/chat-group-api'

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
