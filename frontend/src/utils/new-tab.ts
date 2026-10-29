// bao-CR-693 — mở chi tiết ở TAB MỚI từ màn danh sách (Ctrl/Cmd + bấm, hoặc bấm chuột giữa),
// để trang danh sách đang lọc giữ nguyên. Bấm thường vẫn mở cùng tab như cũ.
import type { MouseEvent } from 'react'

/** Cú bấm này người dùng muốn mở tab mới: Ctrl/Cmd + bấm trái, hoặc bấm chuột giữa. */
export function wantsNewTab(e: MouseEvent): boolean {
  return e.ctrlKey || e.metaKey || e.button === 1
}

/** Cú bấm rơi vào ô có thao tác riêng (ô tick, nút, link, ô nhập) — dòng không được mở chi tiết. */
export function isInteractiveTarget(e: MouseEvent): boolean {
  const el = e.target as HTMLElement | null
  return !!el?.closest?.('a, button, input, select, textarea, label')
}

export function openInNewTab(url: string): void {
  window.open(url, '_blank', 'noopener')
}
