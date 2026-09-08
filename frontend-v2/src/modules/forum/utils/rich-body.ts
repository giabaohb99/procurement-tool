/**
 * Bóc thẻ HTML của bài rich (CR-261) lấy CHỮ TRƠN — để kiểm rỗng ở hộp soạn,
 * ước bài "dài" cho nút «Xem thêm», và làm nhãn một dòng trên sidebar.
 *
 * KHÔNG phải bộ lọc an toàn (việc đó của `sanitizeHtml` + sanitize server) và
 * CHỈ gọi cho body có `body_format = richHtml` — chữ trơn chứa `a < b` mà đi
 * qua đây sẽ bị ăn mất chữ vì regex tưởng là thẻ.
 */
export function stripRichBodyText(html: string): string {
  return html
    .replace(/<[^>]+>/g, ' ')
    .replace(/&nbsp;/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
}

/** Bài rich coi là RỖNG khi bóc thẻ xong không còn chữ (`<p></p>`, `&nbsp;`...). */
export function isBlankRichBody(html: string): boolean {
  return stripRichBodyText(html) === ''
}
