import type { ReactNode } from 'react'

import { cn } from '@/shared/utils/cn'
import {
  BOOKING_STATUS_BADGE,
  BOOKING_STATUS_LABELS,
  DRIVER_STATUS_BADGE,
  DRIVER_STATUS_LABELS,
  type BadgeTone,
} from '../types/vehicle-booking'

/**
 * Badge trạng thái dạng "pill" theo po_badges_design.md: bo tròn mạnh, chữ hoa,
 * nhỏ + đậm. Màu là bộ cố định của tài liệu thiết kế (không phải token theme) nên
 * đặt thẳng ở đây bằng inline style — đổi màu badge thì sửa DUY NHẤT bảng này.
 */
const TONE_COLORS: Record<BadgeTone, { bg: string; fg: string }> = {
  gray: { bg: '#eef1f4', fg: '#5b6770' },
  warn: { bg: '#fef3c7', fg: '#d97706' },
  ok: { bg: '#e6f8ec', fg: '#16a34a' },
  err: { bg: '#fdecea', fg: '#d32f2f' },
  info: { bg: '#e6f0fd', fg: '#2563eb' },
}

interface StatusPillProps {
  tone: BadgeTone
  children: ReactNode
  className?: string
}

export function StatusPill({ tone, children, className }: StatusPillProps) {
  const c = TONE_COLORS[tone]
  return (
    <span
      className={cn(
        'inline-flex items-center justify-center whitespace-nowrap rounded-full px-2.5 py-1',
        'text-[10.5px] font-bold uppercase leading-none tracking-wide',
        className,
      )}
      style={{ backgroundColor: c.bg, color: c.fg }}
    >
      {children}
    </span>
  )
}

/** Badge trạng thái CHUNG của phiếu (Nháp / Chờ duyệt / Điều phối…). */
export function BookingStatusBadge({ status, label }: { status: number; label?: string }) {
  return (
    <StatusPill tone={BOOKING_STATUS_BADGE[status] ?? 'gray'}>
      {label || BOOKING_STATUS_LABELS[status] || '—'}
    </StatusPill>
  )
}

/** Badge trạng thái TÀI XẾ (Chờ tài xế / Đã nhận / Đang đi…). Trả null khi chưa phân. */
export function DriverStatusBadge({ status, label }: { status: number; label?: string }) {
  const text = label || DRIVER_STATUS_LABELS[status]
  if (!text) return null
  return <StatusPill tone={DRIVER_STATUS_BADGE[status] ?? 'gray'}>{text}</StatusPill>
}

/**
 * Badge NGUỒN (xe/tài xế nội bộ hay thuê ngoài) — dùng chung cho hai danh mục.
 * Đồng bộ màu với nút chọn nguồn trong form: Nội bộ = xanh dương, Thuê ngoài = hổ phách.
 */
export function SourceBadge({ isExternal }: { isExternal: boolean }) {
  return (
    <StatusPill tone={isExternal ? 'warn' : 'info'}>{isExternal ? 'Thuê ngoài' : 'Nội bộ'}</StatusPill>
  )
}

/** Badge trạng thái sẵn sàng của XE / TÀI XẾ (chuỗi mã 'available' | 'maintenance' | …). */
export function AvailabilityBadge({ status, label }: { status: string; label?: string }) {
  //  Sẵn sàng = xanh lá; Bảo trì / Nghỉ phép = vàng (amber); còn lại (Ngưng dùng…) = xám.
  const tone: BadgeTone =
    status === 'available'
      ? 'ok'
      : status === 'maintenance' || status === 'on_leave'
        ? 'warn'
        : 'gray'
  return <StatusPill tone={tone}>{label || status || '—'}</StatusPill>
}
