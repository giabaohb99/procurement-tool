/**
 * duoc-CR-784 — tiêu đề tab của BẢN IN cụm Giá bao bì, cũng là tên tệp PDF mà trình duyệt gợi ý khi "Lưu thành PDF".
 * Giữ tiếng Việt có dấu + khoảng trắng như tên báo cáo, chỉ thay các ký tự hệ điều hành cấm đặt tên tệp.
 * Ví dụ: "Giá nguyên vật liệu sản xuất - Lịch sử mua hàng - 26-11-2026".
 */
const REPORT_NAME = 'Giá nguyên vật liệu sản xuất'
/** Ký tự Windows / macOS cấm trong tên tệp (cộng ký tự điều khiển). */
// eslint-disable-next-line no-control-regex
const FORBIDDEN_FILENAME_CHARS = /[\\/:*?"<>|\u0000-\u001f]/g

function pad2(value: number): string {
  return String(value).padStart(2, '0')
}

/** `dd-mm-yyyy` theo giờ máy người in. */
export function formatPrintFileDate(date: Date): string {
  return `${pad2(date.getDate())}-${pad2(date.getMonth() + 1)}-${date.getFullYear()}`
}

/** `Giá nguyên vật liệu sản xuất - <tên bản in> - dd-mm-yyyy`, đã lọc ký tự cấm và gộp khoảng trắng. */
export function buildPackagingPrintTitle(subtitle: string, date: Date = new Date()): string {
  const clean = subtitle.replace(FORBIDDEN_FILENAME_CHARS, ' ').replace(/\s+/g, ' ').trim()
  return [REPORT_NAME, clean, formatPrintFileDate(date)].filter(Boolean).join(' - ')
}
