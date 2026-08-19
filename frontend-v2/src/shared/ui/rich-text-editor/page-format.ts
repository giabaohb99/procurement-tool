/**
 * THỂ THỨC TRANG GIẤY — một nguồn số duy nhất cho trình soạn thảo và bản in.
 *
 * Nghị định 30/2020 điều 8 khoản 3 quy định văn bản hành chính dùng khổ A4, lề
 * trên 20–25mm, lề dưới 20–25mm, **lề trái 30–35mm**, lề phải 15–20mm. Lề trái
 * rộng là để đóng gáy — in ra rồi mới phát hiện chữ bị kẹp vào gáy thì phải in
 * lại cả tập.
 *
 * Backend giữ lề của từng phiên bản theo **mm** (`tab_document_version`), giao
 * diện làm việc bằng **px** ở 96dpi. Mọi phép quy đổi đi qua đúng hai hàm dưới
 * đây, đừng rải hằng số 3.7795 ra các tệp khác.
 */

/** 1mm ở 96dpi. Cùng hệ quy đổi với `PX_PER_CM` của thước kẻ. */
export const PX_PER_MM = 96 / 25.4

/** Khổ A4 ở 96dpi: 210 × 297mm. */
export const A4_WIDTH_PX = 794
export const A4_HEIGHT_PX = 1123

/**
 * Lề trên/dưới, cố định 20mm.
 *
 * Không cho sửa vì đây là số liệu `PaginationPlus` dùng để tính một trang chứa
 * bao nhiêu dòng: đổi nóng thì phải dựng lại trình soạn thảo, mất sạch lịch sử
 * hoàn tác của người đang gõ.
 */
export const MARGIN_TOP_MM = 20
export const MARGIN_BOTTOM_MM = 20

/** Lề ngang mặc định khi bản ghi chưa nói gì — đúng Nghị định 30. */
export const MARGIN_LEFT_MM = 30
export const MARGIN_RIGHT_MM = 20

export function mmToPx(mm: number): number {
  return Math.round(mm * PX_PER_MM)
}

export function pxToMm(px: number): number {
  return Math.round(px / PX_PER_MM)
}
