// duoc-CR-612 — hằng số + kiểu dùng chung của dạng «Bảng» (khối Báo cáo thực hiện). Tách khỏi
// tệp component để Fast Refresh không than (`react-refresh/only-export-components`).
import type { ReportDocPayload } from '../../api/survey-request-report-api'

/** Trường sửa được trên hàng — tiên quyết (`depends`) cố ý không có (ô chọn nhiều, ít đổi). */
export type ReportDocInlineChanges = Partial<Omit<ReportDocPayload, 'depends'>>

/** Giá trị ô «Dòng hàng» của hồ sơ CHUNG — trùng `item_id = 0`. */
export const COMMON_ITEM_VALUE = '0'

/**
 * Lớp GHIM của ba cột đầu (✓ · # · Hồ sơ), theo vị trí cột. Mốc `left` khớp bề rộng
 * 36px + 36px ở `COLUMNS` của bảng. Ô ghim phải có nền đặc, không thì chữ của cột cuộn
 * qua bên dưới lộ ra; cột tên có vạch phải để thấy chỗ ghim.
 */
export const STICKY_CELL: Record<number, string> = {
  0: 'sticky left-0 z-10',
  1: 'sticky left-9 z-10',
  2: 'sticky left-[72px] z-10 shadow-[inset_-1px_0_0_var(--color-border)]',
}

export interface SelectOption {
  value: string
  label: string
}
