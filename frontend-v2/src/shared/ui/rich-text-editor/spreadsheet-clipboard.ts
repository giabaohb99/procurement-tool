/**
 * NHẬN DIỆN CLIPBOARD TỪ EXCEL / GOOGLE SHEETS.
 *
 * Excel thường đặt CÙNG LÚC ba bản của vùng vừa chép vào clipboard:
 *
 * - `text/html` có một `<table>` — bản cần dùng để dán thành bảng sửa được;
 * - `text/plain` phân cột bằng tab;
 * - một file ảnh xem trước.
 *
 * Nếu plugin ảnh nhìn mỗi `clipboardData.files`, nó sẽ lấy ảnh xem trước và
 * nuốt mất bảng. Các hàm ở đây giúp mọi đường dán cùng ưu tiên dữ liệu bảng.
 */

export function containsHtmlTable(html: string): boolean {
  return /<table(?:\s|>)/i.test(html)
}

export function isTabSeparatedTable(text: string): boolean {
  // Một hàng nhiều cột vẫn là bảng, nên chỉ cần có tab; không bắt buộc có \n.
  return text.includes('\t')
}

type ClipboardTextReader = Pick<DataTransfer, 'getData'>

export function clipboardHasSpreadsheetTable(data: ClipboardTextReader | null): boolean {
  if (!data) return false

  try {
    return (
      containsHtmlTable(data.getData('text/html')) ||
      isTabSeparatedTable(data.getData('text/plain'))
    )
  } catch {
    // Một số trình duyệt chỉ cho đọc đúng loại dữ liệu trong chính sự kiện dán.
    // Không đọc được thì để các plugin khác xử lý theo hành vi cũ.
    return false
  }
}

/** Đổi TSV thành bảng HTML để ProseMirror có thể rải từng ô vào CellSelection. */
export function tabSeparatedTextToTableHtml(text: string): string | null {
  if (!isTabSeparatedTable(text)) return null

  const normalized = text.replace(/\r\n?/g, '\n').replace(/\n$/, '')
  const rows = normalized.split('\n')
  const body = rows
    .map(
      (row) =>
        `<tr>${row
          .split('\t')
          .map((cell) => `<td><p>${escapeHtml(cell)}</p></td>`)
          .join('')}</tr>`,
    )
    .join('')

  return `<table><tbody>${body}</tbody></table>`
}

function escapeHtml(value: string): string {
  return value
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;')
}
