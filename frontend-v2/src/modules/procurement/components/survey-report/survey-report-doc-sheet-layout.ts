// duoc-CR-612 — hằng số + kiểu dùng chung của dạng «Bảng» (khối Báo cáo thực hiện). Tách khỏi
// tệp component để Fast Refresh không than (`react-refresh/only-export-components`).
import type { ReportDocPayload } from '../../api/survey-request-report-api'

/** Trường sửa được trên hàng — tiên quyết (`depends`) cố ý không có (ô chọn nhiều, ít đổi). */
export type ReportDocInlineChanges = Partial<Omit<ReportDocPayload, 'depends'>>

/** Giá trị ô «Dòng hàng» của hồ sơ CHUNG — trùng `item_id = 0`. */
export const COMMON_ITEM_VALUE = '0'

/**
 * Lớp GHIM của hai cột đầu (# · Hồ sơ), theo vị trí cột. Mốc `left` khớp bề rộng 36px
 * của cột # ở `COLUMNS` của bảng. Ô ghim phải có nền đặc, không thì chữ của cột cuộn
 * qua bên dưới lộ ra; cột tên có vạch phải để thấy chỗ ghim. Cột ô tick ✓ đầu bảng đã
 * bỏ (duoc-CR-617) — đánh dấu xong chọn «Hoàn thành» ở cột Trạng thái.
 */
export const STICKY_CELL: Record<number, string> = {
  0: 'sticky left-0 z-10',
  1: 'sticky left-9 z-10 shadow-[inset_-1px_0_0_var(--color-border)]',
}

/**
 * Ô chọn «Giai đoạn» trong bảng: tên giai đoạn dài («1. Kế hoạch công việc nhập khẩu») phải
 * XUỐNG DÒNG như ô «Dòng hàng» bên cạnh, không bị cắt cụt. `SelectTrigger` gốc ép một dòng
 * bằng `line-clamp-1` + `whitespace-nowrap` + `data-[size=sm]:h-8` — phải đè đúng các biến thể
 * đó (`h-7` trơn thua `data-[size=sm]:h-8` về độ ưu tiên nên không có tác dụng).
 */
export const WRAP_SELECT_TRIGGER =
  'h-auto min-h-7 w-full px-2 py-1 text-left text-xs whitespace-normal [overflow-wrap:anywhere] data-[size=sm]:h-auto *:data-[slot=select-value]:line-clamp-none'

export interface SelectOption {
  value: string
  label: string
}
