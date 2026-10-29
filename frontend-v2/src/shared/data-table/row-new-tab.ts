import type { MouseEvent } from 'react'

/**
 * bao-CR-693 — mở chi tiết ở TAB MỚI từ màn danh sách, để trang đang tìm / lọc
 * giữ nguyên (phiếu TK29102601). Dùng chung cho `DataTable` (`getRowHref`) và
 * ô mã chứng từ (`RowLink` ở `row-link.tsx`).
 */

/** Người dùng muốn mở tab mới: Ctrl / Cmd + bấm trái, hoặc bấm chuột giữa. */
export function wantsNewTab(event: Pick<MouseEvent, 'ctrlKey' | 'metaKey' | 'button'>): boolean {
  return event.ctrlKey || event.metaKey || event.button === 1
}

/**
 * Cú bấm rơi vào thứ có thao tác riêng (ô tick, nút, link, ô nhập) — dòng
 * không được mở chi tiết, kẻo bấm chuột giữa vào ô tick cũng bật ra một tab.
 */
export function isInteractiveTarget(event: { target: EventTarget | null }): boolean {
  const target = event.target
  if (!(target instanceof Element)) return false
  return target.closest('a, button, input, select, textarea, label, [role="checkbox"]') !== null
}

/**
 * Đổi đường của router (`/procurement/purchase-orders/12`) thành href đầy đủ
 * để mở bằng `window.open`. Router v2 không khai `basename`, nên tiền tố duy
 * nhất là `base` của Vite (`import.meta.env.BASE_URL`, mặc định `/`) — có
 * dựng app dưới thư mục con thì hai chỗ đó phải đổi cùng nhau.
 */
export function toAppHref(path: string): string {
  if (/^[a-z][a-z0-9+.-]*:/i.test(path)) return path
  const base = (import.meta.env.BASE_URL || '/').replace(/\/+$/, '')
  return `${base}${path.startsWith('/') ? path : `/${path}`}`
}

export function openInNewTab(path: string): void {
  window.open(toAppHref(path), '_blank', 'noopener')
}
