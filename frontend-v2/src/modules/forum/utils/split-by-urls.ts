/** Một mẩu của nội dung bài: chữ thường hoặc một đường link. */
export interface TextPart {
  type: 'text' | 'url'
  value: string
}

// Chỉ nhận http(s) tường minh — "abc.com" trần không biến thành link, vì trong
// nội dung tiếng Việt nó dễ là tên tệp/mã hàng hơn là địa chỉ web.
const URL_RE = /https?:\/\/[^\s<>"]+/g

/**
 * Cắt nội dung bài viết thành mảng chữ / link để tầng hiển thị gắn `<a>` cho
 * từng link. Dấu câu đóng ngay sau link (`.` `,` `)` …) được trả về phần chữ —
 * người dùng gõ "xem https://a.vn." thì dấu chấm không thuộc địa chỉ.
 */
export function splitByUrls(text: string): TextPart[] {
  const parts: TextPart[] = []
  let cursor = 0
  for (const match of text.matchAll(URL_RE)) {
    let url = match[0]
    // Gọt dấu câu bám đuôi; `)` chỉ gọt khi trong link không có `(` mở tương ứng
    // (link Wikipedia kiểu `..._(film)` phải giữ nguyên).
    while (/[.,;:!?)]$/.test(url)) {
      if (url.endsWith(')') && url.includes('(')) break
      url = url.slice(0, -1)
    }
    if (match.index > cursor) {
      parts.push({ type: 'text', value: text.slice(cursor, match.index) })
    }
    parts.push({ type: 'url', value: url })
    cursor = match.index + url.length
  }
  if (cursor < text.length) parts.push({ type: 'text', value: text.slice(cursor) })
  return parts
}
