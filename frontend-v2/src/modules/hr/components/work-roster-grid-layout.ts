import type { CSSProperties } from 'react'

import type { WorkRosterMode } from '../utils/work-roster-range'

/**
 * Hằng bố cục của lưới «Xem lịch». Lưới dựng bằng `div` + CSS grid (vai trò ARIA của bảng giữ nguyên) chứ
 * không bằng `<table>`: ô dính trong `<table>` chỉ bị giới hạn bởi CẢ BẢNG, nên không có cách CSS nào để một
 * khối hàng dính bị khối sau ĐẨY ra. Với `div`, hàng dính bị giới hạn bởi khung cha (một «đợt») — trình duyệt
 * tự đẩy, không cần JS theo dõi cuộn (bản JS luôn trễ một nhịp so với cuộn trên macOS → giật).
 */

/** Đầu bảng: hàng ngày h-12 (48px) + hàng tổng h-7 (28px). */
export const ROSTER_HEADER_HEIGHT = 48 + 28

/** Chiều cao một hàng nhân sự (khớp `h-10` / `h-8` trong `WorkRosterRow`). */
export function rosterRowHeight(mode: WorkRosterMode): number {
  return mode === 'month' ? 32 : 40
}

/** Số hàng có nghỉ phép dính thành một khối (đại ca chốt 05/10/2026: «3 row, từ row 4 5 6 đẩy lên 1 lượt»). */
export const STICKY_LEAVE_SLOTS = 3

/** Mọi hàng dùng chung khuôn cột qua biến `--roster-cols` đặt ở khung ngoài. */
export const ROSTER_ROW_GRID = 'grid [grid-template-columns:var(--roster-cols)]'

/** Biến CSS khuôn cột: cột tên 200px + cột ngày (tuần giãn đều, tháng hẹp cố định). */
export function rosterColumnsStyle(mode: WorkRosterMode, dayCount: number): CSSProperties {
  const day = mode === 'month' ? '2rem' : 'minmax(7rem, 1fr)'
  return { '--roster-cols': `12.5rem repeat(${dayCount}, ${day})` } as CSSProperties
}

/** Ô tên dính trái; bóng mờ bên phải báo hiệu nội dung đang cuộn ngang dưới nó. */
export const STICKY_NAME_CELL =
  'sticky left-0 z-10 min-w-0 border-r border-border/60 bg-card after:pointer-events-none after:absolute after:inset-y-0 after:-right-2 after:w-2 after:bg-gradient-to-r after:from-foreground/5 after:to-transparent'
