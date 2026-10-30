/**
 * Tách chữ có `**in đậm**` / `*in nghiêng*` kiểu markdown thành từng đoạn để vẽ bằng `<strong>` / `<em>`.
 *
 * Sinh ra ở bao-CR-695 (30/10/2026): máy chủ bỏ dấu ngoặc kép góc, câu bot / Trợ lý / mô tả công cụ chuyển sang
 * `**x**`. Chỗ nào vẽ chữ đó bằng chữ TRƠN (vd ghi chú, kế hoạch của bot sửa mã ở Quản trị > Việc của bot) là lộ nguyên
 * hai dấu sao. Đây CỐ Ý chỉ là đánh dấu trong dòng — không tiêu đề, không danh sách, không link, không HTML — nên dùng
 * được ở mọi ô chữ trơn mà không đổi bố cục; cần markdown đầy đủ thì dùng `MarkdownMessage` của Trợ lý.
 *
 * Luật để không bắt nhầm:
 * - dấu mở phải dính chữ phía sau, dấu đóng dính chữ phía trước (`**x**`, không nhận `** x **`);
 * - in nghiêng một sao không đứng giữa chữ (`a*b*c`) và không qua dòng — tránh dấu nhân, gạch đầu dòng `* mục`;
 * - dấu không đóng thì giữ nguyên văn.
 */
export interface EmphasisSegment {
  text: string
  bold?: boolean
  italic?: boolean
}

const EMPHASIS_RE = /\*\*(?=\S)([^\n]*?\S)\*\*|(?<![*\p{L}\p{N}])\*(?=[^\s*])([^*\n]*?[^\s*])\*(?![*\p{L}\p{N}])/gu

export function splitInlineEmphasis(text: string): EmphasisSegment[] {
  if (!text) return []
  const out: EmphasisSegment[] = []
  let last = 0
  for (const match of text.matchAll(EMPHASIS_RE)) {
    const start = match.index ?? 0
    if (start > last) out.push({ text: text.slice(last, start) })
    if (match[1] !== undefined) out.push({ text: match[1], bold: true })
    else out.push({ text: match[2], italic: true })
    last = start + match[0].length
  }
  if (last < text.length) out.push({ text: text.slice(last) })
  return out
}

/** Bỏ dấu, giữ chữ — cho chỗ BẮT BUỘC là chuỗi thuần (toast, `title=`, hộp xác nhận). */
export function stripInlineEmphasis(text: string): string {
  return splitInlineEmphasis(text)
    .map((s) => s.text)
    .join('')
}
