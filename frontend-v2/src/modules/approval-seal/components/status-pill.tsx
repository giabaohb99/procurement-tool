import type { ReactNode } from 'react'

import { cn } from '@/shared/utils/cn'
import { SEAL_STATUS_BADGE, SEAL_STATUS_LABELS, type BadgeTone } from '../types/seal-request'

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

/** Badge trạng thái phiếu đóng dấu (Nháp / Chờ duyệt / Đã duyệt / Hoàn thành…). */
export function SealStatusBadge({ status, label }: { status: number; label?: string }) {
  return (
    <StatusPill tone={SEAL_STATUS_BADGE[status] ?? 'gray'}>
      {label || SEAL_STATUS_LABELS[status] || '—'}
    </StatusPill>
  )
}
