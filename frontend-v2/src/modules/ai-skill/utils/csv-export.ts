/**
 * Dựng tệp CSV ngay trên trình duyệt từ các dòng ĐANG XEM (nhật ký lượt gọi, trang hiện tại) — không có đường xuất
 * phía máy chủ ở đợt K5.
 *
 * Hai chốt an toàn:
 * - Mỗi ô bọc nháy kép, nháy kép bên trong nhân đôi (RFC 4180) để dấu phẩy / xuống dòng trong lý do từ chối không
 *   làm lệch cột.
 * - Ô bắt đầu bằng `=`, `+`, `-`, `@`, tab hay CR được thêm dấu nháy đơn ở đầu: Excel coi các ô đó là CÔNG THỨC, mà
 *   tên công cụ / tên ứng dụng AI trong nhật ký là chuỗi bên ngoài gửi vào (kẻ xấu đặt tên ứng dụng
 *   `=HYPERLINK(...)` là người mở tệp bấm phải link độc).
 */

const FORMULA_START = /^[=+\-@\t\r]/
const UTF8_BOM = '\uFEFF'

export function escapeCsvCell(value: unknown): string {
  let text = value == null ? '' : String(value)
  if (FORMULA_START.test(text)) text = `'${text}`
  return `"${text.replaceAll('"', '""')}"`
}

export interface CsvColumn<T> {
  header: string
  value: (row: T) => unknown
}

/** Chuỗi CSV có BOM UTF-8 ở đầu để Excel đọc đúng tiếng Việt. */
export function buildCsv<T>(rows: readonly T[], columns: readonly CsvColumn<T>[]): string {
  const lines = [columns.map((c) => escapeCsvCell(c.header)).join(',')]
  for (const row of rows) lines.push(columns.map((c) => escapeCsvCell(c.value(row))).join(','))
  return UTF8_BOM + lines.join('\r\n')
}

/** Tải chuỗi CSV xuống máy người dùng. */
export function downloadCsv(filename: string, csv: string): void {
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}
